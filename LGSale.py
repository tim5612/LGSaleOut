"""LGSale local UI prototype server.

Run:
    python LGSale.py

Pages:
    http://127.0.0.1:8097/          Desktop task administration
    http://127.0.0.1:8097/mobile    Employee mobile store-visit interface
    http://127.0.0.1:8097/dealer    Dealer mobile portal
    http://127.0.0.1:8097/photo     Mobile task-photo interface

All application data is read from and written to the LGSaleOut SQL Server
database. Database connection settings can be overridden with LGSALEOUT_DB_*
environment variables; see lgsale_db.py.
"""

from __future__ import annotations

import socket
import argparse
import os
import secrets
from io import BytesIO
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory, session
from werkzeug.utils import secure_filename
import qrcode
import lgsale_db as db
import lgsale_auth as auth
from lgsale_config import required


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "task_photos"
PORT = int(required("LGSALEOUT_PORT"))
app = Flask(__name__)
app.secret_key = os.getenv("LGSALEOUT_SESSION_SECRET") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=auth.ORIGIN.startswith("https://"),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


@app.before_request
def require_login():
    public = request.endpoint in {
        "health", "login_page", "register_page", "auth_register_options",
        "auth_register_verify", "auth_login_options", "auth_login_verify",
        "desktop_approve_page", "desktop_approval_start", "desktop_approval_info",
        "desktop_approval_status", "desktop_approval_qr",
    }
    if public or request.endpoint is None:
        return None
    user = session.get("user")
    if user is None:
        if request.path.startswith("/api/"):
            return jsonify(error="請先使用 Passkey 登入"), 401
        entry = "dealer" if request.path == "/dealer" else "employee"
        return redirect(f"/login/{entry}?next={request.path}")
    if not db.account_login_allowed(int(user["id"])):
        session.clear()
        if request.path.startswith("/api/"):
            return jsonify(error="此帳號已停用，請聯絡管理人員"), 401
        entry = "dealer" if user.get("type") == "DEALER" else "employee"
        return redirect(f"/login/{entry}")
    dealer_allowed = request.path == "/dealer" or request.path in {"/api/auth/me", "/api/auth/logout", "/api/dealers", "/api/products", "/api/mobile-dashboard"} or request.path.startswith("/api/visits")
    if user["type"] == "DEALER" and not dealer_allowed:
        if request.path.startswith("/api/"):
            return jsonify(error="經銷商帳號無權存取此功能"), 403
        return redirect("/dealer")
    if user["type"] == "EMPLOYEE" and request.path == "/dealer":
        return redirect("/mobile")
    return None


@app.get("/login/<account_type>")
def login_page(account_type: str):
    if account_type not in {"employee", "dealer"}:
        return "Not found", 404
    if session.get("user"):
        return redirect("/dealer" if session["user"]["type"] == "DEALER" else "/")
    return send_from_directory(BASE_DIR, "LGSale_Auth.html")


@app.get("/register")
def register_page():
    return send_from_directory(BASE_DIR, "LGSale_Auth.html")


@app.get("/desktop-approve")
def desktop_approve_page():
    token = str(request.args.get("token", ""))
    if not token:
        return "缺少桌機登入授權碼", 400
    if not session.get("user"):
        next_path = quote(f"/desktop-approve?token={token}", safe="")
        return redirect(f"/login/employee?next={next_path}")
    if session["user"].get("type") != "EMPLOYEE":
        return "經銷商帳號不能授權桌機管理版", 403
    return send_from_directory(BASE_DIR, "LGSale_DesktopApprove.html")


def _auth_call(func, *args):
    try:
        return jsonify(func(*args))
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/auth/register/options")
def auth_register_options():
    return _auth_call(auth.registration_options, str((request.get_json(silent=True) or {}).get("token", "")))


@app.post("/api/auth/register/verify")
def auth_register_verify():
    data = request.get_json(silent=True) or {}
    return _auth_call(auth.finish_registration, data.get("credential") or {}, str(data.get("deviceName", "")))


@app.post("/api/auth/login/options")
def auth_login_options():
    return _auth_call(auth.authentication_options, str((request.get_json(silent=True) or {}).get("accountType", "")))


@app.post("/api/auth/login/verify")
def auth_login_verify():
    return _auth_call(auth.finish_authentication, (request.get_json(silent=True) or {}).get("credential") or {})


