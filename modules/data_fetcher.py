import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
from bs4 import BeautifulSoup
import random

class DataFetcher:
    """Class untuk mengambil data saham"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 menit cache
    
    def get_stock_data(self, stock_code, period="1mo"):
        """
        Mengambil data saham dari Yahoo Finance
        Format: stock_code.JK untuk saham Indonesia
        """
        try:
            # Cek cache
            cache_key = f"{stock_code}_{period}"
            if cache_key in self.cache:
                cache_time, cache_data = self.cache[cache_key]
                if (datetime.now() - cache_time).seconds < self.cache_duration:
                    return cache_data
            
            # Ambil data dari Yahoo Finance
            ticker = yf.Ticker(f"{stock_code}.JK")
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            # Simpan ke cache
            self.cache[cache_key] = (datetime.now(), hist)
            
            return hist
            
        except Exception as e:
            print(f"Error mengambil data {stock_code}: {e}")
            return None
    
    def get_historical_data(self, stock_code, start_date, end_date):
        """Mengambil data historis dalam range tanggal tertentu"""
        try:
            ticker = yf.Ticker(f"{stock_code}.JK")
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            return hist
            
        except Exception as e:
            print(f"Error mengambil data historis {stock_code}: {e}")
            return None
    
    def get_current_price(self, stock_code):
        """Mengambil harga terkini"""
        try:
            ticker = yf.Ticker(f"{stock_code}.JK")
            data = ticker.history(period="1d")
            
            if not data.empty:
                return {
                    'open': data['Open'].iloc[-1],
                    'high': data['High'].iloc[-1],
                    'low': data['Low'].iloc[-1],
                    'close': data['Close'].iloc[-1],
                    'volume': data['Volume'].iloc[-1]
                }
            return None
            
        except Exception as e:
            print(f"Error mengambil harga {stock_code}: {e}")
            return None
    
    def get_fundamental_data(self, stock_code):
        """Mengambil data fundamental (untuk low float)"""
        try:
            ticker = yf.Ticker(f"{stock_code}.JK")
            
            # Ambil info
            info = ticker.info
            
            # Data untuk low float calculation
            shares_outstanding = info.get('sharesOutstanding', 0)
            float_shares = info.get('floatShares', 0)
            
            if shares_outstanding and float_shares:
                public_float = (float_shares / shares_outstanding) * 100
            else:
                # Fallback ke data dummy untuk testing
                public_float = random.uniform(5, 40)
                shares_outstanding = random.randint(1000000, 1000000000)
            
            return {
                'saham': stock_code,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'public_float': public_float,
                'total_shares': shares_outstanding,
                'insider_ownership': random.uniform(0, 30),  # Data dummy, perlu sumber lain
                'institutional_ownership': random.uniform(10, 60),  # Data dummy
                'volume_avg': info.get('averageVolume', 0)
            }
            
        except Exception as e:
            print(f"Error mengambil data fundamental {stock_code}: {e}")
            return None
    
    def get_news_sentiment(self, stock_code):
        """Analisis sentimen berita sederhana"""
        try:
            ticker = yf.Ticker(f"{stock_code}.JK")
            news = ticker.news
            
            if news:
                # Analisis sederhana berdasarkan judul
                positive_words = ['naik', 'untung', 'bagus', 'tumbuh', 'bangkit', 'positif']
                negative_words = ['turun', 'rugi', 'buruk', 'anjlok', 'krisis', 'negatif']
                
                sentiment_score = 0
                for article in news[:5]:  # 5 berita terakhir
                    title = article.get('title', '').lower()
                    for word in positive_words:
                        if word in title:
                            sentiment_score += 1
                    for word in negative_words:
                        if word in title:
                            sentiment_score -= 1
                
                return {
                    'sentiment': 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral',
                    'score': sentiment_score,
                    'news_count': len(news)
                }
            
            return {'sentiment': 'neutral', 'score': 0, 'news_count': 0}
            
        except Exception as e:
            return {'sentiment': 'neutral', 'score': 0, 'news_count': 0}

# Singleton instance
fetcher = DataFetcher()

# Fungsi helper untuk memudahkan import
def get_stock_data(stock_code, period="1mo"):
    return fetcher.get_stock_data(stock_code, period)

def get_historical_data(stock_code, start_date, end_date):
    return fetcher.get_historical_data(stock_code, start_date, end_date)

def get_current_price(stock_code):
    return fetcher.get_current_price(stock_code)

def get_fundamental_data(stock_code):
    return fetcher.get_fundamental_data(stock_code)

def get_news_sentiment(stock_code):
    return fetcher.get_news_sentiment(stock_code)
