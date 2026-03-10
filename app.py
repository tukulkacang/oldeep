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

# ─────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────
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
        'free_float': 95.67,
        'insider': [
            {'tanggal':'10 Mar 2026','insider':'Presdir','aksi':'BELI','jumlah':1000000,'harga':10250},
            {'tanggal':'25 Feb 2026','insider':'Komisaris','aksi':'BELI','jumlah':500000,'harga':10100},
        ]
    },
    'BBRI':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.09,'tipe':'Institusi'}],'free_float':98.91,'insider':[{'tanggal':'09 Mar 2026','insider':'Dirut','aksi':'JUAL','jumlah':50000,'harga':5800}]},
    'MDKA':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':2.15,'tipe':'Institusi'},{'nama':'Pemerintah Norwegia','persen':1.08,'tipe':'Asing'}],'free_float':89.31,'insider':[{'tanggal':'15 Feb 2026','insider':'Dirut','aksi':'BELI','jumlah':200000,'harga':2500}]},
    'CUAN':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.02,'tipe':'Institusi'},{'nama':'Vanguard Group','persen':1.15,'tipe':'Asing'}],'free_float':13.73,'insider':[{'tanggal':'05 Mar 2026','insider':'Direktur Utama','aksi':'BELI','jumlah':100000,'harga':15000}]},
    'BRPT':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.22,'tipe':'Institusi'}],'free_float':27.41,'insider':[{'tanggal':'28 Feb 2026','insider':'Komisaris','aksi':'JUAL','jumlah':75000,'harga':8500}]},
    'TPIA':  {'pemegang':[{'nama':'GIC Singapore','persen':3.45,'tipe':'Asing'}],'free_float':91.52,'insider':[]},
    'ASII':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':2.74,'tipe':'Institusi'}],'free_float':97.26,'insider':[]},
    'KLBF':  {'pemegang':[{'nama':'Pemerintah Norwegia','persen':1.30,'tipe':'Asing'},{'nama':'BPJS Ketenagakerjaan','persen':2.01,'tipe':'Institusi'}],'free_float':96.69,'insider':[]},
    'BYAN':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':1.33,'tipe':'Institusi'}],'free_float':58.45,'insider':[]},
    'ARTO':  {'pemegang':[{'nama':'Pemerintah Singapura','persen':8.28,'tipe':'Asing'}],'free_float':91.72,'insider':[]},
    'MTEL':  {'pemegang':[{'nama':'Pemerintah Singapura','persen':5.33,'tipe':'Asing'}],'free_float':94.67,'insider':[]},
    'AKRA':  {'pemegang':[{'nama':'Pemerintah Norwegia','persen':3.03,'tipe':'Asing'}],'free_float':96.97,'insider':[]},
    'INDF':  {'pemegang':[{'nama':'BPJS Ketenagakerjaan','persen':3.74,'tipe':'Institusi'}],'free_float':92.52,'insider':[]},
}

# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def stock_level(c):
    if c in BLUE_CHIP:    return '💎 Blue Chip'
    if c in SECOND_LINER: return '📈 Second Liner'
    return '🎯 Third Liner'

def level_abbr(c):
    m = {'💎 Blue Chip':'BC','📈 Second Liner':'SL','🎯 Third Liner':'TL'}
    return m.get(stock_level(c),'')

def stocks_by_level(lvls):
    r = []
    if 'Blue Chip'    in lvls: r += BLUE_CHIP
    if 'Second Liner' in lvls: r += SECOND_LINER
    if 'Third Liner'  in lvls: r += [s for s in STOCKS_LIST if s not in BLUE_CHIP and s not in SECOND_LINER]
    return list(set(r))

def ff_val(c):     return SHAREHOLDERS.get(c, {}).get('free_float', 100.0)
def ff_holders(c): return SHAREHOLDERS.get(c, {}).get('pemegang', [])
def insider_tx(c): return SHAREHOLDERS.get(c, {}).get('insider', [])
def is_fca(c):     return c in FCA_STOCKS

def goreng(ff):
    if ff < 10: return '🔥 UT'
    if ff < 15: return '🔥 ST'
    if ff < 25: return '⚡ TG'
    if ff < 40: return '📊 SD'
    return '📉 RD'

def kat_abbr(k):
    m = {'Ultra Low Float':'ULF','Very Low Float':'VLF','Low Float':'LF','Moderate Low Float':'MLF','Normal Float':'NF'}
    return m.get(k, k)

