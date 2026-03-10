import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import random

# Import modules kita
from data.stocks_list import STOCKS_LIST, get_sector
from modules.data_fetcher import get_stock_data, get_current_price, get_fundamental_data
from modules.open_low_scanner import scan_open_low_pattern, get_pattern_summary
from modules.low_float_scanner import scan_low_float, get_low_float_summary
from modules.ai_analyzer import analyze_pattern, analyze_low_float, predict_next_pattern, get_market_context
from utils.exporters import export_to_excel, format_number

# ===================================================================
#  DATA TINGKATAN SAHAM
# ===================================================================
BLUE_CHIP_STOCKS = [
    'BBCA','BBRI','BMRI','BBNI','BTPS','BRIS',
    'TLKM','ISAT','EXCL','TOWR','MTEL',
    'UNVR','ICBP','INDF','KLBF','GGRM','HMSP',
    'ASII','UNTR','ADRO','BYAN','PTBA','ITMG',
    'CPIN','JPFA','MAIN','SIDO','ULTJ',
    'SMGR','INTP','SMCB',
    'PGAS','MEDC','ELSA',
    'ANTM','INCO','MDKA','HRUM','BRPT','TPIA',
    'WIKA','PTPP','WSKT','ADHI','JSMR',
]

SECOND_LINER_STOCKS = [
    'AKRA','INKP','BUMI','PTRO','DOID','TINS','BRMS','DKFT',
    'BMTR','MAPI','ERAA','ACES','MIKA','SILO','HEAL','PRAY',
    'CLEO','ROTI','MYOR','GOOD','SKBM','SKLT','STTP',
    'WSBP','PBSA','MTFN','BKSL','SMRA','CTRA','BSDE','PWON',
    'LPKR','LPCK','DILD','RDTX','MREI','PZZA','MAPB','DMAS',
    'LMPI','ARNA','TOTO','MLIA','INTD','IKAI','JECC','KBLI',
    'KBLM','VOKS','UNIT','INAI','IMPC','ASGR','POWR','RAJA',
    'PJAA','SAME','SCCO','SPMA','SRSN','TALF','TRST','TSPC',
    'UNIC','YPAS',
]

FCA_STOCKS = ['COIN', 'CDIA']

SHAREHOLDER_DATA = {
    'CUAN': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.02, 'tipe': 'Institusi', 'catatan': 'Masuk Q4 2025'},
            {'nama': 'Vanguard', 'persen': 1.15, 'tipe': 'Asing', 'catatan': 'Nambah Jan 2026'},
        ],
        'free_float': 13.73, 'total_shares': 12345678900,
        'insider_activity': [
            {'tanggal': '05 Mar 2026', 'insider': 'Direktur Utama', 'aksi': 'BELI', 'jumlah': 100000, 'harga': 15000},
            {'tanggal': '20 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 50000, 'harga': 14800},
        ]
    },
    'BRPT': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.22, 'tipe': 'Institusi', 'catatan': 'Nambah Feb 2026'}],
        'free_float': 27.41, 'total_shares': 8765432100,
        'insider_activity': [{'tanggal': '28 Feb 2026', 'insider': 'Komisaris', 'aksi': 'JUAL', 'jumlah': 75000, 'harga': 8500}]
    },
    'TPIA': {
        'pemegang': [{'nama': 'GIC Singapore', 'persen': 3.45, 'tipe': 'Asing', 'catatan': 'Masuk Jan 2026'}],
        'free_float': 91.52, 'total_shares': 1122334455, 'insider_activity': []
    },
    'BBCA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.06, 'tipe': 'Institusi', 'catatan': 'Nambah'},
            {'nama': 'Vanguard', 'persen': 1.23, 'tipe': 'Asing', 'catatan': 'Nambah'},
        ],
        'free_float': 95.67, 'total_shares': 123456789000,
        'insider_activity': [
            {'tanggal': '10 Mar 2026', 'insider': 'Presdir', 'aksi': 'BELI', 'jumlah': 1000000, 'harga': 10250},
            {'tanggal': '25 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 500000, 'harga': 10100},
        ]
    },
    'BBRI': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.09, 'tipe': 'Institusi', 'catatan': 'Nambah'}],
        'free_float': 98.91, 'total_shares': 123456789000,
        'insider_activity': [{'tanggal': '09 Mar 2026', 'insider': 'Dirut', 'aksi': 'JUAL', 'jumlah': 50000, 'harga': 5800}]
    },
    'MDKA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah'},
            {'nama': 'Pemerintah Norwegia', 'persen': 1.08, 'tipe': 'Asing', 'catatan': 'Masuk Q1 2026'},
        ],
        'free_float': 89.31, 'total_shares': 8877665544,
        'insider_activity': [{'tanggal': '15 Feb 2026', 'insider': 'Dirut', 'aksi': 'BELI', 'jumlah': 200000, 'harga': 2500}]
    },
    'INDF': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 3.74, 'tipe': 'Institusi', 'catatan': 'Nambah'}],
        'free_float': 92.52, 'total_shares': 8765432100, 'insider_activity': []
    },
    'ASII': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 2.74, 'tipe': 'Institusi', 'catatan': 'Nambah'}],
        'free_float': 97.26, 'total_shares': 9988776655, 'insider_activity': []
    },
    'KLBF': {
        'pemegang': [
            {'nama': 'Pemerintah Norwegia', 'persen': 1.30, 'tipe': 'Asing', 'catatan': 'Nambah'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.01, 'tipe': 'Institusi', 'catatan': 'Nambah'},
        ],
        'free_float': 96.69, 'total_shares': 5566778899, 'insider_activity': []
    },
    'ARTO': {
        'pemegang': [{'nama': 'Pemerintah Singapura', 'persen': 8.28, 'tipe': 'Asing', 'catatan': 'Masuk besar'}],
        'free_float': 91.72, 'total_shares': 1122334455, 'insider_activity': []
    },
    'MTEL': {
        'pemegang': [{'nama': 'Pemerintah Singapura', 'persen': 5.33, 'tipe': 'Asing', 'catatan': 'Nambah'}],
        'free_float': 94.67, 'total_shares': 2233445566, 'insider_activity': []
    },
    'BYAN': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.33, 'tipe': 'Institusi', 'catatan': 'Nambah'}],
        'free_float': 58.45, 'total_shares': 10000000000, 'insider_activity': []
    },
    'AKRA': {
        'pemegang': [{'nama': 'Pemerintah Norwegia', 'persen': 3.03, 'tipe': 'Asing', 'catatan': 'Aktif nambah'}],
        'free_float': 96.97, 'total_shares': 4455667788, 'insider_activity': []
    },
}


