import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

from data.stocks_list import STOCKS_LIST, get_sector
from modules.data_fetcher import get_stock_data, get_current_price, get_fundamental_data
from modules.open_low_scanner import scan_open_low_pattern, get_pattern_summary
from modules.low_float_scanner import scan_low_float, get_low_float_summary
from modules.ai_analyzer import analyze_pattern, analyze_low_float, predict_next_pattern, get_market_context
from utils.exporters import export_to_excel, format_number

# ══════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════
BLUE_CHIP = [
    "BBCA","BBRI","BMRI","BBNI","BTPS","BRIS","TLKM","ISAT","EXCL","TOWR","MTEL",
    "UNVR","ICBP","INDF","KLBF","GGRM","HMSP","ASII","UNTR","ADRO","BYAN","PTBA",
    "ITMG","CPIN","JPFA","MAIN","SIDO","ULTJ","SMGR","INTP","SMCB","PGAS","MEDC",
    "ELSA","ANTM","INCO","MDKA","HRUM","BRPT","TPIA","WIKA","PTPP","WSKT","ADHI","JSMR",
]
SECOND_LINER = [
    "AKRA","INKP","BUMI","PTRO","DOID","TINS","BRMS","DKFT","BMTR","MAPI","ERAA",
    "ACES","MIKA","SILO","HEAL","PRAY","CLEO","ROTI","MYOR","GOOD","SKBM","SKLT",
    "STTP","WSBP","PBSA","MTFN","BKSL","SMRA","CTRA","BSDE","PWON","LPKR","LPCK",
    "DILD","RDTX","MREI","PZZA","MAPB","DMAS","LMPI","ARNA","TOTO","MLIA","INTD",
    "IKAI","JECC","KBLI","KBLM","VOKS","UNIT","INAI","IMPC","ASGR","POWR","RAJA",
    "PJAA","SAME","SCCO","SPMA","SRSN","TALF","TRST","TSPC","UNIC","YPAS",
]
FCA_STOCKS = ["COIN","CDIA"]
SHAREHOLDERS = {
    "BBCA": {
        "pemegang": [{"nama":"BPJS Ketenagakerjaan","persen":1.06,"tipe":"Institusi"},{"nama":"Vanguard","persen":1.23,"tipe":"Asing"}],
        "free_float": 95.67,
        "insider": [
            {"tanggal":"10 Mar 2026","insider":"Presdir","aksi":"BELI","jumlah":1000000,"harga":10250},
            {"tanggal":"25 Feb 2026","insider":"Komisaris","aksi":"BELI","jumlah":500000,"harga":10100},
        ]
    },
    "BBRI":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.09,"tipe":"Institusi"}],"free_float":98.91,"insider":[{"tanggal":"09 Mar 2026","insider":"Dirut","aksi":"JUAL","jumlah":50000,"harga":5800}]},
    "MDKA":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":2.15,"tipe":"Institusi"},{"nama":"Pemerintah Norwegia","persen":1.08,"tipe":"Asing"}],"free_float":89.31,"insider":[{"tanggal":"15 Feb 2026","insider":"Dirut","aksi":"BELI","jumlah":200000,"harga":2500}]},
    "CUAN":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.02,"tipe":"Institusi"},{"nama":"Vanguard","persen":1.15,"tipe":"Asing"}],"free_float":13.73,"insider":[{"tanggal":"05 Mar 2026","insider":"Direktur Utama","aksi":"BELI","jumlah":100000,"harga":15000}]},
    "BRPT":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.22,"tipe":"Institusi"}],"free_float":27.41,"insider":[{"tanggal":"28 Feb 2026","insider":"Komisaris","aksi":"JUAL","jumlah":75000,"harga":8500}]},
    "TPIA":  {"pemegang":[{"nama":"GIC Singapore","persen":3.45,"tipe":"Asing"}],"free_float":91.52,"insider":[]},
    "ASII":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":2.74,"tipe":"Institusi"}],"free_float":97.26,"insider":[]},
    "KLBF":  {"pemegang":[{"nama":"Pemerintah Norwegia","persen":1.30,"tipe":"Asing"},{"nama":"BPJS Ketenagakerjaan","persen":2.01,"tipe":"Institusi"}],"free_float":96.69,"insider":[]},
    "BYAN":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.33,"tipe":"Institusi"}],"free_float":58.45,"insider":[]},
    "ARTO":  {"pemegang":[{"nama":"Pemerintah Singapura","persen":8.28,"tipe":"Asing"}],"free_float":91.72,"insider":[]},
    "MTEL":  {"pemegang":[{"nama":"Pemerintah Singapura","persen":5.33,"tipe":"Asing"}],"free_float":94.67,"insider":[]},
    "AKRA":  {"pemegang":[{"nama":"Pemerintah Norwegia","persen":3.03,"tipe":"Asing"}],"free_float":96.97,"insider":[]},
    "INDF":  {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":3.74,"tipe":"Institusi"}],"free_float":92.52,"insider":[]},
}

def lvl(c):
    if c in BLUE_CHIP:    return "\U0001f48e Blue Chip"
    if c in SECOND_LINER: return "\U0001f4c8 Second Liner"
    return "\U0001f3af Third Liner"
def lvl_s(c): return {"\U0001f48e Blue Chip":"BC","\U0001f4c8 Second Liner":"SL","\U0001f3af Third Liner":"TL"}.get(lvl(c),"")
def by_lvl(ls):
    r=[]
    if "Blue Chip" in ls:    r+=BLUE_CHIP
    if "Second Liner" in ls: r+=SECOND_LINER
    if "Third Liner" in ls:  r+=[s for s in STOCKS_LIST if s not in BLUE_CHIP and s not in SECOND_LINER]
    return list(set(r))
