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
        return str(num)            output.seek(0)
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
