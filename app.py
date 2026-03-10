import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import concurrent.futures
import random
import html

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
    'WIKA', 'PTPP', 'WSKT', 'ADHI', 'JSMR',
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

FCA_STOCKS = ['COIN', 'CDIA']

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
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.22, 'tipe': 'Institusi', 'catatan': 'Nambah Feb 2026', 'update': 'Feb 2026'}],
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
    'BBRI': {
        'pemegang': [{'nama': 'BPJS Ketenagakerjaan', 'persen': 1.09, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}],
        'free_float': 98.91, 'total_shares': 123456789000,
        'insider_activity': [{'tanggal': '09 Mar 2026', 'insider': 'Dirut', 'aksi': 'JUAL', 'jumlah': 50000, 'harga': 5800}]
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

# ========== HELPER FUNCTIONS ==========

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

def get_kategori_singkatan(kategori):
    singkatan = {
        'Ultra Low Float': 'ULF',
        'Very Low Float': 'VLF',
        'Low Float': 'LF',
        'Moderate Low Float': 'MLF',
        'Normal Float': 'NF'
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

def display_free_float_info(stock_code, free_float_value):
    free_float_holders = get_free_float_holders(stock_code)
    
    h = f"""
    <div style='background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); 
                padding: 18px; border-radius: 12px; margin: 12px 0;
                border: 1px solid #30363d; box-shadow: 0 4px 24px rgba(0,0,0,0.4);'>
        <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 14px;'>
            <span style='width: 3px; height: 20px; background: linear-gradient(180deg, #00d4aa, #0099ff); 
                         border-radius: 2px; display: inline-block;'></span>
            <h4 style='color: #e6edf3; margin: 0; font-size: 0.95rem; letter-spacing: 0.5px; font-family: "JetBrains Mono", monospace;'>
                FREE FLOAT — {stock_code}
            </h4>
        </div>
    """
    
    if is_fca(stock_code):
        h += """
        <div style='background: rgba(255,170,0,0.1); border: 1px solid rgba(255,170,0,0.3); 
                    padding: 8px 12px; border-radius: 8px; margin-bottom: 12px;'>
            <span style='color: #ffaa00; font-size: 0.82rem; font-weight: 600; letter-spacing: 1px;'>
                ⚠ FCA — PAPAN PEMANTAUAN KHUSUS
            </span>
        </div>
        """
    
    h += f"""
    <div style='background: rgba(0, 212, 170, 0.08); border: 1px solid rgba(0, 212, 170, 0.2);
                padding: 10px 14px; border-radius: 8px; margin-bottom: 14px;
                display: flex; justify-content: space-between; align-items: center;'>
        <span style='color: #8b949e; font-size: 0.82rem; font-family: "JetBrains Mono", monospace;'>FREE FLOAT</span>
        <span style='color: #00d4aa; font-size: 1.4rem; font-weight: 700; font-family: "JetBrains Mono", monospace;'>{free_float_value:.2f}%</span>
    </div>
    """
    
    if free_float_holders:
        h += "<p style='color: #8b949e; font-size: 0.78rem; margin: 0 0 8px 0; letter-spacing: 1px; text-transform: uppercase; font-family: \"JetBrains Mono\", monospace;'>Pemegang Institusi / Asing &gt;1%</p>"
        total_dari_ff = 0
        
        for p in free_float_holders:
            persen_dalam_ff = (p['persen'] / free_float_value) * 100
            total_dari_ff += persen_dalam_ff
            
            color = '#4da6ff' if p['tipe'] == 'Institusi' else '#00d4aa'
            icon = '🏛' if p['tipe'] == 'Institusi' else '🌐'
            
            h += f"""
            <div style='display: flex; justify-content: space-between; align-items: center;
                        background: rgba(255,255,255,0.03); padding: 9px 12px; border-radius: 7px; 
                        margin: 5px 0; border-left: 2px solid {color};'>
                <div>
                    <span style='color: #c9d1d9; font-size: 0.85rem;'>{icon} {p['nama']}</span>
                    <span style='color: #484f58; font-size: 0.75rem; margin-left: 8px;'>{p['catatan']}</span>
                </div>
                <span style='color: {color}; font-weight: 700; font-size: 0.95rem; font-family: "JetBrains Mono", monospace;'>{persen_dalam_ff:.1f}%</span>
            </div>
            """
        
        sisa_ritel = 100 - total_dari_ff
        h += f"""
        <div style='display: flex; justify-content: space-between; align-items: center;
                    background: rgba(0,212,170,0.06); padding: 9px 12px; border-radius: 7px; 
                    margin: 5px 0; border-left: 2px solid #00d4aa;'>
            <span style='color: #c9d1d9; font-size: 0.85rem;'>👥 Ritel</span>
            <span style='color: #00d4aa; font-weight: 700; font-size: 0.95rem; font-family: "JetBrains Mono", monospace;'>{sisa_ritel:.1f}%</span>
        </div>
        """
    else:
        h += """
        <div style='text-align: center; padding: 16px; color: #484f58; font-size: 0.85rem;'>
            Tidak ada institusi/asing &gt;1%
        </div>
        <div style='display: flex; justify-content: space-between; align-items: center;
                    background: rgba(0,212,170,0.06); padding: 9px 12px; border-radius: 7px; border-left: 2px solid #00d4aa;'>
            <span style='color: #c9d1d9; font-size: 0.85rem;'>👥 Ritel</span>
            <span style='color: #00d4aa; font-weight: 700; font-family: "JetBrains Mono", monospace;'>100%</span>
        </div>
        """
    
    insider = get_insider_activity(stock_code)
    if insider:
        h += "<p style='color: #8b949e; font-size: 0.78rem; margin: 16px 0 8px 0; letter-spacing: 1px; text-transform: uppercase; font-family: \"JetBrains Mono\", monospace;'>Aktivitas Insider — 30 Hari</p>"
        for a in insider:
            is_buy = a['aksi'] == 'BELI'
            color = '#00d4aa' if is_buy else '#ff5c5c'
            icon = '▲' if is_buy else '▼'
            h += f"""
            <div style='display: flex; justify-content: space-between; align-items: center;
                        background: rgba(255,255,255,0.03); padding: 9px 12px; border-radius: 7px; margin: 5px 0;'>
                <div>
                    <span style='color: #8b949e; font-size: 0.78rem; font-family: "JetBrains Mono", monospace;'>{a['tanggal']}</span>
                    <span style='color: #484f58; font-size: 0.78rem; margin-left: 8px;'>{a['insider']}</span>
                </div>
                <span style='color: {color}; font-weight: 700; font-size: 0.85rem; font-family: "JetBrains Mono", monospace;'>
                    {icon} {a['aksi']} {a['jumlah']:,}
                </span>
            </div>
            """
    
    h += "</div>"
    return h

def create_download_buttons(data, prefix, key_suffix):
    col1, col2 = st.columns(2)
    with col1:
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Download CSV",
            data=csv,
            file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"csv_{key_suffix}"
        )
    with col2:
        excel = export_to_excel(data)
        if excel:
            st.download_button(
                label="⬇ Download Excel",
                data=excel,
                file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"excel_{key_suffix}"
            )

def scan_stocks_parallel(stocks_to_scan, scan_function, *args, **kwargs):
    results = []
    failed_stocks = []
    
    with st.spinner(f"Memproses {len(stocks_to_scan)} saham..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_stock = {
                executor.submit(scan_function, stock, *args, **kwargs): stock 
                for stock in stocks_to_scan
            }
            
            completed = 0
            total = len(future_to_stock)
            
            for future in concurrent.futures.as_completed(future_to_stock):
                stock = future_to_stock[future]
                completed += 1
                
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    failed_stocks.append(stock)
                
                progress = completed / total
                progress_bar.progress(progress)
                status_text.markdown(
                    f"<span style='color:#00d4aa; font-family:monospace; font-size:0.85rem;'>✓ {completed}/{total} diproses &nbsp;|&nbsp; ✗ {len(failed_stocks)} gagal</span>",
                    unsafe_allow_html=True
                )
        
        progress_bar.empty()
        status_text.empty()
        
        if failed_stocks:
            st.warning(f"{len(failed_stocks)} saham gagal: {', '.join(failed_stocks[:10])}" + 
                      ("..." if len(failed_stocks) > 10 else ""))
    
    return results

def reset_session_data():
    keys_to_reset = ['scan_results', 'enhanced_df', 'watchlist_df', 'display_df', 'df_results']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]


# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="RADAR AKSARA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS — PREMIUM DARK TRADING TERMINAL ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* ── ROOT VARIABLES ── */
    :root {
        --bg-base:      #060a0f;
        --bg-surface:   #0d1117;
        --bg-elevated:  #161b22;
        --bg-hover:     #1c2128;
        --border:       #21262d;
        --border-light: #30363d;
        --text-primary: #e6edf3;
        --text-secondary:#8b949e;
        --text-muted:   #484f58;
        --accent-green: #00d4aa;
        --accent-blue:  #4da6ff;
        --accent-gold:  #e3b341;
        --accent-red:   #ff5c5c;
        --accent-purple:#c084fc;
        --glow-green:   rgba(0,212,170,0.15);
        --glow-blue:    rgba(77,166,255,0.15);
    }

    /* ── GLOBAL RESET ── */
    .stApp {
        background-color: var(--bg-base) !important;
        background-image: 
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,212,170,0.04) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 90% 80%, rgba(77,166,255,0.03) 0%, transparent 60%);
        font-family: 'Space Grotesk', sans-serif;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-secondary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* ── MAIN TEXT ── */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text-primary) !important;
    }
    .stApp p, .stApp label, .stApp div {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text-secondary);
    }

    /* ── INPUTS ── */
    .stSelectbox > div > div,
    .stMultiselect > div > div,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    .stSelectbox > div > div:hover,
    .stMultiselect > div > div:hover {
        border-color: var(--accent-green) !important;
    }

    /* ── SLIDER ── */
    .stSlider > div > div > div {
        background: var(--border-light) !important;
    }
    .stSlider > div > div > div > div {
        background: var(--accent-green) !important;
    }

    /* ── PRIMARY BUTTON — SCAN ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d4aa 0%, #0099cc 100%) !important;
        color: #060a0f !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        box-shadow: 0 0 24px rgba(0,212,170,0.3), 0 4px 12px rgba(0,0,0,0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 36px rgba(0,212,170,0.5), 0 8px 20px rgba(0,0,0,0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* ── SECONDARY BUTTONS ── */
    .stButton > button {
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.82rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
        background: rgba(0,212,170,0.05) !important;
    }

    /* ── DOWNLOAD BUTTONS ── */
    .stDownloadButton > button {
        background: var(--bg-elevated) !important;
        color: var(--accent-blue) !important;
        border: 1px solid rgba(77,166,255,0.3) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.5px !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(77,166,255,0.08) !important;
        border-color: var(--accent-blue) !important;
    }

    /* ── DATAFRAME ── */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
    }
    .stDataFrame iframe {
        border-radius: 12px !important;
    }

    /* ── METRICS ── */
    [data-testid="stMetric"] {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent-green) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: var(--accent-green) !important;
        background: rgba(0,212,170,0.04) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 4px !important;
        border-bottom: 1px solid var(--border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        border: none !important;
        border-radius: 8px 8px 0 0 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.85rem !important;
        padding: 8px 18px !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0,212,170,0.08) !important;
        color: var(--accent-green) !important;
        border-bottom: 2px solid var(--accent-green) !important;
    }

    /* ── INFO / WARNING / SUCCESS ── */
    .stInfo {
        background: rgba(77,166,255,0.07) !important;
        border: 1px solid rgba(77,166,255,0.2) !important;
        border-radius: 8px !important;
        color: var(--accent-blue) !important;
        font-size: 0.85rem !important;
    }
    .stWarning {
        background: rgba(227,179,65,0.07) !important;
        border: 1px solid rgba(227,179,65,0.25) !important;
        border-radius: 8px !important;
        color: var(--accent-gold) !important;
        font-size: 0.85rem !important;
    }
    .stSuccess {
        background: rgba(0,212,170,0.07) !important;
        border: 1px solid rgba(0,212,170,0.2) !important;
        border-radius: 8px !important;
    }

    /* ── PROGRESS BAR ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-green), var(--accent-blue)) !important;
        border-radius: 4px !important;
    }
    .stProgress > div > div > div {
        background: var(--bg-elevated) !important;
        border-radius: 4px !important;
    }

    /* ── RADIO ── */
    .stRadio > div {
        gap: 8px !important;
    }
    .stRadio label {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        transition: all 0.15s !important;
    }
    .stRadio label:hover {
        border-color: var(--accent-green) !important;
        background: rgba(0,212,170,0.04) !important;
    }

    /* ── CHECKBOX ── */
    .stCheckbox label {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
    }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-surface); }
    ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ── DIVIDER ── */
    hr { border-color: var(--border) !important; margin: 24px 0 !important; }

    /* ── CAPTION ── */
    .stCaption { color: var(--text-muted) !important; font-size: 0.78rem !important; font-family: 'JetBrains Mono', monospace !important; }

    /* ── SPINNER ── */
    .stSpinner > div { border-top-color: var(--accent-green) !important; }