# ─────────────────────────────────────────────────────────
# HTML COMPONENTS  (semua via list + join, zero f-string)
# ─────────────────────────────────────────────────────────
def html_ff_card(code):
    ff    = ff_val(code)
    hlds  = ff_holders(code)
    ins   = insider_tx(code)
    parts = []

    # card wrapper
    parts.append(
        '<div style="'
            'background:#0d0d0d;'
            'border:1px solid #1c1c1c;'
            'border-radius:12px;'
            'padding:20px 22px;'
            'margin:8px 0 4px;'
        '">'
    )

    # header row
    parts.append('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">')
    parts.append(
        '<div style="display:flex;align-items:center;gap:8px;">'
            '<span style="'
                'font-family:\'Geist Mono\',monospace;'
                'font-size:.7rem;'
                'letter-spacing:.15em;'
                'color:#f97316;'
                'font-weight:500;'
            '">FREE FLOAT</span>'
            '<span style="'
                'font-family:\'Geist Mono\',monospace;'
                'font-size:.7rem;'
                'color:#404040;'
                'letter-spacing:.1em;'
            '">' + code + '</span>'
        '</div>'
    )
    if is_fca(code):
        parts.append(
            '<span style="'
                'font-family:\'Geist Mono\',monospace;'
                'font-size:.62rem;'
                'letter-spacing:.1em;'
                'color:#f97316;'
                'border:1px solid #3d1c00;'
                'padding:2px 8px;'
                'border-radius:4px;'
                'background:#1a0d00;'
            '">FCA</span>'
        )
    parts.append('</div>')  # close header row

    # total FF value — big number
    ff_str = str(round(ff, 1)) + '%'
    parts.append(
        '<div style="margin-bottom:20px;">'
            '<div style="'
                'font-family:\'Geist Mono\',monospace;'
                'font-size:2.2rem;'
                'font-weight:600;'
                'color:#ffffff;'
                'letter-spacing:-.02em;'
                'line-height:1;'
            '">' + ff_str + '</div>'
            '<div style="'
                'font-size:.73rem;'
                'color:#404040;'
                'margin-top:4px;'
                'letter-spacing:.05em;'
            '">total free float</div>'
        '</div>'
    )

    # divider
    parts.append('<div style="height:1px;background:#1c1c1c;margin-bottom:16px;"></div>')

    # breakdown rows
    total_inst = 0.0
    for h in hlds:
        pct = (h['persen'] / ff * 100) if ff > 0 else 0
        total_inst += pct
        pct_str  = str(round(pct, 1)) + '%'
        bar_pct  = str(round(min(pct * 2, 100)))
        dot_col  = '#3b82f6' if h['tipe'] == 'Institusi' else '#8b5cf6'
        parts.append(
            '<div style="margin-bottom:10px;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
                    '<div style="display:flex;align-items:center;gap:7px;">'
                        '<div style="width:5px;height:5px;border-radius:50%;background:' + dot_col + ';flex-shrink:0;"></div>'
                        '<span style="font-size:.78rem;color:#737373;">' + h['nama'] + '</span>'
                        '<span style="font-size:.65rem;color:#2d2d2d;background:#161616;padding:1px 6px;border-radius:3px;">' + h['tipe'] + '</span>'
                    '</div>'
                    '<span style="font-family:\'Geist Mono\',monospace;font-size:.78rem;color:#a3a3a3;">' + pct_str + '</span>'
                '</div>'
                '<div style="height:1px;background:#161616;border-radius:1px;overflow:hidden;">'
                    '<div style="height:1px;width:' + bar_pct + '%;background:' + dot_col + ';opacity:.5;"></div>'
                '</div>'
            '</div>'
        )

    ritel     = 100.0 - total_inst
    ritel_str = str(round(ritel, 1)) + '%'
    ritel_bar = str(round(min(ritel * 0.7, 100)))
    parts.append(
        '<div style="margin-bottom:10px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
                '<div style="display:flex;align-items:center;gap:7px;">'
                    '<div style="width:5px;height:5px;border-radius:50%;background:#22c55e;flex-shrink:0;"></div>'
                    '<span style="font-size:.78rem;color:#737373;">Ritel &amp; Publik</span>'
                '</div>'
                '<span style="font-family:\'Geist Mono\',monospace;font-size:.78rem;color:#22c55e;">' + ritel_str + '</span>'
            '</div>'
            '<div style="height:1px;background:#161616;border-radius:1px;overflow:hidden;">'
                '<div style="height:1px;width:' + ritel_bar + '%;background:#22c55e;opacity:.5;"></div>'
            '</div>'
        '</div>'
    )

    if not hlds:
        parts.append('<p style="font-size:.76rem;color:#404040;margin:0 0 12px;">Tidak ada institusi/asing di atas 1%</p>')

    # insider activity
    if ins:
        parts.append('<div style="height:1px;background:#1c1c1c;margin:16px 0 14px;"></div>')
        parts.append(
            '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#2d2d2d;margin-bottom:10px;">INSIDER ACTIVITY</div>'
        )
        for a in ins:
            is_buy   = a['aksi'] == 'BELI'
            val_col  = '#22c55e' if is_buy else '#ef4444'
            bg_col   = '#0a1a0f' if is_buy else '#1a0a0a'
            bdr_col  = '#1a3d20' if is_buy else '#3d1a1a'
            jml_fmt  = '{:,}'.format(a['jumlah'])
            parts.append(
                '<div style="'
                    'display:flex;justify-content:space-between;align-items:center;'
                    'background:' + bg_col + ';'
                    'border:1px solid ' + bdr_col + ';'
                    'border-radius:6px;'
                    'padding:7px 10px;'
                    'margin-bottom:4px;'
                '">'
                    '<span style="font-size:.72rem;color:#404040;">' + a['tanggal'] + '</span>'
                    '<span style="font-size:.72rem;color:#525252;">' + a['insider'] + '</span>'
                    '<span style="font-family:\'Geist Mono\',monospace;font-size:.74rem;font-weight:600;color:' + val_col + ';">' + a['aksi'] + ' ' + jml_fmt + '</span>'
                '</div>'
            )

    parts.append('</div>')  # close card
    return ''.join(parts)


