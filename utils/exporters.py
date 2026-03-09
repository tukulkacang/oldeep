import pandas as pd
from io import BytesIO

def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    """
    Export DataFrame ke Excel - VERSI PALING SIMPLE
    """
    try:
        # Buat file Excel di memory
        output = BytesIO()
        
        # Simpan dataframe ke Excel
        dataframe.to_excel(output, index=False, engine='openpyxl')
        
        # Kembali ke awal file
        output.seek(0)
        
        # Langsung return
        return output.getvalue()
        
    except Exception as e:
        print(f"ERROR: {e}")
        # Return None kalo gagal
        return None

def format_number(num):
    """Format angka"""
    try:
        return f"{num:,.0f}"
    except:
        return str(num)