# ===================================================================
#  HELPER FUNCTIONS
# ===================================================================
def get_stock_level(code):
    if code in BLUE_CHIP_STOCKS:    return '💎 Blue Chip'
    if code in SECOND_LINER_STOCKS: return '📈 Second Liner'
    return '🎯 Third Liner'

def get_stocks_by_level(levels):
    result = []
    if 'Blue Chip'    in levels: result += BLUE_CHIP_STOCKS
    if 'Second Liner' in levels: result += SECOND_LINER_STOCKS
    if 'Third Liner'  in levels:
        result += [s for s in STOCKS_LIST if s not in BLUE_CHIP_STOCKS and s not in SECOND_LINER_STOCKS]
    return list(set(result))

def is_fca(code):            return code in FCA_STOCKS
def get_ff_holders(code):   return SHAREHOLDER_DATA.get(code, {}).get('pemegang', [])
def get_ff_value(code):     return SHAREHOLDER_DATA.get(code, {}).get('free_float', 100.0)
def get_insider(code):      return SHAREHOLDER_DATA.get(code, {}).get('insider_activity', [])

def goreng_pot(ff):
    if ff < 10:  return '🔥 UT'
    if ff < 15:  return '🔥 ST'
    if ff < 25:  return '⚡ TG'
    if ff < 40:  return '📊 SD'
    return '📉 RD'

def kat_short(k):
    return {'Ultra Low Float':'ULF','Very Low Float':'VLF','Low Float':'LF',
            'Moderate Low Float':'MLF','Normal Float':'NF'}.get(k, k)

def lvl_short(code):
    return {'💎 Blue Chip':'BC','📈 Second Liner':'SL','🎯 Third Liner':'TL'}.get(get_stock_level(code), '')


# ===================================================================
#  FREE FLOAT CARD  — built via string concat, ZERO f-strings inside HTML
# ===================================================================
def ff_card(code, ff_val):
    holders = get_ff_holders(code)
    insider  = get_insider(code)

    # FCA badge
    fca_html = ""
    if is_fca(code):
        fca_html = (
            '<div style="display:inline-block;background:rgba(255,170,0,.1);'
            'border:1px solid rgba(255,170,0,.3);border-radius:6px;'
            'padding:4px 11px;margin-bottom:10px;">'
            '<span style="color:#ffaa00;font-size:.75rem;letter-spacing:.5px;">'
            '&#9888; FCA &mdash; PAPAN PEMANTAUAN KHUSUS</span></div>'
        )

    # FF total row
    ff_pct_str = str(round(ff_val, 2)) + "%"
    ff_row = (
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'background:rgba(0,210,110,.07);border:1px solid rgba(0,210,110,.18);'
        'border-radius:8px;padding:9px 14px;margin-bottom:12px;">'
        '<span style="color:#8b949e;font-size:.81rem;">Total Free Float</span>'
        '<span style="color:#00d26e;font-weight:700;font-size:1.02rem;'
        'font-family:Courier New,monospace;">' + ff_pct_str + '</span>'
        '</div>'
    )

    # Holder rows
    holder_html = ""
    total_inst  = 0.0
    for p in holders:
        pct = (p['persen'] / ff_val * 100) if ff_val > 0 else 0.0
        total_inst += pct
        bar   = min(pct * 1.8, 100)
        clr   = '#58a6ff' if p['tipe'] == 'Institusi' else '#3fb950'
        pct_s = str(round(pct, 1)) + "%"
        bar_s = str(round(bar)) + "%"
        holder_html += (
            '<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);'
            'border-radius:8px;padding:9px 12px;margin-bottom:5px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<span style="width:7px;height:7px;border-radius:50%;background:' + clr + ';display:inline-block;"></span>'
            '<span style="color:#c9d1d9;font-size:.81rem;">' + p['nama'] + '</span>'
            '<span style="color:#484f58;font-size:.7rem;background:rgba(255,255,255,.04);'
            'padding:1px 7px;border-radius:10px;">' + p['tipe'] + '</span>'
            '</div>'
            '<span style="color:' + clr + ';font-weight:700;font-family:Courier New,monospace;font-size:.87rem;">'
            + pct_s + '</span>'
            '</div>'
            '<div style="height:3px;background:rgba(255,255,255,.05);border-radius:2px;">'
            '<div style="width:' + bar_s + ';height:100%;background:' + clr + ';border-radius:2px;"></div>'
            '</div>'
            '</div>'
        )

    # Ritel row
    ritel     = 100.0 - total_inst
    ritel_bar = str(round(min(ritel * 0.7, 100))) + "%"
    ritel_pct = str(round(ritel, 1)) + "%"
    ritel_html = (
        '<div style="background:rgba(0,210,110,.05);border:1px solid rgba(0,210,110,.15);'
        'border-radius:8px;padding:9px 12px;margin-bottom:5px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
        '<div style="display:flex;align-items:center;gap:8px;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:#00d26e;display:inline-block;"></span>'
        '<span style="color:#c9d1d9;font-size:.81rem;">Ritel</span>'
        '</div>'
        '<span style="color:#00d26e;font-weight:700;font-family:Courier New,monospace;font-size:.87rem;">'
        + ritel_pct + '</span>'
        '</div>'
        '<div style="height:3px;background:rgba(255,255,255,.05);border-radius:2px;">'
        '<div style="width:' + ritel_bar + ';height:100%;background:#00d26e;border-radius:2px;"></div>'
        '</div>'
        '</div>'
    )

    no_holder_note = ""
    if not holders:
        no_holder_note = (
            '<p style="color:#484f58;font-size:.8rem;margin-bottom:8px;">'
            'Tidak ada institusi/asing &gt;1%</p>'
        )

    # Insider activity
    ins_html = ""
    if insider:
        ins_rows = ""
        for a in insider:
            clr2 = '#3fb950'             if a['aksi'] == 'BELI' else '#f85149'
            bg2  = 'rgba(63,185,80,.07)' if a['aksi'] == 'BELI' else 'rgba(248,81,73,.07)'
            bd2  = 'rgba(63,185,80,.2)'  if a['aksi'] == 'BELI' else 'rgba(248,81,73,.2)'
            jml  = "{:,}".format(a['jumlah'])
            ins_rows += (
                '<div style="display:flex;justify-content:space-between;align-items:center;'
                'background:' + bg2 + ';border:1px solid ' + bd2 + ';'
                'border-radius:7px;padding:7px 12px;margin-bottom:4px;">'
                '<span style="color:#8b949e;font-size:.77rem;font-family:Courier New,monospace;">'
                + a['tanggal'] + '</span>'
                '<span style="color:#c9d1d9;font-size:.77rem;">' + a['insider'] + '</span>'
                '<span style="color:' + clr2 + ';font-weight:700;font-size:.81rem;'
                'font-family:Courier New,monospace;">' + a['aksi'] + ' ' + jml + '</span>'
                '</div>'
            )
        ins_html = (
            '<div style="margin-top:12px;margin-bottom:6px;">'
            '<span style="color:#484f58;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;">'
            'Insider Activity (30 Hari)</span></div>'
            + ins_rows
        )

    # Assemble full card
    card = (
        '<div style="background:linear-gradient(135deg,#0d1117,#161b22);'
        'padding:16px;border-radius:12px;margin:10px 0;'
        'border:1px solid #21262d;box-shadow:0 4px 20px rgba(0,0,0,.4);">'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
        '<div style="width:3px;height:22px;background:linear-gradient(180deg,#e8b84b,#c8891a);'
        'border-radius:2px;"></div>'
        '<span style="color:#e8b84b;font-family:Courier New,monospace;font-size:.87rem;letter-spacing:1px;">'
        'FREE FLOAT &mdash; ' + code + '</span>'
        '</div>'
        + fca_html
        + ff_row
        + no_holder_note
        + holder_html
        + ritel_html
        + ins_html
        + '</div>'
    )
    return card