def html_scan_progress(stk, i, total, el, rem):
    pct     = round((i + 1) / total * 100)
    pct_str = str(pct)
    elapsed = str(round(el)) + 's'
    remain  = '~' + str(round(rem)) + 's'
    num     = str(i + 1) + ' / ' + str(total)

    return ''.join([
        '<div style="'
            'background:#0d0d0d;'
            'border:1px solid #1c1c1c;'
            'border-radius:8px;'
            'padding:12px 16px;'
        '">',
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">',
        '<div style="display:flex;align-items:center;gap:8px;">',
        '<div style="'
            'width:4px;height:4px;border-radius:50%;'
            'background:#f97316;'
            'box-shadow:0 0 6px #f97316;'
        '"></div>',
        '<span style="font-family:\'Geist Mono\',monospace;font-size:.82rem;color:#d4d4d4;letter-spacing:.05em;">' + stk + '</span>',
        '</div>',
        '<div style="display:flex;gap:16px;">',
        '<span style="font-family:\'Geist Mono\',monospace;font-size:.7rem;color:#3d3d3d;">' + num + '</span>',
        '<span style="font-family:\'Geist Mono\',monospace;font-size:.7rem;color:#3d3d3d;">' + elapsed + '</span>',
        '<span style="font-family:\'Geist Mono\',monospace;font-size:.7rem;color:#3d3d3d;">' + remain + '</span>',
        '</div>',
        '</div>',
        '<div style="height:2px;background:#1c1c1c;border-radius:1px;overflow:hidden;">',
        '<div style="height:2px;width:' + pct_str + '%;background:#f97316;border-radius:1px;transition:width .3s;"></div>',
        '</div>',
        '</div>',
    ])


def html_result_banner(count, secs, period, gain):
    count_s  = str(count)
    secs_s   = str(round(secs)) + 's'
    gain_s   = str(gain) + '%'

    return ''.join([
        '<div style="'
            'background:#0d0d0d;'
            'border:1px solid #1c1c1c;'
            'border-radius:12px;'
            'padding:28px 32px;'
            'margin:20px 0 28px;'
        '">',
        '<div style="display:flex;align-items:flex-start;gap:48px;flex-wrap:wrap;">',

        # — count
        '<div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#3d3d3d;margin-bottom:6px;">DITEMUKAN</div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:3rem;font-weight:600;color:#ffffff;letter-spacing:-.04em;line-height:1;">' + count_s + '</div>',
        '<div style="font-size:.73rem;color:#525252;margin-top:4px;">saham</div>',
        '</div>',

        '<div style="width:1px;height:60px;background:#1c1c1c;align-self:center;"></div>',

        # — period
        '<div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#3d3d3d;margin-bottom:6px;">PERIODE</div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:1.4rem;font-weight:500;color:#a3a3a3;line-height:1;">' + period + '</div>',
        '</div>',

        '<div style="width:1px;height:60px;background:#1c1c1c;align-self:center;"></div>',

        # — gain
        '<div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#3d3d3d;margin-bottom:6px;">MIN GAIN</div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:1.4rem;font-weight:500;color:#f97316;line-height:1;">' + gain_s + '</div>',
        '</div>',

        '<div style="width:1px;height:60px;background:#1c1c1c;align-self:center;"></div>',

        # — time
        '<div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#3d3d3d;margin-bottom:6px;">WAKTU PROSES</div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:1.4rem;font-weight:500;color:#525252;line-height:1;">' + secs_s + '</div>',
        '</div>',

        '</div>',  # close flex
        '</div>',  # close card
    ])


def html_empty(msg, hint):
    return ''.join([
        '<div style="'
            'background:#0d0d0d;'
            'border:1px solid #1c1c1c;'
            'border-radius:12px;'
            'padding:56px 32px;'
            'text-align:center;'
        '">',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.65rem;letter-spacing:.2em;color:#2d2d2d;margin-bottom:8px;">TIDAK ADA HASIL</div>',
        '<div style="font-size:.85rem;color:#525252;">' + msg + '</div>',
        '<div style="font-size:.75rem;color:#2d2d2d;margin-top:6px;">' + hint + '</div>',
        '</div>',
    ])


def html_watchlist_header(date_str):
    return ''.join([
        '<div style="'
            'background:#0d0d0d;'
            'border:1px solid #1c1c1c;'
            'border-top:1px solid #f97316;'
            'border-radius:12px;'
            'padding:18px 22px;'
            'margin:16px 0 12px;'
        '">',
        '<div style="display:flex;justify-content:space-between;align-items:center;">',
        '<div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.62rem;letter-spacing:.15em;color:#3d3d3d;margin-bottom:4px;">WATCHLIST</div>',
        '<div style="font-size:.95rem;color:#d4d4d4;font-weight:500;">' + date_str + '</div>',
        '</div>',
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.68rem;color:#525252;letter-spacing:.05em;">pantau 15 menit pertama</div>',
        '</div>',
        '</div>',
    ])


