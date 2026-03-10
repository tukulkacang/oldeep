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

# ── Stocks ──────────────────────────────────────────────────────────
BLUE_CHIP = [
    'BBCA','BBRI','BMRI','BBNI','BTPS','BRIS','TLKM','ISAT','EXCL','TOWR','MTEL',
    'UNVR','ICBP','INDF','KLBF','GGRM','HMSP','ASII','UNTR','ADRO','BYAN','PTBA',
    'ITMG','CPIN','JPFA','MAIN','SIDO','ULTJ','SMGR','INTP','SMCB','PGAS','MEDC',
    'ELSA','ANTM','INCO','MDKA','HRUM','BRPT','TPIA','WIKA','PTPP','WSKT','ADHI','JSMR',
]
SECOND_LINER = [
    'AKRA','INKP','BUMI','PTRO','DOID','TINS','BRMS','DKFT','BMTR','MAPI','ERAA',
    'ACES','MIKA','SILO','HEAL','PRAY','CLEO','ROTI','MYOR','GOOD','SKBM','SKLT',
    'STTP','WSBP','PBSA','MTFN','BKSL','SMRA','CTRA','BSDE','PWON','LPKR','LPCK',
    'DILD','RDTX','MREI','PZZA','MAPB','DMAS','LMPI','ARNA','TOTO','MLIA','INTD',
    'IKAI','JECC','KBLI','KBLM','VOKS','UNIT','INAI','IMPC','ASGR','POWR','RAJA',
    'PJAA','SAME','SCCO','SPMA','SRSN','TALF','TRST','TSPC','UNIC','YPAS',
]
FCA_STOCKS = ['COIN','CDIA']

SHAREHOLDERS = {
    'BBCA': {
        'pemegang': [
            {'nama':'BPJS Ketenagakerjaan','persen':1.06,'tipe':'Institusi'},
            {'nama':'Vanguard Group','persen':1.23,'tipe':'Asing'},
        ],
        'free_float':95.67,
        'insider':[
            {'tanggal':'10 Mar 2026','insider':'Presdir','aksi':'BELI','jumlah':1000000,'harga':10250},
            {'tanggal':'25 Feb 2026','insider':'Komisaris','aksi':'BELI','jumlah':500000,'harga':10100},
        ]
    },
    'BBRI': {
        'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.09,'tipe':'Institusi'}],
        'free_float':98.91,
        'insider':[{'tanggal':'09 Mar 2026','insider':'Dirut','aksi':'JUAL','jumlah':50000,'harga':5800}]
    },
    'MDKA': {
        'pemegang':[
            {'nama':'BPJS Ketenagakerjaan','persen':2.15,'tipe':'Institusi'},
            {'nama':'Pemerintah Norwegia','persen':1.08,'tipe':'Asing'},
        ],
        'free_float':89.31,
        'insider':[{'tanggal':'15 Feb 2026','insider':'Dirut','aksi':'BELI','jumlah':200000,'harga':2500}]
    },
    'CUAN': {
        'pemegang':[
            {'nama':'BPJS Ketenagakerjaan','persen':1.02,'tipe':'Institusi'},
            {'nama':'Vanguard Group','persen':1.15,'tipe':'Asing'},
        ],
        'free_float':13.73,
        'insider':[
            {'tanggal':'05 Mar 2026','insider':'Direktur Utama','aksi':'BELI','jumlah':100000,'harga':15000},
            {'tanggal':'20 Feb 2026','insider':'Komisaris','aksi':'BELI','jumlah':50000,'harga':14800},
        ]
    },
    'BRPT': {
        'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.22,'tipe':'Institusi'}],
        'free_float':27.41,
        'insider':[{'tanggal':'28 Feb 2026','insider':'Komisaris','aksi':'JUAL','jumlah':75000,'harga':8500}]
    },
    'TPIA': {
        'pemegang':[{'nama':'GIC Singapore','persen':3.45,'tipe':'Asing'}],
        'free_float':91.52,'insider':[]
    },
    'ASII': {
        'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':2.74,'tipe':'Institusi'}],
        'free_float':97.26,'insider':[]
    },
    'KLBF': {
        'pemegang':[
            {'nama':'Pemerintah Norwegia','persen':1.30,'tipe':'Asing'},
            {'nama':'BPJS Ketenagakerjaan','persen':2.01,'tipe':'Institusi'},
        ],
        'free_float':96.69,'insider':[]
    },
    'BYAN': {
        'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.33,'tipe':'Institusi'}],
        'free_float':58.45,'insider':[]
    },
    'ARTO': {
        'pemegang':[{'nama':'Pemerintah Singapura','persen':8.28,'tipe':'Asing'}],
        'free_float':91.72,'insider':[]
    },
    'MTEL': {
        'pemegang':[{'nama':'Pemerintah Singapura','persen':5.33,'tipe':'Asing'}],
        'free_float':94.67,'insider':[]
    },
    'AKRA': {
        'pemegang':[{'nama':'Pemerintah Norwegia','persen':3.03,'tipe':'Asing'}],
        'free_float':96.97,'insider':[]
    },
    'INDF': {
        'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':3.74,'tipe':'Institusi'}],
        'free_float':92.52,'insider':[]
    },
}

# ── Helpers ─────────────────────────────────────────────────────────
def stock_level(c):
    if c in BLUE_CHIP:     return '💎 Blue Chip'
    if c in SECOND_LINER:  return '📈 Second Liner'
    return '🎯 Third Liner'

