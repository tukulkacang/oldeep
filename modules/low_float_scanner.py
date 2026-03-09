import pandas as pd
import numpy as np
from .data_fetcher import get_fundamental_data, get_stock_data

def scan_low_float(stocks_list, max_public_float=20, min_volume=0):
    """
    Scanner untuk saham low float
    
    Parameters:
    - stocks_list: list saham yang akan discan
    - max_public_float: batas maksimal public float (%)
    - min_volume: minimal volume rata-rata
    
    Returns:
    - List saham low float dengan datanya
    """
    results = []
    
    for stock in stocks_list:
        # Ambil data fundamental
        fund_data = get_fundamental_data(stock)
        
        if fund_data and fund_data['public_float'] <= max_public_float:
            # Cek volume jika diperlukan
            if min_volume > 0 and fund_data['volume_avg'] < min_volume:
                continue
            
            # Ambil data tambahan
            hist_data = get_stock_data(stock, period="1mo")
            
            if hist_data is not None and not hist_data.empty:
                # Hitung volatility
                returns = hist_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100  # Annualized
                
                # Hitung average true range
                high_low = hist_data['High'] - hist_data['Low']
                high_close = abs(hist_data['High'] - hist_data['Close'].shift())
                low_close = abs(hist_data['Low'] - hist_data['Close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                atr = true_range.rolling(14).mean().iloc[-1]
            else:
                volatility = 0
                atr = 0
            
            # Hitung skor low float
            low_float_score = calculate_low_float_score(
                fund_data['public_float'],
                volatility,
                fund_data['volume_avg']
            )
            
            result = {
                'saham': stock,
                'company_name': fund_data.get('company_name', 'N/A'),
                'sector': fund_data.get('sector', 'N/A'),
                'public_float': fund_data['public_float'],
                'total_shares': fund_data['total_shares'],
                'market_cap': fund_data.get('market_cap', 0),
                'insider_ownership': fund_data.get('insider_ownership', 0),
                'institutional_ownership': fund_data.get('institutional_ownership', 0),
                'volume_avg': fund_data.get('volume_avg', 0),
                'volatility': volatility,
                'atr': atr,
                'low_float_score': low_float_score,
                'category': categorize_low_float(fund_data['public_float'])
            }
            
            results.append(result)
    
    # Sort by low float (ascending) and score
    results.sort(key=lambda x: (x['public_float'], -x['low_float_score']))
    
    return results

def calculate_low_float_score(public_float, volatility, volume):
    """
    Menghitung skor untuk saham low float
    Semakin rendah float, semakin tinggi skor
    """
    float_score = max(0, 100 - public_float)  # 100 - float%
    
    # Volatility score (higher volatility = higher score untuk trader)
    vol_score = min(volatility * 2, 50)  # Cap di 50
    
    # Volume score (higher volume = higher score)
    volume_score = min(np.log10(volume + 1) * 5, 30) if volume > 0 else 0
    
    total_score = float_score * 0.5 + vol_score * 0.3 + volume_score * 0.2
    
    return round(total_score, 2)

def categorize_low_float(public_float):
    """Kategorisasi berdasarkan persentase public float"""
    if public_float < 5:
        return "Ultra Low Float"
    elif public_float < 10:
        return "Very Low Float"
    elif public_float < 15:
        return "Low Float"
    elif public_float < 20:
        return "Moderate Low Float"
    else:
        return "Normal Float"

def get_low_float_summary(results):
    """Membuat ringkasan hasil scanning low float"""
    if not results:
        return "Tidak ada data"
    
    df = pd.DataFrame(results)
    
    summary = {
        'total_saham': len(df),
        'rata_rata_public_float': df['public_float'].mean(),
        'rata_rata_volume': df['volume_avg'].mean(),
        'rata_rata_volatility': df['volatility'].mean(),
        'ultra_low_count': len(df[df['category'] == 'Ultra Low Float']),
        'very_low_count': len(df[df['category'] == 'Very Low Float']),
        'low_count': len(df[df['category'] == 'Low Float']),
        'top_saham': df.nsmallest(5, 'public_float')[['saham', 'public_float', 'category']].to_dict('records')
    }
    
    return summary

def get_float_analysis(stock_code):
    """Analisis detail untuk satu saham"""
    fund_data = get_fundamental_data(stock_code)
    
    if not fund_data:
        return None
    
    hist_data = get_stock_data(stock_code, period="3mo")
    
    analysis = {
        'saham': stock_code,
        'public_float': fund_data['public_float'],
        'category': categorize_low_float(fund_data['public_float']),
        'insider_ownership': fund_data.get('insider_ownership', 0),
        'institutional_ownership': fund_data.get('institutional_ownership', 0),
        'total_shares': fund_data['total_shares'],
    }
    
    if hist_data is not None:
        # Analisis tambahan
        analysis['price_trend'] = "Uptrend" if hist_data['Close'].iloc[-1] > hist_data['Close'].mean() else "Downtrend"
        analysis['volume_trend'] = "High" if hist_data['Volume'].iloc[-5:].mean() > hist_data['Volume'].mean() else "Normal"
    
    return analysis