def section_label(title, sub=''):
    sub_html = ''
    if sub:
        sub_html = '<span style="font-size:.72rem;color:#3d3d3d;margin-left:8px;">' + sub + '</span>'
    st.markdown(
        '<div style="display:flex;align-items:center;margin:32px 0 14px;">'
            '<span style="'
                'font-family:\'Geist Mono\',monospace;'
                'font-size:.62rem;'
                'letter-spacing:.2em;'
                'color:#525252;'
                'text-transform:uppercase;'
                'font-weight:500;'
            '">' + title + '</span>'
            + sub_html +
            '<div style="flex:1;height:1px;background:#1c1c1c;margin-left:16px;"></div>'
        '</div>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Radar Aksara",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600&family=Geist:wght@300;400;500;600&display=swap');

/* ── reset ── */
*, html, body, [class*="css"] {
    font-family: 'Geist', -apple-system, sans-serif !important;
}
.stApp {
    background: #080808;
}
.main .block-container {
    padding: 0 2.5rem 4rem;
    max-width: 1360px;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2d2d2d; border-radius: 2px; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #080808 !important;
    border-right: 1px solid #141414 !important;
}

/* ── widget labels ── */
.stRadio [data-testid="stWidgetLabel"],
.stSelectbox label,
.stMultiSelect label,
.stSlider [data-testid="stWidgetLabel"],
.stNumberInput label,
.stCheckbox label {
    font-family: 'Geist Mono', monospace !important;
    font-size: .62rem !important;
    letter-spacing: .15em !important;
    text-transform: uppercase !important;
    color: #3d3d3d !important;
}
.stCheckbox label {
    font-size: .82rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    color: #737373 !important;
}

/* ── radio ── */
div[role="radiogroup"] label {
    background: transparent !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 6px !important;
    padding: 5px 12px !important;
    color: #525252 !important;
    font-size: .82rem !important;
    transition: all .15s !important;
}
div[role="radiogroup"] label:hover {
    border-color: #404040 !important;
    color: #a3a3a3 !important;
    background: #111111 !important;
}