def level_abbr(c):
    return {'💎 Blue Chip':'BC','📈 Second Liner':'SL','🎯 Third Liner':'TL'}.get(stock_level(c),'')

def stocks_by_level(lvls):
    r = []
    if 'Blue Chip'    in lvls: r += BLUE_CHIP
    if 'Second Liner' in lvls: r += SECOND_LINER
    if 'Third Liner'  in lvls: r += [s for s in STOCKS_LIST if s not in BLUE_CHIP and s not in SECOND_LINER]
    return list(set(r))

def ff_val(c):    return SHAREHOLDERS.get(c,{}).get('free_float',100.0)
def ff_holders(c): return SHAREHOLDERS.get(c,{}).get('pemegang',[])
def insider_tx(c): return SHAREHOLDERS.get(c,{}).get('insider',[])
def is_fca(c):     return c in FCA_STOCKS

def goreng(ff):
    if ff < 10: return '🔥 UT'
    if ff < 15: return '🔥 ST'
    if ff < 25: return '⚡ TG'
    if ff < 40: return '📊 SD'
    return '📉 RD'

def kat_abbr(k):
    return {'Ultra Low Float':'ULF','Very Low Float':'VLF','Low Float':'LF',
            'Moderate Low Float':'MLF','Normal Float':'NF'}.get(k,k)

# ── Free Float Card ──────────────────────────────────────────────────
def ff_card(code):
    ff     = ff_val(code)
    hlds   = ff_holders(code)
    ins    = insider_tx(code)
    fca    = is_fca(code)

    rows = []

    # header
    rows.append(
        '<div style="'
        'background:#0b0f1a;'
        'border:1px solid #1a2236;'
        'border-top:2px solid #c9a84c;'
        'border-radius:12px;'
        'padding:18px 20px;'
        'margin:12px 0;'
        '">'
    )

    # title row
    rows.append(
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        '<span style="font-family:\'JetBrains Mono\',monospace;color:#c9a84c;font-size:.82rem;letter-spacing:2px;">FREE FLOAT — ' + code + '</span>'
    )
    if fca:
        rows.append('<span style="background:rgba(255,165,0,.12);border:1px solid rgba(255,165,0,.3);border-radius:4px;padding:2px 8px;color:#ffa500;font-size:.7rem;">⚠ FCA</span>')
    rows.append('</div>')

    # FF bar
    ff_str = str(round(ff,1)) + '%'
    rows.append(
        '<div style="margin-bottom:14px;">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:5px;">'
        '<span style="color:#4a5568;font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;">Total Free Float</span>'
        '<span style="color:#52d68a;font-family:\'JetBrains Mono\',monospace;font-size:.9rem;font-weight:700;">' + ff_str + '</span>'
        '</div>'
        '<div style="height:4px;background:#111827;border-radius:2px;">'
        '<div style="height:4px;width:' + str(round(min(ff,100))) + '%;background:linear-gradient(90deg,#52d68a,#2ebd6b);border-radius:2px;"></div>'
        '</div>'
        '</div>'
    )

    # holders
    if hlds:
        rows.append('<div style="display:flex;flex-direction:column;gap:6px;margin-bottom:12px;">')
        total_inst = 0.0
        for p in hlds:
            pct = (p['persen'] / ff * 100) if ff > 0 else 0
            total_inst += pct
            clr = '#5b9cf6' if p['tipe'] == 'Institusi' else '#a78bfa'
            dot_clr = '#5b9cf6' if p['tipe'] == 'Institusi' else '#a78bfa'
            pct_s = str(round(pct,1)) + '%'
            bar_w = str(round(min(pct*1.5,100))) + '%'
            rows.append(
                '<div style="background:#111827;border:1px solid #1e2d42;border-radius:8px;padding:8px 12px;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                '<div style="display:flex;align-items:center;gap:7px;">'
                '<div style="width:6px;height:6px;border-radius:50%;background:' + dot_clr + ';flex-shrink:0;"></div>'
                '<span style="color:#94a3b8;font-size:.79rem;">' + p['nama'] + '</span>'
                '<span style="background:#1e2d42;color:#4a5568;font-size:.67rem;padding:1px 6px;border-radius:10px;">' + p['tipe'] + '</span>'
                '</div>'
                '<span style="color:' + clr + ';font-family:\'JetBrains Mono\',monospace;font-size:.82rem;font-weight:600;">' + pct_s + '</span>'
                '</div>'
                '<div style="height:2px;background:#1e2d42;border-radius:1px;">'
                '<div style="height:2px;width:' + bar_w + ';background:' + clr + ';border-radius:1px;opacity:.6;"></div>'
                '</div>'
                '</div>'
            )

        # ritel
        ritel = 100.0 - total_inst
        ritel_s = str(round(ritel,1)) + '%'
        ritel_w = str(round(min(ritel*0.6,100))) + '%'
        rows.append(
            '<div style="background:rgba(82,214,138,.05);border:1px solid rgba(82,214,138,.12);border-radius:8px;padding:8px 12px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            '<div style="display:flex;align-items:center;gap:7px;">'
            '<div style="width:6px;height:6px;border-radius:50%;background:#52d68a;flex-shrink:0;"></div>'
            '<span style="color:#94a3b8;font-size:.79rem;">Ritel</span>'
            '</div>'
            '<span style="color:#52d68a;font-family:\'JetBrains Mono\',monospace;font-size:.82rem;font-weight:600;">' + ritel_s + '</span>'
            '</div>'
            '<div style="height:2px;background:#1e2d42;border-radius:1px;">'
            '<div style="height:2px;width:' + ritel_w + ';background:#52d68a;border-radius:1px;opacity:.6;"></div>'
            '</div>'
            '</div>'
        )
        rows.append('</div>')
    else:
        rows.append(
            '<div style="background:rgba(82,214,138,.05);border:1px solid rgba(82,214,138,.12);'
            'border-radius:8px;padding:10px 12px;margin-bottom:12px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            '<span style="color:#4a5568;font-size:.78rem;">Tidak ada institusi/asing &gt;1%</span>'
            '<span style="color:#52d68a;font-family:\'JetBrains Mono\',monospace;font-size:.82rem;font-weight:600;">Ritel 100%</span>'
            '</div>'
            '</div>'
        )

    # insider
    if ins:
        rows.append('<div style="border-top:1px solid #1a2236;padding-top:10px;margin-top:4px;">')
        rows.append('<p style="color:#4a5568;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px 0;">Insider Activity · 30 Hari</p>')
        for a in ins:
            is_buy = a['aksi'] == 'BELI'
            clr    = '#52d68a' if is_buy else '#f87171'
            bg     = 'rgba(82,214,138,.06)' if is_buy else 'rgba(248,113,113,.06)'
            bd     = 'rgba(82,214,138,.15)' if is_buy else 'rgba(248,113,113,.15)'
            jml    = '{:,}'.format(a['jumlah'])
            rows.append(
                '<div style="display:flex;justify-content:space-between;align-items:center;'
                'background:' + bg + ';border:1px solid ' + bd + ';'
                'border-radius:6px;padding:6px 10px;margin-bottom:4px;">'
                '<span style="color:#4a5568;font-size:.73rem;font-family:\'JetBrains Mono\',monospace;">' + a['tanggal'] + '</span>'
                '<span style="color:#64748b;font-size:.73rem;">' + a['insider'] + '</span>'
                '<span style="color:' + clr + ';font-weight:700;font-size:.76rem;font-family:\'JetBrains Mono\',monospace;">' + a['aksi'] + ' ' + jml + '</span>'
                '</div>'
            )
        rows.append('</div>')

    rows.append('</div>')
    return ''.join(rows)


