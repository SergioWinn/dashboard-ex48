# ui/components.py

import streamlit as st
import hashlib
import re
from html import escape
from datetime import datetime, timedelta
from urllib.parse import quote
import streamlit.components.v1 as components


def _as_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
        raw_date = str(sesi.get('date') or '')
        session_date_wib = None
        
        if raw_date:
            try:
                clean_date = raw_date.split('.')[0].replace('Z', '')
                if 'T' in clean_date:
                    session_date_wib = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
                    if 'Z' in raw_date:
                        session_date_wib += timedelta(hours=7)
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
                        t_end = datetime.strptime(str(sesi.get('end_time')), "%H:%M:%S").time()
                        session_end_datetime = datetime.combine(session_date_wib.date(), t_end)
                        if now_wib > session_end_datetime:
                            is_before_deadline = False
                    except:
                        pass

        members = sesi.get('session_detail', [])
                
        if search_query:
            members = [
                m for m in members 
                if str(m.get('jkt48_member_name') or '').lower() in matched_full_names
                or search_query in str(m.get('jkt48_member_name') or '').lower()
            ]
            
        if available_only:
            # Jika mode available dihidupkan, dan event tutup, langsung sembunyikan semua
            if not is_before_deadline or is_event_closed:
                continue
            members = [m for m in members if _as_int(m.get('available_quota')) > 0]

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
            st.success(f"Showing all schedules for **'{search_query.title()}'** across dates.")
    else:
        if len(unique_dates) > 0:
            st.markdown(f"**Event date:** {unique_dates[0] if len(unique_dates) == 1 else ''}")
            if len(unique_dates) > 1:
                selected_date = st.radio("Select date", unique_dates, horizontal=True, key=f"filter_date_{event_id}")
            else:
                selected_date = unique_dates[0]
            active_sessions = sessions_by_date.get(selected_date, [])
        else:
            active_sessions = []

    if not active_sessions:
        if search_query:
            st.warning(f"Member '{search_query.title()}' not found in this event.")
        else:
            st.warning("No active tickets or available sessions right now.")
        return

    is_search_mode = bool(search_query)
    now_dt = datetime.utcnow() + timedelta(hours=7)
    waktu_sekarang = now_dt.strftime('%d/%m/%Y %H:%M WIB')
    judul_event = escape(str(event_data.get('title', 'JKT48 Exclusive Event')).upper())
    
    if is_search_mode:
        report_title = escape(f"Search: {search_query.upper()}")
    else:
        report_title = escape(f"Event date: {selected_date}")

    banner_html = f"""
    <div id="share-banner" class="share-banner" style="display: none;">
        <div class="sb-left">
            <h3>{judul_event}</h3>
            <p>{report_title}</p>
        </div>
        <div class="sb-right">
            <div class="sb-time">{waktu_sekarang}</div>
            <div class="sb-wm">LIVE TRACKER BY @ESTRELLAWIN19</div>
        </div>
    </div>
    """
    
    master_html_buffer = f'<div id="laporan-container">{banner_html}'
    
    if is_search_mode:
        master_html_buffer += '<div class="cards-grid">'

    for sesi in active_sessions:
        members = sesi['filtered_members']
        is_before_deadline = sesi['is_before_deadline']
        session_date_wib = sesi['session_date_wib']

        raw_label = str(sesi.get('label', 'Session'))
        sesi_label = re.split(r'[\(Â·]', raw_label)[0].strip().replace("Sesi", "Session")
        start_time = str(sesi.get('start_time') or '')
        end_time = str(sesi.get('end_time') or '')
        time_info = f" | {start_time[:5]} - {end_time[:5]}" if start_time else ""
        session_date_label = session_date_wib.strftime('%d/%m/%Y') if session_date_wib else str(sesi.get('date') or '')[:10]
        session_identity = f"{session_date_label}|{raw_label}|{start_time}|{end_time}"
        session_share_key = f"session-{hashlib.sha1(session_identity.encode('utf-8')).hexdigest()[:12]}"
        session_share_label = escape(f"{session_date_label} Â· {sesi_label}{time_info}", quote=True)
        display_session_label = escape(sesi_label)
        display_time_info = escape(time_info)
        
        if not is_search_mode:
            master_html_buffer += f'<h4 class="session-heading" data-share-session-heading="{session_share_key}">{display_session_label} <span class="session-time">{display_time_info}</span></h4>'
            master_html_buffer += f'<div class="cards-grid" data-share-session-grid="{session_share_key}">'
            
        for m in members:
            member_name = str(m.get('jkt48_member_name') or 'Unknown')
            current_quota = _as_int(m.get('available_quota'))
            tickets_sold = _as_int(m.get('tickets_sold'))
            jalur_label = str(m.get("label", "-"))
            jalur_title = jalur_label
            
            if is_search_mode:
                if session_date_wib:
                    date_short = session_date_wib.strftime('%d/%m')
                else:
                    raw_d = str(sesi.get('date') or '')
                    date_short = f"{raw_d[8:10]}/{raw_d[5:7]}" if len(raw_d) >= 10 else ""

                sesi_short = sesi_label.replace("Session", "S.").replace("Sesi", "S.")
                time_range = f"{start_time[:5]}-{end_time[:5]}" if start_time else ""
                time_str = f"<br>({time_range})" if time_range else ""
                
                if date_short:
                    display_jalur = f"{escape(date_short)} Â· {escape(sesi_short)}{time_str}<br>{escape(jalur_label)}"
                else:
                    display_jalur = f"{escape(sesi_short)}{time_str}<br>{escape(jalur_label)}"
                jalur_title = f"{date_short} {sesi_short} {jalur_label}"
            else:
                display_jalur = escape(jalur_label)
            
            display_member = escape(member_name)
            share_member_name = escape(member_name, quote=True)
            share_attributes = f'data-share-session="{session_share_key}" data-share-session-label="{session_share_label}" data-share-member="{share_member_name}"'
            
            total_slot_capacity = tickets_sold + current_quota
            sold_percentage = (tickets_sold / total_slot_capacity * 100) if total_slot_capacity > 0 else 0
            
           # --- LOGIKA TEMA CARD TERPADU (CLOSED / SOLD OUT / LOW / AVAILABLE) ---
            if is_event_closed or not is_before_deadline:
                # Event closed tetap pakai komposisi sold/remaining asli supaya tidak terlihat sold out.
                cls = "closed"
                btn_text = "CLOSED"
                badge_html = ""
            elif current_quota <= 0:
                # TEMA SOLD OUT (Merah murni)
                cls, btn_text = "sold", "SOLD&nbsp;OUT"
                sold_percentage = 100
                badge_html = ""
            elif current_quota < warn_limit:
                # TEMA LOW QUOTA (Kuning hati-hati)
                cls, btn_text = "warn", f"{current_quota}&nbsp;LEFT"
                badge_html = '<div class="c-badge">LOW</div>'
            else:
                # TEMA AVAILABLE (Hijau normal)
                cls, btn_text = "avail", f"{current_quota}&nbsp;LEFT"
                badge_html = '<div class="c-badge">AVAILABLE</div>'
            # ----------------------------------------------------------------------

            safe_name_img = member_name.strip().lower()
            raw_photo_value = photo_map.get(safe_name_img)
            raw_photo_url = str(raw_photo_value) if raw_photo_value else ""
            
            if raw_photo_url:
                proxy_url = f"https://wsrv.nl/?url={quote(raw_photo_url, safe='')}&w=180&h=180&fit=cover&a=top&output=webp"
            else:
                proxy_url = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

            safe_proxy_url = escape(proxy_url, quote=True)
            safe_photo_alt = escape(f"{member_name} JKT48 photo", quote=True)
            img_html = (
                f'<div class="c-photo">'
                f'<img class="c-photo-image" src="{safe_proxy_url}" alt="{safe_photo_alt}" '
                f'width="180" height="180" loading="lazy">'
                f'</div>'
            )
                                        
            combined_ui = f"""
            <div class="c-stats">
                <span>Sold:&nbsp;<b>{tickets_sold}</b></span>
            </div>
            <div class="c-prog-btn">
                <div class="c-prog-fill" style="transform: scaleX({max(0, min(100, sold_percentage)) / 100:.4f});"></div>
                <div class="c-prog-text">{btn_text}</div>
            </div>
            """
            
            card_html = ""
            # Jika sudah habis ATAU lewat deadline sesi ATAU event tutup total, matikan link <a>
            if current_quota <= 0 or not is_before_deadline or is_event_closed: 
                card_html += (
                    f'<div class="ldp-card {cls}" {share_attributes}>'
                    f'{badge_html}'
                    f'<div class="c-jalur" title="{escape(jalur_title, quote=True)}">{display_jalur}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{display_member}</div>'
                    f'<div class="c-card-foot">'
                    f'{combined_ui}'
                    f'</div>'
                    f'</div>'
                )
            else: 
                purchase_aria = escape(
                    f"Purchase ticket for {member_name}, {sesi_label}, {current_quota} remaining",
                    quote=True,
                )
                card_html += (
                    f'<a href="{escape(purchase_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="ldp-card purchase-card {cls}" aria-label="{purchase_aria}" {share_attributes}>'
                    f'{badge_html}'
                    f'<div class="c-jalur" title="{escape(jalur_title, quote=True)}">{display_jalur}</div>'
                    f'{img_html}'
                    f'<div class="c-member">{display_member}</div>'
                    f'<div class="c-card-foot">'
                    f'{combined_ui}'
                    f'</div></a>'
                )
            
            master_html_buffer += card_html

        if not is_search_mode:
            master_html_buffer += '</div>'
            
    if is_search_mode:
        master_html_buffer += '</div>'

    master_html_buffer += '</div>'

    st.markdown(master_html_buffer, unsafe_allow_html=True)
    
