import pandas as pd
import io
from typing import Dict, List, Union, Optional
import base64

def format_number(value: Union[int, float], decimal_places: int = 2) -> str:
    """Format angka dengan separator ribuan"""
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{value:,.{decimal_places}f}".replace(",", ".")
    except:
        return str(value)

def export_to_excel(
    data_dict: Dict[str, pd.DataFrame], 
    filename: str = "screener_results.xlsx"
) -> bytes:
    """
    Export multiple DataFrames ke Excel dengan multiple sheets.
    
    Args:
        data_dict: Dictionary dengan key=nama sheet, value=DataFrame
        filename: Nama file (untuk reference saja)
    
    Returns:
        bytes: Excel file dalam bentuk bytes untuk download
    """
    # Gunakan BytesIO untuk menyimpan file di memory (wajib untuk Streamlit)
    output = io.BytesIO()
    
    try:
        # Gunakan engine xlsxwriter (lebih stabil untuk Streamlit)
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, df in data_dict.items():
                # Bersihkan nama sheet (Excel limit 31 chars, no special chars)
                clean_sheet_name = str(sheet_name)[:31].replace('/', '-').replace('\\', '-')
                
                # Write DataFrame ke sheet
                df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets[clean_sheet_name]
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    # Limit width max 50
                    worksheet.set_column(i, i, min(max_len, 50))
        
        # Get value dan reset pointer
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        # Fallback ke openpyxl kalau xlsxwriter error
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                    clean_sheet_name = str(sheet_name)[:31].replace('/', '-').replace('\\', '-')
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
            
            output.seek(0)
            return output.getvalue()
        except Exception as e2:
            raise Exception(f"Export Excel gagal: xlsxwriter error: {e}, openpyxl error: {e2}")

def export_single_df_to_excel(df: pd.DataFrame, filename: str = "data.xlsx") -> bytes:
    """
    Export single DataFrame ke Excel
    """
    return export_to_excel({"Data": df}, filename)

def get_excel_download_link(
    df: pd.DataFrame, 
    filename: str = "data.xlsx", 
    link_text: str = "📥 Download Excel"
) -> str:
    """
    Generate HTML download link untuk Excel (alternative ke download_button)
    """
    val = export_to_excel({"Data": df}, filename)
    b64 = base64.b64encode(val).decode()
    
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" style="text-decoration: none; background-color: #1f77b4; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block;">{link_text}</a>'