# ── PAGE CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Radar Aksara",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --gold:    #c9a84c;
    --gold-lt: #e2c97e;
    --gold-dk: #7d5f1a;
    --bg:      #060912;
    --bg2:     #0b0f1a;
    --bg3:     #0f1520;
    --border:  #1a2236;
    --border2: #243048;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --dim:     #2d3a50;
    --green:   #52d68a;
    --red:     #f87171;
    --blue:    #5b9cf6;
    --purple:  #a78bfa;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}
.stApp { background: var(--bg); }
.main .block-container {
    padding: 1.2rem 2rem 3rem;
    max-width: 1400px;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--dim); border-radius: 3px; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown p { color: var(--muted) !important; font-size: .82rem !important; }
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

/* ── radio ── */
.stRadio [data-testid="stWidgetLabel"] {
    color: var(--dim) !important;
    font-size: .68rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[role="radiogroup"] label {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 5px 12px !important;
    color: var(--muted) !important;
    font-size: .81rem !important;
    transition: all .18s !important;
}
div[role="radiogroup"] label:hover {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
    background: rgba(201,168,76,.05) !important;
}

/* ── inputs ── */
.stSelectbox label, .stMultiSelect label,
.stSlider [data-testid="stWidgetLabel"],
.stNumberInput label {
    color: var(--dim) !important;
    font-size: .68rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
.stSelectbox > div > div:hover, .stMultiSelect > div > div:hover {
    border-color: var(--gold-dk) !important;
}
.stSlider .st-be { background: var(--border2) !important; }
.stSlider .st-bf { background: var(--gold) !important; }
.stNumberInput input {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
.stCheckbox label { color: var(--muted) !important; font-size: .83rem !important; }

/* ── PRIMARY button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #c9a84c 0%, #a07828 50%, #c9a84c 100%) !important;
    background-size: 200% !important;
    color: #06090f !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: .82rem !important;
    letter-spacing: 3px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: .7rem 2rem !important;
    box-shadow: 0 0 30px rgba(201,168,76,.2), inset 0 1px 0 rgba(255,255,255,.15) !important;
    transition: all .3s ease !important;
    text-transform: uppercase !important;
    position: relative !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 50px rgba(201,168,76,.4), inset 0 1px 0 rgba(255,255,255,.2) !important;
    transform: translateY(-1px) !important;
}

/* ── secondary button ── */
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 7px !important;
    font-size: .81rem !important;
    transition: all .18s !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--gold-dk) !important;
    color: var(--gold) !important;
}

/* ── metrics ── */
[data-testid="metric-container"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--gold-dk) !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
}
[data-testid="metric-container"] label {
    color: var(--dim) !important;
    font-size: .68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--gold-lt) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.45rem !important;
}

/* ── dataframe ── */
.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── expander ── */
.streamlit-expanderHeader {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-size: .84rem !important;
    transition: all .18s !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--gold-dk) !important;
    color: var(--gold) !important;
}
.streamlit-expanderContent {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── alerts ── */
.stInfo {
    background: rgba(91,156,246,.05) !important;
    border: 1px solid rgba(91,156,246,.15) !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-size: .82rem !important;
}
.stWarning {
    background: rgba(201,168,76,.05) !important;
    border: 1px solid rgba(201,168,76,.18) !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: .82rem !important;
}
.stSuccess {
    background: rgba(82,214,138,.05) !important;
    border: 1px solid rgba(82,214,138,.15) !important;
    border-radius: 8px !important;
}
.stError {
    background: rgba(248,113,113,.05) !important;
    border: 1px solid rgba(248,113,113,.15) !important;
    border-radius: 8px !important;
}

/* ── progress ── */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--gold-dk), var(--gold), var(--gold-lt)) !important;
    border-radius: 2px !important;
}
.stProgress > div { background: var(--border) !important; border-radius: 2px !important; }

