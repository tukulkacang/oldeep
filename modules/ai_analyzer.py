import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# HAPUS baris import yang salah
# from modules.data_fetcher import get_news_sentiment  # <-- Ini juga gak dipakai

class StockAnalyzer:
    """Class untuk analisis AI sederhana"""
    
    def __init__(self):
        self.patterns = {}
        self.insights = {}
    
    def analyze_pattern(self, stock_data):
        """Analisis pattern untuk satu saham"""
        if not stock_data:
            return "Data tidak cukup untuk analisis"
        
        saham = stock_data.get('saham', 'Unknown')
        prob = stock_data.get('probabilitas', 0)
        avg_gain = stock_data.get('rata_rata_kenaikan', 0)
        freq = stock_data.get('frekuensi', 0)
        last_gain = stock_data.get('last_kenaikan', 0)
        
        analysis = []
        analysis.append(f"📊 **Analisis untuk {saham}:**")
        analysis.append(f"• Probabilitas pattern: {prob:.1f}%")
        analysis.append(f"• Rata-rata kenaikan: {avg_gain:.1f}%")
        analysis.append(f"• Frekuensi kejadian: {freq}x")
        analysis.append(f"• Kenaikan terakhir: {last_gain:.1f}%")
        
        if prob >= 20:
            analysis.append("\n✅ **Kesimpulan:** Potensi TINGGI untuk pattern Open=Low")
        elif prob >= 10:
            analysis.append("\n⚠️ **Kesimpulan:** Potensi SEDANG untuk pattern Open=Low") 
        else:
            analysis.append("\n📌 **Kesimpulan:** Potensi RENDAH untuk pattern Open=Low")
        
        return "\n".join(analysis)
    
    def analyze_low_float(self, stock_data):
        """Analisis untuk saham low float"""
        if not stock_data:
            return "Data tidak cukup"
        
        saham = stock_data.get('saham', 'Unknown')
        public_float = stock_data.get('public_float', 0)
        category = stock_data.get('category', 'Normal')
        volatility = stock_data.get('volatility', 0)
        volume = stock_data.get('volume_avg', 0)
        score = stock_data.get('low_float_score', 0)
        
        analysis = []
        analysis.append(f"📊 **Analisis Low Float {saham}:**")
        analysis.append(f"• Public Float: {public_float:.1f}% ({category})")
        analysis.append(f"• Volatilitas: {volatility:.1f}%")
        analysis.append(f"• Volume rata-rata: {volume:,.0f}")
        analysis.append(f"• Score: {score:.1f}/100")
        
        if public_float < 5:
            analysis.append("\n🔥 **Ultra Low Float** - Sangat langka, potensi pergerakan ekstrem!")
        elif public_float < 10:
            analysis.append("\n⚡ **Very Low Float** - Pergerakan bisa sangat volatil.")
        elif public_float < 15:
            analysis.append("\n📊 **Low Float** - Cukup likuid dengan potensi pergerakan besar.")
        else:
            analysis.append("\n📈 **Normal Float** - Lebih stabil, pergerakan lebih moderat.")
        
        return "\n".join(analysis)
    
    def predict_next_pattern(self, stock_code, historical_data):
        """Prediksi sederhana kapan pattern akan muncul lagi"""
        return "🔮 Fitur prediksi dalam pengembangan"
    
    def get_market_context(self, stock_code):
        """Mendapatkan konteks pasar untuk saham"""
        return "📰 **Konteks Pasar:**\n• Sentimen: Netral\n• Tidak ada berita signifikan"

# Fungsi helper
analyzer = StockAnalyzer()

def analyze_pattern(stock_data):
    return analyzer.analyze_pattern(stock_data)

def analyze_low_float(stock_data):
    return analyzer.analyze_low_float(stock_data)

def predict_next_pattern(stock_code, historical_data):
    return analyzer.predict_next_pattern(stock_code, historical_data)

def get_market_context(stock_code):
    return analyzer.get_market_context(stock_code)
