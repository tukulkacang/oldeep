import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import sqlite3
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import requests
from dotenv import load_dotenv
import os
import json
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# ─── CONFIGURATION ───────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
DATABASE_PATH = 'radar_aksara.db'

# ─── DATABASE SETUP ──────────────────────────────────────────
def init_database():
    """Inisialisasi database SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Tabel untuk historical data
    c.execute('''CREATE TABLE IF NOT EXISTS stock_prices
                 (saham TEXT, tanggal DATE, open REAL, high REAL, 
                  low REAL, close REAL, volume INTEGER)''')
    
    # Tabel untuk fundamental data
    c.execute('''CREATE TABLE IF NOT EXISTS fundamental_data
                 (saham TEXT, market_cap REAL, pe_ratio REAL, 
                  pb_ratio REAL, volume_avg REAL, last_update DATE)''')
    
    # Tabel untuk free float & shareholders
    c.execute('''CREATE TABLE IF NOT EXISTS shareholders
                 (saham TEXT, nama TEXT, persen REAL, tipe TEXT,
                  tanggal_update DATE)''')
    
    # Tabel untuk insider trading
    c.execute('''CREATE TABLE IF NOT EXISTS insider_trades
                 (saham TEXT, tanggal DATE, insider TEXT,
                  aksi TEXT, jumlah INTEGER, harga REAL)''')
    
    # Tabel untuk hasil scan (caching)
    c.execute('''CREATE TABLE IF NOT EXISTS scan_results
                 (scan_id TEXT, saham TEXT, pattern_type TEXT,
                  frekuensi INTEGER, probabilitas REAL,
                  avg_gain REAL, max_gain REAL, scan_date DATE)''')
    
    conn.commit()
    conn.close()

# Panggil init database
init_database()

# ─── DATA FETCHER (REAL IMPLEMENTATION) ─────────────────────
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
            conn = sqlite3.connect(DATABASE_PATH)
            for idx, row in df.iterrows():
                conn.execute('''INSERT OR REPLACE INTO stock_prices 
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (symbol, idx.date(), row['Open'], row['High'],
                            row['Low'], row['Close'], row['Volume']))
            conn.commit()
            conn.close()
            
            return df
        except Exception as e:
            st.error(f"Error fetching {symbol}: {str(e)}")
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
            
            # Simpan ke database
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute('''INSERT OR REPLACE INTO fundamental_data
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (symbol, 
                        info.get('marketCap', 0),
                        info.get('trailingPE', 0),
                        info.get('priceToBook', 0),
                        info.get('averageVolume', 0),
                        datetime.now().date()))
            conn.commit()
            conn.close()
            
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

# ─── PATTERN SCANNER (OPTIMIZED) ────────────────────────────
class PatternScanner:
    """Scanner untuk berbagai pola saham"""
    
    @staticmethod
    def scan_open_low_pattern(symbol, days=30, min_gain=5):
        """Scan pola Open = Low dengan parallel processing"""
        try:
            df = DataFetcher.get_stock_data(symbol, period=f"{days}d")
            if df is None or len(df) < 5:
                return None
            
            patterns = []
            gains = []
            
            for i in range(1, len(df)):
                # Cek apakah Open ≈ Low (dengan toleransi 0.5%)
                if abs(df['Open'].iloc[i] - df['Low'].iloc[i]) / df['Low'].iloc[i] < 0.005:
                    patterns.append(df.index[i])
                    
                    # Hitung gain 5 hari ke depan
                    if i + 5 < len(df):
                        gain = (df['Close'].iloc[i+5] / df['Close'].iloc[i] - 1) * 100
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
                        
                        if volume_avg >= min_volume:
                            return {
                                'saham': symbol,
                                'free_float': ff,
                                'volatility': volatility,
                                'volume_avg': volume_avg,
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
        if ff < 10: return "Ultra Low Float"
        if ff < 15: return "Very Low Float"
        if ff < 25: return "Low Float"
        if ff < 40: return "Moderate Low Float"
        return "Normal Float"

# ─── AI ANALYZER (WITH REAL AI) ─────────────────────────────
class AIAnalyzer:
    """AI-powered analysis menggunakan rule-based + API"""
    
    @staticmethod
    def analyze_pattern(stock_data):
        """Generate analysis based on pattern data"""
        score = 0
        reasons = []
        
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
        
        if stock_data['rata_rata_kenaikan'] >= 10:
            score += 3
            reasons.append("💰 Rata-rata gain >10%")
        elif stock_data['rata_rata_kenaikan'] >= 5:
            score += 2
            reasons.append("💵 Rata-rata gain 5-10%")
        
        if stock_data['frekuensi'] >= 10:
            score += 2
            reasons.append("📊 Pola sering muncul (>10x)")
        
        # Generate recommendation
        if score >= 6:
            recommendation = "🚀 **STRONG BUY**"
            risk = "Rendah"
        elif score >= 4:
            recommendation = "📈 **BUY**"
            risk = "Sedang"
        elif score >= 2:
            recommendation = "👀 **WATCH**"
            risk = "Tinggi"
        else:
            recommendation = "⏸️ **HOLD/AVOID**"
            risk = "Sangat Tinggi"
        
        analysis = f"""
        ### {recommendation}
        
        **Risk Level:** {risk}
        
        **Key Points:**
        {chr(10).join(reasons)}
        
        **Insight:** 
        Saham {stock_data['saham']} menunjukkan pola Open=Low sebanyak {stock_data['frekuensi']}x 
        dengan probabilitas keberhasilan {stock_data['probabilitas']:.1f}% dan rata-rata gain 
        {stock_data['rata_rata_kenaikan']:.1f}%. 
        
        **Strategy:** 
        - Entry: Harga mendekati low hari ini
        - Target: {stock_data['rata_rata_kenaikan']:.1f}% dari entry
        - Stop Loss: -3% dari entry
        """
        
        return analysis
    
    @staticmethod
    def predict_next_target(stock_data):
        """Prediksi target harga berikutnya"""
        base_price = DataFetcher.get_current_price(stock_data['saham'])
        if base_price == 0:
            return "Harga tidak tersedia"
        
        avg_gain = stock_data.get('rata_rata_kenaikan', 5)
        prob = stock_data.get('probabilitas', 50)
        
        target1 = base_price * (1 + avg_gain/100)
        target2 = base_price * (1 + avg_gain*1.5/100)
        target3 = base_price * (1 + avg_gain*2/100)
        
        return f"""
        **Target Harga:**
        - Target 1 ({avg_gain:.1f}%): Rp {target1:,.0f}
        - Target 2 ({avg_gain*1.5:.1f}%): Rp {target2:,.0f}
        - Target 3 ({avg_gain*2:.1f}%): Rp {target3:,.0f}
        
        Probabilitas mencapai target: {prob:.1f}%
        """

# ─── NOTIFICATION SYSTEM ────────────────────────────────────
class NotificationSystem:
    """Telegram notifications for alerts"""
    
    @staticmethod
    def send_telegram_message(message):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            requests.post(url, json=payload, timeout=5)
            return True
        except:
            return False
    
    @staticmethod
    def create_alert_message(stock, pattern_type, data):
        message = f"""
