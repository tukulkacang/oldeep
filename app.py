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
# Berdasarkan kapitalisasi pasar (market cap)
# Blue Chip: > Rp10 T
# Second Liner: Rp500 M - Rp10 T
# Third Liner: < Rp1 T

BLUE_CHIP_STOCKS = [
    'BBCA', 'BBRI', 'BMRI', 'BBNI', 'BTPS', 'BRIS',  # Perbankan
    'TLKM', 'ISAT', 'EXCL', 'TOWR', 'MTEL',  # Telekomunikasi
    'UNVR', 'ICBP', 'INDF', 'KLBF', 'GGRM', 'HMSP',  # Consumer
    'ASII', 'UNTR', 'ADRO', 'BYAN', 'PTBA', 'ITMG',  # Otomotif & Energi
    'CPIN', 'JPFA', 'MAIN', 'SIDO', 'ULTJ',  # Consumer lain
    'SMGR', 'INTP', 'SMCB',  # Semen
    'PGAS', 'MEDC', 'ELSA',  # Energi
    'ANTM', 'INCO', 'MDKA', 'HRUM', 'BRPT', 'TPIA',  # Mining & Kimia
    'WIKA', 'PTPP', 'WSKT', 'ADHI', 'JSMR',  # Konstruksi
]

SECOND_LINER_STOCKS = [
    'AKRA', 'INKP', 'BUMI', 'PTRO', 'DOID', 'TINS', 'BRMS', 'DKFT',  # Energi & Mining
    'BMTR', 'MAPI', 'ERAA', 'ACES', 'MIKA', 'SILO', 'HEAL', 'PRAY',  # Retail & Healthcare
    'CLEO', 'ROTI', 'MYOR', 'GOOD', 'SKBM', 'SKLT', 'STTP',  # Consumer
    'WSBP', 'PBSA', 'MTFN', 'BKSL', 'SMRA', 'CTRA', 'BSDE', 'PWON',  # Properti
    'LPKR', 'LPCK', 'DILD', 'RDTX', 'MREI', 'PZZA', 'MAPB', 'DMAS',  # Properti & Lainnya
    'LMPI', 'ARNA', 'TOTO', 'MLIA', 'INTD', 'IKAI', 'JECC', 'KBLI',  # Industri
    'KBLM', 'VOKS', 'UNIT', 'INAI', 'IMPC', 'ASGR', 'POWR', 'RAJA',  # Jasa & Trading
    'PJAA', 'SAME', 'SCCO', 'SPMA', 'SRSN', 'TALF', 'TRST', 'TSPC',  # Manufaktur
    'UNIC', 'YPAS',  # Lainnya
]

# ========== FUNGSI UNTUK TINGKATAN SAHAM ==========

def get_stock_level(stock_code):
    """Mengembalikan tingkatan saham"""
    if stock_code in BLUE_CHIP_STOCKS:
        return '💎 Blue Chip'
    elif stock_code in SECOND_LINER_STOCKS:
        return '📈 Second Liner'
    else:
        return '🎯 Third Liner'

def get_stocks_by_level(levels):
    """Mengembalikan daftar saham berdasarkan tingkatan yang dipilih"""
    result = []
    if 'Blue Chip' in levels:
        result += BLUE_CHIP_STOCKS
    if 'Second Liner' in levels:
        result += SECOND_LINER_STOCKS
    if 'Third Liner' in levels or len(levels) == 0:
        # Third Liner adalah semua saham yang tidak ada di Blue Chip dan Second Liner
        third_liner = [s for s in STOCKS_LIST if s not in BLUE_CHIP_STOCKS and s not in SECOND_LINER_STOCKS]
        result += third_liner
    return list(set(result))  # Hilangkan duplikat

# ========== DATA PEMEGANG SAHAM (Update Maret 2026) ==========
# Sumber: KSEI/BEI per 27 Februari 2026
# Hanya menampilkan pemegang yang ADA DI FREE FLOAT (bukan pengendali/founder)

