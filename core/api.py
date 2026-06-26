# core/api.py

import requests
import streamlit as st
import os
import json
from datetime import datetime, timedelta

# Fungsi baru untuk merakit Headers secara dinamis
def get_headers():
    headers = {
        "Referer": "https://jkt48.com/",
        "Accept": "application/json, text/plain, */*"
    }
    
    # Tangkap payload dari Streamlit Session State
    injected_cookie = st.session_state.get("cf_cookie", "")
    injected_ua = st.session_state.get("cf_ua", "")
    
    # Wajib samakan User-Agent dengan browser aslimu, atau pakai default
    if injected_ua:
        headers["User-Agent"] = injected_ua
    else:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
    # Masukkan Cookie (termasuk cf_clearance) jika ada
    if injected_cookie:
        headers["Cookie"] = injected_cookie
        
    return headers

@st.cache_data(ttl=3600)
def get_member_database():
    url = "https://jkt48.com/api/v1/members?lang=id"
    nickname_map = {}
    photo_map = {}
    
    # 1. Panggil headers dinamis
    dinamic_headers = get_headers()
    
    try:
        # 2. Gunakan dinamic_headers
        response = requests.get(url, headers=dinamic_headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") is True and "data" in res_json:
                for member in res_json["data"]:
                    name = member.get("name", "").strip().lower()
                    nickname = member.get("nickname", "").strip().lower()
                    photo = member.get("photo", "")
                    
                    if nickname and name:
                        nickname_map[nickname] = name
                    if name and photo:
                        photo_map[name] = photo
    except:
        pass
    return nickname_map, photo_map

@st.cache_data(ttl=300)
def get_active_exclusive_codes():
    url = "https://jkt48.com/api/v1/exclusives?lang=id"
    
    # 1. Panggil headers dinamis
    dinamic_headers = get_headers()
    
    try:
        # 2. Gunakan dinamic_headers
        response = requests.get(url, headers=dinamic_headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") is True and "data" in res_json:
                data_content = res_json["data"]
                event_list = data_content if isinstance(data_content, list) else data_content.get("data", [])
                return [ev.get("code") for ev in event_list if ev.get("code")]
    except:
        pass
    return []

@st.cache_data(ttl=4)
def fetch_exclusive_detail(code):
    url = f"https://jkt48.com/api/v1/exclusives/{code}?lang=id"
    cache_file = f"cache_exclusive_{code}.json"
    now_wib = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_wib.strftime('%d/%m/%Y %H:%M:%S WIB')

    # Panggil fungsi headers dinamis di sini
    dinamic_headers = get_headers()

    try:
        # Gunakan dinamic_headers yang sudah disuntik
        r = requests.get(url, headers=dinamic_headers, timeout=5)
        
        if r.status_code == 200:
            res_json = r.json()
            data = res_json.get('data')
            
            if data:
                cache_payload = {
                    "last_updated": waktu_sekarang,
                    "data": data
                }
                with open(cache_file, "w") as f:
                    json.dump(cache_payload, f)
                
                st.session_state[f"wr_status_{code}"] = {"is_live": True, "time": waktu_sekarang}
                return data
                
    except Exception as e:
        pass

    # --- FALLBACK MECHANISM (Sama persis seperti sebelumnya) ---
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_payload = json.load(f)
            
            st.session_state[f"wr_status_{code}"] = {
                "is_live": False, 
                "time": cache_payload.get("last_updated", "Unknown")
            }
            return cache_payload.get("data")
        except:
            pass

    st.session_state[f"wr_status_{code}"] = {"is_live": False, "time": "No Cache Available"}
    return None