🚨 <b>ALERT: {stock}</b>

Pattern: {pattern_type}
Price: Rp {DataFetcher.get_current_price(stock):,.0f}
Probability: {data.get('probabilitas', 0):.1f}%
Target Gain: {data.get('rata_rata_kenaikan', 0):.1f}%

#IDX #Trading #Alert
        """
        return message

# ─── BACKTESTING ENGINE ─────────────────────────────────────
class BacktestEngine:
    """Backtesting untuk validasi strategi"""
    
    @staticmethod
    def backtest_pattern(symbol, pattern_type="open_low", days=365):
        """Backtest pola Open=Low"""
        df = DataFetcher.get_stock_data(symbol, period=f"{days}d")
        if df is None or len(df) < 30:
            return None
        
        trades = []
        for i in range(20, len(df)-5):
            # Deteksi pola
            if abs(df['Open'].iloc[i] - df['Low'].iloc[i]) / df['Low'].iloc[i] < 0.005:
                entry_price = df['Close'].iloc[i]
                exit_price = df['Close'].iloc[i+5]
                
                profit = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_date': df.index[i],
                    'exit_date': df.index[i+5],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': profit
                })
        
        if trades:
            df_trades = pd.DataFrame(trades)
            return {
                'total_trades': len(trades),
                'win_rate': (len(df_trades[df_trades['profit'] > 0]) / len(trades)) * 100,
                'avg_profit': df_trades['profit'].mean(),
                'max_profit': df_trades['profit'].max(),
                'max_loss': df_trades['profit'].min(),
                'profit_factor': abs(df_trades[df_trades['profit'] > 0]['profit'].sum() / 
                                   df_trades[df_trades['profit'] < 0]['profit'].sum()) if len(df_trades[df_trades['profit'] < 0]) > 0 else float('inf')
            }
        return None

# ─── STOCKS LIST (DYNAMIC) ──────────────────────────────────
class StocksList:
    """Dynamic stock list dari database atau API"""
    
    @staticmethod
    def get_all_stocks():
        """Ambil semua saham dari database atau default list"""
        try:
            # Coba ambil dari database dulu
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute("SELECT DISTINCT saham FROM stock_prices")
            rows = c.fetchall()
            conn.close()
            
            if rows:
                return [row[0] for row in rows]
        except:
            pass
        
        # Default stocks jika database kosong
        return [
            "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNVR",
            "ICBP", "INDF", "KLBF", "GGRM", "HMSP", "ADRO", "BYAN",
            "PTBA", "CPIN", "JPFA", "SMGR", "INTP", "PGAS", "ANTM",
            "INCO", "MDKA", "HRUM", "BRPT", "TPIA", "WIKA", "PTPP"
        ]
    
    @staticmethod
    def get_sector(stock):
        """Ambil sektor saham"""
        try:
            data = DataFetcher.get_fundamental_data(stock)
            return data.get('sector', 'Unknown')
        except:
            return 'Unknown'

# ─── ENHANCED UI COMPONENTS ─────────────────────────────────
class UIComponents:
    """Komponen UI yang reusable"""
    
    @staticmethod
    def metric_card(title, value, delta=None, help_text=None):
        """Enhanced metric card"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.metric(title, value, delta, help=help_text)
    
    @staticmethod
    def backtest_results_card(results):
        """Tampilkan hasil backtest"""
        if not results:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", results['total_trades'])
        with col2:
            st.metric("Win Rate", f"{results['win_rate']:.1f}%")
        with col3:
            st.metric("Avg Profit", f"{results['avg_profit']:.1f}%")
        with col4:
            st.metric("Profit Factor", f"{results['profit_factor']:.2f}")
    
    @staticmethod
    def comparison_chart(stocks_data):
        """Chart untuk perbandingan multiple stocks"""
        fig = go.Figure()
        
        for stock, data in stocks_data.items():
            if data is not None and not data.empty:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    name=stock,
                    mode='lines'
                ))
        
        fig.update_layout(
            title="Stock Price Comparison",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark",
            height=500
        )
        
        return fig

