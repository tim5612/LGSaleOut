import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
from flask import Flask

import lgsale_sellin as sellin


HEADERS = [
    "Category", "Order No", "Item", "Sold-to", "Model(Prefix)",
    "Invoiced Qty", "Order Date", "Billing Date", "Invoice No", "Invoice Date",
]


def workbook(rows):
    handle = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    handle.close()
    path = Path(handle.name)
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "Data"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    book.save(path)
    return path


class ParserTests(unittest.TestCase):
    def tearDown(self):
        for path in getattr(self, "paths", []):
            path.unlink(missing_ok=True)

    def make(self, rows):
        self.paths = getattr(self, "paths", [])
        path = workbook(rows)
        self.paths.append(path)
        return path

    def test_sales_and_return_are_parsed_with_billing_effective_date(self):
        path = self.make([
            ["Sales", "1124001", "10", "TW001A1", "OLED55", 2, "2026-09-01", "2026-09-03", "EQ1", "2026-09-03"],
            ["Return", "600001", "10", "TW001A1", "OLED55", -1, "2026-09-02", "2026-09-04", None, None],
        ])
        rows, errors = sellin.parse_workbook(path)
        self.assertEqual(errors, [])
        self.assertEqual([row["quantity"] for row in rows], [2, -1])
        self.assertEqual(rows[1]["billingDate"].isoformat(), "2026-09-04")
        self.assertIsNone(rows[1]["invoiceDate"])

    def test_wrong_sign_and_duplicate_order_item_are_errors(self):
        path = self.make([
            ["Return", "600001", "10", "TW001A1", "OLED55", 1, "2026-09-01", "2026-09-03", None, None],
            ["Sales", "1124001", "10", "TW001A1", "OLED55", 1, "2026-09-01", "2026-09-03", "EQ1", "2026-09-03"],
            ["Sales", "1124001", "10", "TW001A1", "OLED55", 1, "2026-09-01", "2026-09-03", "EQ1", "2026-09-03"],
        ])
        rows, errors = sellin.parse_workbook(path)
        self.assertEqual(len(rows), 1)
        self.assertTrue(any("退貨數量必須為負數" in error for error in errors))
        self.assertTrue(any("Order No＋Item" in error for error in errors))

    def test_missing_required_header_is_rejected(self):
        path = self.make([])
        book = openpyxl.load_workbook(path)
        book["Data"]["D1"] = "Wrong dealer header"
        book.save(path)
        with self.assertRaisesRegex(ValueError, "Sold-to"):
            sellin.parse_workbook(path)


class ReviewTests(unittest.TestCase):
    def test_review_classifies_master_and_duplicate_results(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [("TW001A1", 1, "經銷商一")],
            [("OLED55", 2, "OLED 電視")],
            [("OLD", "10")],
        ]
        cursor.fetchone.return_value = ("202609",)
        base = dict(category="Sales", itemNo="10", quantity=1,
                    orderDate=sellin.date(2026, 9, 1), billingDate=sellin.date(2026, 9, 3),
                    invoiceNo="EQ1", invoiceDate=sellin.date(2026, 9, 3))
        rows = [
            dict(base, row=2, orderNo="NEW", dealerCode="TW001A1", productCode="OLED55"),
            dict(base, row=3, orderNo="OUT", dealerCode="TW999A1", productCode="OLED55"),
            dict(base, row=4, orderNo="SKU", dealerCode="TW001A1", productCode="UNKNOWN"),
            dict(base, row=5, orderNo="OLD", dealerCode="TW001A1", productCode="OLED55"),
        ]
        review = sellin.build_review(rows, [], cursor)
        self.assertEqual([row["status"] for row in review["rows"]], ["ready", "outsideDealer", "newProduct", "duplicate"])
        self.assertEqual(review["summary"]["ready"], 2)
        self.assertEqual(review["summary"]["newProducts"], 1)

    def test_salein_before_opening_month_is_warned_but_still_importable(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [("TW001A1", 1, "經銷商一")],
            [("OLED55", 2, "OLED 電視")],
            [],
        ]
        cursor.fetchone.return_value = ("202609",)
        row = dict(row=2, category="Sales", orderNo="A1", itemNo="10",
                   dealerCode="TW001A1", productCode="OLED55", quantity=1,
                   orderDate=sellin.date(2026, 8, 20), billingDate=sellin.date(2026, 8, 25),
                   invoiceNo="EQ1", invoiceDate=sellin.date(2026, 8, 25))
        review = sellin.build_review([row], [], cursor)
        self.assertEqual(review["summary"]["ready"], 1)
        self.assertEqual(review["summary"]["beforeOpening"], 1)
        self.assertTrue(review["rows"][0]["beforeOpening"])


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test"
        self.app.register_blueprint(sellin.bp)
        self.client = self.app.test_client()

    def test_page_requires_employee(self):
        response = self.client.get("/sellin-import")
        self.assertEqual(response.status_code, 403)

    def test_context_returns_history(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        connection = MagicMock()
        connection.cursor.return_value = cursor
        with self.client.session_transaction() as session:
            session["user"] = {"id": 7, "employeeId": 7, "type": "EMPLOYEE", "name": "測試者"}
        with patch.object(sellin.db, "connect", return_value=connection):
            response = self.client.get("/api/sellin-import/context")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["history"], [])


if __name__ == "__main__":
    unittest.main()
