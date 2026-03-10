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

# ─── DATA ────────────────────────────────────────────────────
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
    "BBCA": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.06,"tipe":"Institusi"},{"nama":"Vanguard","persen":1.23,"tipe":"Asing"}],"free_float":95.67,"insider":[{"tanggal":"10 Mar 2026","insider":"Presdir","aksi":"BELI","jumlah":1000000,"harga":10250},{"tanggal":"25 Feb 2026","insider":"Komisaris","aksi":"BELI","jumlah":500000,"harga":10100}]},
    "BBRI": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.09,"tipe":"Institusi"}],"free_float":98.91,"insider":[{"tanggal":"09 Mar 2026","insider":"Dirut","aksi":"JUAL","jumlah":50000,"harga":5800}]},
    "MDKA": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":2.15,"tipe":"Institusi"},{"nama":"Pemerintah Norwegia","persen":1.08,"tipe":"Asing"}],"free_float":89.31,"insider":[{"tanggal":"15 Feb 2026","insider":"Dirut","aksi":"BELI","jumlah":200000,"harga":2500}]},
    "CUAN": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.02,"tipe":"Institusi"},{"nama":"Vanguard","persen":1.15,"tipe":"Asing"}],"free_float":13.73,"insider":[{"tanggal":"05 Mar 2026","insider":"Direktur Utama","aksi":"BELI","jumlah":100000,"harga":15000}]},
    "BRPT": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.22,"tipe":"Institusi"}],"free_float":27.41,"insider":[{"tanggal":"28 Feb 2026","insider":"Komisaris","aksi":"JUAL","jumlah":75000,"harga":8500}]},
    "TPIA": {"pemegang":[{"nama":"GIC Singapore","persen":3.45,"tipe":"Asing"}],"free_float":91.52,"insider":[]},
    "ASII": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":2.74,"tipe":"Institusi"}],"free_float":97.26,"insider":[]},
    "KLBF": {"pemegang":[{"nama":"Pemerintah Norwegia","persen":1.30,"tipe":"Asing"},{"nama":"BPJS Ketenagakerjaan","persen":2.01,"tipe":"Institusi"}],"free_float":96.69,"insider":[]},
    "BYAN": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":1.33,"tipe":"Institusi"}],"free_float":58.45,"insider":[]},
    "ARTO": {"pemegang":[{"nama":"Pemerintah Singapura","persen":8.28,"tipe":"Asing"}],"free_float":91.72,"insider":[]},
    "MTEL": {"pemegang":[{"nama":"Pemerintah Singapura","persen":5.33,"tipe":"Asing"}],"free_float":94.67,"insider":[]},
    "AKRA": {"pemegang":[{"nama":"Pemerintah Norwegia","persen":3.03,"tipe":"Asing"}],"free_float":96.97,"insider":[]},
    "INDF": {"pemegang":[{"nama":"BPJS Ketenagakerjaan","persen":3.74,"tipe":"Institusi"}],"free_float":92.52,"insider":[]},
}

def lvl(c):
    if c in BLUE_CHIP:    return "\U0001f451 Blue Chip"
    if c in SECOND_LINER: return "\u2728 Second Liner"
    return "\u25ce Third Liner"
def lvl_s(c): return {"\U0001f451 Blue Chip":"BC","\u2728 Second Liner":"SL","\u25ce Third Liner":"TL"}.get(lvl(c),"")
def by_lvl(ls):
    r=[]
    if "Blue Chip"    in ls: r+=BLUE_CHIP
    if "Second Liner" in ls: r+=SECOND_LINER
    if "Third Liner"  in ls: r+=[s for s in STOCKS_LIST if s not in BLUE_CHIP and s not in SECOND_LINER]
    return list(set(r))
def ff(c):   return SHAREHOLDERS.get(c,{}).get("free_float",100.0)
def hlds(c): return SHAREHOLDERS.get(c,{}).get("pemegang",[])
def ins(c):  return SHAREHOLDERS.get(c,{}).get("insider",[])
def fca(c):  return c in FCA_STOCKS
def pot(f):
    if f<10: return "\U0001f525 Ultra Tight"
    if f<15: return "\U0001f525 Super Tight"
    if f<25: return "\u26a1 Tight"
    if f<40: return "\U0001f4ca Sedang"
    return "\U0001f4c9 Rendah"
def kat(k):  return {"Ultra Low Float":"ULF","Very Low Float":"VLF","Low Float":"LF","Moderate Low Float":"MLF","Normal Float":"NF"}.get(k,k)

# ─── HTML BUILDERS (list+join only) ─────────────────────────
def C(tag, style, *children):
    return "<" + tag + " style=\"" + style + "\">" + "".join(children) + "</" + tag + ">"

