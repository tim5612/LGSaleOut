import unittest
import tempfile
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
from flask import Flask, g, jsonify, session
from types import SimpleNamespace
from PIL import Image

import lgsale_psi as psi


def source():
    return dict(month="2026-09", currentMonth="2026-09", asOf="2026-09-14T12:00:00", fetchedAt="2026-09-14T12:00:00",
                dealers=[dict(id=i, code=f"D{i}", name=f"Dealer {i}", employeeId=i, employee=f"E{i}", orgId=1, org="Region") for i in (1, 2)],
                products=[dict(id=1, code="P1", name="Product 1", category="HA", subcategory="Fridge", price=None),
                          dict(id=2, code="P2", name="Product 2", category="TV", subcategory="OLED", price=None)],
                opening=[(1, 1, 10), (2, 1, 5), (1, 2, 2)], incoming=[(1, 1, Decimal("2"))],
                outgoing=[(1, 1, 4)], displays=[(1, 1, 2, datetime(2026, 8, 30)), (2, 1, 1, datetime(2026, 9, 1)), (1, 2, 1, datetime(2026, 9, 1))], exclusions=[],
                displayPhotos=[(1,1,91,datetime(2026,9,2,10),"E1","主要店面")],
                averageFrom="2026-06", averageTo="2026-09", averageMonths=4,
                averageSales=[(1,1,40),(2,1,20),(1,2,8)])


