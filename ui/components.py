# ui/components.py

import streamlit as st
import re
from html import escape
from datetime import datetime, timedelta
import streamlit.components.v1 as components

def render_event_cards(fresh_event_data, search_query, nickname_map, photo_map, available_only, is_event_closed=False):
    # PERBAIKAN BUG: Samakan variabel parameter dengan yang dipakai di dalam fungsi
    event_data = fresh_event_data 
    
    event_id = event_data.get('code', '')
    category = event_data.get('category', 'GENERAL')
    purchase_link = f"https://jkt48.com/purchase/exclusive?code={event_id}"
    
    warn_limit = 5 if category in ["TWO_SHOT", "DIGITAL_PHOTOBOOK"] else 20
    sessions = event_data.get('session', [])
    
    if not sessions:
        st.info("Sessions are not available for this event yet.")
        return

    now_wib = datetime.utcnow() + timedelta(hours=7)
    general_end_wib = None
    
    # --- PERBAIKAN LOGIKA WAKTU TUTUP ---
    for period in event_data.get('sales_period', []):
        if not period.get('is_ofc_only', False) or period.get('label') == 'General':
            ed = period.get('end_date')
            if ed:
                try:
                    clean_ed = ed.split('.')[0]
                    if 'Z' in ed:
                        # Kalau ada Z berarti beneran UTC, baru ditambah 7 jam
                        general_end_wib = datetime.strptime(clean_ed.replace('Z', ''), "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
                    else:
                        # Data dari API JKT48 untuk sales_period sudah WIB (tanpa 'Z')
                        # Jadi TIDAK PERLU ditambah 7 jam lagi
                        general_end_wib = datetime.strptime(clean_ed, "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
    # ------------------------------------

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
                if 'T' in clean_date:
                    session_date_wib = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
                else:
                    session_date_wib = datetime.strptime(clean_date, "%Y-%m-%d")
            except:
                pass

        if general_end_wib:
            if now_wib > general_end_wib:
                is_before_deadline = False
            elif session_date_wib:
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
            # Jika mode available dihidupkan, dan event tutup, langsung sembunyikan semua
            if not is_before_deadline or is_event_closed:
                continue
            members = [m for m in members if m.get('available_quota', 0) > 0]

        if not members:
            continue

        date_str = "Others"
        if session_date_wib:
            if session_date_wib.date() == now_wib.date():
                date_str = f"{session_date_wib.strftime('%d/%m/%Y')} (Today)"
            elif session_date_wib.date() == (now_wib + timedelta(days=1)).date():
                date_str = f"{session_date_wib.strftime('%d/%m/%Y')} (Tomorrow)"
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
            st.success(f"🔎 Showing all schedules for **'{search_query.title()}'** across dates.")
    else:
        if len(unique_dates) > 0:
            st.markdown(f"📅 **Event Date:** {unique_dates[0] if len(unique_dates) == 1 else ''}")
            if len(unique_dates) > 1:
                selected_date = st.radio("Select Date:", unique_dates, horizontal=True, key=f"filter_date_{event_id}", label_visibility="collapsed")
                st.write("")
            else:
                selected_date = unique_dates[0]
            active_sessions = sessions_by_date.get(selected_date, [])
        else:
            active_sessions = []

    if not active_sessions:
        if search_query:
            st.warning(f"Member '{search_query.title()}' not found in this event.")
        else:
            st.warning("🟢 All clear! No active tickets or available sessions right now.")
        return

    is_search_mode = bool(search_query)
    admin_keys = st.secrets.get("ADMIN_KEYS", [])
    is_admin = st.query_params.get("akses") in admin_keys

    now_dt = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_dt.strftime('%d/%m/%Y %H:%M WIB')
    judul_event = event_data.get('title', 'JKT48 Exclusive Event').upper()
    
    if is_search_mode:
        report_title = f"🔍 {search_query.upper()}"
    else:
        report_title = f"📅 {selected_date}"

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

    for session_index, sesi in enumerate(active_sessions):
        members = sesi['filtered_members']
        is_before_deadline = sesi['is_before_deadline']
        session_date_wib = sesi['session_date_wib']

        raw_label = sesi.get('label', 'Session')
        sesi_label = re.split(r'[\(·]', raw_label)[0].strip().replace("Sesi", "Session")
        time_info = f" | {sesi.get('start_time', '')[:5]} - {sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
        session_share_key = f"session-{session_index}"
        session_date_label = session_date_wib.strftime('%d/%m/%Y') if session_date_wib else sesi.get('date', '')[:10]
        session_share_label = escape(f"{session_date_label} · {sesi_label}{time_info}", quote=True)
        
        if not is_search_mode:
            master_html_buffer += f"<h4 data-share-session-heading='{session_share_key}' style='color: inherit; margin-top: 5px; margin-bottom: 15px; font-family: Inter, sans-serif; font-size: 16px;'>{sesi_label} <span style='opacity:0.5; font-size: 13px; font-weight: 500;'>{time_info}</span></h4>"
            master_html_buffer += f'<div class="cards-grid" data-share-session-grid="{session_share_key}">'
            
        for m in members:
            member_name = m.get('jkt48_member_name', 'Unknown')
            current_quota = m.get('available_quota', 0)
            tickets_sold = m.get('tickets_sold', 0)
            jalur_label = m.get("label", "-")
            
            if is_search_mode:
                if session_date_wib:
                    date_short = session_date_wib.strftime('%d/%m')
                else:
                    raw_d = sesi.get('date', '')
                    date_short = f"{raw_d[8:10]}/{raw_d[5:7]}" if len(raw_d) >= 10 else ""

                sesi_short = sesi_label.replace("Session", "S.").replace("Sesi", "S.")
                time_range = f"{sesi.get('start_time', '')[:5]}-{sesi.get('end_time', '')[:5]}" if sesi.get('start_time') else ""
                time_str = f"<br>({time_range})" if time_range else ""
                
                if date_short:
                    jalur_label = f"{date_short} • {sesi_short}{time_str}<br>{jalur_label}"
                else:
                    jalur_label = f"{sesi_short}{time_str}<br>{jalur_label}"
            
            display_member = member_name.replace(' ', '&nbsp;')            
            display_jalur = jalur_label
            share_member_name = escape(member_name, quote=True)
            share_attributes = f'data-share-session="{session_share_key}" data-share-session-label="{session_share_label}" data-share-member="{share_member_name}"'
            
            total_slot_capacity = tickets_sold + current_quota
            sold_percentage = (tickets_sold / total_slot_capacity * 100) if total_slot_capacity > 0 else 0
            
           # --- LOGIKA TEMA CARD TERPADU (CLOSED / SOLD OUT / LOW / AVAILABLE) ---
            if is_event_closed or not is_before_deadline:
                # TEMA CLOSED (Abu-abu mati mendominasi)
                cls, btn_text = "closed", "CLOSED"
                sold_percentage = 100
                bar_color = "#555555"
                badge_html = ""
            elif current_quota <= 0:
                # TEMA SOLD OUT (Merah murni)
                cls, btn_text = "sold", "SOLD&nbsp;OUT"
                sold_percentage = 100
                bar_color = "#EF4444"
                badge_html = ""
            elif current_quota < warn_limit:
                # TEMA LOW QUOTA (Kuning hati-hati)
                cls, btn_text = "warn", f"{current_quota}&nbsp;LEFT"
                bar_color = "#FBBF24"
                badge_html = '<div class="c-badge" style="background-color: #FBBF24; color: black;">LOW</div>'
            else:
                # TEMA AVAILABLE (Hijau normal)
                cls, btn_text = "avail", f"{current_quota}&nbsp;LEFT"
                bar_color = "#10B981"
                badge_html = '<div class="c-badge">AVAILABLE</div>'
            # ----------------------------------------------------------------------

            safe_name_img = member_name.strip().lower()
            raw_photo_url = photo_map.get(safe_name_img, "")
            
            if raw_photo_url:
                proxy_url = f"https://wsrv.nl/?url={raw_photo_url}&w=150&output=webp"
            else:
                proxy_url = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                
            img_html = f'<div class="c-photo" style="background-image: url(\'{proxy_url}\');" role="img" aria-label="{member_name} JKT48 Photo"></div>'
                                        
            combined_ui = f"""
            <div class="c-stats">
                <span>Sold:&nbsp;<b>{tickets_sold}</b></span>
            </div>
            <div class="c-prog-btn">
                <div class="c-prog-fill" style="width: {sold_percentage}%; background-color: {bar_color};"></div>
                <div class="c-prog-text">{btn_text}</div>
            </div>
            """
            
            card_html = ""
            # Jika sudah habis ATAU lewat deadline sesi ATAU event tutup total, matikan link <a>
            if current_quota <= 0 or not is_before_deadline or is_event_closed: 
                card_html += (
                    f'<div class="ldp-card {cls}" {share_attributes}>'
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
                    f'<div class="ldp-card {cls}" {share_attributes}>'
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
    
    if is_admin:
        selection_context = search_query if is_search_mode else selected_date
        safe_context = re.sub(r'[^a-zA-Z0-9]+', '_', selection_context).strip('_')
        render_share_controls(f"share_selection_{event_id}_{safe_context}")


def render_share_controls(storage_key):
    controls_html = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body { margin: 0; background: transparent; display: flex; gap: 10px; justify-content: center; align-items: center; overflow: hidden; }
        .btn-action { color: white; border: 0; width: 50px; height: 50px; border-radius: 50%; font-size: 20px; cursor: pointer; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 8px rgba(0,0,0,.45); transition: transform 180ms ease, background 180ms ease; }
        .btn-action:hover { transform: translateY(-2px); }
        .btn-action:focus-visible { outline: 3px solid white; outline-offset: 2px; }
        #copy-btn { background: #3B82F6; }
        #copy-btn:hover { background: #1D4ED8; }
        #select-btn { background: #10B981; }
        #select-btn:hover { background: #0D9488; }
        @media (prefers-reduced-motion: reduce) { .btn-action { transition: none; } }
    </style>
    <button class="btn-action" id="copy-btn" title="Copy selected cards" aria-label="Copy selected cards to clipboard">📋</button>
    <button class="btn-action" id="select-btn" title="Select sessions and members" aria-label="Select sessions and members">☑️</button>
    <script>
        const storageKey = "__STORAGE_KEY__";
        let selectedSessions = new Set();
        let selectedMembers = new Set();
        let sessionItems = [];
        let memberItems = [];

        try {
            const iframe = window.frameElement;
            if (iframe) {
                iframe.style.position = "fixed";
                iframe.style.bottom = "30px";
                iframe.style.right = "30px";
                iframe.style.width = "130px";
                iframe.style.height = "65px";
                iframe.style.zIndex = "1000";
                iframe.style.border = "none";
            }
        } catch (e) {}

        function loadSaved(group, available) {
            try {
                const saved = JSON.parse(window.parent.localStorage.getItem(`${storageKey}_${group}`));
                if (Array.isArray(saved)) return new Set(saved.filter(value => available.includes(value)));
            } catch (e) {}
            return new Set(available);
        }

        function saveSelection() {
            try {
                window.parent.localStorage.setItem(`${storageKey}_sessions`, JSON.stringify([...selectedSessions]));
                window.parent.localStorage.setItem(`${storageKey}_members`, JSON.stringify([...selectedMembers]));
            } catch (e) {}
        }

        function refreshData() {
            const cards = [...window.parent.document.querySelectorAll("#laporan-container .ldp-card[data-share-session]")];
            const sessions = new Map();
            const members = new Set();
            cards.forEach(card => {
                sessions.set(card.dataset.shareSession, card.dataset.shareSessionLabel);
                members.add(card.dataset.shareMember);
            });
            sessionItems = [...sessions].map(([value, label]) => ({ value, label }));
            memberItems = [...members].sort((a, b) => a.localeCompare(b)).map(value => ({ value, label: value }));
            selectedSessions = loadSaved("sessions", sessionItems.map(item => item.value));
            selectedMembers = loadSaved("members", memberItems.map(item => item.value));
        }

        const oldDialog = window.parent.document.getElementById("share-selection-dialog");
        const reopenDialog = Boolean(oldDialog && oldDialog.open);
        if (oldDialog) oldDialog.remove();
        const dialog = window.parent.document.createElement("dialog");
        dialog.id = "share-selection-dialog";
        dialog.innerHTML = `
            <style>
                #share-selection-dialog { width: min(680px, calc(100vw - 32px)); max-height: min(720px, calc(100vh - 32px)); padding: 0; border: 0; border-radius: 16px; background: #111827; color: #F9FAFB; font-family: Inter, system-ui, sans-serif; box-shadow: 0 12px 32px rgba(0,0,0,.45); }
                #share-selection-dialog::backdrop { background: rgba(0,0,0,.62); }
                .share-picker-head { display: flex; align-items: center; justify-content: space-between; padding: 20px 22px 14px; border-bottom: 1px solid #374151; }
                .share-picker-head h2 { margin: 0; font-size: 18px; }
                .share-picker-head p { margin: 4px 0 0; color: #D1D5DB; font-size: 12px; }
                .share-picker-close { width: 36px; height: 36px; border: 0; border-radius: 50%; background: #374151; color: white; cursor: pointer; font-size: 20px; }
                .share-picker-body { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 18px 22px; overflow: auto; max-height: calc(100vh - 210px); }
                .share-picker-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
                .share-picker-section h3 { margin: 0; font-size: 14px; }
                .share-picker-actions { display: flex; gap: 6px; }
                .share-picker-actions button { border: 0; background: transparent; color: #6EE7B7; font: inherit; font-size: 11px; cursor: pointer; padding: 4px; }
                .share-picker-list { display: flex; flex-direction: column; gap: 4px; }
                .share-picker-item { display: flex; align-items: flex-start; gap: 9px; padding: 8px; border-radius: 8px; cursor: pointer; color: #F3F4F6; font-size: 13px; line-height: 1.35; }
                .share-picker-item:hover { background: #1F2937; }
                .share-picker-item input { margin-top: 2px; accent-color: #10B981; }
                .share-picker-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px 18px; border-top: 1px solid #374151; }
                #share-picker-count { color: #D1D5DB; font-size: 12px; }
                #share-picker-done { border: 0; border-radius: 9px; background: #10B981; color: #052E25; padding: 9px 18px; font-weight: 800; cursor: pointer; }
                @media (max-width: 600px) { .share-picker-body { grid-template-columns: 1fr; } }
            </style>
            <div class="share-picker-head">
                <div><h2>Select content to copy</h2><p>Choose sessions and members for the clipboard image.</p></div>
                <button class="share-picker-close" aria-label="Close">×</button>
            </div>
            <div class="share-picker-body">
                <section class="share-picker-section">
                    <div class="share-picker-section-head"><h3>Sessions</h3><div class="share-picker-actions"><button data-group="sessions" data-action="all">All</button><button data-group="sessions" data-action="none">None</button></div></div>
                    <div class="share-picker-list" id="share-session-list"></div>
                </section>
                <section class="share-picker-section">
                    <div class="share-picker-section-head"><h3>Members</h3><div class="share-picker-actions"><button data-group="members" data-action="all">All</button><button data-group="members" data-action="none">None</button></div></div>
                    <div class="share-picker-list" id="share-member-list"></div>
                </section>
            </div>
            <div class="share-picker-foot"><span id="share-picker-count"></span><button id="share-picker-done">Done</button></div>`;
        window.parent.document.body.appendChild(dialog);

        function updateCount() {
            dialog.querySelector("#share-picker-count").textContent = `${selectedSessions.size} session(s) · ${selectedMembers.size} member(s)`;
        }

        function renderList(containerId, items, selection) {
            const container = dialog.querySelector(containerId);
            container.replaceChildren();
            items.forEach(item => {
                const label = window.parent.document.createElement("label");
                label.className = "share-picker-item";
                const checkbox = window.parent.document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.checked = selection.has(item.value);
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) selection.add(item.value); else selection.delete(item.value);
                    saveSelection();
                    updateCount();
                });
                const text = window.parent.document.createElement("span");
                text.textContent = item.label;
                label.append(checkbox, text);
                container.appendChild(label);
            });
        }

        function renderPicker() {
            renderList("#share-session-list", sessionItems, selectedSessions);
            renderList("#share-member-list", memberItems, selectedMembers);
            updateCount();
        }

        dialog.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => {
            const isSessions = button.dataset.group === "sessions";
            const items = isSessions ? sessionItems : memberItems;
            const selection = button.dataset.action === "all" ? new Set(items.map(item => item.value)) : new Set();
            if (isSessions) selectedSessions = selection; else selectedMembers = selection;
            saveSelection();
            renderPicker();
        }));
        dialog.querySelector(".share-picker-close").addEventListener("click", () => dialog.close());
        dialog.querySelector("#share-picker-done").addEventListener("click", () => dialog.close());
        dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });

        document.getElementById("select-btn").addEventListener("click", () => {
            refreshData();
            renderPicker();
            dialog.showModal();
        });
        if (reopenDialog) {
            refreshData();
            renderPicker();
            dialog.showModal();
        }

        function siapkanTarget() {
            refreshData();
            if (!selectedSessions.size || !selectedMembers.size) {
                renderPicker();
                dialog.showModal();
                return null;
            }
            const target = window.parent.document.getElementById("laporan-container");
            const banner = window.parent.document.getElementById("share-banner");
            if (!target) return null;
            const changedElements = [];
            const hide = element => {
                changedElements.push([element, element.style.display]);
                element.style.display = "none";
            };
            target.querySelectorAll(".ldp-card[data-share-session]").forEach(card => {
                if (!selectedSessions.has(card.dataset.shareSession) || !selectedMembers.has(card.dataset.shareMember)) hide(card);
            });
            target.querySelectorAll("[data-share-session-grid]").forEach(grid => {
                const hasVisibleCard = [...grid.querySelectorAll(".ldp-card")].some(card => card.style.display !== "none");
                if (!hasVisibleCard) {
                    hide(grid);
                    const heading = target.querySelector(`[data-share-session-heading="${grid.dataset.shareSessionGrid}"]`);
                    if (heading) hide(heading);
                }
            });
            const appBgColor = window.getComputedStyle(window.parent.document.body).backgroundColor;
            const targetStyle = [target.style.padding, target.style.backgroundColor, target.style.borderRadius];
            const bannerDisplay = banner ? banner.style.display : "";
            if (banner) banner.style.display = "flex";
            target.style.padding = "20px";
            target.style.backgroundColor = appBgColor;
            target.style.borderRadius = "15px";
            return { target, banner, bannerDisplay, changedElements, targetStyle, appBgColor };
        }

        function kembalikanTarget(state) {
            if (state.banner) state.banner.style.display = state.bannerDisplay;
            state.changedElements.forEach(([element, display]) => { element.style.display = display; });
            [state.target.style.padding, state.target.style.backgroundColor, state.target.style.borderRadius] = state.targetStyle;
        }

        function resetCopyButton(button) {
            setTimeout(() => { button.innerText = "📋"; button.style.background = "#3B82F6"; }, 1500);
        }

        document.getElementById("copy-btn").addEventListener("click", function() {
            const button = this;
            const state = siapkanTarget();
            if (!state) return;
            button.innerText = "⏳";
            button.style.background = "#FBBF24";
            setTimeout(() => {
                window.html2canvas(state.target, { useCORS: true, backgroundColor: state.appBgColor, scale: 2 }).then(canvas => {
                    kembalikanTarget(state);
                    canvas.toBlob(blob => {
                        navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]).then(() => {
                            button.innerText = "✅";
                            button.style.background = "#10B981";
                            resetCopyButton(button);
                        }).catch(() => {
                            button.innerText = "❌";
                            button.style.background = "#EF4444";
                            resetCopyButton(button);
                        });
                    }, "image/png");
                }).catch(() => {
                    kembalikanTarget(state);
                    button.innerText = "❌";
                    button.style.background = "#EF4444";
                    resetCopyButton(button);
                });
            }, 150);
        });
    </script>
    """
    components.html(controls_html.replace("__STORAGE_KEY__", storage_key), height=70)
