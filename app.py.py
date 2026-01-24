import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import re
from bs4 import BeautifulSoup
from io import BytesIO
import os
import warnings

warnings.filterwarnings("ignore")

# ===========================
# ⚙️ GLOBAL CONFIGURATION
# ===========================
st.set_page_config(page_title="Portfolio Tracker", layout="wide", page_icon="📈")

# ===========================
# 🎨 UI & CSS OVERHAUL (THE "CRYPTO DARK" THEME)
# ===========================
st.markdown("""
    <style>
        /* 1. MAIN BACKGROUND */
        .stApp {
            background-color: #121212;
            color: #E0E0E0;
        }

        /* 2. SIDEBAR BACKGROUND */
        [data-testid="stSidebar"] {
            background-color: #1E1E1E;
            border-right: 1px solid #333;
        }

        /* 3. TEXT COLORS & HEADINGS */
        h1, h2, h3, h4, h5, h6, p, label {
            color: #E0E0E0 !important;
            font-family: 'Inter', sans-serif;
        }
        .stMarkdown {
            color: #B0B0B0;
        }
        
        /* 4. METRIC CARDS (Custom Class) */
        .metric-card {
            background-color: #2D2D2D;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
            border: 1px solid #3E3E3E;
            text-align: center;
        }
        .metric-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF;
        }
        .metric-delta {
            font-size: 14px;
            color: #4CAF50; /* Green for profit */
            font-weight: 600;
        }
        .metric-delta.negative {
            color: #FF5252;
        }

        /* 5. BUTTONS & ACCENTS */
        .stButton > button {
            background-color: #FF6D00;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background-color: #E65100;
            box-shadow: 0 0 10px rgba(255, 109, 0, 0.5);
        }
        /* Download Button Specifics */
        .stDownloadButton > button {
            background-color: #2D2D2D;
            color: #FF6D00;
            border: 1px solid #FF6D00;
            width: 100%;
        }
        .stDownloadButton > button:hover {
            background-color: #FF6D00;
            color: white;
        }

        /* 6. TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: #888;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2D2D2D;
            color: #FF6D00 !important;
            border-bottom: 2px solid #FF6D00;
        }

        /* 7. DATAFRAME */
        [data-testid="stDataFrame"] {
            border: 1px solid #333;
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Remove standard streamlit footer/menu for cleaner look */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
YEARS = [2025]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Fund Specific Settings
FUND_CONFIG = {
    "PPFAS Flexi Cap": {
        "file": "PPFCF_Portfolio_Dashboard_2025.xlsx",
        "url": "https://amc.ppfas.com/downloads/portfolio-disclosure/",
        "sheet": None
    },
    "Nippon India Small Cap": {
        "file": "Nippon_SC_Portfolio_2025.xlsx",
        "url": "https://mf.nipponindiaim.com/investor-service/downloads/factsheet-portfolio-and-other-disclosures",
        "base_url": "https://mf.nipponindiaim.com",
        "sheet": "SC"
    }
}

# ===========================
# 🧠 SCRAPER ENGINES (Logic Preserved)
# ===========================
def get_ppfas_url(month, year):
    try:
        response = requests.get(FUND_CONFIG["PPFAS Flexi Cap"]["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        search_terms = [month[:3].lower(), str(year), "ppfcf"]
        for link in links:
            full_str = (link['href'] + link.text).lower()
            if all(t in full_str for t in search_terms) and re.search(r'\.xlsx?($|\?)', link['href']):
                return link['href'] if link['href'].startswith('http') else f"https://amc.ppfas.com{link['href']}"
    except: pass
    return None

def fetch_ppfas_data(month, year):
    url = get_ppfas_url(month, year)
    if not url: return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        try: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='openpyxl')
        except: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='xlrd')
        
        full_df = pd.concat(all_sheets.values(), ignore_index=True)
        valid_holdings = []
        for idx, row in full_df.iterrows():
            row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
            row_str = " ".join(row_vals).lower()
            if "arbitrage" in row_str or "grand total" in row_str:
                if valid_holdings: break
            isin_match = re.search(r'\b(ine|inf)[a-z0-9]{9}\b', row_str)
            if isin_match:
                isin = isin_match.group(0)
                name = next((s for s in row_vals if len(s) > 4 and s != isin and not re.search(r'\d', s)), "Unknown")
                qty = next((float(v.replace(",","")) for v in row_vals if v.replace(",","").replace(".","").isdigit() and float(v.replace(",","")) > 0), 0)
                if qty > 0: valid_holdings.append({"Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty})
        if not valid_holdings: return None
        return pd.DataFrame(valid_holdings).groupby("ISIN", as_index=False).agg({"Stock Name": "first", f"Qty_{month}_{year}": "sum"})
    except: return None

def get_nippon_url(month, year):
    month_short = month[:3]
    year_short = str(year)[-2:]
    direct_patterns = [
        f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month_short}-{year_short}.xls",
        f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month}-{year}.xls"
    ]
    for url in direct_patterns:
        try: 
            if requests.head(url, headers=HEADERS, timeout=3).status_code == 200: return url
        except: continue
    try:
        resp = requests.get(FUND_CONFIG["Nippon India Small Cap"]["url"], headers=HEADERS, timeout=10)
        regex = fr'href=["\']([^"\']*(?:monthly|portfolio)[^"\']*(?:{month}|{month_short})[^"\']*(?:{year}|{year_short})[^"\']*\.xls[x]?)["\']'
        matches = re.findall(regex, resp.text, re.IGNORECASE)
        if matches:
            link = matches[0]
            return FUND_CONFIG["Nippon India Small Cap"]["base_url"] + link if link.startswith("/") else link
    except: pass
    return None

def fetch_nippon_data(month, year):
    url = get_nippon_url(month, year)
    if not url: return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        target_sheet = FUND_CONFIG["Nippon India Small Cap"]["sheet"]
        try: df = pd.read_excel(BytesIO(resp.content), sheet_name=target_sheet, header=None, engine='openpyxl')
        except: df = pd.read_excel(BytesIO(resp.content), sheet_name=target_sheet, header=None, engine='xlrd')

        header_idx = None
        for idx, row in df.iterrows():
            if "name of the instrument" in row.astype(str).str.cat(sep=' ').lower():
                header_idx = idx; break
        if header_idx is None: return None

        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx+1:].copy()
        col_map = {c: "Stock Name" if "name of the instrument" in str(c).lower() else "ISIN" if "isin" in str(c).lower() else f"Qty_{month}_{year}" if "quantity" in str(c).lower() else c for c in df.columns}
        df = df.rename(columns=col_map)
        
        valid_rows = []
        for _, row in df.iterrows():
            isin = str(row.get("ISIN", "")).upper()
            if isin.startswith("INE") and "total" not in str(row.get("Stock Name", "")).lower():
                try:
                    qty = float(str(row.get(f"Qty_{month}_{year}", 0)).replace(",", ""))
                    if qty > 0: valid_rows.append({"Stock Name": row["Stock Name"], "ISIN": isin, f"Qty_{month}_{year}": qty})
                except: continue
        return pd.DataFrame(valid_rows)
    except: return None

def run_update(fund_name):
    config = FUND_CONFIG[fund_name]
    output_file = config["file"]
    status = st.empty()
    bar = st.progress(0)
    
    if os.path.exists(output_file):
        master_df = pd.read_excel(output_file)
        master_df["ISIN"] = master_df["ISIN"].astype(str).str.strip()
    else:
        master_df = pd.DataFrame(columns=["ISIN", "Stock Name"])

    for i, month in enumerate(MONTHS):
        col_name = f"Qty_{month}_{YEARS[0]}"
        if col_name not in master_df.columns:
            status.text(f"📥 Fetching {month} for {fund_name}...")
            if fund_name == "PPFAS Flexi Cap": new_df = fetch_ppfas_data(month, YEARS[0])
            else: new_df = fetch_nippon_data(month, YEARS[0])
            
            if new_df is not None:
                new_df["ISIN"] = new_df["ISIN"].astype(str).str.strip()
                master_df = pd.merge(master_df, new_df, on="ISIN", how="outer", suffixes=("", "_new"))
                if "Stock Name_new" in master_df.columns:
                    master_df["Stock Name"] = master_df["Stock Name"].fillna(master_df["Stock Name_new"])
                    master_df.drop(columns=["Stock Name_new"], inplace=True)
                if f"{col_name}_new" in master_df.columns:
                    master_df[col_name] = master_df[f"{col_name}_new"]
                    master_df.drop(columns=[f"{col_name}_new"], inplace=True)
        bar.progress((i + 1) / len(MONTHS))
    
    master_df.to_excel(output_file, index=False)
    status.text("✅ Update Complete!")
    return master_df

# ===========================
# 🖥️ DASHBOARD UI
# ===========================

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    selected_fund = st.selectbox("Fund Source", list(FUND_CONFIG.keys()))
    current_file = FUND_CONFIG[selected_fund]["file"]
    
    st.divider()
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("↻ Sync", use_container_width=True):
            with st.spinner("Scraping..."):
                run_update(selected_fund)
                st.rerun()
    
    if os.path.exists(current_file):
        with open(current_file, "rb") as f:
            with col_sb2:
                st.download_button("⬇ Save", f, file_name=current_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.divider()
    
    available_months = []
    if os.path.exists(current_file):
        temp = pd.read_excel(current_file)
        available_months = [c.replace("Qty_", "").replace(f"_{YEARS[0]}", "") for c in temp.columns if "Qty_" in c]
    view_month = st.selectbox("📅 Filter View", ["All Months"] + available_months) if available_months else "All Months"


# --- HEADER ---
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <div>
            <h1 style="color: #FF6D00; margin: 0;">🔥 {selected_fund}</h1>
            <p style="color: #888; margin: 0;">Advanced Portfolio Analytics Dashboard</p>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- MAIN VIEW ---
if os.path.exists(current_file):
    df = pd.read_excel(current_file)
    qty_cols = [c for c in df.columns if "Qty_" in c]
    for c in qty_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if view_month != "All Months":
        target_col = f"Qty_{view_month}_{YEARS[0]}"
        display_df = df[df[target_col] > 0][["Stock Name", "ISIN", target_col]].copy()
        view_cols = [target_col]
        latest_col = target_col
    else:
        display_df = df.copy()
        view_cols = qty_cols
        latest_col = qty_cols[-1] if qty_cols else None

    # --- METRIC CARDS ---
    # Prepare Data
    total_holdings = len(display_df)
    
    if not display_df.empty and latest_col:
        top_stock_row = display_df.sort_values(by=latest_col, ascending=False).iloc[0]
        top_stock_name = top_stock_row['Stock Name']
        top_stock_qty = top_stock_row[latest_col]
    else:
        top_stock_name = "N/A"
        top_stock_qty = 0

    # Calculate MoM Change (Aggregate)
    if len(qty_cols) >= 2 and view_month == "All Months":
        curr_total = df[qty_cols[-1]].sum()
        prev_total = df[qty_cols[-2]].sum()
        delta_pct = ((curr_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
    else:
        delta_pct = 0

    # Display Cards
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Holdings</div>
            <div class="metric-value">{total_holdings}</div>
            <div class="metric-delta">Stocks Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Allocation</div>
            <div class="metric-value" style="font-size: 24px;">{top_stock_name[:15]}..</div>
            <div class="metric-delta">{top_stock_qty:,.0f} Units</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        color_class = "negative" if delta_pct < 0 else ""
        arrow = "▼" if delta_pct < 0 else "▲"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Portfolio Momentum</div>
            <div class="metric-value">{abs(delta_pct):.1f}%</div>
            <div class="metric-delta {color_class}">{arrow} MoM Change</div>
        </div>
        """, unsafe_allow_html=True)

    # --- TABS ---
    if latest_col:
        st.markdown("### 📊 Market Analysis")
        tab1, tab2, tab3 = st.tabs(["Holdings Map", "Data Grid", "Trend Scanner"])

        # TAB 1: TREEMAP (Dark Mode)
        with tab1:
            top_stocks = display_df.nlargest(30, latest_col)
            fig = px.treemap(
                top_stocks, 
                path=['Stock Name'], 
                values=latest_col,
                color=latest_col,
                color_continuous_scale='Tealgrn' # Looks good on dark
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#E0E0E0",
                margin=dict(t=20, l=0, r=0, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2: GRID (Dark Mode)
        with tab2:
            if "Stock Name" in display_df.columns:
                agg_dict = {col: "sum" for col in view_cols}
                if "ISIN" in display_df.columns: agg_dict["ISIN"] = "first"
                grid_df = display_df.groupby("Stock Name", as_index=False).agg(agg_dict).set_index("Stock Name")
            else:
                grid_df = display_df

            # Apply orange gradient
            st.dataframe(
                grid_df.style.background_gradient(cmap="Oranges", subset=view_cols)
                             .format("{:,.0f}", subset=view_cols),
                use_container_width=True,
                height=500
            )

        # TAB 3: GLOWING CHART
        with tab3:
            col_search, _ = st.columns([1, 2])
            with col_search:
                stock_list = sorted(df["Stock Name"].unique().tolist())
                stock = st.selectbox("Select Asset", stock_list)

            trend_data = df[df["Stock Name"] == stock].melt(
                id_vars=["Stock Name"], value_vars=qty_cols, var_name="Month", value_name="Qty"
            )
            trend_data["Month"] = trend_data["Month"].str.replace("Qty_", "").str.replace(f"_{YEARS[0]}", "")

            # Custom Plotly Graph Object for Glow Effect
            fig_area = go.Figure()
            fig_area.add_trace(go.Scatter(
                x=trend_data['Month'], 
                y=trend_data['Qty'],
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color='#FF6D00', width=3), # Orange Line
                marker=dict(size=8, color='#FF6D00', line=dict(width=2, color='white')),
                fillcolor='rgba(255, 109, 0, 0.2)' # Semi-transparent Fill
            ))

            fig_area.update_layout(
                title=f"Asset Trajectory: {stock}",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#E0E0E0"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#333'),
                hovermode="x unified"
            )
            st.plotly_chart(fig_area, use_container_width=True)

else:
    # --- WELCOME SCREEN (Dark Mode) ---
    st.markdown(f"""
    <div style="text-align: center; padding: 100px; color: #666;">
        <h1 style="color: #444;">No Data Initialized</h1>
        <p>You have selected <b>{selected_fund}</b>.</p>
        <p>Click <b>Sync</b> in the sidebar to scrape the latest disclosures.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button(f"🚀 Initialize Data for {selected_fund}", use_container_width=True):
             with st.spinner(f"Scraping {selected_fund} website... This may take a minute."):
                run_update(selected_fund)
                st.success("Initialization Complete! Reloading...")
                st.rerun()