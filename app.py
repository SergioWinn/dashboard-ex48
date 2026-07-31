# app.py

import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from html import escape

from core.api import get_active_exclusive_events, get_member_database, fetch_exclusive_detail
from core.refresh import get_detail_refresh_interval
from ui.styles import GLOBAL_CSS
from ui.components import render_event_cards, render_share_controls

try:
    from ui.components import install_motion_observer
except ImportError:
    install_motion_observer = None

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="JKT48 GLOBAL EXCLUSIVE", layout="wide", page_icon="🔴")

# --- 2. APPLY CSS ---
st.markdown(GLOBAL_CSS.replace('\n', '').replace('\r', ''), unsafe_allow_html=True)
if install_motion_observer:
    install_motion_observer()

# --- RENDER MAIN HEADER ---
st.markdown(
    """
    <div class="ldp-header">
        <div class="ldp-wordmark">
            <h1 class="ldp-title">GLOBAL EXCLUSIVE MONITOR</h1>
        </div>
        <a href="https://tako.id/Sportagame19Win" target="_blank" rel="noopener noreferrer" class="tako-btn">Support project ↗</a>
    </div>
    <p class="ldp-subtitle">Find an event, isolate a date, and scan which member slots can still be purchased.</p>
    """,
    unsafe_allow_html=True
)


