import pandas as pd
from io import BytesIO
from datetime import datetime

def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    """
    Export DataFrame ke Excel
    """
    try:
        # Buat file Excel di memory
        output = BytesIO()
        
        # Simpan dataframe ke Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Kembali ke awal file
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Error di export_to_excel: {e}")
        return None

def format_number(num):
    """Format angka biar enak dibaca"""
    try:
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        else:
            return str(num)
    except:
        return str(num)
