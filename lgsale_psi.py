"""Read-only PSI matrix built from official inventory and active visit facts.

No PSI table is persisted: reloading reflects visit edits/voids and new imports.
Absent display snapshots and absent opening baselines are not invented as zero.
"""
from __future__ import annotations

import re
import math
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file, send_from_directory, session
from werkzeug.exceptions import HTTPException

import lgsale_db as db

bp = Blueprint("psi", __name__)
BASE = Path(__file__).resolve().parent
METRICS = ["陳列", "期初", "Sell In", "退貨", "Sell Out", "期末", "可銷售"]
_SOURCE_CACHE = {}
_SOURCE_CACHE_LOCK = threading.RLock()
_SOURCE_CACHE_SECONDS = 8


def period(month, now):
    month = month or now.strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("月份格式必須為 YYYY-MM")
    try:
        start = datetime.strptime(month, "%Y-%m")
        end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    except ValueError:
        raise ValueError("月份無效") from None
    if start > now:
        raise ValueError("PSI 僅提供本月及歷史月份")
    as_of = min(now, end - timedelta(microseconds=1))
    return month, start, end, as_of


def load_source(month=None):
    with db.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SYSDATETIME()")
        now = cur.fetchone()[0]
        month, start, end, as_of = period(month, now)
        key = month.replace("-", "")
        # Assignment at the report cutoff: each dealer appears once, including unassigned dealers.
        cur.execute("""SELECT d.DealerId,d.DealerCode,d.DealerName,e.EmployeeId,e.EmployeeName,
                   o.OrgUnitId,o.OrgUnitName
            FROM dbo.Dealer d
            OUTER APPLY (SELECT TOP 1 a.EmployeeId FROM dbo.DealerAssignmentHistory a
                WHERE a.DealerId=d.DealerId AND a.StartDateTime<=%s
                  AND (a.EndDateTime IS NULL OR a.EndDateTime>%s)
                ORDER BY a.StartDateTime DESC,a.DealerAssignmentId DESC) a
            LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
            OUTER APPLY (SELECT TOP 1 h.OrgUnitId FROM dbo.EmployeeOrgAssignmentHistory h
                WHERE h.EmployeeId=e.EmployeeId AND h.StartDateTime<=%s
                  AND (h.EndDateTime IS NULL OR h.EndDateTime>%s)
                ORDER BY h.StartDateTime DESC,h.EmployeeOrgAssignmentId DESC) h
            LEFT JOIN dbo.OrganizationUnit o ON o.OrgUnitId=h.OrgUnitId
            ORDER BY o.OrgUnitName,e.EmployeeName,d.DealerCode""", (as_of,)*4)
        dealers = [dict(id=int(r[0]), code=r[1], name=r[2], employeeId=int(r[3] or 0),
                        employee=r[4] or "未指派業務", orgId=int(r[5] or 0), org=r[6] or "未歸屬區域")
                   for r in cur.fetchall()]
        cur.execute("SELECT ProductId,ProductCode,ProductName,CategoryLevel1,CategoryLevel2 FROM dbo.Product ORDER BY CategoryLevel1,CategoryLevel2,ProductCode")
        products = [dict(id=int(r[0]), code=r[1], name=r[2], category=r[3] or "未分類",
                         subcategory=r[4] or "未分類", price=None) for r in cur.fetchall()]
        cur.execute("""SELECT i.DealerId,i.ProductId,SUM(CAST(i.OpeningQuantity AS bigint))
            FROM dbo.MonthlyOpeningInventoryDetail i JOIN dbo.ImportBatch b ON b.ImportBatchId=i.ImportBatchId
            WHERE b.ImportType='OPENING_INVENTORY' AND b.ImportStatus='Official' AND b.DataMonth=%s
            GROUP BY i.DealerId,i.ProductId""", (key,))
        opening = list(cur.fetchall())
        cur.execute("""SELECT t.DealerId,t.ProductId,
                SUM(CASE WHEN t.Quantity>0 THEN t.Quantity ELSE 0 END),
                SUM(CASE WHEN t.Quantity<0 THEN t.Quantity ELSE 0 END)
            FROM dbo.SellInTransaction t JOIN dbo.ImportBatch b ON b.ImportBatchId=t.ImportBatchId
            WHERE b.ImportType='SELL_IN' AND b.ImportStatus='Official'
              AND t.TransactionStatus='VALID' AND t.ReviewStatus='APPROVED'
              AND t.InventoryEffectiveDate>=%s AND t.InventoryEffectiveDate<%s AND t.InventoryEffectiveDate<=%s
            GROUP BY t.DealerId,t.ProductId""", (start.date(), end.date(), as_of.date()))
        incoming = list(cur.fetchall())
        cur.execute("""SELECT v.DealerId,p.ProductId,SUM(CAST(p.SellOutQuantity AS bigint))
            FROM dbo.StoreVisit v JOIN dbo.StoreVisitProductDetail p ON p.StoreVisitId=v.StoreVisitId
            WHERE v.RecordStatus='ACTIVE' AND v.ReportDateTime<=%s
              AND p.SellOutDate>=%s AND p.SellOutDate<%s AND p.SellOutDate<=%s
              AND p.SellOutQuantity IS NOT NULL
            GROUP BY v.DealerId,p.ProductId""", (now, start.date(), end.date(), as_of.date()))
        outgoing = list(cur.fetchall())
        cur.execute("""WITH latest_visits AS (
            SELECT v.StoreVisitId,v.DealerId,v.ReportDateTime,
                ROW_NUMBER() OVER (PARTITION BY v.DealerId
                    ORDER BY v.ReportDateTime DESC,v.StoreVisitId DESC) AS rn
            FROM dbo.StoreVisit v
            WHERE v.RecordStatus='ACTIVE' AND v.ReportDateTime<=%s)
            SELECT v.DealerId,p.ProductId,p.DisplayQuantity,v.ReportDateTime
            FROM latest_visits v JOIN dbo.StoreVisitProductDetail p ON p.StoreVisitId=v.StoreVisitId
            WHERE v.rn=1 AND p.DisplayQuantity IS NOT NULL""", (as_of,))
        displays = list(cur.fetchall())
        cur.execute("""SELECT ProductId,DealerId FROM dbo.OpeningInventoryProductExclusion
            WHERE EffectiveFromMonth<=%s AND (EffectiveToMonth IS NULL OR EffectiveToMonth>=%s)""", (key, key))
        exclusions = list(cur.fetchall())
        cur.execute("""SELECT p.DealerId,p.ProductId,p.DisplayPhotoId,p.CapturedAt,
                   COALESCE(e.EmployeeName,d.DealerName,'—')
            FROM dbo.DealerProductDisplayPhoto p JOIN dbo.UserAccount a ON a.UserAccountId=p.UploadedByUserAccountId
            LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId LEFT JOIN dbo.Dealer d ON d.DealerId=a.DealerId
            WHERE p.DataMonth=%s AND p.RecordStatus='ACTIVE'""",(key,))
        display_photos=list(cur.fetchall())
    return dict(month=month, asOf=as_of.isoformat(timespec="seconds"), fetchedAt=now.isoformat(timespec="seconds"),
                currentMonth=now.strftime("%Y-%m"), dealers=dealers, products=products,
                opening=opening, incoming=incoming, outgoing=outgoing, displays=displays,
                exclusions=exclusions, displayPhotos=display_photos)


