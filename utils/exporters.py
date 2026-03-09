import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .data_fetcher import get_stock_data, get_news_sentiment

class StockAnalyzer:
    """Class untuk analisis AI sederhana"""
    
    def __init__(self):
        self.patterns = {}
        self.insights = {}
    
    def analyze_pattern(self, stock_data):
        """
        Analisis pattern untuk satu saham
        
        Parameters:
        - stock_data: dictionary hasil dari open_low_scanner
        
        Returns:
        - String analisis
        """
        if not stock_data:
            return "Data tidak cukup untuk analisis"
        
        saham = stock_data['saham']
        prob = stock_data['probabilitas']
        avg_gain = stock_data['rata_rata_kenaikan']
        last_gain = stock_data['last_kenaikan']
        freq = stock_data['frekuensi']
        
        analysis = []
        
        # Analisis probabilitas
        if prob >= 20:
            analysis.append(f"📊 **Probabilitas Tinggi ({prob:.1f}%)** - Saham ini sering menunjukkan pattern Open=Low dalam {stock_data['total_hari_dianalisis']} hari terakhir.")
        elif prob >= 10:
            analysis.append(f"📊 **Probabilitas Sedang ({prob:.1f}%)** - Cukup sering muncul pattern Open=Low.")
        else:
            analysis.append(f"📊 **Probabilitas Rendah ({prob:.1f}%)** - Pattern Open=Low jarang terjadi.")
        
        # Analisis kenaikan
        if avg_gain >= 10:
            analysis.append(f"💰 **Kenaikan Rata-rata Tinggi ({avg_gain:.1f}%)** - Potensi gain besar saat pattern terjadi.")
        elif avg_gain >= 7:
            analysis.append(f"💰 **Kenaikan Rata-rata Sedang ({avg_gain:.1f}%)** - Potensi gain cukup baik.")
        else:
            analysis.append(f"💰 **Kenaikan Rata-rata ({avg_gain:.1f}%)** - Gain moderat.")
        
        # Konsistensi pattern
        if freq >= 10:
            analysis.append(f"🎯 **Sangat Konsisten** - Telah terjadi {freq} kali dalam periode analisis.")
        elif freq >= 5:
            analysis.append(f"🎯 **Cukup Konsisten** - Terjadi {freq} kali.")
        else:
            analysis.append(f"🎯 **Masih Jarang** - Baru {freq} kali terjadi.")
        
        # Trend terakhir
        if stock_data['recent_trend']:
            analysis.append(f"📈 **Trend Terkini:** {stock_data['recent_trend']}")
        
        # Pattern terakhir
        if stock_data['last_pattern_date']:
            analysis.append(f"⏰ **Pattern Terakhir:** {stock_data['last_pattern_date']} dengan kenaikan {stock_data['last_kenaikan']:.1f}%")
        
        # Rekomendasi
        if prob > 15 and avg_gain > 5:
            analysis.append("\n✅ **REKOMENDASI:** Menarik untuk diperhatikan. Pattern cukup sering terjadi dengan gain yang baik.")
        elif prob > 10:
            analysis.append("\n⚠️ **REKOMENDASI:** Bisa dicoba dengan risk management ketat.")
        else:
            analysis.append("\n📌 **REKOMENDASI:** Observasi dulu, pattern belum konsisten.")
        
        return "\n".join(analysis)
    
    def analyze_low_float(self, stock_data):
        """
        Analisis untuk saham low float
        """
        if not stock_data:
            return "Data tidak cukup"
        
        saham = stock_data['saham']
        public_float = stock_data['public_float']
        category = stock_data['category']
        volatility = stock_data['volatility']
        volume = stock_data['volume_avg']
        
        analysis = []
        
        # Analisis kategori
        if public_float < 5:
            analysis.append(f"🔥 **Ultra Low Float ({public_float:.1f}%)** - Sangat langka, potensi pergerakan ekstrem!")
        elif public_float < 10:
            analysis.append(f"⚡ **Very Low Float ({public_float:.1f}%)** - Pergerakan bisa sangat volatil.")
        elif public_float < 15:
            analysis.append(f"📊 **Low Float ({public_float:.1f}%)** - Cukup likuid dengan potensi pergerakan besar.")
        else:
            analysis.append(f"📈 **Normal Float ({public_float:.1f}%)** - Lebih stabil, pergerakan lebih moderat.")
        
        # Analisis volatilitas
        if volatility > 50:
            analysis.append(f"🌋 **Volatilitas Sangat Tinggi ({volatility:.1f}%)** - Siap untuk pergerakan besar!")
        elif volatility > 30:
            analysis.append(f"⚡ **Volatilitas Tinggi ({volatility:.1f}%)** - Cocok untuk trader aktif.")
        else:
            analysis.append(f"💧 **Volatilitas Normal ({volatility:.1f}%)** - Pergerakan relatif stabil.")
        
        # Analisis volume
        avg_vol_text = f"{volume:,.0f}" if volume > 0 else "N/A"
        if volume > 10000000:
            analysis.append(f"📊 **Volume Tinggi ({avg_vol_text})** - Likuiditas sangat baik.")
        elif volume > 1000000:
            analysis.append(f"📊 **Volume Sedang ({avg_vol_text})** - Cukup likuid.")
        else:
            analysis.append(f"📊 **Volume Rendah ({avg_vol_text})** - Waspada likuiditas.")
        
        # Skor low float
        analysis.append(f"🎯 **Low Float Score:** {stock_data['low_float_score']:.1f}/100")
        
        return "\n".join(analysis)
    
    def predict_next_pattern(self, stock_code, historical_data):
        """
        Prediksi sederhana kapan pattern akan muncul lagi
        """
        if historical_data is None or len(historical_data) < 50:
            return "Data historis tidak cukup untuk prediksi"
        
        # Analisis sederhana berdasarkan jarak antar pattern
        pattern_dates = []
        for i in range(1, len(historical_data)):
            if abs(historical_data['Open'].iloc[i] - historical_data['Low'].iloc[i]) / historical_data['Low'].iloc[i] <= 0.005:
                pattern_dates.append(historical_data.index[i])
        
        if len(pattern_dates) < 3:
            return "Belum cukup data pattern untuk prediksi"
        
        # Hitung rata-rata jarak antar pattern
        intervals = []
        for i in range(1, len(pattern_dates)):
            interval = (pattern_dates[i] - pattern_dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = np.mean(intervals)
        last_pattern = pattern_dates[-1]
        days_since_last = (datetime.now() - last_pattern).days
        
        if days_since_last >= avg_interval:
            return f"🔮 **Potensi pattern dalam waktu dekat** (rata-rata interval {avg_interval:.0f} hari, sudah {days_since_last} hari sejak pattern terakhir)"
        else:
            remaining = avg_interval - days_since_last
            return f"📅 **Rata-rata pattern setiap {avg_interval:.0f} hari** (terakhir {days_since_last} hari lalu, prediksi {remaining:.0f} hari lagi)"
    
    def get_market_context(self, stock_code):
        """
        Mendapatkan konteks pasar untuk saham
        """
        sentiment = get_news_sentiment(stock_code)
        
        context = []
        
        # Sentimen berita
        if sentiment['sentiment'] == 'positive':
            context.append(f"📰 **Sentimen Positif** (skor: {sentiment['score']})")
        elif sentiment['sentiment'] == 'negative':
            context.append(f"⚠️ **Sentimen Negatif** (skor: {sentiment['score']})")
        else:
            context.append("📰 **Sentimen Netral**")
        
        return "\n".join(context)

# Singleton instance
analyzer = StockAnalyzer()

# Fungsi helper
def analyze_pattern(stock_data):
    return analyzer.analyze_pattern(stock_data)

def analyze_low_float(stock_data):
    return analyzer.analyze_low_float(stock_data)

def predict_next_pattern(stock_code, historical_data):
    return analyzer.predict_next_pattern(stock_code, historical_data)

def get_market_context(stock_code):
    return analyzer.get_market_context(stock_code)
