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

# ========== DATA TINGKATAN SAHAM ==========
BLUE_CHIP_STOCKS = [
    'BBCA', 'BBRI', 'BMRI', 'BBNI', 'BTPS', 'BRIS',
    'TLKM', 'ISAT', 'EXCL', 'TOWR', 'MTEL',
    'UNVR', 'ICBP', 'INDF', 'KLBF', 'GGRM', 'HMSP',
    'ASII', 'UNTR', 'ADRO', 'BYAN', 'PTBA', 'ITMG',
    'CPIN', 'JPFA', 'MAIN', 'SIDO', 'ULTJ',
    'SMGR', 'INTP', 'SMCB',
    'PGAS', 'MEDC', 'ELSA',
    'ANTM', 'INCO', 'MDKA', 'HRUM', 'BRPT', 'TPIA',
    'WIKA', 'PTPP', 'WSKT', 'ADHI', 'JSMR', 'TLKM',
]

SECOND_LINER_STOCKS = [
    'AKRA', 'INKP', 'BUMI', 'PTRO', 'DOID', 'TINS', 'BRMS', 'DKFT',
    'BMTR', 'MAPI', 'ERAA', 'ACES', 'MIKA', 'SILO', 'HEAL', 'PRAY',
    'CLEO', 'ROTI', 'MYOR', 'GOOD', 'SKBM', 'SKLT', 'STTP',
    'WSBP', 'PBSA', 'MTFN', 'BKSL', 'SMRA', 'CTRA', 'BSDE', 'PWON',
    'LPKR', 'LPCK', 'DILD', 'RDTX', 'MREI', 'PZZA', 'MAPB', 'DMAS',
    'LMPI', 'ARNA', 'TOTO', 'MLIA', 'INTD', 'IKAI', 'JECC', 'KBLI',
    'KBLM', 'VOKS', 'UNIT', 'INAI', 'IMPC', 'ASGR', 'POWR', 'RAJA',
    'PJAA', 'SAME', 'SCCO', 'SPMA', 'SRSN', 'TALF', 'TRST', 'TSPC',
    'UNIC', 'YPAS',
]

def get_stock_level(stock_code):
    if stock_code in BLUE_CHIP_STOCKS:
        return '💎 Blue Chip'
    elif stock_code in SECOND_LINER_STOCKS:
        return '📈 Second Liner'
    else:
        return '🎯 Third Liner'

def get_stocks_by_level(levels):
    result = []
    if 'Blue Chip' in levels:
        result += BLUE_CHIP_STOCKS
    if 'Second Liner' in levels:
        result += SECOND_LINER_STOCKS
    if 'Third Liner' in levels or len(levels) == 0:
        third_liner = [s for s in STOCKS_LIST if s not in BLUE_CHIP_STOCKS and s not in SECOND_LINER_STOCKS]
        result += third_liner
    return list(set(result))