def cached_source(month=None, fresh=False):
    """Briefly reuse raw facts while a user changes filters; explicit refresh bypasses it."""
    key = month or "CURRENT"
    now = time.monotonic()
    with _SOURCE_CACHE_LOCK:
        cached = _SOURCE_CACHE.get(key)
        if not fresh and cached and now - cached[0] < _SOURCE_CACHE_SECONDS:
            return cached[1]
    result = load_source(month)
    with _SOURCE_CACHE_LOCK:
        _SOURCE_CACHE[key] = (time.monotonic(), result)
        # Only current/recent filter activity is useful; avoid unbounded month keys.
        if len(_SOURCE_CACHE) > 6:
            oldest = min(_SOURCE_CACHE, key=lambda item: _SOURCE_CACHE[item][0])
            _SOURCE_CACHE.pop(oldest, None)
    return result


def number(value):
    value = Decimal(value)
    return int(value) if value == value.to_integral_value() else float(value)


def metrics(fact):
    opening = fact.get("opening")
    incoming, returned, outgoing = (fact.get(k, 0) for k in ("incoming", "returned", "outgoing"))
    display = fact.get("display")
    closing = None if opening is None else opening + incoming + returned - outgoing
    available = None if closing is None or display is None else closing - display
    return [None if n is None else number(n) for n in (display, opening, incoming, returned, outgoing, closing, available)]