</style>
""", unsafe_allow_html=True)


# ========== HEADER ==========
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; 
            padding: 28px 0 20px 0; border-bottom: 1px solid #21262d; margin-bottom: 28px;">
    <div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #00d4aa, #0099cc);
                        border-radius: 10px; display: flex; align-items: center; justify-content: center;
                        box-shadow: 0 0 20px rgba(0,212,170,0.35); font-size: 1.2rem;">📡</div>
            <div>
                <h1 style="color: #e6edf3; font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; 
                           font-weight: 700; margin: 0; letter-spacing: -0.5px;">
                    RADAR <span style="color: #00d4aa;">AKSARA</span>
                </h1>
                <p style="color: #484f58; font-size: 0.75rem; margin: 0; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;">
                    IDX STOCK SCANNER  ·  OPEN=LOW  ·  LOW FLOAT  ·  AI ANALYSIS
                </p>
            </div>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="display: inline-flex; align-items: center; gap: 6px; 
                    background: rgba(0,212,170,0.08); border: 1px solid rgba(0,212,170,0.2);
                    padding: 6px 14px; border-radius: 20px;">
            <span style="width: 7px; height: 7px; background: #00d4aa; border-radius: 50%;
                         display: inline-block; animation: pulse 2s infinite;"></span>
            <span style="color: #00d4aa; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;">LIVE</span>
        </div>
        <p style="color: #484f58; font-size: 0.72rem; margin: 6px 0 0 0; font-family: 'JetBrains Mono', monospace;">
            IDX · BEI · KSEI
        </p>
    </div>
</div>
<style>
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 6px #00d4aa; }
    50% { opacity: 0.5; box-shadow: 0 0 12px #00d4aa; }
}
</style>
""", unsafe_allow_html=True)


# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 12px 0; border-bottom: 1px solid #21262d; margin-bottom: 16px;">
        <p style="color: #484f58; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; 
                  font-family: 'JetBrains Mono', monospace; margin: 0;">CONTROL PANEL</p>
    </div>
    """, unsafe_allow_html=True)
    
    scan_mode = st.radio(
        "**Mode Scanning**",
        ["📈 Open = Low Scanner", "🔍 Low Float Scanner"],
        index=0
    )
    
    st.markdown("<div style='height: 1px; background: #21262d; margin: 16px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("""<p style="color: #484f58; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; 
                  font-family: 'JetBrains Mono', monospace; margin: 0 0 12px 0;">FILTER SAHAM</p>""", unsafe_allow_html=True)
    
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
            "Tingkatan Saham",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
            help="Blue Chip: >Rp10T | Second Liner: Rp500M–Rp10T | Third Liner: <Rp1T"
        )
        if selected_levels:
            stocks_count = len(get_stocks_by_level(selected_levels))
            st.markdown(f"""
            <div style="background: rgba(77,166,255,0.06); border: 1px solid rgba(77,166,255,0.15); 
                        padding: 10px 12px; border-radius: 8px; margin-top: 8px;">
                <span style="color: #4da6ff; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                    📊 {stocks_count} saham terpilih
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1px; background: #21262d; margin: 16px 0;'></div>", unsafe_allow_html=True)
    
    if st.button("↺  Reset Data", use_container_width=True):
        reset_session_data()
        st.success("✓ Session direset")
        st.rerun()
    
    st.markdown("<div style='height: 1px; background: #21262d; margin: 16px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #484f58; line-height: 2;">
        <p style="margin:0; color: #8b949e; font-size: 0.7rem; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px;">Legenda</p>
        <p style="margin: 3px 0;">💎 BC &nbsp;·&nbsp; Blue Chip >Rp10T</p>
        <p style="margin: 3px 0;">📈 SL &nbsp;·&nbsp; Second Liner</p>
        <p style="margin: 3px 0;">🎯 TL &nbsp;·&nbsp; Third Liner</p>
        <p style="margin: 3px 0;">⚠️ FCA &nbsp;·&nbsp; Pemantauan Khusus</p>
        <p style="margin: 3px 0;">🔥 UT/ST &nbsp;·&nbsp; Ultra/Sangat Tinggi</p>
        <p style="margin: 3px 0;">⚡ TG &nbsp;·&nbsp; Tinggi &nbsp;·&nbsp; 📊 SD &nbsp;·&nbsp; Sedang</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #21262d; 
                text-align: center; color: #30363d; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">
        RADAR AKSARA &nbsp;·&nbsp; IDX SCANNER<br>
        <span style="color: #484f58;">Data: Yahoo Finance · KSEI · BEI</span>
    </div>
    """, unsafe_allow_html=True)


