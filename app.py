# app.py

import streamlit as st
import concurrent.futures
from datetime import datetime, timedelta

from core.api import get_member_database, get_active_exclusive_codes, fetch_exclusive_detail
from ui.styles import GLOBAL_CSS
from ui.components import render_event_cards, render_share_controls

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
            <span>Developed by <a href="https://x.com/estrellawin19" target="_blank" rel="noopener noreferrer">@estrellawin19</a></span>
            <a href="https://tako.id/Sportagame19Win" target="_blank" rel="noopener noreferrer" class="tako-btn">Support via Tako</a>
        </div>
        <div class="live-badge"><span class="live-dot"></span> LIVE MONITORING</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- 3. STREAMLIT FRAGMENT: ISOLATED AUTO-REFRESH ---
@st.fragment(run_every=5)
def live_dashboard_fragment(event_code, search_query, nickname_map, photo_map, available_only, raw_close_date):
    fresh_event_data = fetch_exclusive_detail(event_code)
    
    # --- 1. TENTUKAN STATUS EVENT CLOSED ---
    is_event_closed = False
    if raw_close_date:
        try:
            dt_close_wib = datetime.strptime(raw_close_date, "%Y-%m-%dT%H:%M:%S")
            now_wib = datetime.utcnow() + timedelta(hours=7)
            
            if now_wib >= dt_close_wib:
                is_event_closed = True # Set jadi True jika sudah lewat jam tutup
        except:
            pass
    # ---------------------------------------
        
    # --- CEK STATUS CLOUDFLARE WAITING ROOM ---
    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    
    if not wr_info.get("is_live"):
        st.warning(
            f"**JKT48 Server is currently in Cloudflare Waiting Room / Down.** "
            f"Showing last known good data backup (Last Updated: {wr_info.get('time')})."
        )
    else:
        current_time_wib = (datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M:%S')
        st.caption(f"Live data · Updated {current_time_wib} WIB")
    # ------------------------------------------
    
    if not fresh_event_data:
        st.warning("Waiting for data sync update...")
        return
        
    total_sold = 0
    sisa_kuota = 0
    
    for sesi in fresh_event_data.get('session', []):
        for m in sesi.get('session_detail', []):
            try:
                sold = int(m.get('tickets_sold') or 0)
                avail = int(m.get('available_quota') or 0)
            except (TypeError, ValueError):
                sold, avail = 0, 0
            total_sold += sold
            sisa_kuota += avail
            
    total_tiket = total_sold + sisa_kuota
    sold_rate = (total_sold / total_tiket * 100) if total_tiket > 0 else 0.0
            
    with st.container(border=True, key="summary_metrics"):
        col_m1, col_m2, col_m3 = st.columns(3, vertical_alignment="center")
        with col_m1:
            st.metric(label="Total Tickets", value=f"{total_tiket:,}")
        with col_m2:
            st.metric(label="Remaining", value=f"{sisa_kuota:,}")
        with col_m3:
            st.metric(label="Sold Rate", value=f"{sold_rate:.1f}%")
            
    # --- 3. KIRIM is_event_closed KE KOMPONEN CARD ---
    render_event_cards(fresh_event_data, search_query, nickname_map, photo_map, available_only, is_event_closed)

# --- 4. MAIN LAYOUT & DISCOVERY ---
nickname_map, photo_map = get_member_database()

active_codes = get_active_exclusive_codes()
if not active_codes:
    active_codes = ['EX783D', 'EX9A4A', 'EXCD2C', 'EXCB75']

active_events = []
with st.spinner("Fetching latest JKT48 Exclusive data..."):
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
        cat_label = "Video Call"
    elif cat == "TWO_SHOT":
        cat_label = "2-Shot"
    elif cat == "PHOTOCARD":
        cat_label = "Meet & Greet"
    else:
        cat_label = "Others"

    categories_dict.setdefault(cat_label, []).append(ev_info)

available_categories = dict(sorted(
    categories_dict.items(),
    key=lambda item: max(
        event["data"].get('valid_date_from', '') for event in item[1]
    ),
    reverse=True,
))

if available_categories:
    with st.container(border=True, key="event_filters"):
        col_cat, col_ev, col_search, col_toggle = st.columns(
            [1.3, 2.5, 1.2, 1.2],
            vertical_alignment="bottom",
        )

        with col_cat:
            selected_cat = st.selectbox("Category", list(available_categories.keys()))

        with col_ev:
            events_in_cat = available_categories[selected_cat]
            event_labels = [e["label"] for e in events_in_cat]
            selected_event_label = st.selectbox("JKT48 Event", event_labels)

            selected_event = next(e["data"] for e in events_in_cat if e["label"] == selected_event_label)

        with col_search:
            global_query = st.text_input("Search member", placeholder="Michie, Gracie...").lower().strip()
            
        with col_toggle:
            available_only = st.toggle("Available only", value=False)
            
    event_code = selected_event.get('code')
    
    # --- LOGIKA BARU: Cari jam tutup dari array sales_period (Jalur General) ---
    raw_close_date = None
    sales_periods = selected_event.get('sales_period', [])
    for sp in sales_periods:
        if sp.get('label') == 'General':
            raw_close_date = sp.get('end_date') # Ambil "2026-06-27T09:00:00"
            break
            
    # Jika di sales_period tidak ada, coba fallback ke valid_date_to
    if not raw_close_date and selected_event.get('valid_date_to'):
        # Kita potong mili-detiknya agar formatnya sama-sama "%Y-%m-%dT%H:%M:%S"
        raw_close_date = selected_event.get('valid_date_to').split('.')[0]
    # -------------------------------------------------------------------------
    
    st.markdown(f"### {selected_event.get('title', 'Event')}")
    st.caption(f"**Category:** {selected_event.get('category', '-').replace('_', ' ')} | **Price:** IDR {selected_event.get('default_price', 0):,}")
    
    # Kirim raw_close_date ke dalam fragment
    live_dashboard_fragment(event_code, global_query, nickname_map, photo_map, available_only, raw_close_date)

    try:
        admin_keys = st.secrets.get("ADMIN_KEYS", [])
    except Exception:
        admin_keys = []
    if isinstance(admin_keys, str):
        admin_keys = [admin_keys]
    access_key = st.query_params.get("akses", "")
    if access_key and access_key in admin_keys:
        render_share_controls(f"share_selection_{event_code}")
    
else:
    st.error("No active Exclusive events found or failed to fetch data.")
