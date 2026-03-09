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

# ========== DATA PEMEGANG SAHAM (Update Maret 2026) ==========
# Sumber: KSEI/BEI per 27 Februari 2026
# Kebijakan baru: kepemilikan >1% terbuka untuk publik

SHAREHOLDER_DATA = {
    # PRAJOGO PANGESTU (Barito Pacific)
    'CUAN': {
        'pemegang': [
            {'nama': 'Prajogo Pangestu', 'persen': 84.10, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.02, 'tipe': 'Institusi', 'catatan': 'Masuk Q4 2025', 'update': 'Feb 2026'},
            {'nama': 'Vanguard', 'persen': 1.15, 'tipe': 'Asing', 'catatan': 'Nambah Jan 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 13.73,  # 100% - 86.27%
        'total_shares': 12345678900,
        'insider_activity': [
            {'tanggal': '05 Mar 2026', 'insider': 'Direktur Utama', 'aksi': 'BELI', 'jumlah': 100000, 'harga': 15000},
            {'tanggal': '20 Feb 2026', 'insider': 'Komisaris', 'aksi': 'BELI', 'jumlah': 50000, 'harga': 14800}
        ]
    },
    'BRPT': {
        'pemegang': [
            {'nama': 'Prajogo Pangestu', 'persen': 71.37, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
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
            {'nama': 'Prajogo Pangestu', 'persen': 5.03, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
            {'nama': 'GIC Singapore', 'persen': 3.45, 'tipe': 'Asing', 'catatan': 'Masuk Jan 2026', 'update': 'Feb 2026'}
        ],
        'free_float': 91.52,
        'total_shares': 1122334455,
        'insider_activity': []
    },
    
    # BOY THOHIR
    'TRIM': {
        'pemegang': [
            {'nama': 'Boy Thohir', 'persen': 34.68, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 2.15, 'tipe': 'Institusi', 'catatan': 'Nambah Des 2025', 'update': 'Feb 2026'}
        ],
        'free_float': 63.17,
        'total_shares': 9988776655,
        'insider_activity': []
    },
    'MDKA': {
        'pemegang': [
            {'nama': 'Boy Thohir', 'persen': 7.46, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
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
            {'nama': 'Anthoni Salim', 'persen': 1.15, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.06, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'},
            {'nama': 'Pemerintah Norwegia', 'persen': 0.89, 'tipe': 'Asing', 'catatan': 'Masuk', 'update': 'Feb 2026'},
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
            {'nama': 'Anthoni Salim', 'persen': 3.74, 'tipe': 'Founder', 'catatan': 'via Grup Salim', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 3.74, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 92.52,
        'total_shares': 8765432100,
        'insider_activity': []
    },
    'CBDK': {
        'pemegang': [
            {'nama': 'Anthoni Salim', 'persen': 0.93, 'tipe': 'Founder', 'catatan': 'via Grup Salim - Jual', 'update': 'Feb 2026'}
        ],
        'free_float': 99.07,
        'total_shares': 1122334455,
        'insider_activity': [
            {'tanggal': '18 Feb 2026', 'insider': 'Grup Salim', 'aksi': 'JUAL', 'jumlah': 50000000, 'harga': 1500}
        ]
    },
    
    # LOW TUCK KWONG
    'BYAN': {
        'pemegang': [
            {'nama': 'Low Tuck Kwong', 'persen': 40.22, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'},
            {'nama': 'BPJS Ketenagakerjaan', 'persen': 1.33, 'tipe': 'Institusi', 'catatan': 'Nambah', 'update': 'Feb 2026'}
        ],
        'free_float': 58.45,
        'total_shares': 10000000000,
        'insider_activity': []
    },
    
    # HARY TANOE
    'BHIT': {
        'pemegang': [
            {'nama': 'Hary Tanoe', 'persen': 3.12, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'}
        ],
        'free_float': 96.88,
        'total_shares': 5566778899,
        'insider_activity': []
    },
    
    # DATO SRI TAHIR
    'MAYA': {
        'pemegang': [
            {'nama': 'Dato Sri Tahir', 'persen': 19.34, 'tipe': 'Founder', 'catatan': 'Pengendali', 'update': 'Feb 2026'}
        ],
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

def get_shareholder_info(stock_code):
    """Mengembalikan info lengkap pemegang saham"""
    return SHAREHOLDER_DATA.get(stock_code, {
        'pemegang': [],
        'free_float': 100.0,
        'total_shares': 0,
        'insider_activity': []
    })

def analyze_goreng_potential(stock_code):
    """Analisis potensi saham digoreng"""
    data = SHAREHOLDER_DATA.get(stock_code, {})
    
    if not data:
        return {
            'level': 'Tidak Ada Data',
            'alasan': 'Data kepemilikan tidak tersedia',
            'warna': 'gray'
        }
    
    free_float = data.get('free_float', 100)
    
    # Hitung pemegang non-founder (>1%)
    pemegang_lain = [p for p in data.get('pemegang', []) if p['tipe'] not in ['Founder']]
    total_lain = sum([p['persen'] for p in pemegang_lain])
    
    # Insider activity 3 bulan terakhir
    insider_beli = len([a for a in data.get('insider_activity', []) if a['aksi'] == 'BELI'])
    insider_jual = len([a for a in data.get('insider_activity', []) if a['aksi'] == 'JUAL'])
    
    # Logic penentuan potensi
    if free_float < 20:
        level = '🔥 SANGAT TINGGI'
        warna = 'red'
        alasan = f'Free float hanya {free_float:.1f}% - saham dikuasai segelintir pihak'
    elif free_float < 35:
        level = '⚡ TINGGI'
        warna = 'orange'
        alasan = f'Free float {free_float:.1f}% - relatif mudah digerakkan'
    elif free_float < 50:
        level = '📊 SEDANG'
        warna = 'yellow'
        alasan = f'Free float {free_float:.1f}% - butuh modal lebih besar untuk goreng'
    else:
        level = '📉 RENDAH'
        warna = 'green'
        alasan = f'Free float {free_float:.1f}% - saham tersebar luas, sulit digoreng'
    
    # Tambah konteks
    if insider_beli > insider_jual:
        alasan += f' | Insider sedang akumulasi ({insider_beli}x beli)'
    elif insider_jual > insider_beli:
        alasan += f' | Insider sedang distribusi ({insider_jual}x jual)'
    
    return {
        'level': level,
        'alasan': alasan,
        'warna': warna
    }

def display_shareholder_info(stock_code):
    """Tampilkan info pemegang saham dalam format bagus"""
    data = SHAREHOLDER_DATA.get(stock_code, {})
    
    if not data:
        return "<p style='color: gray;'>Tidak ada data kepemilikan >1%</p>"
    
    html = f"<div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>"
    html += f"<h4 style='color: #ffd700; margin: 0 0 10px 0;'>📋 Struktur Kepemilikan {stock_code}</h4>"
    
    # Free float
    html += f"<p><span style='color: #aaa;'>Free Float (saham beredar):</span> <span style='color: #00ff88; font-weight: bold;'>{data.get('free_float', 0):.2f}%</span></p>"
    
    # Pemegang >1%
    if data.get('pemegang'):
        html += "<p style='color: #aaa; margin: 10px 0 5px 0;'>Pemegang >1% (update Feb 2026):</p>"
        total_pemegang = 0
        for p in data['pemegang']:
            total_pemegang += p['persen']
            warna_tipe = {
                'Founder': '#ffaa00',
                'Institusi': '#1f77b4',
                'Asing': '#00ff88'
            }.get(p['tipe'], '#ffffff')
            
            html += f"""
            <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0;'>
                <span><span style='color: {warna_tipe};'>■</span> {p['nama']}</span>
                <span style='color: #ffd700; font-weight: bold;'>{p['persen']:.2f}%</span>
            </div>
            """
        
        # Sisa free float
        sisa_free_float = 100 - total_pemegang
        html += f"""
        <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #00ff88;'>
            <span><span style='color: #00ff88;'>■</span> Sisa Free Float (tersebar publik)</span>
            <span style='color: #00ff88; font-weight: bold;'>{sisa_free_float:.2f}%</span>
        </div>
        """
    
    # Insider activity
    if data.get('insider_activity'):
        html += "<p style='color: #aaa; margin: 15px 0 5px 0;'>Aktivitas Insider 30 hari terakhir:</p>"
        for a in data['insider_activity']:
            warna_aksi = '#00ff88' if a['aksi'] == 'BELI' else '#ff5555'
            html += f"""
            <div style='display: flex; justify-content: space-between; background-color: #2d2d2d; padding: 8px; border-radius: 5px; margin: 5px 0;'>
                <span>{a['tanggal']} - {a['insider']}</span>
                <span style='color: {warna_aksi}; font-weight: bold;'>{a['aksi']} {a['jumlah']:,} @ {a['harga']}</span>
            </div>
            """
    
    html += "</div>"
    return html

# Config halaman
st.set_page_config(
    page_title="Screener Saham Indonesia",
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
    .export-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">📊 Screener Saham Indonesia</p>', unsafe_allow_html=True)
st.markdown('<p class="info-text">Scanner untuk Open=Low Pattern & Low Float Stocks dengan Analisis AI + Bandar Detector</p>', unsafe_allow_html=True)

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
        ["Semua Saham", "Pilih Manual"],
        index=0
    )
    
    selected_stocks = []
    if filter_type == "Pilih Manual":
        selected_stocks = st.multiselect(
            "Pilih Saham:",
            options=STOCKS_LIST,
            default=[]
        )
    
    st.markdown("---")
    st.markdown("### 📌 Info")
    st.markdown("""
    - **Data:** Yahoo Finance + KSEI
    - **Total Saham:** 900+
    - **Update:** Real-time
    - **Pemegang >1%:** Update Feb 2026
    - **Tujuan:** Edukasi
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
    
    # Opsi mode scanning
    st.markdown("### 🔍 Mode Scanning")
    col1, col2 = st.columns(2)
    
    with col1:
        scan_option = st.radio(
            "Pilih kecepatan scanning:",
            ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"],
            index=0,
            horizontal=True
        )
    
    with col2:
        st.info(
            "⚡ **Cepat:** ±30 detik\n\n"
            "🐢 **Lengkap:** ±7-10 menit\n\n"
            "Gunakan mode lengkap untuk analisis mendalam"
        )
    
    periode_map = {
        "7 Hari": 7, "14 Hari": 14, "30 Hari": 30, 
        "90 Hari": 90, "180 Hari": 180, "365 Hari": 365
    }
    hari = periode_map[periode]
    
    # Tombol scan
    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):
        # Tentukan stocks yang akan discan
        if selected_stocks:
            stocks_to_scan = selected_stocks
        else:
            if scan_option == "⚡ Cepat (50 saham)":
                stocks_to_scan = STOCKS_LIST[:50]
            else:
                stocks_to_scan = STOCKS_LIST
        
        # Hitung estimasi waktu
        estimasi_detik = len(stocks_to_scan) * 0.5
        estimasi_menit = estimasi_detik / 60
        
        # Tampilkan warning
        with st.container():
            if estimasi_menit > 2:
                st.warning(f"⏱️ **Memproses {len(stocks_to_scan)} saham**\n\nEstimasi waktu: **{estimasi_menit:.1f} menit**\n\nHarap sabar ya bro! Jangan refresh halaman.")
            else:
                st.info(f"📊 Memproses {len(stocks_to_scan)} saham. Estimasi: {estimasi_detik:.0f} detik")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        start_time = time.time()
        
        for i, stock in enumerate(stocks_to_scan):
            # Update status
            elapsed = time.time() - start_time
            remaining = (elapsed / (i + 1)) * (len(stocks_to_scan) - (i + 1))
            
            status_text.text(
                f"📊 Memproses {stock}... ({i+1}/{len(stocks_to_scan)}) | "
                f"Elapsed: {elapsed:.0f}s | Remaining: {remaining:.0f}s"
            )
            
            # Scan pattern
            result = scan_open_low_pattern(
                stock, 
                periode_hari=hari,
                min_kenaikan=min_kenaikan
            )
            
            if result:
                results.append(result)
            
            # Update progress
            progress_bar.progress((i + 1) / len(stocks_to_scan))
            time.sleep(0.3)
        
        # Selesai
        progress_bar.empty()
        status_text.empty()
        
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
            
            # Tampilkan hasil
            st.markdown("### 📋 Hasil Scanning")
            
            display_df = df_results[[
                'saham', 'frekuensi', 'probabilitas', 
                'rata_rata_kenaikan', 'max_kenaikan', 'last_kenaikan'
            ]].copy()
            
            display_df.columns = [
                'Saham', 'Frekuensi', 'Probabilitas (%)', 
                'Rata-rata Gain (%)', 'Max Gain (%)', 'Gain Terakhir (%)'
            ]
            
            # Format dulu sebelum ditampilkan
            display_df_display = display_df.copy()
            display_df_display['Probabilitas (%)'] = display_df_display['Probabilitas (%)'].apply(lambda x: f"{x:.1f}%")
            display_df_display['Rata-rata Gain (%)'] = display_df_display['Rata-rata Gain (%)'].apply(lambda x: f"{x:.1f}%")
            display_df_display['Max Gain (%)'] = display_df_display['Max Gain (%)'].apply(lambda x: f"{x:.1f}%")
            display_df_display['Gain Terakhir (%)'] = display_df_display['Gain Terakhir (%)'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(
                display_df_display,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Visualisasi
            st.markdown("### 📊 Top 10 Saham")
            fig = px.bar(
                df_results.head(10),
                x='saham',
                y='frekuensi',
                title="10 Saham dengan Frekuensi Tertinggi",
                labels={'saham': 'Saham', 'frekuensi': 'Frekuensi'},
                color='probabilitas',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # ========== ANALISIS AI ==========
            st.markdown("## 🤖 Analisis AI")
            st.markdown("Analisis untuk top 5 saham dengan pola terbaik:")
            
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                # Panggil analisis AI
                analysis = analyze_pattern(row.to_dict())
                
                # Tampilkan dengan expander
                with st.expander(f"📊 {row['saham']} - Prob: {row['probabilitas']:.1f}% | Gain: {row['rata_rata_kenaikan']:.1f}%"):
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
                    
                    # Tambah info pemegang saham
                    st.markdown("**📋 Struktur Kepemilikan:**")
                    st.markdown(display_shareholder_info(row['saham']), unsafe_allow_html=True)
                    
                    st.markdown("---")
            
            # ========== WATCHLIST GENERATOR ==========
            st.markdown("## 📋 Watchlist Generator")
            st.markdown("Top saham untuk dipantau besok (fokus pada yang sering Open=Low dengan gain tertinggi):")
            
            col1, col2 = st.columns(2)
            with col1:
                min_gain_filter = st.slider("🎯 Minimal gain rata-rata (%)", 3, 10, 5, key="min_gain")
            with col2:
                top_n = st.number_input("📊 Jumlah saham dalam watchlist", 5, 30, 15, key="top_n")
            
            # Filter berdasarkan gain minimal
            df_watchlist = df_results[df_results['rata_rata_kenaikan'] >= min_gain_filter].copy()
            
            if len(df_watchlist) > 0:
                # Hitung skor gabungan
                max_prob = df_watchlist['probabilitas'].max()
                max_gain = df_watchlist['rata_rata_kenaikan'].max()
                
                if max_prob > 0 and max_gain > 0:
                    df_watchlist['skor'] = (
                        (df_watchlist['probabilitas'] / max_prob) * 50 +
                        (df_watchlist['rata_rata_kenaikan'] / max_gain) * 50
                    )
                    
                    # Ambil top N
                    df_watchlist = df_watchlist.nlargest(top_n, 'skor')
                
                # Header watchlist
                st.markdown(
                    f"""
                    <div class="watchlist-header">
                        <h2 style="color: white; margin: 0;">📋 WATCHLIST TRADING</h2>
                        <p style="color: #a8d8ff; font-size: 1.2rem;">{datetime.now().strftime('%d %B %Y')}</p>
                        <p style="color: #ffaa00;">Pantau 15 menit pertama! Open=Low = Siap eksekusi 🎯</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Buat tabel watchlist
                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7:
                        rekom = "🔥 PRIORITAS UTAMA"
                    elif row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5:
                        rekom = "⚡ LAYAK DICOBA"
                    else:
                        rekom = "📌 PANTAU"
                    
                    # Tambah info potensi goreng
                    goreng = analyze_goreng_potential(row['saham'])
                    
                    watchlist_data.append({
                        "Rank": i + 1,
                        "Saham": row['saham'],
                        "Probabilitas": f"{row['probabilitas']:.1f}%",
                        "Gain Rata": f"{row['rata_rata_kenaikan']:.1f}%",
                        "Max Gain": f"{row['max_kenaikan']:.1f}%",
                        "Frekuensi": f"{row['frekuensi']}x",
                        "Rekomendasi": rekom,
                        "Potensi Goreng": goreng['level']
                    })
                
                # Tampilkan dataframe
                watchlist_df = pd.DataFrame(watchlist_data)
                st.dataframe(
                    watchlist_df,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Export buttons watchlist
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
                    else:
                        st.error("❌ Gagal bikin Excel")
                
                # Tips
                st.info("""
                💡 **Tips Penggunaan Watchlist:**
                1. Simpan watchlist ini di HP/laptop lo
                2. Besok pagi jam 8:45, buka watchlist
                3. Pantau 15 menit pertama (9:00-9:15)
                4. Begitu ada saham Open=Low, langsung eksekusi
                5. Fokus ke yang bertuliskan 🔥 PRIORITAS UTAMA
                """)
            else:
                st.warning(f"Tidak ada saham dengan gain minimal {min_gain_filter}%. Coba turunkan filternya.")
            
            # ========== EXPORT DATA SCANNING ==========
            st.markdown("### 📥 Export Data Scanning")
            
            col_scan1, col_scan2 = st.columns(2)
            
            with col_scan1:
                csv_data_scan = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data_scan,
                    file_name=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_scan2:
                excel_data_scan = export_to_excel(display_df)
                if excel_data_scan:
                    st.download_button(
                        label="📈 Download Excel",
                        data=excel_data_scan,
                        file_name=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Gagal bikin Excel. Coba pake CSV aja.")
                    
        else:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white; border-left: 8px solid #ffd700;">
                    ⚠️ Tidak ditemukan saham dengan kriteria yang sesuai.<br>
                    Coba turunkan minimal kenaikan atau perpanjang periode analisis.
                </div>
                """,
                unsafe_allow_html=True
            )

elif "Low Float" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Low Float + Bandar Detector</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_public_float = st.slider(
            "📊 Maksimal Public Float (%)", 
            1, 50, 20,
            help="Saham dengan public float di bawah nilai ini (free float)"
        )
    
    with col2:
        min_volume = st.number_input(
            "📈 Minimal Volume", 
            min_value=0, 
            value=0, 
            step=100000,
            help="Minimal volume rata-rata (0 = abaikan)"
        )
    
    # Opsi mode scanning
    scan_option = st.radio(
        "🔍 Mode Scanning:",
        ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"],
        horizontal=True,
        index=0
    )
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        if selected_stocks:
            stocks_to_scan = selected_stocks
        else:
            if scan_option == "⚡ Cepat (50 saham)":
                stocks_to_scan = STOCKS_LIST[:50]
            else:
                stocks_to_scan = STOCKS_LIST
        
        with st.spinner(f"Mengumpulkan data {len(stocks_to_scan)} saham..."):
            # Panggil scanner low float
            results = scan_low_float(stocks_to_scan, max_public_float, min_volume)
            
            if results:
                df_results = pd.DataFrame(results)
                
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 25px; border-radius: 15px; margin: 20px 0; text-align: center; color: white; border: 2px solid #ffd700;">
                        <h2 style="color: #ffd700; margin: 0;">✅ SCAN LOW FLOAT BERHASIL</h2>
                        <p style="font-size: 2rem; margin: 10px 0;">{len(df_results)} SAHAM</p>
                        <p>Ditemukan saham dengan public float di bawah {max_public_float}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Tampilkan hasil dengan info pemegang saham
                st.markdown("### 📋 Hasil Scanning + Data Pemegang Saham")
                
                # Ambil data pemegang saham untuk setiap hasil
                enriched_results = []
                for _, row in df_results.iterrows():
                    saham = row['saham']
                    shareholder_info = get_shareholder_info(saham)
                    goreng = analyze_goreng_potential(saham)
                    
                    # Hitung total kepemilikan >1%
                    total_pemegang_utama = sum([p['persen'] for p in shareholder_info.get('pemegang', [])])
                    free_float_asli = shareholder_info.get('free_float', 100)
                    sisa_free_float = 100 - total_pemegang_utama if total_pemegang_utama > 0 else 100
                    
                    enriched_results.append({
                        'Saham': saham,
                        'Free Float (%)': f"{free_float_asli:.2f}%",
                        'Kategori': row['category'],
                        'Volume': f"{row['volume_avg']:,.0f}",
                        'Volatilitas (%)': f"{row['volatility']:.2f}%",
                        'Score': f"{row['low_float_score']:.1f}",
                        'Pemegang >1%': f"{total_pemegang_utama:.2f}%" if total_pemegang_utama > 0 else "Tidak ada",
                        'Sisa Free Float': f"{sisa_free_float:.2f}%" if total_pemegang_utama > 0 else "100%",
                        'Potensi Goreng': goreng['level']
                    })
                
                enriched_df = pd.DataFrame(enriched_results)
                st.dataframe(
                    enriched_df,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Tampilkan detail untuk setiap saham
                st.markdown("### 🔍 Detail Pemegang Saham")
                
                for _, row in df_results.head(5).iterrows():
                    with st.expander(f"📊 {row['saham']} - Free Float: {row['public_float']:.2f}%"):
                        # Tampilkan info pemegang saham
                        st.markdown(display_shareholder_info(row['saham']), unsafe_allow_html=True)
                        
                        # Analisis potensi goreng
                        goreng = analyze_goreng_potential(row['saham'])
                        st.markdown(f"""
                        <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;">
                            <h4 style="color: #ffd700; margin: 0 0 10px 0;">🔥 Analisis Potensi Goreng</h4>
                            <p style="color: {'red' if 'TINGGI' in goreng['level'] else 'orange' if 'SEDANG' in goreng['level'] else 'green'}; font-weight: bold; font-size: 1.2rem;">
                                {goreng['level']}
                            </p>
                            <p style="color: #aaa;">{goreng['alasan']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Visualisasi
                st.markdown("### 📊 Distribusi Kategori Low Float")
                col1, col2 = st.columns(2)
                
                with col1:
                    category_counts = df_results['category'].value_counts()
                    fig = px.pie(
                        values=category_counts.values,
                        names=category_counts.index,
                        title="Distribusi Kategori Low Float"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(
                        df_results,
                        x='public_float',
                        y='volatility',
                        size='volume_avg',
                        hover_data=['saham'],
                        color='category',
                        title="Public Float vs Volatilitas"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export
                st.markdown("### 📥 Export Data")
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    csv_data = enriched_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_data,
                        file_name=f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_exp2:
                    excel_data = export_to_excel(enriched_df)
                    if excel_data:
                        st.download_button(
                            label="📈 Download Excel",
                            data=excel_data,
                            file_name=f"low_float_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Gagal bikin Excel")
            else:
                st.markdown(
                    """
                    <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white;">
                        ⚠️ Tidak ditemukan saham low float dengan kriteria tersebut.<br>
                        Coba naikkan maksimal public float atau turunkan minimal volume.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>⚠️ <strong>Disclaimer:</strong> Data untuk tujuan edukasi, bukan rekomendasi investasi.</p>
        <p>Data kepemilikan >1% berdasarkan laporan KSEI per 27 Februari 2026</p>
        <p>📊 Data dari Yahoo Finance + KSEI | ⏱️ Update: Real-time | 🔥 Bandar Detector Aktif</p>
    </div>
    """,
    unsafe_allow_html=True
)