def sum_values(values):
    values = list(values)
    result = []
    for i in range(7):
        column = [v[i] for v in values]
        if not column or any(v is None for v in column):
            result.append(None)
            continue
        total = math.fsum(column)
        result.append(int(total) if total.is_integer() else round(total, 3))
    return result


def matrix(report, level="dealer"):
    if level not in {"dealer", "employee", "org", "company"}:
        raise ValueError("顯示層級無效")
    groups = {}
    for d in report["dealers"]:
        groups.setdefault((d["orgId"], d["employeeId"]), []).append(d)
    columns = []

    def column(ds, title, total=False, org=None, employee=None):
        columns.append(dict(dealerIds=[d["id"] for d in ds], title=title, total=total,
                            org=org or ds[0]["org"], employee=employee or ds[0]["employee"]))

    if level in {"dealer", "employee"}:
        for ds in groups.values():
            if level == "dealer":
                for d in ds:
                    column([d], d["code"] + "\n" + d["name"])
            column(ds, ds[0]["employee"] + " / TTL", True)
    elif level == "org":
        orgs = {}
        for d in report["dealers"]:
            orgs.setdefault(d["orgId"], []).append(d)
        for ds in orgs.values():
            column(ds, ds[0]["org"] + " / TTL", True, employee="區域合計")
    if report["dealers"]:
        column(report["dealers"], "篩選範圍合計 / TTL", True, org="篩選範圍", employee="全部所選客戶")
    rows = []
    category_rows = []
    last_category = None

    def subtotal(category, category_rows):
        if not category_rows:
            return
        rows.append(dict(kind="subtotal", category=category, subcategory="", code=f"{len(category_rows)} 個型號", price=None,
                         values=[sum_values(r["values"][i] for r in category_rows) for i in range(len(columns))]))

    product_rows = []
    for row in report["rows"]:
        if last_category != row["category"]:
            subtotal(last_category, category_rows)
            category_rows = []
            last_category = row["category"]
        values = []
        for c in columns:
            present = [row["cells"][str(d)]["values"] for d in c["dealerIds"] if str(d) in row["cells"]]
            values.append(present[0] if len(present) == 1 else sum_values(present))
        photos=[]
        for c in columns:
            present=[row["cells"][str(d)].get("displayPhoto") for d in c["dealerIds"] if str(d) in row["cells"]]
            photos.append(present[0] if not c["total"] and len(present)==1 else None)
        item = dict(kind="product", category=row["category"], subcategory=row["subcategory"], code=row["code"],
                    name=row["name"], price=None, values=values, photos=photos)
        rows.append(item)
        category_rows.append(item)
        product_rows.append(item)
    subtotal(last_category, category_rows)
    if product_rows:
        rows.append(dict(kind="total", category="總計", subcategory="", code=f"{len(product_rows)} 個型號", price=None,
                         values=[sum_values(r["values"][i] for r in product_rows) for i in range(len(columns))]))
    return {k: v for k, v in report.items() if k not in {"rows", "dealers"}} | dict(
        columns=columns, rows=rows, productCount=len(product_rows), dealerCount=len(report["dealers"]), level=level)


