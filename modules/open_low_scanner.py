import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .data_fetcher import get_stock_data, get_current_price

def scan_open_low_pattern(stock_code, periode_hari=30, min_kenaikan=5):
    """
    Scanner untuk pattern Open = Low dan naik minimal X%
    
    Parameters:
    - stock_code: kode saham
    - periode_hari: jumlah hari ke belakang untuk analisis
    - min_kenaikan: minimal kenaikan persentase dari low ke close
    
    Returns:
    - Dictionary hasil scanning atau None jika tidak memenuhi kriteria
    """
    try:
        # Ambil data historis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periode_hari + 10)  # Tambah buffer
        
        hist = get_stock_data(stock_code, period=f"{periode_hari + 10}d")
        
        if hist is None or len(hist) < periode_hari:
            return None
        
        # Analisis pattern Open = Low
        pattern_days = []
        kenaikan_values = []
        
        for i in range(len(hist)):
            row = hist.iloc[i]
            
            # Cek apakah Open = Low (dengan toleransi 0.5% untuk data real)
            open_price = row['Open']
            low_price = row['Low']
            
            # Open dianggap sama dengan Low jika selisih kurang dari 0.5%
            if abs(open_price - low_price) / low_price <= 0.005:
                # Hitung kenaikan dari low ke close
                kenaikan = ((row['Close'] - low_price) / low_price) * 100
                
                if kenaikan >= min_kenaikan:
                    pattern_days.append({
                        'date': row.name,
                        'open': open_price,
                        'low': low_price,
                        'close': row['Close'],
                        'high': row['High'],
                        'volume': row['Volume'],
                        'kenaikan': kenaikan
                    })
                    kenaikan_values.append(kenaikan)
        
        # Kalau tidak ada pattern, return None
        if not pattern_days:
            return None
        
        # Hitung statistik
        total_hari = len(hist)
        frekuensi = len(pattern_days)
        
        # Ambil data terkini
        current_data = get_current_price(stock_code)
        
        # Data tambahan untuk analisis
        recent_trend = analyze_recent_trend(hist.tail(10))
        
        result = {
            'saham': stock_code,
            'frekuensi': frekuensi,
            'total_kejadian': frekuensi,
            'total_hari_dianalisis': total_hari,
            'probabilitas': (frekuensi / total_hari) * 100,
            'rata_rata_kenaikan': np.mean(kenaikan_values) if kenaikan_values else 0,
            'max_kenaikan': max(kenaikan_values) if kenaikan_values else 0,
            'min_kenaikan': min(kenaikan_values) if kenaikan_values else 0,
            'std_kenaikan': np.std(kenaikan_values) if kenaikan_values else 0,
            'total_volume_pattern': sum(d['volume'] for d in pattern_days),
            'rata_rata_volume': sum(d['volume'] for d in pattern_days) / frekuensi if frekuensi > 0 else 0,
            'last_pattern_date': pattern_days[-1]['date'].strftime('%Y-%m-%d') if pattern_days else None,
            'last_kenaikan': pattern_days[-1]['kenaikan'] if pattern_days else 0,
            'current_price': current_data['close'] if current_data else 0,
            'recent_trend': recent_trend,
            'pattern_details': pattern_days[-5:]  # 5 pattern terakhir
        }
        
        return result
        
    except Exception as e:
        print(f"Error scanning {stock_code}: {e}")
        return None

def analyze_recent_trend(recent_data):
    """Analisis trend 10 hari terakhir"""
    if len(recent_data) < 5:
        return "Data tidak cukup"
    
    # Hitung moving average
    closes = recent_data['Close'].values
    ma5 = np.mean(closes[-5:])
    ma10 = np.mean(closes)
    
    # Trend based on MA
    if closes[-1] > ma5 > ma10:
        return "Uptrend kuat"
    elif closes[-1] > ma5:
        return "Uptrend"
    elif closes[-1] < ma5 < ma10:
        return "Downtrend kuat"
    elif closes[-1] < ma5:
        return "Downtrend"
    else:
        return "Sideways"

def scan_multiple_stocks(stocks_list, periode_hari=30, min_kenaikan=5, limit=20):
    """Scan multiple stocks sekaligus"""
    results = []
    
    for stock in stocks_list:
        result = scan_open_low_pattern(stock, periode_hari, min_kenaikan)
        if result:
            results.append(result)
    
    # Sort by frequency and return top results
    results.sort(key=lambda x: x['frekuensi'], reverse=True)
    return results[:limit]

def get_pattern_summary(results_df):
    """Membuat ringkasan dari hasil scanning"""
    if results_df.empty:
        return "Tidak ada data"
    
    summary = {
        'total_saham': len(results_df),
        'rata_rata_probabilitas': results_df['probabilitas'].mean(),
        'rata_rata_kenaikan': results_df['rata_rata_kenaikan'].mean(),
        'saham_tertinggi': results_df.iloc[0]['saham'] if not results_df.empty else None,
        'probabilitas_tertinggi': results_df['probabilitas'].max(),
        'kenaikan_tertinggi': results_df['max_kenaikan'].max()
    }
    
    return summary
