"""LGSale local UI prototype server.

Run:
    python LGSale.py

Pages:
    http://127.0.0.1:8097/          Desktop task administration
    http://127.0.0.1:8097/mobile    Mobile store-visit interface
    http://127.0.0.1:8097/photo     Mobile task-photo interface

The server intentionally uses an in-memory demo store. It lets the three UI
prototypes share data without modifying LGSaleOut while the screens are being
discussed. Restarting the process restores the original demo data.
"""

from __future__ import annotations

import socket
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
PORT = 8097
app = Flask(__name__)
store_lock = threading.RLock()


TASKS: list[dict[str, Any]] = [
    {
        "id": 12,
        "code": "VT-202608-012",
        "title": "新機上市展示布置",
        "instruction": "依序拍攝跳跳牌、製冰盒與鏡面烤漆區域。",
        "validFrom": "2026-08-05",
        "dueDate": "2026-08-16",
        "recordStatus": "ACTIVE",
        "sampleStatus": "APPROVED",
        "sampleDealer": "光華家電",
        "samplePhotos": 3,
        "completed": 18,
        "total": 32,
        "photoCount": 54,
        "creator": "林怡君",
    },
    {
        "id": 9,
        "code": "VT-202608-009",
        "title": "夏季冰箱清潔檢查",
        "instruction": "清潔並拍攝冰箱內外觀，確認價格牌完整。",
        "validFrom": "2026-08-08",
        "dueDate": "2026-08-22",
        "recordStatus": "ACTIVE",
        "sampleStatus": "PENDING",
        "sampleDealer": None,
        "samplePhotos": 0,
        "completed": 4,
        "total": 28,
        "photoCount": 12,
        "creator": "陳美玲",
    },
    {
        "id": 31,
        "code": "VT-202607-031",
        "title": "門市端架陳列回報",
        "instruction": "拍攝端架全景及商品近照。",
        "validFrom": "2026-07-20",
        "dueDate": "2026-08-03",
        "recordStatus": "ACTIVE",
        "sampleStatus": "APPROVED",
        "sampleDealer": "三民電器",
        "samplePhotos": 2,
        "completed": 25,
        "total": 26,
        "photoCount": 50,
        "creator": "林怡君",
    },
    {
        "id": 26,
        "code": "VT-202607-026",
        "title": "冷氣新品 POP 更新",
        "instruction": "更新冷氣新品 POP 並拍攝完成畫面。",
        "validFrom": "2026-07-15",
        "dueDate": "2026-07-31",
        "recordStatus": "VOIDED",
        "sampleStatus": "APPROVED",
        "sampleDealer": "東區生活館",
        "samplePhotos": 3,
        "completed": 31,
        "total": 31,
        "photoCount": 93,
        "creator": "張志豪",
    },
]

DEALERS = [
    {"id": 1, "code": "TW002351001H", "name": "台北大同電器", "level": "A", "employee": "王小明", "lastVisit": "2026-07-22"},
    {"id": 2, "code": "TW002351018B", "name": "宏達家電", "level": "B", "employee": "王小明", "lastVisit": "2026-07-28"},
    {"id": 3, "code": "TW002351077C", "name": "信義生活館", "level": "C", "employee": "李小華", "lastVisit": "2026-08-08"},
    {"id": 4, "code": "TW002351102A", "name": "光華家電", "level": "A", "employee": "王小明", "lastVisit": "2026-08-06"},
]

PRODUCTS = [
    {"id": 1, "code": "GN-B372PL", "name": "雙門變頻冰箱", "category": "冰箱"},
    {"id": 2, "code": "WD-S13VDW", "name": "滾筒洗衣機", "category": "洗衣機"},
    {"id": 3, "code": "OLED65C4", "name": "65 吋智慧電視", "category": "電視"},
    {"id": 4, "code": "S13ETW", "name": "變頻冷氣", "category": "空調"},
]

PHOTO_TASKS = [
    {"executionId": 1201, "taskId": 12, "dealerId": 1, "title": "新機上市布置", "dealer": "台北大同電器", "dueDate": "2026-08-16", "sample": ["跳跳牌照片", "製冰盒照片", "鏡面烤漆照片"], "completed": False},
    {"executionId": 1202, "taskId": 9, "dealerId": 2, "title": "展示區檢查", "dealer": "宏達家電", "dueDate": "2026-08-22", "sample": [], "completed": False},
]

VISITS: list[dict[str, Any]] = []
PHOTOS: list[dict[str, Any]] = []
ASSIGNMENTS: list[dict[str, Any]] = []


def task_phase(task: dict[str, Any]) -> str:
    if task["recordStatus"] == "VOIDED":
        return "VOIDED"
    today = date.today().isoformat()
    if today < task["validFrom"]:
        return "UPCOMING"
    if today > task["dueDate"]:
        return "CLOSED"
    return "ACTIVE"


