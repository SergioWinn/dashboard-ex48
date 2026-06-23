# ui/styles.py

GLOBAL_CSS = """
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
    position: relative;
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

/* --- BADGE STATUS BARU DI POJOK KARTU --- */
.c-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    font-size: 8px;
    font-weight: 800;
    padding: 4px 8px;
    border-radius: 12px;
    color: white;
    letter-spacing: 0.5px;
    z-index: 2;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.ldp-card.avail .c-badge { background: #10B981; }
.ldp-card.warn .c-badge { background: #FBBF24; color: #000; }
.ldp-card.sold .c-badge { background: #EF4444; }

/* Border Status Tetap Ada Sebagai Aksen */
.ldp-card.avail { border-bottom: 5px solid #10B981; }
.ldp-card.warn { border-bottom: 5px solid #FBBF24; animation: glow 2s infinite; }
.ldp-card.sold { border-bottom: 5px solid #EF4444; opacity: 0.8; } 
.ldp-card.sold .c-photo { 
    opacity: 0.35; /* Dibuat sangat transparan sehingga menyatu dengan background */
    filter: brightness(0.8) saturate(75%); /* Warnanya sedikit saja diturunkan biar tidak terlalu "nyala" */
}

/* Foto Kabesha */
.c-photo { 
    width: 74px; 
    height: 74px; 
    border-radius: 50%; 
    background-size: 105%; 
    background-position: center 5%; 
    background-repeat: no-repeat;
    margin: 0 auto 12px auto; 
    border: 2px solid rgba(128, 128, 128, 0.2); 
    box-shadow: 0 4px 10px rgba(0,0,0,0.15); 
    background-color: #ffffff; 
    display: block;
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

/* --- SMART PROGRESS BUTTON --- */
.c-stats { 
    font-size: 11px; 
    color: inherit; 
    opacity: 0.9; 
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
    background: rgba(128, 128, 128, 0.25); 
    border-radius: 8px; 
    overflow: hidden; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
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
/* Tambahkan white-space: pre-wrap agar spasi dikunci mati dan tidak ditelan canvas */
.sb-left h3 { margin: 0 0 4px 0; font-size: 14px; font-weight: 800; white-space: pre-wrap; }
.sb-left p { margin: 0; font-size: 11px; opacity: 0.9; font-weight: 600; white-space: pre-wrap; }
.sb-right { text-align: right; }
.sb-right .sb-time { font-size: 11px; font-weight: 700; background: rgba(0,0,0,0.25); padding: 4px 10px; border-radius: 20px; display: inline-block; border: 1px solid rgba(255,255,255,0.2); white-space: pre-wrap; }
.sb-right .sb-wm { font-size: 9px; margin-top: 5px; opacity: 0.8; font-weight: 700; letter-spacing: 0.5px; white-space: pre-wrap; }

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
