"""Read-only PSI matrix built from official inventory and active visit facts.

No PSI table is persisted: reloading reflects visit edits/voids and new imports.
Absent display snapshots and absent opening baselines are not invented as zero.
"""
from __future__ import annotations

import re
import math
import hashlib
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException

import lgsale_db as db

bp = Blueprint("psi", __name__)
BASE = Path(__file__).resolve().parent
METRICS = ["陳列", "期初", "Sell In", "Sell Out", "期末", "可銷售"]
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
        next_key = end.strftime("%Y%m")
        cur.execute("""SELECT i.DealerId,i.ProductId,SUM(CAST(i.OpeningQuantity AS bigint))
            FROM dbo.MonthlyOpeningInventoryDetail i JOIN dbo.ImportBatch b ON b.ImportBatchId=i.ImportBatchId
            WHERE b.ImportType='OPENING_INVENTORY' AND b.ImportStatus='Official' AND b.DataMonth=%s
            GROUP BY i.DealerId,i.ProductId""", (next_key,))
        next_opening = list(cur.fetchall())
        cur.execute("""SELECT t.DealerId,t.ProductId,SUM(CAST(t.Quantity AS bigint))
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
                currentMonth=now.strftime("%Y-%m"), isCurrentMonth=month == now.strftime("%Y-%m"),
                isLastDay=month == now.strftime("%Y-%m") and now.date() == (end - timedelta(days=1)).date(),
                dealers=dealers, products=products,
                opening=opening, incoming=incoming, outgoing=outgoing, displays=displays,
                nextOpening=next_opening, exclusions=exclusions, displayPhotos=display_photos)


def ensure_month_end_rollover(employee_id: int | None) -> bool:
    """On the last calendar day, persist the calculated closing as next month's opening."""
    if not employee_id:
        return False
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cur.execute("SELECT SYSDATETIME()")
        now = cur.fetchone()[0]
        month, start, end, _ = period(None, now)
        if now.date() != (end - timedelta(days=1)).date():
            conn.rollback()
            return False
        source_key, next_key = month.replace("-", ""), end.strftime("%Y%m")
        cur.execute("""SELECT TOP 1 ImportBatchId FROM dbo.ImportBatch WITH (UPDLOCK,HOLDLOCK)
            WHERE ImportType='OPENING_INVENTORY' AND DataMonth=%s AND ImportStatus='Official'""", (next_key,))
        if cur.fetchone():
            conn.commit()
            return False
        cur.execute("""WITH opening AS (
                SELECT i.DealerId,i.ProductId,SUM(CAST(i.OpeningQuantity AS bigint)) Quantity
                FROM dbo.MonthlyOpeningInventoryDetail i JOIN dbo.ImportBatch b ON b.ImportBatchId=i.ImportBatchId
                WHERE b.ImportType='OPENING_INVENTORY' AND b.ImportStatus='Official' AND b.DataMonth=%s
                GROUP BY i.DealerId,i.ProductId),
            incoming AS (
                SELECT t.DealerId,t.ProductId,SUM(CAST(t.Quantity AS bigint)) Quantity
                FROM dbo.SellInTransaction t JOIN dbo.ImportBatch b ON b.ImportBatchId=t.ImportBatchId
                WHERE b.ImportType='SELL_IN' AND b.ImportStatus='Official' AND t.TransactionStatus='VALID'
                  AND t.ReviewStatus='APPROVED' AND t.InventoryEffectiveDate>=%s AND t.InventoryEffectiveDate<%s
                GROUP BY t.DealerId,t.ProductId),
            outgoing AS (
                SELECT v.DealerId,p.ProductId,SUM(CAST(p.SellOutQuantity AS bigint)) Quantity
                FROM dbo.StoreVisit v JOIN dbo.StoreVisitProductDetail p ON p.StoreVisitId=v.StoreVisitId
                WHERE v.RecordStatus='ACTIVE' AND p.SellOutDate>=%s AND p.SellOutDate<%s
                  AND p.SellOutQuantity IS NOT NULL
                GROUP BY v.DealerId,p.ProductId),
            pairs AS (SELECT DealerId,ProductId FROM opening UNION SELECT DealerId,ProductId FROM incoming)
            SELECT p.DealerId,p.ProductId,
                   COALESCE(o.Quantity,0)+COALESCE(i.Quantity,0)-COALESCE(s.Quantity,0)
            FROM pairs p LEFT JOIN opening o ON o.DealerId=p.DealerId AND o.ProductId=p.ProductId
            LEFT JOIN incoming i ON i.DealerId=p.DealerId AND i.ProductId=p.ProductId
            LEFT JOIN outgoing s ON s.DealerId=p.DealerId AND s.ProductId=p.ProductId
            ORDER BY p.DealerId,p.ProductId""",
            (source_key, start.date(), end.date(), start.date(), end.date()))
        rows = [(int(d), int(p), int(q)) for d, p, q in cur.fetchall()]
        if not rows:
            conn.rollback()
            return False
        marker = f"SYSTEM-MONTH-END:{source_key}:{next_key}"
        cur.execute("""INSERT dbo.ImportBatch
            (ImportType,DataMonth,OriginalFileName,StoredFilePath,FileHash,FileSize,ImportStatus,
             TotalRowCount,SuccessRowCount,ErrorRowCount,ImportedByEmployeeId)
            OUTPUT inserted.ImportBatchId
            VALUES('OPENING_INVENTORY',%s,%s,%s,%s,0,'Official',%s,%s,0,%s)""",
            (next_key, f"系統月結 {source_key}", f"system://month-end/{source_key}",
             hashlib.sha256(marker.encode()).hexdigest(), len(rows), len(rows), employee_id))
        batch_id = int(cur.fetchone()[0])
        cur.executemany("""INSERT dbo.MonthlyOpeningInventoryDetail
            (ImportBatchId,SourceRowNumber,DealerId,ProductId,OpeningQuantity)
            VALUES(%s,%s,%s,%s,%s)""",
            [(batch_id, index, dealer_id, product_id, quantity)
             for index, (dealer_id, product_id, quantity) in enumerate(rows, 1)])
        conn.commit()
        _SOURCE_CACHE.clear()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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


def metrics(fact, *, is_current_month=True, is_last_day=False):
    opening = fact.get("opening")
    incoming, outgoing = (fact.get(k, 0) for k in ("incoming", "outgoing"))
    display = fact.get("display")
    if is_current_month:
        closing = None if not is_last_day or opening is None else opening + incoming - outgoing
    else:
        closing = fact.get("nextOpening")
        outgoing = None if opening is None or closing is None else opening + incoming - closing
    available = None if display is None or outgoing is None else display + incoming - outgoing - display
    return [None if n is None else number(n) for n in (display, opening, incoming, outgoing, closing, available)]


def sum_values(values):
    values = list(values)
    result = []
    for i in range(len(METRICS)):
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


def build_report(source, filters, allowed_dealer_ids=None):
    facts = defaultdict(dict)
    for d, p, n in source["opening"]:
        quantity = Decimal(n)
        if quantity != 0:
            facts[int(d), int(p)]["opening"] = quantity
    # PSI membership starts with a non-zero official opening balance, or with
    # valid signed in-month Sale In activity for a product launched mid-month.
    for d, p, quantity in source["incoming"]:
        key = (int(d), int(p))
        incoming = Decimal(quantity)
        if incoming != 0:
            facts[key].setdefault("opening", Decimal(0))
            facts[key]["incoming"] = incoming
    active_pairs = set(facts)
    for d, p, n in source["outgoing"]:
        key = (int(d), int(p))
        if key in active_pairs:
            facts[key]["outgoing"] = Decimal(n)
    for d, p, n in source.get("nextOpening", []):
        key = (int(d), int(p))
        if key in facts:
            facts[key]["nextOpening"] = Decimal(n)
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
    dealers = [d for d in source["dealers"] if d["id"] in active_dealers and
               (allowed_dealer_ids is None or d["id"] in allowed_dealer_ids)]
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
            "values": metrics(fact, is_current_month=source.get("isCurrentMonth", True),
                              is_last_day=source.get("isLastDay", False)),
            "displayAt": fact.get("displayAt"), "displayPhoto":fact.get("displayPhoto"),
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
        notes=["Sell In 為帶正負號的淨進貨量；歷史 Sale Out = 期初 + Sell In − 期末。",
               "月中期末留白；月底以期初 + Sell In − 已回報 Sale Out 形成期末並建立下月期初。歷史期末取下月正式期初。",
               "可銷售依即時回報計算：(陳列 + Sell In) − Sale Out − 陳列。",
               "陳列取該經銷商截至日最後一次有效巡店的商品明細（可沿用前月），不是巡店累加；該次未填陳列時可銷售留白。",
               "PSI 納入當月正式非零期初，或當月有有效正／負 Sell In 的客戶／商品；僅有 Sell Out 或陳列不能單獨建立商品列。",
               "依截至日的區域與業務歸屬分組，套用有效 PSI 排除規則；售價待新增，零值留白。"])


