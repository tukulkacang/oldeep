import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.data_fetcher import DataFetcher
from modules.scanner_open_low import OpenLowScanner
from modules.scanner_low_float import LowFloatScanner
from modules.ai_analyzer import AIAnalyzer
from modules.exporter import ReportExporter
from idx_stocks import IDX_STOCKS, LIQUID_STOCKS

# Page configuration
st.set_page_config(
    page_title="IDX Pro Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .scanner-button {
        background-color: #ff4b4b;
        color: white;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scan_results_open_low' not in st.session_state:
    st.session_state.scan_results_open_low = None
if 'scan_results_low_float' not in st.session_state:
    st.session_state.scan_results_low_float = None
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# Header
st.markdown('<h1 class="main-header">📈 IDX Pro Scanner</h1>', unsafe_allow_html=True)
st.markdown("### Advanced Indonesian Stock Analysis Tool")

# Initialize components
data_fetcher = DataFetcher()
open_low_scanner = OpenLowScanner(data_fetcher)
low_float_scanner = LowFloatScanner(data_fetcher)
exporter = ReportExporter()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Universe selection
    universe = st.selectbox(
        "Stock Universe",
        ["All IDX Stocks (800+)", "Liquid Stocks Only (LQ45)", "Custom Selection"]
    )
    
    if universe == "All IDX Stocks (800+)":
        stock_list = IDX_STOCKS
    elif universe == "Liquid Stocks Only (LQ45)":
        stock_list = LIQUID_STOCKS
    else:
        selected = st.multiselect("Select Stocks", IDX_STOCKS, default=["BBCA", "BBRI", "TLKM"])
        stock_list = selected
    
    st.markdown("---")
    st.info("💡 **Tips:**\n- Open=Low Scanner: Cari saham dengan pola reversal kuat\n- Low Float: Cari saham volatile dengan supply terbatas")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["🔥 Open = Low Scanner", "🎯 Low Float Scanner", "🤖 AI Analysis"])