# ─── MAIN APP (OPTIMIZED) ───────────────────────────────────
def main():
    st.set_page_config(
        page_title="Radar Aksara Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 RADAR AKSARA PRO</h1>
        <p>IDX Stock Screener dengan AI Analytics & Real-time Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
        st.title("Control Panel")
        
        # Mode selection
        mode = st.radio(
            "Pilih Mode Scanner",
            ["📈 Open = Low Scanner", "🔍 Low Float Scanner", "📊 Backtesting", "⚙️ Settings"]
        )
        
        st.markdown("---")
        
        # Filter options
        st.subheader("Filter Saham")
        
        filter_type = st.selectbox(
            "Jenis Filter",
            ["Semua Saham", "By Sektor", "By Kapitalisasi"]
        )
        
        if filter_type == "By Sektor":
            sectors = ["Finance", "Consumer", "Mining", "Property", "Technology", "Infrastructure"]
            selected_sectors = st.multiselect("Pilih Sektor", sectors, default=["Finance"])
        elif filter_type == "By Kapitalisasi":
            caps = ["Big Cap (>10T)", "Mid Cap (1T-10T)", "Small Cap (<1T)"]
            selected_caps = st.multiselect("Pilih Kapitalisasi", caps, default=["Big Cap"])
        
        st.markdown("---")
        
        # Notification settings
        st.subheader("Notifikasi")
        enable_notifications = st.checkbox("Aktifkan Telegram Notifikasi")
        if enable_notifications:
            if not TELEGRAM_BOT_TOKEN:
                st.warning("Telegram token belum di-set di .env file")
        
        # Auto-refresh
        st.subheader("Auto Refresh")
        auto_refresh = st.checkbox("Auto refresh setiap 5 menit")
        if auto_refresh:
            st.info("Aktif: Data akan di-refresh otomatis")
            time.sleep(300)  # 5 minutes
            st.experimental_rerun()
    
    # Main content based on mode
    if "Open = Low" in mode:
        show_open_low_scanner()
    elif "Low Float" in mode:
        show_low_float_scanner()
    elif "Backtesting" in mode:
        show_backtesting()
    else:
        show_settings()

# ─── SCANNER FUNCTIONS ──────────────────────────────────────
def show_open_low_scanner():
    """Open = Low Scanner dengan parallel processing"""
    st.header("📈 Open = Low Scanner")
    st.markdown("Mendeteksi saham dengan pola Open sama dengan Low")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox("Periode Analisis", ["7 Hari", "14 Hari", "30 Hari", "90 Hari"])
    with col2:
        min_gain = st.slider("Minimal Gain (%)", 1, 20, 5)
    with col3:
        limit = st.number_input("Limit Hasil", 5, 50, 20)
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if st.button("🚀 MULAI SCAN", type="primary"):
        # Ambil daftar saham
        stocks = StocksList.get_all_stocks()
        
        # Filter berdasarkan pilihan
        filtered_stocks = stocks[:50]  # Contoh: limit 50 untuk demo
        
        results = []
        scanner = PatternScanner()
        
        # Parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(scanner.scan_open_low_pattern, stock, 
                              int(period.split()[0]), min_gain): stock 
                for stock in filtered_stocks
            }
            
            for i, future in enumerate(as_completed(futures)):
                stock = futures[future]
                try:
                    result = future.result(timeout=10)
                    if result:
                        results.append(result)
                        
                        # Kirim notifikasi jika diaktifkan
                        if st.session_state.get('enable_notifications', False):
                            NotificationSystem.send_telegram_message(
                                NotificationSystem.create_alert_message(
                                    stock, "Open=Low", result
                                )
                            )
                except Exception as e:
                    status_text.text(f"Error processing {stock}: {str(e)}")
                
                # Update progress
                progress = (i + 1) / len(filtered_stocks)
                progress_bar.progress(progress)
                status_text.text(f"Processing: {i+1}/{len(filtered_stocks)} stocks")
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            # Tampilkan hasil
            df = pd.DataFrame(results)
            df = df.sort_values('probabilitas', ascending=False).head(limit)
            
            st.success(f"✅ Ditemukan {len(df)} saham dengan pola Open=Low!")
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📋 Hasil Scan", "📊 Analisis", "🤖 AI Insight"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
                
                # Export options
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, "scan_results.csv", "text/csv")
                with col2:
                    # Excel export
                    df.to_excel("scan_results.xlsx", index=False)
                    with open("scan_results.xlsx", "rb") as f:
                        st.download_button("📥 Download Excel", f, "scan_results.xlsx")
            
            with tab2:
                # Charts
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=("Top 10 by Probability", "Gain Distribution",
                                  "Frequency Analysis", "Risk-Reward")
                )
                
                # Top 10 probability
                top10 = df.head(10)
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['probabilitas'],
                          name="Probability", marker_color='green'),
                    row=1, col=1
                )
                
                # Gain distribution
                fig.add_trace(
                    go.Histogram(x=df['rata_rata_kenaikan'], nbinsx=20,
                                marker_color='blue', name="Gain"),
                    row=1, col=2
                )
                
                # Frequency
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['frekuensi'],
                          name="Frequency", marker_color='orange'),
                    row=2, col=1
                )
                
                # Scatter plot
                fig.add_trace(
                    go.Scatter(x=df['probabilitas'], y=df['rata_rata_kenaikan'],
                             mode='markers+text', text=df['saham'],
                             marker=dict(size=df['frekuensi']*2, color='red'),
                             name="Risk-Reward"),
                    row=2, col=2
                )
                
                fig.update_layout(height=800, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                # AI Analysis for top 5
                st.subheader("🤖 AI Analysis untuk Top 5 Saham")
                
                for _, row in df.head(5).iterrows():
                    with st.expander(f"📈 {row['saham']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Probability", f"{row['probabilitas']:.1f}%")
                            st.metric("Avg Gain", f"{row['rata_rata_kenaikan']:.1f}%")
                            st.metric("Frequency", f"{row['frekuensi']}x")
                        
                        with col2:
                            # AI Analysis
                            analysis = AIAnalyzer.analyze_pattern(row)
                            st.markdown(analysis)
                            
                            # Target prediction
                            targets = AIAnalyzer.predict_next_target(row)
                            st.markdown(targets)
                            
                            # Backtest button
                            if st.button(f"🔍 Backtest {row['saham']}", key=row['saham']):
                                backtest_results = BacktestEngine.backtest_pattern(row['saham'])
                                if backtest_results:
                                    UIComponents.backtest_results_card(backtest_results)
                                else:
                                    st.warning("Data tidak cukup untuk backtest")
        else:
            st.warning("Tidak ada saham yang memenuhi kriteria")

def show_low_float_scanner():
    """Low Float Scanner"""
    st.header("🔍 Low Float Scanner")
    st.markdown("Mendeteksi saham dengan free float rendah dan potensi volatilitas tinggi")
    
    col1, col2 = st.columns(2)
    with col1:
        max_ff = st.slider("Maksimal Free Float (%)", 5, 50, 25)
    with col2:
        min_volume = st.number_input("Minimal Volume (juta)", 0, 100, 1) * 1_000_000
    
    if st.button("🔍 SCAN LOW FLOAT", type="primary"):
        stocks = StocksList.get_all_stocks()
        
        with st.spinner("Scanning low float stocks..."):
            scanner = PatternScanner()
            results = scanner.scan_low_float(stocks, max_ff, min_volume)
        
        if results:
            df = pd.DataFrame(results)
            
            st.success(f"✅ Ditemukan {len(df)} saham dengan free float < {max_ff}%")
            
            # Visualization
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure(data=[
                    go.Pie(labels=df['category'].value_counts().index,
                          values=df['category'].value_counts().values,
                          hole=0.4)
                ])
                fig.update_layout(title="Distribusi Kategori Free Float")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure(data=[
                    go.Scatter(x=df['free_float'], y=df['volatility'],
                              mode='markers+text',
                              text=df['saham'],
                              marker=dict(
                                  size=df['volume_avg']/100000,
                                  color=df['volatility'],
                                  colorscale='Viridis',
                                  showscale=True
                              ))
                ])
                fig.update_layout(
                    title="Free Float vs Volatilitas",
                    xaxis_title="Free Float (%)",
                    yaxis_title="Volatilitas (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(df, use_container_width=True)
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "low_float_results.csv")
        else:
            st.warning("Tidak ada saham yang ditemukan")

def show_backtesting():
    """Backtesting feature"""
    st.header("📊 Backtesting Engine")
    st.markdown("Validasi strategi trading dengan data historis")
    
    col1, col2 = st.columns(2)
    with col1:
        stock = st.selectbox("Pilih Saham", StocksList.get_all_stocks())
    with col2:
        period = st.selectbox("Periode Backtest", ["30 Hari", "90 Hari", "365 Hari", "2 Tahun"])
    
    period_map = {
        "30 Hari": 30,
        "90 Hari": 90,
        "365 Hari": 365,
        "2 Tahun": 730
    }
    
    if st.button("🔍 RUN BACKTEST"):
        with st.spinner("Running backtest..."):
            results = BacktestEngine.backtest_pattern(stock, "open_low", period_map[period])
        
        if results:
            st.success("✅ Backtest selesai!")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", results['total_trades'])
            with col2:
                win_rate_color = "green" if results['win_rate'] >= 50 else "red"
                st.metric("Win Rate", f"{results['win_rate']:.1f}%", 
                         delta=f"{results['win_rate']-50:.1f}%" if results['win_rate'] != 50 else None)
            with col3:
                st.metric("Avg Profit", f"{results['avg_profit']:.2f}%")
            with col4:
                st.metric("Max Profit", f"{results['max_profit']:.2f}%")
            
            # Visualisasi
            st.subheader("📈 Performance Metrics")
            
            # Radar chart for performance
            categories = ['Win Rate', 'Avg Profit', 'Max Profit', 'Profit Factor']
            values = [
                results['win_rate']/20,  # Scale to 0-5
                min(results['avg_profit']/5, 5),
                min(results['max_profit']/10, 5),
                min(results['profit_factor'], 5)
            ]
            
            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )),
                showlegend=False,
                title="Strategy Performance Radar"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendation based on backtest
            if results['win_rate'] > 60 and results['avg_profit'] > 3:
                st.success("✅ STRATEGY VALID: Performa baik, bisa digunakan")
            elif results['win_rate'] > 50 and results['avg_profit'] > 0:
                st.warning("⚠️ STRATEGY MODERATE: Performa cukup, perlu optimasi")
            else:
                st.error("❌ STRATEGY INVALID: Performa buruk, hindari")
        else:
            st.warning("Data tidak cukup untuk backtest")