def ff(c):     return SHAREHOLDERS.get(c,{}).get("free_float",100.0)
def hlds(c):   return SHAREHOLDERS.get(c,{}).get("pemegang",[])
def ins(c):    return SHAREHOLDERS.get(c,{}).get("insider",[])
def fca(c):    return c in FCA_STOCKS
def pot(f):
    if f<10: return "\U0001f525 UT"
    if f<15: return "\U0001f525 ST"
    if f<25: return "\u26a1 TG"
    if f<40: return "\U0001f4ca SD"
    return "\U0001f4c9 RD"
def kat(k):    return {"Ultra Low Float":"ULF","Very Low Float":"VLF","Low Float":"LF","Moderate Low Float":"MLF","Normal Float":"NF"}.get(k,k)

# ══════════════════════════════════════════════════════════════
# HTML COMPONENTS  (list + join only, zero f-string in HTML)
# ══════════════════════════════════════════════════════════════
def html_ff_card(code):
    f   = ff(code); h = hlds(code); ia = ins(code)
    p   = []
    p.append("<div style=\"background:linear-gradient(135deg,#0d1117 0%,#161b22 100%);border:1px solid #21262d;border-radius:14px;padding:20px 24px;margin:14px 0;box-shadow:0 4px 28px rgba(0,0,0,0.5);">")
    # header
    p.append("<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;\">")
    p.append("<div style=\"display:flex;align-items:center;gap:10px;\">")
    p.append("<div style=\"width:4px;height:22px;background:linear-gradient(180deg,#f0b429,#e88c0e);border-radius:2px;flex-shrink:0;\"></div>")
    p.append("<span style=\"color:#f0b429;font-family:Space Mono,monospace;font-size:.9rem;font-weight:700;letter-spacing:1px;\">FREE FLOAT \u2014 " + code + "</span>")
    p.append("</div>")
    if fca(code):
        p.append("<span style=\"background:rgba(255,170,0,.1);border:1px solid rgba(255,170,0,.4);border-radius:20px;padding:3px 12px;color:#ffaa00;font-size:.74rem;font-family:Space Mono,monospace;\">\u26a0 FCA</span>")
    p.append("</div>")
    # total FF
    p.append("<div style=\"background:rgba(0,255,136,.06);border:1px solid rgba(0,255,136,.2);border-radius:10px;padding:12px 18px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;\">")
    p.append("<span style=\"color:#8b949e;font-size:.84rem;\">Total Free Float</span>")
    p.append("<span style=\"color:#00ff88;font-weight:700;font-size:1.2rem;font-family:Space Mono,monospace;\">" + str(round(f,1)) + "%</span>")
    p.append("</div>")
    # holder bars
    total_i = 0.0
    for h_ in h:
        pct = (h_["persen"]/f*100) if f>0 else 0; total_i += pct
        warna = "#58a6ff" if h_["tipe"]=="Institusi" else "#3fb950"
        bw    = str(round(min(pct*2,100)))
        p.append("<div style=\"background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:10px 14px;margin:5px 0;\">")
        p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;\">")
        p.append("<div style=\"display:flex;align-items:center;gap:8px;\">")
        p.append("<span style=\"width:8px;height:8px;border-radius:50%;background:" + warna + ";display:inline-block;flex-shrink:0;\"></span>")
        p.append("<span style=\"color:#e6edf3;font-size:.83rem;\">" + h_["nama"] + "</span>")
        p.append("<span style=\"color:#484f58;font-size:.72rem;background:rgba(255,255,255,.04);padding:1px 7px;border-radius:10px;\">" + h_["tipe"] + "</span>")
        p.append("</div>")
        p.append("<span style=\"color:" + warna + ";font-weight:700;font-family:Space Mono,monospace;font-size:.88rem;\">" + str(round(pct,1)) + "%</span>")
        p.append("</div>")
        p.append("<div style=\"height:3px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden;\"><div style=\"width:" + bw + "%;height:3px;background:" + warna + ";border-radius:2px;\"></div></div>")
        p.append("</div>")
    ritel = 100.0 - total_i; bwr = str(round(min(ritel*0.65,100)))
    p.append("<div style=\"background:rgba(0,255,136,.05);border:1px solid rgba(0,255,136,.15);border-radius:8px;padding:10px 14px;margin:5px 0;\">")
    p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;\">")
    p.append("<div style=\"display:flex;align-items:center;gap:8px;\"><span style=\"width:8px;height:8px;border-radius:50%;background:#00ff88;display:inline-block;flex-shrink:0;\"></span><span style=\"color:#e6edf3;font-size:.83rem;\">Ritel</span></div>")
    p.append("<span style=\"color:#00ff88;font-weight:700;font-family:Space Mono,monospace;font-size:.88rem;\">" + str(round(ritel,1)) + "%</span>")
    p.append("</div>")
    p.append("<div style=\"height:3px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden;\"><div style=\"width:" + bwr + "%;height:3px;background:#00ff88;border-radius:2px;\"></div></div>")
    p.append("</div>")
    if not h:
        p.append("<p style=\"color:#484f58;font-size:.82rem;margin:4px 0 10px;\">Tidak ada institusi/asing &gt;1%</p>")
    # insider
    if ia:
        p.append("<div style=\"border-top:1px solid #21262d;padding-top:14px;margin-top:14px;\">")
        p.append("<div style=\"color:#484f58;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;\">Aktivitas Insider \u00b7 30 Hari</div>")
        for a in ia:
            buy = a["aksi"]=="BELI"
            ac  = "#3fb950" if buy else "#f85149"
            ab  = "rgba(63,185,80,.07)" if buy else "rgba(248,81,73,.07)"
            abd = "rgba(63,185,80,.22)" if buy else "rgba(248,81,73,.22)"
            jf  = "{:,}".format(a["jumlah"])
            p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;background:" + ab + ";border:1px solid " + abd + ";border-radius:8px;padding:8px 13px;margin:4px 0;\">")
            p.append("<span style=\"color:#8b949e;font-size:.79rem;font-family:Space Mono,monospace;\">" + a["tanggal"] + "</span>")
            p.append("<span style=\"color:#e6edf3;font-size:.79rem;\">" + a["insider"] + "</span>")
            p.append("<span style=\"color:" + ac + ";font-weight:700;font-size:.82rem;font-family:Space Mono,monospace;\">" + a["aksi"] + " " + jf + "</span>")
            p.append("</div>")
        p.append("</div>")
    p.append("</div>")
    return "".join(p)