def html_ff_card(code):
    f=ff(code); h=hlds(code); ia=ins(code)
    p=[]
    p.append("<div style=\"background:linear-gradient(160deg,#0a2416 0%,#071810 100%);border:1px solid rgba(16,185,129,.18);border-radius:16px;padding:22px 26px;margin:16px 0;\">")
    # header
    p.append("<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;\">")
    p.append("<div style=\"display:flex;align-items:center;gap:10px;\">")
    p.append("<div style=\"width:3px;height:20px;background:linear-gradient(180deg,#10b981,#059669);border-radius:2px;\"></div>")
    p.append("<span style=\"font-family:'IBM Plex Mono',monospace;font-size:.85rem;color:#6ee7b7;letter-spacing:.08em;\">FREE FLOAT \u2014 " + code + "</span>")
    p.append("</div>")
    if fca(code):
        p.append("<span style=\"background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.35);border-radius:6px;padding:3px 10px;color:#fbbf24;font-size:.72rem;font-family:'IBM Plex Mono',monospace;\">\u26a0 FCA</span>")
    p.append("</div>")
    # total
    p.append("<div style=\"background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:10px;padding:14px 18px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;\">")
    p.append("<span style=\"color:#a7f3d0;font-size:.84rem;\">Total Free Float</span>")
    p.append("<span style=\"color:#10b981;font-weight:700;font-size:1.3rem;font-family:'IBM Plex Mono',monospace;\">" + str(round(f,1)) + "%</span>")
    p.append("</div>")
    # holders
    total_i=0.0
    for h_ in h:
        pct=(h_["persen"]/f*100) if f>0 else 0; total_i+=pct
        warna="#6ee7b7" if h_["tipe"]=="Institusi" else "#93c5fd"
        bw=str(round(min(pct*2,100)))
        p.append("<div style=\"background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:10px 14px;margin:5px 0;\">")
        p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;\">")
        p.append("<div style=\"display:flex;align-items:center;gap:8px;\">")
        p.append("<span style=\"width:7px;height:7px;border-radius:50%;background:" + warna + ";display:inline-block;\"></span>")
        p.append("<span style=\"color:#d1fae5;font-size:.82rem;\">" + h_["nama"] + "</span>")
        p.append("<span style=\"color:#374151;font-size:.71rem;background:rgba(255,255,255,.05);padding:1px 7px;border-radius:8px;\">" + h_["tipe"] + "</span>")
        p.append("</div>")
        p.append("<span style=\"color:" + warna + ";font-weight:700;font-family:'IBM Plex Mono',monospace;font-size:.85rem;\">" + str(round(pct,1)) + "%</span>")
        p.append("</div>")
        p.append("<div style=\"height:2px;background:rgba(255,255,255,.06);border-radius:1px;overflow:hidden;\"><div style=\"width:" + bw + "%;height:2px;background:" + warna + ";border-radius:1px;\"></div></div>")
        p.append("</div>")
    ritel=100.0-total_i; bwr=str(round(min(ritel*.65,100)))
    p.append("<div style=\"background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.15);border-radius:8px;padding:10px 14px;margin:5px 0;\">")
    p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;\">")
    p.append("<div style=\"display:flex;align-items:center;gap:8px;\"><span style=\"width:7px;height:7px;border-radius:50%;background:#10b981;display:inline-block;\"></span><span style=\"color:#d1fae5;font-size:.82rem;\">Ritel &amp; Publik</span></div>")
    p.append("<span style=\"color:#10b981;font-weight:700;font-family:'IBM Plex Mono',monospace;font-size:.85rem;\">" + str(round(ritel,1)) + "%</span>")
    p.append("</div>")
    p.append("<div style=\"height:2px;background:rgba(255,255,255,.06);border-radius:1px;overflow:hidden;\"><div style=\"width:" + bwr + "%;height:2px;background:#10b981;border-radius:1px;\"></div></div>")
    p.append("</div>")
    if not h:
        p.append("<p style=\"color:#374151;font-size:.81rem;margin:4px 0 10px;\">Tidak ada institusi/asing &gt;1%</p>")
    if ia:
        p.append("<div style=\"border-top:1px solid rgba(16,185,129,.12);padding-top:14px;margin-top:16px;\">")
        p.append("<div style=\"color:#374151;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;\">Aktivitas Insider \u00b7 30 Hari</div>")
        for a in ia:
            buy=a["aksi"]=="BELI"; ac="#10b981" if buy else "#f87171"
            ab="rgba(16,185,129,.07)" if buy else "rgba(248,113,113,.07)"
            abd="rgba(16,185,129,.2)" if buy else "rgba(248,113,113,.2)"
            jf="{:,}".format(a["jumlah"])
            p.append("<div style=\"display:flex;justify-content:space-between;align-items:center;background:" + ab + ";border:1px solid " + abd + ";border-radius:8px;padding:8px 13px;margin:4px 0;\">")
            p.append("<span style=\"color:#6b7280;font-size:.78rem;font-family:'IBM Plex Mono',monospace;\">" + a["tanggal"] + "</span>")
            p.append("<span style=\"color:#d1fae5;font-size:.78rem;\">" + a["insider"] + "</span>")
            p.append("<span style=\"color:" + ac + ";font-weight:700;font-size:.8rem;font-family:'IBM Plex Mono',monospace;\">" + a["aksi"] + " " + jf + "</span>")
            p.append("</div>")
        p.append("</div>")
    p.append("</div>")
    return "".join(p)


