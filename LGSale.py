"""LGSale local UI prototype server.

Run:
    python LGSale.py

Pages:
    http://127.0.0.1:8097/          Desktop task administration
    http://127.0.0.1:8097/mobile    Mobile store-visit interface
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
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session
import lgsale_db as db
import lgsale_auth as auth


BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.getenv("LGSALEOUT_PORT", "8098"))
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
    }
    if public or request.endpoint is None:
        return None
    user = session.get("user")
    if user is None:
        if request.path.startswith("/api/"):
            return jsonify(error="請先使用 Passkey 登入"), 401
        entry = "dealer" if request.path == "/mobile" else "employee"
        return redirect(f"/login/{entry}")
    dealer_allowed = {"/mobile", "/api/auth/me", "/api/auth/logout", "/api/dealers", "/api/products", "/api/visits"}
    if user["type"] == "DEALER" and request.path not in dealer_allowed:
        if request.path.startswith("/api/"):
            return jsonify(error="經銷商帳號無權存取此功能"), 403
        return redirect("/mobile")
    return None


@app.get("/login/<account_type>")
def login_page(account_type: str):
    if account_type not in {"employee", "dealer"}:
        return "Not found", 404
    if session.get("user"):
        return redirect("/mobile" if session["user"]["type"] == "DEALER" else "/")
    return send_from_directory(BASE_DIR, "LGSale_Auth.html")


@app.get("/register")
def register_page():
    return send_from_directory(BASE_DIR, "LGSale_Auth.html")


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


@app.get("/api/auth/me")
def auth_me():
    return jsonify(session["user"])


@app.post("/api/auth/logout")
def auth_logout():
    session.clear()
    return jsonify(loggedOut=True)


@app.get("/")
def desktop_page():
    return send_from_directory(BASE_DIR, "LGSale_UI_Desktop.html")


@app.get("/mobile")
def mobile_page():
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


@app.get("/api/dealers")
def dealers():
    try:
        user = session["user"]
        return jsonify(db.dealers(user["dealerId"] if user["type"] == "DEALER" else None))
    except Exception as exc:
        return jsonify(error="經銷商資料庫查詢失敗：" + str(exc)), 503


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
        return jsonify(db.products())
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


@app.get("/api/photo-tasks")
def photo_tasks():
    try:
        return jsonify(db.photo_tasks())
    except Exception as exc:
        return jsonify(error="手機任務資料庫查詢失敗：" + str(exc)), 503


@app.post("/api/task-executions/<int:execution_id>/photos")
def upload_photo(execution_id: int):
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    if not description:
        return jsonify(error="照片說明必填"), 400
    try:
        photo_id = db.add_photo(execution_id, description)
        return jsonify(taskPhotoId=photo_id, executionId=execution_id, description=description), 201
    except Exception as exc:
        return jsonify(error="照片資料建立失敗：" + str(exc)), 500


@app.post("/api/task-executions/<int:execution_id>/complete")
def complete_execution(execution_id: int):
    data = request.get_json(silent=True) or {}
    photo_count = int(data.get("photoCount", 0))
    note = str(data.get("executionNote", "")).strip()
    if photo_count == 0 and not note:
        return jsonify(error="不拍照完成時必須填寫原因"), 400
    try:
        submitted_at = db.complete_execution(execution_id, note or None)
        return jsonify(executionId=execution_id, completed=True, submittedAt=submitted_at.isoformat(timespec="seconds"), executionNote=note or None)
    except LookupError as exc:
        return jsonify(error=str(exc)), 404
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
    print(f"Photo:   http://127.0.0.1:{PORT}/photo")
    if address := lan_ip():
        print(f"LAN:     http://{address}:{PORT}/mobile")
    app.run(host="0.0.0.0", port=PORT, debug=False)
