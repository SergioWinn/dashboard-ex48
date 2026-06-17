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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;700;800&display=swap');
html, body, .stApp { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }

/* Header & Badge */
.ldp-header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 20px; }
.ldp-title { font-weight: 800; font-size: 2.5rem; margin: 0; margin-bottom: 5px; }
.stElementContainer [data-testid="stExpander"] { margin-bottom: 25px !important; }
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

/* Custom Container Dropdown */
.selectbox-container { margin-bottom: 25px; padding: 20px; background: rgba(128,128,128,0.05); border-radius: 15px; border: 1px solid rgba(128,128,128,0.15); }

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

@st.cache_data(ttl=300)
def get_active_exclusive_codes():
    url = "https://jkt48.com/api/v1/exclusives?lang=id"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
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
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get('data')
    except:
        pass
    return None

def render_event_cards(event_data, search_query, available_only=False):
    event_id = event_data.get('code', '')
    category = event_data.get('category', 'GENERAL')
    purchase_link = f"https://jkt48.com/purchase/exclusive?code={event_id}"
    
    warn_limit = 5 if category in ["TWO_SHOT", "DIGITAL_PHOTOBOOK"] else 20
    sessions = event_data.get('session', [])
    
    if not sessions:
        st.info("Sesi belum tersedia untuk event ini.")
        return

    # --- AMBIL WAKTU SEKARANG (WIB) ---
    now_wib = datetime.utcnow() + timedelta(hours=7)

    # --- CARI DEADLINE PENJUALAN UMUM (END DATE EVENT) ---
    general_end_wib = None
    for period in event_data.get('sales_period', []):
        if not period.get('is_ofc_only', False) or period.get('label') == 'General':
            ed = period.get('end_date')
            if ed:
                try:
                    clean_ed = ed.split('.')[0].replace('Z', '')
                    general_end_wib = datetime.strptime(clean_ed, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
                except:
                    pass

    # --- SEPARASI TANGGAL ---
    sessions_by_date = {}
    for sesi in sessions:
        raw_date = sesi.get('date', '')
        date_str = "Lainnya"
        if raw_date:
            try:
                clean_date = raw_date.split('.')[0].replace('Z', '')
                dt_utc = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
                dt_wib = dt_utc + timedelta(hours=7)
                date_str = dt_wib.strftime('%d/%m/%Y')
            except:
                date_str = raw_date[:10]
        
        if date_str not in sessions_by_date:
            sessions_by_date[date_str] = []
        sessions_by_date[date_str].append(sesi)
        
    unique_dates = list(sessions_by_date.keys())
    
    # Mode normal: pilah per tanggal. Mode search: bypass tanggal
    if search_query:
        active_sessions = sessions
        st.success(f"🔎 Menampilkan seluruh jadwal untuk **'{search_query}'** lintas tanggal.")
    else:
        if len(unique_dates) > 1:
            selected_date = st.radio("📅 Pilih Tanggal Pelaksanaan Event:", unique_dates, horizontal=True, key=f"filter_date_{event_id}")
            st.write("")
        else:
            selected_date = unique_dates[0] if unique_dates else None
        active_sessions = sessions_by_date.get(selected_date, []) if selected_date else sessions

    # --- RUN LOGIKA ITERASI SESI ---
    for sesi in active_sessions:
        # Evaluasi batas waktu (deadline) sesi ini secara dinamis
        is_before_deadline = True
        
        raw_date = sesi.get('date', '')
        session_date_wib = None
        if raw_date:
            try:
                clean_date = raw_date.split('.')[0].replace('Z', '')
                session_date_wib = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            except:
                pass

        # Aturan Deadline Berdasarkan Kategori
        if category == "DIGITAL_PHOTOBOOK" and session_date_wib:
            # Aturan VC: Jam 7 pagi WIB di Hari H Pelaksanaan Sesi
            vc_deadline = datetime.combine(session_date_wib.date(), datetime.strptime("07:00:00", "%H:%M:%S").time())
            is_before_deadline = now_wib < vc_deadline
        else:
            # Aturan Biasa (2-Shot / PC): Cek General End Date Event
            if general_end_wib:
                is_before_deadline = now_wib < general_end_wib
            
            # Pengaman: Jika jam sesi berakhir sudah lewat di hari H teater, otomatis ditutup
            if session_date_wib and sesi.get('end_time'):
                try:
                    t_end = datetime.strptime(sesi.get('end_time'), "%H:%M:%S").time()
                    session_end_datetime = datetime.combine(session_date_wib.date(), t_end)
                    if now_wib > session_end_datetime:
                        is_before_deadline = False
                except:
                    pass

        members = sesi.get('session_detail', [])
        
        # Jalankan Filter Nama (Search)
        if search_query:
            members = [m for m in members if search_query in m.get('jkt48_member_name', '').lower()]
            
        # Jalankan Filter Ketersediaan Aktual (Toggle Available Only)
        if available_only:
            if not is_before_deadline:
                continue  # Sembunyikan seluruh sesi jika sudah lewat deadline
            else:
                members = [m for m in members if m.get('available_quota', 0) > 0]
                
        if not members:
            continue
            
        # Ekstraksi Label Sesi Bersih
        raw_label = sesi.get('label', 'Sesi')
        sesi_label = re.split(r'[\(·]', raw_label)[0].strip()
        time_info = f" | {sesi.get('start_time', '')[:5]} - {sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
        
        # Tampilkan tanggal di header sesi jika dalam mode global search
        date_header = f" ({session_date_wib.strftime('%d/%m/%Y')})" if search_query and session_date_wib else ""
        
        st.markdown(f"#### {sesi_label} <small style='opacity:0.5'>{time_info}{date_header}</small>", unsafe_allow_html=True)
        
        html = '<div class="cards-grid">'
        for m in members:
            member_name = m.get('jkt48_member_name', 'Unknown')
            current_quota = m.get('available_quota', 0)
            tickets_sold = m.get('tickets_sold', 0)
            jalur_label = m.get("label", "-")
            
            sold_text = f"<div class='c-sold'>Terjual: {tickets_sold}</div>"
            
            # Logika pewarnaan card (Mendukung status CLOSED jika lewat jam deadline)
            if current_quota <= 0 or not is_before_deadline: 
                cls, lbl = "sold", "CLOSED" if not is_before_deadline else "HABIS"
                html += f'<div class="ldp-card {cls}"><div class="c-jalur">{jalur_label}</div><div class="c-member">{member_name}</div>{sold_text}<div class="c-badge">{lbl}</div></div>'
            else: 
                if current_quota < warn_limit: 
                    cls, lbl = "warn", f"SISA {current_quota}"
                else: 
                    cls, lbl = "avail", f"SISA {current_quota}"
                
                html += f'<div class="ldp-card {cls}"><div class="c-jalur">{jalur_label}</div><div class