def html_scan_row(stk, i, total, el, rem):
    pct=str(round((i+1)/total*100))
    return "".join([
        "<div style=\"background:rgba(16,185,129,.04);border:1px solid rgba(16,185,129,.12);border-radius:10px;padding:12px 18px;\">",
        "<div style=\"display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;\">",
        "<div style=\"display:flex;align-items:center;gap:10px;\">",
        "<div style=\"width:6px;height:6px;border-radius:50%;background:#10b981;animation:none;\"></div>",
        "<span style=\"color:#a7f3d0;font-family:'IBM Plex Mono',monospace;font-size:.88rem;\">" + stk + "</span>",
        "</div>",
        "<span style=\"color:#4b5563;font-size:.77rem;font-family:'IBM Plex Mono',monospace;\">" + str(i+1) + "/" + str(total) + " \u00b7 " + str(round(el)) + "s \u00b7 ~" + str(round(rem)) + "s</span>",
        "</div>",
        "<div style=\"height:2px;background:rgba(16,185,129,.12);border-radius:1px;overflow:hidden;\">",
        "<div style=\"width:" + pct + "%;height:2px;background:linear-gradient(90deg,#059669,#10b981,#34d399);border-radius:1px;\"></div>",
        "</div></div>",
    ])


def html_scan_done(count, secs, period, gain):
    return "".join([
        "<div style=\"background:linear-gradient(160deg,#0a2416 0%,#071810 100%);border:1px solid rgba(16,185,129,.25);border-radius:18px;padding:30px 36px;margin:22px 0;position:relative;overflow:hidden;\">",
        "<div style=\"position:absolute;top:-40px;right:-40px;width:220px;height:220px;background:radial-gradient(circle,rgba(16,185,129,.1) 0%,transparent 65%);pointer-events:none;\"></div>",
        "<div style=\"position:absolute;bottom:-20px;left:60px;width:160px;height:160px;background:radial-gradient(circle,rgba(52,211,153,.05) 0%,transparent 70%);pointer-events:none;\"></div>",
        "<div style=\"display:flex;align-items:center;gap:24px;flex-wrap:wrap;position:relative;\">",
        "<div>",
        "<div style=\"font-family:'IBM Plex Mono',monospace;color:#6ee7b7;font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;margin-bottom:8px;\">Scan Berhasil</div>",
        "<div style=\"font-family:'Playfair Display',serif;color:#f5f0e8;font-size:3rem;font-weight:700;line-height:1;\">" + str(count) + "</div>",
        "<div style=\"color:#6b7280;font-size:.83rem;margin-top:4px;\">saham ditemukan</div>",
        "</div>",
        "<div style=\"width:1px;height:60px;background:rgba(16,185,129,.2);align-self:center;\"></div>",
        "<div style=\"display:flex;gap:28px;flex-wrap:wrap;\">",
        "<div><div style=\"font-family:'IBM Plex Mono',monospace;color:#4b5563;font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;\">Periode</div><div style=\"font-family:'IBM Plex Mono',monospace;color:#a7f3d0;font-size:1.1rem;margin-top:5px;\">" + period + "</div></div>",
        "<div><div style=\"font-family:'IBM Plex Mono',monospace;color:#4b5563;font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;\">Min Gain</div><div style=\"font-family:'IBM Plex Mono',monospace;color:#10b981;font-size:1.1rem;margin-top:5px;\">" + str(gain) + "%</div></div>",
        "<div><div style=\"font-family:'IBM Plex Mono',monospace;color:#4b5563;font-size:.65rem;letter-spacing:.1em;text-transform:uppercase;\">Waktu</div><div style=\"font-family:'IBM Plex Mono',monospace;color:#6b7280;font-size:1.1rem;margin-top:5px;\">" + str(round(secs)) + "s</div></div>",
        "</div></div></div>",
    ])


def html_empty(msg, hint):
    return "".join([
        "<div style=\"background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.15);border-radius:14px;padding:40px;text-align:center;\">",
        "<div style=\"font-family:'Playfair Display',serif;color:#fca5a5;font-size:1.1rem;margin-bottom:8px;\">" + msg + "</div>",
        "<div style=\"color:#4b5563;font-size:.81rem;\">" + hint + "</div>",
        "</div>",
    ])


def html_watchlist_header(ds):
    return "".join([
        "<div style=\"background:linear-gradient(160deg,#0a2416,#071810);border:1px solid rgba(16,185,129,.18);border-radius:14px;padding:20px 26px;margin:18px 0;position:relative;overflow:hidden;\">",
        "<div style=\"position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#10b981 40%,#34d399 60%,transparent);\"></div>",
        "<div style=\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;\">",
        "<div>",
        "<div style=\"font-family:'IBM Plex Mono',monospace;color:#6ee7b7;font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;margin-bottom:5px;\">Watchlist Trading</div>",
        "<div style=\"font-family:'Playfair Display',serif;color:#f5f0e8;font-size:1.1rem;\">" + ds + "</div>",
        "</div>",
        "<div style=\"background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);border-radius:20px;padding:6px 16px;color:#6ee7b7;font-size:.79rem;font-family:'IBM Plex Mono',monospace;\">Pantau 15 menit pertama</div>",
        "</div></div>",
    ])


# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(page_title="Radar Aksara", page_icon="\U0001f4ca", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg:      #061a0e;
  --card:    #0a2416;
  --card2:   #0d2e1c;
  --border:  rgba(16,185,129,.15);
  --green:   #10b981;
  --green2:  #059669;
  --green3:  #34d399;
  --mint:    #a7f3d0;
  --cream:   #f5f0e8;
  --muted:   #6b7280;
  --dim:     #374151;
  --red:     #f87171;
  --amber:   #fbbf24;
}

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: var(--bg); }
.main .block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1420px; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--card); }
::-webkit-scrollbar-thumb { background: rgba(16,185,129,.3); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--green); }

/* Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #071810 0%, #061a0e 100%) !important;
  border-right: 1px solid rgba(16,185,129,.12) !important;
}

/* Labels */
.stRadio [data-testid="stWidgetLabel"],
.stSelectbox label, .stMultiSelect label,
.stSlider [data-testid="stWidgetLabel"],
.stNumberInput label {
  color: var(--muted) !important; font-size: .75rem !important;
  font-weight: 500 !important; letter-spacing: .08em !important;
  text-transform: uppercase !important;
  font-family: 'IBM Plex Mono', monospace !important;
}
.stCheckbox label { color: #d1fae5 !important; font-size: .85rem !important; }

/* Radio */
div[role="radiogroup"] label {
  background: rgba(16,185,129,.04) !important;
  border: 1px solid rgba(16,185,129,.14) !important;
  border-radius: 8px !important; padding: 5px 14px !important;
  color: var(--muted) !important; font-size: .83rem !important;
  transition: all .2s !important;
}
div[role="radiogroup"] label:hover {
  border-color: var(--green) !important; color: var(--mint) !important;
  background: rgba(16,185,129,.08) !important;
}

/* Inputs */
.stSelectbox > div > div, .stMultiSelect > div > div {
  background: rgba(16,185,129,.04) !important;
  border: 1px solid rgba(16,185,129,.15) !important;
  border-radius: 8px !important; color: #d1fae5 !important;
}
.stSelectbox > div > div:hover, .stMultiSelect > div > div:hover {
  border-color: var(--green) !important;
}
.stNumberInput input {
  background: rgba(16,185,129,.04) !important;
  border: 1px solid rgba(16,185,129,.15) !important;
  border-radius: 8px !important; color: #d1fae5 !important;
}
.stSlider .st-be { background: rgba(16,185,129,.15) !important; }
.stSlider .st-bf { background: var(--green) !important; }

/* Primary button */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: #022c1a !important; font-family: 'IBM Plex Mono', monospace !important;
  font-weight: 600 !important; font-size: .86rem !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  border: none !important; border-radius: 10px !important;
  padding: .7rem 2rem !important;
  box-shadow: 0 4px 20px rgba(16,185,129,.3) !important;
  transition: all .25s !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 30px rgba(16,185,129,.5) !important;
  transform: translateY(-1px) !important;
}

/* Secondary button */
.stButton > button:not([kind="primary"]) {
  background: rgba(16,185,129,.05) !important; color: #a7f3d0 !important;
  border: 1px solid rgba(16,185,129,.2) !important;
  border-radius: 8px !important; font-size: .84rem !important;
  transition: all .2s !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--green) !important; color: var(--mint) !important;
  background: rgba(16,185,129,.1) !important;
}

/* Metrics */
[data-testid="metric-container"] {
  background: rgba(16,185,129,.05) !important;
  border: 1px solid rgba(16,185,129,.15) !important;
  border-radius: 12px !important; padding: 18px !important;
  transition: all .2s !important;
}
[data-testid="metric-container"]:hover {
  border-color: rgba(16,185,129,.35) !important;
  background: rgba(16,185,129,.08) !important;
}
[data-testid="metric-container"] label {
  color: var(--muted) !important; font-size: .7rem !important;
  text-transform: uppercase !important; letter-spacing: .08em !important;
  font-family: 'IBM Plex Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: #10b981 !important; font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.55rem !important;
}

/* Dataframe */
.stDataFrame { border: 1px solid rgba(16,185,129,.15) !important; border-radius: 12px !important; overflow: hidden !important; }

/* Expander */
.streamlit-expanderHeader {
  background: rgba(16,185,129,.04) !important;
  border: 1px solid rgba(16,185,129,.14) !important;
  border-radius: 10px !important; color: #d1fae5 !important;
  font-size: .87rem !important; transition: all .2s !important;
}
.streamlit-expanderHeader:hover {
  border-color: var(--green) !important; color: var(--mint) !important;
  background: rgba(16,185,129,.08) !important;
}
.streamlit-expanderContent {
  background: rgba(6,26,14,.9) !important;
  border: 1px solid rgba(16,185,129,.12) !important;
  border-top: none !important; border-radius: 0 0 10px 10px !important;
}