# ==================== TAB 1: OPEN = LOW SCANNER ====================
with tab1:
    st.header("Scanner A: Open = Low + Momentum Pattern")
    st.markdown("""
    **Mendeteksi saham dengan pola:**
    - Open = Low (harga pembukaan = harga terendah)
    - Kenaikan dari Open ke High ≥ threshold%
    - Analisis frekuensi historis
    """)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        period = st.selectbox(
            "Analysis Period",
            ["1mo", "3mo", "6mo", "1y"],
            index=1
        )
    
    with col2:
        min_gain = st.slider("Min Gain %", 3, 15, 5, help="Minimal kenaikan dari Open ke High")
    
    with col3:
        tolerance = st.slider("Open=Low Tolerance %", 0.0, 1.0, 0.1, step=0.1) / 100
    
    with col4:
        top_n = st.number_input("Top Results", 10, 100, 20)
    
    # Scan Button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        scan_button = st.button("🚀 RUN OPEN=LOW SCAN", use_container_width=True, type="primary")
    
    if scan_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress, ticker):
            progress_bar.progress(progress, f"Scanning {ticker}...")
        
        with st.spinner(f"Scanning {len(stock_list)} stocks... This may take a while"):
            results = open_low_scanner.scan_batch(
                stock_list, 
                period=period, 
                min_gain_percent=min_gain,
                top_n=top_n,
                progress_callback=update_progress
            )
            
            st.session_state.scan_results_open_low = results
        
        progress_bar.empty()
        status_text.empty()
    
    # Display Results
    if st.session_state.scan_results_open_low is not None:
        results = st.session_state.scan_results_open_low
        
        if not results.empty:
            # Metrics
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total Pattern Found", int(results['pattern_count'].sum()))
            with col_m2:
                st.metric("Best Frequency", f"{results['frequency_pct'].iloc[0]}%")
            with col_m3:
                st.metric("Best Avg Gain", f"{results['avg_gain_when_pattern'].iloc[0]}%")
            with col_m4:
                st.metric("Top Stock", results['ticker'].iloc[0])
            
            # Charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                fig = px.bar(
                    results.head(10),
                    x='ticker',
                    y='frequency_pct',
                    title='Top 10 - Pattern Frequency (%)',
                    color='frequency_pct',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_chart2:
                fig = px.scatter(
                    results,
                    x='frequency_pct',
                    y='avg_gain_when_pattern',
                    size='pattern_count',
                    color='score',
                    hover_data=['ticker'],
                    title='Frequency vs Average Gain',
                    color_continuous_scale='Plasma'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Data Table
            st.subheader("📊 Detailed Results")
            
            # Format dataframe
            display_df = results[['ticker', 'pattern_count', 'frequency_pct', 'avg_gain_when_pattern', 
                                 'max_gain', 'last_pattern_date', 'score']].copy()
            display_df.columns = ['Ticker', 'Pattern Count', 'Frequency %', 'Avg Gain %', 
                                 'Max Gain %', 'Last Pattern', 'Score']
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Export Options
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                pdf_bytes = exporter.export_open_low_to_pdf(results, period, min_gain)
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"open_low_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col_exp2:
                excel_bytes = exporter.export_to_excel(df_open_low=display_df)
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_bytes,
                    file_name=f"open_low_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # Deep Analysis for selected stock
            st.markdown("---")
            st.subheader("🔍 Deep Analysis")
            
            selected = st.selectbox("Select stock for detailed analysis", results['ticker'].tolist())
            
            if selected:
                with st.spinner("Analyzing..."):
                    # Get detailed analysis
                    detailed = open_low_scanner.get_pattern_analysis(selected, period="1y")
                    
                    col_d1, col_d2 = st.columns(2)
                    
                    with col_d1:
                        st.markdown("**Day of Week Analysis**")
                        if 'day_of_week_stats' in detailed:
                            dow_df = detailed['day_of_week_stats']
                            fig = px.bar(dow_df, x='day', y='frequency', title='Pattern Frequency by Day')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col_d2:
                        st.markdown("**Volume Analysis**")
                        if 'volume_analysis' in detailed:
                            vol_data = detailed['volume_analysis']
                            st.json(vol_data)
                    
                    # AI Prediction
                    st.markdown("**🤖 AI Prediction for Next Day**")
                    df_stock = data_fetcher.get_stock_data(selected, period="1y")
                    
                    if df_stock is not None:
                        # Add pattern columns
                        df_stock['Open_Low_Diff'] = abs(df_stock['Open'] - df_stock['Low']) / df_stock['Open']
                        df_stock['Is_Open_Equal_Low'] = df_stock['Open_Low_Diff'] <= tolerance
                        df_stock['Gain_From_Open'] = (df_stock['High'] - df_stock['Open']) / df_stock['Open'] * 100
                        df_stock['Is_Strong_Mover'] = df_stock['Gain_From_Open'] >= min_gain
                        df_stock['Pattern_Match'] = df_stock['Is_Open_Equal_Low'] & df_stock['Is_Strong_Mover']
                        
                        ai = AIAnalyzer()
                        train_result = ai.train_models(df_stock, selected)
                        
                        if train_result:
                            st.info(f"Model Accuracy: {train_result['accuracy']*100:.1f}%")
                            prediction = ai.predict_next_day(df_stock)
                            
                            if prediction:
                                col_p1, col_p2, col_p3 = st.columns(3)
                                with col_p1:
                                    st.metric("Pattern Probability", f"{prediction['pattern_probability']}%")
                                with col_p2:
                                    st.metric("Predicted Gain", f"{prediction['predicted_gain']}%")
                                with col_p3:
                                    st.metric("Confidence", prediction['confidence'])
                        else:
                            st.warning("Insufficient data for AI prediction")
        else:
            st.warning("No patterns found with current criteria. Try adjusting the parameters.")

# ==================== TAB 2: LOW FLOAT SCANNER ====================
with tab2:
    st.header("Scanner B: Low Float Stocks")
    st.markdown("""
    **Mendeteksi saham dengan:**
    - Free float rendah (< 25%)
    - Supply terbatas = potensi volatilitas tinggi
    - Analisis kepemilikan dan estimasi risiko
    """)
    
    col_f1, col_f2 = st.columns([1, 3])
    
    with col_f1:
        max_float = st.slider("Max Free Float %", 5, 40, 25)
        run_float_scan = st.button("🎯 SCAN LOW FLOAT", use_container_width=True, type="primary")
    
    if run_float_scan:
        with st.spinner("Scanning low float stocks..."):
            float_results = low_float_scanner.scan_low_float(min_float_pct=max_float)
            st.session_state.scan_results_low_float = float_results
    
    if st.session_state.scan_results_low_float is not None:
        float_df = st.session_state.scan_results_low_float
        
        if not float_df.empty:
            # Summary metrics
            col_fm1, col_fm2, col_fm3 = st.columns(3)
            with col_fm1:
                very_low = len(float_df[float_df['category'] == 'Very Low'])
                st.metric("Very Low Float (<15%)", very_low)
            with col_fm2:
                low = len(float_df[float_df['category'] == 'Low'])
                st.metric("Low Float (15-25%)", low)
            with col_fm3:
                avg_vol = float_df['volatility_score'].mean()
                st.metric("Avg Volatility", f"{avg_vol:.1f}%")
            
            # Visualization
           