@st.fragment(run_every=5)
def live_dashboard_fragment(
    selected_event,
    search_query,
    nickname_map,
    photo_map,
    available_only,
    raw_close_date,
    current_event_codes,
):
    refreshed_events = get_active_exclusive_events()
    refreshed_codes = {event.get("code") for event in refreshed_events if event.get("code")}
    if refreshed_codes.difference(current_event_codes):
        st.rerun()

    event_code = selected_event.get("code")
    event_state_key = f"event_data_{event_code}"
    attempt_state_key = f"event_fetch_attempt_{event_code}"
    event_data = st.session_state.get(event_state_key) or selected_event
    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    last_attempt = st.session_state.get(attempt_state_key, 0.0)

    if event_code and (
        event_state_key not in st.session_state
        or time.monotonic() - last_attempt >= refresh_interval
    ):
        fetched_event_data = fetch_exclusive_detail(event_code)
        st.session_state[attempt_state_key] = time.monotonic()
        if fetched_event_data:
            st.session_state[event_state_key] = fetched_event_data
            event_data = fetched_event_data

    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    has_event_detail = "session" in event_data

    if not raw_close_date:
        for sales_period in event_data.get("sales_period", []):
            if sales_period.get("label") == "General":
                raw_close_date = sales_period.get("end_date")
                break
    if not raw_close_date and event_data.get("valid_date_to"):
        raw_close_date = event_data["valid_date_to"].split(".")[0]

    source_class = "is-live" if wr_info.get("is_live") else "is-cached"
    source_label = "LIVE API" if wr_info.get("is_live") else "CACHED DATA"
    sync_label = wr_info.get("time") or "Waiting for first sync"
    event_title = escape(str(event_data.get("title", "Event")))
    event_category = escape(str(event_data.get("category", "-")).replace("_", " "))
    event_price = int(event_data.get("default_price") or 0)
    st.markdown(
        f"""
        <section class="event-index-head">
            <div>
                <div class="event-meta">{event_category} · IDR {event_price:,}</div>
                <h2>{event_title}</h2>
            </div>
            <div class="source-readout {source_class}">
                <strong>{source_label}</strong>
                <span>{refresh_interval}s poll interval</span>
                <small>{escape(str(sync_label))}</small>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    is_event_closed = False
    if raw_close_date:
        try:
            dt_close_wib = datetime.strptime(raw_close_date, "%Y-%m-%dT%H:%M:%S")
            if now_wib >= dt_close_wib:
                is_event_closed = True
        except Exception:
            pass

    if has_event_detail and wr_info.get("is_live"):
        pass
    elif has_event_detail:
        st.warning(
            f"Live API unavailable ({wr_info.get('reason', 'Waiting Room / upstream down')}). "
            f"Showing last known good data ({wr_info.get('time')}). "
            f"Retrying every {refresh_interval}s."
        )
    elif not wr_info.get("is_live"):
        st.warning(
            f"**JKT48 Server is currently in Cloudflare Waiting Room / Down.** "
            f"Showing last known good data backup (Last Updated: {wr_info.get('time')})."
        )
    else:
        st.warning("Event details are temporarily unavailable. Showing event list data only.")

    if not has_event_detail:
        return

    total_sold = 0
    sisa_kuota = 0
    for sesi in event_data.get("session", []):
        for member in sesi.get("session_detail", []):
            try:
                sold = int(member.get("tickets_sold") or 0)
                avail = int(member.get("available_quota") or 0)
            except (TypeError, ValueError):
                sold, avail = 0, 0
            total_sold += sold
            sisa_kuota += avail

    total_tiket = total_sold + sisa_kuota
    sold_rate = (total_sold / total_tiket * 100) if total_tiket > 0 else 0.0

    with st.container(border=False, key="summary_metrics"):
        col_m1, col_m2, col_m3 = st.columns(3, vertical_alignment="center")
        with col_m1:
            st.metric(label="Total Tickets", value=f"{total_tiket:,}")
        with col_m2:
            st.metric(label="Remaining", value=f"{sisa_kuota:,}")
        with col_m3:
            st.metric(label="Sold Rate", value=f"{sold_rate:.1f}%")

    render_event_cards(event_data, search_query, nickname_map, photo_map, available_only, is_event_closed)


nickname_map, photo_map = get_member_database()
active_events = get_active_exclusive_events()

categories_dict = {}
for ev in active_events:
    cat = ev.get("category", "")
    title = ev.get("title", "Unknown Event")
    raw_open_date = ev.get("valid_date_from", "")
    open_date_str = ""
    if raw_open_date:
        try:
            dt_wib = datetime.strptime(raw_open_date.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            open_date_str = f"[{dt_wib.strftime('%d/%m/%Y')}] "
        except Exception:
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

for events in categories_dict.values():
    events.sort(
        key=lambda event: event["data"].get("valid_date_from", ""),
        reverse=True,
    )

category_filters = dict(sorted(
    categories_dict.items(),
    key=lambda item: max(event["data"].get("valid_date_from", "") for event in item[1]),
    reverse=True,
))
available_categories = category_filters

if available_categories:
    with st.container(border=False, key="event_filters"):
        col_cat, col_ev, col_search, col_toggle = st.columns([1.3, 2.5, 1.2, 1.2], vertical_alignment="bottom")

        with col_cat:
            selected_cat = st.selectbox(
                "Category",
                list(available_categories.keys()),
            )

        with col_ev:
            events_in_cat = available_categories[selected_cat]
            event_labels = [e["label"] for e in events_in_cat]
            selected_event_label = st.selectbox("JKT48 Event", event_labels)
            selected_event = next(e["data"] for e in events_in_cat if e["label"] == selected_event_label)

        with col_search:
            global_query = st.text_input("Search member", placeholder="Michie, Gracie…").lower().strip()

        with col_toggle:
            available_only = st.toggle("Available only", value=False)

    raw_close_date = None
    for sales_period in selected_event.get("sales_period", []):
        if sales_period.get("label") == "General":
            raw_close_date = sales_period.get("end_date")
            break

    if not raw_close_date and selected_event.get("valid_date_to"):
        raw_close_date = selected_event.get("valid_date_to").split(".")[0]

    live_dashboard_fragment(
        selected_event,
        global_query,
        nickname_map,
        photo_map,
        available_only,
        raw_close_date,
        tuple(event.get("code") for event in active_events if event.get("code")),
    )

    try:
        admin_keys = st.secrets.get("ADMIN_KEYS", [])
    except Exception:
        admin_keys = []
    if isinstance(admin_keys, str):
        admin_keys = [admin_keys]
    access_key = st.query_params.get("akses", "")
    if access_key and access_key in admin_keys:
        render_share_controls(f"share_selection_{selected_event.get('code', 'unknown')}")
else:
    st.error("No active Exclusive events found or failed to fetch data.")

st.markdown(
    """
    <footer class="index-footer">
        <span>GLOBAL EXCLUSIVE MONITOR · DATA FROM JKT48 PUBLIC API</span>
        <span>DEVELOPED BY <a href="https://x.com/estrellawin19" target="_blank" rel="noopener noreferrer">@ESTRELLAWIN19</a></span>
    </footer>
    """,
    unsafe_allow_html=True,
)
