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
    return []


@st.cache_data(ttl=300)
def get_active_exclusive_codes():
    return [ev.get("code") for ev in get_active_exclusive_events() if ev.get("code")]


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
                cache_payload = {
                    "last_updated": waktu_sekarang,
                    "data": data,
                }
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

    _set_wr_status(code, False, "No Cache Available")
    return None
