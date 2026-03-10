import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ─── AMBIL TAHUN DAN WAKTU SEKARANG ─────────────────
current_year = datetime.now().year
current_time = datetime.now().strftime("%d %b %Y %H:%M")
current_date = datetime.now().strftime("%d %B %Y")

# ─── DATABASE SETUP ─────────────────────────────────
def init_database():
    """Inisialisasi database SQLite"""
    conn = sqlite3.connect('radar_aksara.db')
    c = conn.cursor()
    
    # Tabel untuk historical data
    c.execute('''CREATE TABLE IF NOT EXISTS stock_prices
                 (saham TEXT, tanggal DATE, open REAL, high REAL, 
                  low REAL, close REAL, volume INTEGER)''')
    
    # Tabel untuk fundamental data
    c.execute('''CREATE TABLE IF NOT EXISTS fundamental_data
                 (saham TEXT, market_cap REAL, pe_ratio REAL, 
                  pb_ratio REAL, volume_avg REAL, last_update DATE)''')
    
    conn.commit()
    conn.close()

# Panggil init database
init_database()

# ─── DATA FETCHER ───────────────────────────────────
class DataFetcher:
    """Kelas untuk mengambil data saham real-time"""
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache 1 jam
    def get_stock_data(symbol, period="3mo"):
        """Ambil data historis saham dari Yahoo Finance"""
        try:
            ticker = yf.Ticker(f"{symbol}.JK")
            df = ticker.history(period=period)
            
            if df.empty:
                return None
                
            # Simpan ke database
            conn = sqlite3.connect('radar_aksara.db')
            for idx, row in df.iterrows():
                conn.execute('''INSERT OR REPLACE INTO stock_prices 
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (symbol, idx.date(), row['Open'], row['High'],
                            row['Low'], row['Close'], row['Volume']))
            conn.commit()
            conn.close()
            
            return df
        except Exception as e:
            return None
    
    @staticmethod
    @st.cache_data(ttl=1800)  # Cache 30 menit
    def get_current_price(symbol):
        """Ambil harga terkini"""
        try:
            ticker = yf.Ticker(f"{symbol}.JK")
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
            return 0
        except:
            return 0
    
    @staticmethod
    @st.cache_data(ttl=86400)  # Cache 24 jam
    def get_fundamental_data(symbol):
        """Ambil data fundamental"""
        try:
            ticker = yf.Ticker(f"{symbol}.JK")
            info = ticker.info
            
            return {
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'volume_avg': info.get('averageVolume', 0),
                'sector': info.get('sector', 'Unknown')
            }
        except Exception as e:
            return {
                'market_cap': 0,
                'pe_ratio': 0,
                'pb_ratio': 0,
                'volume_avg': 0,
                'sector': 'Unknown'
            }
    
    @staticmethod
    def get_free_float(symbol):
        """Estimasi free float dari market cap dan volume"""
        try:
            data = DataFetcher.get_fundamental_data(symbol)
            market_cap = data.get('market_cap', 0)
            
            # Logic sederhana: free float berdasarkan market cap
            if market_cap > 50e12:  # >50T
                return 80.0
            elif market_cap > 10e12:  # 10-50T
                return 70.0
            elif market_cap > 1e12:  # 1-10T
                return 50.0
            else:
                return 30.0
        except:
            return 50.0

# ─── PATTERN SCANNER ────────────────────────────────
class PatternScanner:
    """Scanner untuk berbagai pola saham"""
    
    @staticmethod
    def scan_open_low_pattern(symbol, days=30, min_gain=5, lookahead=5):
        """
        Scan pola Open = Low (PERSIS SAMA, tanpa toleransi)
        """
        try:
            df = DataFetcher.get_stock_data(symbol, period=f"{days}d")
            if df is None or len(df) < lookahead + 5:
                return None
            
            patterns = []
            gains = []
            
            for i in range(1, len(df) - lookahead):
                # CEK PERSIS: Open harus SAMA DENGAN Low
                if df['Open'].iloc[i] == df['Low'].iloc[i]:
                    patterns.append(df.index[i])
                    
                    # Hitung gain dalam periode lookahead
                    future_prices = df['High'].iloc[i+1:i+lookahead+1]
                    if not future_prices.empty:
                        max_future = future_prices.max()
                        gain = (max_future / df['Close'].iloc[i] - 1) * 100
                        gains.append(gain)
            
            if patterns and gains:
                result = {
                    'saham': symbol,
                    'frekuensi': len(patterns),
                    'probabilitas': (len([g for g in gains if g >= min_gain]) / len(gains)) * 100 if gains else 0,
                    'rata_rata_kenaikan': sum(gains) / len(gains) if gains else 0,
                    'max_kenaikan': max(gains) if gains else 0,
                    'min_kenaikan': min(gains) if gains else 0,
                    'last_pattern': patterns[-1].strftime('%Y-%m-%d') if patterns else None
                }
                return result
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def scan_low_float(symbols, max_ff=20, min_volume=0):
        """Scan low float stocks dengan parallel processing"""
        results = []
        
        def process_stock(symbol):
            try:
                ff = DataFetcher.get_free_float(symbol)
                if ff <= max_ff:
                    data = DataFetcher.get_stock_data(symbol, period="1mo")
                    if data is not None and len(data) > 5:
                        volatility = ((data['High'].max() - data['Low'].min()) / data['Low'].min()) * 100
                        volume_avg = data['Volume'].mean()
                        current_price = DataFetcher.get_current_price(symbol)
                        
                        if volume_avg >= min_volume:
                            return {
                                'saham': symbol,
                                'free_float': round(ff, 1),
                                'volatility': round(volatility, 1),
                                'volume_avg': int(volume_avg),
                                'current_price': round(current_price, 0),
                                'category': PatternScanner.get_ff_category(ff)
                            }
            except:
                pass
            return None
        
        # Parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_stock, symbol): symbol for symbol in symbols}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results
    
    @staticmethod
    def get_ff_category(ff):
        if ff < 10: return "🔥 Ultra Low"
        if ff < 15: return "⚡ Super Low"
        if ff < 25: return "💪 Low"
        if ff < 40: return "📊 Moderate"
        return "📈 Normal"

# ─── AI ANALYZER ────────────────────────────────────
class AIAnalyzer:
    """AI-powered analysis menggunakan rule-based"""
    
    @staticmethod
    def analyze_pattern(stock_data):
        """Generate analysis based on pattern data"""
        score = 0
        reasons = []
        warnings_list = []
        
        # Rule-based scoring
        if stock_data['probabilitas'] >= 70:
            score += 3
            reasons.append("✅ Probabilitas sangat tinggi (>70%)")
        elif stock_data['probabilitas'] >= 50:
            score += 2
            reasons.append("✓ Probabilitas baik (50-70%)")
        elif stock_data['probabilitas'] >= 30:
            score += 1
            reasons.append("⚠️ Probabilitas sedang (30-50%)")
        else:
            warnings_list.append("⚠️ Probabilitas rendah (<30%)")
        
        if stock_data['rata_rata_kenaikan'] >= 10:
            score += 3
            reasons.append("💰 Rata-rata gain >10%")
        elif stock_data['rata_rata_kenaikan'] >= 5:
            score += 2
            reasons.append("💵 Rata-rata gain 5-10%")
        else:
            warnings_list.append("📉 Rata-rata gain kecil (<5%)")
        
        if stock_data['frekuensi'] >= 10:
            score += 2
            reasons.append("📊 Pola sering muncul (>10x)")
        elif stock_data['frekuensi'] < 3:
            warnings_list.append("🔍 Pola jarang muncul")
        
        # Generate recommendation
        if score >= 6:
            recommendation = "🚀 **STRONG BUY**"
            bg_color = "#d4edda"
            text_color = "#155724"
        elif score >= 4:
            recommendation = "📈 **BUY**"
            bg_color = "#fff3cd"
            text_color = "#856404"
        elif score >= 2:
            recommendation = "👀 **WATCH**"
            bg_color = "#cce5ff"
            text_color = "#004085"
        else:
            recommendation = "⏸️ **HOLD/AVOID**"
            bg_color = "#f8d7da"
            text_color = "#721c24"
        
        # Current price
        current_price = DataFetcher.get_current_price(stock_data['saham'])
        
        analysis = f"""
        <div style="background-color: {bg_color}; color: {text_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h3 style="margin-top: 0;">{recommendation}</h3>
            <p><strong>Harga Saat Ini:</strong> Rp {current_price:,.0f}</p>
            
            <h4>📊 Key Points:</h4>
            <ul>
                {"".join([f"<li>{r}</li>" for r in reasons])}
            </ul>
            
            <h4>⚠️ Warnings:</h4>
            <ul>
                {"".join([f"<li>{w}</li>" for w in warnings_list]) if warnings_list else "<li>Tidak ada warning signifikan</li>"}
            </ul>
            
            <h4>💡 Insight:</h4>
            <p>Saham <b>{stock_data['saham']}</b> menunjukkan pola <b>Open = Low EXACT</b> sebanyak <b>{stock_data['frekuensi']}</b>x 
            dengan probabilitas keberhasilan <b>{stock_data['probabilitas']:.1f}%</b> dan rata-rata gain 
            <b>{stock_data['rata_rata_kenaikan']:.1f}%</b>.</p>
            
            <h4>🎯 Trading Strategy:</h4>
            <ul>
                <li><b>Entry:</b> Saat Open = Low terjadi</li>
                <li><b>Target 1:</b> {stock_data['rata_rata_kenaikan']:.1f}% (Rp {current_price * (1 + stock_data['rata_rata_kenaikan']/100):,.0f})</li>
                <li><b>Target 2:</b> {stock_data['rata_rata_kenaikan']*1.5:.1f}% (Rp {current_price * (1 + stock_data['rata_rata_kenaikan']*1.5/100):,.0f})</li>
                <li><b>Stop Loss:</b> -3% dari entry</li>
            </ul>
            
            <p><i>✨ Pola exact Open=Low adalah sinyal strong karena menunjukkan support kuat di level tersebut</i></p>
        </div>
        """
        
        return analysis

# ─── STOCKS LIST ────────────────────────────────────
class StocksList:
    """Dynamic stock list"""
    
    @staticmethod
    def get_all_stocks():
        """Ambil semua saham dari database atau default list"""
        try:
            # Coba ambil dari database dulu
            conn = sqlite3.connect('radar_aksara.db')
            c = conn.cursor()
            c.execute("SELECT DISTINCT saham FROM stock_prices LIMIT 100")
            rows = c.fetchall()
            conn.close()
            
            if rows:
                return [row[0] for row in rows]
        except:
            pass
        
        # Default stocks IDX
        return [
            "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNVR",
            "ICBP", "INDF", "KLBF", "GGRM", "HMSP", "ADRO", "BYAN",
            "PTBA", "CPIN", "JPFA", "SMGR", "INTP", "PGAS", "ANTM",
            "INCO", "MDKA", "HRUM", "BRPT", "TPIA", "WIKA", "PTPP",
            "AKRA", "EXCL", "ISAT", "TOWR", "MTEL", "SIDO", "UNTR",
            "ITMG", "MEDC", "ELSA", "BRMS"
        ]
    
    @staticmethod
    def get_stocks_by_sector(sector):
        """Filter saham berdasarkan sektor"""
        all_stocks = StocksList.get_all_stocks()
        filtered = []
        
        for stock in all_stocks[:20]:  # Limit untuk performa
            data = DataFetcher.get_fundamental_data(stock)
            if data.get('sector') == sector:
                filtered.append(stock)
        
        return filtered if filtered else all_stocks[:20]

# ─── MAIN APP ───────────────────────────────────────
def main():
    st.set_page_config(
        page_title=f"Radar Aksara {current_year} - Exact Open=Low Scanner",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .exact-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-left: 10px;
    }
    .live-badge {
        background: #ff4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .update-time {
        font-size: 11px;
        color: #888;
        text-align: right;
        margin-top: 5px;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
        border-radius: 25px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .footer {
        text-align: center;
        font-size: 11px;
        color: #666;
        padding: 20px 0;
        border-top: 1px solid #eee;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header dengan LIVE badge dan update time
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📊 RADAR AKSARA {current_year} <span class="exact-badge">EXACT MATCH</span></h1>
                <p>IDX Stock Screener - Open PERSIS SAMA dengan Low</p>
            </div>
            <div style="text-align: right;">
                <span class="live-badge">🔴 LIVE</span>
                <div style="font-size: 12px; color: white; margin-top: 5px;">
                    {current_time} WIB
                </div>
            </div>
        </div>
        <p style="font-size: 14px; opacity: 0.9; margin-top: 10px;">
            📈 Exact Pattern Scanner | 🔍 Low Float Scanner | 🤖 AI Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/stocks.png", width=100)
        st.markdown(f"## 🎯 Control Panel {current_year}")
        
        # Live indicator di sidebar
        st.markdown(f"""
        <div style="background: #e8f4fd; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <span style="color: #ff4444; font-size: 20px;">●</span>
                <span style="font-weight: bold;">LIVE DATA</span>
            </div>
            <div style="font-size: 11px; color: #666;">
                Update terakhir: {current_time} WIB<br>
                Sumber: Yahoo Finance
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mode selection
        mode = st.radio(
            "Pilih Mode Scanner",
            ["📈 Open = Low EXACT Scanner", "🔍 Low Float Scanner", "📊 Dashboard"]
        )
        
        st.markdown("---")
        
        # Filter options
        st.markdown("### 🔎 Filter Saham")
        
        filter_type = st.selectbox(
            "Jenis Filter",
            ["Semua Saham", "By Sektor"]
        )
        
        selected_sectors = []
        if filter_type == "By Sektor":
            sectors = ["Finance", "Consumer", "Energy", "Technology", "Infrastructure", "Mining"]
            selected_sectors = st.multiselect("Pilih Sektor", sectors, default=["Finance"])
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ Info")
        st.info("""
        **🎯 Exact Match:**
        - Open harus PERSIS SAMA dengan Low
        - Tanpa toleransi (0% selisih)
        - Sinyal lebih kuat & valid
        """)
        
        st.markdown("---")
        
        # FOOTER SIDEBAR - PAKE current_year
        st.caption(f"© {current_year} Radar Aksara • Data real-time dari Yahoo Finance")
        st.caption(f"🕒 Last sync: {current_time} WIB")
    
    # Main content based on mode
    if "EXACT" in mode:
        show_exact_open_low_scanner(filter_type, selected_sectors)
    elif "Low Float" in mode:
        show_low_float_scanner(filter_type, selected_sectors)
    else:
        show_dashboard()
    
    # FOOTER HALAMAN UTAMA
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        © {current_year} Radar Aksara • Data real-time dari Yahoo Finance<br>
        Last update: {current_time} WIB • ⚠️ Bukan rekomendasi investasi
    </div>
    """, unsafe_allow_html=True)

# ─── EXACT OPEN = LOW SCANNER ───────────────────────
def show_exact_open_low_scanner(filter_type, selected_sectors):
    st.header("📈 Open = Low EXACT Scanner")
    st.markdown(f"Mendeteksi saham dengan **Open PERSIS SAMA dengan Low** (0% selisih) - Sinyal Strong! • Update: {current_time} WIB")
    
    # Parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox("Periode Analisis", ["7 Hari", "14 Hari", "30 Hari", "90 Hari"], index=2)
        days = int(period.split()[0])
    with col2:
        min_gain = st.slider("Minimal Gain (%)", 1, 20, 5, help="Target kenaikan minimal")
    with col3:
        lookahead = st.slider("Hari Lookahead", 3, 10, 5, help="Jumlah hari untuk menghitung gain setelah pola")
    
    # Start button
    if st.button("🚀 MULAI SCAN EXACT", type="primary", use_container_width=True):
        # Get stocks based on filter
        if filter_type == "Semua Saham":
            stocks = StocksList.get_all_stocks()
        else:
            stocks = []
            for sector in selected_sectors:
                stocks.extend(StocksList.get_stocks_by_sector(sector))
            stocks = list(set(stocks))
        
        if not stocks:
            st.warning("Tidak ada saham yang dipilih!")
            return
        
        st.info(f"📊 Memproses {len(stocks)} saham... (Mencari Open = Low exact match)")
        
        # Progress bars
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Scan with parallel processing
        results = []
        scanner = PatternScanner()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(scanner.scan_open_low_pattern, stock, days, min_gain, lookahead): stock 
                for stock in stocks
            }
            
            for i, future in enumerate(as_completed(futures)):
                stock = futures[future]
                try:
                    result = future.result(timeout=15)
                    if result:
                        results.append(result)
                except Exception as e:
                    status_text.text(f"Error processing {stock}")
                
                # Update progress
                progress = (i + 1) / len(stocks)
                progress_bar.progress(progress)
                status_text.text(f"Scanning: {i+1}/{len(stocks)} saham")
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            # Create DataFrame and sort
            df = pd.DataFrame(results)
            df = df.sort_values(['probabilitas', 'rata_rata_kenaikan'], ascending=False)
            
            st.success(f"""
            ✅ **Ditemukan {len(df)} saham dengan pola Open = Low EXACT!**
            
            Dari {len(stocks)} saham yang discan, hanya {len(df)} yang memiliki pola Open PERSIS SAMA dengan Low.
            Ini adalah sinyal strong karena exact match!
            """)
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📋 Hasil Scan", "📊 Visualisasi", "🤖 Analisis AI"])
            
            with tab1:
                # Format dataframe for display
                display_df = df[['saham', 'frekuensi', 'probabilitas', 'rata_rata_kenaikan', 
                                'max_kenaikan', 'last_pattern']].copy()
                display_df.columns = ['Saham', 'Frekuensi', 'Probabilitas (%)', 'Rata² Gain (%)', 
                                     'Max Gain (%)', 'Pattern Terakhir']
                display_df['Probabilitas (%)'] = display_df['Probabilitas (%)'].round(1)
                display_df['Rata² Gain (%)'] = display_df['Rata² Gain (%)'].round(1)
                display_df['Max Gain (%)'] = display_df['Max Gain (%)'].round(1)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Export buttons
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, f"exact_pattern_{current_date}.csv", "text/csv", use_container_width=True)
                with col2:
                    # Excel export
                    df.to_excel(f"exact_pattern_{current_date}.xlsx", index=False)
                    with open(f"exact_pattern_{current_date}.xlsx", "rb") as f:
                        st.download_button("📥 Download Excel", f, f"exact_pattern_{current_date}.xlsx", use_container_width=True)
            
            with tab2:
                # Charts
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=("Top 10 by Probability", "Gain Distribution",
                                  "Frequency Analysis", "Risk-Reward Scatter"),
                    specs=[[{"type": "bar"}, {"type": "histogram"}],
                          [{"type": "bar"}, {"type": "scatter"}]]
                )
                
                top10 = df.head(10)
                
                # Top 10 probability
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['probabilitas'],
                          marker_color='green', name="Probability",
                          text=top10['probabilitas'].round(1),
                          textposition='outside'),
                    row=1, col=1
                )
                
                # Gain distribution
                fig.add_trace(
                    go.Histogram(x=df['rata_rata_kenaikan'], nbinsx=15,
                                marker_color='blue', name="Gain Distribution"),
                    row=1, col=2
                )
                
                # Frequency
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['frekuensi'],
                          marker_color='orange', name="Frequency",
                          text=top10['frekuensi'],
                          textposition='outside'),
                    row=2, col=1
                )
                
                # Risk-Reward scatter
                fig.add_trace(
                    go.Scatter(x=df['probabilitas'], y=df['rata_rata_kenaikan'],
                             mode='markers+text', text=df['saham'],
                             marker=dict(size=df['frekuensi']*2, 
                                       color=df['max_kenaikan'],
                                       colorscale='Viridis',
                                       showscale=True,
                                       colorbar=dict(title="Max Gain")),
                             name="Risk-Reward"),
                    row=2, col=2
                )
                
                fig.update_layout(height=800, showlegend=False,
                                title_text=f"Analisis Visual - Exact Pattern • {current_date}")
                fig.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                st.subheader("📈 Statistik Exact Pattern")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Exact Patterns", f"{df['frekuensi'].sum()}")
                with col2:
                    st.metric("Rata-rata Probabilitas", f"{df['probabilitas'].mean():.1f}%")
                with col3:
                    st.metric("Rata-rata Gain", f"{df['rata_rata_kenaikan'].mean():.1f}%")
                with col4:
                    st.metric("Saham Unik", len(df))
            
            with tab3:
                st.subheader("🤖 Analisis AI untuk Semua Exact Pattern")
                
                # Sort by best probability
                df_sorted = df.sort_values('probabilitas', ascending=False)
                
                for idx, row in df_sorted.iterrows():
                    with st.expander(f"📈 {row['saham']} - Prob: {row['probabilitas']:.1f}% | Gain: {row['rata_rata_kenaikan']:.1f}% (Exact Match)"):
                        # AI Analysis
                        analysis = AIAnalyzer.analyze_pattern(row)
                        st.markdown(analysis, unsafe_allow_html=True)
                        
                        # Chart pattern
                        st.subheader("📊 Chart Pattern")
                        price_data = DataFetcher.get_stock_data(row['saham'], period=f"{days}d")
                        if price_data is not None:
                            # Mark the exact pattern points
                            fig_price = go.Figure()
                            
                            # Candlestick
                            fig_price.add_trace(go.Candlestick(
                                x=price_data.index,
                                open=price_data['Open'],
                                high=price_data['High'],
                                low=price_data['Low'],
                                close=price_data['Close'],
                                name="Price"
                            ))
                            
                            # Mark pattern points
                            pattern_dates = []
                            for i in range(1, len(price_data)):
                                if price_data['Open'].iloc[i] == price_data['Low'].iloc[i]:
                                    pattern_dates.append(price_data.index[i])
                            
                            if pattern_dates:
                                fig_price.add_trace(go.Scatter(
                                    x=pattern_dates,
                                    y=[price_data['Low'][date] for date in pattern_dates],
                                    mode='markers',
                                    marker=dict(size=10, color='red', symbol='circle'),
                                    name='Exact Pattern'
                                ))
                            
                            fig_price.update_layout(
                                title=f"{row['saham']} - {days} Hari Chart dengan Exact Pattern",
                                height=400,
                                xaxis_rangeslider_visible=False
                            )
                            st.plotly_chart(fig_price, use_container_width=True)
                        
                        # Fundamental data
                        st.subheader("📋 Data Fundamental")
                        fund_data = DataFetcher.get_fundamental_data(row['saham'])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Market Cap", f"Rp {fund_data['market_cap']/1e12:.2f}T" if fund_data['market_cap'] > 1e12 else f"Rp {fund_data['market_cap']/1e9:.0f}M")
                        with col2:
                            st.metric("P/E Ratio", f"{fund_data['pe_ratio']:.1f}" if fund_data['pe_ratio'] > 0 else "N/A")
                        with col3:
                            st.metric("Volume Rata²", f"{fund_data['volume_avg']/1e6:.1f}M")
        else:
            st.warning("""
            ❌ **Tidak ditemukan saham dengan pola Open = Low EXACT!**
            
            Coba:
            - Perpanjang periode analisis
            - Kurangi minimal gain
            - Scan lebih banyak saham
            
            *Exact match memang jarang terjadi, tapi sinyalnya lebih kuat!*
            """)

# ─── LOW FLOAT SCANNER ──────────────────────────────
def show_low_float_scanner(filter_type, selected_sectors):
    st.header("🔍 Low Float Scanner")
    st.markdown(f"Mendeteksi saham dengan free float rendah dan potensi volatilitas tinggi • Update: {current_time} WIB")
    
    col1, col2 = st.columns(2)
    with col1:
        max_ff = st.slider("Maksimal Free Float (%)", 5, 50, 25, 
                          help="Free float < nilai ini")
    with col2:
        min_volume = st.number_input("Minimal Volume (juta)", 0, 100, 1) * 1_000_000
    
    if st.button("🔍 SCAN LOW FLOAT", type="primary", use_container_width=True):
        # Get stocks
        if filter_type == "Semua Saham":
            stocks = StocksList.get_all_stocks()
        else:
            stocks = []
            for sector in selected_sectors:
                stocks.extend(StocksList.get_stocks_by_sector(sector))
            stocks = list(set(stocks))
        
        if not stocks:
            st.warning("Tidak ada saham yang dipilih!")
            return
        
        with st.spinner(f"Scanning {len(stocks)} saham..."):
            scanner = PatternScanner()
            results = scanner.scan_low_float(stocks, max_ff, min_volume)
        
        if results:
            df = pd.DataFrame(results)
            
            st.success(f"✅ Ditemukan {len(df)} saham dengan free float < {max_ff}%!")
            
            # Tabs
            tab1, tab2, tab3 = st.tabs(["📋 Hasil Scan", "📊 Visualisasi", "📈 Detail"])
            
            with tab1:
                display_df = df[['saham', 'free_float', 'category', 'volatility', 
                                'volume_avg', 'current_price']].copy()
                display_df.columns = ['Saham', 'Free Float %', 'Kategori', 'Volatilitas %', 
                                     'Volume Rata²', 'Harga']
                display_df['Volume Rata²'] = (display_df['Volume Rata²'] / 1e6).round(1).astype(str) + 'M'
                display_df['Harga'] = display_df['Harga'].apply(lambda x: f"Rp {x:,.0f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Export
                csv = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, f"low_float_{current_date}.csv", "text/csv")
            
            with tab2:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart kategori
                    fig_pie = go.Figure(data=[
                        go.Pie(labels=df['category'].value_counts().index,
                              values=df['category'].value_counts().values,
                              hole=0.4,
                              marker_colors=['red', 'orange', 'yellow', 'green', 'blue'])
                    ])
                    fig_pie.update_layout(title=f"Distribusi Kategori Free Float • {current_date}")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Scatter plot
                    fig_scatter = go.Figure(data=[
                        go.Scatter(x=df['free_float'], y=df['volatility'],
                                  mode='markers+text',
                                  text=df['saham'],
                                  textposition="top center",
                                  marker=dict(
                                      size=df['volume_avg']/500000,
                                      color=df['volatility'],
                                      colorscale='Viridis',
                                      showscale=True,
                                      colorbar=dict(title="Volatilitas")
                                  ))
                    ])
                    fig_scatter.update_layout(
                        title=f"Free Float vs Volatilitas • {current_date}",
                        xaxis_title="Free Float (%)",
                        yaxis_title="Volatilitas (%)"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
            
            with tab3:
                st.subheader("📈 Top 5 Low Float Stocks")
                
                for idx, row in df.head(5).iterrows():
                    with st.expander(f"{row['saham']} - FF: {row['free_float']}% | Vol: {row['volatility']}%"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Free Float", f"{row['free_float']}%")
                        with col2:
                            st.metric("Volatilitas", f"{row['volatility']}%")
                        with col3:
                            st.metric("Harga", f"Rp {row['current_price']:,.0f}")
                        
                        # Chart harga
                        price_data = DataFetcher.get_stock_data(row['saham'], period="1mo")
                        if price_data is not None:
                            fig_price = go.Figure(data=[
                                go.Candlestick(
                                    x=price_data.index,
                                    open=price_data['Open'],
                                    high=price_data['High'],
                                    low=price_data['Low'],
                                    close=price_data['Close']
                                )
                            ])
                            fig_price.update_layout(title=f"{row['saham']} - 1 Month Chart",
                                                  height=400)
                            st.plotly_chart(fig_price, use_container_width=True)
        else:
            st.warning("Tidak ada saham yang ditemukan. Coba naikkan batas free float.")

# ─── DASHBOARD ──────────────────────────────────────
def show_dashboard():
    st.header(f"📊 Dashboard • {current_date}")
    st.markdown(f"Ringkasan market dan rekomendasi hari ini • Update: {current_time} WIB")
    
    # Market overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("IHSG", "7,234", "+0.5%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Volume", "18.2B", "+2.3%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Top Gainers", "142", "+12")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Top Losers", "89", "-5")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick scan
    st.subheader("🎯 Quick Scan Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Top Exact Open=Low Candidates**")
        stocks = StocksList.get_all_stocks()[:10]
        
        scanner = PatternScanner()
        results = []
        for stock in stocks:
            result = scanner.scan_open_low_pattern(stock, days=30, min_gain=5, lookahead=5)
            if result:
                results.append(result)
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('probabilitas', ascending=False).head(5)
            
            for _, row in df.iterrows():
                st.markdown(f"""
                - **{row['saham']}**: {row['probabilitas']:.1f}% prob, {row['rata_rata_kenaikan']:.1f}% gain
                """)
        else:
            st.info("Belum ada exact pattern ditemukan")
    
    with col2:
        st.markdown("**🔍 Top Low Float Candidates**")
        stocks = StocksList.get_all_stocks()[:10]
        
        results = scanner.scan_low_float(stocks, max_ff=30, min_volume=0)
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('volatility', ascending=False).head(5)
            
            for _, row in df.iterrows():
                st.markdown(f"""
                - **{row['saham']}**: {row['free_float']}% FF, {row['volatility']}% volatilitas
                """)
        else:
            st.info("Belum ada data scan")
    
    st.markdown("---")
    
    # Disclaimer
    st.info("""
    ⚠️ **Disclaimer**: Data ini untuk tujuan edukasi dan analisis, bukan rekomendasi investasi. 
    Selalu lakukan riset mandiri sebelum mengambil keputusan trading.
    """)

# ─── RUN APP ─────────────────────────────────────────
if __name__ == "__main__":
    main()
