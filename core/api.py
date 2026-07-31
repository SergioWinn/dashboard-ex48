# core/api.py

import json
import os
import time
from datetime import datetime, timedelta

import streamlit as st

try:
    from curl_cffi import requests as browser_requests
    USING_BROWSER_CLIENT = True
except ImportError:
    import requests as browser_requests
    USING_BROWSER_CLIENT = False

BASE_HEADERS = {
    "Accept": "application/json",
    "Referer": "https://jkt48.com/",
}
FALLBACK_HEADERS = {
    **BASE_HEADERS,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}
KNOWN_EXCLUSIVE_EVENTS = [
    {"exclusive_id": 936, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex7b6d-thumb-d71768.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex7b6d-preview-8a69c1.jpg", "code": "EXE588", "valid_date_from": "2026-04-02T11:00:00.000Z", "sort_order": 1, "title": "Personal Meet and Greet Festival: LOVE DREAM PASSION, Meet & Greet - 23 May", "short_description": ""},
    {"exclusive_id": 962, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-thumb-a2122e.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-preview-872f71.jpg", "code": "EX7F6C", "valid_date_from": "2026-07-16T13:00:00.000Z", "sort_order": None, "title": "JKT48 Request Hour 2026 Setlist Best 40", "short_description": ""},
    {"exclusive_id": 960, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exfb66-thumb-ba1e85.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exfb66-preview-bb4a0e.jpg", "code": "EXFB66", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, 2shot Yogyakarta", "short_description": ""},
    {"exclusive_id": 959, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exa340-thumb-bc4526.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exa340-preview-c338ee.jpg", "code": "EXA340", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, Meet and Greet Yogyakarta", "short_description": ""},
    {"exclusive_id": 958, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex38a5-thumb-ec17a2.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex38a5-preview-108c95.jpg", "code": "EX38A5", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Passion, 2shot Surabaya", "short_description": ""},
    {"exclusive_id": 957, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exafb8-thumb-26d9a3.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exafb8-preview-b668a4.jpg", "code": "EXAFB8", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Passion, Meet and Greet Surabaya", "short_description": ""},
    {"exclusive_id": 954, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex3773-thumb-f96b44.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex3773-preview-cbccce.jpg", "code": "EX3773", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, 2shot Surabaya", "short_description": ""},
    {"exclusive_id": 953, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex9a4a-thumb-736b1c.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex9a4a-preview-792fcc.jpg", "code": "EX9A4A", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, Meet and Greet Surabaya", "short_description": ""},
    {"exclusive_id": 956, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excd2c-thumb-d289a4.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excd2c-preview-385402.jpg", "code": "EXCD2C", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Passion, 2shot Yogyakarta", "short_description": ""},
    {"exclusive_id": 955, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excb75-thumb-fd9e9c.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excb75-preview-03c4c8.jpg", "code": "EXCB75", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Passion, Meet and Greet Yogyakarta", "short_description": ""},
    {"exclusive_id": 947, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex783d-thumb-edd92f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex783d-preview-c1bec0.jpg", "code": "EX783D", "valid_date_from": "2026-06-09T13:00:00.000Z", "sort_order": None, "title": "JKT48 Personal Meet and Greet Festival: LOVE DREAM PASSION", "short_description": ""},
    {"exclusive_id": 946, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/05/ex3725-thumb-f9f5e7.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/05/ex3725-preview-d270de.jpg", "code": "EX3725", "valid_date_from": "2026-05-06T15:00:00.000Z", "sort_order": None, "title": "We Are Love, Dream Team, Passion On Fire!", "short_description": ""},
    {"exclusive_id": 945, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex8432-thumb-0bd15f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex8432-preview-5bec27.jpg", "code": "EX8432", "valid_date_from": "2026-04-26T12:00:00.000Z", "sort_order": None, "title": "Love Dream Passion - Music Video Behind the Scenes (Without Bonus Video Call)", "short_description": ""},
    {"exclusive_id": 944, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/exbe10-thumb-37400f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/exbe10-preview-98404e.jpg", "code": "EXBE10", "valid_date_from": "2026-04-10T15:00:00.000Z", "sort_order": None, "title": "Love Dream Passion - Music Video Behind the Scenes", "short_description": ""},
    {"exclusive_id": 933, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/03/ex579e-thumb-c637b9.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/03/ex579e-preview-e420c5.jpg", "code": "EX579E", "valid_date_from": "2026-04-01T11:00:00.000Z", "sort_order": None, "title": "Personal Meet and Greet Festival: LOVE DREAM PASSION, 2Shot - 23 May", "short_description": ""},
]
KNOWN_EXCLUSIVE_CODES = [event["code"] for event in KNOWN_EXCLUSIVE_EVENTS]
EMERGENCY_EXCLUSIVE_DETAILS = {
    "EX7F6C": {
        "exclusive_id": 962,
        "category": "DIGITAL_PHOTOBOOK",
        "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-thumb-a2122e.jpg",
        "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-preview-872f71.jpg",
        "code": "EX7F6C",
        "default_price": 120000,
        "total_quota": 10800,
        "max_purchase": 5,
        "max_purchase_transaction": 5,
        "sort_order": None,
        "valid_date_from": "2026-07-16T13:00:00.000Z",
        "valid_date_to": None,
        "status": True,
        "title": "JKT48 Request Hour 2026 Setlist Best 40",
        "short_description": "",
        "content_body": "<div>Photobook JKT48 \"Request Hour 2026 Setlist Best 40\" menghadirkan berbagai momen spesial dari pertunjukan yang penuh semangat. Setiap halaman menampilkan kenangan indah para member di atas panggung. </div>",
        "sales_period": [
            {"label": "OFC", "start_date": "2026-07-16T20:00:00", "end_date": "2026-07-26T07:00:00", "is_ofc_only": True},
            {"label": "General", "start_date": "2026-07-17T20:00:00", "end_date": "2026-07-26T07:00:00", "is_ofc_only": False}
        ],
        "session": [
            {"label": "Sesi 1", "date": "2026-07-19", "start_time": "11:45:00", "end_time": "12:45:00", "reception_start_time": "11:30:00", "reception_end_time": "12:00:00", "prep_start_time": "11:30:00", "prep_end_time": "11:45:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 5, "jkt48_member_name": "Bong Aprilli", "available_quota": 40}, {"label": "Jalur 2", "tickets_sold": 18, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 27}, {"label": "Jalur 3", "tickets_sold": 4, "jkt48_member_name": "Maxine Faye", "available_quota": 41}, {"label": "Jalur 4", "tickets_sold": 17, "jkt48_member_name": "Sona Kalyana", "available_quota": 28}, {"label": "Jalur 5", "tickets_sold": 5, "jkt48_member_name": "Fahira Putri", "available_quota": 40}, {"label": "Jalur 6", "tickets_sold": 14, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 31}, {"label": "Jalur 7", "tickets_sold": 23, "jkt48_member_name": "Christabella Bonita", "available_quota": 22}]},
            {"label": "Sesi 2", "date": "2026-07-19", "start_time": "13:15:00", "end_time": "14:15:00", "reception_start_time": "13:00:00", "reception_end_time": "13:30:00", "prep_start_time": "13:00:00", "prep_end_time": "13:15:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 12, "jkt48_member_name": "Bong Aprilli", "available_quota": 33}, {"label": "Jalur 2", "tickets_sold": 26, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 19}, {"label": "Jalur 3", "tickets_sold": 7, "jkt48_member_name": "Maxine Faye", "available_quota": 38}, {"label": "Jalur 4", "tickets_sold": 11, "jkt48_member_name": "Sona Kalyana", "available_quota": 34}, {"label": "Jalur 5", "tickets_sold": 14, "jkt48_member_name": "Fahira Putri", "available_quota": 31}, {"label": "Jalur 6", "tickets_sold": 9, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 36}, {"label": "Jalur 7", "tickets_sold": 13, "jkt48_member_name": "Christabella Bonita", "available_quota": 32}]},
            {"label": "Sesi 3", "date": "2026-07-19", "start_time": "14:45:00", "end_time": "15:45:00", "reception_start_time": "14:30:00", "reception_end_time": "15:00:00", "prep_start_time": "14:30:00", "prep_end_time": "14:45:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 8, "jkt48_member_name": "Bong Aprilli", "available_quota": 37}, {"label": "Jalur 2", "tickets_sold": 37, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 8}, {"label": "Jalur 3", "tickets_sold": 6, "jkt48_member_name": "Maxine Faye", "available_quota": 39}, {"label": "Jalur 4", "tickets_sold": 32, "jkt48_member_name": "Sona Kalyana", "available_quota": 13}, {"label": "Jalur 5", "tickets_sold": 9, "jkt48_member_name": "Fahira Putri", "available_quota": 36}, {"label": "Jalur 6", "tickets_sold": 18, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 27}, {"label": "Jalur 7", "tickets_sold": 17, "jkt48_member_name": "Christabella Bonita", "available_quota": 28}]},
            {"label": "Sesi 4", "date": "2026-07-19", "start_time": "16:30:00", "end_time": "17:30:00", "reception_start_time": "16:15:00", "reception_end_time": "16:45:00", "prep_start_time": "16:15:00", "prep_end_time": "16:30:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 45, "jkt48_member_name": "Nur Intan", "available_quota": 0}, {"label": "Jalur 2", "tickets_sold": 45, "jkt48_member_name": "Hagia Sopia", "available_quota": 0}, {"label": "Jalur 3", "tickets_sold": 45, "jkt48_member_name": "Jemima Evodie", "available_quota": 0}, {"label": "Jalur 4", "tickets_sold": 45, "jkt48_member_name": "Jacqueline Immanuela", "available_quota": 0}, {"label": "Jalur 5", "tickets_sold": 33, "jkt48_member_name": "Astrella Virgiananda", "available_quota": 12}, {"label": "Jalur 6", "tickets_sold": 10, "jkt48_member_name": "Humaira Ramadhani", "available_quota": 35}, {"label": "Jalur 7", "tickets_sold": 19, "jkt48_member_name": "Aulia Riza", "available_quota": 26}]}
        ]
    }
}


@st.cache_resource
def get_http_session():
    session = browser_requests.Session()
    session.headers.update(FALLBACK_HEADERS)
    return session


def _set_wr_status(code, is_live, time_label):
    try:
        st.session_state[f"wr_status_{code}"] = {"is_live": is_live, "time": time_label}
    except Exception:
        pass


def _http_get(url, timeout):
    session = get_http_session()
    kwargs = {"timeout": timeout, "headers": BASE_HEADERS}
    if USING_BROWSER_CLIENT:
        kwargs["impersonate"] = "chrome"
    return session.get(url, **kwargs)


def _get_json(url, timeout):
    response = _http_get(url, timeout)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    return response.json()


def _event_summary_from_detail(detail):
    return {
        "exclusive_id": detail.get("exclusive_id"),
        "category": detail.get("category"),
        "thumbnail_image": detail.get("thumbnail_image"),
        "preview_image": detail.get("preview_image"),
        "code": detail.get("code"),
        "valid_date_from": detail.get("valid_date_from"),
        "sort_order": detail.get("sort_order"),
        "title": detail.get("title"),
        "short_description": detail.get("short_description", ""),
        "default_price": detail.get("default_price", 0),
        "valid_date_to": detail.get("valid_date_to"),
        "sales_period": detail.get("sales_period", []),
    }


@st.cache_data(ttl=3600)
def get_member_database():
    url = "https://jkt48.com/api/v1/members?lang=id"
    nickname_map = {}
    photo_map = {}
    try:
        res_json = _get_json(url, 15)
        if res_json.get("status") is True and "data" in res_json:
            for member in res_json["data"]:
                name = member.get("name", "").strip().lower()
                nickname = member.get("nickname", "").strip().lower()
                photo = member.get("photo", "")
                if nickname and name:
                    nickname_map[nickname] = name
                if name and photo:
                    photo_map[name] = photo
    except Exception:
        pass
    return nickname_map, photo_map


@st.cache_data(ttl=300)
def get_active_exclusive_events():
    url = "https://jkt48.com/api/v1/exclusives?lang=id"
    try:
        res_json = _get_json(url, 20)
        if res_json.get("status") is True and "data" in res_json:
            data_content = res_json["data"]
            event_list = data_content if isinstance(data_content, list) else data_content.get("data", [])
            return [ev for ev in event_list if ev.get("code")]
    except Exception:
        pass

    hydrated_events = []
    for code in KNOWN_EXCLUSIVE_CODES:
        detail = fetch_exclusive_detail(code)
        if detail:
            hydrated_events.append(_event_summary_from_detail(detail))
    if hydrated_events:
        return hydrated_events

    return KNOWN_EXCLUSIVE_EVENTS.copy()


@st.cache_data(ttl=15)
def fetch_exclusive_detail(code):
    url = f"https://jkt48.com/api/v1/exclusives/{code}?lang=id"
    cache_file = f"cache_exclusive_{code}.json"
    now_wib = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_wib.strftime('%d/%m/%Y %H:%M:%S WIB')

    for timeout in (15, 25):
        try:
            res_json = _get_json(url, timeout)
            data = res_json.get("data")
            if data:
                cache_payload = {"last_updated": waktu_sekarang, "data": data}
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_payload, f)
                _set_wr_status(code, True, waktu_sekarang)
                return data
        except Exception:
            time.sleep(0.5)

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_payload = json.load(f)
            _set_wr_status(code, False, cache_payload.get("last_updated", "Unknown"))
            return cache_payload.get("data")
        except Exception:
            pass

    emergency_data = EMERGENCY_EXCLUSIVE_DETAILS.get(code)
    if emergency_data:
        _set_wr_status(code, False, "Bundled emergency fallback")
        return emergency_data

    _set_wr_status(code, False, "No Cache Available")
    return None
