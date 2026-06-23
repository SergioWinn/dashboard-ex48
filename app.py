# app.py

import streamlit as st
import concurrent.futures
from datetime import datetime, timedelta

from core.api import get_member_database, get_active_exclusive_codes, fetch_exclusive_detail
from ui.styles import GLOBAL_CSS
from ui.components import render_event_cards

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="JKT48 GLOBAL EXCLUSIVE", layout="wide", page_icon="🔴")

# --- 2. APPLY CSS ---
st.markdown(GLOBAL_CSS.replace('\n', '').replace('\r', ''), unsafe_allow_html=True)

# --- RENDER MAIN HEADER ---
st.markdown(
    """
    <div class="ldp-header">
        <h1 class="ldp-title">GLOBAL EXCLUSIVE MONITOR</h1>
        <p class="ldp-subtitle">Live Tracker for All JKT48 Exclusive Events</p>
        <div class="credit-container">
            <span>Developed by <a href="https://x.com/estrellawin19" target="_blank">@estrellawin19</a></span>
            <a href="https://tako.id/Sportagame19Win" target="_blank" class="tako-btn">🐙 Support via Tako</a>
        </div>
        <div class="live-badge"><span class="live-dot"></span> LIVE MONITORING</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- 3. STREAMLIT FRAGMENT: ISOLATED AUTO-REFRESH ---
@st.fragment(run_every=5)
def live_dashboard_fragment(event_code, search_query, nickname_map, photo_map, available_only):
    fresh_event_data = fetch_exclusive_detail(event_code)
    
    current_time_wib = (datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M:%S')
    st.caption(f"🔄 **Live Data - Last Updated:** {current_time_wib} WIB")
    
    if not fresh_event_data:
        st.warning("⏳ Waiting for data sync update...")
        return
        
    total_sold = 0
    sisa_kuota = 0
    
    for sesi in fresh_event_data.get('session', []):
        for m in sesi.get('session_detail', []):
            sold = m.get('tickets_sold', 0)
            avail = m.get('available_quota', 0)
            total_sold += sold
            sisa_kuota += avail
            
    total_tiket = total_sold + sisa_kuota
    sold_rate = (total_sold / total_tiket * 100) if total_tiket > 0 else 0.0
            
    with st.container(border=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="🎟️ Total Tickets", value=f"{total_tiket:,}")
        with col_m2:
            st.metric(label="📦 Remaining", value=f"{sisa_kuota:,}")
        with col_m3:
            st.metric(label="🔥 Sold Rate", value=f"{sold_rate:.1f}%")
            
    render_event_cards(fresh_event_data, search_query, nickname_map, photo_map, available_only)


# --- 4. MAIN LAYOUT & DISCOVERY ---
nickname_map, photo_map = get_member_database()

active_codes = get_active_exclusive_codes()
if not active_codes:
    active_codes = ['EX783D', 'EX9A4A', 'EXCD2C', 'EXCB75']

active_events = []
with st.spinner("⏳ Fetching latest JKT48 Exclusive data..."):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_exclusive_detail, active_codes)
        for data in results:
            if data and data.get('status') is not False: 
                active_events.append(data)

active_events.sort(key=lambda x: x.get('valid_date_from', ''), reverse=True)

categories_dict = {}
for ev in active_events:
    cat = ev.get('category', '')
    title = ev.get('title', 'Unknown Event')
    raw_open_date = ev.get('valid_date_from', '')
    open_date_str = ""
    if raw_open_date:
        try:
            dt_wib = datetime.strptime(raw_open_date.split('.')[0].replace('Z', ''), "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            open_date_str = f"[{dt_wib.strftime('%d/%m/%Y')}] "
        except:
            pass
            
    dropdown_label = f"{open_date_str}{title}"
    ev_info = {"label": dropdown_label, "data": ev}
    
    if cat == "DIGITAL_PHOTOBOOK":
        cat_label = "📱 Video Call"
    elif cat == "TWO_SHOT":
        cat_label = "📸 2-Shot"
    elif cat == "PHOTOCARD":
        cat_label = "🤝 Meet & Greet"
    else:
        cat_label = "🎟️ Others"
        
    categories_dict.setdefault(cat_label, []).append(ev_info)

available_categories = {k: v for k, v in categories_dict.items() if len(v) > 0}

if available_categories:
    with st.container(border=True):
        col_cat, col_ev, col_search, col_toggle = st.columns([1.3, 2.5, 1.2, 1.2])
        
        with col_cat:
            selected_cat = st.selectbox("🎯 Select Category:", list(available_categories.keys()))
            
        with col_ev:
            events_in_cat = available_categories[selected_cat]
            event_labels = [e["label"] for e in events_in_cat]
            selected_event_label = st.selectbox("📌 Select JKT48 Event:", event_labels)
            
            selected_event = next(e["data"] for e in events_in_cat if e["label"] == selected_event_label)
            
        with col_search:
            global_query = st.text_input("🔍 Search Name/Nickname...", placeholder="Type Michie, Gracie...").lower().strip()
            
        with col_toggle:
            st.write("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True) 
            available_only = st.toggle("🟢 Available Only", value=False)
            
    event_code = selected_event.get('code')
    
    st.markdown(f"### {selected_event.get('title', 'Event')}")
    # Mengubah format mata uang dari Rp menjadi IDR standar internasional
    st.caption(f"**Category:** {selected_event.get('category', '-').replace('_', ' ')} | **Price:** IDR {selected_event.get('default_price', 0):,}")
    
    live_dashboard_fragment(event_code, global_query, nickname_map, photo_map, available_only)
    
else:
    st.error("No active Exclusive events found or failed to fetch data.")
