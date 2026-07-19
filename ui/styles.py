# ui/styles.py

GLOBAL_CSS = """
<style>
/* Hallmark · pre-emit critique: P5 H4 E4 S5 R5 V4
 * genre: modern-minimal · macrostructure: Workbench · tone: utilitarian
 */
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --font-display: 'Barlow Condensed', 'Arial Narrow', sans-serif;
    --font-body: 'Inter', system-ui, sans-serif;
    --color-accent: #10B981;
    --color-accent-strong: #047857;
    --color-focus: #047857;
    --color-accent-soft: rgba(16, 185, 129, 0.12);
    --color-accent-ink: #052E25;
    --color-danger: #B91C1C;
    --color-warning: #FBBF24;
    --color-warning-ink: #171717;
    --color-closed: #737373;
    --color-rule: rgba(128, 128, 128, 0.22);
    --color-rule-strong: rgba(128, 128, 128, 0.42);
    --color-surface: rgba(128, 128, 128, 0.06);
    --color-surface-raised: rgba(128, 128, 128, 0.11);
    --color-on-status: #FFFFFF;
    --color-photo: #FFFFFF;
    --color-text-shadow: rgba(0, 0, 0, 0.5);
    --space-2xs: 0.25rem;
    --space-xs: 0.5rem;
    --space-sm: 0.75rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-pill: 999px;
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
    --dur-short: 180ms;
}

html, body, .stApp {
    font-family: var(--font-body);
    overflow-x: clip;
}

.block-container {
    width: 100%;
    max-width: 1400px;
    padding-block: clamp(1rem, 3vw, 2rem) 6rem;
    padding-inline: clamp(0.75rem, 3vw, 2rem);
}

/* Operational header */
.ldp-header {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-xs);
    margin-bottom: var(--space-lg);
    padding-bottom: var(--space-md);
    border-bottom: 1px solid var(--color-rule);
    text-align: left;
}

.ldp-title {
    margin: 0;
    min-width: 0;
    font-family: var(--font-display);
    font-size: clamp(2rem, 9vw, 3rem);
    font-weight: 700;
    line-height: 0.95;
    letter-spacing: -0.02em;
    overflow-wrap: anywhere;
}

.ldp-subtitle {
    margin: 0;
    max-width: 48rem;
    font-size: 0.95rem;
    font-weight: 500;
    opacity: 0.72;
}

.credit-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-xs) var(--space-md);
    margin-top: var(--space-xs);
    font-size: 0.78rem;
}

.credit-container a {
    color: var(--color-accent);
    font-weight: 700;
    text-decoration: none;
}

.tako-btn {
    display: inline-flex;
    min-height: 44px;
    align-items: center;
    padding-inline: var(--space-md);
    border-radius: var(--radius-pill);
    background: var(--color-danger);
    color: var(--color-on-status) !important;
    white-space: nowrap;
}

.live-badge {
    display: inline-flex;
    width: fit-content;
    min-height: 32px;
    align-items: center;
    gap: var(--space-xs);
    padding-inline: var(--space-sm);
    border: 1px solid var(--color-accent);
    border-radius: var(--radius-pill);
    background: var(--color-accent-soft);
    color: var(--color-accent);
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.04em;
}

.live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent);
    animation: live-pulse 2s infinite;
}

@keyframes live-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.35; }
}

/* Streamlit control rails */
.st-key-event_filters [data-testid="stHorizontalBlock"],
.st-key-summary_metrics [data-testid="stHorizontalBlock"] {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-sm);
}

.st-key-event_filters [data-testid="stColumn"],
.st-key-summary_metrics [data-testid="stColumn"] {
    width: 100% !important;
    min-width: 0;
}

.st-key-summary_metrics [data-testid="stMetric"] {
    font-variant-numeric: tabular-nums;
}

.st-key-summary_metrics [data-testid="stMetricValue"] {
    font-family: var(--font-display);
    letter-spacing: -0.01em;
}

div[class*="st-key-filter_date_"] [role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-xs) var(--space-md);
}

div[class*="st-key-filter_date_"] [role="radiogroup"] label {
    min-height: 44px;
    align-items: center;
    white-space: nowrap;
}

/* Session and member workbench */
.session-heading {
    margin: var(--space-xs) 0 var(--space-sm);
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    line-height: 1.1;
}

.session-time {
    font-family: var(--font-body);
    font-size: 0.76rem;
    font-weight: 500;
    opacity: 0.58;
}

.cards-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: var(--space-sm);
    margin-bottom: var(--space-xl);
}

.ldp-card {
    position: relative;
    min-width: 0;
    min-height: 228px;
    padding: var(--space-md) var(--space-sm);
    border: 1px solid var(--color-rule);
    border-bottom-width: 4px;
    border-radius: var(--radius-md);
    background: var(--color-surface);
    color: inherit;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    text-decoration: none !important;
    transition: transform var(--dur-short) var(--ease-out), border-color var(--dur-short) var(--ease-out), background-color var(--dur-short) var(--ease-out);
}

.ldp-card.avail { border-bottom-color: var(--color-accent); }
.ldp-card.warn { border-bottom-color: var(--color-warning); }
.ldp-card.sold { border-bottom-color: var(--color-danger); }
.ldp-card.closed { border-bottom-color: var(--color-closed); opacity: 0.86; }

.purchase-card:focus-visible,
.credit-container a:focus-visible,
.tako-btn:focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: 3px;
}

.c-badge {
    position: absolute;
    top: var(--space-xs);
    right: var(--space-xs);
    z-index: 2;
    padding: 0.25rem 0.45rem;
    border-radius: var(--radius-pill);
    background: var(--color-accent);
    color: var(--color-accent-ink);
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: 0.04em;
}

.ldp-card.warn .c-badge {
    background: var(--color-warning);
    color: var(--color-warning-ink);
}

.c-photo {
    width: 72px;
    height: 72px;
    flex: 0 0 72px;
    margin: var(--space-sm) auto;
    border: 2px solid var(--color-rule-strong);
    border-radius: 50%;
    background: var(--color-photo);
    object-fit: cover;
    object-position: center 8%;
}

.ldp-card.sold .c-photo,
.ldp-card.closed .c-photo {
    filter: saturate(35%);
    opacity: 0.82;
}

.c-jalur {
    width: 100%;
    min-height: 1.25rem;
    padding-inline: 2.5rem;
    overflow: hidden;
    color: inherit;
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.035em;
    line-height: 1.25;
    opacity: 0.62;
    text-overflow: ellipsis;
    text-transform: uppercase;
    white-space: nowrap;
}

.c-member {
    width: 100%;
    min-width: 0;
    height: 2.5em;
    margin-bottom: var(--space-xs);
    display: -webkit-box;
    overflow: hidden;
    font-size: 0.88rem;
    font-weight: 700;
    line-height: 1.25;
    overflow-wrap: anywhere;
    text-overflow: ellipsis;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
}

.c-card-foot {
    width: 100%;
    margin-top: auto;
}

.c-stats {
    width: 100%;
    margin-bottom: var(--space-xs);
    display: flex;
    justify-content: center;
    font-size: 0.72rem;
    font-variant-numeric: tabular-nums;
}

.c-stats b { margin-left: 0.2rem; font-weight: 800; }

.c-prog-btn {
    position: relative;
    width: 100%;
    min-height: 36px;
    border: 1px solid var(--color-rule-strong);
    border-radius: var(--radius-sm);
    background: var(--color-surface-raised);
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

.c-prog-fill {
    position: absolute;
    inset: 0;
    z-index: 0;
    transform-origin: left center;
    transition: transform 400ms var(--ease-out);
}

.ldp-card.avail .c-prog-fill { background: var(--color-accent); }
.ldp-card.warn .c-prog-fill { background: var(--color-warning); }
.ldp-card.sold .c-prog-fill { background: var(--color-danger); }
.ldp-card.closed .c-prog-fill { background: var(--color-closed); }

.c-prog-text {
    position: relative;
    z-index: 1;
    color: var(--color-on-status);
    padding: 0.15rem 0.4rem;
    border-radius: var(--radius-sm);
    background: var(--color-text-shadow);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.035em;
    white-space: nowrap;
}

/* Share capture banner and fixed export layout */
.share-banner {
    padding: var(--space-md);
    border-radius: var(--radius-md);
    background: var(--color-accent-strong);
    color: var(--color-on-status);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-md);
    margin-bottom: var(--space-md);
}

.sb-left h3 { margin: 0 0 var(--space-2xs); font-family: var(--font-display); font-size: 1.2rem; line-height: 1; overflow-wrap: anywhere; }
.sb-left p { margin: 0; font-size: 0.72rem; font-weight: 600; }
.sb-right { text-align: right; }
.sb-time { font-size: 0.7rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.sb-wm { margin-top: var(--space-2xs); font-size: 0.58rem; font-weight: 700; letter-spacing: 0.04em; }

.capture-mode {
    width: 1080px !important;
    padding: 20px !important;
}

.capture-mode .cards-grid {
    grid-template-columns: repeat(7, minmax(0, 1fr)) !important;
    gap: 12px !important;
    margin-bottom: 22px;
}

.capture-mode .ldp-card {
    min-height: 210px;
    padding: 12px 10px;
}

@media (min-width: 22rem) {
    .cards-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (min-width: 40rem) {
    .ldp-header {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
    }
    .ldp-title, .ldp-subtitle, .credit-container { grid-column: 1; }
    .live-badge { grid-column: 2; grid-row: 1 / span 2; }
    .st-key-event_filters [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .st-key-summary_metrics [data-testid="stHorizontalBlock"] { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .cards-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (min-width: 64rem) {
    .st-key-event_filters [data-testid="stHorizontalBlock"] { grid-template-columns: minmax(0, 1.3fr) minmax(0, 2.5fr) minmax(0, 1.2fr) minmax(0, 1.2fr); }
    .cards-grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--space-md); }
}

@media (hover: hover) and (pointer: fine) {
    .ldp-card.purchase-card:hover { transform: translateY(-2px); border-color: var(--color-rule-strong); background: var(--color-surface-raised); }
    .credit-container a:hover { text-decoration: underline; }
    .tako-btn:hover { transform: translateY(-1px); }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""