# ===================================================================
#  PAGE CONFIG
# ===================================================================
st.set_page_config(
    page_title="Radar Aksara",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================
#  GLOBAL CSS
# ===================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background: #080c12; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1380px; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

[data-testid="stSidebar"] {
    background: #0a0e18 !important;
    border-right: 1px solid #181f2e !important;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    color: #e8b84b !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: .78rem !important; letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #3d4f6e !important; font-size: .72rem !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    margin-top: 1.1rem !important;
}
[data-testid="stSidebar"] label { color: #8b97ae !important; font-size: .83rem !important; }
[data-testid="stSidebar"] .stCaption { color: #2e3a4e !important; font-size: .72rem !important; }
[data-testid="stSidebar"] hr { border-color: #181f2e !important; margin: .8rem 0 !important; }

.stRadio [data-testid="stWidgetLabel"] {
    color: #3d4f6e !important; font-size: .72rem !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
}
div[role="radiogroup"] label {
    background: rgba(255,255,255,.02) !important; border: 1px solid #1e2840 !important;
    border-radius: 8px !important; padding: 5px 13px !important;
    color: #6b7a8e !important; font-size: .82rem !important; transition: all .2s !important;
}
div[role="radiogroup"] label:hover {
    border-color: #e8b84b !important; color: #e8b84b !important;
    background: rgba(232,184,75,.05) !important;
}

.stSelectbox > div > div, .stMultiSelect > div > div {
    background: rgba(255,255,255,.025) !important; border: 1px solid #1e2840 !important;
    border-radius: 9px !important; color: #c9d1d9 !important;
}
.stSelectbox > div > div:hover, .stMultiSelect > div > div:hover { border-color: #58a6ff !important; }
.stSelectbox label, .stMultiSelect label {
    color: #3d4f6e !important; font-size: .72rem !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
}

.stSlider [data-testid="stWidgetLabel"] {
    color: #3d4f6e !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: 1px !important;
}
.stSlider .st-be { background: #1e2840 !important; }
.stSlider .st-bf { background: #e8b84b !important; }

.stNumberInput label {
    color: #3d4f6e !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: 1px !important;
}
.stNumberInput input {
    background: rgba(255,255,255,.025) !important; border: 1px solid #1e2840 !important;
    border-radius: 8px !important; color: #c9d1d9 !important;
}

.stCheckbox label { color: #8b97ae !important; font-size: .84rem !important; }

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e8b84b 0%, #c8891a 100%) !important;
    color: #080c12 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important; font-size: .88rem !important;
    letter-spacing: 2px !important; border: none !important;
    border-radius: 10px !important; padding: .65rem 2rem !important;
    box-shadow: 0 4px 22px rgba(232,184,75,.28) !important;
    transition: all .25s ease !important; text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 32px rgba(232,184,75,.48) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0) !important; }

.stButton > button:not([kind="primary"]) {
    background: rgba(255,255,255,.025) !important; color: #8b97ae !important;
    border: 1px solid #1e2840 !important; border-radius: 8px !important;
    font-size: .82rem !important; transition: all .2s !important;
}
.stButton > button:not([kind="primary"]):hover { border-color: #58a6ff !important; color: #58a6ff !important; }

[data-testid="metric-container"] {
    background: rgba(255,255,255,.02) !important; border: 1px solid #1e2840 !important;
    border-radius: 10px !important; padding: 14px !important;
}
[data-testid="metric-container"] label {
    color: #3d4f6e !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: .8px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8b84b !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.5rem !important;
}

.stDataFrame { border: 1px solid #181f2e !important; border-radius: 12px !important; overflow: hidden !important; }

.streamlit-expanderHeader {
    background: rgba(255,255,255,.02) !important; border: 1px solid #1e2840 !important;
    border-radius: 10px !important; color: #8b97ae !important; font-size: .86rem !important;
    transition: all .2s !important;
}
.streamlit-expanderHeader:hover { border-color: #e8b84b !important; color: #e8b84b !important; }
.streamlit-expanderContent {
    background: rgba(10,14,24,.9) !important; border: 1px solid #1e2840 !important;
    border-top: none !important; border-radius: 0 0 10px 10px !important;
}

.stInfo {
    background: rgba(88,166,255,.05) !important; border: 1px solid rgba(88,166,255,.18) !important;
    border-radius: 9px !important; color: #8b97ae !important; font-size: .83rem !important;
}
.stWarning {
    background: rgba(232,184,75,.05) !important; border: 1px solid rgba(232,184,75,.22) !important;
    border-radius: 9px !important; color: #c9d1d9 !important; font-size: .83rem !important;
}
.stSuccess {
    background: rgba(63,185,80,.05) !important; border: 1px solid rgba(63,185,80,.18) !important;
    border-radius: 9px !important;
}
.stError {
    background: rgba(248,81,73,.05) !important; border: 1px solid rgba(248,81,73,.18) !important;
    border-radius: 9px !important;
}

.stProgress > div > div { background: linear-gradient(90deg,#e8b84b,#c8891a) !important; border-radius: 3px !important; }
.stProgress > div { background: #1e2840 !important; border-radius: 3px !important; }

.stDownloadButton > button {
    background: rgba(255,255,255,.02) !important; border: 1px solid #1e2840 !important;
    border-radius: 9px !important; color: #8b97ae !important; font-size: .82rem !important;
    width: 100% !important; transition: all .2s !important;
}
.stDownloadButton > button:hover {
    border-color: #3fb950 !important; color: #3fb950 !important;
    background: rgba(63,185,80,.05) !important;
}

hr { border-color: #181f2e !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ===================================================================
#  HEADER
# ===================================================================
today_str = datetime.now().strftime('%d %b %Y')

header_html = (
    '<div style="background:linear-gradient(135deg,#0d1117 0%,#10192a 100%);'
    'border:1px solid #181f2e;border-radius:16px;padding:26px 30px;'
    'margin-bottom:22px;position:relative;overflow:hidden;">'

    '<div style="position:absolute;top:-40px;right:-40px;width:260px;height:260px;'
    'background:radial-gradient(circle,rgba(232,184,75,.1) 0%,transparent 65%);pointer-events:none;"></div>'

    '<div style="position:absolute;bottom:-60px;left:-20px;width:200px;height:200px;'
    'background:radial-gradient(circle,rgba(88,166,255,.06) 0%,transparent 70%);pointer-events:none;"></div>'

    '<div style="display:flex;align-items:center;gap:18px;position:relative;">'

    '<div style="width:52px;height:52px;flex-shrink:0;'
    'background:linear-gradient(135deg,#e8b84b,#c8891a);border-radius:14px;'
    'display:flex;align-items:center;justify-content:center;font-size:1.55rem;'
    'box-shadow:0 6px 24px rgba(232,184,75,.35);">&#127919;</div>'

    '<div>'
    '<div style="font-family:IBM Plex Mono,monospace;font-size:1.65rem;font-weight:700;'
    'color:#f0f6fc;letter-spacing:2px;line-height:1.05;">'
    'RADAR <span style="color:#e8b84b;">AKSARA</span></div>'
    '<div style="color:#2e3a4e;font-size:.77rem;margin-top:5px;letter-spacing:.4px;">'
    'Open=Low Pattern &nbsp;&middot;&nbsp; Low Float Scanner &nbsp;&middot;&nbsp; '
    'Blue Chip &middot; Second &middot; Third Liner'
    '</div>'
    '</div>'

    '<div style="margin-left:auto;text-align:right;">'
    '<div style="background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.25);'
    'border-radius:20px;padding:4px 12px;display:inline-block;'
    'font-family:IBM Plex Mono,monospace;color:#3fb950;font-size:.72rem;letter-spacing:1px;">'
    '&#9679; LIVE</div>'
    '<div style="color:#2e3a4e;font-size:.72rem;margin-top:5px;">' + today_str + '</div>'
    '</div>'

    '</div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)


# ===================================================================
#  SIDEBAR
# ===================================================================
with st.sidebar:
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(232,184,75,.08),transparent);'
        'border:1px solid rgba(232,184,75,.12);border-radius:9px;padding:11px 13px;margin-bottom:14px;">'
        '<div style="font-family:IBM Plex Mono,monospace;color:#e8b84b;'
        'font-size:.72rem;letter-spacing:2px;">&#9881; CONTROL PANEL</div>'
        '</div>',
        unsafe_allow_html=True
    )

    scan_mode = st.radio("MODE", ["📈 Open = Low Scanner", "🔍 Low Float Scanner"], index=0)

    st.markdown("---")
    st.markdown("### 🎯 Filter")
    filter_type = st.radio("Tipe Filter", ["Semua Saham", "Pilih Manual", "Filter Tingkatan"], index=0)

    selected_stocks = []
    selected_levels = []

    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect("Pilih Saham", options=STOCKS_LIST, default=[])
    elif filter_type == "Filter Tingkatan":
        selected_levels = st.multiselect(
            "Tingkatan",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
        )
        if selected_levels:
            cnt = len(get_stocks_by_level(selected_levels))
            st.info("**" + str(cnt) + "** saham · ~" + str(round(cnt * 0.5 / 60, 1)) + " menit")

    st.markdown("---")
    st.markdown("### 📌 Legenda")
    for ico, lbl, desc in [
        ("💎", "Blue Chip", "> Rp10T"),
        ("📈", "Second Liner", "Rp500M – Rp10T"),
        ("🎯", "Third Liner", "< Rp1T"),
        ("⚠️", "FCA", "Papan Pemantauan"),
    ]:
        st.markdown(
            '<div style="display:flex;gap:8px;align-items:center;padding:4px 0;">'
            '<span>' + ico + '</span>'
            '<div>'
            '<div style="color:#c9d1d9;font-size:.8rem;">' + lbl + '</div>'
            '<div style="color:#2e3a4e;font-size:.71rem;">' + desc + '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;color:#1e2840;font-size:.7rem;'
        'font-family:IBM Plex Mono,monospace;">Made with &#10084; for Indonesian Traders</div>',
        unsafe_allow_html=True
    )


# ===================================================================
#  UTILITY: section header
# ===================================================================
def sec_head(title, sub=""):
    sub_block = (
        '<div style="color:#2e3a4e;font-size:.76rem;margin-top:2px;">' + sub + '</div>'
    ) if sub else ""
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;margin:24px 0 14px 0;">'
        '<div style="width:3px;height:20px;background:linear-gradient(180deg,#e8b84b,#c8891a);border-radius:2px;"></div>'
        '<div>'
        '<div style="color:#f0f6fc;font-size:.97rem;font-weight:600;">' + title + '</div>'
        + sub_block +
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# ===================================================================
#  SCAN STATUS BAR  (used during loop)
# ===================================================================
def status_bar(stock, i, total, elapsed, remaining):
    return (
        '<div style="background:rgba(255,255,255,.02);border:1px solid #1e2840;'
        'border-radius:8px;padding:9px 15px;display:flex;align-items:center;gap:12px;">'
        '<span style="color:#e8b84b;font-family:IBM Plex Mono,monospace;font-size:.84rem;">'
        '&#9675; ' + stock + '</span>'
        '<span style="color:#2e3a4e;font-size:.78rem;">'
        + str(i+1) + '/' + str(total)
        + ' &nbsp;&middot;&nbsp; ' + str(round(elapsed)) + 's elapsed'
        + ' &nbsp;&middot;&nbsp; ~' + str(round(remaining)) + 's remaining'
        + '</span>'
        '</div>'
    )


# ===================================================================
#  SUCCESS CARD
# ===================================================================
def success_card(count, total_time_s, periodo, min_g):
    return (
        '<div style="background:linear-gradient(135deg,#0d1117,#10192a);'
        'border:1px solid #181f2e;border-radius:14px;padding:26px 28px;'
        'margin:18px 0;position:relative;overflow:hidden;">'

        '<div style="position:absolute;top:0;right:0;width:220px;height:100%;'
        'background:radial-gradient(ellipse at right,rgba(63,185,80,.09) 0%,transparent 70%);'
        'pointer-events:none;"></div>'

        '<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;position:relative;">'

        '<div style="width:50px;height:50px;background:rgba(63,185,80,.1);'
        'border:1px solid rgba(63,185,80,.28);border-radius:13px;'
        'display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex-shrink:0;">'
        '&#10003;</div>'

        '<div>'
        '<div style="color:#3fb950;font-family:IBM Plex Mono,monospace;'
        'font-size:.7rem;letter-spacing:2px;text-transform:uppercase;">SCAN BERHASIL</div>'
        '<div style="color:#f0f6fc;font-size:1.85rem;font-weight:700;'
        'font-family:IBM Plex Mono,monospace;margin-top:2px;line-height:1;">'
        + str(count) +
        ' <span style="font-size:.9rem;color:#6b7a8e;font-weight:400;">saham ditemukan</span>'
        '</div>'
        '</div>'

        '<div style="margin-left:auto;display:flex;gap:22px;flex-wrap:wrap;">'

        '<div style="text-align:center;">'
        '<div style="color:#2e3a4e;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;">Waktu</div>'
        '<div style="color:#e8b84b;font-family:IBM Plex Mono,monospace;font-size:1.1rem;margin-top:3px;">'
        + str(round(total_time_s)) + 's</div>'
        '</div>'

        '<div style="text-align:center;">'
        '<div style="color:#2e3a4e;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;">Periode</div>'
        '<div style="color:#58a6ff;font-family:IBM Plex Mono,monospace;font-size:1.1rem;margin-top:3px;">'
        + periodo + '</div>'
        '</div>'

        '<div style="text-align:center;">'
        '<div style="color:#2e3a4e;font-size:.67rem;text-transform:uppercase;letter-spacing:1px;">Min Gain</div>'
        '<div style="color:#00d26e;font-family:IBM Plex Mono,monospace;font-size:1.1rem;margin-top:3px;">'
        + str(min_g) + '%</div>'
        '</div>'

        '</div>'
        '</div>'
        '</div>'
    )


# ===================================================================
#  OPEN = LOW SCANNER
# ===================================================================
if "Open = Low" in scan_mode:

    sec_head("Open = Low Scanner", "Deteksi pola Open sama dengan Low + kenaikan ≥ target")

    col1, col2, col3 = st.columns(3)
    with col1:
        periode = st.selectbox("Periode Analisis",
            ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with col2:
        min_kenaikan = st.slider("Minimal Kenaikan (%)", 1, 20, 5)
    with col3:
        limit_saham = st.number_input("Limit Hasil", min_value=5, max_value=100, value=20)

    sec_head("Mode Scanning")
    ca, cb = st.columns(2)
    with ca:
        scan_option = st.radio("Kecepatan",
            ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"], index=0, horizontal=True)
    with cb:
        st.markdown(
            '<div style="background:rgba(255,255,255,.02);border:1px solid #1e2840;'
            'border-radius:10px;padding:13px 16px;">'
            '<div style="color:#2e3a4e;font-size:.7rem;text-transform:uppercase;'
            'letter-spacing:1px;margin-bottom:8px;">Estimasi Waktu</div>'
            '<div style="display:flex;gap:24px;">'
            '<div><div style="color:#e8b84b;font-size:.81rem;font-family:IBM Plex Mono,monospace;">&#9889; Cepat</div>'
            '<div style="color:#c9d1d9;font-size:.87rem;">&#177; 30 detik</div></div>'
            '<div><div style="color:#58a6ff;font-size:.81rem;font-family:IBM Plex Mono,monospace;">&#128034; Lengkap</div>'
            '<div style="color:#c9d1d9;font-size:.87rem;">&#177; 7&ndash;10 menit</div></div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    periode_map = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    hari = periode_map[periode]

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):

        if filter_type == "Pilih Manual" and selected_stocks:
            stocks_to_scan = selected_stocks
        elif filter_type == "Filter Tingkatan" and selected_levels:
            stocks_to_scan = get_stocks_by_level(selected_levels)
        else:
            stocks_to_scan = STOCKS_LIST[:50] if "Cepat" in scan_option else STOCKS_LIST

        est_s = len(stocks_to_scan) * 0.5
        est_m = est_s / 60
        if est_m > 2:
            st.warning("Memproses **" + str(len(stocks_to_scan)) + " saham** · Estimasi **" + str(round(est_m, 1)) + " menit** · Jangan refresh halaman")
        else:
            st.info("Memproses **" + str(len(stocks_to_scan)) + " saham** · Estimasi **" + str(round(est_s)) + " detik**")

        prog_bar   = st.progress(0)
        stat_slot  = st.empty()

        results = []
        t0      = time.time()

        for i, stock in enumerate(stocks_to_scan):
            el  = time.time() - t0
            rem = (el / (i + 1)) * (len(stocks_to_scan) - i - 1) if i > 0 else 0
            stat_slot.markdown(status_bar(stock, i, len(stocks_to_scan), el, rem), unsafe_allow_html=True)
            result = scan_open_low_pattern(stock, periode_hari=hari, min_kenaikan=min_kenaikan)
            if result:
                results.append(result)
            prog_bar.progress((i + 1) / len(stocks_to_scan))
            time.sleep(0.3)

        prog_bar.empty()
        stat_slot.empty()
        total_time = time.time() - t0

        if results:
            df_results = pd.DataFrame(results).sort_values('frekuensi', ascending=False).head(limit_saham)

            st.markdown(success_card(len(df_results), total_time, periode, min_kenaikan), unsafe_allow_html=True)

            # TABLE
            sec_head("Hasil Scanning", "Free float · FCA · tingkatan saham")
            enhanced = []
            for _, row in df_results.iterrows():
                s  = row['saham']
                ff = get_ff_value(s)
                h  = get_ff_holders(s)
                ti = sum((p['persen'] / ff * 100) for p in h if ff > 0)
                enhanced.append({
                    'Saham': s,         'Level': get_stock_level(s),
                    'Frek':  row['frekuensi'],
                    'Prob':  str(round(row['probabilitas'])) + "%",
                    'Gain':  str(round(row['rata_rata_kenaikan'])) + "%",
                    'FF':    str(round(ff)) + "%",
                    'Inst':  str(round(ti)) + "%",
                    'Ritel': str(round(100 - ti)) + "%",
                    'FCA':   '⚠️' if is_fca(s) else '',
                    'Pot':   goreng_pot(ff),
                })
            enhanced_df = pd.DataFrame(enhanced)
            st.dataframe(enhanced_df, use_container_width=True, height=450, hide_index=True)

            # CHART
            sec_head("Top 10 Saham", "Frekuensi pola Open=Low")
            top10 = df_results.head(10)
            fig_bar = go.Figure(go.Bar(
                x=top10['saham'], y=top10['frekuensi'],
                marker=dict(
                    color=top10['probabilitas'],
                    colorscale=[[0,'#111827'],[0.4,'#1e3a5f'],[1,'#e8b84b']],
                    line=dict(color='rgba(232,184,75,.25)', width=1),
                ),
                hovertemplate='<b>%{x}</b><br>Frekuensi: %{y}<br>Prob: %{customdata:.1f}%<extra></extra>',
                customdata=top10['probabilitas'],
            ))
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Outfit', color='#6b7a8e', size=12),
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#6b7a8e')),
                yaxis=dict(showgrid=True, gridcolor='#181f2e', zeroline=False, tickfont=dict(color='#6b7a8e')),
                margin=dict(l=8, r=8, t=18, b=8), height=360,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # AI ANALYSIS
            sec_head("🤖 Analisis AI", "Insight untuk top 5 saham")
            for _, row in df_results.head(5).iterrows():
                analysis = analyze_pattern(row.to_dict())
                lbl = (
                    "**" + row['saham'] + "** — " + get_stock_level(row['saham'])
                    + "  ·  Prob " + str(round(row['probabilitas'], 1)) + "%"
                    + "  ·  Gain " + str(round(row['rata_rata_kenaikan'], 1)) + "%"
                )
                with st.expander(lbl):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Probabilitas",  str(round(row['probabilitas'], 1))    + "%")
                    c2.metric("Rata Gain",     str(round(row['rata_rata_kenaikan'], 1)) + "%")
                    c3.metric("Max Gain",      str(round(row['max_kenaikan'], 1))    + "%")
                    c4.metric("Frekuensi",     str(row['frekuensi']) + "x")
                    st.markdown(
                        '<div style="color:#8b97ae;font-size:.86rem;line-height:1.65;padding:10px 0;">'
                        + analysis + '</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(ff_card(row['saham'], get_ff_value(row['saham'])), unsafe_allow_html=True)

            # WATCHLIST
            sec_head("📋 Watchlist Generator", "Saham prioritas untuk dipantau besok")
            wc1, wc2 = st.columns(2)
            with wc1: min_gain_f = st.slider("Min Gain (%)", 3, 10, 5, key="mg")
            with wc2: top_n      = st.number_input("Jumlah Saham", 5, 30, 15, key="tn")

            df_wl = df_results[df_results['rata_rata_kenaikan'] >= min_gain_f].copy()

            if not df_wl.empty:
                mx_p, mx_g = df_wl['probabilitas'].max(), df_wl['rata_rata_kenaikan'].max()
                if mx_p > 0 and mx_g > 0:
                    df_wl['skor'] = (df_wl['probabilitas']/mx_p)*50 + (df_wl['rata_rata_kenaikan']/mx_g)*50
                    df_wl = df_wl.nlargest(top_n, 'skor')

                today_full = datetime.now().strftime('%d %B %Y')
                st.markdown(
                    '<div style="background:linear-gradient(135deg,#0d1117,#0e1928);'
                    'border:1px solid rgba(88,166,255,.14);border-radius:12px;'
                    'padding:18px 22px;margin:14px 0;position:relative;overflow:hidden;">'

                    '<div style="position:absolute;top:0;left:0;right:0;height:2px;'
                    'background:linear-gradient(90deg,transparent,#58a6ff 50%,transparent);"></div>'

                    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
                    '<div>'
                    '<div style="font-family:IBM Plex Mono,monospace;color:#58a6ff;'
                    'font-size:.7rem;letter-spacing:2px;">WATCHLIST TRADING</div>'
                    '<div style="color:#f0f6fc;font-size:1.02rem;font-weight:600;margin-top:3px;">'
                    + today_full + '</div>'
                    '</div>'
                    '<div style="background:rgba(232,184,75,.1);border:1px solid rgba(232,184,75,.28);'
                    'padding:5px 14px;border-radius:20px;color:#e8b84b;'
                    'font-size:.77rem;font-family:IBM Plex Mono,monospace;">'
                    '&#127919; Pantau 15 menit pertama!'
                    '</div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                wl_data = []
                for i, (_, row) in enumerate(df_wl.iterrows()):
                    rekom = ("🔥 PRIORITAS" if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7
                             else "⚡ LAYAK" if row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5
                             else "📌 PANTAU")
                    ff = get_ff_value(row['saham'])
                    wl_data.append({
                        "Rank": i+1, "Saham": row['saham'], "Lvl": lvl_short(row['saham']),
                        "Prob": str(round(row['probabilitas'])) + "%",
                        "Gain": str(round(row['rata_rata_kenaikan'])) + "%",
                        "FF":   str(round(ff)) + "%",
                        "FCA":  '⚠️' if is_fca(row['saham']) else '',
                        "Pot":  goreng_pot(ff), "Rekom": rekom,
                    })

                wl_df = pd.DataFrame(wl_data)
                st.dataframe(wl_df, use_container_width=True, hide_index=True, height=360)

                ex1, ex2 = st.columns(2)
                with ex1:
                    st.download_button(
                        "⬇ Export CSV", wl_df.to_csv(index=False).encode(),
                        "watchlist_" + datetime.now().strftime('%Y%m%d') + ".csv",
                        "text/csv", use_container_width=True
                    )
                with ex2:
                    xl = export_to_excel(wl_df)
                    if xl:
                        st.download_button(
                            "⬇ Export Excel", xl,
                            "watchlist_" + datetime.now().strftime('%Y%m%d') + ".xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                st.markdown(
                    '<div style="color:#2e3a4e;font-size:.71rem;text-align:center;margin-top:6px;'
                    'font-family:IBM Plex Mono,monospace;">'
                    'BC=Blue Chip &middot; SL=Second Liner &middot; TL=Third Liner &middot; FF=Free Float &middot; FCA=Full Call Auction'
                    '</div>',
                    unsafe_allow_html=True
                )
            else:
                st.warning("Tidak ada saham dengan gain minimal " + str(min_gain_f) + "%")

            # EXPORT SCANNING
            sec_head("📥 Export Data Scanning")
            es1, es2 = st.columns(2)
            with es1:
                st.download_button(
                    "⬇ Export CSV", enhanced_df.to_csv(index=False).encode(),
                    "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True
                )
            with es2:
                xl2 = export_to_excel(enhanced_df)
                if xl2:
                    st.download_button(
                        "⬇ Export Excel", xl2,
                        "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        else:
            st.markdown(
                '<div style="background:rgba(248,81,73,.05);border:1px solid rgba(248,81,73,.18);'
                'border-radius:12px;padding:24px;text-align:center;">'
                '<div style="font-size:2rem;">&#128269;</div>'
                '<div style="color:#f85149;font-family:IBM Plex Mono,monospace;'
                'font-size:.81rem;margin-top:8px;letter-spacing:1px;">TIDAK ADA SAHAM DITEMUKAN</div>'
                '<div style="color:#2e3a4e;font-size:.77rem;margin-top:4px;">'
                'Coba ubah periode atau turunkan minimal kenaikan'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )


# ===================================================================
#  LOW FLOAT SCANNER
# ===================================================================
elif "Low Float" in scan_mode:

    sec_head("Low Float Scanner", "Deteksi saham free float rendah + potensi volatilitas tinggi")

    c1, c2 = st.columns(2)
    with c1: max_ff  = st.slider("Maks Free Float (%)", 1, 50, 20)
    with c2: min_vol = st.number_input("Min Volume", min_value=0, value=0, step=100000)

    sec_head("Filter Tingkatan")
    lc1, lc2, lc3 = st.columns(3)
    with lc1: scan_blue   = st.checkbox("💎 Blue Chip",    value=True)
    with lc2: scan_second = st.checkbox("📈 Second Liner", value=True)
    with lc3: scan_third  = st.checkbox("🎯 Third Liner",  value=True)

    scan_opt_lf = st.radio("Mode", ["⚡ Cepat", "🐢 Lengkap"], horizontal=True, index=0)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        lf_levels = (
            (["Blue Chip"]    if scan_blue   else []) +
            (["Second Liner"] if scan_second else []) +
            (["Third Liner"]  if scan_third  else [])
        )
        if selected_stocks:
            stocks_to_scan = selected_stocks
        elif lf_levels:
            stocks_to_scan = get_stocks_by_level(lf_levels)
        else:
            stocks_to_scan = STOCKS_LIST[:50] if scan_opt_lf == "⚡ Cepat" else STOCKS_LIST

        with st.spinner("Scanning " + str(len(stocks_to_scan)) + " saham..."):
            results = scan_low_float(stocks_to_scan, max_ff, min_vol)

        if results:
            df_r = pd.DataFrame(results)

            st.markdown(
                '<div style="background:linear-gradient(135deg,#0d1117,#0e1928);'
                'border:1px solid rgba(63,185,80,.18);border-radius:14px;'
                'padding:24px 26px;margin:16px 0;position:relative;overflow:hidden;">'

                '<div style="position:absolute;top:0;right:0;width:180px;height:100%;'
                'background:radial-gradient(ellipse at right,rgba(63,185,80,.08) 0%,transparent 70%);'
                'pointer-events:none;"></div>'

                '<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;position:relative;">'
                '<div style="width:48px;height:48px;background:rgba(63,185,80,.1);'
                'border:1px solid rgba(63,185,80,.26);border-radius:12px;'
                'display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">'
                '&#10003;</div>'
                '<div>'
                '<div style="color:#3fb950;font-family:IBM Plex Mono,monospace;'
                'font-size:.68rem;letter-spacing:2px;text-transform:uppercase;">LOW FLOAT SCAN SELESAI</div>'
                '<div style="color:#f0f6fc;font-size:1.7rem;font-weight:700;'
                'font-family:IBM Plex Mono,monospace;margin-top:2px;line-height:1;">'
                + str(len(df_r)) +
                ' <span style="font-size:.87rem;color:#6b7a8e;font-weight:400;">'
                'saham &middot; FF &lt; ' + str(max_ff) + '%</span>'
                '</div>'
                '</div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            sec_head("Hasil Scanning", "Komposisi pemegang, kategori, dan potensi")

            enriched = []
            for _, row in df_r.iterrows():
                s  = row['saham']
                ff = get_ff_value(s)
                h  = get_ff_holders(s)
                ti = sum((p['persen'] / ff * 100) for p in h if ff > 0)
                enriched.append({
                    'Saham':  s,
                    'Lvl':    lvl_short(s),
                    'FF':     str(round(ff)) + "%",
                    'Kat':    kat_short(row['category']),
                    'Vol(M)': str(round(row['volume_avg']/1e6, 1)),
                    'Volat':  str(round(row['volatility'])) + "%",
                    'Inst':   str(round(ti)) + "%",
                    'Ritel':  str(round(100 - ti)) + "%",
                    'FCA':    '⚠️' if is_fca(s) else '',
                    'Pot':    goreng_pot(ff),
                })
            enr_df = pd.DataFrame(enriched)
            st.dataframe(enr_df, use_container_width=True, height=450, hide_index=True)

            sec_head("Detail Free Float", "Top 5 breakdown pemegang")
            for _, row in df_r.head(5).iterrows():
                ff = get_ff_value(row['saham'])
                with st.expander("**" + row['saham'] + "** — " + get_stock_level(row['saham']) + "  ·  FF " + str(round(ff)) + "%"):
                    st.markdown(ff_card(row['saham'], ff), unsafe_allow_html=True)

            sec_head("Visualisasi Distribusi")
            vc1, vc2 = st.columns(2)

            with vc1:
                cat_v   = df_r['category'].value_counts()
                fig_pie = go.Figure(go.Pie(
                    labels=cat_v.index, values=cat_v.values, hole=0.55,
                    marker=dict(
                        colors=['#e8b84b','#58a6ff','#3fb950','#f85149','#bc8cff'],
                        line=dict(color='#080c12', width=2),
                    ),
                    textfont=dict(color='#c9d1d9', size=11),
                ))
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit', color='#6b7a8e'),
                    title=dict(text='Kategori FF', font=dict(color='#6b7a8e', size=13), x=0.5),
                    legend=dict(font=dict(color='#6b7a8e', size=10), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=0, r=0, t=38, b=0), height=290,
                    annotations=[dict(text='FF', x=0.5, y=0.5, font_size=13,
                                      showarrow=False, font_color='#2e3a4e')],
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with vc2:
                fig_sc = go.Figure(go.Scatter(
                    x=df_r['public_float'], y=df_r['volatility'],
                    mode='markers',
                    marker=dict(
                        size=[max(6, v/1e6*0.4) for v in df_r['volume_avg']],
                        color=df_r['volatility'],
                        colorscale=[[0,'#111827'],[0.5,'#1e3a5f'],[1,'#e8b84b']],
                        line=dict(color='rgba(232,184,75,.2)', width=1),
                        sizemode='area', sizeref=2,
                    ),
                    text=df_r['saham'],
                    hovertemplate='<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>',
                ))
                fig_sc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit', color='#6b7a8e', size=11),
                    title=dict(text='FF vs Volatilitas', font=dict(color='#6b7a8e', size=13), x=0.5),
                    xaxis=dict(title='Free Float (%)', showgrid=True, gridcolor='#181f2e', zeroline=False),
                    yaxis=dict(title='Volatilitas (%)', showgrid=True, gridcolor='#181f2e', zeroline=False),
                    margin=dict(l=8, r=8, t=38, b=8), height=290,
                )
                st.plotly_chart(fig_sc, use_container_width=True)

            sec_head("📥 Export Data")
            xe1, xe2 = st.columns(2)
            with xe1:
                st.download_button(
                    "⬇ Export CSV", enr_df.to_csv(index=False).encode(),
                    "low_float_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True
                )
            with xe2:
                xl3 = export_to_excel(enr_df)
                if xl3:
                    st.download_button(
                        "⬇ Export Excel", xl3,
                        "low_float_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        else:
            st.markdown(
                '<div style="background:rgba(248,81,73,.05);border:1px solid rgba(248,81,73,.18);'
                'border-radius:12px;padding:24px;text-align:center;">'
                '<div style="font-size:2rem;">&#128269;</div>'
                '<div style="color:#f85149;font-family:IBM Plex Mono,monospace;'
                'font-size:.81rem;margin-top:8px;letter-spacing:1px;">TIDAK ADA SAHAM DITEMUKAN</div>'
                '<div style="color:#2e3a4e;font-size:.77rem;margin-top:4px;">'
                'Coba naikkan batas maksimal free float'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )


# ===================================================================
#  FOOTER
# ===================================================================
st.markdown("---")
st.markdown(
    '<div style="display:flex;align-items:center;justify-content:space-between;'
    'flex-wrap:wrap;gap:10px;padding:8px 0;">'

    '<div style="display:flex;align-items:center;gap:8px;">'
    '<div style="width:20px;height:20px;background:linear-gradient(135deg,#e8b84b,#c8891a);'
    'border-radius:5px;display:flex;align-items:center;justify-content:center;'
    'font-size:.65rem;">&#127919;</div>'
    '<span style="color:#1e2840;font-size:.7rem;font-family:IBM Plex Mono,monospace;letter-spacing:1px;">'
    'RADAR AKSARA</span>'
    '</div>'

    '<div style="display:flex;gap:18px;flex-wrap:wrap;">'
    '<span style="color:#1e2840;font-size:.69rem;">BC=Blue Chip &middot; SL=Second Liner &middot; TL=Third Liner</span>'
    '<span style="color:#1e2840;font-size:.69rem;">FF=Free Float &middot; FCA=Full Call Auction</span>'
    '<span style="color:#1e2840;font-size:.69rem;">&#9888; Data edukasi, bukan rekomendasi investasi</span>'
    '</div>'

    '</div>',
    unsafe_allow_html=True
)