/* ── selects / inputs ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #0d0d0d !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 8px !important;
    color: #d4d4d4 !important;
    transition: border-color .15s !important;
}
.stSelectbox > div > div:hover,
.stMultiSelect > div > div:hover {
    border-color: #333333 !important;
}
.stNumberInput input {
    background: #0d0d0d !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 8px !important;
    color: #d4d4d4 !important;
}

/* ── slider ── */
.stSlider .st-be { background: #1c1c1c !important; }
.stSlider .st-bf { background: #f97316 !important; }

/* ── PRIMARY button (scan) ── */
.stButton > button[kind="primary"] {
    background: #f97316 !important;
    color: #080808 !important;
    font-family: 'Geist Mono', monospace !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    letter-spacing: .15em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 8px !important;
    padding: .7rem 2rem !important;
    transition: all .15s ease !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #fb923c !important;
    transform: none !important;
}

/* ── secondary button ── */
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    color: #525252 !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 7px !important;
    font-size: .8rem !important;
    transition: all .15s !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #404040 !important;
    color: #a3a3a3 !important;
    background: #111111 !important;
}

/* ── metrics ── */
[data-testid="metric-container"] {
    background: #0d0d0d !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
}
[data-testid="metric-container"] label {
    font-family: 'Geist Mono', monospace !important;
    color: #3d3d3d !important;
    font-size: .62rem !important;
    text-transform: uppercase !important;
    letter-spacing: .15em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Geist Mono', monospace !important;
    color: #f97316 !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
}

/* ── dataframe ── */
.stDataFrame {
    border: 1px solid #1c1c1c !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── expander ── */
.streamlit-expanderHeader {
    background: #0d0d0d !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 8px !important;
    color: #737373 !important;
    font-size: .85rem !important;
    transition: all .15s !important;
}
.streamlit-expanderHeader:hover {
    border-color: #333333 !important;
    color: #d4d4d4 !important;
}
.streamlit-expanderContent {
    background: #0a0a0a !important;
    border: 1px solid #1c1c1c !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── alerts ── */
.stInfo {
    background: #0d0d0d !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 8px !important;
    color: #737373 !important;
    font-size: .83rem !important;
}
.stWarning {
    background: #100e00 !important;
    border: 1px solid #2d2500 !important;
    border-radius: 8px !important;
    color: #a3a3a3 !important;
    font-size: .83rem !important;
}
.stSuccess {
    background: #081008 !important;
    border: 1px solid #1a2e1a !important;
    border-radius: 8px !important;
}
.stError {
    background: #100808 !important;
    border: 1px solid #2e1a1a !important;
    border-radius: 8px !important;
}

/* ── progress bar ── */
.stProgress > div > div {
    background: #f97316 !important;
    border-radius: 1px !important;
}
.stProgress > div {
    background: #1c1c1c !important;
    border-radius: 1px !important;
    height: 2px !important;
}

/* ── download button ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 7px !important;
    color: #525252 !important;
    font-size: .81rem !important;
    width: 100% !important;
    transition: all .15s !important;
}
.stDownloadButton > button:hover {
    border-color: #333333 !important;
    color: #a3a3a3 !important;
    background: #111111 !important;
}

hr { border-color: #1c1c1c !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────
now   = datetime.now()
ts    = now.strftime('%d %b %Y')
time_s = now.strftime('%H:%M')

st.markdown(''.join([
    '<div style="'
        'padding:36px 0 32px;'
        'margin:0 0 8px;'
        'border-bottom:1px solid #141414;'
    '">',

    '<div style="display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:16px;">',

    # ── left: title block
    '<div>',
    '<div style="'
        'font-family:\'Geist Mono\',monospace;'
        'font-size:.62rem;'
        'letter-spacing:.25em;'
        'color:#3d3d3d;'
        'text-transform:uppercase;'
        'margin-bottom:8px;'
    '">IDX / STOCK SCREENER</div>',
    '<h1 style="'
        'font-family:\'Geist Mono\',monospace;'
        'font-size:1.85rem;'
        'font-weight:600;'
        'letter-spacing:-.01em;'
        'color:#ffffff;'
        'margin:0 0 6px;'
        'line-height:1;'
    '">Radar Aksara</h1>',
    '<p style="'
        'font-size:.8rem;'
        'color:#404040;'
        'margin:0;'
        'letter-spacing:.02em;'
    '">Indonesian market pattern & float scanner</p>',
    '</div>',

    # ── right: live badge + date
    '<div style="display:flex;align-items:center;gap:16px;">',
    '<div style="text-align:right;">',
    '<div style="font-family:\'Geist Mono\',monospace;font-size:.65rem;color:#2d2d2d;letter-spacing:.1em;">' + ts + '</div>',
    '<div style="font-family:\'Geist Mono\',monospace;font-size:.75rem;color:#3d3d3d;margin-top:1px;">' + time_s + ' WIB</div>',
    '</div>',
    '<div style="'
        'display:flex;align-items:center;gap:6px;'
        'background:#0d0d0d;'
        'border:1px solid #1c1c1c;'
        'border-radius:6px;'
        'padding:6px 12px;'
    '">',
    '<div style="width:5px;height:5px;border-radius:50%;background:#22c55e;box-shadow:0 0 5px #22c55e;"></div>',
    '<span style="font-family:\'Geist Mono\',monospace;font-size:.65rem;color:#525252;letter-spacing:.1em;">LIVE</span>',
    '</div>',
    '</div>',

    '</div>',  # close flex
    '</div>',  # close header
]), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="padding:28px 0 20px;">'
            '<div style="font-family:\'Geist Mono\',monospace;font-size:.6rem;letter-spacing:.2em;color:#2d2d2d;text-transform:uppercase;margin-bottom:16px;">Navigation</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    scan_mode = st.radio("Mode", ["📈 Open = Low", "🔍 Low Float"], index=0)
    st.markdown("---")

    st.markdown('<div style="font-family:\'Geist Mono\',monospace;font-size:.6rem;letter-spacing:.2em;color:#2d2d2d;text-transform:uppercase;margin-bottom:12px;">Filter</div>', unsafe_allow_html=True)
    filter_type    = st.radio("Pilih saham", ["Semua","Manual","Tingkatan"], index=0)
    selected_stocks, selected_levels = [], []
    if filter_type == "Manual":
        selected_stocks = st.multiselect("Saham", options=STOCKS_LIST, default=[])
    elif filter_type == "Tingkatan":
        selected_levels = st.multiselect(
            "Tingkatan",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
        )
        if selected_levels:
            cnt = len(stocks_by_level(selected_levels))
            st.info(str(cnt) + " saham · ~" + str(round(cnt * 0.5 / 60, 1)) + " menit")

    st.markdown("---")
    st.markdown('<div style="font-family:\'Geist Mono\',monospace;font-size:.6rem;letter-spacing:.2em;color:#2d2d2d;text-transform:uppercase;margin-bottom:12px;">Legenda</div>', unsafe_allow_html=True)
    for ico, lbl, desc in [("💎","Blue Chip","> Rp10T"), ("📈","Second Liner","Rp500M–Rp10T"), ("🎯","Third Liner","< Rp1T"), ("⚠️","FCA","Papan Pemantauan")]:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid #111111;">'
                '<span>' + ico + '</span>'
                '<div>'
                    '<div style="font-size:.8rem;color:#525252;">' + lbl + '</div>'
                    '<div style="font-size:.68rem;color:#2d2d2d;">' + desc + '</div>'
                '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div style="font-family:\'Geist Mono\',monospace;font-size:.58rem;color:#1c1c1c;letter-spacing:.1em;text-align:center;padding-top:4px;">'
            'RADAR AKSARA · IDX'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────
def make_bar_chart(df, x_col, y_col, color_col):
    fig = go.Figure(go.Bar(
        x=df[x_col],
        y=df[y_col],
        marker=dict(
            color=df[color_col],
            colorscale=[[0, '#1c1c1c'], [0.4, '#7c2d12'], [1, '#f97316']],
            line=dict(color='#1c1c1c', width=1),
        ),
        hovertemplate='<b>%{x}</b><br>' + y_col + ': %{y}<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Geist Mono', color='#3d3d3d', size=11),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#525252', size=10), linecolor='#1c1c1c'),
        yaxis=dict(showgrid=True, gridcolor='#141414', zeroline=False, tickfont=dict(color='#525252', size=10)),
        margin=dict(l=4, r=4, t=8, b=4),
        height=300,
    )
    return fig


# ─────────────────────────────────────────────────────────
# OPEN = LOW SCANNER
# ─────────────────────────────────────────────────────────
if "Open = Low" in scan_mode:
    section_label("Open = Low Scanner", "— pola Open sama dengan Low + kenaikan ≥ target")

    c1, c2, c3 = st.columns(3)
    with c1: periode = st.selectbox("Periode", ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with c2: min_nk  = st.slider("Min Kenaikan (%)", 1, 20, 5)
    with c3: lmt     = st.number_input("Limit Hasil", 5, 100, 20)

    section_label("Mode")
    ma, mb = st.columns(2)
    with ma:
        mode = st.radio("Kecepatan", ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua)"], index=0, horizontal=True)
    with mb:
        st.markdown(
            '<div style="background:#0d0d0d;border:1px solid #1c1c1c;border-radius:8px;padding:14px 18px;">'
                '<div style="font-family:\'Geist Mono\',monospace;font-size:.6rem;letter-spacing:.15em;color:#2d2d2d;margin-bottom:10px;">ESTIMASI</div>'
                '<div style="display:flex;gap:28px;">'
                    '<div>'
                        '<div style="font-family:\'Geist Mono\',monospace;font-size:.72rem;color:#f97316;">⚡ CEPAT</div>'
                        '<div style="font-size:.82rem;color:#525252;margin-top:3px;">~30 detik</div>'
                    '</div>'
                    '<div>'
                        '<div style="font-family:\'Geist Mono\',monospace;font-size:.72rem;color:#525252;">🐢 LENGKAP</div>'
                        '<div style="font-size:.82rem;color:#404040;margin-top:3px;">~7–10 menit</div>'
                    '</div>'
                '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    pm = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("Mulai Scanning", type="primary", use_container_width=True):
        if filter_type == "Manual" and selected_stocks:      s2s = selected_stocks
        elif filter_type == "Tingkatan" and selected_levels: s2s = stocks_by_level(selected_levels)
        else: s2s = STOCKS_LIST[:50] if "Cepat" in mode else STOCKS_LIST

        est = len(s2s) * 0.5
        if est / 60 > 2: st.warning("Memproses " + str(len(s2s)) + " saham · ~" + str(round(est / 60, 1)) + " menit · Jangan refresh halaman")
        else:            st.info("Memproses " + str(len(s2s)) + " saham · ~" + str(round(est)) + " detik")

        pg   = st.progress(0)
        slot = st.empty()
        res  = []
        t0   = time.time()

        for i, stk in enumerate(s2s):
            el  = time.time() - t0
            rem = (el / (i + 1)) * (len(s2s) - i - 1) if i > 0 else 0
            slot.markdown(html_scan_progress(stk, i, len(s2s), el, rem), unsafe_allow_html=True)
            r = scan_open_low_pattern(stk, periode_hari=pm[periode], min_kenaikan=min_nk)
            if r: res.append(r)
            pg.progress((i + 1) / len(s2s))
            time.sleep(0.3)

        pg.empty(); slot.empty()
        tt = time.time() - t0

        if res:
            df = pd.DataFrame(res).sort_values('frekuensi', ascending=False).head(lmt)
            st.markdown(html_result_banner(len(df), tt, periode, min_nk), unsafe_allow_html=True)

            section_label("Hasil", "— tabel lengkap dengan free float & tingkatan")
            rows = []
            for _, row in df.iterrows():
                s  = row['saham']
                ff = ff_val(s)
                h  = ff_holders(s)
                ti = sum((p['persen'] / ff * 100) for p in h if ff > 0)
                rows.append({
                    'Saham':  s,
                    'Level':  stock_level(s),
                    'Frek':   row['frekuensi'],
                    'Prob':   str(round(row['probabilitas'])) + '%',
                    'Gain':   str(round(row['rata_rata_kenaikan'])) + '%',
                    'FF':     str(round(ff)) + '%',
                    'Inst':   str(round(ti)) + '%',
                    'Ritel':  str(round(100 - ti)) + '%',
                    'FCA':    '⚠' if is_fca(s) else '',
                    'Pot':    goreng(ff),
                })
            edf = pd.DataFrame(rows)
            st.dataframe(edf, use_container_width=True, height=420, hide_index=True)

            section_label("Top 10", "— frekuensi pola")
            st.plotly_chart(make_bar_chart(df.head(10), 'saham', 'frekuensi', 'probabilitas'), use_container_width=True)

            section_label("Analisis AI", "— breakdown top 5")
            for _, row in df.head(5).iterrows():
                analysis = analyze_pattern(row.to_dict())
                label = (
                    "**" + row['saham'] + "**  ·  " +
                    stock_level(row['saham']) + "  ·  " +
                    "Prob " + str(round(row['probabilitas'], 1)) + "%  ·  " +
                    "Gain " + str(round(row['rata_rata_kenaikan'], 1)) + "%"
                )
                with st.expander(label):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Probabilitas",  str(round(row['probabilitas'], 1))       + "%")
                    c2.metric("Rata Gain",     str(round(row['rata_rata_kenaikan'], 1)) + "%")
                    c3.metric("Max Gain",      str(round(row['max_kenaikan'], 1))       + "%")
                    c4.metric("Frekuensi",     str(row['frekuensi'])                    + "x")
                    st.markdown(
                        '<div style="font-size:.84rem;color:#737373;line-height:1.75;padding:14px 0;border-top:1px solid #141414;margin-top:8px;">'
                        + analysis +
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(html_ff_card(row['saham']), unsafe_allow_html=True)

            section_label("Watchlist", "— saham prioritas untuk besok")
            wc1, wc2 = st.columns(2)
            with wc1: mg = st.slider("Min Gain (%)", 3, 10, 5, key="mg")
            with wc2: tn = st.number_input("Jumlah", 5, 30, 15, key="tn")

            dfw = df[df['rata_rata_kenaikan'] >= mg].copy()
            if not dfw.empty:
                mx_p, mx_g = dfw['probabilitas'].max(), dfw['rata_rata_kenaikan'].max()
                if mx_p > 0 and mx_g > 0:
                    dfw['skor'] = (dfw['probabilitas'] / mx_p) * 50 + (dfw['rata_rata_kenaikan'] / mx_g) * 50
                    dfw = dfw.nlargest(tn, 'skor')

                st.markdown(html_watchlist_header(datetime.now().strftime('%d %B %Y')), unsafe_allow_html=True)

                wl = []
                for i, (_, row) in enumerate(dfw.iterrows()):
                    rk = (
                        "🔥 PRIORITAS" if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7
                        else "⚡ LAYAK"  if row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5
                        else "📌 PANTAU"
                    )
                    ff = ff_val(row['saham'])
                    wl.append({
                        "Rank":  i + 1,
                        "Saham": row['saham'],
                        "Lvl":   level_abbr(row['saham']),
                        "Prob":  str(round(row['probabilitas'])) + "%",
                        "Gain":  str(round(row['rata_rata_kenaikan'])) + "%",
                        "FF":    str(round(ff)) + "%",
                        "FCA":   '⚠' if is_fca(row['saham']) else '',
                        "Pot":   goreng(ff),
                        "Rekom": rk,
                    })
                wdf = pd.DataFrame(wl)
                st.dataframe(wdf, use_container_width=True, hide_index=True, height=320)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        "↓ Export CSV", wdf.to_csv(index=False).encode(),
                        "watchlist_" + datetime.now().strftime('%Y%m%d') + ".csv",
                        "text/csv", use_container_width=True,
                    )
                with d2:
                    xl = export_to_excel(wdf)
                    if xl:
                        st.download_button(
                            "↓ Export Excel", xl,
                            "watchlist_" + datetime.now().strftime('%Y%m%d') + ".xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
            else:
                st.warning("Tidak ada saham dengan gain minimal " + str(mg) + "%")

            section_label("Export")
            e1, e2 = st.columns(2)
            with e1:
                st.download_button(
                    "↓ Export CSV", edf.to_csv(index=False).encode(),
                    "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True,
                )
            with e2:
                xl2 = export_to_excel(edf)
                if xl2:
                    st.download_button(
                        "↓ Export Excel", xl2,
                        "scan_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
        else:
            st.markdown(html_empty("Tidak ada saham yang memenuhi kriteria", "Coba ubah periode atau kurangi minimal kenaikan"), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# LOW FLOAT SCANNER
# ─────────────────────────────────────────────────────────
elif "Low Float" in scan_mode:
    section_label("Low Float Scanner", "— saham dengan free float rendah & volatilitas tinggi")

    lf1, lf2 = st.columns(2)
    with lf1: max_ff  = st.slider("Maks Free Float (%)", 1, 50, 20)
    with lf2: min_vol = st.number_input("Min Volume Harian", 0, value=0, step=100000)

    section_label("Filter Tingkatan")
    fc1, fc2, fc3 = st.columns(3)
    with fc1: sb    = st.checkbox("💎 Blue Chip",    value=True)
    with fc2: ss    = st.checkbox("📈 Second Liner", value=True)
    with fc3: st_cb = st.checkbox("🎯 Third Liner",  value=True)

    scan_lf = st.radio("Mode", ["⚡ Cepat", "🐢 Lengkap"], horizontal=True, index=0)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("Scan Low Float", type="primary", use_container_width=True):
        lv  = (["Blue Chip"] if sb else []) + (["Second Liner"] if ss else []) + (["Third Liner"] if st_cb else [])
        if selected_stocks:               s2s = selected_stocks
        elif lv:                          s2s = stocks_by_level(lv)
        else: s2s = STOCKS_LIST[:50] if "Cepat" in scan_lf else STOCKS_LIST

        with st.spinner("Scanning " + str(len(s2s)) + " saham..."):
            res = scan_low_float(s2s, max_ff, min_vol)

        if res:
            df = pd.DataFrame(res)

            st.markdown(''.join([
                '<div style="background:#0d0d0d;border:1px solid #1c1c1c;border-left:2px solid #22c55e;border-radius:10px;padding:20px 24px;margin:18px 0;">',
                '<div style="font-family:\'Geist Mono\',monospace;font-size:.6rem;letter-spacing:.15em;color:#2d2d2d;margin-bottom:6px;">SCAN SELESAI</div>',
                '<div style="display:flex;align-items:baseline;gap:10px;">',
                '<span style="font-family:\'Geist Mono\',monospace;font-size:2.2rem;font-weight:600;color:#ffffff;">' + str(len(df)) + '</span>',
                '<span style="font-size:.82rem;color:#525252;">saham dengan FF &lt; ' + str(max_ff) + '%</span>',
                '</div>',
                '</div>',
            ]), unsafe_allow_html=True)

            section_label("Hasil", "— komposisi pemegang & potensi goreng")
            enr = []
            for _, row in df.iterrows():
                s  = row['saham']
                ff = ff_val(s)
                h  = ff_holders(s)
                ti = sum((p['persen'] / ff * 100) for p in h if ff > 0)
                enr.append({
                    'Saham': s, 'Lvl': level_abbr(s),
                    'FF':    str(round(ff)) + '%',
                    'Kat':   kat_abbr(row['category']),
                    'Vol(M)': str(round(row['volume_avg'] / 1e6, 1)),
                    'Volat': str(round(row['volatility'])) + '%',
                    'Inst':  str(round(ti)) + '%',
                    'Ritel': str(round(100 - ti)) + '%',
                    'FCA':   '⚠' if is_fca(s) else '',
                    'Pot':   goreng(ff),
                })
            enr_df = pd.DataFrame(enr)
            st.dataframe(enr_df, use_container_width=True, height=420, hide_index=True)

            section_label("Detail Free Float", "— breakdown top 5")
            for _, row in df.head(5).iterrows():
                ff = ff_val(row['saham'])
                with st.expander("**" + row['saham'] + "**  ·  " + stock_level(row['saham']) + "  ·  FF " + str(round(ff)) + "%"):
                    st.markdown(html_ff_card(row['saham']), unsafe_allow_html=True)

            section_label("Distribusi")
            vc1, vc2 = st.columns(2)
            with vc1:
                cv = df['category'].value_counts()
                fig_pie = go.Figure(go.Pie(
                    labels=cv.index, values=cv.values, hole=0.65,
                    marker=dict(
                        colors=['#f97316','#3b82f6','#8b5cf6','#ef4444','#22c55e'],
                        line=dict(color='#080808', width=2),
                    ),
                    textfont=dict(color='#737373', size=10),
                ))
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Geist Mono', color='#3d3d3d'),
                    legend=dict(font=dict(color='#525252', size=9), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=0, r=0, t=8, b=0), height=260,
                    annotations=[dict(text='FF', x=0.5, y=0.5, font_size=11, showarrow=False, font_color='#2d2d2d')]
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            with vc2:
                fig_sc = go.Figure(go.Scatter(
                    x=df['public_float'], y=df['volatility'], mode='markers',
                    marker=dict(
                        size=[max(5, v / 1e6 * 0.35) for v in df['volume_avg']],
                        color=df['volatility'],
                        colorscale=[[0, '#1c1c1c'], [0.5, '#7c2d12'], [1, '#f97316']],
                        line=dict(color='#1c1c1c', width=1),
                        sizemode='area', sizeref=1.5, showscale=False,
                    ),
                    text=df['saham'],
                    hovertemplate='<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>',
                ))
                fig_sc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Geist Mono', color='#3d3d3d', size=10),
                    xaxis=dict(title='Free Float (%)', showgrid=True, gridcolor='#141414', zeroline=False, tickfont=dict(color='#525252')),
                    yaxis=dict(title='Volatilitas (%)', showgrid=True, gridcolor='#141414', zeroline=False, tickfont=dict(color='#525252')),
                    margin=dict(l=8, r=8, t=8, b=8), height=260,
                )
                st.plotly_chart(fig_sc, use_container_width=True)

            section_label("Export")
            xe1, xe2 = st.columns(2)
            with xe1:
                st.download_button(
                    "↓ Export CSV", enr_df.to_csv(index=False).encode(),
                    "lowfloat_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
                    "text/csv", use_container_width=True,
                )
            with xe2:
                xl3 = export_to_excel(enr_df)
                if xl3:
                    st.download_button(
                        "↓ Export Excel", xl3,
                        "lowfloat_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
        else:
            st.markdown(html_empty("Tidak ada saham yang memenuhi kriteria", "Coba naikkan batas maksimal free float"), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────
st.markdown(''.join([
    '<div style="border-top:1px solid #141414;padding:16px 0 8px;margin-top:40px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">',
    '<span style="font-family:\'Geist Mono\',monospace;font-size:.62rem;color:#1c1c1c;letter-spacing:.1em;">Radar Aksara · IDX Scanner</span>',
    '<div style="display:flex;gap:20px;flex-wrap:wrap;">',
    '<span style="font-size:.67rem;color:#1c1c1c;">BC=Blue Chip · SL=Second Liner · TL=Third Liner</span>',
    '<span style="font-size:.67rem;color:#1c1c1c;">FF=Free Float · FCA=Full Call Auction</span>',
    '<span style="font-size:.67rem;color:#1c1c1c;">Data edukasi — bukan rekomendasi investasi</span>',
    '</div>',
    '</div>',
]), unsafe_allow_html=True)
