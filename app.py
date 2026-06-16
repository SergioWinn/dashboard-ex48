import streamlit as st
import requests
import re
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="JKT48 GLOBAL EXCLUSIVE", layout="wide", page_icon="🔴")

# --- 2. STABLE REFRESH (5 Detik) ---
st_autorefresh(interval=5000, key="global_exclusive_refresh")

# --- 3. PREMIUM UI STYLING ---
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }

/* Header & Badge */
.ldp-header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 20px; }
.ldp-title { font-weight: 800; font-size: 2.5rem; margin: 0; margin-bottom: 5px; }
.ldp-subtitle { font-weight: 600; font-size: 1.2rem; opacity: 0.7; margin-bottom: 10px; margin-top: 0; }

/* Credits & Donation */
.credit-container { display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 15px; font-size: 14px; }
.credit-container a { color: #10B981; text-decoration: none; font-weight: 700; }
.credit-container a:hover { text-decoration: underline; }
.tako-btn { background: #FF424D; color: white !important; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; text-decoration: none !important; display: inline-flex; align-items: center; gap: 5px; }
.tako-btn:hover { background: #E0353F; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(255,66,77,0.3); }

.live-badge { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; font-size: 12px; color: #10B981; background: rgba(16,185,129,0.1); padding: 5px 15px; border-radius: 30px; border: 1px solid rgba(16,185,129,0.2); }
.live-dot { height: 8px; width: 8px; background: #10B981; border-radius: 50%; animation: blink 2s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(1.2); } }

/* Grid System */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 20px; justify-content: center; margin-bottom: 30px; }

/* Link Badge Styling */
a.badge-link { text-decoration: none !important; display: block; margin-top: auto; }

/* Card Design */
.ldp-card { 
    background: rgba(128,128,128,0.05); 
    border-radius: 15px; 
    padding: 24px 15px; 
    border: 1px solid rgba(128,128,128,0.15); 
    display: flex; 
    flex-direction: column; 
    justify-content: space-between; 
    text-align: center; 
    transition: 0.3s ease;
    height: 100%;
}
.ldp-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-color: rgba(128,128,128,0.3); }

/* Border Status */
.ldp-card.avail { border-bottom: 5px solid #10B981; }
.ldp-card.warn { border-bottom: 5px solid #FBBF24; animation: glow 2s infinite; }
.ldp-card.sold { border-bottom: 5px solid #EF4444; opacity: 0.7; filter: grayscale(30%); }

@keyframes glow { 0% { box-shadow: 0 0 5px rgba(251,191,36,0.1); } 50% { box-shadow: 0 0 15px rgba(251,191,36,0.3); } 100% { box-shadow: 0 0 5px rgba(251,191,36,0.1); } }

.c-jalur { font-size: 10px; opacity: 0.5; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }
.c-member { font-weight: 700; font-size: 16px; line-height: 1.2; margin-bottom: 10px; height: 2.5em; overflow: hidden; }
.c-sold { font-size: 11px; font-weight: 600; color: #888; margin-bottom: 15px; background: rgba(128,128,128,0.1); padding: 4px; border-radius: 6px; }

.c-badge { font-size: 10px; font-weight: 800; padding: 7px; border-radius: 20px; text-transform: uppercase; width: 100%; display: block; }
.ldp-card.avail .c-badge { background: rgba(16,185,129,0.15); color: #10B981; cursor: pointer; }
.ldp-card.warn .c-badge { background: rgba(251,191,36,0.2); color: #D97706; cursor: pointer; }
.ldp-card.sold .c-badge { background: #EF4444; color: #fff; cursor: not-allowed; }

/* Mobile optimization */
@media (max-width: 500px) { 
    .cards-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; } 
    .ldp-card { padding: 18px 10px; }
    .c-member { font-size: 14px; }
    .ldp-title { font-size: 2rem; }
    .credit-container { flex-direction: column; gap: 10px; }
}
</style>
"""
st.markdown(css.replace('\n', '').replace('\r', ''), unsafe_allow_html=True)

# --- 4. RENDER HEADER ---
st.markdown(
    """
    <div class="ldp-header">
        <h1 class="ldp-title">GLOBAL EXCLUSIVE MONITOR</h1>
        <p class="ldp-subtitle">Live Tracker untuk Seluruh Event JKT48</p>
        <div class="credit-container">
            <span>Developed by <a href="https://x.com/estrellawin19" target="_blank">@estrellawin19</a></span>
            <a href="https://tako.id/Sportagame19Win" target="_blank" class="tako-btn">🐙 Support via Tako</a>
        </div>
        <div class="live-badge"><span class="live-dot"></span> MONITORING LIVE</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- 5. DATA ENGINE (GENERAL API FETCHING) ---
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

@st.cache_data(ttl=3600) # Cache 1 jam
def get_active_exclusive_codes():
    try:
        r = requests.get("https://jkt48.com/purchase/exclusive", headers=HEADERS, timeout=10)
        codes = set(re.findall(r'EX[A-Z0-9]{4,6}', r.text))
        return list(codes)
    except:
        return []

@st.cache_data(ttl=4) # Cache 4 detik
def fetch_exclusive_detail(code):
    url = f"https://jkt48.com/api/v1/exclusives/{code}?lang=id"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get('data')
    except:
        pass
    return None

def render_event_cards(event_data, search_query):
    event_id = event_data.get('code', '')
    category = event_data.get('category', 'GENERAL')
    purchase_link = f"https://jkt48.com/purchase/exclusive?code={event_id}"
    
    warn_limit = 5 if category in ["TWO_SHOT", "DIGITAL_PHOTOBOOK"] else 20
    
    sessions = event_data.get('session', [])
    if not sessions:
        st.info("Sesi belum tersedia untuk event ini.")
        return

    has_data = False
    for sesi in sessions:
        members = sesi.get('session_detail', [])
        
        # Filter Search
        if search_query:
            members = [m for m in members if search_query in m.get('jkt48_member_name', '').lower()]
            
        if not members:
            continue
            
        has_data = True
        
        # Ekstraksi Label & Waktu
        sesi_label = sesi.get('label', 'Sesi')
        time_info = f" | {sesi.get('start_time', '')[:5]} - {sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
        
        # --- FIX ZONAWAKTU (UTC ke WIB) ---
        raw_date = sesi.get('date', '')
        date_info = ""
        if raw_date:
            try:
                # Format JSON: "2026-06-27T17:00:00.000Z"
                # Buang 'Z' dan milidetik sebelum di-parse
                clean_date = raw_date.split('.')[0].replace('Z', '')
                dt_utc = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
                # Konversi ke WIB (UTC+7)
                dt_wib = dt_utc + timedelta(hours=7)
                date_info = f" ({dt_wib.strftime('%d/%m/%Y')})"
            except:
                date_info = f" ({raw_date[:10]})"
        # ----------------------------------
        
        st.markdown(f"#### {sesi_label} <small style='opacity:0.5'>{time_info}{date_info}</small>", unsafe_allow_html=True)
        
        html = '<div class="cards-grid">'
        for m in members:
            member_name = m.get('jkt48_member_name', 'Unknown')
            current_quota = m.get('available_quota', 0)
            tickets_sold = m.get('tickets_sold', 0)
            jalur_label = m.get("label", "-")
            
            sold_text = f"<div class='c-sold'>Terjual: {tickets_sold}</div>"
            
            if current_quota <= 0: 
                cls, lbl = "sold", "HABIS"
                html += f'<div class="ldp-card {cls}"><div class="c-jalur">{jalur_label}</div><div class="c-member">{member_name}</div>{sold_text}<div class="c-badge">{lbl}</div></div>'
            else: 
                if current_quota < warn_limit: 
                    cls, lbl = "warn", f"SISA {current_quota}"
                else: 
                    cls, lbl = "avail", f"SISA {current_quota}"
                
                html += f'<div class="ldp-card {cls}"><div class="c-jalur">{jalur_label}</div><div class="c-member">{member_name}</div>{sold_text}<a href="{purchase_link}" target="_blank" class="badge-link"><div class="c-badge">{lbl}</div></a></div>'
        
        st.markdown(html + '</div>', unsafe_allow_html=True)
        
    if not has_data and search_query:
        st.warning("Member tidak ditemukan pada event ini.")


# --- 6. MAIN LAYOUT & DISCOVERY ---

st.info("💡 **Petunjuk:** Klik tombol **SISA** pada kartu member untuk langsung menuju halaman pembelian tiket JKT48.")
global_query = st.text_input("🔍 Cari Member (Global Search)...", placeholder="Masukkan nama member...").lower().strip()
st.write("")

# Tarik semua kode event yang sedang aktif di web
active_codes = get_active_exclusive_codes()

# Fallback codes
if not active_codes:
    active_codes = ['EX783D', 'EX9A4A', 'EXCD2C', 'EXCB75']

# Ambil payload JSON secara berurutan
active_events = []
for code in active_codes:
    data = fetch_exclusive_detail(code)
    if data and data.get('status') is not False: 
        active_events.append(data)

# Render Dashboard Dinamis
if active_events:
    tab_titles = []
    for ev in active_events:
        cat = ev.get('category', '')
        icon = "📸" if cat == "TWO_SHOT" else "🤝" if cat == "PHOTOCARD" else "📱" if cat == "DIGITAL_PHOTOBOOK" else "🎟️"
        title = ev.get('title', 'Unknown Event')
        
        short_title = (title[:25] + '..') if len(title) > 25 else title
        tab_titles.append(f"{icon} {short_title}")
        
    rendered_tabs = st.tabs(tab_titles)
    
    for idx, tab in enumerate(rendered_tabs):
        with tab:
            event = active_events[idx]
            st.markdown(f"### {event.get('title', 'Event')}")
            
            meta_html = f"""
            <div style="font-size: 14px; opacity: 0.8; margin-bottom: 20px;">
                <b>Kategori:</b> {event.get('category', '-').replace('_', ' ')} | 
                <b>Harga Default:</b> Rp {event.get('default_price', 0):,} | 
                <b>Kuota Total:</b> {event.get('total_quota', 0):,}
            </div>
            """
            st.markdown(meta_html, unsafe_allow_html=True)
            
            render_event_cards(event, global_query)
else:
    st.error("Tidak ada event Exclusive yang sedang aktif atau sistem gagal menarik data dari JKT48.")
