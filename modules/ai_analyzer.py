import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class StockAnalyzer:
    """Class untuk analisis AI sederhana"""
    
    def __init__(self):
        self.patterns = {}
        self.insights = {}
    
    def analyze_pattern(self, stock_data):
        """
        Analisis pattern untuk satu saham
        """
        if not stock_data:
            return "Data tidak cukup untuk analisis"
        
        saham = stock_data.get('saham', 'Unknown')
        prob = stock_data.get('probabilitas', 0)
        avg_gain = stock_data.get('rata_rata_kenaikan', 0)
        freq = stock_data.get('frekuensi', 0)
        
        analysis = []
        analysis.append(f"📊 Analisis untuk {saham}:")
        analysis.append(f"• Probabilitas pattern: {prob:.1f}%")
        analysis.append(f"• Rata-rata kenaikan: {avg_gain:.1f}%")
        analysis.append(f"• Frekuensi kejadian: {freq}x")
        
        if prob >= 20:
            analysis.append("✅ Potensi tinggi untuk pattern Open=Low")
        elif prob >= 10:
            analysis.append("⚠️ Potensi sedang untuk pattern Open=Low") 
        else:
            analysis.append("📌 Potensi rendah untuk pattern Open=Low")
        
        return "\n".join(analysis)
    
    def analyze_low_float(self, stock_data):
        """Analisis untuk saham low float"""
        if not stock_data:
            return "Data tidak cukup"
        
        saham = stock_data.get('saham', 'Unknown')
        public_float = stock_data.get('public_float', 0)
        category = stock_data.get('category', 'Normal')
        volatility = stock_data.get('volatility', 0)
        
        analysis = []
        analysis.append(f"📊 Analisis Low Float {saham}:")
        analysis.append(f"• Public Float: {public_float:.1f}% ({category})")
        analysis.append(f"• Volatilitas: {volatility:.1f}%")
        
        if public_float < 10:
            analysis.append("🔥 Sangat rendah - potensi pergerakan besar")
        elif public_float < 20:
            analysis.append("⚡ Rendah - cukup volatil")
        else:
            analysis.append("📊 Normal - pergerakan stabil")
        
        return "\n".join(analysis)
    
    def predict_next_pattern(self, stock_code, historical_data):
        """Prediksi sederhana kapan pattern akan muncul lagi"""
        return "🔮 Fitur prediksi dalam pengembangan"
    
    def get_market_context(self, stock_code):
        """Mendapatkan konteks pasar untuk saham"""
        return "📰 Sentimen pasar: Netral"

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