def html_scan_row(stk, i, total, el, rem):
    pct = str(round((i+1)/total*100))
    return "".join([
        "<div style=\"background:rgba(255,255,255,.02);border:1px solid #21262d;border-radius:10px;padding:11px 18px;\">",
        "<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;\">",
        "<span style=\"color:#f0b429;font-family:Space Mono,monospace;font-size:.88rem;\">\u25c9 " + stk + "</span>",
        "<span style=\"color:#484f58;font-size:.78rem;\">" + str(i+1) + "/" + str(total) + " &nbsp;\u00b7&nbsp; " + str(round(el)) + "s &nbsp;\u00b7&nbsp; ~" + str(round(rem)) + "s sisa</span>",
        "</div>",
        "<div style=\"height:3px;background:#1c2230;border-radius:2px;overflow:hidden;\">",
        "<div style=\"width:" + pct + "%;height:3px;background:linear-gradient(90deg,#f0b429,#e88c0e);border-radius:2px;transition:width .3s;\"></div>",
        "</div></div>",
    ])


def html_scan_done(count, secs, period, gain):
    return "".join([
        "<div style=\"background:linear-gradient(135deg,#0d1117 0%,#161b22 100%);border:1px solid #1c2230;border-radius:16px;padding:28px 32px;margin:20px 0;position:relative;overflow:hidden;\">",
        "<div style=\"position:absolute;top:0;right:0;width:280px;height:100%;background:radial-gradient(ellipse at top right,rgba(63,185,80,.09) 0%,transparent 65%);pointer-events:none;\"></div>",
        # watermark number
        "<div style=\"position:absolute;right:32px;top:50%;transform:translateY(-50%);font-family:Space Mono,monospace;font-size:5.5rem;font-weight:700;color:rgba(240,180,41,.05);line-height:1;pointer-events:none;\">" + str(count) + "</div>",
        "<div style=\"display:flex;align-items:center;gap:20px;flex-wrap:wrap;position:relative;\">",
        "<div style=\"width:56px;height:56px;background:linear-gradient(135deg,rgba(63,185,80,.18),rgba(63,185,80,.04));border:1px solid rgba(63,185,80,.3);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.8rem;flex-shrink:0;\">\u2705</div>",
        "<div>",
        "<div style=\"color:#3fb950;font-family:Space Mono,monospace;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;\">SCAN BERHASIL</div>",
        "<div style=\"color:#f0f6fc;font-size:2rem;font-weight:700;font-family:Space Mono,monospace;margin-top:4px;line-height:1;\">" + str(count) + " <span style=\"font-size:.95rem;color:#8b949e;font-weight:400;\">saham ditemukan</span></div>",
        "</div>",
        "<div style=\"margin-left:auto;display:flex;gap:28px;flex-wrap:wrap;\">",
        "<div style=\"text-align:center;\"><div style=\"color:#484f58;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;\">Waktu Proses</div><div style=\"color:#f0b429;font-family:Space Mono,monospace;font-size:1.2rem;margin-top:4px;\">" + str(round(secs)) + "s</div></div>",
        "<div style=\"width:1px;height:36px;background:#21262d;align-self:center;\"></div>",
        "<div style=\"text-align:center;\"><div style=\"color:#484f58;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;\">Periode</div><div style=\"color:#58a6ff;font-family:Space Mono,monospace;font-size:1.2rem;margin-top:4px;\">" + period + "</div></div>",
        "<div style=\"width:1px;height:36px;background:#21262d;align-self:center;\"></div>",
        "<div style=\"text-align:center;\"><div style=\"color:#484f58;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;\">Min Gain</div><div style=\"color:#00ff88;font-family:Space Mono,monospace;font-size:1.2rem;margin-top:4px;\">" + str(gain) + "%</div></div>",
        "</div></div></div>",
    ])


def html_empty(msg, hint):
    return "".join([
        "<div style=\"background:rgba(248,81,73,.05);border:1px solid rgba(248,81,73,.18);border-radius:14px;padding:36px;text-align:center;\">",
        "<div style=\"font-size:2.2rem;margin-bottom:10px;\">\U0001f50d</div>",
        "<div style=\"color:#f85149;font-family:Space Mono,monospace;font-size:.84rem;letter-spacing:1px;\">" + msg + "</div>",
        "<div style=\"color:#484f58;font-size:.79rem;margin-top:6px;\">" + hint + "</div>",
        "</div>",
    ])


def html_watchlist_top(date_s):
    return "".join([
        "<div style=\"background:linear-gradient(135deg,#0d1117,#161b22);border:1px solid rgba(88,166,255,.15);border-radius:12px;padding:20px 26px;margin:16px 0;position:relative;overflow:hidden;\">",
        "<div style=\"position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#58a6ff 40%,#f0b429 60%,transparent);\"></div>",
        "<div style=\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;\">",
        "<div><div style=\"color:#58a6ff;font-family:Space Mono,monospace;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;\">WATCHLIST TRADING</div>",
        "<div style=\"color:#f0f6fc;font-size:1.05rem;font-weight:600;margin-top:4px;\">" + date_s + "</div></div>",
        "<div style=\"background:rgba(240,180,41,.08);border:1px solid rgba(240,180,41,.25);border-radius:20px;padding:6px 16px;color:#f0b429;font-size:.8rem;font-family:Space Mono,monospace;\">\U0001f3af Pantau 15 menit pertama!</div>",
        "</div></div>",
    ])


# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Radar Aksara", page_icon="\U0001f4e1", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Sora:wght@300;400;500;600;700&display=swap');

:root {
    --gold:   #f0b429;
    --gold2:  #e88c0e;
    --green:  #00ff88;
    --blue:   #58a6ff;
    --red:    #f85149;
    --navy:   #0a0e17;
    --card:   #0d1117;
    --card2:  #161b22;
    --border: #21262d;
    --text:   #e6edf3;
    --muted:  #8b949e;
    --dim:    #484f58;
}

html, body, [class*="css"] { font-family: Sora, sans-serif; }
.stApp { background: var(--navy); }
.main .block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1400px; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--card); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #30363d; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e17 100%) !important;
    border-right: 1px solid #1c2230 !important;
}

/* Widget labels */
.stRadio [data-testid="stWidgetLabel"],
.stSelectbox label, .stMultiSelect label,
.stSlider [data-testid="stWidgetLabel"],
.stNumberInput label {
    color: var(--muted) !important; font-size: .78rem !important;
    font-weight: 600 !important; letter-spacing: .5px !important;
    text-transform: uppercase !important;
}
.stCheckbox label { color: var(--text) !important; font-size: .85rem !important; }

/* Radio pills */
div[role="radiogroup"] label {
    background: rgba(255,255,255,.02) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important; padding: 5px 14px !important;
    color: var(--muted) !important; font-size: .84rem !important;
    transition: all .2s !important;
}
div[role="radiogroup"] label:hover {
    border-color: var(--gold) !important; color: var(--gold) !important;
    background: rgba(240,180,41,.06) !important;
    box-shadow: 0 0 12px rgba(240,180,41,.12) !important;
}

/* Selects */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: rgba(255,255,255,.03) !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important; color: var(--text) !important;
}
.stSelectbox > div > div:hover, .stMultiSelect > div > div:hover {
    border-color: var(--blue) !important;
}
.stNumberInput input {
    background: rgba(255,255,255,.03) !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important; color: var(--text) !important;
}
.stSlider .st-be { background: #1c2230 !important; }
.stSlider .st-bf { background: var(--gold) !important; }

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold2) 100%) !important;
    color: var(--navy) !important; font-family: "Space Mono", monospace !important;
    font-weight: 700 !important; font-size: .88rem !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    border: none !important; border-radius: 10px !important;
    padding: .68rem 2rem !important;
    box-shadow: 0 4px 22px rgba(240,180,41,.28) !important;
    transition: all .25s !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 32px rgba(240,180,41,.5) !important;
    transform: translateY(-1px) !important;
}

/* Secondary button */
.stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,.03) !important; color: var(--text) !important;
    border: 1px solid #30363d !important; border-radius: 8px !important;
    font-size: .84rem !important; transition: all .2s !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--blue) !important; color: var(--blue) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: rgba(255,255,255,.02) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important; padding: 16px !important;
    transition: border-color .2s !important;
}
[data-testid="metric-container"]:hover { border-color: rgba(240,180,41,.3) !important; }
[data-testid="metric-container"] label {
    color: var(--muted) !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: .8px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--gold) !important; font-family: "Space Mono", monospace !important;
    font-size: 1.55rem !important;
}

/* Dataframe */
.stDataFrame { border: 1px solid #1c2230 !important; border-radius: 12px !important; overflow: hidden !important; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(255,255,255,.02) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--text) !important;
    font-size: .87rem !important; transition: all .2s !important;
}
.streamlit-expanderHeader:hover { border-color: var(--gold) !important; color: var(--gold) !important; }
.streamlit-expanderContent {
    background: rgba(13,17,23,.9) !important; border: 1px solid var(--border) !important;
    border-top: none !important; border-radius: 0 0 10px 10px !important;
}

/* Alerts */
.stInfo    { background: rgba(88,166,255,.05) !important;  border: 1px solid rgba(88,166,255,.2) !important;  border-radius: 8px !important; color: var(--muted) !important; font-size: .84rem !important; }
.stWarning { background: rgba(240,180,41,.05) !important;  border: 1px solid rgba(240,180,41,.22) !important; border-radius: 8px !important; color: var(--text) !important;  font-size: .84rem !important; }
.stSuccess { background: rgba(63,185,80,.05) !important;   border: 1px solid rgba(63,185,80,.2) !important;   border-radius: 8px !important; }
.stError   { background: rgba(248,81,73,.05) !important;   border: 1px solid rgba(248,81,73,.2) !important;   border-radius: 8px !important; }

