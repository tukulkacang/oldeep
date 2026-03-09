import pandas as pd
from io import BytesIO
from datetime import datetime

def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    """
    Export DataFrame ke Excel
    """
    try:
        # Buat buffer untuk menyimpan file Excel
        output = BytesIO()
        
        # Buat Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Kembalikan ke awal buffer
        output.seek(0)
        
        return output.getvalue()
    
    except Exception as e:
        print(f"Error export Excel: {e}")
        return None

def format_number(num):
    """Format angka untuk display"""
    try:
        if num >= 1e9:
            return f"{num/1e9:.2f} B"
        elif num >= 1e6:
            return f"{num/1e6:.2f} M"
        elif num >= 1e3:
            return f"{num/1e3:.2f} K"
        else:
            return str(num)
    except:
        return str(num)
