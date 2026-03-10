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
    """Mengembalikan tingkatan saham"""
    if stock_code in BLUE_CHIP_STOCKS:
        return 'Blue Chip'
    elif stock_code in SECOND_LINER_STOCKS:
        return 'Second Liner'
    else:
        return 'Third Liner'

def get_stocks_by_level(levels):
    """Mengembalikan daftar saham berdasarkan tingkatan yang dipilih"""
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
    'TPIA': {
        'pemegang': [
            {'nama': 'GIC Singapore', 'persen': 3.45, 'tipe': 'Asing', 'catatan': 'Masuk Jan 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 91.52,
        'total_shares': 1122334455,
        'insider_activity': []
    },
    'TRIM': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah Des 2025', 'update': 'Feb 2026'}
        ],
        'free_float': 63.17,
        'total_shares': 9988776655,
        'insider_activity': []
    },
    'MDKA': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'Pemerintah Norwegia', 'persen': 1.08, 'tipe': 'Asing', 'catatan': 'Masuk Q1 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 89.31,
        'total_shares': 8877665544,
        'insider_activity': [
            {'tanggal': '15 Feb 2026', 'insider': 'Dirut', 'aksi': 'BELI', 'jumlah': 200000, 'harga': 2500}
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
    'INDF': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 3.74, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 92.52,
        'total_shares': 8765432100,
        'insider_activity': []
    },
    'CBDK': {
        'pemegang': [],
        'free_float': 99.07,
        'total_shares': 1122334455,
        'insider_activity': [
            {'tanggal': '18 Feb 2026', 'insider': 'Grup Salim', 'aksi': 'JUAL', 'jumlah': 50000000, 'harga': 1500}
        ]
    },
    'BYAN': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.33, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 58.45,
        'total_shares': 10000000000,
        'insider_activity': []
    },
    'BHIT': {
        'pemegang': [],
        'free_float': 96.88,
        'total_shares': 5566778899,
        'insider_activity': []
    },
    'MAYA': {
        'pemegang': [],
        'free_float': 80.66,
        'total_shares': 4455667788,
        'insider_activity': []
    },
    'AALI': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.18, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 97.82,
        'total_shares': 3344556677,
        'insider_activity': []
    },
    'ASII': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.74, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 97.26,
        'total_shares': 9988776655,
        'insider_activity': []
    },
    'BBNI': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 3.51, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 96.49,
        'total_shares': 8877665544,
        'insider_activity': []
    },
    'BBRI': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.09, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 98.91,
        'total_shares': 123456789000,
        'insider_activity': [
            {'tanggal': '09 Mar 2026', 'insider': 'Dirut', 'aksi': 'JUAL', 'jumlah': 50000, 'harga': 5800}
        ]
    },
    'AKRA': {
        'pemegang': [
            {'nama': 'Pemerintah Norwegia', 'persen': 3.03, 'tipe': 'Asing', 'catatan': 'Aktif nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 96.97,
        'total_shares': 4455667788,
        'insider_activity': []
    },
    'KLBF': {
        'pemegang': [
            {'nama': 'Pemerintah Norwegia', 'persen': 1.30, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.01, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 96.69,
        'total_shares': 5566778899,
        'insider_activity': []
    },
    'ARTO': {
        'pemegang': [
            {'nama': 'Pemerintah Singapura', 'persen': 8.28, 'tipe': 'Asing', 'catatan': 'Masuk besar', 'update': 'Feb 2026'}
        ],
        'free_float': 91.72,
        'total_shares': 1122334455,
        'insider_activity': []
    },
    'MTEL': {
        'pemegang': [
            {'nama': 'Pemerintah Singapura', 'persen': 5.33, 'tipe': 'Asing', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 94.67,
        'total_shares': 2233445566,
        'insider_activity': []
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
        return 'UT'
    elif free_float < 15:
        return 'ST'
    elif free_float < 25:
        return 'TG'
    elif free_float < 40:
        return 'SD'
    else:
        return 'RD'

# ========== PREMIUM STYLING ==========
st.set_page_config(
    page_title="Screener Saham Indonesia Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Headers */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .subtitle {
        color: #94a3b8;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px 32px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    /* Success Box */
    .success-container {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .success-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .success-title {
        font-size: 3rem;
        font-weight: 800;
        color: #34d399;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    /* DataFrames */
    .stDataFrame {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.5);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94a3b8;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 20px;
        font-weight: 600;
        color: #e2e8f0;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Selectbox & Inputs */
    .stSelectbox, .stSlider, .stNumberInput {
        background: rgba(30, 41, 59, 0.5);
    }
    
    /* Custom Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-blue-chip {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-second {
        background: rgba(168, 85, 247, 0.2);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }
    
    .badge-third {
        background: rgba(236, 72, 153, 0.2);
        color: #f472b6;
        border: 1px solid rgba(236, 72, 153, 0.3);
    }
    
    .badge-potential {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Watchlist Header */
    .watchlist-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
        margin: 24px 0;
    }
    
    .watchlist-hero::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.3;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 32px 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.875rem;
        padding: 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #667eea; font-size: 1.5rem; font-weight: 700; margin: 0;">📈 Pro Screener</h1>
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 8px;">Professional Trading Tools</p>
        </div>
    """, unsafe_allow_html=True)
    
    scan_mode = st.radio(
        "**Mode Scanning**",
        ["📈 Open = Low Scanner", "🔍 Low Float Scanner"],
        index=0,
        help="Pilih metode scanning saham"
    )
    
    st.markdown("---")
    
    st.markdown("### 🎯 Filter Universe")
    filter_type = st.radio(
        "Filter Type:",
        ["Semua Saham", "Pilih Manual", "Filter Tingkatan"],
        index=0,
        help="Pilih metode filter saham"
    )
    
    selected_stocks = []
    selected_levels = []
    
    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect(
            "Pilih Saham Target:",
            options=STOCKS_LIST,
            default=[],
            help="Pilih spesifik saham untuk di-scan"
        )
    elif filter_type == "Filter Tingkatan":
        selected_levels = st.multiselect(
            "Tingkatan Saham:",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
            help="Filter berdasarkan kapitalisasi pasar"
        )
        
        if selected_levels:
            stocks_count = len(get_stocks_by_level(selected_levels))
            est_time = stocks_count * 0.5 / 60
            st.info(f"📊 **{stocks_count}** saham dipilih\n\n⏱️ Estimasi: **{est_time:.1f}** menit")
    
    st.markdown("---")
    
    with st.expander("ℹ️ Informasi"):
        st.markdown("""
            **Kategori Saham:**
            - 💎 **Blue Chip**: > Rp10T
            - 📈 **Second Liner**: Rp500M - Rp10T  
            - 🎯 **Third Liner**: < Rp1T
            
            **Legenda:**
            - **FF**: Free Float %
            - **FCA**: Full Call Auction
            - **UT/ST/TG**: Ultra/Sangat/Tinggi
            - **SD/RD**: Sedang/Rendah
        """)
    
    st.markdown("---")
    st.caption("© 2026 Pro Screener v2.0")

# ========== MAIN CONTENT ==========
st.markdown('<h1 class="main-title">📊 Screener Saham Indonesia</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Advanced Pattern Recognition & Float Analysis System</p>', unsafe_allow_html=True)

if "Open = Low" in scan_mode:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periode = st.selectbox(
            "📅 Periode Analisis",
            ["7 Hari", "14 Hari", "30 Hari", "90 Hari", "180 Hari", "365 Hari"],
            index=2,
            help="Rentang waktu analisis historis"
        )
    
    with col2:
        min_kenaikan = st.slider(
            "📈 Minimal Kenaikan (%)", 
            1, 20, 5,
            help="Filter minimal kenaikan harga"
        )
    
    with col3:
        limit_saham = st.number_input(
            "🎯 Limit Hasil", 
            min_value=5, 
            max_value=100, 
            value=20,
            help="Batas jumlah saham ditampilkan"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Scan Options
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        scan_option = st.radio(
            "⚡ Kecepatan Scanning:",
            ["Cepat (50 saham)", "Lengkap (Semua saham)"],
            index=0,
            horizontal=True
        )
    
    with col2:
        st.info("💡 **Tips:** Gunakan filter tingkatan untuk hasil lebih cepat dan relevan")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
            if scan_option == "Cepat (50 saham)":
                stocks_to_scan = STOCKS_LIST[:50]
            else:
                stocks_to_scan = STOCKS_LIST
        
        estimasi_detik = len(stocks_to_scan) * 0.5
        estimasi_menit = estimasi_detik / 60
        
        # Progress Container
        progress_container = st.container()
        with progress_container:
            if estimasi_menit > 2:
                st.warning(f"⏱️ Memproses **{len(stocks_to_scan)}** saham | Estimasi: **{estimasi_menit:.1f}** menit")
            else:
                st.info(f"📊 Memproses **{len(stocks_to_scan)}** saham | Estimasi: **{estimasi_detik:.0f}** detik")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        start_time = time.time()
        
        for i, stock in enumerate(stocks_to_scan):
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(stocks_to_scan) - (i + 1))
            
            status_text.text(f"🔍 Analyzing {stock}... ({i+1}/{len(stocks_to_scan)}) | ⏱️ {elapsed:.0f}s | ⏳ {remaining:.0f}s")
            
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
            
            # Success Animation
            st.markdown(f"""
                <div class="success-container">
                    <div class="success-title">✨ SCAN BERHASIL</div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 24px; position: relative; z-index: 1;">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: 800; color: white;">{len(df_results)}</div>
                            <div style="color: #94a3b8; font-size: 0.875rem;">SAHAM TERDETEKSI</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: 800; color: white;">{total_time:.0f}s</div>
                            <div style="color: #94a3b8; font-size: 0.875rem;">WAKTU PROSES</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: 800; color: white;">{periode}</div>
                            <div style="color: #94a3b8; font-size: 0.875rem;">PERIODE ANALISIS</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Enhanced Results Table
            st.markdown("### 📋 Hasil Analisis Komprehensif")
            
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
                
                # Badge styling
                level_badge = {
                    'Blue Chip': '<span class="badge badge-blue-chip">💎 BLUE CHIP</span>',
                    'Second Liner': '<span class="badge badge-second">📈 SECOND</span>',
                    'Third Liner': '<span class="badge badge-third">🎯 THIRD</span>'
                }.get(level, level)
                
                potensi_badge = f'<span class="badge badge-potential">{potensi}</span>' if potensi in ['UT', 'ST'] else f'<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3);">{potensi}</span>'
                
                enhanced_results.append({
                    'Saham': saham,
                    'Level': level_badge,
                    'Frek': f"{row['frekuensi']}x",
                    'Probabilitas': f"{row['probabilitas']:.1f}%",
                    'Avg Gain': f"{row['rata_rata_kenaikan']:.1f}%",
                    'Max Gain': f"{row['max_kenaikan']:.1f}%",
                    'Free Float': f"{free_float:.1f}%",
                    'Inst/Asing': f"{total_inst_asing:.1f}%",
                    'Ritel': f"{sisa_ritel:.1f}%",
                    'FCA': fca_status,
                    'Potensi': potensi_badge
                })
            
            enhanced_df = pd.DataFrame(enhanced_results)
            st.dataframe(
                enhanced_df,
                use_container_width=True,
                height=600,
                hide_index=True
            )
            
            # Top Performers Chart
            st.markdown("### 📊 Top Performers")
            fig = px.bar(
                df_results.head(10),
                x='saham',
                y='frekuensi',
                title="Top 10 Saham dengan Frekuensi Tertinggi",
                labels={'saham': 'Kode Saham', 'frekuensi': 'Frekuensi Pola'},
                color='probabilitas',
                color_continuous_scale='Viridis',
                template='plotly_dark'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=500,
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # AI Analysis Section
            st.markdown("## 🤖 AI Analysis")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                analysis = analyze_pattern(row.to_dict())
                level = get_stock_level(row['saham'])
                
                with st.expander(f"📊 {row['saham']} | {level} | Prob: {row['probabilitas']:.1f}%"):
                    cols = st.columns(4)
                    metrics = [
                        ("🎯 Probabilitas", f"{row['probabilitas']:.1f}%"),
                        ("💰 Avg Gain", f"{row['rata_rata_kenaikan']:.1f}%"),
                        ("📈 Max Gain", f"{row['max_kenaikan']:.1f}%"),
                        ("🔢 Frekuensi", f"{row['frekuensi']}x")
                    ]
                    
                    for col, (label, value) in zip(cols, metrics):
                        with col:
                            st.metric(label, value)
                    
                    st.markdown("**📝 Analisis AI:**")
                    st.info(analysis)
                    
                    free_float = get_free_float_value(row['saham'])
                    holders = get_free_float_holders(row['saham'])
                    
                    st.markdown("**🏦 Komposisi Free Float:**")
                    holder_cols = st.columns([2, 1, 1])
                    with holder_cols[0]:
                        st.progress(free_float/100, text=f"Free Float: {free_float:.1f}%")
                    
                    total_inst = sum([(p['persen']/free_float)*100 for p in holders]) if holders else 0
                    with holder_cols[1]:
                        st.progress(total_inst/100, text=f"Inst/Asing: {total_inst:.1f}%")
                    with holder_cols[2]:
                        st.progress((100-total_inst)/100, text=f"Ritel: {100-total_inst:.1f}%")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Watchlist Generator
            st.markdown("## 📋 Smart Watchlist Generator")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                min_gain_filter = st.slider("🎯 Minimal Gain (%)", 3, 10, 5, key="wl_gain")
            with col2:
                top_n = st.number_input("📊 Jumlah Saham", 5, 30, 15, key="wl_count")
            
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
                    <div class="watchlist-hero">
                        <h2 style="margin: 0; font-size: 2rem; font-weight: 700;">📋 WATCHLIST PRIORITAS</h2>
                        <p style="margin: 8px 0; opacity: 0.9; font-size: 1.1rem;">{datetime.now().strftime('%d %B %Y')}</p>
                        <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Fokus pada 15 menit pertama market open</p>
                    </div>
                """, unsafe_allow_html=True)
                
                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7:
                        rekom = "🔥 PRIORITAS"
                        rekom_color = "#ef4444"
                    elif row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5:
                        rekom = "⚡ LAYAK"
                        rekom_color = "#f59e0b"
                    else:
                        rekom = "📌 PANTAU"
                        rekom_color = "#6b7280"
                    
                    free_float = get_free_float_value(row['saham'])
                    potensi = analyze_goreng_potential(free_float)
                    fca_status = '⚠️' if is_fca(row['saham']) else ''
                    level_code = {'Blue Chip': 'BC', 'Second Liner': 'SL', 'Third Liner': 'TL'}.get(get_stock_level(row['saham']), '')
                    
                    watchlist_data.append({
                        "Rank": i + 1,
                        "Saham": row['saham'],
                        "Level": level_code,
                        "Prob": f"{row['probabilitas']:.0f}%",
                        "Gain": f"{row['rata_rata_kenaikan']:.0f}%",
                        "FF": f"{free_float:.0f}%",
                        "FCA": fca_status,
                        "Pot": potensi,
                        "Rekomendasi": rekom
                    })
                
                watchlist_df = pd.DataFrame(watchlist_data)
                
                # Color coding for rekomendasi
                def color_rekom(val):
                    color = '#ef4444' if 'PRIORITAS' in val else '#f59e0b' if 'LAYAK' in val else '#6b7280'
                    return f'color: {color}; font-weight: 600;'
                
                styled_wl = watchlist_df.style.applymap(color_rekom, subset=['Rekomendasi'])
                st.dataframe(styled_wl, use_container_width=True, hide_index=True, height=400)
                
                st.info("💡 **Tips:** Fokus pada saham dengan label 🔥 **PRIORITAS** dan potensi **UT/ST**. Waspadai ⚠️ **FCA** (volatilitas ekstrem).")
                
                # Export
                st.markdown("### 📥 Export Data")
                col_w1, col_w2 = st.columns(2)
                
                with col_w1:
                    csv_data = watchlist_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📊 Download CSV", csv_data, f"watchlist_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
                
                with col_w2:
                    excel_data = export_to_excel(watchlist_df)
                    if excel_data:
                        st.download_button("📈 Download Excel", excel_data, f"watchlist_{datetime.now().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Export Full Results
            st.markdown("### 📥 Export Hasil Lengkap")
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                csv_data_scan = enhanced_df.to_csv(index=False).encode('utf-8')
                st.download_button("📊 CSV Full Results", csv_data_scan, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
            
            with col_exp2:
                excel_data_scan = export_to_excel(enhanced_df)
                if excel_data_scan:
                    st.download_button("📈 Excel Full Results", excel_data_scan, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.error("❌ Tidak ditemukan saham dengan pola Open=Low pada kriteria yang dipilih")

elif "Low Float" in scan_mode:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🔍 Low Float Scanner</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_ff = st.slider("📊 Maksimal Free Float (%)", 1, 50, 20, help="Batas maksimal free float")
    
    with col2:
        min_vol = st.number_input("📈 Minimal Volume", min_value=0, value=0, step=100000, help="Filter volume rata-rata")
    
    st.markdown("### 🏷️ Filter Tingkatan")
    col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
    with col_lvl1:
        scan_blue = st.checkbox("Blue Chip 💎", value=True)
    with col_lvl2:
        scan_second = st.checkbox("Second Liner 📈", value=True)
    with col_lvl3:
        scan_third = st.checkbox("Third Liner 🎯", value=True)
    
    scan_option = st.radio("Mode Scanning:", ["⚡ Cepat", "🐢 Lengkap"], horizontal=True, index=0)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        selected_levels = []
        if scan_blue: selected_levels.append('Blue Chip')
        if scan_second: selected_levels.append('Second Liner')
        if scan_third: selected_levels.append('Third Liner')
        
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
                    <div class="success-container">
                        <div class="success-title">✅ {len(df_results)} SAHAM DITEMUKAN</div>
                        <p style="color: #94a3b8; position: relative; z-index: 1;">Free Float < {max_ff}%</p>
                    </div>
                """, unsafe_allow_html=True)
                
                enriched_results = []
                for _, row in df_results.iterrows():
                    saham = row['saham']
                    free_float = get_free_float_value(saham)
                    kategori = row['category']
                    kategori_singkat = get_kategori_singkatan(kategori)
                    potensi = analyze_goreng_potential(free_float)
                    fca_status = '⚠️' if is_fca(saham) else ''
                    level_code = {'Blue Chip': 'BC', 'Second Liner': 'SL', 'Third Liner': 'TL'}.get(get_stock_level(saham), '')
                    
                    holders = get_free_float_holders(saham)
                    total_inst_asing = sum([(p['persen']/free_float)*100 for p in holders]) if holders else 0
                    sisa_ritel = 100 - total_inst_asing
                    
                    enriched_results.append({
                        'Saham': saham,
                        'Level': level_code,
                        'Free Float': f"{free_float:.1f}%",
                        'Kategori': kategori_singkat,
                        'Volume(M)': f"{row['volume_avg']/1e6:.1f}",
                        'Volatilitas': f"{row['volatility']:.1f}%",
                        'Inst/Asing': f"{total_inst_asing:.1f}%",
                        'Ritel': f"{sisa_ritel:.1f}%",
                        'FCA': fca_status,
                        'Potensi': potensi
                    })
                
                enriched_df = pd.DataFrame(enriched_results)
                st.dataframe(enriched_df, use_container_width=True, height=500, hide_index=True)
                
                # Detail Section
                st.markdown("### 🔍 Detail Analisis")
                for _, row in df_results.head(5).iterrows():
                    free_float = get_free_float_value(row['saham'])
                    with st.expander(f"📊 {row['saham']} | FF: {free_float:.1f}% | {get_stock_level(row['saham'])}"):
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Free Float", f"{free_float:.1f}%")
                        with cols[1]:
                            st.metric("Volatilitas", f"{row['volatility']:.1f}%")
                        with cols[2]:
                            st.metric("Volume Avg", f"{row['volume_avg']/1e6:.1f}M")
                        
                        holders = get_free_float_holders(row['saham'])
                        if holders:
                            st.markdown("**🏦 Pemegang Saham (>1%):**")
                            for p in holders:
                                st.progress(p['persen']/100, text=f"{p['nama']}: {p['persen']:.2f}% ({p['tipe']})")
                
                # Visualizations
                st.markdown("### 📊 Distribusi & Analisis")
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.pie(
                        values=df_results['category'].value_counts().values,
                        names=df_results['category'].value_counts().index,
                        title="Distribusi Kategori Free Float",
                        template='plotly_dark',
                        hole=0.4
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter, sans-serif")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(
                        df_results,
                        x='public_float',
                        y='volatility',
                        size='volume_avg',
                        color='category',
                        hover_data=['saham'],
                        title="Free Float vs Volatilitas",
                        template='plotly_dark'
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter, sans-serif")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export
                st.markdown("### 📥 Export Data")
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    csv_data = enriched_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📊 Download CSV", csv_data, f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
                
                with col_exp2:
                    excel_data = export_to_excel(enriched_df)
                    if excel_data:
                        st.download_button("📈 Download Excel", excel_data, f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            else:
                st.error("❌ Tidak ditemukan saham low float dengan kriteria yang dipilih")

# Footer
st.markdown("""
    <div class="footer">
        <p>⚠️ <strong>Disclaimer:</strong> Data hanya untuk edukasi, bukan rekomendasi investasi</p>
        <p style="margin-top: 8px; font-size: 0.75rem;">
            BC = Blue Chip | SL = Second Liner | TL = Third Liner | FF = Free Float | FCA = Full Call Auction<br>
            UT = Ultra Tinggi | ST = Sangat Tinggi | TG = Tinggi | SD = Sedang | RD = Rendah
        </p>
    </div>
""", unsafe_allow_html=True)
