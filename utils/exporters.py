import pandas as pd
from io import BytesIO
from datetime import datetime

def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    """
    Export DataFrame ke Excel - VERSI XLSXWRITER (PALING STABIL)
    """
    try:
        # Buat buffer
        output = BytesIO()
        
        # Pake engine xlsxwriter (lebih stabil dari openpyxl untuk download)
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Tulis dataframe ke Excel
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Ambil workbook dan worksheet untuk formatting (optional)
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-width kolom biar rapi
            for i, col in enumerate(dataframe.columns):
                column_width = max(dataframe[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        # Kembali ke awal buffer
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        print(f"Error di export_to_excel: {e}")
        # Fallback ke CSV kalo Excel gagal
        try:
            output = BytesIO()
            dataframe.to_csv(output, index=False)
            output.seek(0)
            return output.getvalue()
        except:
            return None

def export_to_csv(dataframe):
    """Export ke CSV (opsional)"""
    try:
        output = BytesIO()
        dataframe.to_csv(output, index=False)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        print(f"Error di export_to_csv: {e}")
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