def task_payload(task: dict[str, Any]) -> dict[str, Any]:
    item = dict(task)
    item["phase"] = task_phase(task)
    item["progress"] = round(task["completed"] / task["total"] * 100) if task["total"] else 0
    return item


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
    return jsonify(status="ok", mode="prototype", serverTime=datetime.now().isoformat(timespec="seconds"))


@app.get("/api/tasks")
def tasks():
    with store_lock:
        return jsonify([task_payload(item) for item in TASKS])


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    required = ["title", "instruction", "validFrom", "dueDate"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify(error="缺少欄位：" + "、".join(missing)), 400
    if data["dueDate"] < data["validFrom"]:
        return jsonify(error="完成期限不得早於開始日期"), 400
    with store_lock:
        next_id = max(item["id"] for item in TASKS) + 1
        task = {
            "id": next_id,
            "code": f"VT-{datetime.now():%Y%m}-{next_id:03d}",
            "title": str(data["title"]).strip(),
            "instruction": str(data["instruction"]).strip(),
            "validFrom": data["validFrom"],
            "dueDate": data["dueDate"],
            "recordStatus": "ACTIVE",
            "sampleStatus": "NONE",
            "sampleDealer": None,
            "samplePhotos": 0,
            "completed": 0,
            "total": int(data.get("total", 32)),
            "photoCount": 0,
            "creator": "林怡君",
        }
        TASKS.insert(0, task)
        return jsonify(task_payload(task)), 201


@app.post("/api/tasks/<int:task_id>/toggle")
def toggle_task(task_id: int):
    with store_lock:
        task = next((item for item in TASKS if item["id"] == task_id), None)
        if task is None:
            return jsonify(error="找不到任務"), 404
        task["recordStatus"] = "ACTIVE" if task["recordStatus"] == "VOIDED" else "VOIDED"
        return jsonify(task_payload(task))


@app.get("/api/dealers")
def dealers():
    return jsonify(DEALERS)


@app.get("/api/products")
def products():
    return jsonify(PRODUCTS)


@app.post("/api/assignments")
def create_assignment():
    data = request.get_json(silent=True) or {}
    if not data.get("employee") or not data.get("effectiveAt"):
        return jsonify(error="異動對象與生效時間必填"), 400
    with store_lock:
        item = {"id": len(ASSIGNMENTS) + 1, "createdAt": datetime.now().isoformat(timespec="seconds"), **data}
        ASSIGNMENTS.append(item)
    return jsonify(item), 201


@app.post("/api/visits")
def create_visit():
    data = request.get_json(silent=True) or {}
    if not data.get("dealerId") or not data.get("details"):
        return jsonify(error="經銷商與至少一筆商品資料必填"), 400
    with store_lock:
        item = {"storeVisitId": len(VISITS) + 1, "reportDateTime": datetime.now().isoformat(timespec="seconds"), **data}
        VISITS.append(item)
    return jsonify(item), 201


@app.get("/api/photo-tasks")
def photo_tasks():
    return jsonify(PHOTO_TASKS)


@app.post("/api/task-executions/<int:execution_id>/photos")
def upload_photo(execution_id: int):
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    if not description:
        return jsonify(error="照片說明必填"), 400
    with store_lock:
        photo = {
            "taskPhotoId": len(PHOTOS) + 1,
            "executionId": execution_id,
            "description": description,
            "uploadedAt": datetime.now().isoformat(timespec="seconds"),
        }
        PHOTOS.append(photo)
    return jsonify(photo), 201


@app.post("/api/task-executions/<int:execution_id>/complete")
def complete_execution(execution_id: int):
    data = request.get_json(silent=True) or {}
    photo_count = int(data.get("photoCount", 0))
    note = str(data.get("executionNote", "")).strip()
    if photo_count == 0 and not note:
        return jsonify(error="不拍照完成時必須填寫原因"), 400
    with store_lock:
        task = next((item for item in PHOTO_TASKS if item["executionId"] == execution_id), None)
        if task is None:
            return jsonify(error="找不到任務執行資料"), 404
        task["completed"] = True
        task["submittedAt"] = datetime.now().isoformat(timespec="seconds")
        task["executionNote"] = note or None
    return jsonify(task)


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
    print(f"Desktop: http://127.0.0.1:{PORT}/")
    print(f"Mobile:  http://127.0.0.1:{PORT}/mobile")
    print(f"Photo:   http://127.0.0.1:{PORT}/photo")
    if address := lan_ip():
        print(f"LAN:     http://{address}:{PORT}/mobile")
    app.run(host="0.0.0.0", port=PORT, debug=False)
