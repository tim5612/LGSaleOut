"""Optional localhost-only UI harness. Synthetic data only; never connects to SQL.

Run: .venv/Scripts/python.exe tests/psi_ui_fixture_server.py
Open http://127.0.0.1:18198/psi. Production authentication is tested separately.
"""
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lgsale_psi as psi

app = Flask(__name__)


def fixture():
    dealers = [dict(id=i, code=f"TEST{i:04}", name=f"UI 測試門市 {i}", employeeId=(i-1)//27+1,
                    employee=f"測試業務 {(i-1)//27+1}", orgId=1, org="UI 測試區域") for i in range(1, 82)]
    products = [dict(id=i, code=f"MODEL-{i:04}", name=f"測試商品 {i}", category=f"分類 {(i-1)//95+1}",
                     subcategory="品類", price=None) for i in range(1, 286)]
    pairs = [(d["id"], p["id"]) for d in dealers for p in products if (d["id"]+p["id"]) % 7 == 0]
    month, _, _, cutoff = psi.period(request.args.get("month"), datetime(2026, 9, 14, 12))
    return dict(month=month, asOf=cutoff.isoformat(), fetchedAt="2026-09-14T12:00:00", currentMonth="2026-09",
                dealers=dealers, products=products, opening=[(d,p,10) for d,p in pairs],
                incoming=[(d,p,3,-1) for d,p in pairs], outgoing=[(d,p,2) for d,p in pairs],
                displays=[(d,p,2,datetime(2026, 7, 1)) for d,p in pairs if p%5], exclusions=[])


@app.get("/psi")
def page():
    return (psi.BASE / "LGSale_PSI.html").read_text(encoding="utf-8").replace("真實資料", "UI 測試資料（非真實資料）")


@app.get("/api/psi")
def report():
    return jsonify(psi.matrix(psi.build_report(fixture(), request.args), request.args.get("level", "dealer")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=18198, debug=False)
