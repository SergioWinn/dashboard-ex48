# ui/components.py

import streamlit as st
import hashlib
import re
from html import escape
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import streamlit.components.v1 as components

from core.refresh import get_sales_window


def install_motion_observer():
    components.html(
        """
        <script>
        (() => {
            const parentWindow = window.parent;
            const parentDocument = parentWindow.document;
            const frame = window.frameElement;
            if (frame) {
                frame.style.display = "none";
                frame.setAttribute("aria-hidden", "true");
            }

            parentWindow.__ex48MotionObserver?.disconnect();
            const values = parentWindow.__ex48MotionValues ?? new Map();
            parentWindow.__ex48MotionValues = values;
            let scheduled = false;

            function play(target) {
                if (parentWindow.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
                target.getAnimations().forEach(animation => animation.cancel());
                target.animate(
                    [
                        { opacity: 0.68, transform: "translateY(2px)" },
                        { opacity: 1, transform: "translateY(0)" },
                    ],
                    { duration: 180, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
                );
            }

            function sync() {
                scheduled = false;
                parentDocument.querySelectorAll('[data-testid="stMetric"]').forEach(metric => {
                    const label = metric.querySelector('[data-testid="stMetricLabel"]')?.textContent?.trim();
                    const valueNode = metric.querySelector('[data-testid="stMetricValue"]');
                    if (!label || !valueNode) return;
                    const key = `metric:${label}`;
                    const value = valueNode.textContent?.trim() ?? "";
                    if (values.has(key) && values.get(key) !== value) play(valueNode);
                    values.set(key, value);
                });

                const source = parentDocument.querySelector(".source-readout");
                const sourceValue = source?.querySelector("strong")?.textContent?.trim();
                if (source && sourceValue) {
                    const key = "source-status";
                    if (values.has(key) && values.get(key) !== sourceValue) play(source);
                    values.set(key, sourceValue);
                }
            }

            const observer = new MutationObserver(() => {
                if (scheduled) return;
                scheduled = true;
                parentWindow.requestAnimationFrame(sync);
            });
            observer.observe(parentDocument.body, { childList: true, characterData: true, subtree: true });
            parentWindow.__ex48MotionObserver = observer;
            sync();
        })();
        </script>
        """,
        height=0,
    )


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

    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    _, general_end_wib = get_sales_window(event_data)

    matched_full_names = set()
    if search_query:
        for nick, full_name in nickname_map.items():
            if search_query in nick or search_query in full_name:
                matched_full_names.add(full_name)

    sessions_by_date = {}
    matched_member_found = False
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
            except (TypeError, ValueError):
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
                    except (TypeError, ValueError):
                        pass

        members = sesi.get('session_detail', [])
                
        if search_query:
            members = [
                m for m in members 
                if str(m.get('jkt48_member_name') or '').lower() in matched_full_names
                or search_query in str(m.get('jkt48_member_name') or '').lower()
            ]
            if members:
                matched_member_found = True
            
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

    for date_sessions in sessions_by_date.values():
        date_sessions.sort(key=lambda session: str(session.get('start_time') or ''))

    def date_sort_key(date_label):
        try:
            return datetime.strptime(date_label[:10], '%d/%m/%Y')
        except ValueError:
            return datetime.max

    unique_dates = sorted(sessions_by_date, key=date_sort_key)

    if search_query:
        active_sessions = []
        for d_sessions in sessions_by_date.values():
            active_sessions.extend(d_sessions)
        if active_sessions:
            st.success(f"Showing all schedules for **'{search_query.title()}'** across dates.")
    else:
        if len(unique_dates) > 0:
            if len(unique_dates) > 1:
                selected_date = st.radio("Select date", unique_dates, horizontal=True, key=f"filter_date_{event_id}")
            else:
                selected_date = unique_dates[0]
                st.markdown(f"**Event date:** {selected_date}")
            active_sessions = sessions_by_date.get(selected_date, [])
        else:
            active_sessions = []

    if not active_sessions:
        if search_query:
            if matched_member_found:
                st.warning(f"Member '{search_query.title()}' has no matching available tickets.")
            else:
                st.warning(f"Member '{search_query.title()}' not found in this event.")
        else:
            st.warning("No active tickets or available sessions right now.")
        return

    is_search_mode = bool(search_query)
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
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
    
    search_class = ' class="is-search-mode"' if is_search_mode else ''
    master_html_buffer = f'<div id="laporan-container"{search_class}>{banner_html}'
    
    if is_search_mode:
        master_html_buffer += '<div class="cards-grid">'

    for sesi in active_sessions:
        members = sesi['filtered_members']
        is_before_deadline = sesi['is_before_deadline']
        session_date_wib = sesi['session_date_wib']

        raw_label = str(sesi.get('label', 'Session'))
        sesi_label = re.split(r'[(\u00b7]', raw_label)[0].strip().replace("Sesi", "Session")
        start_time = str(sesi.get('start_time') or '')
        end_time = str(sesi.get('end_time') or '')
        time_info = f" | {start_time[:5]} - {end_time[:5]}" if start_time else ""
        session_date_label = session_date_wib.strftime('%d/%m/%Y') if session_date_wib else str(sesi.get('date') or '')[:10]
        session_identity = f"{session_date_label}|{raw_label}|{start_time}|{end_time}"
        session_share_key = f"session-{hashlib.sha1(session_identity.encode('utf-8')).hexdigest()[:12]}"
        session_share_label = escape(f"{session_date_label} - {sesi_label}{time_info}", quote=True)
        display_session_label = escape(sesi_label)
        display_time_info = escape(time_info)
        
        if not is_search_mode:
            master_html_buffer += f'<h3 class="session-heading" data-share-session-heading="{session_share_key}">{display_session_label} <span class="session-time">{display_time_info}</span></h3>'
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
                    display_jalur = f"{escape(date_short)} - {escape(sesi_short)}{time_str}<br>{escape(jalur_label)}"
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
                cls = "closed"
                btn_text = "CLOSED"
            elif current_quota <= 0:
                cls, btn_text = "sold", "SOLD&nbsp;OUT"
                sold_percentage = 100
            elif current_quota < warn_limit:
                cls, btn_text = "warn", f"LOW&nbsp;·&nbsp;{current_quota}&nbsp;LEFT"
            else:
                cls, btn_text = "avail", f"{current_quota}&nbsp;LEFT"

            safe_name_img = member_name.strip().lower()
            raw_photo_value = photo_map.get(safe_name_img)
            raw_photo_url = str(raw_photo_value) if raw_photo_value else ""
            
            if raw_photo_url:
                proxy_url = f"https://wsrv.nl/?url={quote(raw_photo_url, safe='')}&w=180&h=180&fit=cover&a=top&output=webp"
                safe_proxy_url = escape(proxy_url, quote=True)
                img_html = (
                    f'<div class="c-photo">'
                    f'<img class="c-photo-image" src="{safe_proxy_url}" alt="" aria-hidden="true" '
                    f'width="180" height="180" loading="lazy" crossorigin="anonymous">'
                    f'</div>'
                )
            else:
                initials = ''.join(part[0] for part in member_name.split()[:2]).upper() or '?'
                img_html = f'<div class="c-photo c-photo-placeholder" aria-hidden="true">{escape(initials)}</div>'
                                        
            combined_ui = f"""
            <div class="c-stats">
                <span>Sold:&nbsp;<b>{tickets_sold}</b></span>
            </div>
            <div class="c-prog-btn">
                <div class="c-prog-fill" style="transform: scaleX({max(0, min(100, sold_percentage)) / 100:.4f});"></div>
                <div class="c-prog-text">{btn_text}</div>
            </div>
            """
            identity_ui = (
                f'<div class="c-identity">{img_html}'
                f'<div class="c-member">{display_member}</div></div>'
            )
            
            card_html = ""
            # Jika sudah habis ATAU lewat deadline sesi ATAU event tutup total, matikan link <a>
            if current_quota <= 0 or not is_before_deadline or is_event_closed: 
                card_html += (
                    f'<div class="ldp-card {cls}" {share_attributes}>'
                     f'<div class="c-jalur" title="{escape(jalur_title, quote=True)}">{display_jalur}</div>'
                     f'{identity_ui}'
                    f'<div class="c-card-foot">'
                    f'{combined_ui}'
                    f'</div>'
                    f'</div>'
                )
            else: 
                purchase_aria = escape(
                    f"Purchase ticket for {member_name}, {sesi_label}, {current_quota} remaining; opens in a new tab",
                    quote=True,
                )
                card_html += (
                    f'<a href="{escape(purchase_link, quote=True)}" target="_blank" rel="noopener noreferrer" class="ldp-card purchase-card {cls}" aria-label="{purchase_aria}" {share_attributes}>'
                     f'<div class="c-jalur" title="{escape(jalur_title, quote=True)}">{display_jalur}</div>'
                     f'{identity_ui}'
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
    controls_html = r"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" onerror="const fallback=document.createElement('script');fallback.src='https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';document.head.appendChild(fallback);"></script>
    <style>
        :root { --share-accent: oklch(56% 0.2 256); --share-accent-strong: oklch(48% 0.2 256); --share-ink: oklch(98.5% 0.004 250); --share-focus: oklch(18% 0.02 258); --share-shadow: oklch(24% 0.02 258 / 0.18); --share-space-xs: 8px; --ease-out: cubic-bezier(.16,1,.3,1); }
        body { margin: 0; background: transparent; display: flex; gap: var(--share-space-xs); justify-content: center; align-items: center; overflow: hidden; }
        .btn-action { color: var(--share-ink); border: 0; width: 48px; height: 48px; border-radius: 50%; font-size: 19px; cursor: pointer; display: flex; justify-content: center; align-items: center; box-shadow: 0 1px 2px var(--share-shadow); transition: transform 100ms var(--ease-out); }
        .btn-action svg { width: 20px; height: 20px; stroke: currentColor; }
        .btn-action:active { transform: translateY(1px); }
        .btn-action:focus-visible { outline: 3px solid var(--share-focus); outline-offset: 2px; }
        .btn-action:disabled { cursor: wait; opacity: .75; }
        #share-btn { background: var(--share-accent); }
        @media (hover: hover) and (pointer: fine) {
            #share-btn:hover { background: var(--share-accent-strong); }
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
        dialog.setAttribute("aria-labelledby", "share-picker-title");
        dialog.setAttribute("aria-describedby", "share-picker-description");
        dialog.innerHTML = `
            <style>
                #share-selection-dialog { --dialog-bg: var(--color-graphite); --dialog-surface: var(--color-graphite-2); --dialog-rule: var(--color-graphite-2); --dialog-ink: var(--color-graphite-ink); --dialog-ink-muted: var(--color-graphite-muted); --dialog-accent: var(--color-accent); --dialog-accent-fill: var(--color-accent); --dialog-accent-strong: var(--color-accent-strong); --dialog-accent-ink: var(--color-accent-ink); --dialog-focus: var(--color-graphite-ink); --dialog-warning: var(--color-warning); --dialog-error: var(--color-danger); --dialog-backdrop: var(--color-overlay); --dialog-shadow: var(--color-shadow); --dialog-font: var(--font-body); position: fixed; inset: 0; width: min(680px, calc(100% - 24px)); height: fit-content; max-height: min(720px, calc(100dvh - 24px)); margin: auto; padding: 0; border: 0; border-radius: var(--radius-card); background: var(--dialog-bg); color: var(--dialog-ink); font-family: var(--dialog-font); box-shadow: 0 1px 2px var(--dialog-shadow); }
                #share-selection-dialog::backdrop { background: var(--dialog-backdrop); }
                #share-selection-dialog[open] { animation: share-dialog-in var(--dur-short) var(--ease-out); }
                #share-selection-dialog[open]::backdrop { animation: share-backdrop-in var(--dur-short) var(--ease-out); }
                @keyframes share-dialog-in { from { opacity: 0; transform: translateY(4px); } }
                @keyframes share-backdrop-in { from { opacity: 0; } }
                .share-picker-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-sm); padding: var(--space-sm); border-bottom: 1px solid var(--dialog-rule); }
                .share-picker-head h2 { margin: 0; font-size: 18px; }
                .share-picker-head p { display: none; margin: var(--space-2xs) 0 0; color: var(--dialog-ink-muted); font-size: 12px; }
                .share-picker-close { width: 44px; height: 44px; flex: 0 0 44px; border: 0; border-radius: 50%; background: var(--dialog-rule); color: var(--dialog-ink); cursor: pointer; font-size: 20px; }
                .share-picker-body { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-lg); padding: var(--space-sm); overflow: auto; max-height: calc(100dvh - 170px); }
                .share-picker-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-sm); }
                .share-picker-section h3 { margin: 0; font-size: 14px; }
                .share-picker-actions { display: flex; gap: var(--space-xs); }
                .share-picker-actions button { min-width: 44px; min-height: 44px; border: 0; background: transparent; color: var(--dialog-accent); font: inherit; font-size: 12px; cursor: pointer; padding: var(--space-xs); }
                .share-picker-list { display: flex; flex-direction: column; gap: var(--space-2xs); }
                .share-picker-item { min-height: 44px; display: flex; align-items: center; gap: var(--space-xs); padding: var(--space-xs); border-radius: var(--radius-input); cursor: pointer; color: var(--dialog-ink); font-size: 13px; line-height: 1.35; }
                .share-picker-item:hover { background: var(--dialog-surface); }
                .share-picker-item input { margin-top: var(--space-3xs); accent-color: var(--dialog-accent-fill); }
                .share-picker-foot { display: flex; align-items: center; justify-content: space-between; gap: var(--space-sm); padding: var(--space-sm); border-top: 1px solid var(--dialog-rule); }
                #share-picker-count { color: var(--dialog-ink-muted); font-size: 12px; }
                .share-picker-status { min-width: 0; }
                #share-picker-feedback { display: block; min-height: 1lh; margin-top: var(--space-2xs); color: var(--dialog-ink-muted); font-size: 12px; }
                #share-picker-feedback[data-tone="success"], #share-picker-feedback[data-tone="error"] { color: var(--dialog-ink); }
                #share-picker-copy { min-width: 128px; min-height: 44px; border: 0; border-radius: var(--radius-input); background: var(--dialog-accent-fill); color: var(--dialog-accent-ink); padding: var(--space-xs) var(--space-md); font-weight: 800; cursor: pointer; white-space: nowrap; }
                #share-picker-copy[data-state="loading"] { background: var(--dialog-warning); color: var(--color-status-warning-ink); cursor: wait; }
                #share-picker-copy[data-state="success"] { background: var(--dialog-accent-strong); color: var(--dialog-accent-ink); }
                #share-picker-copy[data-state="blocked"] { background: var(--dialog-warning); color: var(--color-status-warning-ink); }
                #share-picker-copy[data-state="error"] { background: var(--dialog-error); color: var(--color-danger-ink); }
                #share-picker-copy:disabled { cursor: not-allowed; opacity: .55; }
                #share-selection-dialog button:active { transform: translateY(1px); }
                #share-selection-dialog button:focus-visible, #share-selection-dialog input:focus-visible { outline: 3px solid var(--dialog-focus); outline-offset: 2px; }
                @media (hover: hover) and (pointer: fine) {
                    .share-picker-close:hover, .share-picker-actions button:hover { background: var(--dialog-surface); }
                    #share-picker-copy:hover:not(:disabled) { background: var(--dialog-accent-strong); }
                }
                @media (min-width: 40rem) {
                    .share-picker-head { padding: var(--space-md) var(--space-lg) var(--space-sm); }
                    .share-picker-head p { display: block; }
                    .share-picker-body { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); padding: var(--space-md) var(--space-lg); max-height: calc(100dvh - 210px); }
                    .share-picker-foot { padding: var(--space-sm) var(--space-lg) var(--space-md); }
                }
                @media (prefers-reduced-motion: reduce) {
                    #share-selection-dialog[open], #share-selection-dialog[open]::backdrop { animation: none; }
                }
            </style>
            <div class="share-picker-head">
                <div><h2 id="share-picker-title">Select content to copy</h2><p id="share-picker-description">Choose sessions and members for the clipboard image.</p></div>
                <button class="share-picker-close" aria-label="Close">×</button>
            </div>
            <div class="share-picker-body">
                <section class="share-picker-section">
                    <div class="share-picker-section-head"><h3>Sessions</h3><div class="share-picker-actions"><button aria-label="Select all sessions" data-group="sessions" data-action="all">All</button><button aria-label="Clear all sessions" data-group="sessions" data-action="none">None</button></div></div>
                    <div class="share-picker-list" id="share-session-list"></div>
                </section>
                <section class="share-picker-section">
                    <div class="share-picker-section-head"><h3>Members</h3><div class="share-picker-actions"><button aria-label="Select all members" data-group="members" data-action="all">All</button><button aria-label="Clear all members" data-group="members" data-action="none">None</button></div></div>
                    <div class="share-picker-list" id="share-member-list"></div>
                </section>
            </div>
            <div class="share-picker-foot"><div class="share-picker-status"><span id="share-picker-count"></span><span id="share-picker-feedback" role="status" aria-live="polite"></span></div><button id="share-picker-copy" data-state="idle">Copy selected</button></div>`;
        window.parent.document.body.appendChild(dialog);
        window.addEventListener("unload", () => {
            dialog.remove();
            activeCaptureWrapper?.remove();
        }, { once: true });

        function updateCount() {
            const cardCount = selectedCardCount();
            dialog.querySelector("#share-picker-count").textContent = `${cardCount} card(s) · ${selectedSessions.size} session(s) · ${selectedMembers.size} member(s)`;
            const copyAction = dialog.querySelector("#share-picker-copy");
            if (copyAction.dataset.state === "idle") {
                const canCopy = hasSelectedCards();
                copyAction.textContent = canCopy ? "Copy selected" : "Select items";
                copyAction.disabled = !canCopy;
            }
        }

        function setFeedback(message = "", tone = "") {
            const feedback = dialog.querySelector("#share-picker-feedback");
            feedback.textContent = message;
            feedback.dataset.tone = tone;
        }

        function hasSelectedCards() {
            return selectedCardCount() > 0;
        }

        function selectedCardCount() {
            return [...window.parent.document.querySelectorAll("#laporan-container .ldp-card[data-share-session]")].filter(card => (
                selectedSessions.has(card.dataset.shareSession) && selectedMembers.has(card.dataset.shareMember)
            )).length;
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
                    setFeedback();
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
            setFeedback();
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

        function oklchToLegacyRgb(value) {
            const match = value.trim().match(/^oklch\(\s*([\d.]+)(%)?\s+([\d.]+)\s+([\d.]+)(?:deg)?(?:\s*\/\s*([\d.]+)(%)?)?\s*\)$/i);
            if (!match) return value;

            const lightness = Number(match[1]) / (match[2] ? 100 : 1);
            const chroma = Number(match[3]);
            const hue = Number(match[4]) * Math.PI / 180;
            const alpha = match[5] ? Number(match[5]) / (match[6] ? 100 : 1) : 1;
            const a = chroma * Math.cos(hue);
            const b = chroma * Math.sin(hue);
            const l = Math.pow(lightness + 0.3963377774 * a + 0.2158037573 * b, 3);
            const m = Math.pow(lightness - 0.1055613458 * a - 0.0638541728 * b, 3);
            const s = Math.pow(lightness - 0.0894841775 * a - 1.291485548 * b, 3);
            const linear = [
                4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
            ];
            const channels = linear.map(channel => {
                const srgb = channel <= 0.0031308
                    ? 12.92 * channel
                    : 1.055 * Math.pow(channel, 1 / 2.4) - 0.055;
                return Math.round(Math.max(0, Math.min(1, srgb)) * 255);
            });
            return alpha < 1
                ? `rgba(${channels[0]}, ${channels[1]}, ${channels[2]}, ${Math.max(0, Math.min(1, alpha))})`
                : `rgb(${channels[0]}, ${channels[1]}, ${channels[2]})`;
        }

        function colorSrgbToLegacyRgb(value) {
            const match = value.trim().match(/^color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+))?\s*\)$/i);
            if (!match) return value;
            const channels = [match[1], match[2], match[3]].map(channel => (
                Math.round(Math.max(0, Math.min(1, Number(channel))) * 255)
            ));
            const alpha = match[4] === undefined ? 1 : Math.max(0, Math.min(1, Number(match[4])));
            return alpha < 1
                ? `rgba(${channels[0]}, ${channels[1]}, ${channels[2]}, ${alpha})`
                : `rgb(${channels[0]}, ${channels[1]}, ${channels[2]})`;
        }

        function toLegacyColor(value) {
            const trimmed = String(value || "").trim();
            if (trimmed.startsWith("oklch(")) return oklchToLegacyRgb(trimmed);
            if (trimmed.startsWith("color(srgb")) return colorSrgbToLegacyRgb(trimmed);
            return trimmed;
        }

        function normalizeCaptureColors(target, source, background) {
            const colorTokens = [
                "--color-paper", "--color-paper-2", "--color-paper-3", "--color-ink",
                "--color-ink-2", "--color-muted", "--color-rule", "--color-rule-strong",
                "--color-accent", "--color-accent-strong",
                "--color-accent-ink", "--color-focus", "--color-success",
                "--color-success-soft", "--color-success-ink",
                "--color-warning", "--color-warning-soft", "--color-warning-ink",
                "--color-status-warning-ink", "--color-danger", "--color-danger-soft",
                "--color-danger-ink", "--color-closed", "--color-graphite",
                "--color-graphite-2", "--color-graphite-ink", "--color-graphite-muted",
                "--color-overlay", "--color-shadow", "--color-surface",
                "--color-surface-raised", "--color-photo",
            ];
            const probe = window.parent.document.createElement("span");
            const legacyTokens = {};
            probe.style.cssText = "position:fixed;left:-20000px;top:0;pointer-events:none";
            source.appendChild(probe);
            colorTokens.forEach(token => {
                probe.style.color = `var(${token})`;
                const resolved = window.parent.getComputedStyle(probe).color;
                const legacy = toLegacyColor(resolved);
                if (legacy) {
                    target.style.setProperty(token, legacy);
                    legacyTokens[token] = legacy;
                }
            });
            probe.remove();

            const legacyBackground = toLegacyColor(background);
            target.style.backgroundColor = legacyBackground;
            target.style.color = toLegacyColor(window.parent.getComputedStyle(source).color);
            return { background: legacyBackground, tokens: legacyTokens };
        }

        function getCaptureBackground(source) {
            let node = source;
            while (node) {
                const background = window.parent.getComputedStyle(node).backgroundColor;
                if (background && background !== "transparent" && !background.endsWith(", 0)")) return background;
                node = node.parentElement;
            }
            const rootStyles = window.parent.getComputedStyle(window.parent.document.documentElement);
            return rootStyles.getPropertyValue("--color-paper").trim() || "transparent";
        }

        function siapkanTarget() {
            refreshData();
            activeCaptureWrapper?.remove();
            activeCaptureWrapper = null;
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
            target.querySelectorAll(".ldp-card[data-share-session]").forEach(card => {
                if (!selectedSessions.has(card.dataset.shareSession) || !selectedMembers.has(card.dataset.shareMember)) card.remove();
            });
            if (!target.querySelector(".ldp-card[data-share-session]")) {
                renderPicker();
                if (!dialog.open) dialog.showModal();
                requestAnimationFrame(() => dialog.querySelector("input")?.focus());
                return null;
            }
            target.querySelectorAll("[data-share-session-grid]").forEach(grid => {
                if (!grid.querySelector(".ldp-card")) {
                    const heading = target.querySelector(`[data-share-session-heading="${grid.dataset.shareSessionGrid}"]`);
                    heading?.remove();
                    grid.remove();
                }
            });
            target.querySelectorAll("img").forEach(image => {
                image.loading = "eager";
                image.decoding = "async";
                image.crossOrigin = "anonymous";
            });
            const banner = target.querySelector("#share-banner");
            if (banner) banner.style.display = "flex";

            const captureTheme = normalizeCaptureColors(target, source, getCaptureBackground(source));
            const background = captureTheme.background;
            const wrapper = window.parent.document.createElement("div");
            wrapper.style.position = "fixed";
            wrapper.style.left = "-12000px";
            wrapper.style.top = "0";
            wrapper.style.width = "1080px";
            wrapper.style.pointerEvents = "none";
            wrapper.appendChild(target);
            window.parent.document.body.appendChild(wrapper);
            activeCaptureWrapper = wrapper;
            return { target, wrapper, background, colorTokens: captureTheme.tokens };
        }

        function setCopyState(button, state, detail = "") {
            const states = {
                idle: ["Copy selected", "Copy selected cards to clipboard"],
                loading: ["Preparing…", "Preparing image"],
                success: ["Copied", "Image copied"],
                blocked: ["Clipboard blocked", "Clipboard access blocked"],
                error: ["Capture failed", "Image capture failed"]
            };
            const [label, accessibleLabel] = states[state];
            button.textContent = label;
            button.setAttribute("aria-label", detail || accessibleLabel);
            button.title = detail || accessibleLabel;
            button.dataset.state = state;
            button.disabled = state === "loading" || (state === "idle" && !hasSelectedCards());
            if (state === "idle" && button.disabled) button.textContent = "Select items";
        }

        function canvasToBlob(canvas) {
            return new Promise((resolve, reject) => {
                canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("Image conversion failed")), "image/png");
            });
        }

        function withTimeout(promise, timeoutMs) {
            return Promise.race([
                promise,
                new Promise((_, reject) => setTimeout(() => reject(new Error("Asset timeout")), timeoutMs)),
            ]);
        }

        async function waitForCaptureAssets(target) {
            const fallbackPixel = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
            const fontPromise = window.parent.document.fonts?.ready ?? Promise.resolve();
            await withTimeout(fontPromise, 4000).catch(() => undefined);

            await Promise.all([...target.querySelectorAll("img")].map(async image => {
                try {
                    if (!image.complete) {
                        await withTimeout(new Promise((resolve, reject) => {
                            image.addEventListener("load", resolve, { once: true });
                            image.addEventListener("error", reject, { once: true });
                        }), 6000);
                    }
                    if (image.decode) await withTimeout(image.decode(), 3000);
                    if (!image.naturalWidth) throw new Error("Empty image");
                } catch {
                    image.removeAttribute("crossorigin");
                    image.src = fallbackPixel;
                }
            }));

            await new Promise(resolve => window.parent.requestAnimationFrame(() => {
                window.parent.requestAnimationFrame(resolve);
            }));
        }

        async function getCaptureLibrary() {
            for (let attempt = 0; attempt < 20; attempt += 1) {
                if (window.html2canvas) return window.html2canvas;
                await new Promise(resolve => setTimeout(resolve, 250));
            }
            throw new Error("Capture library failed to load");
        }

        async function renderCaptureBlob(state) {
            const html2canvas = await getCaptureLibrary();
            await waitForCaptureAssets(state.target);

            const rect = state.target.getBoundingClientRect();
            const width = Math.max(1, Math.ceil(rect.width));
            const height = Math.max(1, Math.ceil(rect.height));
            const maxPixels = 12000000;
            const maxDimension = 16384;
            const constrainedScale = Math.min(
                1.5,
                Math.sqrt(maxPixels / (width * height)),
                maxDimension / Math.max(width, height),
            );
            if (constrainedScale < 0.25) throw new Error("Capture selection is too large");
            const scale = Math.max(0.25, constrainedScale);
            const canvas = await html2canvas(state.target, {
                useCORS: true,
                allowTaint: false,
                backgroundColor: state.background,
                imageTimeout: 8000,
                ignoreElements: element => element.id === "share-selection-dialog" || element.tagName === "IFRAME",
                logging: false,
                scale,
                scrollX: 0,
                scrollY: 0,
                windowWidth: width,
                windowHeight: height,
                onclone: clonedDocument => {
                    const clonedTarget = clonedDocument.getElementById("share-capture-target");
                    [clonedDocument.documentElement, clonedDocument.body, clonedTarget].forEach(element => {
                        if (!element) return;
                        Object.entries(state.colorTokens).forEach(([token, value]) => {
                            element.style.setProperty(token, value);
                        });
                    });
                    clonedDocument.documentElement.style.backgroundColor = state.background;
                    clonedDocument.body.style.backgroundColor = state.background;
                },
            });
            return canvasToBlob(canvas);
        }

        function captureErrorMessage(error) {
            if (error?.name === "NotAllowedError" || String(error?.message).includes("Clipboard")) {
                return "Browser blocked image clipboard. Allow clipboard access for this site, then try again.";
            }
            if (error?.name === "SecurityError") return "A photo blocked image capture. Reload the page and try again.";
            if (String(error?.message).includes("library")) return "Capture tools did not load. Reload the page and try again.";
            if (String(error?.message).includes("too large")) return "The selection is too large. Select fewer sessions or members and try again.";
            if (String(error?.message).includes("conversion")) return "The image was too large to convert. Select fewer cards and try again.";
            return "The image could not be created. Select fewer cards or reload the page.";
        }

        dialog.querySelector("#share-picker-copy").addEventListener("click", async function() {
            const button = this;
            const state = siapkanTarget();
            if (resetTimer) {
                clearTimeout(resetTimer);
                resetTimer = null;
            }
            if (!state) {
                const message = "No cards match the current session and member selection.";
                setCopyState(button, "error", message);
                setFeedback(message, "error");
                resetTimer = setTimeout(() => setCopyState(button, "idle"), 1800);
                return;
            }
            setCopyState(button, "loading");
            setFeedback("Preparing selected cards…");
            try {
                const blobPromise = renderCaptureBlob(state);
                const clipboardContexts = [
                    {
                        clipboard: window.parent.navigator.clipboard,
                        ClipboardItemClass: window.parent.ClipboardItem,
                    },
                    {
                        clipboard: navigator.clipboard,
                        ClipboardItemClass: window.ClipboardItem,
                    },
                ];
                let clipboardError = new Error("Clipboard API is unavailable");
                let copied = false;

                for (const context of clipboardContexts) {
                    const { clipboard, ClipboardItemClass } = context;
                    if (!clipboard?.write || !ClipboardItemClass) continue;
                    if (ClipboardItemClass.supports && !ClipboardItemClass.supports("image/png")) continue;
                    try {
                        await clipboard.write([new ClipboardItemClass({ "image/png": blobPromise })]);
                        copied = true;
                        setCopyState(button, "success");
                        setFeedback("Copied to clipboard.", "success");
                        break;
                    } catch (error) {
                        clipboardError = error;
                    }
                }

                if (!copied) {
                    await blobPromise;
                    throw clipboardError;
                }
            } catch (error) {
                console.error("Copy image failed", error);
                const message = captureErrorMessage(error);
                const isClipboardError = error?.name === "NotAllowedError" || String(error?.message).includes("Clipboard");
                setCopyState(button, isClipboardError ? "blocked" : "error", message);
                setFeedback(message, "error");
            } finally {
                state.wrapper.remove();
                activeCaptureWrapper = null;
                button.disabled = false;
                const didComplete = button.dataset.state === "success";
                resetTimer = setTimeout(() => {
                    setCopyState(button, "idle");
                    if (didComplete) dialog.close();
                }, didComplete ? 1400 : 3000);
            }
        });
    </script>
    """
    safe_storage_key = re.sub(r'[^a-zA-Z0-9_-]+', '_', storage_key)
    components.html(controls_html.replace("__STORAGE_KEY__", safe_storage_key), height=70)






