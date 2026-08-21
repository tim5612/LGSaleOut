"""Passkey/WebAuthn authentication for LGSale."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from datetime import datetime, timedelta
from typing import Any

from flask import session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

import lgsale_db as db


RP_ID = os.getenv("LGSALEOUT_RP_ID", "lgdeva.superb-supplies.com.tw")
RP_NAME = os.getenv("LGSALEOUT_RP_NAME", "LGSale")
ORIGIN = os.getenv("LGSALEOUT_ORIGIN", "https://lgdeva.superb-supplies.com.tw")
DESKTOP_APPROVAL_TTL_SECONDS = 120
_desktop_approval_lock = threading.Lock()
_desktop_approvals: dict[str, dict[str, Any]] = {}


def _json(value: Any) -> dict[str, Any]:
    return json.loads(options_to_json(value))


def _challenge_key(purpose: str) -> str:
    return f"webauthn_{purpose}"


def _save_challenge(purpose: str, challenge: bytes, **context: Any) -> None:
    session[_challenge_key(purpose)] = {
        "challenge": challenge.hex(),
        "expires": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        **context,
    }


def _take_challenge(purpose: str) -> dict[str, Any]:
    data = session.pop(_challenge_key(purpose), None)
    if not data or datetime.fromisoformat(data["expires"]) < datetime.utcnow():
        raise ValueError("驗證要求已失效，請重新操作")
    data["challenge"] = bytes.fromhex(data["challenge"])
    return data


def _approval_key(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _purge_desktop_approvals(now: datetime) -> None:
    expired = [key for key, value in _desktop_approvals.items() if value["expiresAt"] <= now]
    for key in expired:
        _desktop_approvals.pop(key, None)


def start_desktop_approval(device_name: str, next_path: str) -> dict[str, Any]:
    """Create a short-lived, single-use QR approval bound to this desktop session."""
    now = datetime.utcnow()
    token = secrets.token_urlsafe(32)
    browser_key = secrets.token_urlsafe(24)
    safe_next = next_path if next_path.startswith("/") and not next_path.startswith("//") else "/"
    pending = {
        "browserKey": browser_key,
        "deviceName": (device_name or "LGSale 桌機版").strip()[:100],
        "createdAt": now,
        "expiresAt": now + timedelta(seconds=DESKTOP_APPROVAL_TTL_SECONDS),
        "next": safe_next,
        "approvedUser": None,
    }
    with _desktop_approval_lock:
        _purge_desktop_approvals(now)
        _desktop_approvals[_approval_key(token)] = pending
    session["desktop_approval_browser_key"] = browser_key
    return {
        "token": token,
        "approvalUrl": f"{ORIGIN}/desktop-approve?token={token}",
        "expiresAt": pending["expiresAt"].isoformat(timespec="seconds") + "Z",
        "expiresIn": DESKTOP_APPROVAL_TTL_SECONDS,
    }


def desktop_approval_info(token: str) -> dict[str, Any]:
    now = datetime.utcnow()
    with _desktop_approval_lock:
        _purge_desktop_approvals(now)
        pending = _desktop_approvals.get(_approval_key(token))
        if pending is None:
            raise ValueError("此桌機登入 QR Code 已失效，請回到桌機重新產生")
        verified_at = session.get("passkey_verified_at")
        verification_fresh = False
        if verified_at:
            try:
                verification_fresh = now - datetime.fromisoformat(verified_at) <= timedelta(minutes=2)
            except (TypeError, ValueError):
                pass
        return {
            "deviceName": pending["deviceName"],
            "createdAt": pending["createdAt"].isoformat(timespec="seconds") + "Z",
            "expiresAt": pending["expiresAt"].isoformat(timespec="seconds") + "Z",
            "approved": pending["approvedUser"] is not None,
            "verificationFresh": verification_fresh,
        }


def approve_desktop(token: str) -> dict[str, Any]:
    user = session.get("user")
    if not user or user.get("type") != "EMPLOYEE":
        raise PermissionError("必須使用業務帳號授權桌機版登入")
    now = datetime.utcnow()
    try:
        verified_at = datetime.fromisoformat(str(session.get("passkey_verified_at", "")))
    except ValueError:
        verified_at = datetime.min
    if now - verified_at > timedelta(minutes=2):
        raise PermissionError("授權前必須重新使用 Passkey／Face ID 驗證")
    with _desktop_approval_lock:
        _purge_desktop_approvals(now)
        pending = _desktop_approvals.get(_approval_key(token))
        if pending is None:
            raise ValueError("此桌機登入 QR Code 已失效")
        if pending["approvedUser"] is not None:
            raise ValueError("此桌機登入 QR Code 已完成授權")
        pending["approvedUser"] = dict(user)
        pending["approvedAt"] = now
        return {"approved": True, "desktop": pending["deviceName"], "user": user["name"]}


def poll_desktop_approval(token: str) -> dict[str, Any]:
    now = datetime.utcnow()
    browser_key = session.get("desktop_approval_browser_key")
    with _desktop_approval_lock:
        _purge_desktop_approvals(now)
        key = _approval_key(token)
        pending = _desktop_approvals.get(key)
        if pending is None:
            return {"status": "EXPIRED"}
        if not browser_key or not secrets.compare_digest(browser_key, pending["browserKey"]):
            raise PermissionError("此 QR Code 不屬於目前桌機瀏覽器")
        if pending["approvedUser"] is None:
            return {"status": "PENDING", "expiresAt": pending["expiresAt"].isoformat(timespec="seconds") + "Z"}
        user = dict(pending["approvedUser"])
        next_path = pending["next"]
        _desktop_approvals.pop(key, None)
    session.clear()
    session.permanent = True
    session["user"] = user
    return {"status": "APPROVED", "user": user, "next": next_path}


def registration_options(token: str) -> dict[str, Any]:
    invitation = db.passkey_invitation(hashlib.sha256(token.encode()).digest())
    if invitation is None:
        raise ValueError("註冊邀請無效、已使用或已過期")
    credentials = db.passkey_credentials(invitation["userAccountId"])
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(invitation["userAccountId"]).encode(),
        user_name=invitation["accountLabel"],
        user_display_name=invitation["displayName"],
        timeout=300000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[PublicKeyCredentialDescriptor(id=item["credentialId"]) for item in credentials],
    )
    _save_challenge("registration", options.challenge, invitationId=invitation["invitationId"], userAccountId=invitation["userAccountId"])
    result = _json(options)
    result["account"] = {"type": invitation["accountType"], "label": invitation["displayName"]}
    return result


def registration_invitation_is_valid(token: str) -> bool:
    if not token:
        return False
    return db.passkey_invitation(hashlib.sha256(token.encode()).digest()) is not None


def finish_registration(credential: dict[str, Any], device_name: str) -> dict[str, Any]:
    state = _take_challenge("registration")
    verified = verify_registration_response(
        credential=credential,
        expected_challenge=state["challenge"],
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        require_user_verification=True,
    )
    transports = credential.get("response", {}).get("transports") or []
    db.save_passkey(
        invitation_id=state["invitationId"],
        user_account_id=state["userAccountId"],
        credential_id=verified.credential_id,
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        transports=",".join(transports) or None,
        device_name=(device_name or "未命名 Passkey").strip()[:100],
    )
    return {"registered": True}


def authentication_options(account_type: str) -> dict[str, Any]:
    if account_type not in {"EMPLOYEE", "DEALER"}:
        raise ValueError("登入入口不正確")
    credentials = db.active_passkey_credential_ids(account_type)
    if not credentials:
        raise ValueError("此登入入口尚未設定可用的 Passkey")
    options = generate_authentication_options(
        rp_id=RP_ID,
        timeout=300000,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[PublicKeyCredentialDescriptor(id=value) for value in credentials],
    )
    _save_challenge("authentication", options.challenge, accountType=account_type)
    return _json(options)


def finish_authentication(credential: dict[str, Any]) -> dict[str, Any]:
    state = _take_challenge("authentication")
    raw_id = credential.get("rawId") or credential.get("id")
    record = db.passkey_for_login(raw_id, state["accountType"])
    if record is None:
        raise ValueError("此 Passkey 不屬於本登入入口，或帳號已停用")
    verified = verify_authentication_response(
        credential=credential,
        expected_challenge=state["challenge"],
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=record["publicKey"],
        # Synced passkeys commonly report 0 or non-monotonic counters. The project
        # specification treats the counter as a risk signal, not a login blocker.
        credential_current_sign_count=0,
        require_user_verification=True,
    )
    db.record_passkey_login(record["passkeyCredentialId"], record["userAccountId"], verified.new_sign_count)
    session.clear()
    session.permanent = True
    session["user"] = {
        "id": record["userAccountId"], "type": record["accountType"],
        "employeeId": record["employeeId"], "dealerId": record["dealerId"],
        "name": record["displayName"],
    }
    session["passkey_verified_at"] = datetime.utcnow().isoformat()
    return session["user"]


def create_invitation(account_type: str, owner_ref: str, creator_employee_id: int | None = None) -> str:
    token = secrets.token_urlsafe(32)
    db.create_passkey_invitation(account_type.upper(), owner_ref, hashlib.sha256(token.encode()).digest(), creator_employee_id)
    return token