def render_share_controls(storage_key):
    controls_html = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        :root { --green: #047857; --green-dark: #065F46; --blue: #2563EB; --blue-dark: #1D4ED8; --error: #B91C1C; --warning: #A16207; --button-ink: #FFFFFF; --button-shadow: rgba(0,0,0,.4); --ease-out: cubic-bezier(.16,1,.3,1); }
        body { margin: 0; background: transparent; display: flex; gap: 8px; justify-content: center; align-items: center; overflow: hidden; }
        .btn-action { color: var(--button-ink); border: 0; width: 48px; height: 48px; border-radius: 50%; font-size: 19px; cursor: pointer; display: flex; justify-content: center; align-items: center; box-shadow: 0 3px 8px var(--button-shadow); transition: transform 180ms var(--ease-out), background-color 180ms var(--ease-out); }
        .btn-action svg { width: 20px; height: 20px; stroke: currentColor; }
        .btn-action:active { transform: translateY(1px); }
        .btn-action:focus-visible { outline: 3px solid white; outline-offset: 2px; }
        .btn-action:disabled { cursor: wait; opacity: .75; }
        #share-btn { background: var(--green); }
        @media (hover: hover) and (pointer: fine) {
            #share-btn:hover { background: var(--green-dark); transform: translateY(-2px); }
        }
        @media (prefers-reduced-motion: reduce) { .btn-action { transition: none; } }
    </style>
    <button class="btn-action" id="share-btn" title="Select and copy cards" aria-label="Select sessions and members, then copy"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path><path d="m11 13 1.5 1.5L16 11"></path></svg></button>
    <script>
        const storageKey = "__STORAGE_KEY__";
        let selectedSessions = new Set();
        let selectedMembers = new Set();
        let sessionItems = [];
        let memberItems = [];
        let resetTimer = null;
        let selectionInitialized = false;
        let activeCaptureWrapper = null;

        try {
            const iframe = window.frameElement;
            if (iframe) {
                iframe.style.position = "fixed";
                iframe.style.bottom = "calc(56px + env(safe-area-inset-bottom, 0px))";
                iframe.style.right = "calc(16px + env(safe-area-inset-right, 0px))";
                iframe.style.width = "60px";
                iframe.style.height = "60px";
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
            const availableSessions = sessionItems.map(item => item.value);
            const availableMembers = memberItems.map(item => item.value);
            if (!selectionInitialized) {
                selectedSessions = loadSaved("sessions", availableSessions);
                selectedMembers = loadSaved("members", availableMembers);
                selectionInitialized = true;
            } else {
                selectedSessions = new Set([...selectedSessions].filter(value => availableSessions.includes(value)));
                selectedMembers = new Set([...selectedMembers].filter(value => availableMembers.includes(value)));
            }
        }

        const oldDialog = window.parent.document.getElementById("share-selection-dialog");
        const reopenDialog = Boolean(oldDialog && oldDialog.open);
        if (oldDialog) oldDialog.remove();
        const dialog = window.parent.document.createElement("dialog");
        dialog.id = "share-selection-dialog";
        dialog.innerHTML = `
            <style>
                #share-selection-dialog { --dialog-bg: #111827; --dialog-surface: #1F2937; --dialog-rule: #374151; --dialog-ink: #F9FAFB; --dialog-ink-muted: #D1D5DB; --dialog-accent: #6EE7B7; --dialog-accent-fill: #10B981; --dialog-accent-strong: #047857; --dialog-accent-ink: #052E25; --dialog-warning: #A16207; --dialog-error: #B91C1C; --dialog-backdrop: rgba(0,0,0,.62); --dialog-shadow: rgba(0,0,0,.45); --dialog-font: Inter, system-ui, sans-serif; position: fixed; inset: 0; width: min(680px, calc(100% - 24px)); height: fit-content; max-height: min(720px, calc(100dvh - 24px)); margin: auto; padding: 0; border: 0; border-radius: 12px; background: var(--dialog-bg); color: var(--dialog-ink); font-family: var(--dialog-font); box-shadow: 0 12px 32px var(--dialog-shadow); }
                #share-selection-dialog::backdrop { background: var(--dialog-backdrop); }
                .share-picker-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 18px 20px 14px; border-bottom: 1px solid var(--dialog-rule); }
                .share-picker-head h2 { margin: 0; font-size: 18px; }
                .share-picker-head p { margin: 4px 0 0; color: var(--dialog-ink-muted); font-size: 12px; }
                .share-picker-close { width: 44px; height: 44px; flex: 0 0 44px; border: 0; border-radius: 50%; background: var(--dialog-rule); color: var(--dialog-ink); cursor: pointer; font-size: 20px; }
                .share-picker-body { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; padding: 18px 20px; overflow: auto; max-height: calc(100dvh - 210px); }
                .share-picker-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
                .share-picker-section h3 { margin: 0; font-size: 14px; }
                .share-picker-actions { display: flex; gap: 6px; }
                .share-picker-actions button { min-height: 44px; border: 0; background: transparent; color: var(--dialog-accent); font: inherit; font-size: 12px; cursor: pointer; padding: 8px; }
                .share-picker-list { display: flex; flex-direction: column; gap: 4px; }
                .share-picker-item { min-height: 44px; display: flex; align-items: center; gap: 9px; padding: 8px; border-radius: 8px; cursor: pointer; color: var(--dialog-ink); font-size: 13px; line-height: 1.35; }
                .share-picker-item:hover { background: var(--dialog-surface); }
                .share-picker-item input { margin-top: 2px; accent-color: var(--dialog-accent-fill); }
                .share-picker-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px 18px; border-top: 1px solid var(--dialog-rule); }
                #share-picker-count { color: var(--dialog-ink-muted); font-size: 12px; }
                #share-picker-copy { min-width: 128px; min-height: 44px; border: 0; border-radius: 8px; background: var(--dialog-accent-fill); color: var(--dialog-accent-ink); padding: 9px 18px; font-weight: 800; cursor: pointer; white-space: nowrap; }
                #share-picker-copy[data-state="loading"] { background: var(--dialog-warning); color: var(--dialog-ink); cursor: wait; }
                #share-picker-copy[data-state="success"] { background: var(--dialog-accent-strong); color: var(--dialog-ink); }
                #share-picker-copy[data-state="error"] { background: var(--dialog-error); color: var(--dialog-ink); }
                #share-selection-dialog button:focus-visible, #share-selection-dialog input:focus-visible { outline: 3px solid var(--dialog-accent); outline-offset: 2px; }
                @media (max-width: 600px) {
                    .share-picker-head { padding: 14px 14px 10px; }
                    .share-picker-head p { display: none; }
                    .share-picker-body { grid-template-columns: minmax(0, 1fr); padding: 12px 14px; max-height: calc(100dvh - 170px); }
                    .share-picker-foot { padding: 10px 14px 14px; }
                }
            </style>
            <div class="share-picker-head">
                <div><h2>Select content to copy</h2><p>Choose sessions and members for the clipboard image.</p></div>
                <button class="share-picker-close" aria-label="Close">Ã—</button>
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
            <div class="share-picker-foot"><span id="share-picker-count"></span><button id="share-picker-copy" data-state="idle">Copy selected</button></div>`;
        window.parent.document.body.appendChild(dialog);
        window.addEventListener("unload", () => {
            dialog.remove();
            activeCaptureWrapper?.remove();
        }, { once: true });

        function updateCount() {
            dialog.querySelector("#share-picker-count").textContent = `${selectedSessions.size} session(s) Â· ${selectedMembers.size} member(s)`;
            const copyAction = dialog.querySelector("#share-picker-copy");
            if (copyAction.dataset.state === "idle") {
                const canCopy = hasSelectedCards();
                copyAction.textContent = canCopy ? "Copy selected" : "Select items";
                copyAction.disabled = !canCopy;
            }
        }

        function hasSelectedCards() {
            return [...window.parent.document.querySelectorAll("#laporan-container .ldp-card[data-share-session]")].some(card => (
                selectedSessions.has(card.dataset.shareSession) && selectedMembers.has(card.dataset.shareMember)
            ));
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
        dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });

        function openPicker() {
            refreshData();
            renderPicker();
            if (!dialog.open) dialog.showModal();
            requestAnimationFrame(() => dialog.querySelector("input")?.focus());
        }

        document.getElementById("share-btn").addEventListener("click", openPicker);
        if (reopenDialog) {
            refreshData();
            renderPicker();
            if (!dialog.open) dialog.showModal();
        }

        function getCaptureBackground(source) {
            let node = source;
            while (node) {
                const background = window.getComputedStyle(node).backgroundColor;
                if (background && background !== "transparent" && !background.endsWith(", 0)")) return background;
                node = node.parentElement;
            }
            return window.parent.matchMedia("(prefers-color-scheme: dark)").matches ? "#0E1117" : "#FFFFFF";
        }

        function siapkanTarget() {
            refreshData();
            if (!selectedSessions.size || !selectedMembers.size) {
                renderPicker();
                if (!dialog.open) dialog.showModal();
                requestAnimationFrame(() => dialog.querySelector("input")?.focus());
                return null;
            }
            const source = window.parent.document.getElementById("laporan-container");
            if (!source) return null;

            const target = source.cloneNode(true);
            target.id = "share-capture-target";
            target.classList.add("capture-mode");
            target.querySelectorAll("img").forEach(image => { image.loading = "eager"; });
            target.querySelectorAll(".ldp-card[data-share-session]").forEach(card => {
                if (!selectedSessions.has(card.dataset.shareSession) || !selectedMembers.has(card.dataset.shareMember)) card.style.display = "none";
            });
            const hasSelectedCard = [...target.querySelectorAll(".ldp-card[data-share-session]")].some(card => card.style.display !== "none");
            if (!hasSelectedCard) {
                renderPicker();
                if (!dialog.open) dialog.showModal();
                requestAnimationFrame(() => dialog.querySelector("input")?.focus());
                return null;
            }
            target.querySelectorAll("[data-share-session-grid]").forEach(grid => {
                const hasVisibleCard = [...grid.querySelectorAll(".ldp-card")].some(card => card.style.display !== "none");
                if (!hasVisibleCard) {
                    grid.style.display = "none";
                    const heading = target.querySelector(`[data-share-session-heading="${grid.dataset.shareSessionGrid}"]`);
                    if (heading) heading.style.display = "none";
                }
            });
            const banner = target.querySelector("#share-banner");
            if (banner) banner.style.display = "flex";

            const background = getCaptureBackground(source);
            target.style.backgroundColor = background;
            target.style.color = window.getComputedStyle(source).color;
            const wrapper = window.parent.document.createElement("div");
            wrapper.style.position = "fixed";
            wrapper.style.left = "-12000px";
            wrapper.style.top = "0";
            wrapper.style.width = "1080px";
            wrapper.style.pointerEvents = "none";
            wrapper.appendChild(target);
            window.parent.document.body.appendChild(wrapper);
            activeCaptureWrapper = wrapper;
            return { target, wrapper, background };
        }

        function setCopyState(button, state) {
            const states = {
                idle: ["Copy selected", "Copy selected cards to clipboard"],
                loading: ["Preparingâ€¦", "Preparing image"],
                success: ["Copied", "Image copied"],
                error: ["Copy failed", "Copy failed"]
            };
            const [label, accessibleLabel] = states[state];
            button.textContent = label;
            button.setAttribute("aria-label", accessibleLabel);
            button.title = accessibleLabel;
            button.dataset.state = state;
            button.disabled = state === "loading" || (state === "idle" && !hasSelectedCards());
            if (state === "idle" && button.disabled) button.textContent = "Select items";
        }

        function canvasToBlob(canvas) {
            return new Promise((resolve, reject) => {
                canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("Image conversion failed")), "image/png");
            });
        }

        dialog.querySelector("#share-picker-copy").addEventListener("click", async function() {
            const button = this;
            const state = siapkanTarget();
            if (resetTimer) {
                clearTimeout(resetTimer);
                resetTimer = null;
            }
            if (!state) {
                setCopyState(button, "error");
                resetTimer = setTimeout(() => setCopyState(button, "idle"), 1800);
                return;
            }
            setCopyState(button, "loading");
            try {
                const clipboard = window.parent.navigator.clipboard || navigator.clipboard;
                const ClipboardItemClass = window.parent.ClipboardItem || window.ClipboardItem;
                if (!window.html2canvas || !clipboard?.write || !ClipboardItemClass) {
                    throw new Error("Image clipboard is not supported in this browser");
                }
                const blobPromise = (async () => {
                    await new Promise(resolve => setTimeout(resolve, 80));
                    const canvas = await window.html2canvas(state.target, {
                        useCORS: true,
                        backgroundColor: state.background,
                        scale: 2,
                    });
                    return canvasToBlob(canvas);
                })();
                await clipboard.write([new ClipboardItemClass({ "image/png": blobPromise })]);
                setCopyState(button, "success");
            } catch (error) {
                console.error("Copy image failed", error);
                setCopyState(button, "error");
            } finally {
                state.wrapper.remove();
                activeCaptureWrapper = null;
                button.disabled = false;
                const didCopy = button.dataset.state === "success";
                resetTimer = setTimeout(() => {
                    setCopyState(button, "idle");
                    if (didCopy) dialog.close();
                }, didCopy ? 900 : 1800);
            }
        });
    </script>
    """
    safe_storage_key = re.sub(r'[^a-zA-Z0-9_-]+', '_', storage_key)
    components.html(controls_html.replace("__STORAGE_KEY__", safe_storage_key), height=70)