/* Progress bar */
.stProgress > div > div { background: linear-gradient(90deg, var(--gold), var(--gold2)) !important; border-radius: 3px !important; }
.stProgress > div       { background: #1c2230 !important; border-radius: 3px !important; }

/* Download */
.stDownloadButton > button {
    background: rgba(255,255,255,.03) !important; border: 1px solid #30363d !important;
    border-radius: 8px !important; color: var(--text) !important;
    font-size: .84rem !important; width: 100% !important; transition: all .2s !important;
}
.stDownloadButton > button:hover {
    border-color: #3fb950 !important; color: #3fb950 !important;
    background: rgba(63,185,80,.04) !important;
}

hr { border-color: #1c2230 !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
now = datetime.now()
st.markdown("".join([
    "<div style=\"background:linear-gradient(135deg,#0d1117 0%,#161b22 100%);border:1px solid #1c2230;border-radius:16px;padding:28px 32px;margin-bottom:24px;position:relative;overflow:hidden;\">",
    # glows
    "<div style=\"position:absolute;top:0;right:0;width:340px;height:100%;background:radial-gradient(ellipse at top right,rgba(240,180,41,.08) 0%,transparent 60%);pointer-events:none;\"></div>",
    "<div style=\"position:absolute;bottom:0;left:40px;width:220px;height:220px;background:radial-gradient(ellipse,rgba(88,166,255,.04) 0%,transparent 70%);pointer-events:none;\"></div>",
    "<div style=\"display:flex;align-items:center;gap:18px;position:relative;flex-wrap:wrap;\">",
    # icon
    "<div style=\"width:54px;height:54px;background:linear-gradient(135deg,#f0b429,#e88c0e);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;flex-shrink:0;box-shadow:0 4px 20px rgba(240,180,41,.4);\">\U0001f4e1</div>",
    # text
    "<div>",
    "<div style=\"font-family:Space Mono,monospace;font-size:1.75rem;font-weight:700;letter-spacing:1px;line-height:1;color:#f0f6fc;\">RADAR <span style=\"color:#f0b429;\">AKSARA</span></div>",
    "<div style=\"color:#484f58;font-size:.79rem;margin-top:6px;letter-spacing:.3px;\">Open=Low Pattern &nbsp;\u00b7&nbsp; Low Float Scanner &nbsp;\u00b7&nbsp; Blue Chip &nbsp;\u00b7&nbsp; Second Liner &nbsp;\u00b7&nbsp; Third Liner</div>",
    "</div>",
    # live badge
    "<div style=\"margin-left:auto;display:flex;flex-direction:column;align-items:flex-end;gap:4px;\">",
    "<div style=\"display:flex;align-items:center;gap:7px;background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.2);border-radius:20px;padding:5px 14px;\">",
    "<span style=\"width:6px;height:6px;border-radius:50%;background:#3fb950;display:inline-block;\"></span>",
    "<span style=\"color:#3fb950;font-family:Space Mono,monospace;font-size:.76rem;letter-spacing:1px;\">LIVE</span>",
    "</div>",
    "<div style=\"color:#484f58;font-size:.74rem;font-family:Space Mono,monospace;\">" + now.strftime("%d %b %Y &nbsp;\u00b7&nbsp; %H:%M") + " WIB</div>",
    "</div>",
    "</div></div>",
]), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style=\"background:linear-gradient(135deg,rgba(240,180,41,.08) 0%,transparent 100%);border:1px solid rgba(240,180,41,.15);border-radius:10px;padding:12px 16px;margin-bottom:18px;\">"
        "<div style=\"font-family:Space Mono,monospace;color:#f0b429;font-size:.75rem;letter-spacing:2px;\">\u2699\ufe0f CONTROL PANEL</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    scan_mode = st.radio("Mode Scanning", ["\U0001f4c8 Open = Low Scanner", "\U0001f50d Low Float Scanner"], index=0)
    st.markdown("---")
    filter_type    = st.radio("Filter Saham", ["Semua Saham", "Pilih Manual", "Filter Tingkatan"], index=0)
    sel_stocks, sel_levels = [], []
    if filter_type == "Pilih Manual":
        sel_stocks = st.multiselect("Pilih Saham", options=STOCKS_LIST, default=[])
    elif filter_type == "Filter Tingkatan":
        sel_levels = st.multiselect("Tingkatan", ["Blue Chip","Second Liner","Third Liner"],
                                    default=["Blue Chip","Second Liner","Third Liner"])
        if sel_levels:
            cnt = len(by_lvl(sel_levels))
            st.info(str(cnt) + " saham \u00b7 ~" + str(round(cnt*0.5/60,1)) + " menit")
    st.markdown("---")
    st.markdown("<div style=\"color:#484f58;font-family:Space Mono,monospace;font-size:.68rem;letter-spacing:1px;margin-bottom:10px;\">LEGENDA</div>", unsafe_allow_html=True)
    for ic,lb,ds in [("\U0001f48e","Blue Chip","> Rp10T"),("\U0001f4c8","Second Liner","Rp500M\u2013Rp10T"),("\U0001f3af","Third Liner","< Rp1T"),("\u26a0\ufe0f","FCA","Papan Pemantauan")]:
        st.markdown(
            "<div style=\"display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);\">"
            "<span style=\"font-size:.95rem;\">" + ic + "</span>"
            "<div><div style=\"color:#c9d1d9;font-size:.8rem;\">" + lb + "</div><div style=\"color:#484f58;font-size:.71rem;\">" + ds + "</div></div>"
            "</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style=\"text-align:center;color:#30363d;font-size:.7rem;font-family:Space Mono,monospace;\">RADAR AKSARA \u00b7 IDX SCANNER</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def section_hdr(title, sub=""):
    sub_html = ("<div style=\"color:#484f58;font-size:.78rem;margin-top:3px;\">" + sub + "</div>") if sub else ""
    st.markdown(
        "<div style=\"display:flex;align-items:center;gap:12px;margin:28px 0 16px;\">"
        "<div style=\"width:3px;height:22px;background:linear-gradient(180deg,#f0b429,#e88c0e);border-radius:2px;flex-shrink:0;\"></div>"
        "<div><div style=\"color:#f0f6fc;font-size:1rem;font-weight:600;\">" + title + "</div>" + sub_html + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

def plotly_bar(df_, x_, y_, c_):
    fig = go.Figure(go.Bar(
        x=df_[x_], y=df_[y_],
        marker=dict(color=df_[c_],
            colorscale=[[0,"#1c2230"],[0.5,"#e88c0e"],[1,"#f0b429"]],
            line=dict(color="rgba(240,180,41,.2)",width=1)),
        hovertemplate="<b>%{x}</b><br>" + y_ + ": %{y}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Sora,sans-serif", color="#8b949e", size=12),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#8b949e",size=11)),
        yaxis=dict(showgrid=True, gridcolor="#1c2230", zeroline=False, tickfont=dict(color="#8b949e",size=11)),
        margin=dict(l=8,r=8,t=16,b=8), height=360,
    )
    return fig


# ══════════════════════════════════════════════════════════════
# OPEN = LOW SCANNER
# ══════════════════════════════════════════════════════════════
if "Open = Low" in scan_mode:
    section_hdr("Open = Low Scanner", "Deteksi pola Open sama dengan Low + kenaikan \u2265 target")
    c1,c2,c3 = st.columns(3)
    with c1: periode  = st.selectbox("Periode Analisis", ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with c2: min_nk   = st.slider("Minimal Kenaikan (%)", 1, 20, 5)
    with c3: lmt      = st.number_input("Limit Hasil", 5, 100, 20)

    section_hdr("Mode Scanning", "Kecepatan vs kelengkapan data")
    ma,mb = st.columns(2)
    with ma:
        mode = st.radio("Kecepatan", ["\u26a1 Cepat (50 saham)", "\U0001f422 Lengkap (Semua)"], index=0, horizontal=True)
    with mb:
        st.markdown(
            "<div style=\"background:rgba(255,255,255,.02);border:1px solid #21262d;border-radius:10px;padding:14px 18px;\">"
            "<div style=\"color:#8b949e;font-size:.76rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;\">Estimasi Waktu</div>"
            "<div style=\"display:flex;gap:24px;\">"
            "<div><div style=\"color:#f0b429;font-size:.84rem;font-family:Space Mono,monospace;\">\u26a1 Cepat</div><div style=\"color:#c9d1d9;font-size:.9rem;margin-top:2px;\">\u00b130 detik</div></div>"
            "<div style=\"width:1px;background:#21262d;margin:0 4px;\"></div>"
            "<div><div style=\"color:#58a6ff;font-size:.84rem;font-family:Space Mono,monospace;\">\U0001f422 Lengkap</div><div style=\"color:#c9d1d9;font-size:.9rem;margin-top:2px;\">\u00b17\u201310 menit</div></div>"
            "</div></div>",
            unsafe_allow_html=True)
    pm = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    st.markdown("<div style=\"height:8px\"></div>", unsafe_allow_html=True)

    if st.button("\U0001f680 MULAI SCANNING", type="primary", use_container_width=True):
        if filter_type=="Pilih Manual" and sel_stocks:       s2s=sel_stocks
        elif filter_type=="Filter Tingkatan" and sel_levels: s2s=by_lvl(sel_levels)
        else: s2s = STOCKS_LIST[:50] if "Cepat" in mode else STOCKS_LIST
        est=len(s2s)*0.5
        if est/60>2: st.warning("Memproses **"+str(len(s2s))+" saham** \u00b7 ~"+str(round(est/60,1))+" menit \u00b7 Jangan refresh")
        else:        st.info(   "Memproses **"+str(len(s2s))+" saham** \u00b7 ~"+str(round(est))+" detik")
        pg=st.progress(0); slot=st.empty(); res=[]; t0=time.time()
        for i,stk in enumerate(s2s):
            el=time.time()-t0; rem=(el/(i+1))*(len(s2s)-i-1) if i>0 else 0
            slot.markdown(html_scan_row(stk,i,len(s2s),el,rem), unsafe_allow_html=True)
            r=scan_open_low_pattern(stk, periode_hari=pm[periode], min_kenaikan=min_nk)
            if r: res.append(r)
            pg.progress((i+1)/len(s2s)); time.sleep(0.3)
        pg.empty(); slot.empty(); tt=time.time()-t0
        if res:
            df=pd.DataFrame(res).sort_values("frekuensi",ascending=False).head(lmt)
            st.markdown(html_scan_done(len(df),tt,periode,min_nk), unsafe_allow_html=True)

            section_hdr("Hasil Scanning","Data free float, FCA, dan tingkatan")
            rows=[]
            for _,row in df.iterrows():
                s=row["saham"]; fv=ff(s); h=hlds(s)
                ti=sum((p["persen"]/fv*100) for p in h if fv>0)
                rows.append({"Saham":s,"Level":lvl(s),"Frek":row["frekuensi"],
                    "Prob":str(round(row["probabilitas"]))+"%","Gain":str(round(row["rata_rata_kenaikan"]))+"%",
                    "FF":str(round(fv))+"%","Inst":str(round(ti))+"%","Ritel":str(round(100-ti))+"%",
                    "FCA":"\u26a0\ufe0f" if fca(s) else "","Pot":pot(fv)})
            edf=pd.DataFrame(rows)
            st.dataframe(edf, use_container_width=True, height=450, hide_index=True)

            section_hdr("Top 10 Saham","Frekuensi pola Open=Low")
            st.plotly_chart(plotly_bar(df.head(10),"saham","frekuensi","probabilitas"), use_container_width=True)

            section_hdr("\U0001f916 Analisis AI","Insight mendalam untuk top 5 saham")
            for _,row in df.head(5).iterrows():
                analysis=analyze_pattern(row.to_dict())
                lbl="**"+row["saham"]+"** \u2014 "+lvl(row["saham"])+" \u00b7 Prob "+str(round(row["probabilitas"],1))+"% \u00b7 Gain "+str(round(row["rata_rata_kenaikan"],1))+"%"
                with st.expander(lbl):
                    c1,c2,c3,c4=st.columns(4)
                    c1.metric("Probabilitas", str(round(row["probabilitas"],1))+"%")
                    c2.metric("Rata Gain",    str(round(row["rata_rata_kenaikan"],1))+"%")
                    c3.metric("Max Gain",     str(round(row["max_kenaikan"],1))+"%")
                    c4.metric("Frekuensi",    str(row["frekuensi"])+"x")
                    st.markdown("<div style=\"color:#c9d1d9;font-size:.87rem;line-height:1.65;padding:12px 0;border-top:1px solid #21262d;margin-top:8px;\">" + analysis + "</div>", unsafe_allow_html=True)
                    st.markdown(html_ff_card(row["saham"]), unsafe_allow_html=True)

            section_hdr("\U0001f4cb Watchlist Generator","Saham prioritas besok")
            wc1,wc2=st.columns(2)
            with wc1: mg=st.slider("Min Gain (%)",3,10,5,key="mg")
            with wc2: tn=st.number_input("Jumlah",5,30,15,key="tn")
            dfw=df[df["rata_rata_kenaikan"]>=mg].copy()
            if not dfw.empty:
                mx_p,mx_g=dfw["probabilitas"].max(),dfw["rata_rata_kenaikan"].max()
                if mx_p>0 and mx_g>0:
                    dfw["skor"]=(dfw["probabilitas"]/mx_p)*50+(dfw["rata_rata_kenaikan"]/mx_g)*50
                    dfw=dfw.nlargest(tn,"skor")
                st.markdown(html_watchlist_top(datetime.now().strftime("%d %B %Y")), unsafe_allow_html=True)
                wl=[]
                for i,(_,row) in enumerate(dfw.iterrows()):
                    rk="\U0001f525 PRIORITAS" if row["probabilitas"]>=20 and row["rata_rata_kenaikan"]>=7 else "\u26a1 LAYAK" if row["probabilitas"]>=15 and row["rata_rata_kenaikan"]>=5 else "\U0001f4cc PANTAU"
                    fv=ff(row["saham"])
                    wl.append({"Rank":i+1,"Saham":row["saham"],"Lvl":lvl_s(row["saham"]),
                        "Prob":str(round(row["probabilitas"]))+"%","Gain":str(round(row["rata_rata_kenaikan"]))+"%",
                        "FF":str(round(fv))+"%","FCA":"\u26a0\ufe0f" if fca(row["saham"]) else "","Pot":pot(fv),"Rekom":rk})
                wdf=pd.DataFrame(wl)
                st.dataframe(wdf, use_container_width=True, hide_index=True, height=340)
                d1,d2=st.columns(2)
                with d1: st.download_button("\u2b07 Export CSV",wdf.to_csv(index=False).encode(),"watchlist_"+datetime.now().strftime("%Y%m%d")+".csv","text/csv",use_container_width=True)
                with d2:
                    xl=export_to_excel(wdf)
                    if xl: st.download_button("\u2b07 Export Excel",xl,"watchlist_"+datetime.now().strftime("%Y%m%d")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
            else:
                st.warning("Tidak ada saham dengan gain minimal " + str(mg) + "%")
            section_hdr("\U0001f4e5 Export Data Scanning")
            e1,e2=st.columns(2)
            with e1: st.download_button("\u2b07 Export CSV",edf.to_csv(index=False).encode(),"scan_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv","text/csv",use_container_width=True)
            with e2:
                xl2=export_to_excel(edf)
                if xl2: st.download_button("\u2b07 Export Excel",xl2,"scan_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        else:
            st.markdown(html_empty("TIDAK ADA SAHAM DITEMUKAN","Coba ubah periode atau turunkan minimal kenaikan"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# LOW FLOAT SCANNER
# ══════════════════════════════════════════════════════════════
elif "Low Float" in scan_mode:
    section_hdr("Low Float Scanner","Deteksi saham free float rendah dan potensi volatilitas tinggi")
    lf1,lf2=st.columns(2)
    with lf1: max_ff=st.slider("Maks Free Float (%)",1,50,20)
    with lf2: min_vol=st.number_input("Min Volume",0,value=0,step=100000)
    section_hdr("Filter Tingkatan")
    fc1,fc2,fc3=st.columns(3)
    with fc1: sb=st.checkbox("\U0001f48e Blue Chip",value=True)
    with fc2: ss=st.checkbox("\U0001f4c8 Second Liner",value=True)
    with fc3: st_=st.checkbox("\U0001f3af Third Liner",value=True)
    scan_lf=st.radio("Mode",[" \u26a1 Cepat","\U0001f422 Lengkap"],horizontal=True,index=0)
    st.markdown("<div style=\"height:8px\"></div>", unsafe_allow_html=True)
    if st.button("\U0001f680 SCAN LOW FLOAT", type="primary", use_container_width=True):
        lv=(["Blue Chip"] if sb else [])+(["Second Liner"] if ss else [])+(["Third Liner"] if st_ else [])
        if sel_stocks:   s2s=sel_stocks
        elif lv:         s2s=by_lvl(lv)
        else: s2s=STOCKS_LIST[:50] if "\u26a1" in scan_lf else STOCKS_LIST
        with st.spinner("Scanning " + str(len(s2s)) + " saham..."):
            res=scan_low_float(s2s,max_ff,min_vol)
        if res:
            df=pd.DataFrame(res)
            st.markdown("".join([
                "<div style=\"background:linear-gradient(135deg,#0d1117,#161b22);border:1px solid rgba(63,185,80,.2);border-radius:16px;padding:28px 32px;margin:20px 0;position:relative;overflow:hidden;\">",
                "<div style=\"position:absolute;top:0;right:0;width:200px;height:100%;background:radial-gradient(ellipse at right,rgba(63,185,80,.08) 0%,transparent 70%);pointer-events:none;\"></div>",
                "<div style=\"display:flex;align-items:center;gap:20px;position:relative;\">",
                "<div style=\"width:52px;height:52px;background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.3);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.65rem;flex-shrink:0;\">\u2705</div>",
                "<div><div style=\"color:#3fb950;font-family:Space Mono,monospace;font-size:.72rem;letter-spacing:2px;text-transform:uppercase;\">LOW FLOAT SCAN SELESAI</div>",
                "<div style=\"color:#f0f6fc;font-size:2rem;font-weight:700;font-family:Space Mono,monospace;margin-top:4px;line-height:1;\">" + str(len(df)) + " <span style=\"font-size:.95rem;color:#8b949e;font-weight:400;\">saham FF &lt; " + str(max_ff) + "%</span></div></div>",
                "</div></div>",
            ]), unsafe_allow_html=True)

            section_hdr("Hasil Scanning","Free float, kategori, komposisi pemegang, dan potensi")
            enr=[]
            for _,row in df.iterrows():
                s=row["saham"]; fv=ff(s); h=hlds(s)
                ti=sum((p["persen"]/fv*100) for p in h if fv>0)
                enr.append({"Saham":s,"Lvl":lvl_s(s),"FF":str(round(fv))+"%","Kat":kat(row["category"]),
                    "Vol(M)":str(round(row["volume_avg"]/1e6,1)),"Volat":str(round(row["volatility"]))+"%",
                    "Inst":str(round(ti))+"%","Ritel":str(round(100-ti))+"%",
                    "FCA":"\u26a0\ufe0f" if fca(s) else "","Pot":pot(fv)})
            enr_df=pd.DataFrame(enr)
            st.dataframe(enr_df, use_container_width=True, height=450, hide_index=True)

            section_hdr("Detail Free Float","Top 5 saham dengan breakdown komposisi pemegang")
            for _,row in df.head(5).iterrows():
                fv=ff(row["saham"])
                with st.expander("**"+row["saham"]+"** \u2014 "+lvl(row["saham"])+" \u00b7 FF "+str(round(fv))+"%"):
                    st.markdown(html_ff_card(row["saham"]), unsafe_allow_html=True)

            section_hdr("Distribusi Visual")
            vc1,vc2=st.columns(2)
            with vc1:
                cv=df["category"].value_counts()
                fig_pie=go.Figure(go.Pie(labels=cv.index,values=cv.values,hole=0.56,
                    marker=dict(colors=["#f0b429","#58a6ff","#3fb950","#ff7b72","#d2a8ff"],line=dict(color="#0a0e17",width=2)),
                    textfont=dict(color="#e6edf3",size=11)))
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Sora",color="#8b949e"),
                    title=dict(text="Kategori Free Float",font=dict(color="#8b949e",size=13),x=0.5),
                    legend=dict(font=dict(color="#8b949e",size=11),bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0,r=0,t=40,b=0),height=300,
                    annotations=[dict(text="FF",x=0.5,y=0.5,font_size=14,showarrow=False,font_color="#484f58")])
                st.plotly_chart(fig_pie, use_container_width=True)
            with vc2:
                fig_sc=go.Figure(go.Scatter(x=df["public_float"],y=df["volatility"],mode="markers",
                    marker=dict(size=[max(6,v/1e6*0.5) for v in df["volume_avg"]],color=df["volatility"],
                        colorscale=[[0,"#1c2230"],[0.5,"#e88c0e"],[1,"#f0b429"]],
                        line=dict(color="rgba(240,180,41,.25)",width=1),sizemode="area",sizeref=2),
                    text=df["saham"],hovertemplate="<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>"))
                fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Sora",color="#8b949e",size=11),
                    title=dict(text="FF vs Volatilitas",font=dict(color="#8b949e",size=13),x=0.5),
                    xaxis=dict(title="Free Float (%)",showgrid=True,gridcolor="#1c2230",zeroline=False),
                    yaxis=dict(title="Volatilitas (%)",showgrid=True,gridcolor="#1c2230",zeroline=False),
                    margin=dict(l=10,r=10,t=40,b=10),height=300)
                st.plotly_chart(fig_sc, use_container_width=True)

            section_hdr("\U0001f4e5 Export Data")
            xe1,xe2=st.columns(2)
            with xe1: st.download_button("\u2b07 Export CSV",enr_df.to_csv(index=False).encode(),"lowfloat_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv","text/csv",use_container_width=True)
            with xe2:
                xl3=export_to_excel(enr_df)
                if xl3: st.download_button("\u2b07 Export Excel",xl3,"lowfloat_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        else:
            st.markdown(html_empty("TIDAK ADA SAHAM LOW FLOAT DITEMUKAN","Coba naikkan batas maksimal free float"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("".join([
    "<div style=\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:8px 0;\">",
    "<div style=\"color:#30363d;font-size:.73rem;font-family:Space Mono,monospace;\">\u26a0 Data edukasi, bukan rekomendasi investasi</div>",
    "<div style=\"display:flex;gap:20px;flex-wrap:wrap;\">",
    "<span style=\"color:#484f58;font-size:.71rem;\">BC=Blue Chip \u00b7 SL=Second Liner \u00b7 TL=Third Liner</span>",
    "<span style=\"color:#484f58;font-size:.71rem;\">FF=Free Float \u00b7 FCA=Full Call Auction</span>",
    "<span style=\"color:#484f58;font-size:.71rem;\">\U0001f525 UT/ST \u00b7 \u26a1 TG \u00b7 \U0001f4ca SD \u00b7 \U0001f4c9 RD</span>",
    "</div></div>",
]), unsafe_allow_html=True)
