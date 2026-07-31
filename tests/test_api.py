import json
import unittest
from collections import Counter
from pathlib import Path
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
            Counter(event["category"] for event in events),
            Counter({"DIGITAL_PHOTOBOOK": 5, "TWO_SHOT": 5, "PHOTOCARD": 5}),
        )

    def test_every_known_event_has_bundled_detail(self):
        project_root = Path(__file__).parent.parent

        for event in KNOWN_EXCLUSIVE_EVENTS:
            cache_file = project_root / f"cache_exclusive_{event['code']}.json"
            with self.subTest(code=event["code"]):
                self.assertTrue(cache_file.exists())
                with cache_file.open(encoding="utf-8") as file:
                    cached_event = json.load(file)["data"]
                self.assertEqual(cached_event["code"], event["code"])
                self.assertEqual(cached_event["category"], event["category"])


if __name__ == "__main__":
    unittest.main()
