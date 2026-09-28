import unittest
from unittest.mock import MagicMock, patch

import lgsale_db as db


class SellOutInventoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.cur = MagicMock()
        self.stock = [{"id": 7, "code": "TV-7", "availableQuantity": 3}]

    @patch("lgsale_db.reportable_products_for_cursor")
    def test_sell_out_equal_to_available_inventory_is_allowed(self, inventory):
        inventory.return_value = self.stock
        self.assertEqual(db._sell_out_warnings(
            self.cur, 12, [{"productId": 7, "sellOutQuantity": 3}]
        ), [])

    @patch("lgsale_db.reportable_products_for_cursor")
    def test_sell_out_above_available_inventory_returns_confirmable_warning(self, inventory):
        inventory.return_value = self.stock
        self.assertEqual(db._sell_out_warnings(
            self.cur, 12, [{"productId": 7, "sellOutQuantity": 4}]
        ), [{"productId":7,"productCode":"TV-7","sellOutQuantity":4,"availableQuantity":3}])

    @patch("lgsale_db.reportable_products_for_cursor")
    def test_display_only_detail_does_not_query_inventory(self, inventory):
        self.assertEqual(db._sell_out_warnings(
            self.cur, 12, [{"productId": 7, "displayQuantity": 2}]
        ), [])
        inventory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