def build_report(source, filters):
    facts = defaultdict(dict)
    for d, p, n in source["opening"]:
        quantity = Decimal(n)
        if quantity != 0:
            facts[int(d), int(p)]["opening"] = quantity
    # PSI membership starts with a non-zero official opening balance, or with
    # valid in-month Sale In/return activity for a product launched mid-month.
    for d, p, pos, neg in source["incoming"]:
        key = (int(d), int(p))
        incoming, returned = Decimal(pos), Decimal(neg)
        if incoming != 0 or returned != 0:
            facts[key].setdefault("opening", Decimal(0))
            facts[key].update(incoming=Decimal(pos), returned=Decimal(neg))
    active_pairs = set(facts)
    for d, p, n in source["outgoing"]:
        key = (int(d), int(p))
        if key in active_pairs:
            facts[key]["outgoing"] = Decimal(n)
    for d, p, n, stamp in source["displays"]:
        key = (int(d), int(p))
        if key in active_pairs:
            facts[key].update(display=Decimal(n), displayAt=stamp.isoformat(timespec="seconds"))
    for d,p,photo_id,captured_at,uploader in source.get("displayPhotos",[]):
        key=(int(d),int(p))
        if key in active_pairs:
            facts[key]["displayPhoto"]={"id":int(photo_id),"capturedAt":captured_at.isoformat(timespec="seconds"),"uploader":uploader}
    global_ex = {int(p) for p, d in source["exclusions"] if d is None}
    pair_ex = {(int(d), int(p)) for p, d in source["exclusions"] if d is not None}
    excluded = sum(p in global_ex or (d, p) in pair_ex for d, p in facts)
    excluded_products = sum(p["id"] in global_ex for p in source["products"])
    facts = {k: v for k, v in facts.items() if k[1] not in global_ex and k not in pair_ex}
    active_dealers = {d for d, _ in facts}
    dealers = [d for d in source["dealers"] if d["id"] in active_dealers]
    fact_products = {pid for _, pid in facts}
    options = dict(orgs=list({d["orgId"]: {"id": d["orgId"], "name": d["org"]} for d in dealers}.values()),
                   employees=list({d["employeeId"]: {"id": d["employeeId"], "name": d["employee"], "orgId": d["orgId"]} for d in dealers}.values()),
                   categories=sorted({p["category"] for p in source["products"] if p["id"] in fact_products}))
    for field, key in (("org", "orgId"), ("employee", "employeeId")):
        if filters.get(field, "") != "":
            try:
                ident = int(filters[field])
            except (ValueError, TypeError):
                raise ValueError("區域與業務篩選必須是有效編號") from None
            dealers = [d for d in dealers if d[key] == ident]
    q = filters.get("q", "").strip().casefold()
    products = source["products"]
    if filters.get("category"):
        products = [p for p in products if p["category"] == filters["category"]]
    if q:
        # Search matches model OR dealer; retain the rectangular union without unrelated cells.
        matched_d = {d["id"] for d in dealers if q in (d["code"] + " " + d["name"]).casefold()}
        matched_p = {p["id"] for p in products if q in (p["code"] + " " + p["name"]).casefold()}
        facts = {k: v for k, v in facts.items() if k[0] in matched_d or k[1] in matched_p}
    ds, ps = {d["id"] for d in dealers}, {p["id"] for p in products}
    facts = {k: v for k, v in facts.items() if k[0] in ds and k[1] in ps}
    dealers = [d for d in dealers if any(k[0] == d["id"] for k in facts)]
    cells_by_product = defaultdict(dict)
    for (dealer_id, product_id), fact in facts.items():
        cells_by_product[product_id][str(dealer_id)] = {
            "values": metrics(fact), "displayAt": fact.get("displayAt"), "displayPhoto":fact.get("displayPhoto"),
            "sellOutReported": "outgoing" in fact}
    rows = []
    for p in products:
        values = cells_by_product.get(p["id"], {})
        if values:
            rows.append({**p, "cells": values})
    return {k: source[k] for k in ("month", "asOf", "fetchedAt", "currentMonth")} | dict(
        dealers=dealers, rows=rows, options=options, metrics=METRICS,
        quality=dict(missingOpening=sum("opening" not in f for f in facts.values()),
                     missingDisplay=sum("display" not in f for f in facts.values()),
                     sellOutReportedPairs=sum("outgoing" in f for f in facts.values()),
                     excludedPairs=excluded, excludedProducts=excluded_products),
        notes=["期末 = 期初 + Sell In + 退貨（負數）− Sell Out；可銷售 = 期末 − 陳列。",
               "實銷按 SellOutDate 加總有效回報（含事後補登與修改）；未回報不代表實際無銷售。期末為依已登錄資料推算。",
               "陳列取該經銷商截至日最後一次有效巡店的商品明細（可沿用前月），不是巡店累加；該次未填陳列時可銷售留白。",
               "PSI 納入當月正式非零期初，或當月有有效 Sell In／退貨的客戶／商品；僅有 Sell Out 或陳列不能單獨建立商品列。",
               "依截至日的區域與業務歸屬分組，套用有效 PSI 排除規則；售價待新增，零值留白。"])


@bp.before_request
def protect():
    user = session.get("user", {})
    if user.get("type") != "EMPLOYEE" or not user.get("employeeId"):
        return jsonify(error="僅員工帳號可使用 PSI 月報"), 403


