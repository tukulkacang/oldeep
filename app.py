import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Import modules kita - SEMUA NAMA FILE SUDAH BENAR
from data.stocks_list import STOCKS_LIST, get_sector
from modules.data_fetcher import get_stock_data, get_current_price, get_fundamental_data
from modules.open_low_scanner import scan_open_low_pattern, scan_multiple_stocks, get_pattern_summary
from modules.low_float_scanner import scan_low_float, get_low_float_summary
from modules.ai_analyzer import analyze_pattern, analyze_low_float, predict_next_pattern, get_market_context
from utils.exporters import export_to_excel, export_to_pdf, format_number

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
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">📊 Screener Saham Indonesia</p>', unsafe_allow_html=True)
st.markdown('<p class="info-text">Scanner untuk Open=Low Pattern & Low Float Stocks dengan Analisis AI</p>', unsafe_allow_html=True)

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
    - Data: Yahoo Finance
    - Update: Real-time
    - Tujuan: Edukasi
    """)

# MAIN CONTENT
if "Open = Low" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Open = Low + Kenaikan ≥5%</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periode = st.selectbox(
            "📅 Periode Analisis",
            ["7 Hari", "14 Hari", "30 Hari", "90 Hari", "180 Hari", "365 Hari"],
            index=2
        )
    
    with col2:
        min_kenaikan = st.slider("📈 Minimal Kenaikan (%)", 1, 20, 5)
    
    with col3:
        limit_saham = st.number_input("🎯 Limit Hasil", min_value=5, max_value=100, value=20)
    
    periode_map = {
        "7 Hari": 7, "14 Hari": 14, "30 Hari": 30, 
        "90 Hari": 90, "180 Hari": 180, "365 Hari": 365
    }
    hari = periode_map[periode]
    
    if st.button("🚀 MULAI SCANNING", type="primary", use_container_width=True):
        stocks_to_scan = selected_stocks if selected_stocks else STOCKS_LIST[:50]
        
        with st.spinner("Sedang menganalisis pola saham..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            for i, stock in enumerate(stocks_to_scan):
                status_text.text(f"📊 Memproses {stock}... ({i+1}/{len(stocks_to_scan)})")
                
                result = scan_open_low_pattern(
                    stock, 
                    periode_hari=hari,
                    min_kenaikan=min_kenaikan
                )
                
                if result:
                    results.append(result)
                
                progress_bar.progress((i + 1) / len(stocks_to_scan))
                time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
            
            if results:
                df_results = pd.DataFrame(results)
                df_results = df_results.sort_values('frekuensi', ascending=False).head(limit_saham)
                
                st.success(f"✅ Ditemukan {len(df_results)} saham dengan pola Open=Low!")
                
                # Tampilkan hasil
                st.dataframe(
                    df_results[[
                        'saham', 'frekuensi', 'probabilitas', 
                        'rata_rata_kenaikan', 'max_kenaikan'
                    ]],
                    use_container_width=True
                )
                
                # Export
                if st.button("📥 Export ke Excel"):
                    excel_data = export_to_excel(df_results)
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name=f"open_low_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("⚠️ Tidak ditemukan saham dengan kriteria yang sesuai.")

elif "Low Float" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Low Float</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_public_float = st.slider("📊 Maksimal Public Float (%)", 1, 50, 20)
    
    with col2:
        min_volume = st.number_input("📈 Minimal Volume", min_value=0, value=0, step=100000)
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        stocks_to_scan = selected_stocks if selected_stocks else STOCKS_LIST[:50]
        
        with st.spinner("Mengumpulkan data kepemilikan saham..."):
            results = scan_low_float(stocks_to_scan, max_public_float, min_volume)
            
            if results:
                df_results = pd.DataFrame(results)
                st.success(f"✅ Ditemukan {len(df_results)} saham Low Float!")
                
                st.dataframe(
                    df_results[[
                        'saham', 'public_float', 'category',
                        'volume_avg', 'volatility', 'low_float_score'
                    ]],
                    use_container_width=True
                )
                
                if st.button("📥 Export ke Excel"):
                    excel_data = export_to_excel(df_results)
                    st.download_button(
                        label="Download Excel",
                        data=excel_data,
                        file_name=f"low_float_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("⚠️ Tidak ditemukan saham low float.")

# Footer
st.markdown("---")
st.markdown("⚠️ Disclaimer: Data untuk tujuan edukasi, bukan rekomendasi investasi.")