@app.post("/api/auth/desktop-approval/start")
def desktop_approval_start():
    data = request.get_json(silent=True) or {}
    return _auth_call(auth.start_desktop_approval, str(data.get("deviceName", "")), str(data.get("next", "/")))


@app.get("/api/auth/desktop-approval/info")
def desktop_approval_info():
    return _auth_call(auth.desktop_approval_info, str(request.args.get("token", "")))


@app.post("/api/auth/desktop-approval/approve")
def desktop_approval_approve():
    try:
        return jsonify(auth.approve_desktop(str((request.get_json(silent=True) or {}).get("token", ""))))
    except PermissionError as exc:
        return jsonify(error=str(exc)), 403
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/auth/desktop-approval/status")
def desktop_approval_status():
    try:
        return jsonify(auth.poll_desktop_approval(str(request.args.get("token", ""))))
    except PermissionError as exc:
        return jsonify(error=str(exc)), 403
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/auth/desktop-approval/qr/<token>.png")
def desktop_approval_qr(token: str):
    try:
        auth.desktop_approval_info(token)
        image = qrcode.make(f"{auth.ORIGIN}/desktop-approve?token={token}")
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype="image/png", max_age=0)
    except Exception as exc:
        return jsonify(error=str(exc)), 404


@app.get("/api/auth/me")
def auth_me():
    return jsonify(session["user"])


@app.post("/api/auth/logout")
def auth_logout():
    session.clear()
    return jsonify(loggedOut=True)


@app.get("/api/passkey-accounts")
def passkey_accounts():
    try:
        account_type=str(request.args.get("type", "EMPLOYEE")).upper()
        return jsonify(db.passkey_accounts(account_type))
    except Exception as exc:
        return jsonify(error="Passkey 帳號查詢失敗："+str(exc)),503


@app.put("/api/passkey-accounts")
def update_passkey_account():
    data=request.get_json(silent=True) or {}
    try:
        db.set_passkey_account_enabled(str(data.get("accountType","")).upper(),str(data.get("ownerRef","")).strip(),bool(data.get("enabled")))
        return jsonify(updated=True)
    except LookupError as exc:return jsonify(error=str(exc)),404
    except ValueError as exc:return jsonify(error=str(exc)),400
    except Exception as exc:return jsonify(error="Passkey 帳號更新失敗："+str(exc)),500


@app.post("/api/passkey-invitations")
def create_passkey_invitation():
    data=request.get_json(silent=True) or {};account_type=str(data.get("accountType","")).upper();owner_ref=str(data.get("ownerRef","")).strip()
    if not owner_ref:return jsonify(error="員工編號或經銷商代碼必填"),400
    try:
        token=auth.create_invitation(account_type,owner_ref,session["user"].get("employeeId"))
        return jsonify(token=token,registrationUrl=f"{auth.ORIGIN}/register?token={token}",expiresIn=900),201
    except ValueError as exc:return jsonify(error=str(exc)),400
    except Exception as exc:return jsonify(error="Passkey 邀請建立失敗："+str(exc)),500


@app.get("/api/passkey-invitations/qr/<token>.png")
def passkey_invitation_qr(token:str):
    if not auth.registration_invitation_is_valid(token):return jsonify(error="Passkey 邀請已失效"),404
    image=qrcode.make(f"{auth.ORIGIN}/register?token={token}");output=BytesIO();image.save(output,format="PNG");output.seek(0)
    return send_file(output,mimetype="image/png",max_age=0)


@app.post("/api/passkey-credentials/<int:credential_id>/revoke")
def revoke_passkey_credential(credential_id:int):
    try:
        if not db.revoke_passkey_credential(credential_id):return jsonify(error="找不到可撤銷的 Passkey"),404
        return jsonify(revoked=True)
    except Exception as exc:return jsonify(error="Passkey 撤銷失敗："+str(exc)),500


@app.get("/")
def desktop_page():
    return send_from_directory(BASE_DIR, "LGSale_UI_Desktop.html")


@app.get("/mobile")
def mobile_page():
    return send_from_directory(BASE_DIR, "LGSale_UI_Wireframe.html")


@app.get("/dealer")
def dealer_page():
    return send_from_directory(BASE_DIR, "LGSale_UI_Wireframe.html")


