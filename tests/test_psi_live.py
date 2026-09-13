r"""Opt-in, read-only verification against this machine's configured database.

PowerShell: $env:LGSALE_PSI_LIVE_TEST='1'; .venv\Scripts\python.exe -m unittest discover -s tests -p test_psi_live.py -v
No records, accounts, sessions in the live server, or database schema are changed.
"""
import os
import unittest
from io import BytesIO
from unittest.mock import patch

import openpyxl

import lgsale_psi as psi


@unittest.skipUnless(os.getenv("LGSALE_PSI_LIVE_TEST") == "1", "opt-in live database reads")
class LiveTests(unittest.TestCase):
    def test_live_source_reconciles_after_exclusions(self):
        s = psi.load_source()
        report = psi.build_report(s, {})
        pairs = {(d["id"], p["id"]) for d in report["dealers"] for p in report["rows"] if str(d["id"]) in p["cells"]}
        self.assertEqual(sum(n for d, p, n in s["opening"] if (d, p) in pairs),
                         sum(c["values"][1] or 0 for r in report["rows"] for c in r["cells"].values()))
        total = psi.matrix(report)["rows"][-1]["values"][-1] if report["rows"] else [0]*7
        self.assertEqual(sum(pos for d, p, pos, neg in s["incoming"] if (d, p) in pairs), total[2])
        self.assertEqual(sum(neg for d, p, pos, neg in s["incoming"] if (d, p) in pairs), total[3])

    def test_full_application_routes(self):
        from LGSale import app
        client = app.test_client()
        self.assertEqual(client.get("/api/psi").status_code, 401)
        self.assertEqual(client.get("/psi").status_code, 302)
        with client.session_transaction() as session:
            session["user"] = dict(id=1, employeeId=1, type="EMPLOYEE")
        # Test-client-only session, no authentication changes in the live application.
        with patch("lgsale_db.account_login_allowed", return_value=True):
            page = client.get("/psi")
            self.assertEqual(page.status_code, 200)
            page.close()
            report = client.get("/api/psi?level=company")
            self.assertEqual(report.status_code, 200)
            self.assertIn("quality", report.json)
            result = client.get("/api/psi/export?level=company")
            self.assertEqual(result.status_code, 200)
            book = openpyxl.load_workbook(BytesIO(result.data))
            self.assertEqual(book["PSI"].freeze_panes, "E5")
        with client.session_transaction() as session:
            session["user"] = dict(id=1, dealerId=1, type="DEALER")
        with patch("lgsale_db.account_login_allowed", return_value=True):
            self.assertEqual(client.get("/api/psi").status_code, 403)


if __name__ == "__main__":
    unittest.main()