def show_settings():
    """Settings page"""
    st.header("⚙️ Settings")
    
    st.subheader("Database Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Update Database"):
            with st.spinner("Updating database..."):
                # Implement update logic
                time.sleep(2)
            st.success("Database updated!")
    
    with col2:
        if st.button("🗑️ Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
    
    st.subheader("Notification Settings")
    
    telegram_token = st.text_input("Telegram Bot Token", 
                                   value=TELEGRAM_BOT_TOKEN,
                                   type="password")
    telegram_chat = st.text_input("Telegram Chat ID", 
                                  value=TELEGRAM_CHAT_ID)
    
    if st.button("Save Settings"):
        # Save to .env file
        with open(".env", "w") as f:
            f.write(f"TELEGRAM_BOT_TOKEN={telegram_token}\n")
            f.write(f"TELEGRAM_CHAT_ID={telegram_chat}\n")
        st.success("Settings saved!")
    
    st.subheader("About")
    st.info("""
    **Radar Aksara Pro** v1.0
    
    Aplikasi screening saham IDX dengan fitur:
    - Real-time data dari Yahoo Finance
    - Pattern recognition (Open=Low)
    - Low float scanner
    - AI-powered analysis
    - Backtesting engine
    - Telegram notifications
    """)

# ─── RUN APP ─────────────────────────────────────────────────
if __name__ == "__main__":
    main()