@app.get("/photo")
def photo_page():
    return send_from_directory(BASE_DIR, "LGSale_UI_PHOTO.html")


@app.get("/api/health")
def health():
    try:
        return jsonify(db.health())
    except Exception as exc:
        return jsonify(status="error", mode="sql-server", error=str(exc)), 503


@app.get("/api/tasks")
def tasks():
    try:
        return jsonify(db.tasks())
    except Exception as exc:
        return jsonify(error="任務資料庫查詢失敗：" + str(exc)), 503


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    required = ["title", "instruction", "validFrom", "dueDate"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify(error="缺少欄位：" + "、".join(missing)), 400
    if data["dueDate"] < data["validFrom"]:
        return jsonify(error="完成期限不得早於開始日期"), 400
    try:
        payload = {**data, "title": str(data["title"]).strip(), "instruction": str(data["instruction"]).strip()}
        return jsonify(db.create_task(payload)), 201
    except Exception as exc:
        return jsonify(error="任務建立失敗：" + str(exc)), 500


@app.post("/api/tasks/<int:task_id>/toggle")
def toggle_task(task_id: int):
    try:
        if not db.toggle_task(task_id):
            return jsonify(error="找不到任務"), 404
        task = next(item for item in db.tasks() if item["id"] == task_id)
        return jsonify(task)
    except Exception as exc:
        return jsonify(error="任務狀態更新失敗：" + str(exc)), 500


@app.get("/api/tasks/<int:task_id>")
def task_detail(task_id: int):
    try:
        item = db.task_detail(task_id)
        return jsonify(item) if item else (jsonify(error="找不到任務"), 404)
    except Exception as exc:
        return jsonify(error="任務詳情查詢失敗：" + str(exc)), 503


@app.put("/api/tasks/<int:task_id>/executions/<int:execution_id>/photos")
def update_task_photos(task_id:int,execution_id:int):
    data=request.get_json(silent=True) or {};user=session["user"]
    try:
        db.update_task_photos(task_id,execution_id,data.get("photos") or [],set_sample=bool(data.get("setSample")),employee_id=user["employeeId"])
        return jsonify(db.task_detail(task_id))
    except LookupError as exc:return jsonify(error=str(exc)),404
    except ValueError as exc:return jsonify(error=str(exc)),409
    except Exception as exc:return jsonify(error="照片說明更新失敗："+str(exc)),500


@app.get("/api/dealers")
def dealers():
    try:
        user = session["user"]
        return jsonify(db.dealers(user["dealerId"] if user["type"] == "DEALER" else None))
    except Exception as exc:
        return jsonify(error="經銷商資料庫查詢失敗：" + str(exc)), 503


def _dealer_payload(data: dict) -> dict:
    required = {"code":"經銷商代碼","name":"經銷商名稱","taxId":"統一編號","area":"區域","level":"經銷商級別","condition":"狀況"}
    missing = [label for key,label in required.items() if not str(data.get(key, "")).strip()]
    if missing:
        raise ValueError("缺少欄位：" + "、".join(missing))
    tax_id = str(data["taxId"]).strip()
    if len(tax_id) != 8 or not tax_id.isdigit():
        raise ValueError("統一編號必須是 8 位數字")
    level = str(data["level"]).strip().upper()
    if level not in {"A","B","C","D","E","Z"}:
        raise ValueError("經銷商級別不正確")
    condition = str(data["condition"]).strip().upper()
    if condition not in {"ACTIVE","PENDING","CLOSED"}:
        raise ValueError("經銷商狀況不正確")
    return {"code":str(data["code"]).strip().upper(),"name":str(data["name"]).strip(),"taxId":tax_id,
            "area":str(data["area"]).strip(),"level":level,"condition":condition,
            "employeeId":int(data["employeeId"]) if data.get("employeeId") else None}


@app.post("/api/dealers")
def create_dealer():
    try:
        payload = _dealer_payload(request.get_json(silent=True) or {})
        dealer_id = db.create_dealer(payload)
        return jsonify(next(row for row in db.dealers() if row["id"] == dealer_id)), 201
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        return jsonify(error="經銷商建立失敗：" + str(exc)), 500


@app.put("/api/dealers/<int:dealer_id>")
def update_dealer(dealer_id: int):
    try:
        payload = _dealer_payload(request.get_json(silent=True) or {})
        if not db.update_dealer(dealer_id, payload):
            return jsonify(error="找不到經銷商"), 404
        return jsonify(next(row for row in db.dealers() if row["id"] == dealer_id))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        return jsonify(error="經銷商更新失敗：" + str(exc)), 500


@app.get("/api/mobile-dashboard")
def mobile_dashboard():
    try:
        user = session["user"]
        return jsonify(db.mobile_dashboard(user.get("employeeId") if user["type"] == "EMPLOYEE" else None,
                                           user.get("dealerId") if user["type"] == "DEALER" else None))
    except Exception as exc:
        return jsonify(error="手機工作台查詢失敗：" + str(exc)), 503


@app.get("/api/dealers/<int:dealer_id>/summary")
def dealer_summary(dealer_id: int):
    try:
        user=session["user"]
        if user["type"] == "DEALER" and user.get("dealerId") != dealer_id:
            return jsonify(error="無權查看其他經銷商"),403
        return jsonify(db.dealer_summary(dealer_id))
    except Exception as exc:
        return jsonify(error="經銷商摘要查詢失敗：" + str(exc)),503


@app.get("/api/employees")
def employees():
    try:
        return jsonify(db.employees())
    except Exception as exc:
        return jsonify(error="員工資料庫查詢失敗：" + str(exc)), 503


@app.post("/api/employees")
def create_employee():
    data = request.get_json(silent=True) or {}
    required = ["number", "name", "hireDate", "position", "org"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify(error="必填欄位未完成：" + "、".join(missing)), 400
    try:
        payload = {**data, "number": str(data["number"]).strip().upper(), "name": str(data["name"]).strip()}
        employee_id = db.create_employee(payload)
        item = next(row for row in db.employees() if row["id"] == employee_id)
        return jsonify(item), 201
    except Exception as exc:
        status = 409 if "UNIQUE" in str(exc).upper() else 500
        return jsonify(error="員工建立失敗：" + str(exc)), status


@app.put("/api/employees/<int:employee_id>")
def update_employee(employee_id: int):
    data = request.get_json(silent=True) or {}
    try:
        if not db.update_employee(employee_id, data):
            return jsonify(error="找不到員工"), 404
        return jsonify(next(row for row in db.employees() if row["id"] == employee_id))
    except Exception as exc:
        return jsonify(error="員工資料更新失敗：" + str(exc)), 500


@app.get("/api/organizations")
def organizations():
    try:
        return jsonify(db.organizations())
    except Exception as exc:
        return jsonify(error="處所資料庫查詢失敗：" + str(exc)), 503


@app.put("/api/organizations/<int:org_id>")
def update_organization(org_id: int):
    data = request.get_json(silent=True) or {}
    if not str(data.get("code", "")).strip() or not str(data.get("name", "")).strip():
        return jsonify(error="處所代碼與名稱必填"), 400
    try:
        payload={"code":str(data["code"]).strip().upper(),"name":str(data["name"]).strip(),"active":bool(data.get("active"))}
        if not db.update_organization(org_id,payload):
            return jsonify(error="找不到處所"),404
        return jsonify(next(row for row in db.organizations() if row["id"]==org_id))
    except Exception as exc:
        return jsonify(error="處所資料更新失敗："+str(exc)),500


@app.get("/api/products")
def products():
    try:
        dealer_id=request.args.get("dealerId",type=int)
        return jsonify(db.reportable_products(dealer_id) if dealer_id is not None else db.products())
    except Exception as exc:
        return jsonify(error="商品資料庫查詢失敗：" + str(exc)), 503


@app.post("/api/assignments")
def create_assignment():
    data = request.get_json(silent=True) or {}
    if not data.get("employee") or not data.get("effectiveAt"):
        return jsonify(error="異動對象與生效時間必填"), 400
    try:
        moved = db.create_assignment(data)
        return jsonify(id=int(datetime.now().timestamp()), createdAt=datetime.now().isoformat(timespec="seconds"), dealerCount=moved, **data), 201
    except Exception as exc:
        return jsonify(error="異動建立失敗：" + str(exc)), 500


@app.post("/api/changes")
def create_change():
    data=request.get_json(silent=True) or {}
    if not data.get('employeeId') or not data.get('effectiveAt'):
        return jsonify(error="異動員工與生效時間必填"),400
    try:return jsonify(db.create_change(data)),201
    except ValueError as exc:return jsonify(error=str(exc)),409
    except Exception as exc:return jsonify(error="異動建立失敗："+str(exc)),500


@app.get("/api/dealer-transfer-candidates")
def dealer_transfer_candidates():
    try:return jsonify(db.dealer_transfer_candidates())
    except Exception as exc:return jsonify(error="經銷商轉移清單載入失敗："+str(exc)),503


@app.post("/api/dealer-transfers")
def transfer_dealers():
    try:return jsonify(changed=db.transfer_dealers(request.get_json(silent=True) or {})),201
    except ValueError as exc:return jsonify(error=str(exc)),409
    except Exception as exc:return jsonify(error="經銷商轉移失敗："+str(exc)),500


@app.post("/api/dealer-transfers/retain")
def retain_dealers():
    try:return jsonify(changed=db.retain_dealers(request.get_json(silent=True) or {}))
    except ValueError as exc:return jsonify(error=str(exc)),409
    except Exception as exc:return jsonify(error="經銷商保留確認失敗："+str(exc)),500


@app.post("/api/visits")
def create_visit():
    data = request.get_json(silent=True) or {}
    user = session["user"]
    if user["type"] == "DEALER":
        data = {**data, "dealerId": user["dealerId"], "entrySourceType": "DEALER", "userAccountId": user["id"]}
    else:
        data = {**data, "entrySourceType": "EMPLOYEE", "userAccountId": user["id"]}
    if data.get("dealerId") is None or not data.get("details"):
        return jsonify(error="經銷商與至少一筆商品資料必填"), 400
    try:
        visit_id, report_time = db.create_visit(data)
        return jsonify(storeVisitId=visit_id, reportDateTime=report_time.isoformat(timespec="seconds")), 201
    except Exception as exc:
        return jsonify(error="巡店資料建立失敗：" + str(exc)), 500


@app.get("/api/visits")
def visit_list():
    try:
        user=session["user"]
        dealer_id=request.args.get("dealerId",type=int)
        if user["type"] == "DEALER":dealer_id=user["dealerId"]
        return jsonify(db.visits(employee_id=user.get("employeeId") if user["type"]=="EMPLOYEE" and request.args.get("mine") == "1" else None,
                                 dealer_id=dealer_id,account_id=user["id"],account_type=user["type"]))
    except Exception as exc:
        return jsonify(error="巡店紀錄查詢失敗："+str(exc)),503


@app.get("/api/report-details")
def report_details():
    try:return jsonify(db.report_details())
    except Exception as exc:return jsonify(error="實銷與陳列明細查詢失敗："+str(exc)),503


@app.get("/api/visits/<int:visit_id>")
def visit_detail(visit_id:int):
    try:
        item=db.visit_detail(visit_id)
        if item is None:return jsonify(error="找不到巡店回報"),404
        user=session["user"]
        if user["type"]=='DEALER' and item['dealerId'] != user['dealerId']:
            return jsonify(error="無權查看其他經銷商"),403
        item['canEdit']=item['recordStatus']=='ACTIVE' and datetime.now()<datetime.fromisoformat(item['editableUntil']) and ((user['type']=='EMPLOYEE' and item['entrySourceType']=='EMPLOYEE') or (user['type']=='DEALER' and item['createdByUserAccountId']==user['id']))
        return jsonify(item)
    except Exception as exc:return jsonify(error="巡店詳細查詢失敗："+str(exc)),503


@app.put("/api/visits/<int:visit_id>")
def update_visit(visit_id:int):
    data=request.get_json(silent=True) or {};user=session["user"]
    if not data.get("details"):return jsonify(error="至少保留一筆商品資料"),400
    try:
        db.update_visit(visit_id,data["details"],account_id=user["id"],account_type=user["type"])
        return jsonify(db.visit_detail(visit_id))
    except LookupError as exc:return jsonify(error=str(exc)),404
    except PermissionError as exc:return jsonify(error=str(exc)),403
    except Exception as exc:return jsonify(error="巡店資料修改失敗："+str(exc)),500


@app.get("/api/photo-tasks")
def photo_tasks():
    try:
        return jsonify(db.photo_tasks(session["user"].get("employeeId")))
    except Exception as exc:
        return jsonify(error="手機任務資料庫查詢失敗：" + str(exc)), 503


@app.post("/api/task-executions/<int:execution_id>/photos")
def upload_photo(execution_id: int):
    data = request.form if request.files else (request.get_json(silent=True) or {})
    description = str(data.get("description", "")).strip()
    if not description:
        return jsonify(error="照片說明必填"), 400
    try:
        sample_id=int(data.get("samplePhotoId")) if data.get("samplePhotoId") else None
        replace_photo_id=int(data.get("replacePhotoId")) if data.get("replacePhotoId") else None
        upload=request.files.get("photo")
        if upload:
            UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
            extension=Path(secure_filename(upload.filename or "photo.jpg")).suffix.lower()
            if extension not in {".jpg",".jpeg",".png",".webp"}:extension=".jpg"
            filename=secrets.token_hex(16)+extension
            upload.save(UPLOAD_DIR/filename)
            stored_path=f"uploads/task_photos/{filename}"
            photo_id,submitted_at=db.add_photo(execution_id,description,filename,stored_path,sample_id,session["user"].get("employeeId"),replace_photo_id)
        else:
            photo_id,submitted_at = db.add_photo(execution_id, description,sample_photo_id=sample_id,employee_id=session["user"].get("employeeId"),replace_photo_id=replace_photo_id)
            stored_path=None
        return jsonify(taskPhotoId=photo_id, executionId=execution_id, description=description,fileUrl=("/"+stored_path) if stored_path else None,
                       submittedAt=submitted_at.isoformat(timespec="seconds"),editUntil=(submitted_at+timedelta(hours=72)).isoformat(timespec="seconds")), 201
    except Exception as exc:
        status=403 if isinstance(exc,PermissionError) else 404 if isinstance(exc,LookupError) else 500
        return jsonify(error="照片資料建立失敗：" + str(exc)), status


@app.get("/uploads/task_photos/<path:filename>")
def task_photo_file(filename:str):
    return send_from_directory(UPLOAD_DIR,filename)


@app.post("/api/task-executions/<int:execution_id>/complete")
def complete_execution(execution_id: int):
    data = request.get_json(silent=True) or {}
    photo_count = int(data.get("photoCount", 0))
    raw_note = data.get("executionNote")
    note = "" if raw_note is None else str(raw_note).strip()
    if photo_count == 0 and not note:
        return jsonify(error="不拍照完成時必須填寫原因"), 400
    try:
        submitted_at = db.complete_execution(execution_id, note or None, session["user"].get("employeeId"))
        return jsonify(executionId=execution_id, completed=True, submittedAt=submitted_at.isoformat(timespec="seconds"), executionNote=note or None)
    except LookupError as exc:
        return jsonify(error=str(exc)), 404
    except PermissionError as exc:
        return jsonify(error=str(exc)),403
    except ValueError as exc:
        return jsonify(error=str(exc)),409
    except Exception as exc:
        return jsonify(error="任務完成資料更新失敗：" + str(exc)), 500


def lan_ip() -> str | None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LGSale server and Passkey bootstrap")
    parser.add_argument("command", nargs="?", choices=["serve", "invite"], default="serve")
    parser.add_argument("account_type", nargs="?", choices=["employee", "dealer"])
    parser.add_argument("owner_ref", nargs="?", help="EmployeeNo or DealerCode")
    args = parser.parse_args()
    if args.command == "invite":
        if not args.account_type or not args.owner_ref:
            parser.error("invite requires account_type and owner_ref")
        token = auth.create_invitation(args.account_type, args.owner_ref)
        print(f"{auth.ORIGIN}/register?token={token}")
        raise SystemExit(0)
    print(f"Desktop: http://127.0.0.1:{PORT}/")
    print(f"Mobile:  http://127.0.0.1:{PORT}/mobile")
    print(f"Dealer:  http://127.0.0.1:{PORT}/dealer")
    print(f"Photo:   http://127.0.0.1:{PORT}/photo")
    if address := lan_ip():
        print(f"LAN:     http://{address}:{PORT}/mobile")
    # 測試環境可透過 LGSALE_DEV_RELOAD=1 啟用程式碼自動重載。
    # 僅啟用 reloader，不開啟 Flask debugger，避免對外暴露除錯介面。
    dev_reload = os.getenv("LGSALE_DEV_RELOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=dev_reload,
    )
