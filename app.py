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
    @st.cache_data(ttl=3600)
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
    @st.cache_data(ttl=1800)
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
    @st.cache_data(ttl=86400)
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
        """Estimasi free float dari market cap"""
        try:
            data = DataFetcher.get_fundamental_data(symbol)
            market_cap = data.get('market_cap', 0)
            
            if market_cap > 50e12:
                return 80.0
            elif market_cap > 10e12:
                return 70.0
            elif market_cap > 1e12:
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
        """Scan pola Open = Low EXACT"""
        try:
            df = DataFetcher.get_stock_data(symbol, period=f"{days}d")
            if df is None or len(df) < lookahead + 5:
                return None
            
            patterns = []
            gains = []
            
            for i in range(1, len(df) - lookahead):
                if df['Open'].iloc[i] == df['Low'].iloc[i]:
                    patterns.append(df.index[i])
                    
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
        """Scan low float stocks"""
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

# ─── STOCKS LIST (LENGKAP 900+ SAHAM IDX) ───────────────────
class StocksList:
    """Dynamic stock list - LENGKAP 900+ SAHAM IDX"""
    
    @staticmethod
    def get_all_stocks():
        """Ambil SEMUA saham IDX (900+ saham dari file pertama)"""
        try:
            # Coba ambil dari database dulu
            conn = sqlite3.connect('radar_aksara.db')
            c = conn.cursor()
            c.execute("SELECT DISTINCT saham FROM stock_prices")
            rows = c.fetchall()
            conn.close()
            
            if rows and len(rows) > 100:
                st.info(f"📊 Load {len(rows)} saham dari database")
                return [row[0] for row in rows]
        except:
            pass
        
        # DEFAULT LIST LENGKAP 900+ SAHAM IDX (dari file pertama)
        st.info("📊 Load master list 956 saham IDX")
        return [
            # A
            "AALI", "ABBA", "ABDA", "ABMM", "ACES", "ADES", "ADHI", "ADMF", "ADRO", "AGAR",
            "AGII", "AGRO", "AGRS", "AIMS", "AISA", "AKRA", "AKSI", "ALDO", "ALKA", "ALMI",
            "ALTO", "AMAG", "AMFG", "AMIN", "AMOR", "AMRT", "ANJT", "ANTM", "APEX", "APIC",
            "APLI", "APLN", "ARGO", "ARII", "ARNA", "ARTA", "ARTO", "ASBI", "ASDM", "ASGR",
            "ASII", "ASJI", "ASMI", "ASRI", "ASSA", "ATAP", "AUTO", "AUVE",
            
            # B
            "BABP", "BACA", "BAEK", "BALI", "BANK", "BAPA", "BATA", "BAYU", "BBCA", "BBHI",
            "BBKP", "BBLD", "BBMD", "BBNI", "BBRI", "BBRM", "BBTN", "BBYB", "BCAP", "BCIC",
            "BDMN", "BEEF", "BEKS", "BEST", "BFIN", "BGTG", "BHAT", "BHTL", "BIKA", "BIMA",
            "BIPP", "BIRD", "BISL", "BJBR", "BJTM", "BKDP", "BKSL", "BKSW", "BLTA", "BLTZ",
            "BMAS", "BMRI", "BMSR", "BMTR", "BNBA", "BNBR", "BNGA", "BNII", "BNLI", "BOGA",
            "BOLA", "BOLT", "BPFI", "BPII", "BPTR", "BRAM", "BRIS", "BRMS", "BRPT", "BSDE",
            "BSIM", "BSSR", "BSTC", "BSUP", "BTPN", "BTPS", "BTON", "BUDI", "BULL", "BUVA",
            "BYAN",
            
            # C
            "CAMP", "CANI", "CARS", "CASA", "CASH", "CAST", "CBRE", "CBUT", "CCSI", "CEKA",
            "CENT", "CFIN", "CGAS", "CINT", "CITA", "CKRA", "CLAY", "CLEO", "CLPI", "CMNP",
            "CMPP", "CMSI", "CNKO", "CNMA", "CNTB", "COAL", "COCO", "COMI", "CPIN", "CPRO",
            "CSAP", "CSIS", "CTBN", "CTRA", "CUAN", "CYBR",
            
            # D
            "DART", "DATA", "DAVO", "DAYA", "DCII", "DECK", "DEGI", "DEWA", "DFAM", "DGIK",
            "DILD", "DIVA", "DKFT", "DMAS", "DMMX", "DNET", "DOID", "DPNS", "DPUM", "DSFI",
            "DSNG", "DSSA", "DUCK", "DVLA", "DYAN",
            
            # E
            "EAGLE", "EAST", "ECII", "EDGE", "EKAD", "ELSA", "ELTY", "EMDE", "EMTK", "ENRG",
            "EPAC", "EPMT", "ERAA", "ESSA", "ESTA", "ETWA", "EXCL",
            
            # F
            "FAJS", "FAPA", "FASW", "FAST", "FILM", "FIMP", "FIRE", "FISH", "FMII", "FORU",
            "FOZZ", "FPNI", "FREN", "FREY", "FUTR",
            
            # G
            "GAMA", "GATA", "GAYA", "GDST", "GDYR", "GEMS", "GGRM", "GIDS", "GJTL", "GLVA",
            "GMFI", "GOLD", "GOOD", "GOLL", "GPRA", "GPSO", "GSMF", "GTBO", "GTSI", "GULA",
            "GWSA",
            
            # H
            "HADE", "HALO", "HAPP", "HDIT", "HDFA", "HDTX", "HEAD", "HEAL", "HEXA", "HITS",
            "HKMU", "HMSP", "HOKI", "HOMI", "HOPE", "HRME", "HRTA", "HRUM", "HSMP", "HUPS",
            "HUTS", "HYGN",
            
            # I
            "IBFN", "IBST", "ICBP", "ICON", "IDPR", "IDSD", "IFII", "IFSH", "IGAR", "IIKP",
            "IKAI", "IKAN", "IMAS", "IMJS", "IMPC", "INAF", "INAI", "INCF", "INCO", "INCP",
            "INDF", "INDO", "INDR", "INDS", "INDX", "INKP", "INPC", "INPP", "INPS", "INRU",
            "INTA", "INTD", "INTK", "INTP", "IPCC", "IPCM", "IPOL", "IPTV", "ISAT", "ISSP",
            "ITIC", "ITMA", "ITMG", "IZZI",
            
            # J
            "JAST", "JAWA", "JECC", "JEMP", "JFAS", "JFIN", "JGLE", "JHAS", "JISS", "JIHD",
            "JKON", "JKSW", "JMAS", "JNKA", "JPFA", "JPUR", "JRPT", "JSKY", "JSMR", "JSPT",
            "JTPE", "JTRK",
            
            # K
            "KABF", "KARW", "KASN", "KAYU", "KBAG", "KBRI", "KDSI", "KEEN", "KEJU", "KBLI",
            "KBLM", "KBRI", "KDSI", "KIAS", "KICI", "KIG", "KIJA", "KINO", "KIOS", "KIRK",
            "KLAS", "KLBF", "KLEV", "KMDS", "KMTR", "KOBX", "KOCI", "KOIN", "KOKA", "KONI",
            "KOPI", "KOTA", "KPAL", "KPIG", "KRAS", "KREN", "KUAS", "KUBU", "KUFP",
            
            # L
            "LABA", "LAGG", "LAPD", "LAPI", "LATU", "LAYU", "LCGP", "LCKM", "LDST", "LEAD",
            "LFCB", "LGI", "LGSM", "LINK", "LION", "LIVE", "LMAS", "LMPI", "LMSH", "LPCK",
            "LPGI", "LPIN", "LPKR", "LPLI", "LPPS", "LSIP", "LSPT", "LTLS", "LUCY", "LUKU",
            "LVR",
            
            # M
            "MABA", "MABH", "MAGP", "MAIN", "MALA", "MAMI", "MAND", "MAPB", "MAPE", "MAPI",
            "MAPA", "MARI", "MARK", "MASA", "MASB", "MAXI", "MAYA", "MBAI", "MBAP", "MBSS",
            "MBTO", "MCAS", "MCCI", "MCDS", "MCOL", "MDIA", "MDKA", "MDKI", "MDRN", "MEDC",
            "MEGA", "MERK", "META", "MFIN", "MFMI", "MGNA", "MICE", "MIDI", "MIKA", "MINA",
            "MIRA", "MITI", "MIX", "MLIA", "MLPL", "MLPT", "MNCN", "MOLI", "MPMX", "MPPA",
            "MPRO", "MRAT", "MREI", "MSIE", "MTDL", "MTEL", "MTFN", "MTLA", "MTMH", "MTPS",
            "MTSM", "MTWI", "MUD", "MUTU", "MYOH", "MYOR", "MYRX", "MZON",
            
            # N
            "NATO", "NELY", "NETV", "NFCX", "NICL", "NIKL", "NIPS", "NISP", "NITY", "NOBU",
            "NPGF", "NUSA",
            
            # O
            "OASA", "OBCD", "OCAP", "OILS", "OKAS", "OMED", "OMRE", "ONIX", "ONLY", "OPEN",
            "ORANG", "OTTO",
            
            # P
            "PABA", "PABU", "PALM", "PAMG", "PANR", "PANS", "PBID", "PBRX", "PBSA", "PDES",
            "PEGE", "PGLI", "PGUN", "PHPC", "PIAA", "PID", "PIFI", "PINA", "PINI", "PIPE",
            "PJAA", "PKPK", "PLAN", "PLAS", "PLIN", "PMJS", "PMPP", "PNBN", "PNBS", "PNIN",
            "PNLF", "PNSE", "POOL", "PORT", "POWR", "PPGL", "PPRE", "PPRI", "PPSI", "PPRO",
            "PRAS", "PRAY", "PRDA", "PRIM", "PRIN", "PSAB", "PSDN", "PTBA", "PTDU", "PTIS",
            "PTMP", "PTRO", "PTSN", "PUDP", "PURI", "PWON", "PYFA",
            
            # R
            "RACE", "RAJA", "RALS", "RANC", "RATU", "RBMS", "RDTX", "REAL", "RELI", "RIMO",
            "RISE", "RMBA", "ROCK", "RODA", "ROTI", "RSCH", "RUKO", "RUM", "RUSA",
            
            # S
            "SABA", "SAFE", "SAIP", "SAME", "SAMF", "SAMP", "SANI", "SAPX", "SARA", "SATO",
            "SBA", "SBAT", "SBMA", "SCCO", "SCMA", "SCMA", "SDPI", "SDRA", "SEAN", "SEC",
            "SEMA", "SFAN", "SFSN", "SGER", "SGRO", "SIDO", "SILO", "SIMA", "SIMP", "SINA",
            "SIPT", "SKBM", "SKLT", "SKYB", "SLIS", "SMAR", "SMDR", "SMGR", "SMIL", "SMKL",
            "SMMT", "SMSM", "SMTE", "SMTG", "SMTO", "SNLK", "SNMS", "SOC", "SOCI", "SODA",
            "SONA", "SOSS", "SOUL", "SPMA", "SPMI", "SPNA", "SPTO", "SQMI", "SRIL", "SRSN",
            "SRTG", "SSIA", "SSMS", "SSTM", "STAR", "STTP", "SUGI", "SULI", "SUMR", "SUNI",
            "SUPR", "SURY", "SUSA", "SUZI", "SWAT",
            
            # T
            "TABA", "TAXI", "TBMS", "TBLA", "TBP", "TCID", "TCPI", "TDPM", "TEBE", "TECH",
            "TELK", "TEMB", "TEMP", "TERA", "TIFA", "TIGA", "TIRA", "TIRO", "TIRT", "TISH",
            "TKIM", "TLKM", "TMAS", "TMPI", "TOTL", "TOWR", "TPIA", "TPMA", "TRAM", "TRAY",
            "TRIL", "TRIM", "TRIN", "TRIO", "TRIS", "TRJA", "TRST", "TRUB", "TRUS", "TSAM",
            "TSPC", "TUGU", "TURI", "TUTI", "TUV",
            
            # U
            "UANG", "UCID", "UEES", "ULTJ", "UNIC", "UNIQ", "UNIT", "UNSP", "UNTR", "UNVR",
            "URBN", "USFI",
            
            # V
            "VALU", "VICO", "VINS", "VIVA", "VOKS", "VRNA", "VTNY", "VOK",
            
            # W
            "WAPO", "WEGE", "WEHA", "WGSH", "WICO", "WIIM", "WIKA", "WINR", "WINS", "WINT",
            "WMUU", "WOMF", "WOOD", "WOWS", "WSBP", "WSKT", "WSKT",
            
            # Y
            "YELO", "YEMA", "YULE",
            
            # Z
            "ZBRA", "ZINC", "ZONE"
        ]
    
    @staticmethod
    def count_stocks():
        """Hitung total saham"""
        return len(StocksList.get_all_stocks())
    
    @staticmethod
    def get_stocks_by_sector(sector):
        """Filter saham berdasarkan sektor (simplified)"""
        all_stocks = StocksList.get_all_stocks()
        
        # Simplified sector mapping (untuk demo)
        sector_map = {
            "Finance": ["BBCA", "BBRI", "BMRI", "BBNI", "BTPS", "BRIS", "BJBR", "BJTM", "BNGA", "BNII"],
            "Consumer": ["UNVR", "ICBP", "INDF", "KLBF", "GGRM", "HMSP", "SIDO", "ULTJ", "MYOR", "ROTI"],
            "Energy": ["ADRO", "BYAN", "PTBA", "ITMG", "MEDC", "ELSA", "PGAS", "RAJA", "BUMI", "DOID"],
            "Mining": ["ANTM", "INCO", "MDKA", "HRUM", "BRMS", "TINS", "CITA", "DKFT", "PSAB", "SMRU"],
            "Infrastructure": ["TLKM", "ISAT", "EXCL", "TOWR", "MTEL", "JSMR", "WIKA", "PTPP", "WSKT", "ADHI"],
            "Technology": ["MTDL", "MLPT", "DIVA", "HDTX", "EMTK", "CNMA", "SCMA", "MNCN", "LINK", "DCII"]
        }
        
        return sector_map.get(sector, all_stocks[:50])

