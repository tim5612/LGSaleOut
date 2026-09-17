import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

import LGSale
import lgsale_permissions as permissions


def access(role, *, designer=False, dealer_ids=(1,)):
    return permissions.Access(
        account_id=7, account_type="EMPLOYEE", employee_id=11, dealer_id=None,
        role=role, org_id=3, designer=designer,
        capabilities=permissions.effective_capabilities(role, {}, {}),
        dealer_ids=frozenset(dealer_ids),
    )


class PermissionPolicyTests(unittest.TestCase):
    def test_manager_can_view_but_needs_individual_task_create_grant(self):
        self.assertNotIn("tasks.create", permissions.effective_capabilities("MANAGER", {}, {}))
        granted = permissions.effective_capabilities("MANAGER", {}, {"tasks.create": True})
        self.assertIn("tasks.create", granted)
        self.assertNotIn("employees.manage", granted)

    def test_account_override_wins_and_write_needs_read_surface(self):
        self.assertNotIn("psi.view", permissions.effective_capabilities(
            "MANAGER", {"psi.view": True}, {"psi.view": False}))
        self.assertNotIn("tasks.create", permissions.effective_capabilities(
            "MANAGER", {}, {"tasks.view": False, "tasks.create": True}))

    def test_only_designer_gets_permission_editor(self):
        self.assertFalse(access("ADMIN").can("permissions.manage"))
        self.assertTrue(access("SALES", designer=True).can("permissions.manage"))

    def test_dealer_mobile_is_read_only(self):
        allowed = permissions.effective_capabilities("DEALER", {}, {})
        self.assertIn("mobile.reports.view", allowed)
        self.assertNotIn("reports.create", allowed)
        self.assertNotIn("reports.edit", allowed)

    def test_designer_inherits_admin_permissions_and_all_dealers(self):
        principal = {"accountType": "EMPLOYEE", "employeeId": 11,
                     "dealerId": None, "position": "SALES", "orgId": 3,
                     "designer": True}
        def rules(role, account_id):
            return ({}, {"employees.view": False}) if role == "SALES" else ({}, {})
        with patch.object(permissions.db, "permission_principal", return_value=principal), \
             patch.object(permissions.db, "permission_rules", side_effect=rules), \
             patch.object(permissions.db, "permission_dealer_ids", return_value={1, 2}) as scope:
            result = permissions.resolve({"id": 7, "type": "EMPLOYEE"})
        self.assertTrue(permissions.effective_capabilities("ADMIN", {}, {}).issubset(result.capabilities))
        self.assertTrue(result.can("permissions.manage"))
        self.assertEqual(result.as_public()["scope"], "ALL")
        self.assertEqual(result.dealer_ids, frozenset({1, 2}))
        self.assertEqual(scope.call_args.args[0], "ADMIN")

    def test_designer_can_create_visit_without_granting_all_admins(self):
        principal = {"accountType": "EMPLOYEE", "employeeId": 11,
                     "dealerId": None, "position": "ADMIN", "orgId": 3,
                     "designer": True}
        with patch.object(permissions.db, "permission_principal", return_value=principal), \
             patch.object(permissions.db, "permission_rules", return_value=({}, {})), \
             patch.object(permissions.db, "permission_dealer_ids", return_value={1, 2}):
            result = permissions.resolve({"id": 7, "type": "EMPLOYEE"})
        self.assertNotIn("reports.create", permissions.effective_capabilities("ADMIN", {}, {}))
        self.assertTrue(result.can("reports.create"))
        self.assertTrue(result.can("mobile.reports.view"))
        self.assertFalse(result.can("reports.edit"))
        self.assertTrue(result.has_dealer(2))


class PermissionRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = LGSale.app
        self.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = self.app.test_client()
        with self.client.session_transaction() as s:
            s["user"] = {"id": 7, "type": "EMPLOYEE", "employeeId": 11,
                         "dealerId": None, "name": "測試使用者"}
        self.login_allowed = patch.object(LGSale.db, "account_login_allowed", return_value=True)
        self.login_allowed.start()
        self.addCleanup(self.login_allowed.stop)

    def test_manager_menu_and_forbidden_writes(self):
        with patch.object(LGSale.permissions, "resolve", return_value=access("MANAGER")):
            me = self.client.get("/api/auth/me")
            self.assertEqual(me.status_code, 200)
            self.assertIn("tasks.view", me.json["capabilities"])
            self.assertNotIn("tasks.create", me.json["capabilities"])
            self.assertEqual(self.client.post("/api/tasks", json={}).status_code, 403)
            self.assertEqual(self.client.get("/api/employees").status_code, 403)
            self.assertEqual(self.client.get("/mobile").status_code, 403)
            self.assertEqual(self.client.get("/permissions").status_code, 403)

    def test_designer_page_is_separate_from_management(self):
        with patch.object(LGSale.permissions, "resolve", return_value=access("ADMIN")):
            self.assertEqual(self.client.get("/permissions").status_code, 403)
        with patch.object(LGSale.permissions, "resolve", return_value=access("SALES", designer=True)):
            response = self.client.get("/permissions")
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_display_photo_switch_is_designer_only_and_blocks_new_uploads(self):
        with patch.object(LGSale.permissions, "resolve", return_value=access("SALES")), \
             patch.object(LGSale.db, "display_photo_enabled", return_value=False):
            self.assertEqual(self.client.put("/api/display-photo-setting", json={"enabled": True}).status_code, 403)
            response = self.client.post("/api/display-photos", data={"dealerId": "1", "productId": "3"})
            self.assertEqual(response.status_code, 403)
            self.assertIn("目前關閉", response.json["error"])
            self.assertEqual(self.client.get("/api/display-photo-setting").json, {"enabled": False})
        with patch.object(LGSale.permissions, "resolve", return_value=access("SALES", designer=True)), \
             patch.object(LGSale.db, "set_display_photo_enabled") as save:
            self.assertEqual(self.client.put("/api/display-photo-setting", json={"enabled": True}).status_code, 200)
            save.assert_called_once_with(True, 7)

    def test_designer_visit_records_real_author_for_assigned_dealer(self):
        designer = replace(access("ADMIN", designer=True, dealer_ids=(2,)),
                           capabilities=frozenset(permissions.ROLE_DEFAULTS["ADMIN"] |
                                                  {"mobile.reports.view", "reports.create"}))
        payload = {"dealerId": 2, "details": [{"productId": 3, "displayQuantity": 1}]}
        with patch.object(LGSale.permissions, "resolve", return_value=designer), \
             patch.object(LGSale.db, "create_visit", return_value=(19, datetime(2026, 9, 17, 10, 0))) as create:
            response = self.client.post("/api/visits", json=payload)
        self.assertEqual(response.status_code, 201)
        sent = create.call_args.args[0]
        self.assertEqual(sent["dealerId"], 2)
        self.assertEqual(sent["userAccountId"], 7)
        self.assertEqual(sent["entrySourceType"], "EMPLOYEE")

    def test_passkey_login_qr_uses_selected_entry_and_requires_management_access(self):
        with patch.object(LGSale.permissions, "resolve", return_value=access("SALES")):
            self.assertEqual(self.client.get("/api/passkey-login/qr/employee.png").status_code, 403)
        with patch.object(LGSale.permissions, "resolve", return_value=access("ADMIN")), \
             patch.object(LGSale.qrcode, "make", wraps=LGSale.qrcode.make) as make:
            response = self.client.get("/api/passkey-login/qr/dealer.png")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "image/png")
            self.assertTrue(response.data.startswith(b"\x89PNG"))
            make.assert_called_once_with(f"{LGSale.auth.ORIGIN}/login/dealer")
            response.close()
            self.assertEqual(self.client.get("/api/passkey-login/qr/other.png").status_code, 404)

    def test_task_detail_uses_server_scope(self):
        with patch.object(LGSale.permissions, "resolve", return_value=access("SALES", dealer_ids=(4, 8))), \
             patch.object(LGSale.db, "task_detail", return_value=None) as detail:
            response = self.client.get("/api/tasks/12")
            self.assertEqual(response.status_code, 404)
            detail.assert_called_once_with(12, frozenset({4, 8}))

    def test_one_manager_can_be_granted_task_creation(self):
        manager = access("MANAGER")
        manager = replace(manager, capabilities=permissions.effective_capabilities(
            "MANAGER", {}, {"tasks.create": True}))
        payload = {"title": "新任務", "instruction": "拍照", "validFrom": "2026-09-16",
                   "dueDate": "2026-09-20"}
        with patch.object(LGSale.permissions, "resolve", return_value=manager), \
             patch.object(LGSale.db, "create_task", return_value={"id": 10}) as create:
            self.assertEqual(self.client.post("/api/tasks", json=payload).status_code, 201)
            create.assert_called_once()
            self.assertEqual(create.call_args.kwargs["creator_id"], 11)

    def test_every_application_route_has_a_policy(self):
        public = {"static", "health", "login_page", "register_page",
                  "auth_register_options", "auth_register_verify", "auth_login_options",
                  "auth_login_verify", "desktop_approve_page", "desktop_approval_start",
                  "desktop_approval_info", "desktop_approval_status", "desktop_approval_qr",
                  "auth_me", "auth_logout"}
        endpoints = {rule.endpoint for rule in self.app.url_map.iter_rules()}
        self.assertFalse(endpoints - public - set(LGSale.ENDPOINT_CAPABILITIES))


if __name__ == "__main__":
    unittest.main()
