import unittest
from unittest.mock import patch

from core.api import KNOWN_EXCLUSIVE_EVENTS, get_active_exclusive_events


class GetActiveExclusiveEventsTest(unittest.TestCase):
    def tearDown(self):
        get_active_exclusive_events.clear()

    @patch("core.api._get_json")
    def test_live_response_is_completed_with_known_events(self, get_json):
        live_event = {
            "code": "EX7F6C",
            "category": "DIGITAL_PHOTOBOOK",
            "title": "Live title",
            "valid_date_from": "2026-07-16T13:00:00.000Z",
        }
        get_json.return_value = {"status": True, "data": [live_event]}

        events = get_active_exclusive_events()

        self.assertEqual(len(events), len(KNOWN_EXCLUSIVE_EVENTS))
        self.assertEqual(events[0]["title"], "Live title")
        self.assertEqual(
            {event["category"] for event in events},
            {"DIGITAL_PHOTOBOOK", "TWO_SHOT", "PHOTOCARD"},
        )


if __name__ == "__main__":
    unittest.main()
