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

# ========== CONFIG HALAMAN ==========
st.set_page_config(
    page_title="📈 StockPro Scanner Indonesia",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS - MODERN DESIGN ==========
st.markdown("""
<style>
/* ========== GLOBAL STYLES ========== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

/* Main Background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* Remove default padding */
.stApp > .main > .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* ========== HEADER STYLES ========== */
.main-header {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 50%, #00d2ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
    text-align: center;
    text-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 20px rgba(0, 210, 255, 0.3); }
    to { text-shadow: 0 0 40px rgba(0, 210, 255, 0.6); }
}

.sub-header {
    font-size: 1.3rem;
    color: #a8b2d1;
    font-weight: 500;
    margin-bottom: 2rem;
    text-align: center;
    opacity: 0.9;
}

.info-text {
    font-size: 1rem;
    color: #7f8c8d;
    text-align: center;
    margin-bottom: 2rem;
}

/* ========== CARD STYLES ========== */
.card {
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 25px;
    margin: 15px 0;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
    border-color: rgba(0, 210, 255, 0.3);
}

/* ========== BUTTON STYLES ========== */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 15px 30px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* ========== METRIC STYLES ========== */
.metric-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(102, 126, 234, 0.3);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00d2ff, #3a7bd5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 0.9rem;
    color: #a8b2d1;
    margin-top: 5px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ========== SUCCESS BOX ========== */
.success-box {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    padding: 40px;
    border-radius: 25px;
    margin: 30px 0;
    text-align: center;
    color: white;
    border: 2px solid #ffd700;
    box-shadow: 0 20px 60px rgba(56, 239, 125, 0.4);
    position: relative;
    overflow: hidden;
}

.success-box::before {
    content: '✨';
    position: absolute;
    top: 20px;
    right: 30px;
    font-size: 3rem;
    opacity: 0.3;
    animation: float 3s ease-in-out infinite;
}

.success-box::after {
    content: '🎯';
    position: absolute;
    bottom: 20px;
    left: 30px;
    font-size: 3rem;
    opacity: 0.3;
    animation: float 3s ease-in-out infinite reverse;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

/* ========== WARNING BOX ========== */
.warning-box {
    padding: 20px;
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 152, 0, 0.2) 100%);
    border-left: 5px solid #ffc107;
    border-radius: 10px;
    margin: 20px 0;
    backdrop-filter: blur(5px);
}

/* ========== WATCHLIST HEADER ========== */
.watchlist-header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #1e3c72 100%);
    padding: 30px;
    border-radius: 20px;
    margin: 30px 0;
    text-align: center;
    color: white;
    border: 2px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 10px 40px rgba(30, 60, 114, 0.5);
}

/* ========== DATAFRAME STYLES ========== */
.dataframe-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* ========== SIDEBAR STYLES ========== */
.stSidebar {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.stSidebar .stMarkdown h2 {
    color: #00d2ff;
    font-weight: 700;
}

/* ========== EXPANDER STYLES ========== */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid rgba(102, 126, 234, 0.3);
}

/* ========== PROGRESS BAR ========== */
.stProgress > div > div {
    background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
}

/* ========== BADGE STYLES ========== */
.badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin: 2px;
}

.badge-blue { background: rgba(0, 210, 255, 0.3); color: #00d2ff; }
.badge-green { background: rgba(56, 239, 125, 0.3); color: #38ef7d; }
.badge-gold { background: rgba(255, 215, 0, 0.3); color: #ffd700; }
.badge-red { background: rgba(255, 85, 85, 0.3); color: #ff5555; }
.badge-purple { background: rgba(102, 126, 234, 0.3); color: #667eea; }

/* ========== FREE FLOAT INFO BOX ========== */
.free-float-box {
    background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(50, 50, 50, 0.9) 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    border: 1px solid rgba(255, 215, 0, 0.3);
}

/* ========== FOOTER ========== */
.footer {
    text-align: center;
    color: #666;
    font-size: 0.85rem;
    padding: 30px 0;
    margin-top: 50px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* ========== SCROLLBAR ========== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #667eea);
}
</style>
""", unsafe_allow_html=True)

# ========== HEADER SECTION ==========
st.markdown('<p class="main-header">🚀 StockPro Scanner Indonesia</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Stock Screening dengan AI Analysis & Real-time Data</p>', unsafe_allow_html=True)
st.markdown('<p class="info-text">Open=Low Pattern • Low Float • Free Float • FCA Detection</p>', unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    # Sidebar Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 3rem;">🎯</div>
        <h3 style="color: #00d2ff; margin: 10px 0;">Control Panel</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scan Mode
    st.markdown("### ⚙️ Scan Mode")
    scan_mode = st.radio(
        "**Pilih Mode Scanning:**",
        ["📈 Open = Low Scanner", "🔍 Low Float Scanner"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Filter Section
    st.markdown("### 🎯 Stock Filter")
    filter_type = st.radio(
        "Tipe Filter:",
        ["Semua Saham", "Pilih Manual", "Filter Tingkatan"],
        index=0
    )
    
    selected_stocks = []
    selected_levels = []
    
    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect(
            "Pilih Saham:",
            options=STOCKS_LIST,
            default=[],
            placeholder="Cari saham..."
        )
    elif filter_type == "Filter Tingkatan":
        selected_levels = st.multiselect(
            "Pilih Tingkatan Saham:",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
            help="💎 Blue Chip: > Rp10T | 📈 Second Liner: Rp500M-Rp10T | 🎯 Third Liner: < Rp1T"
        )
        
        if selected_levels:
            stocks_count = len(get_stocks_by_level(selected_levels))
            est_time = stocks_count * 0.5 / 60
            st.info(f"📊 **{stocks_count}** saham | ⏱️ ±**{est_time:.1f}** menit")
    
    st.markdown("---")
    
    # Info Box
    st.markdown("""
    <div class="card">
        <h4 style="color: #ffd700; margin: 0 0 15px 0;">📌 Quick Info</h4>
        <div style="font-size: 0.9rem; color: #a8b2d1; line-height: 1.8;">
            <div><span class="badge badge-blue">DATA</span> Yahoo Finance + KSEI</div>
            <div style="margin-top: 8px;"><span class="badge badge-gold">BLUE CHIP</span> 💎 > Rp10T</div>
            <div style="margin-top: 8px;"><span class="badge badge-purple">SECOND LINER</span> 📈 Rp500M-Rp10T</div>
            <div style="margin-top: 8px;"><span class="badge badge-green">THIRD LINER</span> 🎯 < Rp1T</div>
            <div style="margin-top: 8px;"><span class="badge badge-red">FCA</span> ⚠️ Papan Pemantauan</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown('<p style="text-align: center; color: #666; font-size: 0.8rem;">Made with ❤️ for Indonesian Traders</p>', unsafe_allow_html=True)

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

# ========== SHAREHOLDER DATA ==========
SHAREHOLDER_DATA = {
    'CUAN': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.02, 'tipe': 'Institusi', 'catatan': 'Masuk Q4 2025', 'update': 'Feb 2026'},
            {'nama': 'Vanguard', 'persen': 1.15, 'tipe': 'Asing', 'catatan': 'Nambah Jan 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 13.73,
        'total_shares': 12345678900,
        'insider_activity': [
            {'tanggal': '05 Mar 2026', 'insider': 'Direktur Utama', 'aksi': 'BELI', 'jumlah': 100000, 'harga': 15000},
            {'tanggal': '20 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 50000, 'harga': 14800}
        ]
    },
    'BRPT': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.22, 'tipe': 'Institusi', 'catatan': 'Nambah Feb 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 27.41,
        'total_shares': 8765432100,
        'insider_activity': [
            {'tanggal': '28 Feb 2026', 'insider': 'Komisaris', 'aksi': 'JUAL', 'jumlah': 75000, 'harga': 8500}
        ]
    },
    'BBCA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.06, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'Vanguard', 'persen': 1.23, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 95.67,
        'total_shares': 123456789000,
        'insider_activity': [
            {'tanggal': '10 Mar 2026', 'insider': 'Presdir', 'aksi': 'BELI', 'jumlah': 1000000, 'harga': 10250},
            {'tanggal': '25 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 500000, 'harga': 10100}
        ]
    },
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
    <div class="free-float-box">
        <h4 style="color: #ffd700; margin: 0 0 15px 0; border-bottom: 1px solid rgba(255,215,0,0.3); padding-bottom: 10px;">
            📋 Pemegang Free Float - {stock_code}
        </h4>
    """
    
    if is_fca(stock_code):
        html += f"""<p><span class="badge badge-red">⚠️ FCA - Papan Pemantauan Khusus</span></p>"""
    
    html += f"""
        <div style="display: flex; justify-content: space-between; margin: 15px 0;">
            <span style="color: #a8b2d1;">Free Float:</span>
            <span style="color: #38ef7d; font-weight: bold; font-size: 1.2rem;">{free_float_value:.2f}%</span>
        </div>
    """
    
    if free_float_holders:
        html += "<p style="color: #a8b2d1; margin: 15px 0 10px 0; font-size: 0.9rem;">Pemegang Institusi/Asing >1%:</p>"
        total_dari_ff = 0
        for p in free_float_holders:
            persen_dalam_ff = (p['persen'] / free_float_value) * 100
            total_dari_ff += persen_dalam_ff
            warna_tipe = {'Institusi': '#00d2ff', 'Asing': '#38ef7d'}.get(p['tipe'], '#ffffff')
            html += f"""
                <div style="display: flex; justify-content: space-between; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 8px 0; border-left: 3px solid {warna_tipe};">
                    <span><span style="color: {warna_tipe};">●</span> {p['nama']}</span>
                    <span style="color: #ffd700; font-weight: bold;">{persen_dalam_ff:.1f}%</span>
                </div>
            """
        
        sisa_ritel = 100 - total_dari_ff
        html += f"""
            <div style="display: flex; justify-content: space-between; background: rgba(56,239,125,0.1); padding: 10px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #38ef7d;">
                <span><span style="color: #38ef7d;">●</span> Ritel</span>
                <span style="color: #38ef7d; font-weight: bold;">{sisa_ritel:.1f}%</span>
            </div>
        """
    else:
        html += """
            <div style="display: flex; justify-content: space-between; background: rgba(56,239,125,0.1); padding: 10px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #38ef7d;">
                <span><span style="color: #38ef7d;">●</span> Ritel</span>
                <span style="color: #38ef7d; font-weight: bold;">100%</span>
            </div>
        """
    
    insider = get_insider_activity(stock_code)
    if insider:
        html += "<p style="color: #a8b2d1; margin: 20px 0 10px 0; font-size: 0.9rem;">Aktivitas Insider 30 Hari:</p>"
        for a in insider:
            warna_aksi = '#38ef7d' if a['aksi'] == 'BELI' else '#ff5555'
            html += f"""
                <div style="display: flex; justify-content: space-between; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 8px 0;">
                    <span style="color: #a8b2d1;">{a['tanggal']}</span>
                    <span style="color: {warna_aksi}; font-weight: bold;">{a['aksi']} {a['jumlah']:,}</span>
                </div>
            """
    
    html += "</div>"
    return html

# ========== HELPER FUNCTIONS ==========
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

# ========== MAIN CONTENT ==========
if "Open = Low" in scan_mode:
    # Header Card
    st.markdown("""
    <div class="card">
        <h3 style="color: #00d2ff; margin: 0; text-align: center;">🔍 Open = Low Pattern Scanner</h3>
        <p style="color: #a8b2d1; text-align: center; margin: 10px 0 0 0;">Deteksi saham dengan pola Open = Low + Kenaikan ≥5%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Settings Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        periode = st.selectbox(
            "📅 Periode",
            ["7 Hari", "14 Hari", "30 Hari", "90 Hari", "180 Hari", "365 Hari"],
            index=2,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        min_kenaikan = st.slider(
            "📈 Min Kenaikan (%)",
            1, 20, 5,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        limit_saham = st.number_input(
            "🎯 Limit Hasil",
            min_value=5,
            max_value=100,
            value=20,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Scan Options
    st.markdown("### ⚡ Scan Speed")
    col1, col2 = st.columns([2, 1])
    with col1:
        scan_option = st.radio(
            "Kecepatan:",
            ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )
    with col2:
        st.info("⚡ **Cepat:** ~30s | 🐢 **Lengkap:** ~7-10m")
    
    periode_map = {
        "7 Hari": 7, "14 Hari": 14, "30 Hari": 30,
        "90 Hari": 90, "180 Hari": 180, "365 Hari": 365
    }
    hari = periode_map[periode]
    
    # Scan Button
    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):
        # Determine stocks to scan
        if filter_type == "Pilih Manual" and selected_stocks:
            stocks_to_scan = selected_stocks
        elif filter_type == "Filter Tingkatan" and selected_levels:
            stocks_to_scan = get_stocks_by_level(selected_levels)
        else:
            if scan_option == "⚡ Cepat (50 saham)":
                stocks_to_scan = STOCKS_LIST[:50]
            else:
                stocks_to_scan = STOCKS_LIST
        
        estimasi_detik = len(stocks_to_scan) * 0.5
        estimasi_menit = estimasi_detik / 60
        
        # Warning/Info
        if estimasi_menit > 2:
            st.markdown(f"""
            <div class="warning-box">
                <strong>⏱️ Memproses {len(stocks_to_scan)} saham</strong><br>
                Estimasi waktu: <strong>{estimasi_menit:.1f} menit</strong><br>
                <small>Harap sabar! Jangan refresh halaman.</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"📊 Memproses {len(stocks_to_scan)} saham. Estimasi: {estimasi_detik:.0f} detik")
        
        # Progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        start_time = time.time()
        
        for i, stock in enumerate(stocks_to_scan):
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(stocks_to_scan) - (i + 1))
            status_text.text(
                f"📊 {stock}... ({i+1}/{len(stocks_to_scan)}) | "
                f"Elapsed: {elapsed:.0f}s | Remaining: {remaining:.0f}s"
            )
            
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
            
            # Success Box
            st.markdown(f"""
            <div class="success-box">
                <h1 style="color: white; margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    ✅ SCAN BERHASIL!
                </h1>
                <div style="background: rgba(255,255,255,0.2); padding: 25px; border-radius: 15px; margin: 25px 0;">
                    <p style="color: white; font-size: 3rem; margin: 0; font-weight: 800;">{len(df_results)} SAHAM</p>
                    <p style="color: #ffd700; font-size: 1.2rem; margin: 10px 0 0 0; text-transform: uppercase; letter-spacing: 2px;">
                        Dengan Pola Open=Low
                    </p>
                </div>
                <div style="display: flex; justify-content: center; gap: 50px;">
                    <div>
                        <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;">⏱️ WAKTU</p>
                        <p style="color: white; font-size: 2rem; margin: 5px 0; font-weight: 800;">{total_time:.0f}s</p>
                    </div>
                    <div>
                        <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;">📅 PERIODE</p>
                        <p style="color: white; font-size: 2rem; margin: 5px 0; font-weight: 800;">{periode}</p>
                    </div>
                </div>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin: 25px 0 0 0;">✦ Siap trading cuan ✦</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced Results Table
            st.markdown("### 📋 Hasil Scanning")
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
                fca_status = '⚠️' if is_fca(saham) else ''
                
                enhanced_results.append({
                    'Saham': saham,
                    'Level': level,
                    'Frek': row['frekuensi'],
                    'Prob': f"{row['probabilitas']:.0f}%",
                    'Gain': f"{row['rata_rata_kenaikan']:.0f}%",
                    'FF': f"{free_float:.0f}%",
                    'Inst': f"{total_inst_asing:.0f}%",
                    'Ritel': f"{sisa_ritel:.0f}%",
                    'FCA': fca_status,
                    'Pot': potensi
                })
            
            enhanced_df = pd.DataFrame(enhanced_results)
            
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(enhanced_df, use_container_width=True, height=500, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chart
            st.markdown("### 📊 Top 10 Visualization")
            fig = px.bar(
                df_results.head(10),
                x='saham',
                y='frekuensi',
                title="10 Saham dengan Frekuensi Tertinggi",
                color='probabilitas',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a8b2d1')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Analysis
            st.markdown("### 🤖 AI Analysis")
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                analysis = analyze_pattern(row.to_dict())
                with st.expander(f"📊 {row['saham']} - {get_stock_level(row['saham'])} | Prob: {row['probabilitas']:.1f}%"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🎯 Probabilitas", f"{row['probabilitas']:.1f}%")
                    with col2:
                        st.metric("💰 Avg Gain", f"{row['rata_rata_kenaikan']:.1f}%")
                    with col3:
                        st.metric("📈 Max Gain", f"{row['max_kenaikan']:.1f}%")
                    with col4:
                        st.metric("📊 Frekuensi", f"{row['frekuensi']}x")
                    st.markdown("**📋 AI Conclusion:**")
                    st.markdown(analysis)
                    st.markdown(display_free_float_info(row['saham'], get_free_float_value(row['saham'])), unsafe_allow_html=True)
                    st.markdown("---")
            
            # Watchlist
            st.markdown("### 📋 Watchlist Generator")
            col1, col2 = st.columns(2)
            with col1:
                min_gain_filter = st.slider("🎯 Min Gain (%)", 3, 10, 5, key="min_gain")
            with col2:
                top_n = st.number_input("📊 Jumlah Saham", 5, 30, 15, key="top_n")
            
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
                    <div class="watchlist-header">
                        <h2 style="color: white; margin: 0;">📋 WATCHLIST TRADING</h2>
                        <p style="color: #a8d8ff; font-size: 1.2rem; margin: 10px 0;">{datetime.now().strftime('%d %B %Y')}</p>
                        <p style="color: #ffaa00; margin: 0;">Pantau 15 menit pertama! 🎯</p>
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
                        potensi = analyze_goreng_potential(free_float)
                        fca_status = '⚠️' if is_fca(row['saham']) else ''
                        level_singkat = {
                            '💎 Blue Chip': 'BC',
                            '📈 Second Liner': 'SL',
                            '🎯 Third Liner': 'TL'
                        }.get(get_stock_level(row['saham']), '')
                        
                        watchlist_data.append({
                            "Rank": i + 1,
                            "Saham": row['saham'],
                            "Lvl": level_singkat,
                            "Prob": f"{row['probabilitas']:.0f}%",
                            "Gain": f"{row['rata_rata_kenaikan']:.0f}%",
                            "FF": f"{free_float:.0f}%",
                            "FCA": fca_status,
                            "Pot": potensi,
                            "Rekom": rekom
                        })
                    
                    watchlist_df = pd.DataFrame(watchlist_data)
                    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                    st.dataframe(watchlist_df, use_container_width=True, hide_index=True, height=400)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Export
                    st.markdown("### 📥 Export Watchlist")
                    col_w1, col_w2 = st.columns(2)
                    with col_w1:
                        csv_data = watchlist_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv_data,
                            file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with col_w2:
                        excel_data = export_to_excel(watchlist_df)
                        if excel_data:
                            st.download_button(
                                label="📈 Download Excel",
                                data=excel_data,
                                file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                    
                    st.info("💡 BC=Blue Chip, SL=Second Liner, TL=Third Liner | Fokus 🔥 PRIORITAS dengan 🔥 UT/ST")
                else:
                    st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%")
            
            # Export Scan Data
            st.markdown("### 📥 Export Scan Results")
            col_scan1, col_scan2 = st.columns(2)
            with col_scan1:
                csv_data_scan = enhanced_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📊 CSV",
                    data=csv_data_scan,
                    file_name=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_scan2:
                excel_data_scan = export_to_excel(enhanced_df)
                if excel_data_scan:
                    st.download_button(
                        label="📈 Excel",
                        data=excel_data_scan,
                        file_name=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 30px; border-radius: 20px; text-align: center; color: white; margin: 30px 0;">
                <h2 style="margin: 0;">⚠️ Tidak Ditemukan Saham</h2>
                <p style="margin: 15px 0 0 0; opacity: 0.9;">Tidak ada saham dengan kriteria Open=Low pada periode ini</p>
            </div>
            """, unsafe_allow_html=True)

elif "Low Float" in scan_mode:
    st.markdown("""
    <div class="card">
        <h3 style="color: #38ef7d; margin: 0; text-align: center;">🔍 Low Float Scanner</h3>
        <p style="color: #a8b2d1; text-align: center; margin: 10px 0 0 0;">Deteksi saham dengan free float rendah + potensi high volatility</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        max_ff = st.slider("📊 Max Free Float (%)", 1, 50, 20, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        min_vol = st.number_input("📈 Min Volume", min_value=0, value=0, step=100000, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 🏷️ Filter Tingkatan")
    col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
    with col_lvl1:
        scan_blue = st.checkbox("💎 Blue Chip", value=True)
    with col_lvl2:
        scan_second = st.checkbox("📈 Second Liner", value=True)
    with col_lvl3:
        scan_third = st.checkbox("🎯 Third Liner", value=True)
    
    scan_option = st.radio("Mode:", ["⚡ Cepat", "🐢 Lengkap"], horizontal=True, index=0)
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        selected_levels = []
        if scan_blue:
            selected_levels.append('Blue Chip')
        if scan_second:
            selected_levels.append('Second Liner')
        if scan_third:
            selected_levels.append('Third Liner')
        
        if selected_stocks:
            stocks_to_scan = selected_stocks
        else:
            if selected_levels:
                stocks_to_scan = get_stocks_by_level(selected_levels)
            else:
                stocks_to_scan = STOCKS_LIST[:50] if scan_option == "⚡ Cepat" else STOCKS_LIST
        
        with st.spinner(f"🔍 Scanning {len(stocks_to_scan)} saham..."):
            results = scan_low_float(stocks_to_scan, max_ff, min_vol)
            
            if results:
                df_results = pd.DataFrame(results)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 35px; border-radius: 25px; margin: 30px 0; text-align: center; color: white; border: 2px solid #ffd700; box-shadow: 0 20px 60px rgba(56, 239, 125, 0.4);">
                    <h2 style="color: #ffd700; margin: 0; font-size: 2rem;">✅ BERHASIL</h2>
                    <p style="font-size: 3.5rem; margin: 20px 0; font-weight: 800;">{len(df_results)} SAHAM</p>
                    <p style="font-size: 1.2rem; opacity: 0.9;">Free float < {max_ff}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 📋 Hasil + Free Float + FCA")
                enriched_results = []
                for _, row in df_results.iterrows():
                    saham = row['saham']
                    free_float = get_free_float_value(saham)
                    kategori = row['category']
                    kategori_singkat = get_kategori_singkatan(kategori)
                    potensi = analyze_goreng_potential(free_float)
                    fca_status = '⚠️' if is_fca(saham) else ''
                    level_singkat = {
                        '💎 Blue Chip': 'BC',
                        '📈 Second Liner': 'SL',
                        '🎯 Third Liner': 'TL'
                    }.get(get_stock_level(saham), '')
                    
                    holders = get_free_float_holders(saham)
                    total_inst_asing = 0
                    for p in holders:
                        persen_dalam_ff = (p['persen'] / free_float) * 100 if free_float > 0 else 0
                        total_inst_asing += persen_dalam_ff
                    sisa_ritel = 100 - total_inst_asing
                    
                    enriched_results.append({
                        'Saham': saham,
                        'Lvl': level_singkat,
                        'FF': f"{free_float:.0f}%",
                        'Kat': kategori_singkat,
                        'Vol(M)': f"{row['volume_avg']/1e6:.1f}",
                        'Volat': f"{row['volatility']:.0f}%",
                        'Inst': f"{total_inst_asing:.0f}%",
                        'Ritel': f"{sisa_ritel:.0f}%",
                        'FCA': fca_status,
                        'Pot': potensi
                    })
                
                enriched_df = pd.DataFrame(enriched_results)
                st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                st.dataframe(enriched_df, use_container_width=True, height=500, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Detail
                st.markdown("### 🔍 Free Float Details")
                for _, row in df_results.head(5).iterrows():
                    free_float = get_free_float_value(row['saham'])
                    with st.expander(f"📊 {row['saham']} - {get_stock_level(row['saham'])} | FF: {free_float:.0f}%"):
                        st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)
                
                # Charts
                st.markdown("### 📊 Distribution")
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(
                        values=df_results['category'].value_counts().values,
                        names=df_results['category'].value_counts().index,
                        title="Kategori Free Float"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#a8b2d1')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.scatter(
                        df_results,
                        x='public_float',
                        y='volatility',
                        size='volume_avg',
                        hover_data=['saham'],
                        title="FF vs Volatilitas"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#a8b2d1')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export
                st.markdown("### 📥 Export")
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    csv_data = enriched_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📊 CSV",
                        data=csv_data,
                        file_name=f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_exp2:
                    excel_data = export_to_excel(enriched_df)
                    if excel_data:
                        st.download_button(
                            label="📈 Excel",
                            data=excel_data,
                            file_name=f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
            else:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 30px; border-radius: 20px; text-align: center; color: white; margin: 30px 0;">
                    <h2 style="margin: 0;">⚠️ Tidak Ditemukan Saham</h2>
                    <p style="margin: 15px 0 0 0; opacity: 0.9;">Tidak ada saham low float dengan kriteria ini</p>
                </div>
                """, unsafe_allow_html=True)

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div class="footer">
    <p style="margin: 5px 0;">⚠️ <strong>Data untuk edukasi, bukan rekomendasi trading</strong></p>
    <p style="margin: 5px 0; color: #888;">
        BC=Blue Chip | SL=Second Liner | TL=Third Liner | FF=Free Float | FCA=Full Call Auction
    </p>
    <p style="margin: 5px 0; color: #888;">
        🔥 UT/ST=Ultra/Sangat Tinggi | ⚡ TG=Tinggi | 📊 SD=Sedang | 📉 RD=Rendah
    </p>
    <p style="margin: 20px 0 5px 0; color: #666; font-size: 0.8rem;">
        © 2026 StockPro Scanner Indonesia • Built with Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
