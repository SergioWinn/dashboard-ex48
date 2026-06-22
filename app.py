import streamlit as st
import requests
import re
import concurrent.futures
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="JKT48 GLOBAL EXCLUSIVE", layout="wide", page_icon="🔴")

# --- 2. PREMIUM UI STYLING (Support Light & Dark Mode) ---
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
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
a.badge-link { text-decoration: none !important; display: block; margin-top: auto; width: 100%; }

/* Card Design */
.ldp-card { 
    background: rgba(128,128,128,0.05); 
    border-radius: 15px; 
    padding: 20px 15px; 
    border: 1px solid rgba(128,128,128,0.15); 
    display: flex; 
    flex-direction: column; 
    justify-content: space-between; 
    align-items: center;
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

/* Foto Kabesha CDN Proxy Async */
.c-photo { 
    width: 74px; 
    height: 74px; 
    border-radius: 50%; 
    background-size: cover; 
    background-position: center 10%; 
    background-repeat: no-repeat;
    margin: 0 auto 12px auto; 
    border: 2px solid rgba(128, 128, 128, 0.2); 
    box-shadow: 0 4px 10px rgba(0,0,0,0.15); 
    background-color: rgba(128, 128, 128, 0.1); 
}

.c-jalur { 
    font-size: 10px; 
    opacity: 0.6; 
    font-weight: 600; 
    text-transform: uppercase; 
    margin-bottom: 8px; 
    letter-spacing: 0.5px; 
    width: 100%; 
    max-width: 100%; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    display: block; 
}
.c-member { 
    font-weight: 700; font-size: 15px; line-height: 1.2; margin-bottom: 8px; 
    height: 2.4em; width: 100%;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
    overflow: hidden; text-overflow: ellipsis; 
}

/* --- SMART PROGRESS BUTTON (UI Upgrade) --- */
.c-stats { 
    font-size: 11px; 
    color: inherit; 
    opacity: 0.9; /* NAIKKAN DARI 0.75 KE 0.9 AGAR LEBIH TEGAS DI LIGHT MODE */
    margin-bottom: 6px; 
    display: flex; 
    justify-content: center;
    width: 100%; 
    padding: 0 4px; 
}
.c-stats b { 
    color: inherit; 
    opacity: 1; 
    margin-left: 3px; 
    font-weight: 800; 
}

.c-prog-btn { 
    position: relative; 
    width: 100%; 
    height: 32px; 
    /* Ubah background transparannya agar sedikit lebih gelap/kontras dari kartu */
    background: rgba(128, 128, 128, 0.25); 
    border-radius: 8px; 
    overflow: hidden; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    /* Pertebal sedikit border-nya */
    border: 1px solid rgba(128, 128, 128, 0.4); 
    transition: all 0.2s ease; 
}
.c-prog-btn:hover { border-color: rgba(255,255,255,0.3); transform: translateY(-1px); }
.c-prog-fill { 
    position: absolute; 
    left: 0; 
    top: 0; 
    height: 100%; 
    transition: width 0.5s ease; 
    z-index: 0; 
}

/* Pewarnaan Indikator Fill Button */
.ldp-card.avail .c-prog-fill { background: rgba(16,185,129, 0.8); }
.ldp-card.warn .c-prog-fill { background: rgba(217,119,6, 0.8); }
.ldp-card.sold .c-prog-fill { background: rgba(239,68,68, 0.8); }

.c-prog-text { 
    position: relative; 
    z-index: 1; 
    font-size: 11px; 
    font-weight: 800; 
    color: #fff; 
    letter-spacing: 0.5px; 
    text-shadow: 0 1px 3px rgba(0,0,0,0.8); 
}

/* --- SHAREABLE BANNER --- */
.share-banner {
    background: linear-gradient(135deg, #10B981 0%, #047857 100%);
    border-radius: 12px;
    padding: 12px 15px; 
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
    box-shadow: 0 4px 15px rgba(16,185,129,0.2);
    margin-bottom: 15px;
}
.sb-left h3 { margin: 0 0 4px 0; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; word-spacing: 2px; }
.sb-left p { margin: 0; font-size: 11px; opacity: 0.9; font-weight: 600; word-spacing: 1px; }
.sb-right { text-align: right; }
.sb-right .sb-time { font-size: 11px; font-weight: 700; background: rgba(0,0,0,0.25); padding: 4px 10px; border-radius: 20px; display: inline-block; border: 1px solid rgba(255,255,255,0.2); }
.sb-right .sb-wm { font-size: 9px; margin-top: 5px; opacity: 0.8; font-weight: 700; letter-spacing: 0.5px; }

@media (max-width: 500px) {
    .share-banner { flex-direction: column; align-items: flex-start; gap: 10px; padding: 12px; }
    .sb-right { text-align: left; width: 100%; display: flex; justify-content: space-between; align-items: center; }
    .sb-right .sb-wm { margin-top: 0; }
}

/* Mobile optimization */
@media (max-width: 500px) { 
    .cards-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; } 
    .ldp-card { padding: 18px 10px; }
    .c-member { font-size: 13px; }
    .ldp-title { font-size: 2rem; }
    .credit-container { flex-direction: column; gap: 10px; }
    .c-jalur { font-size: 8.5px; letter-spacing: 0px; } 
}
</style>
"""
st.markdown(css.replace('\n', '').replace('\r', ''), unsafe_allow_html=True)

# --- RENDER HEADER UTAMA ---
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

# --- 3. DATA ENGINE ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://jkt48.com/",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

@st.cache_data(ttl=3600)
def get_member_database():
    url = "https://jkt48.com/api/v1/members?lang=id"
    nickname_map = {}
    photo_map = {}
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
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

def render_event_cards(event_data, search_query, nickname_map, photo_map, available_only=False):
    event_id = event_data.get('code', '')
    category = event_data.get('category', 'GENERAL')
    purchase_link = f"https://jkt48.com/purchase/exclusive?code={event_id}"
    
    warn_limit = 5 if category in ["TWO_SHOT", "DIGITAL_PHOTOBOOK"] else 20
    sessions = event_data.get('session', [])
    
    if not sessions:
        st.info("Sesi belum tersedia untuk event ini.")
        return

    now_wib = datetime.utcnow() + timedelta(hours=7)
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

    # --- FUZZY SEARCH ---
    matched_full_names = set()
    if search_query:
        for nick, full_name in nickname_map.items():
            if search_query in nick or search_query in full_name:
                matched_full_names.add(full_name)

    sessions_by_date = {}
    for sesi in sessions:
        is_before_deadline = True
        raw_date = sesi.get('date', '')
        session_date_wib = None
        
        # --- JANGAN DIHAPUS: Ini yang menerjemahkan tanggal dari API ---
        if raw_date:
            try:
                clean_date = raw_date.split('.')[0].replace('Z', '')
                session_date_wib = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            except:
                pass

        # --- LOGIKA PENUTUPAN DINAMIS PER HARI (MENGIKUTI JAM GLOBAL) ---
        if session_date_wib and general_end_wib:
            
            # 1. Cek apakah sudah melewati batas global keseluruhan event
            if now_wib > general_end_wib:
                is_before_deadline = False
            else:
                # 2. Ambil komponen "Jam" dari batas penutupan global
                jam_tutup_harian = general_end_wib.time()
                
                # 3. Tempelkan jam tersebut ke tanggal pelaksanaan (Hari H)
                batas_penutupan_hari_h = datetime.combine(session_date_wib.date(), jam_tutup_harian)
                
                # 4. Cek apakah waktu saat ini sudah melewati batas tutup di Hari H tersebut
                if now_wib > batas_penutupan_hari_h:
                    is_before_deadline = False
                    
                # 5. Pastikan juga tidak melewati jam selesainya sesi itu sendiri
                if is_before_deadline and sesi.get('end_time'):
                    try:
                        t_end = datetime.strptime(sesi.get('end_time'), "%H:%M:%S").time()
                        session_end_datetime = datetime.combine(session_date_wib.date(), t_end)
                        if now_wib > session_end_datetime:
                            is_before_deadline = False
                    except:
                        pass

        members = sesi.get('session_detail', [])
                
        if search_query:
            members = [
                m for m in members 
                if m.get('jkt48_member_name', '').lower() in matched_full_names 
                or search_query in m.get('jkt48_member_name', '').lower()
            ]
            
        if available_only:
            if not is_before_deadline:
                continue
            members = [m for m in members if m.get('available_quota', 0) > 0]

        if not members:
            continue

        date_str = "Lainnya"
        if session_date_wib:
            if session_date_wib.date() == now_wib.date():
                date_str = f"{session_date_wib.strftime('%d/%m/%Y')} (Hari Ini)"
            elif session_date_wib.date() == (now_wib + timedelta(days=1)).date():
                date_str = f"{session_date_wib.strftime('%d/%m/%Y')} (Besok)"
            else:
                date_str = session_date_wib.strftime('%d/%m/%Y')
        elif raw_date:
            date_str = raw_date[:10]

        if date_str not in sessions_by_date:
            sessions_by_date[date_str] = []
            
        sesi_clean = sesi.copy()
        sesi_clean['filtered_members'] = members
        sesi_clean['is_before_deadline'] = is_before_deadline
        sesi_clean['session_date_wib'] = session_date_wib
        sessions_by_date[date_str].append(sesi_clean)

    unique_dates = list(sessions_by_date.keys())

    if search_query:
        active_sessions = []
        for d_sessions in sessions_by_date.values():
            active_sessions.extend(d_sessions)
        if active_sessions:
            st.success(f"🔎 Menampilkan seluruh jadwal untuk **'{search_query.title()}'** lintas tanggal.")
    else:
        if len(unique_dates) > 0:
            st.markdown(f"📅 **Tanggal Pelaksanaan:** {unique_dates[0] if len(unique_dates) == 1 else ''}")
            if len(unique_dates) > 1:
                selected_date = st.radio("Pilih Tanggal:", unique_dates, horizontal=True, key=f"filter_date_{event_id}", label_visibility="collapsed")
                st.write("")
            else:
                selected_date = unique_dates[0]
            active_sessions = sessions_by_date.get(selected_date, [])
        else:
            active_sessions = []

    if not active_sessions:
        if search_query:
            st.warning(f"Member '{search_query.title()}' tidak ditemukan pada event ini.")
        else:
            st.warning("🟢 Bersih! Tidak ada tiket atau sesi available yang aktif saat ini.")
        return

    # === SOLUSI GLOBAL SCREENSHOT (Pencarian & Per Hari) ===
    is_search_mode = bool(search_query)
    
    # Ambil waktu terkini untuk Banner dan Nama File (Waktu Klik/Save)
    now_dt = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_dt.strftime('%d/%m/%Y %H:%M WIB')
    waktu_save = now_dt.strftime('%d%m%Y_%H%M') # Format DDMMYYYY_HHMM untuk penanda waktu SAVE
    
    judul_event = event_data.get('title', 'JKT48 Exclusive Event')
    safe_event_code = event_id if event_id else "EVENT"
    
    # Penentuan Judul Banner Otomatis & Nama File (Code -> Tanggal/Subjek -> Tanggal Save)
    if is_search_mode:
        report_title = f"🔍 LAPORAN PENCARIAN: {search_query.upper()}"
        safe_query = search_query.strip().replace(' ', '').title()
        # Untuk mode search (lintas tanggal), posisi tanggal pelaksanaan diisi nama Member yang dicari
        file_name = f"Kuota_{safe_event_code}_{safe_query}_Save_{waktu_save}"
    else:
        report_title = f"📅 LAPORAN TANGGAL: {selected_date}"
        # Ambil tanggal pelaksanaan event (misal dari "28/06/2026 (Besok)" diperkecil jadi "28062026")
        safe_date = selected_date.split(' ')[0].replace('/', '') 
        file_name = f"Kuota_{safe_event_code}_{safe_date}_Save_{waktu_save}"

    banner_html = f"""
    <div id="share-banner" class="share-banner" style="display: none;">
        <div class="sb-left">
            <h3>{report_title}</h3>
            <p>{judul_event}</p>
        </div>
        <div class="sb-right">
            <div class="sb-time">⏱️ {waktu_sekarang}</div>
            <div class="sb-wm">LIVE TRACKER BY @ESTRELLAWIN19</div>
        </div>
    </div>
    """
    
    # Buka kontainer utama untuk target screenshot
    master_html_buffer = f'<div id="laporan-container" style="transition: 0.2s;">{banner_html}'
    
    if is_search_mode:
        master_html_buffer += '<div class="cards-grid">'

    for sesi in active_sessions:
        members = sesi['filtered_members']
        is_before_deadline = sesi['is_before_deadline']
        session_date_wib = sesi['session_date_wib']

        raw_label = sesi.get('label', 'Sesi')
        sesi_label = re.split(r'[\(·]', raw_label)[0].strip()
        time_info = f" | {sesi.get('start_time', '')[:5]} - {sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
        
        # Kalau TAMPILAN NORMAL (Tidak di-search), render judul Sesi langsung pakai HTML (Color Inherit untuk Light Mode)
        if not is_search_mode:
            master_html_buffer += f"<h4 style='color: inherit; margin-top: 5px; margin-bottom: 15px; font-family: Inter, sans-serif; font-size: 16px;'>{sesi_label} <span style='opacity:0.5; font-size: 13px; font-weight: 500;'>{time_info}</span></h4>"
            master_html_buffer += '<div class="cards-grid">'
            
        for m in members:
            member_name = m.get('jkt48_member_name', 'Unknown')
            current_quota = m.get('available_quota', 0)
            tickets_sold = m.get('tickets_sold', 0)
            jalur_label = m.get("label", "-")
            
            if is_search_mode:
                date_short = session_date_wib.strftime('%d/%m') if session_date_wib else ""
                sesi_short = sesi_label.replace("Sesi", "S.")
                time_range = f"{sesi.get('start_time', '')[:5]}-{sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
                time_str = f" ({time_range})" if time_range else ""
                jalur_label = f"{date_short} • {sesi_short}{time_str} • {jalur_label}"
                
            safe_name_img = member_name.strip().lower()
            raw_photo_url = photo_map.get(safe_name_img, "")
            
            if raw_photo_url:
                proxy_url = f"https://wsrv.nl/?url={raw_photo_url}&w=100&output=webp"
            else:
                proxy_url = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                
            img_html = f'<div class="c-photo" style="background-image: url(\'{proxy_url}\');" title="{member_name}"></div>'
            
            total_slot_capacity = tickets_sold + current_quota
            sold_percentage = (tickets_sold / total_slot_capacity * 100) if total_slot_capacity > 0 else 0
            
            if not is_before_deadline:
                cls, btn_text = "sold", "TUTUP"
                bar_color = "#EF4444"
            elif current_quota <= 0:
                cls, btn_text = "sold", "HABIS"
                sold_percentage = 100
                bar_color = "#EF4444"
            elif current_quota < warn_limit:
                cls, btn_text = "warn", f"SISA {current_quota}"
                bar_color = "#FBBF24"
            else:
                cls, btn_text = "avail", f"SISA {current_quota}"
                bar_color = "#10B981"
                
            combined_ui = f"""
            <div class="c-stats">
                <span>Terjual: <b>{tickets_sold}</b></span>
            </div>
            <div class="c-prog-btn">
                <div class="c-prog-fill" style="width: {sold_percentage}%; background-color: {bar_color};"></div>
                <div class="c-prog-text">{btn_text}</div>
            </div>
            """
            
            card_html = ""
            if current_quota <= 0 or not is_before_deadline: 
                card_html += (
                    f'<div class="ldp-card {cls}">'
                    f'<div class="c-jalur" title="{jalur_label}">{jalur_label}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{member_name}</div>'
                    f'<div style="margin-top: auto; width: 100%;">'
                    f'{combined_ui}'
                    f'</div>'
                    f'</div>'
                )
            else: 
                card_html += (
                    f'<div class="ldp-card {cls}">'
                    f'<div class="c-jalur" title="{jalur_label}">{jalur_label}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{member_name}</div>'
                    f'<a href="{purchase_link}" target="_blank" class="badge-link">'
                    f'{combined_ui}'
                    f'</a>'
                    f'</div>'
                )
            
            master_html_buffer += card_html

        if not is_search_mode:
            master_html_buffer += '</div>'
            
    if is_search_mode:
        master_html_buffer += '</div>'

    master_html_buffer += '</div>'

    # Render Seluruh DOM Sekaligus
    st.markdown(master_html_buffer, unsafe_allow_html=True)
    
    # --- SISTEM KEAMANAN (STRICT BACKDOOR) ---
    KODE_ADMIN_LIST = st.secrets.get("ADMIN_KEYS", [])
    
    if st.query_params.get("akses") in KODE_ADMIN_LIST:
        
        # --- TOMBOL INTEGRASI JS (Unduh & Salin Gambar) ---
        safe_name = file_name.replace('(', '').replace(')', '')
        components.html(f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            /* Mengatur tata letak dua tombol berdampingan */
            body {{ 
                margin: 0; padding: 0; background: transparent; 
                display: flex; gap: 10px; justify-content: center; align-items: center; 
                overflow: hidden; 
            }}
            
            .btn-action {{
                color: white; border: none; 
                width: 50px; height: 50px; border-radius: 50%; 
                font-size: 20px; cursor: pointer; 
                display: flex; justify-content: center; align-items: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                outline: none;
            }}
            
            /* Tombol Download (Hijau) */
            #dl-btn {{ background: #10B981; }}
            #dl-btn:hover {{ 
                background: #0D9488; 
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.6); 
            }}
            
            /* Tombol Copy (Biru/Ungu) */
            #copy-btn {{ background: #3B82F6; }}
            #copy-btn:hover {{ 
                background: #1D4ED8; 
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.6); 
            }}
        </style>
        
        <button class="btn-action" id="copy-btn" title="Salin Gambar ke Clipboard">📋</button>
        <button class="btn-action" id="dl-btn" title="Download Gambar Infografis">📸</button>
        
        <script>
            // Amankan konfigurasi posisi iframe melayang agar muat dua tombol
            try {{
                const iframe = window.frameElement;
                if (iframe) {{
                    iframe.style.position = 'fixed';
                    iframe.style.bottom = '30px';
                    iframe.style.right = '30px';
                    iframe.style.width = '130px'; /* Diperlebar agar dua tombol muat */
                    iframe.style.height = '65px';
                    iframe.style.zIndex = '999999';
                    iframe.style.border = 'none';
                }}
            }} catch(e) {{}}

            // Fungsi pembantu untuk memicu persiapan render banner & padding laporan
            function siapkanTarget() {{
                const target = window.parent.document.getElementById("laporan-container");
                const banner = window.parent.document.getElementById("share-banner");
                
                // BACA WARNA TEMA STREAMLIT SAAT INI (Light/Dark Mode)
                const appBgColor = window.getComputedStyle(window.parent.document.body).backgroundColor;

                if (target) {{
                    if(banner) banner.style.display = "flex";
                    target.style.padding = "20px";
                    target.style.backgroundColor = appBgColor; // Gunakan warna dinamis
                    target.style.borderRadius = "15px";
                    
                    // Simpan warna di dataset agar bisa dibaca oleh html2canvas
                    target.dataset.themeBg = appBgColor; 
                }}
                return target;
            }}

            // Fungsi pembantu untuk mengembalikan tampilan dashboard seperti semula
            function kembalikanTarget(target, banner) {{
                if(banner) banner.style.display = "none";
                target.style.padding = "0px";
                target.style.backgroundColor = "transparent";
            }}

            // --- FUNGSI 1: DOWNLOAD GAMBAR ---
            document.getElementById("dl-btn").addEventListener("click", function() {{
                const btn = this;
                const banner = window.parent.document.getElementById("share-banner");
                const target = siapkanTarget();
                
                if(target) {{
                    btn.innerText = "⏳";
                    btn.style.background = "#FBBF24";
                    
                    setTimeout(() => {{
                        window.html2canvas(target, {{
                            useCORS: true,
                            backgroundColor: target.dataset.themeBg, // Mengikuti tema
                            scale: 2
                        }}).then(canvas => {{
                            kembalikanTarget(target, banner);
                            
                            let link = document.createElement("a");
                            link.download = "{safe_name}.png";
                            link.href = canvas.toDataURL("image/png");
                            link.click();
                            
                            btn.innerText = "📸";
                            btn.style.background = "#10B981";
                        }});
                    }}, 150);
                }}
            }});

            // --- FUNGSI 2: COPY GAMBAR KE CLIPBOARD ---
            document.getElementById("copy-btn").addEventListener("click", function() {{
                const btn = this;
                const banner = window.parent.document.getElementById("share-banner");
                const target = siapkanTarget();
                
                if(target) {{
                    btn.innerText = "⏳";
                    btn.style.background = "#FBBF24";
                    
                    setTimeout(() => {{
                        window.html2canvas(target, {{
                            useCORS: true,
                            backgroundColor: target.dataset.themeBg, // Mengikuti tema
                            scale: 2
                        }}).then(canvas => {{
                            kembalikanTarget(target, banner);
                            
                            // Konversi canvas hasil render html2canvas menjadi Blob data PNG
                            canvas.toBlob(function(blob) {{
                                try {{
                                    // Memanfaatkan Clipboard API untuk menyuntikkan file gambar ke memori
                                    navigator.clipboard.write([
                                        new ClipboardItem({{ "image/png": blob }})
                                    ]).then(function() {{
                                        btn.innerText = "✅";
                                        btn.style.background = "#10B981"; // Hijau tanda sukses
                                        
                                        // Kembalikan ke ikon semula setelah 1.5 detik
                                        setTimeout(() => {{
                                            btn.innerText = "📋";
                                            btn.style.background = "#3B82F6";
                                        }}, 1500);
                                    }}).catch(function(err) {{
                                        btn.innerText = "❌";
                                        btn.style.background = "#EF4444";
                                        setTimeout(() => {{
                                            btn.innerText = "📋";
                                            btn.style.background = "#3B82F6";
                                        }}, 1500);
                                    }});
                                }} catch (e) {{
                                    btn.innerText = "❌";
                                    btn.style.background = "#EF4444";
                                    setTimeout(() => {{
                                        btn.innerText = "📋";
                                        btn.style.background = "#3B82F6";
                                    }}, 1500);
                                }}
                            }}, "image/png");
                        }});
                    }}, 150);
                }}
            }});
        </script>
        """, height=70)

