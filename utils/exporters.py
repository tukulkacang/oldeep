import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# HAPUS baris import yang bermasalah
# from modules.data_fetcher import get_stock_data, get_news_sentiment

class ExcelExporter:
    """Class untuk export ke Excel"""
    
    @staticmethod
    def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
        """Export DataFrame ke Excel dengan formatting"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Styling
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            
            # Apply header styling
            for col in range(1, len(dataframe.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
            
            # Auto-adjust column widths
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column].width = adjusted_width
            
            # Add border
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            for row in worksheet.iter_rows(min_row=1, max_row=len(dataframe) + 1, min_col=1, max_col=len(dataframe.columns)):
                for cell in row:
                    cell.border = thin_border
        
        output.seek(0)
        return output.getvalue()

# Fungsi export_to_pdf sederhana (kalau mau pake nanti)
def export_to_pdf(dataframe, title="Hasil Scanning", summary=None):
    """Placeholder untuk export PDF"""
    return b"PDF export sedang dalam pengembangan"

def format_number(num):
    """Format angka untuk display"""
    if num >= 1e9:
        return f"{num/1e9:.2f} B"
    elif num >= 1e6:
        return f"{num/1e6:.2f} M"
    elif num >= 1e3:
        return f"{num/1e3:.2f} K"
    else:
        return str(num)

# Wrapper function
def export_to_excel(dataframe, sheet_name="Hasil Scanning"):
    exporter = ExcelExporter()
    return exporter.export_to_excel(dataframe, sheet_name)
