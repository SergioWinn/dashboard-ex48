import unittest
from datetime import datetime

from core.refresh import get_detail_refresh_interval


class DetailRefreshIntervalTest(unittest.TestCase):
    def setUp(self):
        self.event = {
            "sales_period": [
                {
                    "label": "General",
                    "start_date": "2026-08-01T10:00:00",
                    "end_date": "2026-08-01T20:00:00",
                }
            ]
        }

    def test_active_sales_refresh_every_five_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 12, 0, 0),
        )

        self.assertEqual(interval, 5)

    def test_ofc_period_before_general_still_refreshes_every_five_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 9, 0, 0),
        )

        self.assertEqual(interval, 5)

    def test_closed_sales_refresh_every_sixty_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 21, 0, 0),
        )

        self.assertEqual(interval, 60)

    def test_waiting_room_recovery_refresh_every_fifteen_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            False,
            datetime(2026, 8, 1, 12, 0, 0),
        )

        self.assertEqual(interval, 15)


if __name__ == "__main__":
    unittest.main()