# --- 4. STREAMLIT FRAGMENT: ISOLASI AUTO-REFRESH ---
@st.fragment(run_every=5)
def live_dashboard_fragment(event_code, search_query, nickname_map, photo_map, available_only):
    fresh_event_data = fetch_exclusive_detail(event_code)
    
    # --- INDIKATOR LAST UPDATED ---
    current_time_wib = (datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M:%S')
    st.caption(f"🔄 **Data Live - Terakhir Diperbarui:** {current_time_wib} WIB")
    
    if not fresh_event_data:
        st.warning("⏳ Menunggu pembaruan sinkronisasi data...")
        return
        
    total_sold = 0
    sisa_kuota = 0
    
    # Kalkulasi dasar
    for sesi in fresh_event_data.get('session', []):
        for m in sesi.get('session_detail', []):
            sold = m.get('tickets_sold', 0)
            avail = m.get('available_quota', 0)
            total_sold += sold
            sisa_kuota += avail
            
    # Kalkulasi Metrik Baru
    total_tiket = total_sold + sisa_kuota
    sold_rate = (total_sold / total_tiket * 100) if total_tiket > 0 else 0.0
            
    # Render Metrik Strip yang lebih ringkas dan to the point
    with st.container(border=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(label="🎟️ Total Tiket", value=f"{total_tiket:,}")
        with col_m2:
            st.metric(label="📦 Tiket Sisa", value=f"{sisa_kuota:,}")
        with col_m3:
            st.metric(label="🔥 Rate Terjual", value=f"{sold_rate:.1f}%")
            
    render_event_cards(fresh_event_data, search_query, nickname_map, photo_map, available_only)


# --- 5. MAIN LAYOUT & DISCOVERY ---
nickname_map, photo_map = get_member_database()

active_codes = get_active_exclusive_codes()
if not active_codes:
    active_codes = ['EX783D', 'EX9A4A', 'EXCD2C', 'EXCB75']

active_events = []
with st.spinner("⏳ Mengambil data esklusif JKT48 terbaru..."):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_exclusive_detail, active_codes)
        for data in results:
            if data and data.get('status') is not False: 
                active_events.append(data)

active_events.sort(key=lambda x: x.get('valid_date_from', ''), reverse=True)

# --- CASCADING DROPDOWNS SYSTEM ---
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
    
    # Penentuan Label Kategori
    if cat == "DIGITAL_PHOTOBOOK":
        cat_label = "📱 Video Call"
    elif cat == "TWO_SHOT":
        cat_label = "📸 2-shot"
    elif cat == "PHOTOCARD":
        cat_label = "🤝 Meet & Greet"
    else:
        cat_label = "🎟️ Lainnya"
        
    # Auto-create key jika belum ada, jadi 100% mustahil kena KeyError
    categories_dict.setdefault(cat_label, []).append(ev_info)

# Buat daftar kategori yang benar-benar memiliki data aktif
available_categories = {k: v for k, v in categories_dict.items() if len(v) > 0}

if available_categories:
    with st.container(border=True):
        col_cat, col_ev, col_search, col_toggle = st.columns([1.3, 2.5, 1.2, 1.2])
        
        with col_cat:
            selected_cat = st.selectbox("🎯 Pilih Kategori:", list(available_categories.keys()))
            
        with col_ev:
            events_in_cat = available_categories[selected_cat]
            event_labels = [e["label"] for e in events_in_cat]
            selected_event_label = st.selectbox("📌 Pilih Event JKT48:", event_labels)
            
            selected_event = next(e["data"] for e in events_in_cat if e["label"] == selected_event_label)
            
        with col_search:
            global_query = st.text_input("🔍 Cari Nama/Nickname...", placeholder="Ketik Michie, Gracie, Mars...").lower().strip()
            
        with col_toggle:
            st.write("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True) 
            available_only = st.toggle("🟢 Tersedia Saja", value=False)
            
    event_code = selected_event.get('code')
    
    st.markdown(f"### {selected_event.get('title', 'Event')}")
    st.caption(f"**Kategori:** {selected_event.get('category', '-').replace('_', ' ')} | **Harga:** Rp {selected_event.get('default_price', 0):,}")
    
    live_dashboard_fragment(event_code, global_query, nickname_map, photo_map, available_only)
    
else:
    st.error("Tidak ada event Exclusive yang aktif atau sistem gagal menarik data.")