class CalculationTests(unittest.TestCase):
    @patch("lgsale_psi.db.connect")
    def test_sql_periods_and_snapshot_contract(self, connect):
        cur = MagicMock()
        connect.return_value.__enter__.return_value.cursor.return_value = cur
        now = datetime(2026, 9, 14, 12)
        cur.fetchone.return_value = (now,)
        cur.fetchall.side_effect = [[], [], [], [], [], [], [], [], [], []]
        psi.load_source("2026-08")
        calls = cur.execute.call_args_list
        dealer_query = next(c for c in calls if "FROM dbo.Dealer d" in c.args[0])
        self.assertIn("o.OrgUnitId,e.EmployeeId,d.DealerCode", dealer_query.args[0])
        self.assertNotIn("ORDER BY o.OrgUnitName", dealer_query.args[0])
        incoming = next(c for c in calls if "FROM dbo.SellInTransaction" in c.args[0])
        self.assertIn("t.TransactionStatus='VALID'", incoming.args[0])
        self.assertIn("t.ReviewStatus='APPROVED'", incoming.args[0])
        self.assertIn("b.ImportStatus='Official'", incoming.args[0])
        self.assertIn("SUM(CAST(t.Quantity AS bigint))", incoming.args[0])
        self.assertNotIn("CASE WHEN t.Quantity", incoming.args[0])
        outgoing = next(c for c in calls if "SUM(CAST(p.SellOutQuantity" in c.args[0])
        self.assertIn("v.RecordStatus='ACTIVE'", outgoing.args[0])
        self.assertEqual(outgoing.args[1][0], now)  # late-entered August sales still count
        self.assertEqual(outgoing.args[1][1].isoformat(), "2026-08-01")
        self.assertEqual(outgoing.args[1][2].isoformat(), "2026-09-01")
        snapshot = next(c for c in calls if "WITH latest_visits" in c.args[0])
        self.assertIn("PARTITION BY v.DealerLocationId", snapshot.args[0])
        self.assertIn("WHERE v.rn=1", snapshot.args[0])
        self.assertEqual(snapshot.args[1][0].date().isoformat(), "2026-08-31")
        averages = next(c for c in calls if "WITH eligible AS" in c.args[0])
        self.assertIn("MonthlyOpeningInventoryDetail", averages.args[0])
        self.assertIn("SellInTransaction", averages.args[0])
        self.assertIn("SellOutQuantity", averages.args[0])

    def test_balance_signed_sellin_and_display(self):
        r = psi.build_report(source(), {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [2, 10, 2, 4, 8, 6, '10 / 14'])
        self.assertTrue(r["rows"][0]["cells"]["1"]["displayAt"].startswith("2026-08"))
        self.assertEqual(r["rows"][0]["cells"]["1"]["displayPhoto"]["id"],91)

    def test_negative_sellin_stays_in_single_sellin_metric(self):
        s = source(); s["incoming"] = [(1, 1, Decimal("-2"))]
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [2, 10, -2, 4, 4, 2, '10 / 18'])

    def test_last_day_shows_calculated_closing(self):
        s = source(); s["isCurrentMonth"] = True; s["isLastDay"] = True
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [2, 10, 2, 4, 8, 6, '10 / 14'])

    def test_historical_closing_uses_recorded_flows_not_next_opening(self):
        s = source(); s["isCurrentMonth"] = False; s["isLastDay"] = False
        s["nextOpening"] = [(1, 1, 7)]
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [2, 10, 2, 4, 8, 6, '10 / 14'])

    def test_no_snapshot_is_unknown_not_zero(self):
        s = source(); s["displays"] = []
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [None, 10, 2, 4, 8, 8, '10 / 12'])
        self.assertEqual(r["quality"]["missingDisplay"], 3)

    def test_missing_display_is_zero_for_available_when_closing_exists(self):
        s = source(); s["displays"] = []; s["isCurrentMonth"] = True; s["isLastDay"] = True
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [None, 10, 2, 4, 8, 8, '10 / 12'])

    def test_salein_without_opening_creates_psi_with_zero_baseline(self):
        s = source(); s["opening"] = []
        r = psi.build_report(s, {})
        self.assertEqual(len(r["rows"]), 1)
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [2, 0, 2, 4, -2, -4, '10 / 24'])
        self.assertEqual([d["id"] for d in r["dealers"]], [1])

    def test_opening_only_still_calculates_closing_and_available(self):
        r = psi.build_report(source(), {})
        self.assertEqual(r["rows"][0]["cells"]["2"]["values"], [1, 5, 0, 0, 5, 4, '5 / 6'])

    def test_sellout_only_creates_psi_row_with_zero_baseline(self):
        s = source(); s["opening"] = []; s["incoming"] = []; s["outgoing"] = [(1,1,3)]
        s["displays"] = []
        r = psi.build_report(s, {})
        self.assertEqual(len(r["rows"]), 1)
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"], [None, 0, 0, 3, -3, -3, '10 / 23'])

    def test_zero_opening_without_salein_does_not_create_psi_rows(self):
        s = source()
        s["opening"] = [(1, 1, 0)]
        s["incoming"] = []
        s["outgoing"] = []
        r = psi.build_report(s, {})
        self.assertEqual(r["rows"], [])
        self.assertEqual(r["dealers"], [])

    def test_explicit_zero_and_negative_stock(self):
        self.assertEqual(psi.metrics(dict(opening=0, display=0, outgoing=2)), [0, 0, 0, 2, -2, -2, None])

    def test_global_and_dealer_exclusions(self):
        s = source(); s["exclusions"] = [(2, None), (1, 2)]
        r = psi.build_report(s, {})
        self.assertEqual(len(r["rows"]), 1)
        self.assertEqual([d["id"] for d in r["dealers"]], [1])
        self.assertEqual(r["quality"]["excludedPairs"], 2)

    def test_filters_and_no_duplicate_business_totals(self):
        r = psi.matrix(psi.build_report(source(), {}))
        self.assertEqual(len(r["columns"]), 5)  # 2 dealers + 2 sales totals + one scope total
        self.assertEqual(r["rows"][-1]["values"][-1], [4, 17, 2, 4, 15, 11, None])
        filtered = psi.matrix(psi.build_report(source(), {"employee": "1", "category": "HA"}))
        self.assertEqual(filtered["rows"][-1]["values"][-1], [2, 10, 2, 4, 8, 6, None])
        self.assertEqual(filtered["dealerCount"], 1)

    def test_region_order_uses_org_unit_id_not_name(self):
        s = source()
        s["dealers"] = [
            dict(id=2, code="D2", name="Dealer 2", employeeId=2, employee="E2", orgId=20, org="AC Team"),
            dict(id=1, code="D1", name="Dealer 1", employeeId=1, employee="E1", orgId=10, org="嘉南營銷處"),
        ]
        report = psi.build_report(s, {})
        self.assertEqual([item["id"] for item in report["options"]["orgs"]], [10, 20])
        dealer_columns = [column for column in psi.matrix(report)["columns"] if not column["total"]]
        self.assertEqual([column["org"] for column in dealer_columns], ["嘉南營銷處", "AC Team"])

    def test_partial_totals_remain_unknown(self):
        s = source(); s["displays"] = s["displays"][:1]
        r = psi.matrix(psi.build_report(s, {}))
        self.assertEqual(r["rows"][-1]["values"][-1], [None, 17, 2, 4, 15, 13, None])

    def test_search_and_empty(self):
        self.assertEqual(len(psi.build_report(source(), {"q": "p2"})["rows"]), 1)
        self.assertEqual(len(psi.build_report(source(), {"q": "dealer 2"})["dealers"]), 1)
        self.assertEqual(psi.matrix(psi.build_report(source(), {"q": "absent"}))["rows"], [])

    def test_all_levels_share_same_total(self):
        report = psi.build_report(source(), {})
        results = [psi.matrix(report, level) for level in ("dealer", "employee", "org", "company")]
        self.assertEqual([len(r["columns"]) for r in results], [5, 3, 2, 1])
        self.assertTrue(all(r["rows"][-1]["values"][-1] == results[0]["rows"][-1]["values"][-1] for r in results))
        with self.assertRaises(ValueError): psi.matrix(report, "bad")

    def test_decimal_precision(self):
        self.assertEqual(psi.sum_values([[0, 0, .1, 0, .1, .1, None], [0, 0, .2, 0, .2, .2, None]]), [0, 0, .3, 0, .3, .3, None])

    def test_month_boundaries(self):
        now = datetime(2026, 9, 14, 10)
        self.assertEqual(psi.period(None, now)[0], "2026-09")
        self.assertEqual(psi.period("2025-12", now)[2], datetime(2026, 1, 1))
        self.assertEqual(psi.period("2024-02", now)[3].day, 29)
        for invalid in ("2026-13", "2026-9", "2026-10", "9999-12", "x"):
            with self.assertRaises(ValueError): psi.period(invalid, now)

    def test_average_period_includes_report_month(self):
        start, end = psi.average_period(datetime(2026, 9, 1))
        self.assertEqual((start, end), (datetime(2026, 6, 1), datetime(2026, 10, 1)))
        self.assertEqual(psi.average_period(datetime(2026, 9, 1), "2026-01"),
                         (datetime(2026, 1, 1), datetime(2026, 10, 1)))
        with self.assertRaises(ValueError):
            psi.average_period(datetime(2026, 9, 1), "2026-10")

    def test_replenishment_uses_monthly_averages_and_rounds_shortage_up(self):
        s = source(); s["isCurrentMonth"] = True; s["isLastDay"] = True
        s["averageSales"] = [(1,1,41),(2,1,16)]
        r = psi.build_report(s, {})
        # Dealer monthly average ceil(41/4)=11; WOS 8 means two months, so 22-6=16.
        self.assertEqual(r["rows"][0]["cells"]["1"]["values"][-1], "11 / 16")
        self.assertEqual(psi.build_report(s, {"wos":"4"})["rows"][0]["cells"]["1"]["values"][-1], "11 / 5")
        self.assertEqual(psi.build_report(s, {"wos":"12"})["rows"][0]["cells"]["1"]["values"][-1], "11 / 27")
        with self.assertRaises(ValueError):
            psi.build_report(s, {"wos":"6"})

    @patch("lgsale_psi.db.connect")
    def test_month_end_rollover_creates_next_opening_once(self, connect):
        conn, cur = MagicMock(), MagicMock()
        connect.return_value = conn; conn.cursor.return_value = cur
        cur.fetchone.side_effect = [
            (datetime(2026, 9, 30, 23, 50),),
            None,
            (88,),
        ]
        cur.fetchall.return_value = [(1, 1, 8), (1, 2, -2)]
        self.assertTrue(psi.ensure_month_end_rollover(7))
        inserted = cur.executemany.call_args.args[1]
        self.assertEqual(inserted, [(88, 1, 1, 1, 8), (88, 2, 1, 2, -2)])
        conn.commit.assert_called_once()

    @patch("lgsale_psi.db.connect")
    def test_month_end_rollover_skips_when_next_opening_exists(self, connect):
        conn, cur = MagicMock(), MagicMock()
        connect.return_value = conn; conn.cursor.return_value = cur
        cur.fetchone.side_effect = [(datetime(2026, 9, 30, 12),), (55,)]
        self.assertFalse(psi.ensure_month_end_rollover(7))
        cur.executemany.assert_not_called()
        conn.commit.assert_called_once()