/* Alerts */
.stInfo    { background: rgba(16,185,129,.05) !important; border: 1px solid rgba(16,185,129,.2) !important; border-radius: 8px !important; color: #a7f3d0 !important; font-size: .83rem !important; }
.stWarning { background: rgba(245,158,11,.05) !important; border: 1px solid rgba(245,158,11,.2) !important; border-radius: 8px !important; color: #fde68a !important; font-size: .83rem !important; }
.stSuccess { background: rgba(16,185,129,.07) !important; border: 1px solid rgba(16,185,129,.25) !important; border-radius: 8px !important; }
.stError   { background: rgba(248,113,113,.05) !important; border: 1px solid rgba(248,113,113,.2) !important; border-radius: 8px !important; }

/* Progress bar */
.stProgress > div > div { background: linear-gradient(90deg, #059669, #10b981, #34d399) !important; border-radius: 2px !important; }
.stProgress > div       { background: rgba(16,185,129,.1) !important; border-radius: 2px !important; }

/* Download */
.stDownloadButton > button {
  background: rgba(16,185,129,.05) !important;
  border: 1px solid rgba(16,185,129,.2) !important;
  border-radius: 8px !important; color: #a7f3d0 !important;
  font-size: .84rem !important; width: 100% !important; transition: all .2s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--green) !important; color: var(--mint) !important;
  background: rgba(16,185,129,.1) !important;
}

hr { border-color: rgba(16,185,129,.12) !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─── HEADER ──────────────────────────────────────────────────
now = datetime.now()
st.markdown("".join([
    "<div style=\"background:linear-gradient(160deg,#0a2416 0%,#071810 100%);border:1px solid rgba(16,185,129,.2);border-radius:18px;padding:32px 38px;margin-bottom:28px;position:relative;overflow:hidden;\">",
    # atmospheric glows
    "<div style=\"position:absolute;top:-60px;right:-60px;width:320px;height:320px;background:radial-gradient(circle,rgba(16,185,129,.12) 0%,transparent 60%);pointer-events:none;\"></div>",
    "<div style=\"position:absolute;bottom:-40px;left:80px;width:240px;height:240px;background:radial-gradient(circle,rgba(52,211,153,.06) 0%,transparent 65%);pointer-events:none;\"></div>",
    # top shimmer line
    "<div style=\"position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#10b981 30%,#34d399 60%,transparent);\"></div>",
    "<div style=\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px;position:relative;\">",
    # left: title
    "<div>",
    "<div style=\"font-family:'IBM Plex Mono',monospace;font-size:.68rem;letter-spacing:.2em;color:#374151;text-transform:uppercase;margin-bottom:10px;\">IDX / Stock Screener</div>",
    "<div style=\"font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:700;color:#f5f0e8;line-height:1;letter-spacing:-.01em;\">Radar <span style=\"color:#10b981;font-style:italic;\">Aksara</span></div>",
    "<div style=\"font-family:'IBM Plex Sans',sans-serif;color:#4b5563;font-size:.81rem;margin-top:8px;letter-spacing:.02em;\">Open=Low Pattern &nbsp;\u00b7&nbsp; Low Float Scanner &nbsp;\u00b7&nbsp; IDX Market Intelligence</div>",
    "</div>",
    # right: live badge + date
    "<div style=\"display:flex;flex-direction:column;align-items:flex-end;gap:8px;\">",
    "<div style=\"display:flex;align-items:center;gap:8px;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);border-radius:20px;padding:6px 16px;\">",
    "<span style=\"width:6px;height:6px;border-radius:50%;background:#10b981;display:inline-block;\"></span>",
    "<span style=\"color:#6ee7b7;font-family:'IBM Plex Mono',monospace;font-size:.75rem;letter-spacing:.08em;\">LIVE</span>",
    "</div>",
    "<div style=\"font-family:'IBM Plex Mono',monospace;color:#374151;font-size:.73rem;\">" + now.strftime("%d %b %Y \u00b7 %H:%M") + " WIB</div>",
    "</div>",
    "</div></div>",
]), unsafe_allow_html=True)


# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style=\"background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.15);border-radius:10px;padding:12px 16px;margin-bottom:18px;\">"
        "<div style=\"font-family:'IBM Plex Mono',monospace;color:#6ee7b7;font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;\">Control Panel</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    scan_mode = st.radio("Mode Scanning", ["\U0001f4c8 Open = Low Scanner", "\U0001f50d Low Float Scanner"], index=0)
    st.markdown("---")
    filter_type = st.radio("Filter Saham", ["Semua Saham", "Pilih Manual", "Filter Tingkatan"], index=0)
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
    st.markdown("<div style=\"color:#374151;font-family:'IBM Plex Mono',monospace;font-size:.67rem;letter-spacing:.1em;margin-bottom:10px;\">LEGENDA</div>", unsafe_allow_html=True)
    for ic,lb,ds in [("\U0001f451","Blue Chip","> Rp10T"),("\u2728","Second Liner","Rp500M\u2013Rp10T"),("\u25ce","Third Liner","< Rp1T"),("\u26a0\ufe0f","FCA","Papan Pemantauan")]:
        st.markdown(
            "<div style=\"display:flex;align-items:center;gap:9px;padding:5px 0;border-bottom:1px solid rgba(16,185,129,.08);\">"
            "<span style=\"font-size:.9rem;\">" + ic + "</span>"
            "<div><div style=\"color:#d1fae5;font-size:.8rem;\">" + lb + "</div><div style=\"color:#374151;font-size:.7rem;\">" + ds + "</div></div>"
            "</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style=\"text-align:center;color:#1f3a2c;font-size:.68rem;font-family:'IBM Plex Mono',monospace;\">RADAR AKSARA \u00b7 IDX</div>", unsafe_allow_html=True)


# ─── HELPERS ─────────────────────────────────────────────────
def sec_hdr(title, sub=""):
    sub_html = ("<div style=\"color:#4b5563;font-size:.77rem;margin-top:3px;\">" + sub + "</div>") if sub else ""
    st.markdown(
        "<div style=\"display:flex;align-items:center;gap:12px;margin:28px 0 16px;\">"
        "<div style=\"width:2px;height:20px;background:linear-gradient(180deg,#10b981,#059669);border-radius:1px;\"></div>"
        "<div><div style=\"font-family:'Playfair Display',serif;color:#f5f0e8;font-size:1.05rem;font-weight:600;\">" + title + "</div>" + sub_html + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def plotly_bar(df_, x_, y_, c_):
    fig = go.Figure(go.Bar(
        x=df_[x_], y=df_[y_],
        marker=dict(
            color=df_[c_],
            colorscale=[[0,"#071810"],[0.4,"#064e3b"],[0.7,"#059669"],[1,"#10b981"]],
            line=dict(color="rgba(16,185,129,.2)", width=1),
        ),
        hovertemplate="<b>%{x}</b><br>" + y_ + ": %{y}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono, monospace", color="#4b5563", size=11),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#6b7280",size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(16,185,129,.08)", zeroline=False, tickfont=dict(color="#6b7280",size=10)),
        margin=dict(l=8,r=8,t=16,b=8), height=360,
    )
    return fig


# ─── OPEN = LOW ───────────────────────────────────────────────
if "Open = Low" in scan_mode:
    sec_hdr("Open = Low Scanner", "Deteksi pola Open sama dengan Low \u00b7 kenaikan \u2265 target")
    c1,c2,c3 = st.columns(3)
    with c1: periode = st.selectbox("Periode", ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with c2: min_nk  = st.slider("Min Kenaikan (%)", 1, 20, 5)
    with c3: lmt     = st.number_input("Limit Hasil", 5, 100, 20)

    sec_hdr("Mode Scanning")
    ma,mb = st.columns(2)
    with ma:
        mode = st.radio("Kecepatan", ["\u26a1 Cepat (50 saham)", "\U0001f422 Lengkap (Semua)"], index=0, horizontal=True)
    with mb:
        st.markdown(
            "<div style=\"background:rgba(16,185,129,.04);border:1px solid rgba(16,185,129,.12);border-radius:10px;padding:14px 18px;\">"
            "<div style=\"font-family:'IBM Plex Mono',monospace;color:#4b5563;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px;\">Estimasi Waktu</div>"
            "<div style=\"display:flex;gap:24px;\">"
            "<div><div style=\"color:#6ee7b7;font-size:.83rem;font-family:'IBM Plex Mono',monospace;\">\u26a1 Cepat</div><div style=\"color:#a7f3d0;font-size:.9rem;margin-top:2px;\">\u00b130 detik</div></div>"
            "<div style=\"width:1px;background:rgba(16,185,129,.12);\"></div>"
            "<div><div style=\"color:#6b7280;font-size:.83rem;font-family:'IBM Plex Mono',monospace;\">\U0001f422 Lengkap</div><div style=\"color:#6b7280;font-size:.9rem;margin-top:2px;\">\u00b17\u201310 menit</div></div>"
            "</div></div>",
            unsafe_allow_html=True)

    pm = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("\u25b6 MULAI SCANNING", type="primary", use_container_width=True):
        if filter_type=="Pilih Manual" and sel_stocks:       s2s=sel_stocks
        elif filter_type=="Filter Tingkatan" and sel_levels: s2s=by_lvl(sel_levels)
        else: s2s=STOCKS_LIST[:50] if "Cepat" in mode else STOCKS_LIST
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
            sec_hdr("Hasil Scanning", "Free float, FCA, dan tingkatan saham")
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
            sec_hdr("Top 10 Saham", "Frekuensi pola Open=Low")
            st.plotly_chart(plotly_bar(df.head(10),"saham","frekuensi","probabilitas"), use_container_width=True)
            sec_hdr("Analisis AI", "Insight mendalam untuk top 5 saham")
            for _,row in df.head(5).iterrows():
                analysis=analyze_pattern(row.to_dict())
                lbl="**"+row["saham"]+"** \u2014 "+lvl(row["saham"])+" \u00b7 Prob "+str(round(row["probabilitas"],1))+"% \u00b7 Gain "+str(round(row["rata_rata_kenaikan"],1))+"%"
                with st.expander(lbl):
                    c1,c2,c3,c4=st.columns(4)
                    c1.metric("Probabilitas", str(round(row["probabilitas"],1))+"%")
                    c2.metric("Rata Gain",    str(round(row["rata_rata_kenaikan"],1))+"%")
                    c3.metric("Max Gain",     str(round(row["max_kenaikan"],1))+"%")
                    c4.metric("Frekuensi",    str(row["frekuensi"])+"x")
                    st.markdown("<div style=\"color:#a7f3d0;font-size:.86rem;line-height:1.7;padding:12px 0;border-top:1px solid rgba(16,185,129,.1);margin-top:8px;\">" + analysis + "</div>", unsafe_allow_html=True)
                    st.markdown(html_ff_card(row["saham"]), unsafe_allow_html=True)
            sec_hdr("Watchlist Generator", "Saham prioritas untuk dipantau besok")
            wc1,wc2=st.columns(2)
            with wc1: mg=st.slider("Min Gain (%)",3,10,5,key="mg")
            with wc2: tn=st.number_input("Jumlah",5,30,15,key="tn")
            dfw=df[df["rata_rata_kenaikan"]>=mg].copy()
            if not dfw.empty:
                mx_p,mx_g=dfw["probabilitas"].max(),dfw["rata_rata_kenaikan"].max()
                if mx_p>0 and mx_g>0:
                    dfw["skor"]=(dfw["probabilitas"]/mx_p)*50+(dfw["rata_rata_kenaikan"]/mx_g)*50
                    dfw=dfw.nlargest(tn,"skor")
                st.markdown(html_watchlist_header(datetime.now().strftime("%d %B %Y")), unsafe_allow_html=True)
                wl=[]
                for i,(_,row) in enumerate(dfw.iterrows()):
                    rk="\U0001f525 PRIORITAS" if row["probabilitas"]>=20 and row["rata_rata_kenaikan"]>=7 else "\u26a1 LAYAK" if row["probabilitas"]>=15 and row["rata_rata_kenaikan"]>=5 else "\u25ce PANTAU"
                    fv=ff(row["saham"])
                    wl.append({"Rank":i+1,"Saham":row["saham"],"Lvl":lvl_s(row["saham"]),
                        "Prob":str(round(row["probabilitas"]))+"%","Gain":str(round(row["rata_rata_kenaikan"]))+"%",
                        "FF":str(round(fv))+"%","FCA":"\u26a0\ufe0f" if fca(row["saham"]) else "","Pot":pot(fv),"Rekom":rk})
                wdf=pd.DataFrame(wl)
                st.dataframe(wdf, use_container_width=True, hide_index=True, height=340)
                d1,d2=st.columns(2)
                with d1: st.download_button("\u2193 Export CSV",wdf.to_csv(index=False).encode(),"watchlist_"+datetime.now().strftime("%Y%m%d")+".csv","text/csv",use_container_width=True)
                with d2:
                    xl=export_to_excel(wdf)
                    if xl: st.download_button("\u2193 Export Excel",xl,"watchlist_"+datetime.now().strftime("%Y%m%d")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
            else:
                st.warning("Tidak ada saham dengan gain minimal " + str(mg) + "%")
            sec_hdr("Export Data Scanning")
            e1,e2=st.columns(2)
            with e1: st.download_button("\u2193 Export CSV",edf.to_csv(index=False).encode(),"scan_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv","text/csv",use_container_width=True)
            with e2:
                xl2=export_to_excel(edf)
                if xl2: st.download_button("\u2193 Export Excel",xl2,"scan_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        else:
            st.markdown(html_empty("Tidak ada saham yang memenuhi kriteria","Coba ubah periode atau kurangi minimal kenaikan"), unsafe_allow_html=True)


# ─── LOW FLOAT ───────────────────────────────────────────────
elif "Low Float" in scan_mode:
    sec_hdr("Low Float Scanner", "Deteksi saham free float rendah dan potensi volatilitas tinggi")
    lf1,lf2=st.columns(2)
    with lf1: max_ff=st.slider("Maks Free Float (%)",1,50,20)
    with lf2: min_vol=st.number_input("Min Volume",0,value=0,step=100000)
    sec_hdr("Filter Tingkatan")
    fc1,fc2,fc3=st.columns(3)
    with fc1: sb=st.checkbox("\U0001f451 Blue Chip",value=True)
    with fc2: ss=st.checkbox("\u2728 Second Liner",value=True)
    with fc3: st_=st.checkbox("\u25ce Third Liner",value=True)
    scan_lf=st.radio("Mode",["\u26a1 Cepat","\U0001f422 Lengkap"],horizontal=True,index=0)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("\u25b6 SCAN LOW FLOAT", type="primary", use_container_width=True):
        lv=(["Blue Chip"] if sb else [])+(["Second Liner"] if ss else [])+(["Third Liner"] if st_ else [])
        if sel_stocks:   s2s=sel_stocks
        elif lv:         s2s=by_lvl(lv)
        else: s2s=STOCKS_LIST[:50] if "Cepat" in scan_lf else STOCKS_LIST
        with st.spinner("Scanning " + str(len(s2s)) + " saham..."):
            res=scan_low_float(s2s,max_ff,min_vol)
        if res:
            df=pd.DataFrame(res)
            st.markdown("".join([
                "<div style=\"background:linear-gradient(160deg,#0a2416,#071810);border:1px solid rgba(16,185,129,.22);border-radius:16px;padding:28px 32px;margin:22px 0;position:relative;overflow:hidden;\">",
                "<div style=\"position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,#10b981 40%,#34d399 60%,transparent);\"></div>",
                "<div style=\"display:flex;align-items:center;gap:20px;\">",
                "<div>",
                "<div style=\"font-family:'IBM Plex Mono',monospace;color:#6ee7b7;font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;margin-bottom:6px;\">Scan Selesai</div>",
                "<div style=\"font-family:'Playfair Display',serif;color:#f5f0e8;font-size:2.8rem;font-weight:700;line-height:1;\">" + str(len(df)) + "</div>",
                "<div style=\"color:#6b7280;font-size:.82rem;margin-top:4px;\">saham FF &lt; " + str(max_ff) + "%</div>",
                "</div></div></div>",
            ]), unsafe_allow_html=True)
            sec_hdr("Hasil Scanning","Free float, kategori, komposisi pemegang, dan potensi")
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
            sec_hdr("Detail Free Float","Top 5 saham dengan breakdown komposisi pemegang")
            for _,row in df.head(5).iterrows():
                fv=ff(row["saham"])
                with st.expander("**"+row["saham"]+"** \u2014 "+lvl(row["saham"])+" \u00b7 FF "+str(round(fv))+"%"):
                    st.markdown(html_ff_card(row["saham"]), unsafe_allow_html=True)
            sec_hdr("Distribusi Visual")
            vc1,vc2=st.columns(2)
            with vc1:
                cv=df["category"].value_counts()
                fig_pie=go.Figure(go.Pie(labels=cv.index,values=cv.values,hole=0.58,
                    marker=dict(colors=["#10b981","#34d399","#6ee7b7","#a7f3d0","#d1fae5"],line=dict(color="#061a0e",width=2)),
                    textfont=dict(color="#f5f0e8",size=11)))
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="IBM Plex Mono",color="#6b7280"),
                    title=dict(text="Kategori Free Float",font=dict(color="#4b5563",size=13),x=0.5),
                    legend=dict(font=dict(color="#6b7280",size=10),bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0,r=0,t=40,b=0),height=300,
                    annotations=[dict(text="FF",x=0.5,y=0.5,font_size=13,showarrow=False,font_color="#374151")])
                st.plotly_chart(fig_pie, use_container_width=True)
            with vc2:
                fig_sc=go.Figure(go.Scatter(x=df["public_float"],y=df["volatility"],mode="markers",
                    marker=dict(size=[max(6,v/1e6*0.5) for v in df["volume_avg"]],color=df["volatility"],
                        colorscale=[[0,"#071810"],[0.5,"#059669"],[1,"#10b981"]],
                        line=dict(color="rgba(16,185,129,.2)",width=1),sizemode="area",sizeref=2),
                    text=df["saham"],hovertemplate="<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>"))
                fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="IBM Plex Mono",color="#6b7280",size=10),
                    title=dict(text="FF vs Volatilitas",font=dict(color="#4b5563",size=13),x=0.5),
                    xaxis=dict(title="Free Float (%)",showgrid=True,gridcolor="rgba(16,185,129,.07)",zeroline=False),
                    yaxis=dict(title="Volatilitas (%)",showgrid=True,gridcolor="rgba(16,185,129,.07)",zeroline=False),
                    margin=dict(l=10,r=10,t=40,b=10),height=300)
                st.plotly_chart(fig_sc, use_container_width=True)
            sec_hdr("Export Data")
            xe1,xe2=st.columns(2)
            with xe1: st.download_button("\u2193 Export CSV",enr_df.to_csv(index=False).encode(),"lowfloat_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv","text/csv",use_container_width=True)
            with xe2:
                xl3=export_to_excel(enr_df)
                if xl3: st.download_button("\u2193 Export Excel",xl3,"lowfloat_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        else:
            st.markdown(html_empty("Tidak ada saham yang memenuhi kriteria","Coba naikkan batas maksimal free float"), unsafe_allow_html=True)


# ─── FOOTER ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("".join([
    "<div style=\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:6px 0;\">",
    "<div style=\"font-family:'IBM Plex Mono',monospace;color:#1f3a2c;font-size:.71rem;\">\u26a0 Data edukasi \u00b7 bukan rekomendasi investasi</div>",
    "<div style=\"display:flex;gap:20px;flex-wrap:wrap;\">",
    "<span style=\"color:#1f3a2c;font-size:.7rem;\">BC=Blue Chip \u00b7 SL=Second Liner \u00b7 TL=Third Liner</span>",
    "<span style=\"color:#1f3a2c;font-size:.7rem;\">FF=Free Float \u00b7 FCA=Full Call Auction</span>",
    "</div></div>",
]), unsafe_allow_html=True)
