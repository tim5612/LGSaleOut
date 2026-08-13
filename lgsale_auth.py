"""Passkey/WebAuthn authentication for LGSale."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
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


RP_ID = os.getenv("LGSALEOUT_RP_ID", "localhost")
RP_NAME = os.getenv("LGSALEOUT_RP_NAME", "LGSale")
ORIGIN = os.getenv("LGSALEOUT_ORIGIN", "http://localhost:8098")


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
    options = generate_authentication_options(
        rp_id=RP_ID,
        timeout=300000,
        user_verification=UserVerificationRequirement.REQUIRED,
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
    return session["user"]


def create_invitation(account_type: str, owner_ref: str) -> str:
    token = secrets.token_urlsafe(32)
    db.create_passkey_invitation(account_type.upper(), owner_ref, hashlib.sha256(token.encode()).digest())
    return token