@bp.before_request
def protect():
    # The app-wide permission check supplies g.access for employees and dealers.
    return None


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
    ensure_month_end_rollover(getattr(g.access, "employee_id", None))
    source = cached_source(request.args.get("month"), request.args.get("fresh") == "1")
    return jsonify(matrix(build_report(source, request.args, g.access.dealer_ids),
                          request.args.get("level", "dealer")))


@bp.get("/api/psi/export")
def export():
    import openpyxl
    from openpyxl.drawing.image import Image as ExcelImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    photo_mode = request.args.get("photos", "")
    if photo_mode not in {"", "thumbnail"}:
        raise ValueError("Excel 照片選項無效")
    ensure_month_end_rollover(getattr(g.access, "employee_id", None))
    result = matrix(build_report(cached_source(request.args.get("month")), request.args,
                                 g.access.dealer_ids), request.args.get("level", "dealer"))
    metric_count = len(METRICS)
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "PSI"
    sheet.append([f"PSI 月報 {result['month']}｜截至 {result['asOf']}｜單位：台"])
    sheet.append(["商品基本資料", "", "", ""] + [v for c in result["columns"] for v in [c["org"]] + [None]*(metric_count-1)])
    sheet.append([None]*4 + [v for c in result["columns"] for v in [c["employee"] + "｜" + c["title"].replace("\n", " ")] + [None]*(metric_count-1)])
    sheet.append(["大分類", "品類", "型號", "建議售價（待新增）"] + METRICS * len(result["columns"]))
    sheet.merge_cells(start_row=2, start_column=1, end_row=3, end_column=4)
    for i in range(len(result["columns"])):
        for r in (2, 3):
            sheet.merge_cells(start_row=r, start_column=5 + i*metric_count, end_row=r, end_column=4 + (i+1)*metric_count)
    for row in result["rows"]:
        sheet.append([row["category"], row["subcategory"], row["code"], None] + [v for group in row["values"] for v in group])
        excel_row = sheet.max_row
        for cell in sheet[sheet.max_row]:
            cell.number_format = '#,##0.###;-#,##0.###;;@'
            if row["kind"] != "product":
                cell.fill = PatternFill("solid", fgColor="D4E6C4" if row["kind"] == "total" else "E5EEDB")
                cell.font = Font(bold=True)
            elif cell.column > 4 and result["columns"][(cell.column-5)//metric_count]["total"]:
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
                sheet.add_image(picture, f"{get_column_letter(5 + group_index * metric_count)}{excel_row}")
                sheet.row_dimensions[excel_row].height = max(sheet.row_dimensions[excel_row].height or 15, 42)
    for row in sheet.iter_rows(min_row=1, max_row=4):
        for cell in row:
            cell.fill = PatternFill("solid", fgColor="DDE9F2")
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if isinstance(cell.value, str):
                cell.data_type = "s"
    for i, w in enumerate([18, 16, 24, 20] + [10]*metric_count*len(result["columns"]), 1):
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
