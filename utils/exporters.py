import pandas as pd
from io import BytesIO
from datetime import datetime

def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    """
    Export DataFrame ke Excel - VERSI SUPER SIMPLE
    """
    try:
        # Buat buffer
        output = BytesIO()
        
        # Langsung to_excel tanpa writer ribet
        dataframe.to_excel(output, index=False, sheet_name=sheet_name, engine='openpyxl')
        
        # Kembalikan ke awal
        output.seek(0)
        
        # Balikin datanya
        return output.getvalue()
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def format_number(num):
    """Format angka"""
    try:
        return f"{num:,.0f}"
    except:
        return str(num)
