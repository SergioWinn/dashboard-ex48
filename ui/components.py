# ui/components.py

import streamlit as st
import re
from datetime import datetime, timedelta
import streamlit.components.v1 as components

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
        
        if raw_date:
            try:
                clean_date = raw_date.split('.')[0].replace('Z', '')
                session_date_wib = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            except:
                pass

        if session_date_wib and general_end_wib:
            if now_wib > general_end_wib:
                is_before_deadline = False
            else:
                jam_tutup_harian = general_end_wib.time()
                batas_penutupan_hari_h = datetime.combine(session_date_wib.date(), jam_tutup_harian)
                if now_wib > batas_penutupan_hari_h:
                    is_before_deadline = False
                    
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

    is_search_mode = bool(search_query)
    now_dt = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_dt.strftime('%d/%m/%Y %H:%M WIB')
    waktu_save = now_dt.strftime('%d%m%Y_%H%M') 
    
    judul_event = event_data.get('title', 'JKT48 Exclusive Event')
    safe_event_code = event_id if event_id else "EVENT"
    
    if is_search_mode:
        report_title = f"🔍 LAPORAN PENCARIAN: {search_query.upper()}"
        safe_query = search_query.strip().replace(' ', '').title()
        file_name = f"Kuota_{safe_event_code}_{safe_query}_Save_{waktu_save}"
    else:
        report_title = f"📅 LAPORAN TANGGAL: {selected_date}"
        safe_date = selected_date.split(' ')[0].replace('/', '') 
        file_name = f"Kuota_{safe_event_code}_{safe_date}_Save_{waktu_save}"

    banner_html = f"""
    <div id="share-banner" class="share-banner" style="display: none;">
        <div class="sb-left">
            <h3>{judul_event}</h3>
            <p>{report_title}</p>
        </div>
        <div class="sb-right">
            <div class="sb-time">⏱️ {waktu_sekarang}</div>
            <div class="sb-wm">LIVE TRACKER BY @ESTRELLAWIN19</div>
        </div>
    </div>
    """
    
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
            
            display_member = member_name.replace(' ', '&nbsp;')
            display_jalur = jalur_label.replace(' ', '&nbsp;')
            
            total_slot_capacity = tickets_sold + current_quota
            sold_percentage = (tickets_sold / total_slot_capacity * 100) if total_slot_capacity > 0 else 0
            
            is_sold_out = False
            if not is_before_deadline:
                cls, btn_text = "sold", "TUTUP"
                bar_color = "#EF4444"
                is_sold_out = True
            elif current_quota <= 0:
                cls, btn_text = "sold", "HABIS"
                sold_percentage = 100
                bar_color = "#EF4444"
                is_sold_out = True
            elif current_quota < warn_limit:
                cls, btn_text = "warn", f"SISA&nbsp;{current_quota}"
                bar_color = "#FBBF24"
            else:
                cls, btn_text = "avail", f"SISA&nbsp;{current_quota}"
                bar_color = "#10B981"

            safe_name_img = member_name.strip().lower()
            raw_photo_url = photo_map.get(safe_name_img, "")
            
            if raw_photo_url:
                if is_sold_out:
                    proxy_url = f"https://wsrv.nl/?url={raw_photo_url}&w=150&output=webp&filt=greyscale"
                else:
                    proxy_url = f"https://wsrv.nl/?url={raw_photo_url}&w=150&output=webp"
            else:
                proxy_url = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                
            img_html = f'<div class="c-photo" style="background-image: url(\'{proxy_url}\');" role="img" aria-label="Foto {member_name} JKT48"></div>'
                        
            if is_sold_out:
                badge_html = "" 
            elif current_quota < warn_limit:
                badge_text = "LOW"
                badge_html = f'<div class="c-badge">{badge_text}</div>'
            else:
                badge_text = "TERSEDIA"
                badge_html = f'<div class="c-badge">{badge_text}</div>'
                                
            combined_ui = f"""
            <div class="c-stats">
                <span>Terjual:&nbsp;<b>{tickets_sold}</b></span>
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
                    f'{badge_html}'
                    f'<div class="c-jalur" title="{jalur_label}">{display_jalur}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{display_member}</div>'
                    f'<div style="margin-top: auto; width: 100%;">'
                    f'{combined_ui}'
                    f'</div>'
                    f'</div>'
                )
            else: 
                card_html += (
                    f'<div class="ldp-card {cls}">'
                    f'{badge_html}'
                    f'<div class="c-jalur" title="{jalur_label}">{display_jalur}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{display_member}</div>'
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

    st.markdown(master_html_buffer, unsafe_allow_html=True)
    
    KODE_ADMIN_LIST = st.secrets.get("ADMIN_KEYS", [])
    if st.query_params.get("akses") in KODE_ADMIN_LIST:
        safe_name = file_name.replace('(', '').replace(')', '')
        components.html(f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; display: flex; gap: 10px; justify-content: center; align-items: center; overflow: hidden; }}
            .btn-action {{
                color: white; border: none; width: 50px; height: 50px; border-radius: 50%; font-size: 20px; cursor: pointer; 
                display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); outline: none;
            }}
            #dl-btn {{ background: #10B981; }}
            #dl-btn:hover {{ background: #0D9488; box-shadow: 0 0 15px rgba(16, 185, 129, 0.6); }}
            #copy-btn {{ background: #3B82F6; }}
            #copy-btn:hover {{ background: #1D4ED8; box-shadow: 0 0 15px rgba(59, 130, 246, 0.6); }}
        </style>
        
        <button class="btn-action" id="copy-btn" title="Salin Gambar ke Clipboard" aria-label="Salin gambar infografis ke clipboard">📋</button>
        <button class="btn-action" id="dl-btn" title="Download Gambar Infografis" aria-label="Unduh gambar infografis">📸</button>
        
        <script>
            try {{
                const iframe = window.frameElement;
                if (iframe) {{
                    iframe.style.position = 'fixed'; iframe.style.bottom = '30px'; iframe.style.right = '30px';
                    iframe.style.width = '130px'; iframe.style.height = '65px'; iframe.style.zIndex = '999999'; iframe.style.border = 'none';
                }}
            }} catch(e) {{}}

            function siapkanTarget() {{
                const target = window.parent.document.getElementById("laporan-container");
                const banner = window.parent.document.getElementById("share-banner");
                const appBgColor = window.getComputedStyle(window.parent.document.body).backgroundColor;

                if (target) {{
                    if(banner) banner.style.display = "flex";
                    target.style.padding = "20px"; target.style.backgroundColor = appBgColor; target.style.borderRadius = "15px";
                    target.dataset.themeBg = appBgColor; 
                }}
                return target;
            }}

            function kembalikanTarget(target, banner) {{
                if(banner) banner.style.display = "none";
                target.style.padding = "0px"; target.style.backgroundColor = "transparent";
            }}

            document.getElementById("dl-btn").addEventListener("click", function() {{
                const btn = this; const banner = window.parent.document.getElementById("share-banner"); const target = siapkanTarget();
                if(target) {{
                    btn.innerText = "⏳"; btn.style.background = "#FBBF24";
                    setTimeout(() => {{
                        window.html2canvas(target, {{ useCORS: true, backgroundColor: target.dataset.themeBg, scale: 2 }}).then(canvas => {{
                            kembalikanTarget(target, banner);
                            let link = document.createElement("a"); link.download = "{safe_name}.png"; link.href = canvas.toDataURL("image/png"); link.click();
                            btn.innerText = "📸"; btn.style.background = "#10B981";
                        }});
                    }}, 150);
                }}
            }});

            document.getElementById("copy-btn").addEventListener("click", function() {{
                const btn = this; const banner = window.parent.document.getElementById("share-banner"); const target = siapkanTarget();
                if(target) {{
                    btn.innerText = "⏳"; btn.style.background = "#FBBF24";
                    setTimeout(() => {{
                        window.html2canvas(target, {{ useCORS: true, backgroundColor: target.dataset.themeBg, scale: 2 }}).then(canvas => {{
                            kembalikanTarget(target, banner);
                            canvas.toBlob(function(blob) {{
                                try {{
                                    navigator.clipboard.write([new ClipboardItem({{ "image/png": blob }})]).then(function() {{
                                        btn.innerText = "✅"; btn.style.background = "#10B981"; 
                                        setTimeout(() => {{ btn.innerText = "📋"; btn.style.background = "#3B82F6"; }}, 1500);
                                    }}).catch(function(err) {{
                                        btn.innerText = "❌"; btn.style.background = "#EF4444";
                                        setTimeout(() => {{ btn.innerText = "📋"; btn.style.background = "#3B82F6"; }}, 1500);
                                    }});
                                }} catch (e) {{
                                    btn.innerText = "❌"; btn.style.background = "#EF4444";
                                    setTimeout(() => {{ btn.innerText = "📋"; btn.style.background = "#3B82F6"; }}, 1500);
                                }}
                            }}, "image/png");
                        }});
                    }}, 150);
                }}
            }});
        </script>
        """, height=70)