@bp.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.errorhandler(Exception)
def error(exc):
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.description), exc.code
    if isinstance(exc, ValueError):
        return jsonify(error=str(exc)), 400
    current_app.logger.exception("PSI query failed")
    return jsonify(error="PSI 資料讀取失敗，請稍後重新整理或聯絡管理人員"), 500


@bp.get("/psi")
def page():
    response = send_from_directory(BASE, "LGSale_PSI.html", max_age=0)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@bp.get("/api/psi")
def report():
    source = cached_source(request.args.get("month"), request.args.get("fresh") == "1")
    return jsonify(matrix(build_report(source, request.args), request.args.get("level", "dealer")))


@bp.get("/api/psi/export")
def export():
    import openpyxl
    from openpyxl.drawing.image import Image as ExcelImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    photo_mode = request.args.get("photos", "")
    if photo_mode not in {"", "thumbnail"}:
        raise ValueError("Excel 照片選項無效")
    result = matrix(build_report(cached_source(request.args.get("month")), request.args), request.args.get("level", "dealer"))
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "PSI"
    sheet.append([f"PSI 月報 {result['month']}｜截至 {result['asOf']}｜單位：台"])
    sheet.append(["商品基本資料", "", "", ""] + [v for c in result["columns"] for v in [c["org"]] + [None]*6])
    sheet.append([None]*4 + [v for c in result["columns"] for v in [c["employee"] + "｜" + c["title"].replace("\n", " ")] + [None]*6])
    sheet.append(["大分類", "品類", "型號", "建議售價（待新增）"] + METRICS * len(result["columns"]))
    sheet.merge_cells(start_row=2, start_column=1, end_row=3, end_column=4)
    for i in range(len(result["columns"])):
        for r in (2, 3):
            sheet.merge_cells(start_row=r, start_column=5 + i*7, end_row=r, end_column=11 + i*7)
    for row in result["rows"]:
        sheet.append([row["category"], row["subcategory"], row["code"], None] + [v for group in row["values"] for v in group])
        excel_row = sheet.max_row
        for cell in sheet[sheet.max_row]:
            cell.number_format = '#,##0.###;-#,##0.###;;@'
            if row["kind"] != "product":
                cell.fill = PatternFill("solid", fgColor="D4E6C4" if row["kind"] == "total" else "E5EEDB")
                cell.font = Font(bold=True)
            elif cell.column > 4 and result["columns"][(cell.column-5)//7]["total"]:
                cell.fill = PatternFill("solid", fgColor="FFF3E4")
            # Database labels must remain literal text, not executable spreadsheet formulas.
            if isinstance(cell.value, str):
                cell.data_type = "s"
        if photo_mode == "thumbnail" and row["kind"] == "product":
            for group_index, photo in enumerate(row.get("photos", [])):
                if not photo:
                    continue
                item = db.display_photo_file(int(photo["id"]), "thumbnail")
                target = (BASE / item["path"]).resolve() if item else None
                photo_root = (BASE / "uploads" / "display_photos").resolve()
                if target is None or photo_root not in target.parents or not target.is_file():
                    continue
                picture = ExcelImage(str(target))
                picture.width = picture.height = 48
                sheet.add_image(picture, f"{get_column_letter(5 + group_index * 7)}{excel_row}")
                sheet.row_dimensions[excel_row].height = max(sheet.row_dimensions[excel_row].height or 15, 42)
    for row in sheet.iter_rows(min_row=1, max_row=4):
        for cell in row:
            cell.fill = PatternFill("solid", fgColor="DDE9F2")
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if isinstance(cell.value, str):
                cell.data_type = "s"
    for i, w in enumerate([18, 16, 24, 20] + [10]*7*len(result["columns"]), 1):
        sheet.column_dimensions[get_column_letter(i)].width = w
    sheet.row_dimensions[3].height = 36
    sheet.freeze_panes = "E5"
    note = book.create_sheet("計算說明")
    for line in result["notes"]:
        note.append([line])
    note.append(["空白可能為零值或資料未齊；缺少期初或陳列時，相關合計也留白，不以部分資料冒充完整庫存。"])
    note.append(["照片匯出：" + ("已在客戶明細的陳列欄插入固定尺寸縮圖；原圖請回到 PSI 點擊相機圖示查看。" if photo_mode else "本檔未插入照片，以維持較小檔案。")])
    note.column_dimensions["A"].width = 120
    output = BytesIO()
    book.save(output)
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=f"PSI-{result['month']}.xlsx")
