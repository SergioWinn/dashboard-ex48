import json
import unittest
from pathlib import Path
from unittest.mock import patch

from core.api import (
    KNOWN_EXCLUSIVE_EVENTS,
    LiveApiUnavailable,
    fetch_exclusive_detail,
    get_active_exclusive_events,
)


class GetActiveExclusiveEventsTest(unittest.TestCase):
    def tearDown(self):
        get_active_exclusive_events.clear()

    @patch("core.api._write_cache")
    @patch("core.api._get_json")
    def test_live_response_is_used_without_manual_event_list(self, get_json, write_cache):
        live_event = {
            "code": "EXNEW1",
            "category": "DIGITAL_PHOTOBOOK",
            "title": "New live event",
            "valid_date_from": "2026-08-01T13:00:00.000Z",
        }
        get_json.return_value = {"status": True, "data": [live_event]}

        events = get_active_exclusive_events()

        self.assertEqual(events, [live_event])
        write_cache.assert_called_once()

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare Waiting Room"))
    def test_event_list_falls_back_when_live_api_is_unavailable(self, _get_json, read_cache):
        read_cache.return_value = {"last_updated": "now", "data": KNOWN_EXCLUSIVE_EVENTS}

        events = get_active_exclusive_events()

        self.assertEqual(events, KNOWN_EXCLUSIVE_EVENTS)

    @patch("builtins.open", side_effect=PermissionError)
    @patch("core.api._get_json")
    def test_cache_write_failure_does_not_discard_live_detail(self, get_json, _open):
        live_detail = {"code": "EXNEW1", "session": []}
        get_json.return_value = {"status": True, "data": live_detail}

        detail = fetch_exclusive_detail("EXNEW1")

        self.assertEqual(detail, live_detail)

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