# ========== OPEN=LOW SCANNER ==========
if "Open = Low" in scan_mode:
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 24px;">
        <span style="width: 3px; height: 24px; background: linear-gradient(180deg, #00d4aa, transparent); 
                     border-radius: 2px; display: inline-block;"></span>
        <h2 style="color: #e6edf3; font-size: 1.1rem; font-weight: 600; margin: 0; letter-spacing: 0.3px; font-family: 'Space Grotesk', sans-serif;">
            Scanner Open = Low &nbsp;<span style="color: #484f58; font-weight: 400; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;">+ KENAIKAN ≥5%</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        periode = st.selectbox(
            "Periode Analisis",
            ["7 Hari", "14 Hari", "30 Hari", "90 Hari", "180 Hari", "365 Hari"],
            index=2
        )
    with col2:
        min_kenaikan = st.slider("Minimal Kenaikan (%)", 1, 20, 5)
    with col3:
        limit_saham = st.number_input("Limit Hasil", min_value=5, max_value=100, value=20)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    col_par1, col_par2 = st.columns([1, 2])
    with col_par1:
        use_parallel = st.checkbox("⚡ Parallel Scanning", value=True)
    with col_par2:
        st.markdown("""
        <div style="background: rgba(0,212,170,0.05); border: 1px solid rgba(0,212,170,0.15); 
                    padding: 8px 14px; border-radius: 8px; margin-top: 2px;">
            <span style="color: #00d4aa; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">
                ⚡ Parallel mode &nbsp;·&nbsp; 5–10× lebih cepat
            </span>
        </div>
        """, unsafe_allow_html=True)

    periode_map = {"7 Hari": 7, "14 Hari": 14, "30 Hari": 30, "90 Hari": 90, "180 Hari": 180, "365 Hari": 365}
    hari = periode_map[periode]

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    if st.button("🚀  MULAI SCANNING", type="primary", use_container_width=True):
        reset_session_data()
        
        if filter_type == "Pilih Manual" and selected_stocks:
            stocks_to_scan = selected_stocks
        elif filter_type == "Filter Tingkatan" and selected_levels:
            stocks_to_scan = get_stocks_by_level(selected_levels)
        else:
            stocks_to_scan = STOCKS_LIST
        
        estimasi_detik = len(stocks_to_scan) * (0.1 if use_parallel else 0.5)
        
        st.markdown(f"""
        <div style="background: rgba(77,166,255,0.06); border: 1px solid rgba(77,166,255,0.15); 
                    padding: 12px 16px; border-radius: 10px; margin: 12px 0;
                    display: flex; align-items: center; gap: 12px;">
            <span style="color: #4da6ff; font-size: 1.2rem;">⏳</span>
            <div>
                <span style="color: #4da6ff; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600;">
                    {len(stocks_to_scan)} SAHAM
                </span>
                <span style="color: #484f58; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; margin-left: 12px;">
                    estimasi ~{estimasi_detik:.0f} detik
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        start_time = time.time()
        
        if use_parallel:
            results = scan_stocks_parallel(
                stocks_to_scan, scan_open_low_pattern,
                periode_hari=hari, min_kenaikan=min_kenaikan
            )
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            for i, stock in enumerate(stocks_to_scan):
                status_text.markdown(f"<span style='color:#8b949e; font-family:monospace; font-size:0.82rem;'>Memproses {stock}... ({i+1}/{len(stocks_to_scan)})</span>", unsafe_allow_html=True)
                try:
                    result = scan_open_low_pattern(stock, periode_hari=hari, min_kenaikan=min_kenaikan)
                    if result:
                        results.append(result)
                except:
                    pass
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
            <div style="background: linear-gradient(135deg, #0d1f17 0%, #0d1a24 100%);
                        border: 1px solid rgba(0,212,170,0.25); border-radius: 16px;
                        padding: 28px 32px; margin: 24px 0 32px 0;
                        box-shadow: 0 0 40px rgba(0,212,170,0.08), inset 0 1px 0 rgba(0,212,170,0.1);
                        position: relative; overflow: hidden;">
                <div style="position: absolute; top: -40px; right: -40px; width: 160px; height: 160px;
                             background: radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%);
                             border-radius: 50%;"></div>
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
                    <div>
                        <p style="color: #00d4aa; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; 
                                  letter-spacing: 2px; text-transform: uppercase; margin: 0 0 6px 0;">SCAN BERHASIL</p>
                        <p style="color: #e6edf3; font-size: 2.8rem; font-weight: 700; margin: 0; line-height: 1; 
                                  font-family: 'JetBrains Mono', monospace;">
                            {len(df_results)}<span style="color: #00d4aa;">.</span>
                        </p>
                        <p style="color: #8b949e; font-size: 0.85rem; margin: 6px 0 0 0;">Saham pola Open = Low ditemukan</p>
                    </div>
                    <div style="display: flex; gap: 24px;">
                        <div style="text-align: center; padding: 12px 20px; background: rgba(255,255,255,0.03); 
                                    border-radius: 10px; border: 1px solid #21262d;">
                            <p style="color: #484f58; font-size: 0.68rem; letter-spacing: 1.5px; text-transform: uppercase; 
                                      font-family: 'JetBrains Mono', monospace; margin: 0 0 4px 0;">DURASI</p>
                            <p style="color: #e6edf3; font-size: 1.4rem; font-weight: 700; margin: 0; 
                                      font-family: 'JetBrains Mono', monospace;">{total_time:.0f}<span style="color: #484f58; font-size: 0.9rem;">s</span></p>
                        </div>
                        <div style="text-align: center; padding: 12px 20px; background: rgba(255,255,255,0.03); 
                                    border-radius: 10px; border: 1px solid #21262d;">
                            <p style="color: #484f58; font-size: 0.68rem; letter-spacing: 1.5px; text-transform: uppercase; 
                                      font-family: 'JetBrains Mono', monospace; margin: 0 0 4px 0;">PERIODE</p>
                            <p style="color: #e6edf3; font-size: 1.4rem; font-weight: 700; margin: 0; 
                                      font-family: 'JetBrains Mono', monospace;">{hari}<span style="color: #484f58; font-size: 0.9rem;">d</span></p>
                        </div>
                        <div style="text-align: center; padding: 12px 20px; background: rgba(255,255,255,0.03); 
                                    border-radius: 10px; border: 1px solid #21262d;">
                            <p style="color: #484f58; font-size: 0.68rem; letter-spacing: 1.5px; text-transform: uppercase; 
                                      font-family: 'JetBrains Mono', monospace; margin: 0 0 4px 0;">MIN GAIN</p>
                            <p style="color: #e6edf3; font-size: 1.4rem; font-weight: 700; margin: 0; 
                                      font-family: 'JetBrains Mono', monospace;">{min_kenaikan}<span style="color: #484f58; font-size: 0.9rem;">%</span></p>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ── SECTION LABEL ──
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 24px 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #00d4aa; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Hasil Scanning · Free Float · FCA · Tingkatan</p>
            </div>
            """, unsafe_allow_html=True)
            
            enhanced_results = []
            for _, row in df_results.iterrows():
                saham = row['saham']
                free_float = get_free_float_value(saham)
                holders = get_free_float_holders(saham)
                level = get_stock_level(saham)
                
                total_inst_asing = 0
                for p in holders:
                    persen_dalam_ff = (p['persen'] / free_float) * 100 if free_float > 0 else 0
                    total_inst_asing += persen_dalam_ff
                
                sisa_ritel = 100 - total_inst_asing
                potensi = analyze_goreng_potential(free_float)
                fca_status = '⚠️' if is_fca(saham) else '—'
                
                enhanced_results.append({
                    'Saham': saham,
                    'Level': level,
                    'Frek': row['frekuensi'],
                    'Prob_Val': row['probabilitas'],
                    'Prob': f"{row['probabilitas']:.0f}%",
                    'Gain_Val': row['rata_rata_kenaikan'],
                    'Gain': f"{row['rata_rata_kenaikan']:.0f}%",
                    'FF_Val': free_float,
                    'FF': f"{free_float:.0f}%",
                    'Inst_Val': total_inst_asing,
                    'Inst': f"{total_inst_asing:.0f}%",
                    'Ritel_Val': sisa_ritel,
                    'Ritel': f"{sisa_ritel:.0f}%",
                    'FCA': fca_status,
                    'Pot': potensi
                })
            
            enhanced_df = pd.DataFrame(enhanced_results)
            display_df = enhanced_df[['Saham', 'Level', 'Frek', 'Prob', 'Gain', 'FF', 'Inst', 'Ritel', 'FCA', 'Pot']]
            st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
            
            st.session_state['scan_results'] = df_results
            st.session_state['enhanced_df'] = enhanced_df
            st.session_state['display_df'] = display_df
            st.session_state['watchlist_df'] = None
            
            # ── CHART ──
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 28px 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #4da6ff; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Top 10 · Frekuensi Tertinggi</p>
            </div>
            """, unsafe_allow_html=True)
            
            top10_df = df_results.head(10).copy()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=top10_df['saham'],
                y=top10_df['frekuensi'],
                marker=dict(
                    color=top10_df['probabilitas'].tolist(),
                    colorscale='Teal',
                    showscale=True,
                    colorbar=dict(
                        title=dict(
                            text="Prob (%)",
                            font=dict(color='#8b949e', size=10, family='JetBrains Mono')
                        ),
                        tickfont=dict(color='#8b949e', size=10, family='JetBrains Mono'),
                        outlinecolor='#21262d',
                        outlinewidth=1
                    ),
                    line=dict(width=0),
                    opacity=0.9
                ),
                hovertemplate='<b>%{x}</b><br>Frekuensi: %{y}<br>Prob: %{marker.color:.1f}%<extra></extra>'
            ))
            fig.update_layout(
                plot_bgcolor='#0d1117',
                paper_bgcolor='#0d1117',
                font=dict(family='JetBrains Mono', color='#8b949e', size=11),
                xaxis=dict(
                    categoryorder='array',
                    categoryarray=top10_df['saham'].tolist(),
                    gridcolor='#21262d',
                    tickfont=dict(color='#8b949e'),
                    title=dict(text='', font=dict(color='#484f58'))
                ),
                yaxis=dict(
                    gridcolor='#21262d',
                    tickfont=dict(color='#8b949e'),
                    title=dict(text='Frekuensi', font=dict(color='#484f58', size=10))
                ),
                height=360,
                margin=dict(l=40, r=60, t=20, b=40),
                hoverlabel=dict(bgcolor='#161b22', bordercolor='#30363d', font=dict(color='#e6edf3'))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Urutan: {' · '.join(top10_df['saham'].tolist())}")
            
            # ── AI ANALYSIS ──
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 32px 0 16px 0;">
                <span style="width: 3px; height: 18px; background: #c084fc; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Analisis AI · Top 5 Saham</p>
            </div>
            """, unsafe_allow_html=True)
            
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                analysis = analyze_pattern(row.to_dict())
                level = get_stock_level(row['saham'])
                
                with st.expander(f"#{idx+1} &nbsp; {row['saham']} &nbsp;·&nbsp; {level} &nbsp;·&nbsp; Prob {row['probabilitas']:.1f}%"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Probabilitas", f"{row['probabilitas']:.1f}%")
                    with col2:
                        st.metric("Rata Gain", f"{row['rata_rata_kenaikan']:.1f}%")
                    with col3:
                        st.metric("Max Gain", f"{row['max_kenaikan']:.1f}%")
                    with col4:
                        st.metric("Frekuensi", f"{row['frekuensi']}x")
                    
                    st.markdown(f"""
                    <div style="background: rgba(192,132,252,0.05); border: 1px solid rgba(192,132,252,0.15); 
                                border-radius: 10px; padding: 14px 16px; margin: 12px 0;">
                        <p style="color: #484f58; font-size: 0.68rem; letter-spacing: 2px; text-transform: uppercase;
                                  font-family: 'JetBrains Mono', monospace; margin: 0 0 8px 0;">AI SUMMARY</p>
                        <p style="color: #c9d1d9; font-size: 0.88rem; margin: 0; line-height: 1.6;">{analysis}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    free_float = get_free_float_value(row['saham'])
                    st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)
            
            # ── WATCHLIST ──
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 32px 0 16px 0;">
                <span style="width: 3px; height: 18px; background: #e3b341; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Watchlist Generator</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                min_gain_filter = st.slider("Minimal Gain Rata-rata (%)", 3, 10, 5, key="min_gain")
            with col2:
                top_n = st.number_input("Jumlah Saham", 5, 30, 15, key="top_n")
            
            if 'enhanced_df' in st.session_state:
                df_watchlist = st.session_state['enhanced_df'][st.session_state['enhanced_df']['Gain_Val'] >= min_gain_filter].copy()
            else:
                df_watchlist = enhanced_df[enhanced_df['Gain_Val'] >= min_gain_filter].copy()
            
            if len(df_watchlist) > 0:
                max_prob = df_watchlist['Prob_Val'].max()
                max_gain = df_watchlist['Gain_Val'].max()
                
                if max_prob > 0 and max_gain > 0:
                    df_watchlist['skor'] = (
                        (df_watchlist['Prob_Val'] / max_prob) * 50 +
                        (df_watchlist['Gain_Val'] / max_gain) * 50
                    )
                    df_watchlist = df_watchlist.nlargest(top_n, 'skor')
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0f1a0f 0%, #0a1520 100%);
                            border: 1px solid rgba(227,179,65,0.2); border-radius: 14px;
                            padding: 20px 24px; margin: 16px 0 20px 0;
                            box-shadow: 0 0 30px rgba(227,179,65,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <p style="color: #e3b341; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; 
                                      letter-spacing: 2px; text-transform: uppercase; margin: 0 0 4px 0;">WATCHLIST TRADING</p>
                            <p style="color: #e6edf3; font-size: 1rem; font-weight: 600; margin: 0; font-family: 'Space Grotesk', sans-serif;">
                                {datetime.now().strftime('%d %B %Y')}
                            </p>
                        </div>
                        <div style="background: rgba(227,179,65,0.1); border: 1px solid rgba(227,179,65,0.2); 
                                    padding: 8px 16px; border-radius: 8px;">
                            <span style="color: #e3b341; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 600;">
                                ⚡ PANTAU 15 MENIT PERTAMA
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['Prob_Val'] >= 20 and row['Gain_Val'] >= 7:
                        rekom = "🔥 PRIORITAS"
                    elif row['Prob_Val'] >= 15 and row['Gain_Val'] >= 5:
                        rekom = "⚡ LAYAK"
                    else:
                        rekom = "📌 PANTAU"
                    
                    level_singkat = {'💎 Blue Chip': 'BC', '📈 Second Liner': 'SL', '🎯 Third Liner': 'TL'}.get(row['Level'], '')
                    
                    watchlist_data.append({
                        "Rank": i + 1,
                        "Saham": row['Saham'],
                        "Lvl": level_singkat,
                        "Prob": row['Prob'],
                        "Gain": row['Gain'],
                        "FF": row['FF'],
                        "FCA": row['FCA'],
                        "Pot": row['Pot'],
                        "Rekom": rekom
                    })
                
                watchlist_df = pd.DataFrame(watchlist_data)
                st.session_state['watchlist_df'] = watchlist_df
                st.dataframe(watchlist_df, use_container_width=True, hide_index=True, height=400)
                
                # ── EXPORT ──
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 10px; margin: 28px 0 12px 0;">
                    <span style="width: 3px; height: 18px; background: #4da6ff; border-radius: 2px; display: inline-block;"></span>
                    <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                              font-family: 'JetBrains Mono', monospace; margin: 0;">Export Data</p>
                </div>
                """, unsafe_allow_html=True)
                
                tab_exp1, tab_exp2 = st.tabs(["📋 Watchlist", "📊 Hasil Scanning"])
                
                with tab_exp1:
                    if 'watchlist_df' in st.session_state and st.session_state['watchlist_df'] is not None:
                        create_download_buttons(st.session_state['watchlist_df'], "watchlist", "watchlist_tab")
                
                with tab_exp2:
                    if 'display_df' in st.session_state:
                        create_download_buttons(st.session_state['display_df'], "scan", "scan_tab")
            
            else:
                st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%")
        
        else:
            st.markdown("""
            <div style="background: rgba(255,92,92,0.06); border: 1px solid rgba(255,92,92,0.2); 
                        border-radius: 12px; padding: 24px; text-align: center; margin: 16px 0;">
                <p style="color: #ff5c5c; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin: 0;">
                    ⚠ &nbsp; Tidak ditemukan saham dengan kriteria Open = Low
                </p>
            </div>
            """, unsafe_allow_html=True)


# ========== LOW FLOAT SCANNER ==========
elif "Low Float" in scan_mode:
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 24px;">
        <span style="width: 3px; height: 24px; background: linear-gradient(180deg, #4da6ff, transparent); 
                     border-radius: 2px; display: inline-block;"></span>
        <h2 style="color: #e6edf3; font-size: 1.1rem; font-weight: 600; margin: 0; letter-spacing: 0.3px; font-family: 'Space Grotesk', sans-serif;">
            Scanner Low Float &nbsp;<span style="color: #484f58; font-weight: 400; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;">+ FREE FLOAT + FCA</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        max_ff = st.slider("Maks Free Float (%)", 1, 50, 20)
    with col2:
        min_vol = st.number_input("Min Volume", min_value=0, value=0, step=100000)
    
    st.markdown("""<p style="color: #484f58; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; 
                  font-family: 'JetBrains Mono', monospace; margin: 16px 0 10px 0;">FILTER TINGKATAN</p>""", unsafe_allow_html=True)
    
    col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
    with col_lvl1:
        scan_blue = st.checkbox("💎 Blue Chip", value=True)
    with col_lvl2:
        scan_second = st.checkbox("📈 Second Liner", value=True)
    with col_lvl3:
        scan_third = st.checkbox("🎯 Third Liner", value=True)
    
    col_par1, col_par2 = st.columns([1, 2])
    with col_par1:
        use_parallel = st.checkbox("⚡ Parallel Scanning", value=True)
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    if st.button("🚀  SCAN LOW FLOAT", type="primary", use_container_width=True):
        reset_session_data()
        
        selected_levels = []
        if scan_blue: selected_levels.append('Blue Chip')
        if scan_second: selected_levels.append('Second Liner')
        if scan_third: selected_levels.append('Third Liner')
        
        if selected_stocks:
            stocks_to_scan = selected_stocks
        else:
            stocks_to_scan = get_stocks_by_level(selected_levels) if selected_levels else STOCKS_LIST
        
        start_time = time.time()
        
        if use_parallel:
            results = scan_stocks_parallel(stocks_to_scan, scan_low_float, max_public_float=max_ff, min_volume=min_vol)
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            for i, stock in enumerate(stocks_to_scan):
                status_text.markdown(f"<span style='color:#8b949e; font-family:monospace; font-size:0.82rem;'>Memproses {stock}... ({i+1}/{len(stocks_to_scan)})</span>", unsafe_allow_html=True)
                try:
                    result = scan_low_float([stock], max_ff, min_vol)
                    if result: results.extend(result)
                except: pass
                progress_bar.progress((i + 1) / len(stocks_to_scan))
                time.sleep(0.3)
            progress_bar.empty()
            status_text.empty()
        
        total_time = time.time() - start_time
        
        if results:
            df_results = pd.DataFrame(results)
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0d1a24 0%, #0d1f1a 100%);
                        border: 1px solid rgba(77,166,255,0.2); border-radius: 16px;
                        padding: 24px 28px; margin: 20px 0 28px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
                    <div>
                        <p style="color: #4da6ff; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; 
                                  letter-spacing: 2px; text-transform: uppercase; margin: 0 0 6px 0;">SCAN BERHASIL</p>
                        <p style="color: #e6edf3; font-size: 2.5rem; font-weight: 700; margin: 0; 
                                  font-family: 'JetBrains Mono', monospace; line-height: 1;">{len(df_results)}<span style="color: #4da6ff;">.</span></p>
                        <p style="color: #8b949e; font-size: 0.82rem; margin: 6px 0 0 0;">Saham Low Float &lt; {max_ff}%</p>
                    </div>
                    <div style="text-align: center; padding: 12px 20px; background: rgba(255,255,255,0.03); 
                                border-radius: 10px; border: 1px solid #21262d;">
                        <p style="color: #484f58; font-size: 0.68rem; letter-spacing: 1.5px; text-transform: uppercase; 
                                  font-family: 'JetBrains Mono', monospace; margin: 0 0 4px 0;">DURASI</p>
                        <p style="color: #e6edf3; font-size: 1.4rem; font-weight: 700; margin: 0; 
                                  font-family: 'JetBrains Mono', monospace;">{total_time:.0f}<span style="color: #484f58; font-size: 0.9rem;">s</span></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 0 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #4da6ff; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Hasil · Free Float · FCA</p>
            </div>
            """, unsafe_allow_html=True)
            
            enriched_results = []
            for _, row in df_results.iterrows():
                saham = row['saham']
                free_float = get_free_float_value(saham)
                kategori_singkat = get_kategori_singkatan(row['category'])
                potensi = analyze_goreng_potential(free_float)
                fca_status = '⚠️' if is_fca(saham) else '—'
                level_singkat = {'💎 Blue Chip': 'BC', '📈 Second Liner': 'SL', '🎯 Third Liner': 'TL'}.get(get_stock_level(saham), '')
                
                holders = get_free_float_holders(saham)
                total_inst_asing = sum((p['persen'] / free_float) * 100 for p in holders if free_float > 0)
                sisa_ritel = 100 - total_inst_asing
                
                enriched_results.append({
                    'Saham': saham, 'Lvl': level_singkat,
                    'FF': f"{free_float:.0f}%", 'Kat': kategori_singkat,
                    'Vol(M)': f"{row['volume_avg']/1e6:.1f}", 'Volat': f"{row['volatility']:.0f}%",
                    'Inst': f"{total_inst_asing:.0f}%", 'Ritel': f"{sisa_ritel:.0f}%",
                    'FCA': fca_status, 'Pot': potensi
                })
            
            enriched_df = pd.DataFrame(enriched_results)
            st.dataframe(enriched_df, use_container_width=True, height=500, hide_index=True)
            
            st.session_state['low_float_results'] = df_results
            st.session_state['low_float_enriched'] = enriched_df
            
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 28px 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #00d4aa; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Detail Free Float · Top 5</p>
            </div>
            """, unsafe_allow_html=True)
            
            for _, row in df_results.head(5).iterrows():
                free_float = get_free_float_value(row['saham'])
                with st.expander(f"{row['saham']}  ·  {get_stock_level(row['saham'])}  ·  FF {free_float:.0f}%"):
                    st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)
            
            # Charts
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 28px 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #e3b341; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Distribusi & Analitik</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                counts = df_results['category'].value_counts()
                fig = go.Figure(go.Pie(
                    labels=counts.index,
                    values=counts.values,
                    hole=0.55,
                    marker=dict(
                        colors=['#00d4aa', '#0099cc', '#4da6ff', '#c084fc', '#e3b341'],
                        line=dict(color='#0d1117', width=2)
                    ),
                    textfont=dict(color='#e6edf3', family='JetBrains Mono', size=10)
                ))
                fig.update_layout(
                    plot_bgcolor='#0d1117', paper_bgcolor='#0d1117',
                    font=dict(color='#8b949e', family='JetBrains Mono', size=10),
                    legend=dict(font=dict(color='#8b949e', size=9)),
                    title=dict(text='Kategori Float', font=dict(color='#8b949e', size=11), x=0.5),
                    height=300, margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure()
                vol_max = df_results['volume_avg'].max()
                marker_sizes = (df_results['volume_avg'] / vol_max * 20 + 5).tolist() if vol_max > 0 else [8] * len(df_results)
                fig.add_trace(go.Scatter(
                    x=df_results['public_float'].tolist(),
                    y=df_results['volatility'].tolist(),
                    mode='markers',
                    marker=dict(
                        size=marker_sizes,
                        color=df_results['volatility'].tolist(),
                        colorscale='Teal',
                        opacity=0.8,
                        line=dict(width=0)
                    ),
                    text=df_results['saham'].tolist(),
                    hovertemplate='<b>%{text}</b><br>Float: %{x:.1f}%<br>Volatilitas: %{y:.1f}%<extra></extra>'
                ))
                fig.update_layout(
                    plot_bgcolor='#0d1117', paper_bgcolor='#0d1117',
                    font=dict(color='#8b949e', family='JetBrains Mono', size=10),
                    xaxis=dict(gridcolor='#21262d', title=dict(text='Free Float (%)', font=dict(color='#484f58', size=10))),
                    yaxis=dict(gridcolor='#21262d', title=dict(text='Volatilitas (%)', font=dict(color='#484f58', size=10))),
                    title=dict(text='FF vs Volatilitas', font=dict(color='#8b949e', size=11), x=0.5),
                    height=300, margin=dict(l=50, r=20, t=40, b=50),
                    hoverlabel=dict(bgcolor='#161b22', bordercolor='#30363d', font=dict(color='#e6edf3'))
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Export
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 28px 0 12px 0;">
                <span style="width: 3px; height: 18px; background: #4da6ff; border-radius: 2px; display: inline-block;"></span>
                <p style="color: #8b949e; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; 
                          font-family: 'JetBrains Mono', monospace; margin: 0;">Export Data</p>
            </div>
            """, unsafe_allow_html=True)
            
            tab_exp1, tab_exp2 = st.tabs(["📊 Hasil Low Float", "📋 Info"])
            with tab_exp1:
                create_download_buttons(
                    st.session_state.get('low_float_enriched', enriched_df),
                    "low_float", "low_float_tab"
                )
            with tab_exp2:
                st.info("Gunakan hasil di atas untuk analisis lebih lanjut bro!")
        
        else:
            st.markdown("""
            <div style="background: rgba(255,92,92,0.06); border: 1px solid rgba(255,92,92,0.2); 
                        border-radius: 12px; padding: 24px; text-align: center; margin: 16px 0;">
                <p style="color: #ff5c5c; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin: 0;">
                    ⚠ &nbsp; Tidak ditemukan saham low float
                </p>
            </div>
            """, unsafe_allow_html=True)


# ========== FOOTER ==========
st.markdown("""
<div style="border-top: 1px solid #21262d; margin-top: 48px; padding-top: 20px; padding-bottom: 24px;
            display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px;">
    <div>
        <p style="color: #30363d; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; 
                  letter-spacing: 0.5px; margin: 0 0 4px 0;">
            ⚠ &nbsp; Data bersifat edukatif, bukan rekomendasi investasi
        </p>
        <p style="color: #30363d; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; margin: 0;">
            BC=Blue Chip &nbsp;·&nbsp; SL=Second Liner &nbsp;·&nbsp; TL=Third Liner &nbsp;·&nbsp; FF=Free Float &nbsp;·&nbsp; FCA=Full Call Auction
        </p>
    </div>
    <div style="text-align: right;">
        <p style="color: #30363d; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; margin: 0;">
            RADAR AKSARA &nbsp;·&nbsp; IDX Scanner &nbsp;·&nbsp; Data: Yahoo Finance · KSEI · BEI
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