# ========== DATA PEMEGANG SAHAM ==========
SHAREHOLDER_DATA = {
    'CUAN': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.02, 'tipe': 'Institusi', 'catatan': 'Masuk Q4 2025', 'update': 'Feb 2026'},
            {'nama': 'Vanguard', 'persen': 1.15, 'tipe': 'Asing', 'catatan': 'Nambah Jan 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 13.73, 'total_shares': 12345678900,
        'insider_activity': [
            {'tanggal': '05 Mar 2026', 'insider': 'Direktur Utama', 'aksi': 'BELI', 'jumlah': 100000, 'harga': 15000},
            {'tanggal': '20 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 50000, 'harga': 14800}
        ]
    },
    'BRPT': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.22, 'tipe': 'Institusi', 'catatan': 'Nambah Feb 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 27.41, 'total_shares': 8765432100,
        'insider_activity': [{'tanggal': '28 Feb 2026', 'insider': 'Komisaris', 'aksi': 'JUAL', 'jumlah': 75000, 'harga': 8500}]
    },
    'TPIA': {
        'pemegang': [{'nama': 'GIC Singapore', 'persen': 3.45, 'tipe': 'Asing', 'catatan': 'Masuk Jan 2026', 'update': 'Feb 2026'}],
        'free_float': 91.52, 'total_shares': 1122334455, 'insider_activity': []
    },
    'TRIM': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah Des 2025', 'update': 'Feb 2026'}],
        'free_float': 63.17, 'total_shares': 9988776655, 'insider_activity': []
    },
    'MDKA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'Pemerintah Norwegia', 'persen': 1.08, 'tipe': 'Asing', 'catatan': 'Masuk Q1 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 89.31, 'total_shares': 8877665544,
        'insider_activity': [{'tanggal': '15 Feb 2026', 'insider': 'Dirut', 'aksi': 'BELI', 'jumlah': 200000, 'harga': 2500}]
    },
    'BBCA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.06, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'Vanguard', 'persen': 1.23, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 95.67, 'total_shares': 123456789000,
        'insider_activity': [
            {'tanggal': '10 Mar 2026', 'insider': 'Presdir', 'aksi': 'BELI', 'jumlah': 1000000, 'harga': 10250},
            {'tanggal': '25 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 500000, 'harga': 10100}
        ]
    },
    'INDF': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 3.74, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 92.52, 'total_shares': 8765432100, 'insider_activity': []
    },
    'CBDK': {
        'pemegang': [], 'free_float': 99.07, 'total_shares': 1122334455,
        'insider_activity': [{'tanggal': '18 Feb 2026', 'insider': 'Grup Salim', 'aksi': 'JUAL', 'jumlah': 50000000, 'harga': 1500}]
    },
    'BYAN': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.33, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 58.45, 'total_shares': 10000000000, 'insider_activity': []
    },
    'BHIT': {'pemegang': [], 'free_float': 96.88, 'total_shares': 5566778899, 'insider_activity': []},
    'MAYA': {'pemegang': [], 'free_float': 80.66, 'total_shares': 4455667788, 'insider_activity': []},
    'AALI': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 2.18, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 97.82, 'total_shares': 3344556677, 'insider_activity': []
    },
    'ASII': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 2.74, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 97.26, 'total_shares': 9988776655, 'insider_activity': []
    },
    'BBNI': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 3.51, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 96.49, 'total_shares': 8877665544, 'insider_activity': []
    },
    'BBRI': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.09, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 98.91, 'total_shares': 123456789000,
        'insider_activity': [{'tanggal': '09 Mar 2026', 'insider': 'Dirut', 'aksi': 'JUAL', 'jumlah': 50000, 'harga': 5800}]
    },
    'AKRA': {
        'pemegang': [{'nama': 'Pemerintah Norwegia', 'persen': 3.03, 'tipe': 'Asing', 'catatan': 'Aktif nambah', 'update': 'Feb 2026'}],
        'free_float': 96.97, 'total_shares': 4455667788, 'insider_activity': []
    },
    'KLBF': {
        'pemegang': [
            {'nama': 'Pemerintah Norwegia', 'persen': 1.30, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.01, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 96.69, 'total_shares': 5566778899, 'insider_activity': []
    },
    'ARTO': {
        'pemegang': [{'nama': 'Pemerintah Singapura', 'persen': 8.28, 'tipe': 'Asing', 'catatan': 'Masuk besar', 'update': 'Feb 2026'}],
        'free_float': 91.72, 'total_shares': 1122334455, 'insider_activity': []
    },
    'MTEL': {
        'pemegang': [{'nama': 'Pemerintah Singapura', 'persen': 5.33, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 94.67, 'total_shares': 2233445566, 'insider_activity': []
    }
}

FCA_STOCKS = ['COIN', 'CDIA']

def is_fca(stock_code):
    return stock_code in FCA_STOCKS

def get_free_float_holders(stock_code):
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('pemegang', [])

def get_free_float_value(stock_code):
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('free_float', 100.0)

def get_insider_activity(stock_code):
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('insider_activity', [])

def display_free_float_info(stock_code, free_float_value):
    free_float_holders = get_free_float_holders(stock_code)
    
    html = f"""
    <div style='background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                padding: 18px; border-radius: 12px; margin: 12px 0;
                border: 1px solid #21262d; box-shadow: 0 4px 20px rgba(0,0,0,0.4);'>
        <div style='display:flex; align-items:center; gap:10px; margin-bottom:14px;'>
            <div style='width:4px; height:24px; background: linear-gradient(180deg, #f0b429, #e88c0e); border-radius:2px;'></div>
            <h4 style='color:#f0b429; margin:0; font-family: "Courier New", monospace; font-size:0.95rem; letter-spacing:1px;'>
                FREE FLOAT COMPOSITION — {stock_code}
            </h4>
        </div>
    """
    
    if is_fca(stock_code):
        html += """<div style='background: rgba(255,170,0,0.1); border: 1px solid rgba(255,170,0,0.4);
                               padding: 6px 12px; border-radius: 6px; margin-bottom: 10px;'>
                      <span style='color:#ffaa00; font-size:0.82rem; font-family: "Courier New", monospace;'>
                          ⚠️ FCA — PAPAN PEMANTAUAN KHUSUS
                      </span>
                   </div>"""
    
    html += f"""
        <div style='display:flex; justify-content:space-between; align-items:center;
                    background: rgba(0,255,136,0.07); border: 1px solid rgba(0,255,136,0.2);
                    padding: 10px 14px; border-radius: 8px; margin-bottom: 12px;'>
            <span style='color:#8b949e; font-size:0.85rem;'>Free Float Total</span>
            <span style='color:#00ff88; font-weight:700; font-size:1.1rem; font-family: "Courier New", monospace;'>{free_float_value:.2f}%</span>
        </div>
    """
    
    if free_float_holders:
        total_dari_ff = 0
        holder_html = ""
        
        for p in free_float_holders:
            persen_dalam_ff = (p['persen'] / free_float_value) * 100
            total_dari_ff += persen_dalam_ff
            bar_width = min(persen_dalam_ff * 2, 100)
            warna = '#58a6ff' if p['tipe'] == 'Institusi' else '#3fb950'
            
            holder_html += f"""
            <div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                        padding: 10px 12px; border-radius: 8px; margin: 5px 0;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                    <div style='display:flex; align-items:center; gap:8px;'>
                        <span style='width:8px; height:8px; border-radius:50%; background:{warna}; display:inline-block;'></span>
                        <span style='color:#e6edf3; font-size:0.84rem;'>{p['nama']}</span>
                        <span style='color:#484f58; font-size:0.75rem; background:rgba(255,255,255,0.05);
                                     padding:1px 6px; border-radius:10px;'>{p['tipe']}</span>
                    </div>
                    <span style='color:{warna}; font-weight:700; font-family:"Courier New",monospace; font-size:0.9rem;'>{persen_dalam_ff:.1f}%</span>
                </div>
                <div style='height:3px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden;'>
                    <div style='width:{bar_width}%; height:100%; background:{warna}; border-radius:2px;
                                transition: width 0.5s ease;'></div>
                </div>
            </div>
            """
        
        sisa_ritel = 100 - total_dari_ff
        bar_ritel = min(sisa_ritel * 0.6, 100)
        
        html += holder_html
        html += f"""
        <div style='background: rgba(0,255,136,0.05); border: 1px solid rgba(0,255,136,0.15);
                    padding: 10px 12px; border-radius: 8px; margin: 5px 0;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                <div style='display:flex; align-items:center; gap:8px;'>
                    <span style='width:8px; height:8px; border-radius:50%; background:#00ff88; display:inline-block;'></span>
                    <span style='color:#e6edf3; font-size:0.84rem;'>Ritel</span>
                </div>
                <span style='color:#00ff88; font-weight:700; font-family:"Courier New",monospace; font-size:0.9rem;'>{sisa_ritel:.1f}%</span>
            </div>
            <div style='height:3px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden;'>
                <div style='width:{bar_ritel}%; height:100%; background:#00ff88; border-radius:2px;'></div>
            </div>
        </div>
        """
    else:
        html += """
        <div style='background: rgba(0,255,136,0.05); border: 1px solid rgba(0,255,136,0.15);
                    padding: 10px 12px; border-radius: 8px; margin: 5px 0;'>
            <div style='display:flex; justify-content:space-between;'>
                <span style='color:#8b949e; font-size:0.84rem;'>Tidak ada institusi/asing &gt;1%</span>
                <span style='color:#00ff88; font-weight:700; font-family:"Courier New",monospace;'>Ritel 100%</span>
            </div>
        </div>
        """
    
    insider = get_insider_activity(stock_code)
    if insider:
        html += """<div style='margin-top:14px; margin-bottom:8px;'>
                      <span style='color:#8b949e; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>
                          Aktivitas Insider 30 Hari
                      </span>
                   </div>"""
        for a in insider:
            warna_aksi = '#3fb950' if a['aksi'] == 'BELI' else '#f85149'
            bg_aksi = 'rgba(63,185,80,0.07)' if a['aksi'] == 'BELI' else 'rgba(248,81,73,0.07)'
            border_aksi = 'rgba(63,185,80,0.2)' if a['aksi'] == 'BELI' else 'rgba(248,81,73,0.2)'
            html += f"""
            <div style='display:flex; justify-content:space-between; align-items:center;
                        background:{bg_aksi}; border:1px solid {border_aksi};
                        padding:8px 12px; border-radius:8px; margin:4px 0;'>
                <span style='color:#8b949e; font-size:0.82rem; font-family:"Courier New",monospace;'>{a['tanggal']}</span>
                <span style='color:#e6edf3; font-size:0.82rem;'>{a['insider']}</span>
                <span style='color:{warna_aksi}; font-weight:700; font-size:0.85rem; font-family:"Courier New",monospace;'>
                    {a['aksi']} {a['jumlah']:,}
                </span>
            </div>
            """
    
    html += "</div>"
    return html

def get_kategori_singkatan(kategori):
    singkatan = {
        'Ultra Low Float': 'ULF', 'Very Low Float': 'VLF',
        'Low Float': 'LF', 'Moderate Low Float': 'MLF', 'Normal Float': 'NF'
    }
    return singkatan.get(kategori, kategori)

def analyze_goreng_potential(free_float):
    if free_float < 10:
        return '🔥 UT'
    elif free_float < 15:
        return '🔥 ST'
    elif free_float < 25:
        return '⚡ TG'
    elif free_float < 40:
        return '📊 SD'
    else:
        return '📉 RD'

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="StockRadar ID",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== MASTER CSS ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;500;600;700&display=swap');

    /* ── Global Reset & Base ── */
    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
    }
    .stApp {
        background: #0a0e17;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0a0e17 100%) !important;
        border-right: 1px solid #1c2230 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #f0b429 !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 0.9rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #8b949e !important;
        font-size: 0.78rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        margin-top: 1.2rem !important;
    }
    [data-testid="stSidebar"] label {
        color: #c9d1d9 !important;
        font-size: 0.84rem !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #8b949e !important;
        font-size: 0.83rem !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1c2230 !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #484f58 !important;
        font-size: 0.75rem !important;
    }
    [data-testid="stSidebar"] .stInfo {
        background: rgba(88, 166, 255, 0.06) !important;
        border: 1px solid rgba(88, 166, 255, 0.15) !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
    }

    /* ── Radio Buttons ── */
    .stRadio [data-testid="stWidgetLabel"] {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
    }
    div[role="radiogroup"] label {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid #21262d !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        color: #8b949e !important;
        transition: all 0.2s !important;
        font-size: 0.84rem !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #f0b429 !important;
        color: #f0b429 !important;
        background: rgba(240,180,41,0.05) !important;
    }

    /* ── Primary Button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #f0b429 0%, #e88c0e 100%) !important;
        color: #0a0e17 !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 2px !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 2rem !important;
        box-shadow: 0 4px 20px rgba(240,180,41,0.3) !important;
        transition: all 0.3s !important;
        text-transform: uppercase !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 28px rgba(240,180,41,0.5) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* ── Secondary Button ── */
    .stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.03) !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-size: 0.84rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #58a6ff !important;
        color: #58a6ff !important;
    }

    /* ── Selectbox / Multiselect ── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #c9d1d9 !important;
    }
    .stSelectbox > div > div:hover,
    .stMultiSelect > div > div:hover {
        border-color: #58a6ff !important;
    }
    .stSelectbox label, .stMultiSelect label {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* ── Slider ── */
    .stSlider [data-testid="stWidgetLabel"] {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .stSlider .st-be { background: #1c2230 !important; }
    .stSlider .st-bf { background: #f0b429 !important; }

    /* ── Number Input ── */
    .stNumberInput label {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .stNumberInput input {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #c9d1d9 !important;
    }

    /* ── Checkbox ── */
    .stCheckbox label {
        color: #c9d1d9 !important;
        font-size: 0.85rem !important;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border: 1px solid #1c2230 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: #0d1117 !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid #21262d !important;
        border-radius: 10px !important;
        color: #c9d1d9 !important;
        font-size: 0.88rem !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #f0b429 !important;
        color: #f0b429 !important;
    }
    .streamlit-expanderContent {
        background: rgba(13,17,23,0.8) !important;
        border: 1px solid #21262d !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid #21262d !important;
        border-radius: 10px !important;
        padding: 14px !important;
    }
    [data-testid="metric-container"] label {
        color: #8b949e !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f0b429 !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 1.6rem !important;
    }

    /* ── Alerts ── */
    .stInfo {
        background: rgba(88,166,255,0.06) !important;
        border: 1px solid rgba(88,166,255,0.2) !important;
        border-radius: 8px !important;
        color: #8b949e !important;
        font-size: 0.84rem !important;
    }
    .stWarning {
        background: rgba(240,180,41,0.06) !important;
        border: 1px solid rgba(240,180,41,0.25) !important;
        border-radius: 8px !important;
        color: #c9d1d9 !important;
        font-size: 0.84rem !important;
    }
    .stSuccess {
        background: rgba(63,185,80,0.06) !important;
        border: 1px solid rgba(63,185,80,0.2) !important;
        border-radius: 8px !important;
    }
    .stError {
        background: rgba(248,81,73,0.06) !important;
        border: 1px solid rgba(248,81,73,0.2) !important;
        border-radius: 8px !important;
    }

    /* ── Progress Bar ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #f0b429, #e88c0e) !important;
        border-radius: 3px !important;
    }
    .stProgress > div {
        background: #1c2230 !important;
        border-radius: 3px !important;
    }

    /* ── Download Button ── */
    .stDownloadButton > button {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #c9d1d9 !important;
        font-size: 0.84rem !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stDownloadButton > button:hover {
        border-color: #3fb950 !important;
        color: #3fb950 !important;
        background: rgba(63,185,80,0.05) !important;
    }

    /* ── Divider ── */
    hr { border-color: #1c2230 !important; margin: 1.2rem 0 !important; }

    /* ── Plotly charts dark bg ── */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown("""
<div style='
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #1c2230;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
'>
    <div style='
        position: absolute; top: 0; right: 0;
        width: 300px; height: 100%;
        background: radial-gradient(ellipse at top right, rgba(240,180,41,0.07) 0%, transparent 70%);
        pointer-events: none;
    '></div>
    <div style='display: flex; align-items: center; gap: 16px;'>
        <div style='
            width: 48px; height: 48px;
            background: linear-gradient(135deg, #f0b429, #e88c0e);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem;
            flex-shrink: 0;
        '>📡</div>
        <div>
            <div style='
                font-family: "Space Mono", monospace;
                font-size: 1.6rem;
                font-weight: 700;
                color: #f0f6fc;
                letter-spacing: 1px;
                line-height: 1.1;
            '>StockRadar <span style="color:#f0b429;">ID</span></div>
            <div style='color: #484f58; font-size: 0.82rem; margin-top: 4px; letter-spacing: 0.5px;'>
                Open=Low Pattern · Low Float Scanner · Blue Chip · Second Liner · Third Liner
            </div>
        </div>
        <div style='margin-left: auto; text-align: right;'>
            <div style='
                font-family: "Space Mono", monospace;
                color: #3fb950; font-size: 0.8rem; letter-spacing: 1px;
            '>● LIVE</div>
            <div style='color: #484f58; font-size: 0.75rem; margin-top: 2px;'>
""" + datetime.now().strftime('%d %b %Y') + """
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(240,180,41,0.08) 0%, transparent 100%);
        border: 1px solid rgba(240,180,41,0.15);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 16px;
    '>
        <div style='font-family:"Space Mono",monospace; color:#f0b429; font-size:0.75rem; letter-spacing:2px;'>
            ⚙ CONTROL PANEL
        </div>
    </div>
    """, unsafe_allow_html=True)

    scan_mode = st.radio(
        "MODE SCANNING",
        ["📈 Open = Low Scanner", "🔍 Low Float Scanner"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🎯 Filter Saham")
    
    filter_type = st.radio(
        "Tipe Filter",
        ["Semua Saham", "Pilih Manual", "Filter Tingkatan"],
        index=0
    )

    selected_stocks = []
    selected_levels = []

    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect("Pilih Saham", options=STOCKS_LIST, default=[])
    elif filter_type == "Filter Tingkatan":
        selected_levels = st.multiselect(
            "Pilih Tingkatan",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
            help="Blue Chip: > Rp10T | Second Liner: Rp500M-Rp10T | Third Liner: < Rp1T"
        )
        if selected_levels:
            stocks_count = len(get_stocks_by_level(selected_levels))
            est_time = stocks_count * 0.5 / 60
            st.info(f"**{stocks_count}** saham · ±{est_time:.1f} menit")

    st.markdown("---")

    st.markdown("""
    <div style='font-family:"Space Mono",monospace; color:#484f58; font-size:0.72rem; letter-spacing:1px; margin-bottom:8px;'>
        LEGENDA
    </div>
    """, unsafe_allow_html=True)

    legend_items = [
        ("💎", "Blue Chip", "> Rp10T"),
        ("📈", "Second Liner", "Rp500M–Rp10T"),
        ("🎯", "Third Liner", "< Rp1T"),
        ("⚠️", "FCA", "Papan Pemantauan"),
    ]
    for icon, label, desc in legend_items:
        st.markdown(f"""
        <div style='display:flex; align-items:center; gap:8px; padding:4px 0;'>
            <span>{icon}</span>
            <div>
                <div style='color:#c9d1d9; font-size:0.8rem;'>{label}</div>
                <div style='color:#484f58; font-size:0.72rem;'>{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; color:#30363d; font-size:0.72rem; font-family:"Space Mono",monospace;'>
        Made with ❤ for Indonesian Traders
    </div>
    """, unsafe_allow_html=True)


# ========= HELPER: SECTION HEADER =========
def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:12px; margin: 24px 0 16px 0;'>
        <div style='width:3px; height:20px; background:linear-gradient(180deg,#f0b429,#e88c0e); border-radius:2px;'></div>
        <div>
            <div style='color:#f0f6fc; font-size:1rem; font-weight:600; font-family:"Sora",sans-serif;'>{title}</div>
            {"<div style='color:#484f58; font-size:0.78rem; margin-top:2px;'>" + subtitle + "</div>" if subtitle else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# OPEN = LOW SCANNER
# ============================================================
if "Open = Low" in scan_mode:

    section_header("Open = Low Scanner", "Deteksi pola Open sama dengan Low + kenaikan ≥ target")

    col1, col2, col3 = st.columns(3)
    with col1:
        periode = st.selectbox("Periode Analisis", ["7 Hari","14 Hari","30 Hari","90 Hari","180 Hari","365 Hari"], index=2)
    with col2:
        min_kenaikan = st.slider("Minimal Kenaikan (%)", 1, 20, 5)
    with col3:
        limit_saham = st.number_input("Limit Hasil", min_value=5, max_value=100, value=20)

    section_header("Mode Scanning", "Pilih kecepatan vs kelengkapan data")
    col_mode1, col_mode2 = st.columns(2)
    with col_mode1:
        scan_option = st.radio(
            "Kecepatan", ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"],
            index=0, horizontal=True
        )
    with col_mode2:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.02); border:1px solid #21262d; border-radius:10px; padding:14px;'>
            <div style='color:#8b949e; font-size:0.78rem; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.5px;'>Estimasi Waktu</div>
            <div style='display:flex; gap:20px;'>
                <div>
                    <div style='color:#f0b429; font-size:0.85rem; font-family:"Space Mono",monospace;'>⚡ Cepat</div>
                    <div style='color:#c9d1d9; font-size:0.9rem;'>±30 detik</div>
                </div>
                <div>
                    <div style='color:#58a6ff; font-size:0.85rem; font-family:"Space Mono",monospace;'>🐢 Lengkap</div>
                    <div style='color:#c9d1d9; font-size:0.9rem;'>±7–10 menit</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    periode_map = {"7 Hari":7,"14 Hari":14,"30 Hari":30,"90 Hari":90,"180 Hari":180,"365 Hari":365}
    hari = periode_map[periode]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):
        if filter_type == "Pilih Manual" and selected_stocks:
            stocks_to_scan = selected_stocks
        elif filter_type == "Filter Tingkatan" and selected_levels:
            stocks_to_scan = get_stocks_by_level(selected_levels)
        else:
            stocks_to_scan = STOCKS_LIST[:50] if scan_option == "⚡ Cepat (50 saham)" else STOCKS_LIST

        estimasi_detik = len(stocks_to_scan) * 0.5
        estimasi_menit = estimasi_detik / 60

        if estimasi_menit > 2:
            st.warning(f"⏱ Memproses **{len(stocks_to_scan)} saham** · Estimasi **{estimasi_menit:.1f} menit** · Jangan refresh halaman")
        else:
            st.info(f"📡 Memproses **{len(stocks_to_scan)} saham** · Estimasi **{estimasi_detik:.0f} detik**")

        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []
        start_time = time.time()

        for i, stock in enumerate(stocks_to_scan):
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(stocks_to_scan) - (i + 1)) if i > 0 else 0

            status_text.markdown(f"""
            <div style='
                background:rgba(255,255,255,0.02); border:1px solid #21262d;
                border-radius:8px; padding:10px 16px;
                display:flex; align-items:center; gap:12px;
            '>
                <span style='color:#f0b429; font-family:"Space Mono",monospace; font-size:0.85rem;'>
                    ◉ {stock}
                </span>
                <span style='color:#484f58; font-size:0.8rem;'>
                    {i+1}/{len(stocks_to_scan)} &nbsp;·&nbsp; {elapsed:.0f}s elapsed &nbsp;·&nbsp; ~{remaining:.0f}s remaining
                </span>
            </div>
            """, unsafe_allow_html=True)

            result = scan_open_low_pattern(stock, periode_hari=hari, min_kenaikan=min_kenaikan)
            if result:
                results.append(result)

            progress_bar.progress((i + 1) / len(stocks_to_scan))
            time.sleep(0.3)

        progress_bar.empty()
        status_text.empty()
        total_time = time.time() - start_time

        if results:
            df_results = pd.DataFrame(results)
            df_results = df_results.sort_values('frekuensi', ascending=False).head(limit_saham)

            # ── SUCCESS CARD ──
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                border: 1px solid #1c2230;
                border-radius: 16px;
                padding: 28px 32px;
                margin: 20px 0;
                position: relative;
                overflow: hidden;
            '>
                <div style='
                    position:absolute; top:0; right:0;
                    width:250px; height:100%;
                    background: radial-gradient(ellipse at top right, rgba(63,185,80,0.1) 0%, transparent 70%);
                    pointer-events:none;
                '></div>
                <div style='display:flex; align-items:center; gap:20px; flex-wrap:wrap;'>
                    <div style='
                        width:56px; height:56px;
                        background:linear-gradient(135deg,rgba(63,185,80,0.2),rgba(63,185,80,0.05));
                        border:1px solid rgba(63,185,80,0.3);
                        border-radius:14px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:1.8rem; flex-shrink:0;
                    '>✅</div>
                    <div>
                        <div style='
                            font-family:"Space Mono",monospace;
                            color:#3fb950; font-size:0.75rem;
                            letter-spacing:2px; text-transform:uppercase;
                        '>SCAN BERHASIL</div>
                        <div style='
                            color:#f0f6fc; font-size:2rem; font-weight:700;
                            font-family:"Space Mono",monospace; margin-top:4px; line-height:1;
                        '>{len(df_results)} <span style="font-size:1rem; color:#8b949e; font-weight:400;">saham ditemukan</span></div>
                    </div>
                    <div style='margin-left:auto; display:flex; gap:24px;'>
                        <div style='text-align:center;'>
                            <div style='color:#484f58; font-size:0.72rem; text-transform:uppercase; letter-spacing:1px;'>Waktu Proses</div>
                            <div style='color:#f0b429; font-family:"Space Mono",monospace; font-size:1.2rem; margin-top:4px;'>{total_time:.0f}s</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='color:#484f58; font-size:0.72rem; text-transform:uppercase; letter-spacing:1px;'>Periode</div>
                            <div style='color:#58a6ff; font-family:"Space Mono",monospace; font-size:1.2rem; margin-top:4px;'>{periode}</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='color:#484f58; font-size:0.72rem; text-transform:uppercase; letter-spacing:1px;'>Min Gain</div>
                            <div style='color:#00ff88; font-family:"Space Mono",monospace; font-size:1.2rem; margin-top:4px;'>{min_kenaikan}%</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── HASIL TABLE ──
            section_header("Hasil Scanning", "Data free float, FCA, dan tingkatan saham")

            enhanced_results = []
            for _, row in df_results.iterrows():
                saham = row['saham']
                free_float = get_free_float_value(saham)
                holders = get_free_float_holders(saham)
                level = get_stock_level(saham)
                total_inst_asing = sum((p['persen'] / free_float) * 100 for p in holders if free_float > 0)
                sisa_ritel = 100 - total_inst_asing
                potensi = analyze_goreng_potential(free_float)
                fca_status = '⚠️' if is_fca(saham) else ''
                enhanced_results.append({
                    'Saham': saham, 'Level': level,
                    'Frek': row['frekuensi'], 'Prob': f"{row['probabilitas']:.0f}%",
                    'Gain': f"{row['rata_rata_kenaikan']:.0f}%",
                    'FF': f"{free_float:.0f}%", 'Inst': f"{total_inst_asing:.0f}%",
                    'Ritel': f"{sisa_ritel:.0f}%", 'FCA': fca_status, 'Pot': potensi
                })

            enhanced_df = pd.DataFrame(enhanced_results)
            st.dataframe(enhanced_df, use_container_width=True, height=460, hide_index=True)

            # ── CHART ──
            section_header("Top 10 Saham", "Frekuensi pola Open=Low")

            fig = go.Figure()
            top10 = df_results.head(10)
            fig.add_trace(go.Bar(
                x=top10['saham'], y=top10['frekuensi'],
                marker=dict(
                    color=top10['probabilitas'],
                    colorscale=[[0,'#1c2230'],[0.5,'#f0b429'],[1,'#e88c0e']],
                    line=dict(color='rgba(240,180,41,0.3)', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>Frekuensi: %{y}<br>Probabilitas: %{customdata:.1f}%<extra></extra>',
                customdata=top10['probabilitas']
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Sora, sans-serif', color='#8b949e', size=12),
                title=dict(text='', x=0.5),
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#8b949e', size=11)),
                yaxis=dict(showgrid=True, gridcolor='#1c2230', zeroline=False, tickfont=dict(color='#8b949e', size=11)),
                margin=dict(l=10, r=10, t=20, b=10),
                height=380
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── AI ANALYSIS ──
            section_header("🤖 Analisis AI", "Insight mendalam untuk top 5 saham")

            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                analysis = analyze_pattern(row.to_dict())
                with st.expander(f"**{row['saham']}** — {get_stock_level(row['saham'])} · Prob {row['probabilitas']:.1f}% · Gain {row['rata_rata_kenaikan']:.1f}%"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("Probabilitas", f"{row['probabilitas']:.1f}%")
                    with col2: st.metric("Rata Gain", f"{row['rata_rata_kenaikan']:.1f}%")
                    with col3: st.metric("Max Gain", f"{row['max_kenaikan']:.1f}%")
                    with col4: st.metric("Frekuensi", f"{row['frekuensi']}x")
                    st.markdown(f"<div style='color:#c9d1d9; font-size:0.88rem; line-height:1.6; padding:12px 0;'>{analysis}</div>", unsafe_allow_html=True)
                    free_float = get_free_float_value(row['saham'])
                    st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)

            # ── WATCHLIST ──
            section_header("📋 Watchlist Generator", "Saham prioritas untuk dipantau besok")

            col_wl1, col_wl2 = st.columns(2)
            with col_wl1: min_gain_filter = st.slider("Minimal Gain Rata-rata (%)", 3, 10, 5, key="min_gain")
            with col_wl2: top_n = st.number_input("Jumlah Saham", 5, 30, 15, key="top_n")

            df_watchlist = df_results[df_results['rata_rata_kenaikan'] >= min_gain_filter].copy()

            if len(df_watchlist) > 0:
                max_prob = df_watchlist['probabilitas'].max()
                max_gain = df_watchlist['rata_rata_kenaikan'].max()
                if max_prob > 0 and max_gain > 0:
                    df_watchlist['skor'] = (
                        (df_watchlist['probabilitas'] / max_prob) * 50 +
                        (df_watchlist['rata_rata_kenaikan'] / max_gain) * 50
                    )
                    df_watchlist = df_watchlist.nlargest(top_n, 'skor')

                st.markdown(f"""
                <div style='
                    background:linear-gradient(135deg,#0d1117,#161b22);
                    border:1px solid rgba(88,166,255,0.15);
                    border-radius:12px; padding:20px 24px; margin:16px 0;
                    position:relative; overflow:hidden;
                '>
                    <div style='
                        position:absolute; top:0; left:0; right:0; height:2px;
                        background:linear-gradient(90deg,transparent,#58a6ff,transparent);
                    '></div>
                    <div style='display:flex; align-items:center; justify-content:space-between;'>
                        <div>
                            <div style='font-family:"Space Mono",monospace; color:#58a6ff; font-size:0.75rem; letter-spacing:2px;'>WATCHLIST TRADING</div>
                            <div style='color:#f0f6fc; font-size:1.1rem; font-weight:600; margin-top:4px;'>{datetime.now().strftime("%d %B %Y")}</div>
                        </div>
                        <div style='
                            background:rgba(240,180,41,0.1); border:1px solid rgba(240,180,41,0.3);
                            padding:6px 14px; border-radius:20px;
                            color:#f0b429; font-size:0.82rem; font-family:"Space Mono",monospace;
                        '>🎯 Pantau 15 menit pertama!</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7:
                        rekom = "🔥 PRIORITAS"
                    elif row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5:
                        rekom = "⚡ LAYAK"
                    else:
                        rekom = "📌 PANTAU"
                    free_float = get_free_float_value(row['saham'])
                    level_singkat = {'💎 Blue Chip':'BC','📈 Second Liner':'SL','🎯 Third Liner':'TL'}.get(get_stock_level(row['saham']),'')
                    watchlist_data.append({
                        "Rank": i+1, "Saham": row['saham'], "Lvl": level_singkat,
                        "Prob": f"{row['probabilitas']:.0f}%", "Gain": f"{row['rata_rata_kenaikan']:.0f}%",
                        "FF": f"{free_float:.0f}%", "FCA": '⚠️' if is_fca(row['saham']) else '',
                        "Pot": analyze_goreng_potential(free_float), "Rekom": rekom
                    })

                watchlist_df = pd.DataFrame(watchlist_data)
                st.dataframe(watchlist_df, use_container_width=True, hide_index=True, height=380)

                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    st.download_button("⬇ Export CSV", watchlist_df.to_csv(index=False).encode('utf-8'),
                        f"watchlist_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
                with col_exp2:
                    excel_data = export_to_excel(watchlist_df)
                    if excel_data:
                        st.download_button("⬇ Export Excel", excel_data,
                            f"watchlist_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

                st.markdown("""
                <div style='color:#484f58; font-size:0.75rem; margin-top:8px; text-align:center; font-family:"Space Mono",monospace;'>
                    BC=Blue Chip · SL=Second Liner · TL=Third Liner · FF=Free Float · FCA=Full Call Auction
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%")

            section_header("📥 Export Data Scanning")
            col_scan1, col_scan2 = st.columns(2)
            with col_scan1:
                st.download_button("⬇ Export CSV", enhanced_df.to_csv(index=False).encode('utf-8'),
                    f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
            with col_scan2:
                excel_data_scan = export_to_excel(enhanced_df)
                if excel_data_scan:
                    st.download_button("⬇ Export Excel", excel_data_scan,
                        f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.markdown("""
            <div style='
                background:rgba(248,81,73,0.06); border:1px solid rgba(248,81,73,0.2);
                border-radius:12px; padding:24px; text-align:center;
            '>
                <div style='font-size:2rem;'>🔍</div>
                <div style='color:#f85149; font-family:"Space Mono",monospace; font-size:0.85rem; margin-top:8px; letter-spacing:1px;'>
                    TIDAK ADA SAHAM DITEMUKAN
                </div>
                <div style='color:#484f58; font-size:0.8rem; margin-top:4px;'>
                    Coba ubah periode atau turunkan minimal kenaikan
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# LOW FLOAT SCANNER
# ============================================================
elif "Low Float" in scan_mode:

    section_header("Low Float Scanner", "Deteksi saham dengan free float rendah dan potensi volatilitas tinggi")

    col1, col2 = st.columns(2)
    with col1:
        max_ff = st.slider("Maks Free Float (%)", 1, 50, 20)
    with col2:
        min_vol = st.number_input("Min Volume", min_value=0, value=0, step=100000)

    section_header("Filter Tingkatan Saham")
    col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
    with col_lvl1: scan_blue = st.checkbox("💎 Blue Chip", value=True)
    with col_lvl2: scan_second = st.checkbox("📈 Second Liner", value=True)
    with col_lvl3: scan_third = st.checkbox("🎯 Third Liner", value=True)

    scan_option_lf = st.radio("Mode Scanning", ["⚡ Cepat", "🐢 Lengkap"], horizontal=True, index=0)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        selected_levels_lf = []
        if scan_blue: selected_levels_lf.append('Blue Chip')
        if scan_second: selected_levels_lf.append('Second Liner')
        if scan_third: selected_levels_lf.append('Third Liner')

        if selected_stocks:
            stocks_to_scan = selected_stocks
        elif selected_levels_lf:
            stocks_to_scan = get_stocks_by_level(selected_levels_lf)
        else:
            stocks_to_scan = STOCKS_LIST[:50] if scan_option_lf == "⚡ Cepat" else STOCKS_LIST

        with st.spinner(f"Scanning {len(stocks_to_scan)} saham..."):
            results = scan_low_float(stocks_to_scan, max_ff, min_vol)

            if results:
                df_results = pd.DataFrame(results)

                st.markdown(f"""
                <div style='
                    background:linear-gradient(135deg,#0d1117,#161b22);
                    border:1px solid rgba(63,185,80,0.2);
                    border-radius:16px; padding:28px 32px; margin:20px 0;
                    position:relative; overflow:hidden;
                '>
                    <div style='
                        position:absolute; top:0; right:0;
                        width:200px; height:100%;
                        background:radial-gradient(ellipse at right, rgba(63,185,80,0.08) 0%, transparent 70%);
                    '></div>
                    <div style='display:flex; align-items:center; gap:20px; flex-wrap:wrap;'>
                        <div style='
                            width:52px; height:52px;
                            background:rgba(63,185,80,0.1); border:1px solid rgba(63,185,80,0.3);
                            border-radius:14px; display:flex; align-items:center; justify-content:center;
                            font-size:1.6rem; flex-shrink:0;
                        '>✅</div>
                        <div>
                            <div style='color:#3fb950; font-family:"Space Mono",monospace; font-size:0.72rem; letter-spacing:2px; text-transform:uppercase;'>LOW FLOAT SCAN SELESAI</div>
                            <div style='color:#f0f6fc; font-size:2rem; font-weight:700; font-family:"Space Mono",monospace; margin-top:4px; line-height:1;'>
                                {len(df_results)} <span style='font-size:1rem; color:#8b949e; font-weight:400;'>saham free float &lt; {max_ff}%</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                section_header("Hasil Scanning", "Free float, kategori, komposisi pemegang, dan potensi")

                enriched_results = []
                for _, row in df_results.iterrows():
                    saham = row['saham']
                    free_float = get_free_float_value(saham)
                    holders = get_free_float_holders(saham)
                    total_inst_asing = sum((p['persen'] / free_float) * 100 for p in holders if free_float > 0)
                    sisa_ritel = 100 - total_inst_asing
                    level_singkat = {'💎 Blue Chip':'BC','📈 Second Liner':'SL','🎯 Third Liner':'TL'}.get(get_stock_level(saham),'')
                    enriched_results.append({
                        'Saham': saham, 'Lvl': level_singkat,
                        'FF': f"{free_float:.0f}%",
                        'Kat': get_kategori_singkatan(row['category']),
                        'Vol(M)': f"{row['volume_avg']/1e6:.1f}",
                        'Volat': f"{row['volatility']:.0f}%",
                        'Inst': f"{total_inst_asing:.0f}%",
                        'Ritel': f"{sisa_ritel:.0f}%",
                        'FCA': '⚠️' if is_fca(saham) else '',
                        'Pot': analyze_goreng_potential(free_float)
                    })

                enriched_df = pd.DataFrame(enriched_results)
                st.dataframe(enriched_df, use_container_width=True, height=460, hide_index=True)

                section_header("Detail Free Float", "Top 5 saham dengan breakdown komposisi pemegang")
                for _, row in df_results.head(5).iterrows():
                    free_float = get_free_float_value(row['saham'])
                    with st.expander(f"**{row['saham']}** — {get_stock_level(row['saham'])} · FF {free_float:.0f}%"):
                        st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)

                section_header("Distribusi Visual")
                col_v1, col_v2 = st.columns(2)

                with col_v1:
                    cat_counts = df_results['category'].value_counts()
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=cat_counts.index, values=cat_counts.values,
                        hole=0.55,
                        marker=dict(colors=['#f0b429','#58a6ff','#3fb950','#ff7b72','#d2a8ff'],
                                    line=dict(color='#0a0e17', width=2)),
                        textfont=dict(color='#e6edf3', size=11)
                    )])
                    fig_pie.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Sora', color='#8b949e'),
                        title=dict(text='Kategori Free Float', font=dict(color='#8b949e', size=13), x=0.5),
                        legend=dict(font=dict(color='#8b949e', size=11), bgcolor='rgba(0,0,0,0)'),
                        margin=dict(l=0, r=0, t=40, b=0), height=300,
                        annotations=[dict(text='FF', x=0.5, y=0.5, font_size=14, showarrow=False, font_color='#484f58')]
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col_v2:
                    fig_scatter = go.Figure()
                    fig_scatter.add_trace(go.Scatter(
                        x=df_results['public_float'], y=df_results['volatility'],
                        mode='markers',
                        marker=dict(
                            size=[max(6, v/1e6*0.5) for v in df_results['volume_avg']],
                            color=df_results['volatility'],
                            colorscale=[[0,'#1c2230'],[0.5,'#f0b429'],[1,'#e88c0e']],
                            line=dict(color='rgba(240,180,41,0.3)', width=1),
                            sizemode='area', sizeref=2
                        ),
                        text=df_results['saham'],
                        hovertemplate='<b>%{text}</b><br>FF: %{x:.1f}%<br>Volat: %{y:.1f}%<extra></extra>'
                    ))
                    fig_scatter.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Sora', color='#8b949e', size=11),
                        title=dict(text='FF vs Volatilitas', font=dict(color='#8b949e', size=13), x=0.5),
                        xaxis=dict(title='Free Float (%)', showgrid=True, gridcolor='#1c2230', zeroline=False),
                        yaxis=dict(title='Volatilitas (%)', showgrid=True, gridcolor='#1c2230', zeroline=False),
                        margin=dict(l=10, r=10, t=40, b=10), height=300
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)

                section_header("📥 Export Data")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.download_button("⬇ Export CSV", enriched_df.to_csv(index=False).encode('utf-8'),
                        f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
                with col_e2:
                    excel_data = export_to_excel(enriched_df)
                    if excel_data:
                        st.download_button("⬇ Export Excel", excel_data,
                            f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.markdown("""
                <div style='
                    background:rgba(248,81,73,0.06); border:1px solid rgba(248,81,73,0.2);
                    border-radius:12px; padding:24px; text-align:center;
                '>
                    <div style='font-size:2rem;'>🔍</div>
                    <div style='color:#f85149; font-family:"Space Mono",monospace; font-size:0.85rem; margin-top:8px; letter-spacing:1px;'>
                        TIDAK ADA SAHAM LOW FLOAT DITEMUKAN
                    </div>
                    <div style='color:#484f58; font-size:0.8rem; margin-top:4px;'>
                        Coba naikkan batas maksimal free float
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 12px;
    padding: 12px 0;
'>
    <div style='color:#30363d; font-size:0.75rem; font-family:"Space Mono",monospace;'>
        ⚠ Data edukasi, bukan rekomendasi investasi
    </div>
    <div style='display:flex; gap:20px; flex-wrap:wrap;'>
        <span style='color:#484f58; font-size:0.72rem;'>BC=Blue Chip · SL=Second Liner · TL=Third Liner</span>
        <span style='color:#484f58; font-size:0.72rem;'>FF=Free Float · FCA=Full Call Auction</span>
        <span style='color:#484f58; font-size:0.72rem;'>🔥 UT/ST · ⚡ TG · 📊 SD · 📉 RD</span>
    </div>
</div>
""", unsafe_allow_html=True)