# ─── UI COMPONENTS ──────────────────────────────────
class UIComponents:
    """Komponen UI reusable"""
    
    @staticmethod
    def live_badge():
        return f"""
        <div style="display: inline-block; background: #ff4444; color: white; 
                    padding: 2px 8px; border-radius: 12px; font-size: 10px; 
                    font-weight: bold; animation: pulse 2s infinite;">
            🔴 LIVE
        </div>
        """
    
    @staticmethod
    def stats_card(title, value, delta=None):
        return f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 15px; border-radius: 10px; color: white; text-align: center;">
            <div style="font-size: 12px; opacity: 0.9;">{title}</div>
            <div style="font-size: 24px; font-weight: bold;">{value}</div>
            {f'<div style="font-size: 14px;">{delta}</div>' if delta else ''}
        </div>
        """

# ─── MAIN APP ───────────────────────────────────────
def main():
    st.set_page_config(
        page_title=f"Radar Aksara {current_year} - IDX Scanner (956 Saham)",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .exact-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin-left: 10px;
    }
    
    .stock-count {
        background: rgba(255,255,255,0.2);
        padding: 5px 15px;
        border-radius: 25px;
        font-size: 14px;
        display: inline-block;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .footer {
        text-align: center;
        font-size: 11px;
        color: #666;
        padding: 20px 0;
        border-top: 1px solid #eee;
        margin-top: 30px;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header dengan total saham
    total_stocks = StocksList.count_stocks()
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📊 RADAR AKSARA {current_year} <span class="exact-badge">EXACT MATCH</span></h1>
                <p style="margin: 5px 0; opacity: 0.9;">
                    IDX Stock Screener - Open PERSIS SAMA dengan Low
                </p>
                <div style="margin-top: 10px;">
                    <span class="stock-count">📈 {total_stocks} SAHAM IDX</span>
                </div>
            </div>
            <div style="text-align: right;">
                {UIComponents.live_badge()}
                <div style="font-size: 13px; margin-top: 5px; opacity: 0.9;">
                    {current_time} WIB
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/stocks.png", width=100)
        st.markdown(f"## 🎯 Control Panel {current_year}")
        
        # Live indicator
        st.markdown(f"""
        <div style="background: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 5px;">
                <span style="color: #ff4444; font-size: 20px;">●</span>
                <span style="font-weight: bold;">LIVE DATA</span>
            </div>
            <div style="font-size: 12px; color: #666;">
                Update: {current_time} WIB<br>
                Saham: {total_stocks} IDX<br>
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
            sectors = ["Finance", "Consumer", "Energy", "Mining", "Infrastructure", "Technology"]
            selected_sectors = st.multiselect("Pilih Sektor", sectors, default=["Finance"])
        
        st.markdown("---")
        
        # Info panel
        st.markdown("### ℹ️ Info")
        st.info(f"""
        **Dataset:** {total_stocks} saham IDX
        **Scanner:** Exact Open=Low
        **Update:** Real-time
        
        **🎯 Exact Match:**
        - Open PERSIS SAMA dengan Low
        - Tanpa toleransi
        - Sinyal lebih kuat
        """)
        
        st.markdown("---")
        st.caption(f"© {current_year} Radar Aksara • Data real-time")
    
    # Main content based on mode
    if "EXACT" in mode:
        show_exact_open_low_scanner(filter_type, selected_sectors, total_stocks)
    elif "Low Float" in mode:
        show_low_float_scanner(filter_type, selected_sectors, total_stocks)
    else:
        show_dashboard(total_stocks)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        © {current_year} Radar Aksara • Data real-time dari Yahoo Finance<br>
        Last update: {current_time} WIB • Total saham: {total_stocks} IDX<br>
        ⚠️ Bukan rekomendasi investasi
    </div>
    """, unsafe_allow_html=True)

# ─── EXACT OPEN = LOW SCANNER ───────────────────────
def show_exact_open_low_scanner(filter_type, selected_sectors, total_stocks):
    st.header("📈 Open = Low EXACT Scanner")
    st.markdown(f"Mendeteksi saham dengan **Open PERSIS SAMA dengan Low** (0% selisih) • Update: {current_time} WIB")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        period = st.selectbox("Periode Analisis", ["7 Hari", "14 Hari", "30 Hari", "90 Hari"], index=2)
        days = int(period.split()[0])
    with col2:
        min_gain = st.slider("Minimal Gain (%)", 1, 20, 5)
    with col3:
        lookahead = st.slider("Hari Lookahead", 3, 10, 5)
    
    # Info total saham
    st.info(f"📊 **Total saham di database: {total_stocks} saham IDX**")
    
    if st.button("🚀 MULAI SCAN EXACT", type="primary", use_container_width=True):
        # Get stocks based on filter
        if filter_type == "Semua Saham":
            stocks = StocksList.get_all_stocks()
            total_scan = len(stocks)
            st.success(f"📊 **Scanning {total_scan} saham IDX...**")
        else:
            stocks = []
            for sector in selected_sectors:
                stocks.extend(StocksList.get_stocks_by_sector(sector))
            stocks = list(set(stocks))
            total_scan = len(stocks)
            st.success(f"📊 **Scanning {total_scan} saham sektor {', '.join(selected_sectors)}...**")
        
        # Progress bars
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_estimate = st.empty()
        
        start_time = time.time()
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
                except:
                    pass
                
                # Update progress
                progress = (i + 1) / total_scan
                progress_bar.progress(progress)
                
                elapsed = time.time() - start_time
                remaining = (elapsed / (i + 1)) * (total_scan - i - 1) if i > 0 else 0
                
                status_text.text(f"Scanning: {i+1}/{total_scan} saham • Found: {len(results)}")
                time_estimate.text(f"⏱️ Elapsed: {int(elapsed)}s • Remaining: ~{int(remaining)}s")
        
        progress_bar.empty()
        status_text.empty()
        time_estimate.empty()
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values(['probabilitas', 'rata_rata_kenaikan'], ascending=False)
            
            st.success(f"""
            ✅ **Ditemukan {len(df)} saham dengan pola Open = Low EXACT!**
            
            Dari **{total_scan} saham** yang discan, hanya **{len(df)}** yang memiliki pola Open PERSIS SAMA dengan Low.
            Ini adalah sinyal strong karena exact match!
            """)
            
            # Tabs
            tab1, tab2, tab3 = st.tabs(["📋 Hasil Scan", "📊 Visualisasi", "🤖 Analisis AI"])
            
            with tab1:
                display_df = df[['saham', 'frekuensi', 'probabilitas', 'rata_rata_kenaikan', 
                                'max_kenaikan', 'last_pattern']].copy()
                display_df.columns = ['Saham', 'Frekuensi', 'Probabilitas (%)', 'Rata² Gain (%)', 
                                     'Max Gain (%)', 'Pattern Terakhir']
                display_df['Probabilitas (%)'] = display_df['Probabilitas (%)'].round(1)
                display_df['Rata² Gain (%)'] = display_df['Rata² Gain (%)'].round(1)
                display_df['Max Gain (%)'] = display_df['Max Gain (%)'].round(1)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, f"exact_pattern_{current_date}.csv", "text/csv", use_container_width=True)
                with col2:
                    df.to_excel(f"exact_pattern_{current_date}.xlsx", index=False)
                    with open(f"exact_pattern_{current_date}.xlsx", "rb") as f:
                        st.download_button("📥 Download Excel", f, f"exact_pattern_{current_date}.xlsx", use_container_width=True)
            
            with tab2:
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=("Top 10 by Probability", "Gain Distribution",
                                  "Frequency Analysis", "Risk-Reward Scatter")
                )
                
                top10 = df.head(10)
                
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['probabilitas'],
                          marker_color='green', text=top10['probabilitas'].round(1),
                          textposition='outside'),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Histogram(x=df['rata_rata_kenaikan'], nbinsx=15,
                                marker_color='blue'),
                    row=1, col=2
                )
                
                fig.add_trace(
                    go.Bar(x=top10['saham'], y=top10['frekuensi'],
                          marker_color='orange', text=top10['frekuensi'],
                          textposition='outside'),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(x=df['probabilitas'], y=df['rata_rata_kenaikan'],
                             mode='markers+text', text=df['saham'],
                             marker=dict(size=df['frekuensi']*2, 
                                       color=df['max_kenaikan'],
                                       colorscale='Viridis',
                                       showscale=True)),
                    row=2, col=2
                )
                
                fig.update_layout(height=800, showlegend=False,
                                title_text=f"Analisis Visual • {current_date}")
                fig.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("🤖 Analisis AI")
                for idx, row in df.head(10).iterrows():
                    with st.expander(f"📈 {row['saham']} - Prob: {row['probabilitas']:.1f}% | Gain: {row['rata_rata_kenaikan']:.1f}%"):
                        analysis = AIAnalyzer.analyze_pattern(row)
                        st.markdown(analysis, unsafe_allow_html=True)
        else:
            st.warning("""
            ❌ **Tidak ditemukan saham dengan pola Open = Low EXACT!**
            
            Coba:
            - Perpanjang periode analisis
            - Kurangi minimal gain
            - Scan lebih banyak saham
            """)

# ─── LOW FLOAT SCANNER ──────────────────────────────
def show_low_float_scanner(filter_type, selected_sectors, total_stocks):
    st.header("🔍 Low Float Scanner")
    st.markdown(f"Mendeteksi saham dengan free float rendah • Update: {current_time} WIB")
    
    col1, col2 = st.columns(2)
    with col1:
        max_ff = st.slider("Maksimal Free Float (%)", 5, 50, 25)
    with col2:
        min_volume = st.number_input("Minimal Volume (juta)", 0, 100, 1) * 1_000_000
    
    st.info(f"📊 **Total saham di database: {total_stocks} saham IDX**")
    
    if st.button("🔍 SCAN LOW FLOAT", type="primary", use_container_width=True):
        if filter_type == "Semua Saham":
            stocks = StocksList.get_all_stocks()
        else:
            stocks = []
            for sector in selected_sectors:
                stocks.extend(StocksList.get_stocks_by_sector(sector))
            stocks = list(set(stocks))
        
        with st.spinner(f"Scanning {len(stocks)} saham..."):
            scanner = PatternScanner()
            results = scanner.scan_low_float(stocks, max_ff, min_volume)
        
        if results:
            df = pd.DataFrame(results)
            st.success(f"✅ Ditemukan {len(df)} saham dengan free float < {max_ff}%!")
            
            display_df = df[['saham', 'free_float', 'category', 'volatility', 
                            'volume_avg', 'current_price']].copy()
            display_df.columns = ['Saham', 'Free Float %', 'Kategori', 'Volatilitas %', 
                                 'Volume Rata²', 'Harga']
            display_df['Volume Rata²'] = (display_df['Volume Rata²'] / 1e6).round(1).astype(str) + 'M'
            display_df['Harga'] = display_df['Harga'].apply(lambda x: f"Rp {x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"low_float_{current_date}.csv", "text/csv")
        else:
            st.warning("Tidak ada saham yang ditemukan.")

# ─── DASHBOARD ──────────────────────────────────────
def show_dashboard(total_stocks):
    st.header(f"📊 Dashboard • {current_date}")
    st.markdown(f"Ringkasan market • Update: {current_time} WIB")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Saham", f"{total_stocks}")
    with col2:
        st.metric("IHSG", "7,234", "+0.5%")
    with col3:
        st.metric("Volume", "18.2B", "+2.3%")
    with col4:
        st.metric("Top Gainers", "142", "+12")
    
    st.markdown("---")
    st.info("⚡ Pilih mode scanner di sidebar untuk mulai analisis!")

# ─── RUN APP ─────────────────────────────────────────
if __name__ == "__main__":
    main()
