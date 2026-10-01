import unittest
from pathlib import Path
from unittest.mock import patch

import LGSale


class PasskeyOnboardingTests(unittest.TestCase):
    def setUp(self):
        LGSale.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = LGSale.app.test_client()

    def test_registration_status_is_public_and_returns_lifecycle(self):
        expected = {"status": "USED", "accountType": "EMPLOYEE",
                    "displayName": "王小明", "ownerRef": "E001"}
        with patch.object(LGSale.auth, "registration_invitation_status",
                          return_value=expected) as status:
            response = self.client.get("/api/auth/register/status?token=old-token")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected)
        status.assert_called_once_with("old-token")

    def test_registration_page_contains_precheck_and_completed_link_guidance(self):
        source = (Path(__file__).resolve().parents[1] / "LGSale_Auth.html").read_text(encoding="utf-8")
        self.assertIn("/api/auth/register/status?token=", source)
        self.assertIn("Passkey 已設定完成", source)
        self.assertIn("複製／分享固定登入網址", source)
        self.assertIn("mobile.tasks.view", source)

    def test_onboarding_has_mobile_cards_desktop_help_and_reopen_button(self):
        source = (Path(__file__).resolve().parents[1] / "lgsale_onboarding.js").read_text(encoding="utf-8")
        self.assertIn("手機可以做什麼？", source)
        self.assertIn("如何登入電腦？", source)
        self.assertIn("歡迎使用 LGSale 電腦版", source)
        self.assertIn("？ 使用說明", source)
        self.assertIn("mobile.tasks.view", source)
        self.assertIn("複製手機版連結", source)
        self.assertIn("複製電腦版連結", source)
        self.assertIn('copyUrl(event.currentTarget, "/mobile"', source)
        self.assertIn('copyUrl(event.currentTarget, "/"', source)

    def test_mobile_locked_page_explains_successful_login_and_desktop_qr(self):
        source = (Path(__file__).resolve().parents[1] / "LGSale_MobileLocked.html").read_text(encoding="utf-8")
        self.assertIn("你的帳號已成功登入", source)
        self.assertIn("使用 iPhone 掃碼授權桌機", source)
        self.assertIn("複製電腦登入網址", source)


if __name__ == "__main__":
    unittest.main()