class RouteTests(unittest.TestCase):
    def setUp(self):
        psi._SOURCE_CACHE.clear()
        self.app = Flask(__name__)
        self.app.secret_key = "unit-test-only"
        self.app.register_blueprint(psi.bp)
        @self.app.before_request
        def permission_fixture():
            user = session.get("user")
            if not user:
                return jsonify(error="請先登入"), 403
            g.access = SimpleNamespace(dealer_ids={1} if user["type"] == "DEALER" else {1, 2})
        self.client = self.app.test_client()

    def login(self, kind="EMPLOYEE"):
        with self.client.session_transaction() as s:
            s["user"] = {"type": kind, "employeeId": 1}

    @patch.object(psi, "load_source", side_effect=lambda month: source())
    def test_unauthenticated_and_dealer_limited_to_own_store(self, load):
        for path in ("/psi", "/api/psi", "/api/psi/export"):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.login("DEALER")
        result = self.client.get("/api/psi")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["dealerCount"], 1)

    @patch.object(psi, "load_source", side_effect=source)
    def test_employee_api(self, load):
        load.side_effect = lambda month: source()
        self.login()
        result = self.client.get("/api/psi?month=2026-09&level=employee")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["dealerCount"], 2)
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get("/api/psi?employee=abc").status_code, 400)
        self.assertEqual(self.client.post("/api/psi").status_code, 405)

    @patch.object(psi, "load_source")
    def test_reload_reflects_sellout_edits_and_voids(self, load):
        self.login()
        s = source(); s["isCurrentMonth"] = True; s["isLastDay"] = True; load.return_value = s
        def available():
            return self.client.get("/api/psi?level=company&fresh=1").json["rows"][-1]["values"][-1][5]
        self.assertEqual(available(), 11)
        s["outgoing"] = [(1, 1, 7)]
        self.assertEqual(available(), 8)
        s["outgoing"] = []
        self.assertEqual(available(), 15)
        self.assertEqual(load.call_count, 3)

    @patch.object(psi, "load_source")
    def test_export_matches_table_and_neutralizes_formulas(self, load):
        s = source(); s["products"][0]["code"] = '=HYPERLINK("bad")';load.return_value = s
        self.login()
        result = self.client.get("/api/psi/export?level=company")
        self.assertEqual(result.status_code, 200)
        book = openpyxl.load_workbook(BytesIO(result.data))
        sheet = book["PSI"]
        self.assertEqual(sheet.freeze_panes, "E5")
        self.assertEqual(sheet["C5"].data_type, "s")
        self.assertEqual([sheet.cell(sheet.max_row, c).value for c in range(5, 12)], [4, 17, 2, 4, 15, 11, None])
        self.assertIn("計算說明", book.sheetnames)

    @patch.object(psi, "load_source")
    def test_export_can_embed_thumbnail_without_changing_default(self, load):
        load.return_value = source()
        self.login()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            relative = Path("uploads/display_photos/2026/09/1/photo_thumb.jpg")
            target = root / relative
            target.parent.mkdir(parents=True)
            Image.new("RGB", (32, 32), "navy").save(target, "JPEG")
            with patch.object(psi, "BASE", root), patch.object(
                psi.db, "display_photo_file", return_value={"path": relative.as_posix()}
            ):
                result = self.client.get("/api/psi/export?level=dealer&photos=thumbnail")
        self.assertEqual(result.status_code, 200)
        book = openpyxl.load_workbook(BytesIO(result.data))
        self.assertEqual(len(book["PSI"]._images), 1)
        self.assertTrue(any("已在客戶明細" in str(cell.value) for cell in book["計算說明"]["A"]))

    @patch.object(psi, "load_source", side_effect=source)
    def test_export_rejects_unknown_photo_mode(self, load):
        self.login()
        result = self.client.get("/api/psi/export?photos=original")
        self.assertEqual(result.status_code, 400)


if __name__ == "__main__":
    unittest.main()