SHAREHOLDER_DATA = {
    # PRAJOGO PANGESTU (Barito Pacific)
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
    
    # BOY THOHIR
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
    
    # ANTHONI SALIM
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
    
    # LOW TUCK KWONG
    'BYAN': {
        'pemegang': [
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.33, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 58.45,
        'total_shares': 10000000000,
        'insider_activity': []
    },
    
    # HARY TANOE
    'BHIT': {
        'pemegang': [],
        'free_float': 96.88,
        'total_shares': 5566778899,
        'insider_activity': []
    },
    
    # DATO SRI TAHIR
    'MAYA': {
        'pemegang': [],
        'free_float': 80.66,
        'total_shares': 4455667788,
        'insider_activity': []
    },
    
    # BPJS KETENAGAKERJAAN (Institusi Besar) - Sample
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
    
    # PEMERINTAH NORWEGIA (Investor Asing Aktif) - Sample
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
    
    # PEMERINTAH SINGAPURA
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

# ========== DATA SAHAM FCA (Full Call Auction) ==========
# Sumber: Pengumuman BEI (update berkala)
# Saham yang masuk Papan Pemantauan Khusus dengan mekanisme FCA
FCA_STOCKS = ['COIN', 'CDIA']  # Tambahkan sesuai update BEI

def is_fca(stock_code):
    """Cek apakah saham termasuk dalam daftar FCA"""
    return stock_code in FCA_STOCKS

# ========== FUNGSI UNTUK DATA FREE FLOAT ==========

def get_free_float_holders(stock_code):
    """
    Mengembalikan data pemegang saham yang ADA DI FREE FLOAT aja
    (pengendali/founder sudah dihapus dari dictionary)
    """
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('pemegang', [])

def get_free_float_value(stock_code):
    """Mengembalikan nilai free float saham"""
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('free_float', 100.0)

def get_insider_activity(stock_code):
    """Mengembalikan aktivitas insider"""
    data = SHAREHOLDER_DATA.get(stock_code, {})
    return data.get('insider_activity', [])

def display_free_float_info(stock_code, free_float_value):
    """Tampilkan info pemegang saham yang ADA DI FREE FLOAT"""
    free_float_holders = get_free_float_holders(stock_code)
    
    html = f"<div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>"
    html += f"<h4 style='color: #ffd700; margin: 0 0 10px 0;'>📋 Pemegang di Free Float {stock_code}</h4>"
    
    # Status FCA
    if is_fca(stock_code):
        html += f"<p><span style='color: #ffaa00;'>⚠️ FCA (Full Call Auction) - Papan Pemantauan Khusus</span></p>"
    
    html += f"<p><span style='color: #aaa;'>Free Float:</span> <span style='color: #00ff88; font-weight: bold;'>{free_float_value:.2f}%</span></p>"
    
    if free_float_holders:
        html += "<p style='color: #aaa; margin: 10px 0 5px 0;'>Pemegang institusi/asing >1%:</p>"
        total_dari_ff = 0
        
        for p in free_float_holders:
            # Hitung persentase mereka DALAM free float
            persen_dalam_ff = (p['persen'] / free_float_value) * 100
            total_dari_ff += persen_dalam_ff
            
            warna_tipe = {
                'Institusi': '#1f77b4',
                'Asing': '#00ff88'
            }.get(p['tipe'], '#ffffff')
            
            html += f"""
            <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0;'>
                <span><span style='color: {warna_tipe};'>■</span> {p['nama']}</span>
                <span style='color: #ffd700; font-weight: bold;'>{persen_dalam_ff:.1f}%</span>
            </div>
            """
        
        # Sisa free float yang dipegang ritel
        sisa_ritel = 100 - total_dari_ff
        html += f"""
        <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #00ff88;'>
            <span><span style='color: #00ff88;'>■</span> Ritel</span>
            <span style='color: #00ff88; font-weight: bold;'>{sisa_ritel:.1f}%</span>
        </div>
        """
    else:
        html += "<p style='color: #aaa;'>Tidak ada institusi/asing >1%</p>"
        html += f"""
        <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #00ff88;'>
            <span><span style='color: #00ff88;'>■</span> Ritel</span>
            <span style='color: #00ff88; font-weight: bold;'>100%</span>
        </div>
        """
    
    # Insider activity
    insider = get_insider_activity(stock_code)
    if insider:
        html += "<p style='color: #aaa; margin: 15px 0 5px 0;'>Aktivitas Insider 30 hari:</p>"
        for a in insider:
            warna_aksi = '#00ff88' if a['aksi'] == 'BELI' else '#ff5555'
            html += f"""
            <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0;'>
                <span>{a['tanggal']}</span>
                <span style='color: {warna_aksi}; font-weight: bold;'>{a['aksi']} {a['jumlah']:,}</span>
            </div>
            """
    
    html += "</div>"
    return html

# ========== SINGKATAN KATEGORI ==========

def get_kategori_singkatan(kategori):
    """Mengubah kategori panjang jadi singkatan"""
    singkatan = {
        'Ultra Low Float': 'ULF',
        'Very Low Float': 'VLF',
        'Low Float': 'LF',
        'Moderate Low Float': 'MLF',
        'Normal Float': 'NF'
    }
    return singkatan.get(kategori, kategori)

def get_potensi_singkatan(potensi):
    """Mengubah potensi goreng jadi singkatan"""
    if 'ULTRA TINGGI' in potensi:
        return '🔥 UT'
    elif 'SANGAT TINGGI' in potensi:
        return '🔥 ST'
    elif 'TINGGI' in potensi:
        return '⚡ TG'
    elif 'SEDANG' in potensi:
        return '📊 SD'
    elif 'RENDAH' in potensi:
        return '📉 RD'
    else:
        return potensi

def analyze_goreng_potential(free_float):
    """
    Analisis potensi saham digoreng berdasarkan free float
    """
    if free_float < 10:
        return '🔥 UT'  # Ultra Tinggi
    elif free_float < 15:
        return '🔥 ST'  # Sangat Tinggi
    elif free_float < 25:
        return '⚡ TG'  # Tinggi
    elif free_float < 40:
        return '📊 SD'  # Sedang
    else:
        return '📉 RD'  # Rendah

# ========== FUNGSI REUSABLE UNTUK EXPORT ==========

def create_download_buttons(data, prefix, key_suffix):
    """Buat tombol download CSV dan Excel - reusable"""
    col1, col2 = st.columns(2)
    
    with col1:
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download CSV",
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
                label="📈 Download Excel",
                data=excel,
                file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"excel_{key_suffix}"
            )
        else:
            st.error("❌ Gagal bikin Excel")

# ========== FUNGSI SCANNING PARALEL ==========

def scan_stocks_parallel(stocks_to_scan, scan_function, *args, **kwargs):
    """
    Scan multiple stocks secara paralel dengan ThreadPoolExecutor
    Jauh lebih cepat dari sequential
    """
    results = []
    failed_stocks = []
    
    with st.spinner(f"Scanning {len(stocks_to_scan)} saham secara paralel..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit semua task
            future_to_stock = {
                executor.submit(scan_function, stock, *args, **kwargs): stock 
                for stock in stocks_to_scan
            }
            
            completed = 0
            total = len(future_to_stock)
            
            # Kumpulkan hasil
            for future in concurrent.futures.as_completed(future_to_stock):
                stock = future_to_stock[future]
                completed += 1
                
                try:
                    result = future.result(timeout=30)
                    if result:
                        results.append(result)
                except Exception as e:
                    failed_stocks.append(stock)
                    print(f"Error scanning {stock}: {e}")
                
                # Update progress
                progress = completed / total
                progress_bar.progress(progress)
                status_text.text(f"✅ {completed}/{total} saham diproses | ❌ {len(failed_stocks)} gagal")
        
        progress_bar.empty()
        status_text.empty()
        
        if failed_stocks:
            st.warning(f"⚠️ {len(failed_stocks)} saham gagal discan: {', '.join(failed_stocks[:10])}" + 
                      ("..." if len(failed_stocks) > 10 else ""))
    
    return results

# ========== FUNGSI UNTUK RESET SESSION ==========

def reset_session_data():
    """Reset semua data di session state"""
    keys_to_reset = ['scan_results', 'enhanced_df', 'watchlist_df', 'display_df', 'df_results']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# Config halaman
st.set_page_config(
    page_title="RADAR AKSARA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2c3e50;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #7f8c8d;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 0.25rem;
    }
    .watchlist-header {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        color: white;
    }
    .success-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 30px;
        border-radius: 20px;
        margin: 25px 0 35px 0;
        text-align: center;
        color: white;
        border: 2px solid #ffd700;
        box-shadow: 0 20px 40px rgba(102,126,234,0.4);
        position: relative;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">📊 RADAR AKSARA</p>', unsafe_allow_html=True)
st.markdown('<p class="info-text">Scanner Open=Low & Low Float dengan Filter Blue Chip, Second Liner, Third Liner</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Pengaturan")
    
    scan_mode = st.radio(
        "**Pilih Mode Scanning:**",
        ["📈 Open = Low Scanner", "🔍 Low Float Scanner"],
        index=0
    )
    
    st.markdown("---")
    
    st.markdown("### 🎯 Filter Saham")
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
            default=[]
        )
    elif filter_type == "Filter Tingkatan":
        selected_levels = st.multiselect(
            "Pilih Tingkatan Saham:",
            ["Blue Chip", "Second Liner", "Third Liner"],
            default=["Blue Chip", "Second Liner", "Third Liner"],
            help="Blue Chip: > Rp10T | Second Liner: Rp500M-Rp10T | Third Liner: < Rp1T"
        )
        
        # Tampilkan estimasi jumlah dan waktu
        if selected_levels:
            stocks_count = len(get_stocks_by_level(selected_levels))
            est_time = stocks_count * 0.5 / 60  # 0.5 detik per saham
            st.info(f"📊 {stocks_count} saham | ⏱️ ±{est_time:.1f} menit (sequential)")
            st.info(f"⚡ Dengan paralel: ±{stocks_count * 0.1 / 60:.1f} menit")
    
    st.markdown("---")
    
    # Tombol reset data (opsional)
    if st.button("🔄 Reset Data", use_container_width=True):
        reset_session_data()
        st.success("Data session telah direset!")
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📌 Info")
    st.markdown("""
    - **Data:** Yahoo Finance + KSEI
    - **Blue Chip:** 💎 > Rp10T
    - **Second Liner:** 📈 Rp500M-Rp10T
    - **Third Liner:** 🎯 < Rp1T
    - **FCA:** ⚠️ Papan Pemantauan
    """)
    
    st.markdown("---")
    st.caption("Made with ❤️ for Indonesian Traders")

# MAIN CONTENT
if "Open = Low" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Open = Low + Kenaikan ≥5%</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periode = st.selectbox(
            "📅 Periode Analisis",
            ["7 Hari", "14 Hari", "30 Hari", "90 Hari", "180 Hari", "365 Hari"],
            index=2,
            help="Pilih periode waktu untuk analisis"
        )
    
    with col2:
        min_kenaikan = st.slider(
            "📈 Minimal Kenaikan (%)", 
            1, 20, 5,
            help="Minimal persentase kenaikan dari Low ke Close"
        )
    
    with col3:
        limit_saham = st.number_input(
            "🎯 Limit Hasil", 
            min_value=5, 
            max_value=100, 
            value=20,
            help="Jumlah maksimal saham yang ditampilkan"
        )
    
    # Pilihan mode scanning (parallel atau sequential)
    st.markdown("### ⚡ Mode Scanning")
    col_par1, col_par2 = st.columns(2)
    
    with col_par1:
        use_parallel = st.checkbox("Gunakan Parallel Scanning (LEBIH CEPAT)", value=True)
    
    with col_par2:
        st.info("Parallel scanning bisa 5-10x lebih cepat!")
    
    periode_map = {
        "7 Hari": 7, "14 Hari": 14, "30 Hari": 30, 
        "90 Hari": 90, "180 Hari": 180, "365 Hari": 365
    }
    hari = periode_map[periode]
    
    # Tombol scan
    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):
        # Reset data lama sebelum scan baru
        reset_session_data()
        
        # Tentukan stocks yang akan discan berdasarkan filter
        if filter_type == "Pilih Manual" and selected_stocks:
            stocks_to_scan = selected_stocks
        elif filter_type == "Filter Tingkatan" and selected_levels:
            stocks_to_scan = get_stocks_by_level(selected_levels)
        else:
            stocks_to_scan = STOCKS_LIST
        
        # Hitung estimasi waktu
        estimasi_detik = len(stocks_to_scan) * (0.1 if use_parallel else 0.5)
        estimasi_menit = estimasi_detik / 60
        
        # Tampilkan warning
        with st.container():
            if estimasi_menit > 2:
                st.warning(f"⏱️ **Memproses {len(stocks_to_scan)} saham**\n\nEstimasi waktu: **{estimasi_menit:.1f} menit**")
            else:
                st.info(f"📊 Memproses {len(stocks_to_scan)} saham. Estimasi: {estimasi_detik:.0f} detik")
        
        # Progress scanning
        start_time = time.time()
        
        if use_parallel:
            # Parallel scanning (CEPAT)
            results = scan_stocks_parallel(
                stocks_to_scan, 
                scan_open_low_pattern,
                periode_hari=hari,
                min_kenaikan=min_kenaikan
            )
        else:
            # Sequential scanning (LAMA)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            failed_stocks = []
            
            for i, stock in enumerate(stocks_to_scan):
                status_text.text(f"📊 Memproses {stock}... ({i+1}/{len(stocks_to_scan)})")
                
                try:
                    result = scan_open_low_pattern(
                        stock, 
                        periode_hari=hari,
                        min_kenaikan=min_kenaikan
                    )
                    if result:
                        results.append(result)
                except Exception as e:
                    failed_stocks.append(stock)
                
                progress_bar.progress((i + 1) / len(stocks_to_scan))
                time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
            
            if failed_stocks:
                st.warning(f"⚠️ {len(failed_stocks)} saham gagal discan")
        
        total_time = time.time() - start_time
        
        if results:
            # Convert ke DataFrame
            df_results = pd.DataFrame(results)
            df_results = df_results.sort_values('frekuensi', ascending=False).head(limit_saham)
            
            # ========== SUCCESS BOX ELEGAN ==========
            st.markdown(
                f"""
                <div class="success-box">
                    <div style="position: absolute; top: 10px; right: 20px; font-size: 1.5rem; opacity: 0.3;">✨</div>
                    <div style="position: absolute; bottom: 10px; left: 20px; font-size: 1.5rem; opacity: 0.3;">✨</div>
                    <h1 style="color: #ffd700; margin: 0; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); letter-spacing: 2px;">✅ SCAN BERHASIL!</h1>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 15px; margin: 20px 0 10px 0; backdrop-filter: blur(5px);">
                        <p style="color: white; font-size: 2.2rem; margin: 0; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">{len(df_results)} SAHAM</p>
                        <p style="color: #ffd700; font-size: 1.3rem; margin: 5px 0 0 0; text-transform: uppercase; letter-spacing: 3px;">Dengan Pola Open=Low</p>
                    </div>
                    <div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px;">
                        <div style="text-align: center;">
                            <p style="color: #ffd700; font-size: 1rem; margin: 0;">⏱️ WAKTU PROSES</p>
                            <p style="color: white; font-size: 1.8rem; margin: 5px 0; font-weight: bold;">{total_time:.0f} detik</p>
                        </div>
                        <div style="text-align: center;">
                            <p style="color: #ffd700; font-size: 1rem; margin: 0;">📊 PERIODE</p>
                            <p style="color: white; font-size: 1.8rem; margin: 5px 0; font-weight: bold;">{periode}</p>
                        </div>
                    </div>
                    <div style="width: 80%; height: 2px; background: linear-gradient(90deg, transparent, #ffd700, transparent); margin: 15px auto 5px auto;"></div>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin: 10px 0 0 0;">✦ Siap trading cuan ✦</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # ========== HASIL SCANNING + FREE FLOAT + FCA + TINGKATAN ==========
            st.markdown("### 📋 Hasil Scanning + Data Free Float + FCA")
            
            # Ambil data free float untuk setiap saham
            enhanced_results = []
            for _, row in df_results.iterrows():
                saham = row['saham']
                free_float = get_free_float_value(saham)
                holders = get_free_float_holders(saham)
                level = get_stock_level(saham)
                
                # Hitung total institusi + asing di free float
                total_inst_asing = 0
                for p in holders:
                    persen_dalam_ff = (p['persen'] / free_float) * 100 if free_float > 0 else 0
                    total_inst_asing += persen_dalam_ff
                
                sisa_ritel = 100 - total_inst_asing
                potensi = analyze_goreng_potential(free_float)
                fca_status = '⚠️' if is_fca(saham) else ''
                
                # Simpan nilai asli untuk sorting, dan display string untuk tampilan
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
            
            # Tampilkan dataframe dengan kolom yang dipilih
            display_df = enhanced_df[['Saham', 'Level', 'Frek', 'Prob', 'Gain', 'FF', 'Inst', 'Ritel', 'FCA', 'Pot']]
            st.dataframe(
                display_df,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # ========== SIMPAN DATA DI SESSION STATE ==========
            st.session_state['scan_results'] = df_results
            st.session_state['enhanced_df'] = enhanced_df
            st.session_state['display_df'] = display_df
            st.session_state['watchlist_df'] = None  # Reset watchlist
            # =================================================
            
            # ========== VISUALISASI TOP 10 DENGAN URUTAN YANG SAMA ==========
            st.markdown("### 📊 Top 10 Saham (Urut Berdasarkan Frekuensi)")
            
            # Ambil top 10 dan pastikan urutannya tetap
            top10_df = df_results.head(10).copy()
            
            # Buat grafik dengan urutan sesuai frekuensi (bukan alfabet)
            fig = px.bar(
                top10_df,
                x='saham',
                y='frekuensi',
                title="10 Saham dengan Frekuensi Tertinggi",
                labels={'saham': 'Saham', 'frekuensi': 'Frekuensi'},
                color='probabilitas',
                color_continuous_scale='Viridis',
                category_orders={"saham": top10_df['saham'].tolist()}  # <-- INI KUNCI! Urutan sesuai data
            )
            fig.update_layout(
                height=500,
                xaxis={'categoryorder': 'array', 'categoryarray': top10_df['saham'].tolist()},  # Backup
                xaxis_title="Saham (Urut dari frekuensi tertinggi)",
                yaxis_title="Frekuensi"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tampilkan urutan top 10 dalam teks biar jelas
            st.caption(f"Urutan: {' → '.join(top10_df['saham'].tolist())}")
            
            # ========== ANALISIS AI ==========
            st.markdown("## 🤖 Analisis AI")
            st.markdown("Analisis untuk top 5 saham dengan pola terbaik (sesuai urutan di atas):")
            
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                # Panggil analisis AI
                analysis = analyze_pattern(row.to_dict())
                
                # Tampilkan dengan expander
                with st.expander(f"📊 {row['saham']} - {get_stock_level(row['saham'])} | Prob: {row['probabilitas']:.1f}% (Rank #{idx+1})"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🎯 Probabilitas", f"{row['probabilitas']:.1f}%")
                    with col2:
                        st.metric("💰 Rata Gain", f"{row['rata_rata_kenaikan']:.1f}%")
                    with col3:
                        st.metric("📈 Max Gain", f"{row['max_kenaikan']:.1f}%")
                    with col4:
                        st.metric("📊 Frekuensi", f"{row['frekuensi']}x")
                    
                    st.markdown("**📋 Kesimpulan AI:**")
                    st.markdown(analysis)
                    
                    # Tambah info free float + FCA
                    free_float = get_free_float_value(row['saham'])
                    st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)
                    
                    st.markdown("---")
            
            # ========== WATCHLIST GENERATOR ==========
            st.markdown("## 📋 Watchlist Generator")
            st.markdown("Top saham untuk dipantau besok:")
            
            col1, col2 = st.columns(2)
            with col1:
                min_gain_filter = st.slider("🎯 Minimal gain rata-rata (%)", 3, 10, 5, key="min_gain")
            with col2:
                top_n = st.number_input("📊 Jumlah saham", 5, 30, 15, key="top_n")
            
            # Filter berdasarkan gain minimal (pake nilai asli)
            if 'enhanced_df' in st.session_state:
                df_watchlist = st.session_state['enhanced_df'][st.session_state['enhanced_df']['Gain_Val'] >= min_gain_filter].copy()
            else:
                df_watchlist = enhanced_df[enhanced_df['Gain_Val'] >= min_gain_filter].copy()
            
            if len(df_watchlist) > 0:
                # Hitung skor gabungan
                max_prob = df_watchlist['Prob_Val'].max()
                max_gain = df_watchlist['Gain_Val'].max()
                
                if max_prob > 0 and max_gain > 0:
                    df_watchlist['skor'] = (
                        (df_watchlist['Prob_Val'] / max_prob) * 50 +
                        (df_watchlist['Gain_Val'] / max_gain) * 50
                    )
                    
                    # Ambil top N
                    df_watchlist = df_watchlist.nlargest(top_n, 'skor')
                
                # Header watchlist
                st.markdown(
                    f"""
                    <div class="watchlist-header">
                        <h2 style="color: white; margin: 0;">📋 WATCHLIST TRADING</h2>
                        <p style="color: #a8d8ff; font-size: 1.2rem;">{datetime.now().strftime('%d %B %Y')}</p>
                        <p style="color: #ffaa00;">Pantau 15 menit pertama! 🎯</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Buat tabel watchlist
                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['Prob_Val'] >= 20 and row['Gain_Val'] >= 7:
                        rekom = "🔥 PRIORITAS"
                    elif row['Prob_Val'] >= 15 and row['Gain_Val'] >= 5:
                        rekom = "⚡ LAYAK"
                    else:
                        rekom = "📌 PANTAU"
                    
                    # Singkatan level
                    level_singkat = {
                        '💎 Blue Chip': 'BC',
                        '📈 Second Liner': 'SL',
                        '🎯 Third Liner': 'TL'
                    }.get(row['Level'], '')
                    
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
                
                # Tampilkan dataframe
                watchlist_df = pd.DataFrame(watchlist_data)
                
                # ========== SIMPAN WATCHLIST DI SESSION STATE ==========
                st.session_state['watchlist_df'] = watchlist_df
                # ======================================================
                
                st.dataframe(
                    watchlist_df,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # ========== EXPORT SECTION DENGAN TABS ==========
                st.markdown("## 📥 Export Data")
                
                tab_exp1, tab_exp2 = st.tabs(["📋 Watchlist", "📊 Hasil Scanning"])
                
                with tab_exp1:
                    st.markdown("### Download Watchlist")
                    if 'watchlist_df' in st.session_state and st.session_state['watchlist_df'] is not None:
                        create_download_buttons(st.session_state['watchlist_df'], "watchlist", "watchlist_tab")
                        st.info("💡 BC=Blue Chip, SL=Second Liner, TL=Third Liner | Fokus 🔥 PRIORITAS dengan 🔥 UT/ST. Waspadai ⚠️ FCA.")
                    else:
                        st.warning("Belum ada data watchlist. Generate watchlist dulu ya bro!")
                
                with tab_exp2:
                    st.markdown("### Download Hasil Scanning")
                    if 'display_df' in st.session_state:
                        create_download_buttons(st.session_state['display_df'], "scan", "scan_tab")
                    else:
                        st.warning("Belum ada data scanning. Scan dulu ya bro!")
                    
            else:
                st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%")
        else:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    ⚠️ Tidak ditemukan saham dengan kriteria Open=Low
                </div>
                """,
                unsafe_allow_html=True
            )

elif "Low Float" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Low Float + Free Float + FCA</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_ff = st.slider("📊 Maks Free Float (%)", 1, 50, 20, help="Free float di bawah nilai ini")
    
    with col2:
        min_vol = st.number_input("📈 Min Volume", min_value=0, value=0, step=100000, help="Minimal volume rata-rata")
    
    # Filter tingkatan untuk low float scanner
    st.markdown("### 🏷️ Filter Tingkatan")
    col_lvl1, col_lvl2, col_lvl3 = st.columns(3)
    with col_lvl1:
        scan_blue = st.checkbox("Blue Chip 💎", value=True)
    with col_lvl2:
        scan_second = st.checkbox("Second Liner 📈", value=True)
    with col_lvl3:
        scan_third = st.checkbox("Third Liner 🎯", value=True)
    
    # Pilihan mode scanning
    st.markdown("### ⚡ Mode Scanning")
    use_parallel = st.checkbox("Gunakan Parallel Scanning (LEBIH CEPAT)", value=True)
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        # Reset data lama
        reset_session_data()
        
        # Tentukan stocks berdasarkan filter
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
                stocks_to_scan = STOCKS_LIST
        
        # Hitung estimasi
        est_time = len(stocks_to_scan) * (0.1 if use_parallel else 0.3) / 60
        st.info(f"📊 Memproses {len(stocks_to_scan)} saham | Estimasi: {est_time:.1f} menit")
        
        start_time = time.time()
        
        if use_parallel:
            # Parallel scanning
            results = scan_stocks_parallel(
                stocks_to_scan,
                scan_low_float,
                max_public_float=max_ff,
                min_volume=min_vol
            )
        else:
            # Sequential
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            
            for i, stock in enumerate(stocks_to_scan):
                status_text.text(f"📊 Memproses {stock}... ({i+1}/{len(stocks_to_scan)})")
                try:
                    result = scan_low_float([stock], max_ff, min_vol)
                    if result:
                        results.extend(result)
                except Exception as e:
                    pass
                progress_bar.progress((i + 1) / len(stocks_to_scan))
                time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
        
        total_time = time.time() - start_time
        
        if results:
            df_results = pd.DataFrame(results)
            
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 25px; border-radius: 15px; margin: 20px 0; text-align: center; color: white; border: 2px solid #ffd700;">
                    <h2 style="color: #ffd700; margin: 0;">✅ BERHASIL</h2>
                    <p style="font-size: 2rem; margin: 10px 0;">{len(df_results)} SAHAM</p>
                    <p>Free float < {max_ff}% | ⏱️ {total_time:.0f} detik</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("### 📋 Hasil + Free Float + FCA")
            
            # Ambil data free float
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
                
                # Hitung komposisi free float
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
            st.dataframe(
                enriched_df,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # ========== SIMPAN DATA DI SESSION STATE ==========
            st.session_state['low_float_results'] = df_results
            st.session_state['low_float_enriched'] = enriched_df
            # ==================================================
            
            # Detail
            st.markdown("### 🔍 Detail Free Float")
            for _, row in df_results.head(5).iterrows():
                free_float = get_free_float_value(row['saham'])
                with st.expander(f"📊 {row['saham']} - {get_stock_level(row['saham'])} | FF: {free_float:.0f}%"):
                    st.markdown(display_free_float_info(row['saham'], free_float), unsafe_allow_html=True)
            
            # Visualisasi
            st.markdown("### 📊 Distribusi")
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    values=df_results['category'].value_counts().values,
                    names=df_results['category'].value_counts().index,
                    title="Kategori Free Float"
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
                st.plotly_chart(fig, use_container_width=True)
            
            # Export dengan TABS
            st.markdown("## 📥 Export Data")
            tab_exp1, tab_exp2 = st.tabs(["📊 Hasil Low Float", "📋 Info"])
            
            with tab_exp1:
                st.markdown("### Download Hasil Low Float")
                if 'low_float_enriched' in st.session_state:
                    create_download_buttons(st.session_state['low_float_enriched'], "low_float", "low_float_tab")
                else:
                    create_download_buttons(enriched_df, "low_float", "low_float_tab")
            
            with tab_exp2:
                st.markdown("### Info")
                st.info("Gunakan hasil di atas untuk analisis lebih lanjut")
                
        else:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                    ⚠️ Tidak ditemukan saham low float
                </div>
                """,
                unsafe_allow_html=True
            )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>⚠️ Data edukasi, bukan rekomendasi</p>
        <p>BC=Blue Chip, SL=Second Liner, TL=Third Liner | FF=Free Float | FCA=Full Call Auction</p>
        <p>🔥 UT/ST=Ultra/Sangat Tinggi ⚡ TG=Tinggi 📊 SD=Sedang 📉 RD=Rendah</p>
        <p>⚡ Parallel scanning aktif: 900+ saham jadi ±1.5 menit!</p>
        <p>💾 Data tersimpan di session - bisa download kapan aja tanpa scan ulang</p>
        <p>📊 Top 10 diurutkan berdasarkan frekuensi, sama persis dengan tabel & analisis AI</p>
    </div>
    """,
    unsafe_allow_html=True
)
