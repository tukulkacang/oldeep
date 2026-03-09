import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Import modules kita
from data.stocks_list import STOCKS_LIST, get_sector
from modules.data_fetcher import get_stock_data, get_current_price, get_fundamental_data
from modules.open_low_scanner import scan_open_low_pattern, get_pattern_summary
from modules.low_float_scanner import scan_low_float, get_low_float_summary
from modules.ai_analyzer import analyze_pattern, analyze_low_float, predict_next_pattern, get_market_context
from utils.exporters import export_to_excel, format_number

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
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 0.25rem;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 0.25rem;
    }
    .ai-card-high {
        background-color: #0a2f1f;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #00ff88;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 8px rgba(0,255,136,0.2);
    }
    .ai-card-mid {
        background-color: #2f2a0a;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #ffaa00;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 8px rgba(255,170,0,0.2);
    }
    .ai-card-low {
        background-color: #2f0a0a;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #ff5555;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 8px rgba(255,85,85,0.2);
    }
    .ai-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 15px;
        border-bottom: 2px solid #444;
        padding-bottom: 10px;
    }
    .ai-stat {
        display: flex;
        justify-content: space-between;
        padding: 8px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 8px;
        margin: 5px 0;
    }
    .ai-label {
        color: #aaa;
    }
    .ai-value {
        font-weight: bold;
        font-size: 1.2rem;
    }
    .ai-value-high {
        color: #00ff88;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .ai-value-mid {
        color: #ffaa00;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .ai-conclusion {
        margin-top: 15px;
        padding: 15px;
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px;
        font-style: italic;
        border-left: 4px solid #1f77b4;
    }
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 10px 0;
    }
    .metric-item {
        flex: 1;
        min-width: 120px;
        background: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 8px;
        text-align: center;
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
    - **Data:** Yahoo Finance
    - **Total Saham:** 900+
    - **Update:** Real-time
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
        warning_box = st.container()
        with warning_box:
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
            
            # Success message
            st.markdown(f"""
            <div class="success-box">
                ✅ **Berhasil!** Ditemukan {len(df_results)} saham dengan pola Open=Low<br>
                ⏱️ Waktu proses: {total_time:.0f} detik
            </div>
            """, unsafe_allow_html=True)
            
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
            
            # ========== FITUR AI DENGAN TAMPILAN KEREN ==========
            st.markdown("## 🤖 Analisis AI")
            st.markdown("Analisis mendalam untuk top 5 saham dengan pola terbaik:")
            
            for idx, (i, row) in enumerate(df_results.head(5).iterrows()):
                # Tentukan kelas card berdasarkan probabilitas
                if row['probabilitas'] >= 20:
                    card_class = "ai-card-high"
                    prob_text = "🔥 PROBABILITAS TINGGI"
                elif row['probabilitas'] >= 10:
                    card_class = "ai-card-mid"
                    prob_text = "⚠️ PROBABILITAS SEDANG"
                else:
                    card_class = "ai-card-low"
                    prob_text = "📌 PROBABILITAS RENDAH"
                
                # Panggil analisis AI
                analysis = analyze_pattern(row.to_dict())
                
                # Tampilkan card keren
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="ai-title">
                        📊 {row['saham']} 
                        <span style="float: right; font-size: 1rem; background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 20px;">
                            {prob_text}
                        </span>
                    </div>
                    
                    <div class="metric-container">
                        <div class="metric-item">
                            <div class="ai-label">🎯 Probabilitas</div>
                            <div class="ai-value-high">{row['probabilitas']:.1f}%</div>
                        </div>
                        <div class="metric-item">
                            <div class="ai-label">💰 Rata-rata Gain</div>
                            <div class="ai-value-mid">{row['rata_rata_kenaikan']:.1f}%</div>
                        </div>
                        <div class="metric-item">
                            <div class="ai-label">📈 Max Gain</div>
                            <div class="ai-value-high">{row['max_kenaikan']:.1f}%</div>
                        </div>
                        <div class="metric-item">
                            <div class="ai-label">📊 Frekuensi</div>
                            <div class="ai-value">{row['frekuensi']}x</div>
                        </div>
                    </div>
                    
                    <div class="ai-stat">
                        <span class="ai-label">📅 Pattern Terakhir:</span>
                        <span class="ai-value">{row.get('last_pattern_date', 'N/A')} (Gain: {row['last_kenaikan']:.1f}%)</span>
                    </div>
                    
                    <div class="ai-stat">
                        <span class="ai-label">📈 Trend Terkini:</span>
                        <span class="ai-value">{row.get('recent_trend', 'Normal')}</span>
                    </div>
                    
                    <div class="ai-conclusion">
                        <strong>📋 KESIMPULAN AI:</strong><br>
                        {analysis.replace('•', '▶').replace('\n', '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Export
            st.markdown("### 📥 Export Data")
            if st.button("📊 Export ke Excel", use_container_width=True):
                excel_data = export_to_excel(display_df)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=f"open_low_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.markdown("""
            <div class="warning-box">
                ⚠️ Tidak ditemukan saham dengan kriteria yang sesuai.<br>
                Coba turunkan minimal kenaikan atau perpanjang periode analisis.
            </div>
            """, unsafe_allow_html=True)

elif "Low Float" in scan_mode:
    st.markdown('<p class="sub-header">🔍 Scanner Low Float</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_public_float = st.slider(
            "📊 Maksimal Public Float (%)", 
            1, 50, 20,
            help="Saham dengan public float di bawah nilai ini"
        )
    
    with col2:
        min_volume = st.number_input(
            "📈 Minimal Volume", 
            min_value=0, 
            value=0, 
            step=100000,
            help="Minimal volume rata-rata (0 = abaikan)"
        )
    
    # Opsi mode scanning untuk low float
    scan_option = st.radio(
        "🔍 Mode Scanning:",
        ["⚡ Cepat (50 saham)", "🐢 Lengkap (Semua saham)"],
        horizontal=True,
        index=0
    )
    
    if st.button("🚀 SCAN LOW FLOAT", type="primary", use_container_width=True):
        # Tentukan stocks yang akan discan
        if selected_stocks:
            stocks_to_scan = selected_stocks
        else:
            if scan_option == "⚡ Cepat (50 saham)":
                stocks_to_scan = STOCKS_LIST[:50]
            else:
                stocks_to_scan = STOCKS_LIST
        
        with st.spinner(f"Mengumpulkan data {len(stocks_to_scan)} saham..."):
            results = scan_low_float(stocks_to_scan, max_public_float, min_volume)
            
            if results:
                df_results = pd.DataFrame(results)
                
                st.markdown(f"""
                <div class="success-box">
                    ✅ **Berhasil!** Ditemukan {len(df_results)} saham Low Float
                </div>
                """, unsafe_allow_html=True)
                
                # Tampilkan hasil
                st.markdown("### 📋 Hasil Scanning")
                
                display_df = df_results[[
                    'saham', 'public_float', 'category',
                    'volume_avg', 'volatility', 'low_float_score'
                ]].copy()
                
                display_df.columns = [
                    'Saham', 'Public Float (%)', 'Kategori',
                    'Volume', 'Volatilitas (%)', 'Score'
                ]
                
                # Format untuk tampilan
                display_df_display = display_df.copy()
                display_df_display['Public Float (%)'] = display_df_display['Public Float (%)'].apply(lambda x: f"{x:.2f}%")
                display_df_display['Volume'] = display_df_display['Volume'].apply(lambda x: f"{x:,.0f}")
                display_df_display['Volatilitas (%)'] = display_df_display['Volatilitas (%)'].apply(lambda x: f"{x:.2f}%")
                display_df_display['Score'] = display_df_display['Score'].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(
                    display_df_display,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Visualisasi
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart kategori
                    category_counts = df_results['category'].value_counts()
                    fig = px.pie(
                        values=category_counts.values,
                        names=category_counts.index,
                        title="Distribusi Kategori Low Float"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Scatter plot
                    fig = px.scatter(
                        df_results,
                        x='public_float',
                        y='volatility',
                        size='volume_avg',
                        hover_data=['saham'],
                        color='category',
                        title="Public Float vs Volatilitas",
                        labels={
                            'public_float': 'Public Float (%)',
                            'volatility': 'Volatilitas (%)'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # ========== FITUR AI UNTUK LOW FLOAT ==========
                st.markdown("## 🤖 Analisis Low Float")
                st.markdown("Analisis untuk saham Low Float terbaik:")
                
                for idx, (i, row) in enumerate(df_results.head(3).iterrows()):
                    # Tentukan kelas card berdasarkan kategori
                    if 'Ultra' in row['category']:
                        card_class = "ai-card-high"
                    elif 'Very' in row['category']:
                        card_class = "ai-card-mid"
                    else:
                        card_class = "ai-card-low"
                    
                    # Panggil analisis AI
                    analysis = analyze_low_float(row.to_dict())
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="ai-title">
                            🔥 {row['saham']} - {row['category']}
                            <span style="float: right; font-size: 1rem; background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 20px;">
                                Score: {row['low_float_score']:.1f}
                            </span>
                        </div>
                        
                        <div class="metric-container">
                            <div class="metric-item">
                                <div class="ai-label">📊 Public Float</div>
                                <div class="ai-value-high">{row['public_float']:.2f}%</div>
                            </div>
                            <div class="metric-item">
                                <div class="ai-label">📈 Volatilitas</div>
                                <div class="ai-value-mid">{row['volatility']:.2f}%</div>
                            </div>
                            <div class="metric-item">
                                <div class="ai-label">📊 Volume</div>
                                <div class="ai-value">{row['volume_avg']:,.0f}</div>
                            </div>
                        </div>
                        
                        <div class="ai-conclusion">
                            <strong>📋 KESIMPULAN AI:</strong><br>
                            {analysis.replace('•', '▶').replace('\n', '<br>')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Export
                if st.button("📊 Export ke Excel", use_container_width=True):
                    excel_data = export_to_excel(display_df)
                    st.download_button(
                        label="💾 Download Excel",
                        data=excel_data,
                        file_name=f"low_float_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.markdown("""
                <div class="warning-box">
                    ⚠️ Tidak ditemukan saham low float dengan kriteria tersebut.<br>
                    Coba naikkan maksimal public float atau turunkan minimal volume.
                </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>⚠️ <strong>Disclaimer:</strong> Data untuk tujuan edukasi, bukan rekomendasi investasi.</p>
    <p>Selalu lakukan analisis sendiri sebelum mengambil keputusan investasi.</p>
    <p>📊 Data dari Yahoo Finance | ⏱️ Update: Real-time | 🤖 AI Analysis Aktif</p>
</div>
""", unsafe_allow_html=True)
