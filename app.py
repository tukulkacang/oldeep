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
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 30px; border-radius: 20px; margin: 25px 0 35px 0; text-align: center; color: white; border: 2px solid #ffd700; box-shadow: 0 20px 40px rgba(102,126,234,0.4); position: relative; overflow: hidden;">
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
                st.markdown(f"""
                <div class="watchlist-header">
                    <h2 style="color: white; margin: 0;">📋 WATCHLIST TRADING</h2>
                    <p style="color: #a8d8ff; font-size: 1.2rem;">{datetime.now().strftime('%d %B %Y')}</p>
                    <p style="color: #ffaa00;">Pantau 15 menit pertama! Open=Low = Siap eksekusi 🎯</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Buat tabel watchlist
                watchlist_data = []
                for i, (idx, row) in enumerate(df_watchlist.iterrows()):
                    if row['probabilitas'] >= 20 and row['rata_rata_kenaikan'] >= 7:
                        rekom = "🔥 PRIORITAS UTAMA"
                    elif row['probabilitas'] >= 15 and row['rata_rata_kenaikan'] >= 5:
                        rekom = "⚡ LAYAK DICOBA"
                    else:
                        rekom = "📌 PANTAU"
                    
                    watchlist_data.append({
                        "Rank": i + 1,
                        "Saham": row['saham'],
                        "Probabilitas": f"{row['probabilitas']:.1f}%",
                        "Gain Rata": f"{row['rata_rata_kenaikan']:.1f}%",
                        "Max Gain": f"{row['max_kenaikan']:.1f}%",
                        "Frekuensi": f"{row['frekuensi']}x",
                        "Rekomendasi": rekom
                    })
                
                # Tampilkan dataframe
                watchlist_df = pd.DataFrame(watchlist_data)
                st.dataframe(
                    watchlist_df,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Export buttons
                st.markdown("### 📥 Export Watchlist")
                
                # Export CSV
                csv_data = watchlist_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data,
                    file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Export Excel
                excel_data = export_to_excel(watchlist_df)
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
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
            
            # Export hasil scanning utama
            st.markdown("### 📥 Export Data Scanning")
            if st.button("📊 Export Hasil Scanning ke Excel", use_container_width=True):
                excel_data = export_to_excel(display_df)
                st.download_button(
                    label="💾 Download Excel Scanning",
                    data=excel_data,
                    file_name=f"open_low_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white; border-left: 8px solid #ffd700;">
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
            results = scan_low_float(stocks_to_scan, max_public_float, min_volume)
            
            if results:
                df_results = pd.DataFrame(results)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 25px; border-radius: 15px; margin: 20px 0; text-align: center; color: white; border: 2px solid #ffd700;">
                    <h2 style="color: #ffd700; margin: 0;">✅ SCAN LOW FLOAT BERHASIL</h2>
                    <p style="font-size: 2rem; margin: 10px 0;">{len(df_results)} SAHAM</p>
                    <p>Ditemukan saham dengan public float di bawah {max_public_float}%</p>
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
                <div style="background: linear-gradient(135deg, #f093fb, #f5576c); padding: 20px; border-radius: 15px; text-align: center; color: white;">
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