/* ── download ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 7px !important;
    color: var(--muted) !important;
    font-size: .81rem !important;
    width: 100% !important;
    transition: all .18s !important;
}
.stDownloadButton > button:hover {
    border-color: var(--green) !important;
    color: var(--green) !important;
    background: rgba(82,214,138,.04) !important;
}

hr { border-color: var(--border) !important; margin: .9rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── HEADER ───────────────────────────────────────────────────────────
def render_header():
    today = datetime.now().strftime('%d %b %Y  %H:%M')
    parts = [
        '<div style="'
        'position:relative;overflow:hidden;'
        'background:#0b0f1a;'
        'border-bottom:1px solid #1a2236;'
        'padding:22px 32px 20px;'
        'margin:-1.2rem -2rem 28px;'
        '">',

        # noise texture strip top
        '<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        'background:linear-gradient(90deg,transparent 0%,#7d5f1a 20%,#c9a84c 50%,#7d5f1a 80%,transparent 100%);"></div>',

        # ambient glow
        '<div style="position:absolute;top:-80px;right:100px;width:400px;height:200px;'
        'background:radial-gradient(ellipse,rgba(201,168,76,.07) 0%,transparent 65%);pointer-events:none;"></div>',

        '<div style="display:flex;align-items:center;gap:20px;position:relative;">',

        # logo mark
        '<div style="flex-shrink:0;width:44px;height:44px;position:relative;">',
        '<div style="position:absolute;inset:0;border:1px solid #c9a84c;border-radius:8px;opacity:.4;transform:rotate(12deg);"></div>',
        '<div style="position:absolute;inset:3px;background:linear-gradient(135deg,#0f1520,#1a2236);border-radius:6px;'
        'display:flex;align-items:center;justify-content:center;'
        'font-family:\'JetBrains Mono\',monospace;color:#c9a84c;font-size:1.1rem;font-weight:700;">◈</div>',
        '</div>',

        # title
        '<div>',
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.5rem;font-weight:700;'
        'letter-spacing:4px;line-height:1;'
        'background:linear-gradient(135deg,#e2c97e 0%,#c9a84c 40%,#a07828 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">'
        'RADAR AKSARA</div>',
        '<div style="color:#2d3a50;font-size:.72rem;letter-spacing:2px;margin-top:5px;font-family:\'JetBrains Mono\',monospace;">'
        'INDONESIAN STOCK SCANNER  ·  IDX</div>',
        '</div>',

        # right side stats
        '<div style="margin-left:auto;display:flex;align-items:center;gap:24px;">',

        '<div style="text-align:right;">',
        '<div style="color:#2d3a50;font-size:.65rem;font-family:\'JetBrains Mono\',monospace;letter-spacing:1px;">MARKET TIME</div>',
        '<div style="color:#c9a84c;font-family:\'JetBrains Mono\',monospace;font-size:.85rem;margin-top:2px;">' + today + ' WIB</div>',
        '</div>',

        '<div style="width:1px;height:28px;background:#1a2236;"></div>',

        '<div style="background:rgba(82,214,138,.08);border:1px solid rgba(82,214,138,.2);'
        'border-radius:5px;padding:5px 12px;display:flex;align-items:center;gap:6px;">'
        '<div style="width:5px;height:5px;border-radius:50%;background:#52d68a;'
        'box-shadow:0 0 6px #52d68a;"></div>'
        '<span style="color:#52d68a;font-family:\'JetBrains Mono\',monospace;font-size:.7rem;letter-spacing:1px;">LIVE</span>'
        '</div>',

        '</div>',
        '</div>',
        '</div>',
    ]
    st.markdown(''.join(parts), unsafe_allow_html=True)

render_header()


# ── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    # brand mark
    st.markdown(
        '<div style="padding:4px 0 16px;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;color:#c9a84c;'
        'font-size:.65rem;letter-spacing:3px;text-transform:uppercase;">◈ Control Panel</div>'
        '</div>',
        unsafe_allow_html=True
    )

    scan_mode = st.radio("Pilih Scanner", ["📈 Open = Low Scanner", "🔍 Low Float Scanner"], index=0)

    st.markdown("---")

    st.markdown(
        '<p style="font-family:\'JetBrains Mono\',monospace;color:#2d3a50 !important;'
        'font-size:.65rem !important;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Filter Saham</p>',
        unsafe_allow_html=True
    )
    filter_type = st.radio("Tipe", ["Semua Saham", "Pilih Manual", "Tingkatan"], index=0)

    selected_stocks = []
    selected_levels = []

    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect("Saham", options=STOCKS_LIST, default=[])
    elif filter_type == "Tingkatan":
        selected_levels = st.multiselect("Tingkatan",
            ["Blue Chip","Second Liner","Third Liner"],
            default=["Blue Chip","Second Liner","Third Liner"])
        if selected_levels:
            cnt = len(stocks_by_level(selected_levels))
            st.info(str(cnt) + " saham · ~" + str(round(cnt*0.5/60,1)) + " menit")

    st.markdown("---")

    # legend
    st.markdown(
        '<p style="font-family:\'JetBrains Mono\',monospace;color:#2d3a50 !important;'
        'font-size:.65rem !important;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;">Legenda</p>',
        unsafe_allow_html=True
    )
    legend = [("💎","Blue Chip","> Rp10T"),("📈","Second Liner","Rp500M–Rp10T"),
              ("🎯","Third Liner","< Rp1T"),("⚠️","FCA","Papan Pemantauan")]
    for ico,lbl,desc in legend:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid #0f1520;">'
            '<span style="font-size:.95rem;flex-shrink:0;">' + ico + '</span>'
            '<div>'
            '<div style="color:#94a3b8;font-size:.78rem;">' + lbl + '</div>'
            '<div style="color:#2d3a50;font-size:.68rem;">' + desc + '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;color:#1a2236;'
        'font-size:.62rem;text-align:center;letter-spacing:1px;padding-top:4px;">'
        'RADAR AKSARA · IDX SCANNER</div>',
        unsafe_allow_html=True
    )


# ── UTILS ────────────────────────────────────────────────────────────
def section(title, sub=''):
    sub_html = (
        '<span style="color:#2d3a50;font-size:.74rem;margin-left:10px;'
        'font-family:\'JetBrains Mono\',monospace;">' + sub + '</span>'
    ) if sub else ''
    st.markdown(
        '<div style="display:flex;align-items:baseline;gap:0;margin:28px 0 14px;">'
        '<span style="color:#c9a84c;font-family:\'JetBrains Mono\',monospace;'
        'font-size:.65rem;letter-spacing:3px;text-transform:uppercase;">'
        + title + '</span>'
        + sub_html +
        '<div style="flex:1;height:1px;background:linear-gradient(90deg,#1a2236,transparent);margin-left:16px;align-self:center;"></div>'
        '</div>',
        unsafe_allow_html=True
    )

def scan_status(stock, i, total, el, rem):
    pct = round((i+1)/total*100)
    return (
        '<div style="background:#0b0f1a;border:1px solid #1a2236;border-radius:8px;padding:10px 16px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        '<span style="font-family:\'JetBrains Mono\',monospace;color:#c9a84c;font-size:.8rem;">'
        '▸ ' + stock + '</span>'
        '<span style="color:#2d3a50;font-size:.73rem;font-family:\'JetBrains Mono\',monospace;">'
        + str(i+1) + ' / ' + str(total) + '  ·  ' + str(round(el)) + 's  ·  ~' + str(round(rem)) + 's left'
        + '</span>'
        '</div>'
        '<div style="height:2px;background:#111827;border-radius:1px;">'
        '<div style="height:2px;width:' + str(pct) + '%;'
        'background:linear-gradient(90deg,#7d5f1a,#c9a84c);border-radius:1px;'
        'transition:width .3s ease;"></div>'
        '</div>'
        '</div>'
    )

def result_banner(count, secs, period, gain):
    return (
        '<div style="'
        'position:relative;overflow:hidden;'
        'background:#0b0f1a;'
        'border:1px solid #1a2236;'
        'border-left:3px solid #c9a84c;'
        'border-radius:10px;'
        'padding:20px 24px;'
        'margin:20px 0;'
        '">'
        '<div style="position:absolute;right:24px;top:50%;transform:translateY(-50%);">'
        '<span style="font-family:\'JetBrains Mono\',monospace;font-size:4rem;font-weight:700;'
        'color:#c9a84c;opacity:.06;line-height:1;">' + str(count) + '</span>'
        '</div>'
        '<div style="display:flex;align-items:center;gap:32px;flex-wrap:wrap;position:relative;">'
        '<div>'
        '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;letter-spacing:2px;text-transform:uppercase;">Saham Ditemukan</div>'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:2.2rem;font-weight:700;'
        'color:#e2c97e;line-height:1.1;margin-top:3px;">' + str(count) + '</div>'
        '</div>'
        '<div style="width:1px;height:40px;background:#1a2236;"></div>'
        '<div>'
        '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;letter-spacing:2px;text-transform:uppercase;">Waktu Proses</div>'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.2rem;color:#94a3b8;margin-top:3px;">' + str(round(secs)) + 's</div>'
        '</div>'
        '<div style="width:1px;height:40px;background:#1a2236;"></div>'
        '<div>'
        '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;letter-spacing:2px;text-transform:uppercase;">Periode</div>'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.2rem;color:#5b9cf6;margin-top:3px;">' + period + '</div>'
        '</div>'
        '<div style="width:1px;height:40px;background:#1a2236;"></div>'
        '<div>'
        '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;letter-spacing:2px;text-transform:uppercase;">Min Gain</div>'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.2rem;color:#52d68a;margin-top:3px;">' + str(gain) + '%</div>'
        '</div>'
        '</div>'
        '</div>'
    )

def empty_state(msg, hint):
    return (
        '<div style="background:#0b0f1a;border:1px solid #1a2236;border-radius:10px;'
        'padding:40px;text-align:center;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;color:#2d3a50;font-size:2rem;margin-bottom:12px;">⊘</div>'
        '<div style="color:#4a5568;font-family:\'JetBrains Mono\',monospace;font-size:.8rem;letter-spacing:1px;">' + msg + '</div>'
        '<div style="color:#2d3a50;font-size:.75rem;margin-top:6px;">' + hint + '</div>'
        '</div>'
    )

def chart_bar(df, x_col, y_col, color_col, title):
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col],
        marker=dict(
            color=df[color_col],
            colorscale=[[0,'#111827'],[0.3,'#1e2d42'],[0.7,'#7d5f1a'],[1,'#c9a84c']],
            line=dict(color='rgba(201,168,76,.15)', width=1),
        ),
        hovertemplate='<b>%{x}</b><br>' + y_col + ': %{y}<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='JetBrains Mono', color='#4a5568', size=11),
        title=dict(text=title, font=dict(color='#2d3a50', size=11, family='JetBrains Mono'), x=0),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#4a5568', size=10)),
        yaxis=dict(showgrid=True, gridcolor='#0f1520', zeroline=False, tickfont=dict(color='#4a5568', size=10)),
        margin=dict(l=4, r=4, t=28, b=4),
        height=340,
    )
    return fig


# ── OPEN = LOW SCANNER ───────────────────────────────────────────────
if "Open = Low" in scan_mode:
    section("Open = Low Scanner", "— deteksi pola Open sama Low + kenaikan ≥ target")

    c1, c2, c3 = st.columns(3)
    with c1: periode    = st.selectbox("Periode", ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with c2: min_nk     = st.slider("Min Kenaikan (%)", 1, 20, 5)
    with c3: lmt        = st.number_input("Limit Hasil", 5, 100, 20)

    section("Mode")
    ma, mb = st.columns(2)
    with ma:
        mode = st.radio("Kecepatan", ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua)"], index=0, horizontal=True)
    with mb:
        st.markdown(
            '<div style="background:#0b0f1a;border:1px solid #1a2236;border-radius:8px;padding:12px 16px;">'
            '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;'
            'letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">Estimasi Durasi</div>'
            '<div style="display:flex;gap:24px;">'
            '<div><div style="color:#c9a84c;font-size:.76rem;font-family:\'JetBrains Mono\',monospace;">⚡ CEPAT</div>'
            '<div style="color:#64748b;font-size:.84rem;margin-top:2px;">~30 detik</div></div>'
            '<div><div style="color:#5b9cf6;font-size:.76rem;font-family:\'JetBrains Mono\',monospace;">🐢 LENGKAP</div>'
            '<div style="color:#64748b;font-size:.84rem;margin-top:2px;">~7–10 menit</div></div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    pm = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    hari = pm[periode]

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("MULAI SCANNING", type="primary", use_container_width=True):
        if filter_type == "Pilih Manual" and selected_stocks:
            s2s = selected_stocks
        elif filter_type == "Tingkatan" and selected_levels:
            s2s = stocks_by_level(selected_levels)
        else:
            s2s = STOCKS_LIST[:50] if "Cepat" in mode else STOCKS_LIST

        est = len(s2s) * 0.5
        if est/60 > 2:
            st.warning("Memproses **" + str(len(s2s)) + " saham** · ~" + str(round(est/60,1)) + " menit · Jangan refresh")
        else:
            st.info("Memproses **" + str(len(s2s)) + " saham** · ~" + str(round(est)) + " detik")

        pg   = st.progress(0)
        slot = st.empty()
        res  = []
        t0   = time.time()

        for i, stk in enumerate(s2s):
            el  = time.time() - t0
            rem = (el/(i+1))*(len(s2s)-i-1) if i > 0 else 0
            slot.markdown(scan_status(stk, i, len(s2s), el, rem), unsafe_allow_html=True)
            r = scan_open_low_pattern(stk, periode_hari=hari, min_kenaikan=min_nk)
            if r: res.append(r)
            pg.progress((i+1)/len(s2s))
            time.sleep(0.3)

        pg.empty(); slot.empty()
        tt = time.time() - t0

        if res:
            df = pd.DataFrame(res).sort_values('frekuensi', ascending=False).head(lmt)

            st.markdown(result_banner(len(df), tt, periode, min_nk), unsafe_allow_html=True)

            # build enhanced table
            section("Hasil Scanning", "— free float · FCA · tingkatan")
            rows = []
            for _, row in df.iterrows():
                s  = row['saham']
                ff = ff_val(s)
                h  = ff_holders(s)
                ti = sum((p['persen']/ff*100) for p in h if ff > 0)
                rows.append({
                    'Saham':  s,
                    'Level':  stock_level(s),
                    'Frek':   row['frekuensi'],
                    'Prob':   str(round(row['probabilitas'])) + '%',
                    'Gain':   str(round(row['rata_rata_kenaikan'])) + '%',
                    'FF':     str(round(ff)) + '%',
                    'Inst':   str(round(ti)) + '%',
                    'Ritel':  str(round(100-ti)) + '%',
                    'FCA':    '⚠' if is_fca(s) else '',
                    'Pot':    goreng(ff),
                })
            edf = pd.DataFrame(rows)
            st.dataframe(edf, use_container_width=True, height=440, hide_index=True)

            # chart
            section("Top 10", "— frekuensi pola Open=Low")
            st.plotly_chart(chart_bar(df.head(10), 'saham', 'frekuensi', 'probabilitas', ''), use_container_width=True)

            # AI
            section("Analisis AI", "— insight top 5 saham")
            for _, row in df.head(5).iterrows():
                analysis = analyze_pattern(row.to_dict())
                label = (
                    "**" + row['saham'] + "**  ·  "
                    + stock_level(row['saham']) + "  ·  "
                    + "Prob " + str(round(row['probabilitas'],1)) + "%  ·  "
                    + "Gain " + str(round(row['rata_rata_kenaikan'],1)) + "%"
                )
                with st.expander(label):
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Probabilitas",  str(round(row['probabilitas'],1))      + "%")
                    c2.metric("Rata Gain",     str(round(row['rata_rata_kenaikan'],1))+ "%")
                    c3.metric("Max Gain",      str(round(row['max_kenaikan'],1))      + "%")
                    c4.metric("Frekuensi",     str(row['frekuensi'])                  + "x")
                    st.markdown(
                        '<div style="color:#64748b;font-size:.84rem;line-height:1.7;'
                        'padding:12px 0;border-top:1px solid #1a2236;margin-top:8px;">'
                        + analysis + '</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(ff_card(row['saham']), unsafe_allow_html=True)

            # watchlist
            section("Watchlist Generator", "— saham prioritas besok")
            wc1, wc2 = st.columns(2)
            with wc1: mg = st.slider("Min Gain (%)", 3, 10, 5, key="mg")
            with wc2: tn = st.number_input("Jumlah", 5, 30, 15, key="tn")

            dfw = df[df['rata_rata_kenaikan'] >= mg].copy()
            if not dfw.empty:
                mx_p, mx_g = dfw['probabilitas'].max(), dfw['rata_rata_kenaikan'].max()
                if mx_p > 0 and mx_g > 0:
                    dfw['skor'] = (dfw['probabilitas']/mx_p)*50 + (dfw['rata_rata_kenaikan']/mx_g)*50
                    dfw = dfw.nlargest(tn, 'skor')

                today_lbl = datetime.now().strftime('%d %B %Y')
                st.markdown(
                    '<div style="background:#0b0f1a;border:1px solid #1a2236;'
                    'border-top:1px solid #c9a84c;'
                    'border-radius:10px;padding:16px 20px;margin:14px 0;">'
                    '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">'
                    '<div>'
                    '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;letter-spacing:2px;text-transform:uppercase;">Watchlist Trading</div>'
                    '<div style="color:#94a3b8;font-size:.95rem;font-weight:500;margin-top:3px;">' + today_lbl + '</div>'
                    '</div>'
                    '<div style="background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);'
                    'border-radius:5px;padding:4px 12px;">'
                    '<span style="color:#c9a84c;font-family:\'JetBrains Mono\',monospace;font-size:.7rem;">◈ Pantau 15 menit pertama</span>'
                    '</div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                wl = []
                for i,(_, row) in enumerate(dfw.iterrows()):
                    rk = ("🔥 PRIORITAS" if row['probabilitas']>=20 and row['rata_rata_kenaikan']>=7
                          else "⚡ LAYAK" if row['probabilitas']>=15 and row['rata_rata_kenaikan']>=5
                          else "📌 PANTAU")
                    ff = ff_val(row['saham'])
                    wl.append({
                        "Rank": i+1, "Saham": row['saham'], "Lvl": level_abbr(row['saham']),
                        "Prob": str(round(row['probabilitas'])) + "%",
                        "Gain": str(round(row['rata_rata_kenaikan'])) + "%",
                        "FF":   str(round(ff)) + "%",
                        "FCA":  '⚠' if is_fca(row['saham']) else '',
                        "Pot":  goreng(ff), "Rekom": rk,
                    })
                wdf = pd.DataFrame(wl)
                st.dataframe(wdf, use_container_width=True, hide_index=True, height=340)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button("⬇ CSV", wdf.to_csv(index=False).encode(),
                        "watchlist_" + datetime.now().strftime('%Y%m%d') + ".csv",
                        "text/csv", use_container_width=True)
                with d2:
                    xl = export_to_excel(wdf)
                    if xl:
                        st.download_button("⬇ Excel", xl,
                            "watchlist_" + datetime.now().strftime('%Y%m%d') + ".xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
            else:
                st.warning("Tidak ada saham dengan gain min " + str(mg) + "%")

            section("Export Hasil Scanning")
            e1, e2 = st.columns(2)
            with e1:
                st.download_button("⬇ CSV", edf.to_csv(index=False).encode(),
                    "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True)
            with e2:
                xl2 = export_to_excel(edf)
                if xl2:
                    st.download_button("⬇ Excel", xl2,
                        "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
        else:
            st.markdown(empty_state("TIDAK ADA SAHAM DITEMUKAN", "Coba ubah periode atau turunkan minimal kenaikan"), unsafe_allow_html=True)


# ── LOW FLOAT SCANNER ────────────────────────────────────────────────
elif "Low Float" in scan_mode:
    section("Low Float Scanner", "— free float rendah + potensi volatilitas tinggi")

    lf1, lf2 = st.columns(2)
    with lf1: max_ff  = st.slider("Maks Free Float (%)", 1, 50, 20)
    with lf2: min_vol = st.number_input("Min Volume", 0, value=0, step=100000)

    section("Filter Tingkatan")
    fc1, fc2, fc3 = st.columns(3)
    with fc1: sb = st.checkbox("💎 Blue Chip",    value=True)
    with fc2: ss = st.checkbox("📈 Second Liner", value=True)
    with fc3: st_cb = st.checkbox("🎯 Third Liner",  value=True)

    scan_lf = st.radio("Mode", ["⚡ Cepat","🐢 Lengkap"], horizontal=True, index=0)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("SCAN LOW FLOAT", type="primary", use_container_width=True):
        lv = (["Blue Chip"] if sb else []) + (["Second Liner"] if ss else []) + (["Third Liner"] if st_cb else [])
        if selected_stocks:  s2s = selected_stocks
        elif lv:             s2s = stocks_by_level(lv)
        else:                s2s = STOCKS_LIST[:50] if scan_lf == "⚡ Cepat" else STOCKS_LIST

        with st.spinner("Scanning " + str(len(s2s)) + " saham..."):
            res = scan_low_float(s2s, max_ff, min_vol)

        if res:
            df = pd.DataFrame(res)

            st.markdown(
                '<div style="background:#0b0f1a;border:1px solid #1a2236;border-left:3px solid #52d68a;'
                'border-radius:10px;padding:20px 24px;margin:18px 0;">'
                '<div style="color:#2d3a50;font-family:\'JetBrains Mono\',monospace;font-size:.62rem;'
                'letter-spacing:2px;text-transform:uppercase;">Low Float Scan Selesai</div>'
                '<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;font-weight:700;'
                'color:#52d68a;margin-top:4px;line-height:1;">'
                + str(len(df)) +
                ' <span style="font-size:.88rem;color:#4a5568;font-weight:400;">saham · FF &lt; '
                + str(max_ff) + '%</span></div>'
                '</div>',
                unsafe_allow_html=True
            )

            section("Hasil Scanning", "— komposisi pemegang & potensi")
            enr = []
            for _, row in df.iterrows():
                s  = row['saham']
                ff = ff_val(s)
                h  = ff_holders(s)
                ti = sum((p['persen']/ff*100) for p in h if ff > 0)
                enr.append({
                    'Saham': s, 'Lvl': level_abbr(s),
                    'FF':    str(round(ff))  + '%',
                    'Kat':   kat_abbr(row['category']),
                    'Vol(M)':str(round(row['volume_avg']/1e6, 1)),
                    'Volat': str(round(row['volatility'])) + '%',
                    'Inst':  str(round(ti))     + '%',
                    'Ritel': str(round(100-ti)) + '%',
                    'FCA':   '⚠' if is_fca(s) else '',
                    'Pot':   goreng(ff),
                })
            enr_df = pd.DataFrame(enr)
            st.dataframe(enr_df, use_container_width=True, height=440, hide_index=True)

            section("Detail Free Float", "— top 5 breakdown pemegang")
            for _, row in df.head(5).iterrows():
                ff = ff_val(row['saham'])
                with st.expander("**" + row['saham'] + "**  ·  " + stock_level(row['saham']) + "  ·  FF " + str(round(ff)) + "%"):
                    st.markdown(ff_card(row['saham']), unsafe_allow_html=True)

            section("Distribusi Visual")
            vc1, vc2 = st.columns(2)
            with vc1:
                cv = df['category'].value_counts()
                fig_pie = go.Figure(go.Pie(
                    labels=cv.index, values=cv.values, hole=0.6,
                    marker=dict(
                        colors=['#c9a84c','#5b9cf6','#52d68a','#f87171','#a78bfa'],
                        line=dict(color='#060912', width=2)
                    ),
                    textfont=dict(color='#94a3b8', size=10),
                ))
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='JetBrains Mono', color='#4a5568'),
                    legend=dict(font=dict(color='#4a5568', size=9), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=0,r=0,t=8,b=0), height=270,
                    annotations=[dict(text='FF', x=0.5, y=0.5, font_size=12,
                                      showarrow=False, font_color='#2d3a50')]
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            with vc2:
                fig_sc = go.Figure(go.Scatter(
                    x=df['public_float'], y=df['volatility'], mode='markers',
                    marker=dict(
                        size=[max(5, v/1e6*0.35) for v in df['volume_avg']],
                        color=df['volatility'],
                        colorscale=[[0,'#111827'],[0.5,'#7d5f1a'],[1,'#c9a84c']],
                        line=dict(color='rgba(201,168,76,.15)', width=1),
                        sizemode='area', sizeref=1.5,
                    ),
                    text=df['saham'],
                    hovertemplate='<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>',
                ))
                fig_sc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='JetBrains Mono', color='#4a5568', size=10),
                    xaxis=dict(title='Free Float (%)', showgrid=True, gridcolor='#0f1520', zeroline=False),
                    yaxis=dict(title='Volatilitas (%)', showgrid=True, gridcolor='#0f1520', zeroline=False),
                    margin=dict(l=8,r=8,t=8,b=8), height=270,
                )
                st.plotly_chart(fig_sc, use_container_width=True)

            section("Export Data")
            xe1, xe2 = st.columns(2)
            with xe1:
                st.download_button("⬇ CSV", enr_df.to_csv(index=False).encode(),
                    "lowfloat_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True)
            with xe2:
                xl3 = export_to_excel(enr_df)
                if xl3:
                    st.download_button("⬇ Excel", xl3,
                        "lowfloat_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
        else:
            st.markdown(empty_state("TIDAK ADA SAHAM DITEMUKAN", "Coba naikkan batas maksimal free float"), unsafe_allow_html=True)


# ── FOOTER ───────────────────────────────────────────────────────────
st.markdown(
    '<div style="'
    'border-top:1px solid #1a2236;'
    'padding:16px 0 8px;'
    'margin-top:32px;'
    'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'

    '<div style="display:flex;align-items:center;gap:8px;">'
    '<span style="font-family:\'JetBrains Mono\',monospace;color:#1a2236;font-size:.65rem;letter-spacing:2px;">◈ RADAR AKSARA</span>'
    '</div>'

    '<div style="display:flex;gap:20px;flex-wrap:wrap;">'
    '<span style="color:#1e2d42;font-size:.67rem;">BC=Blue Chip · SL=Second Liner · TL=Third Liner</span>'
    '<span style="color:#1e2d42;font-size:.67rem;">FF=Free Float · FCA=Full Call Auction</span>'
    '<span style="color:#1e2d42;font-size:.67rem;">⚠ Data edukasi — bukan rekomendasi investasi</span>'
    '</div>'

    '</div>',
    unsafe_allow_html=True
)
