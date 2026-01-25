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
import calendar
import datetime

warnings.filterwarnings("ignore")

# ===========================
# ⚙️ GLOBAL CONFIGURATION
# ===========================
st.set_page_config(page_title="Portfolio Tracker", layout="wide", page_icon="☕")

# ===========================
# 🎨 UI & CSS OVERHAUL (THE "LATTE" THEME)
# ===========================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* 1. GLOBAL RESET & TYPOGRAPHY */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        
        /* 2. MAIN BACKGROUND (Warm Paper) */
        .stApp {
            background-color: #F5F5F4; /* Stone-100 */
            color: #292524; /* Stone-800 */
        }

        /* 3. SIDEBAR BACKGROUND (Mocha / Dark Stone) */
        [data-testid="stSidebar"] {
            background-color: #292524; /* Stone-800 */
            border-right: 1px solid #44403C;
        }
        /* Sidebar Text Overrides */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
            color: #E7E5E4 !important; /* Stone-200 */
        }

        /* 4. TEXT COLORS & HEADINGS */
        h1, h2, h3, h4, h5, h6 {
            color: #292524 !important; /* Stone-800 */
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        p, label, .stMarkdown {
            color: #57534E !important; /* Stone-600 */
        }

        /* 5. METRIC CARDS (White + Warm Shadow) */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E7E5E4; /* Stone-200 */
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(68, 64, 60, 0.05); /* Warm shadow */
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(68, 64, 60, 0.1);
            border-color: #D6D3D1; /* Stone-300 */
        }
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #A8A29E; /* Stone-400 */
            font-weight: 600;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #292524; /* Stone-800 */
            line-height: 1.2;
        }
        .metric-delta {
            display: inline-flex;
            align-items: center;
            font-size: 0.875rem;
            font-weight: 500;
            margin-top: 8px;
            padding: 2px 8px;
            border-radius: 6px;
        }
        /* Earthy Pos/Neg Colors */
        .delta-pos { color: #15803D; background: #DCFCE7; } /* Green-700 on Green-50 */
        .delta-neg { color: #B91C1C; background: #FEE2E2; } /* Red-700 on Red-50 */
        .delta-neu { color: #57534E; background: #F5F5F4; }

        /* 6. BUTTONS (Burnt Orange) */
        .stButton > button {
            background: #EA580C; /* Orange-600 */
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            width: 100%;
        }
        .stButton > button:hover {
            background: #C2410C; /* Orange-700 */
            box-shadow: 0 4px 6px -1px rgba(234, 88, 12, 0.2);
            transform: translateY(-1px);
        }
        
        /* Download Button Variant (Sidebar - Dark Context) */
        .stDownloadButton > button {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #E7E5E4;
            border-radius: 8px;
            width: 100%;
        }
        .stDownloadButton > button:hover {
            border-color: #EA580C;
            color: #EA580C;
            background: rgba(234, 88, 12, 0.1);
        }

        /* 7. CUSTOM TABS */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #E7E5E4; /* Stone-200 */
            padding: 4px;
            border-radius: 8px;
            gap: 0px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 36px;
            border-radius: 6px;
            color: #78716C; /* Stone-500 */
            font-weight: 500;
            border: none;
            flex: 1;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF;
            color: #EA580C !important; /* Orange Active Text */
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }

        /* 8. DATAFRAME */
        [data-testid="stDataFrame"] {
            border: 1px solid #E7E5E4;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }
        
        /* 9. HEADER BADGE */
        .live-badge {
            background: #FFEDD5; /* Orange-100 */
            color: #C2410C; /* Orange-700 */
            padding: 2px 10px;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid #FED7AA;
            margin-left: 10px;
            vertical-align: middle;
            display: inline-block;
        }

        /* --- FIX: VISIBLE SIDEBAR TOGGLE --- */
        #MainMenu {visibility: hidden;} /* Hides the hamburger menu */
        footer {visibility: hidden;}    /* Hides 'Made with Streamlit' */
        /* Removed 'header {visibility: hidden;}' to keep sidebar toggle visible */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0); /* Makes header transparent */
        }
        
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
    },
    "HDFC Nifty 50 Index": {
        "file": "HDFC_Nifty50_Portfolio_2025.xlsx",
        "base_url": "https://files.hdfcfund.com/s3fs-public",
        "fund_keyword": "nifty 50 index fund" 
    }
}

# ===========================
# 🧠 SCRAPER ENGINES (Unchanged)
# ===========================
def fetch_ppfas_data(month, year):
    try:
        response = requests.get(FUND_CONFIG["PPFAS Flexi Cap"]["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        search_terms = [month[:3].lower(), str(year), "ppfcf"]
        target_url = None
        for link in links:
            full_str = (link['href'] + link.text).lower()
            if all(t in full_str for t in search_terms) and re.search(r'\.xlsx?($|\?)', link['href']):
                target_url = link['href'] if link['href'].startswith('http') else f"https://amc.ppfas.com{link['href']}"
                break
        if not target_url: return None
        resp = requests.get(target_url, headers=HEADERS, timeout=30)
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

def fetch_nippon_data(month, year):
    try:
        month_short, year_short = month[:3], str(year)[-2:]
        target_url = None
        patterns = [
            f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month_short}-{year_short}.xls",
            f"https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-{month}-{year}.xls"
        ]
        for url in patterns:
            try: 
                if requests.head(url, headers=HEADERS, timeout=3).status_code == 200: target_url = url; break
            except: continue
        if not target_url:
            resp = requests.get(FUND_CONFIG["Nippon India Small Cap"]["url"], headers=HEADERS, timeout=10)
            regex = fr'href=["\']([^"\']*(?:monthly|portfolio)[^"\']*(?:{month}|{month_short})[^"\']*(?:{year}|{year_short})[^"\']*\.xls[x]?)["\']'
            matches = re.findall(regex, resp.text, re.IGNORECASE)
            if matches:
                link = matches[0]
                target_url = FUND_CONFIG["Nippon India Small Cap"]["base_url"] + link if link.startswith("/") else link
        if not target_url: return None
        resp = requests.get(target_url, headers=HEADERS, timeout=30)
        target_sheet = FUND_CONFIG["Nippon India Small Cap"]["sheet"]
        try: df = pd.read_excel(BytesIO(resp.content), sheet_name=target_sheet, header=None, engine='openpyxl')
        except: df = pd.read_excel(BytesIO(resp.content), sheet_name=target_sheet, header=None, engine='xlrd')
        header_idx = None
        for idx, row in df.iterrows():
            if "name of the instrument" in row.astype(str).str.cat(sep=' ').lower(): header_idx = idx; break
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

def fetch_hdfc_data(month, year):
    try:
        month_num = datetime.datetime.strptime(month, "%B").month
        last_day = calendar.monthrange(year, month_num)[1]
        date_obj = datetime.date(year, month_num, 1)
        next_month = date_obj.replace(day=28) + datetime.timedelta(days=4)
        folder_path = next_month.strftime("%Y-%m")
        filename = f"Monthly HDFC Nifty 50 Index Fund - {last_day} {month} {year}.xlsx"
        url = f"{FUND_CONFIG['HDFC Nifty 50 Index']['base_url']}/{folder_path}/{filename.replace(' ', '%20')}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200: return None
        xls = pd.ExcelFile(BytesIO(resp.content))
        target_df = None
        header_row = None
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            if FUND_CONFIG['HDFC Nifty 50 Index']['fund_keyword'] in df.iloc[0:5].astype(str).to_string().lower():
                target_df = df
                for idx, row in df.iterrows():
                    r_str = row.astype(str).str.cat(sep=" ").lower()
                    if "isin" in r_str and "name" in r_str and "quantity" in r_str: header_row = idx; break
                break
        if target_df is None or header_row is None: return None
        target_df.columns = target_df.iloc[header_row]
        df = target_df.iloc[header_row+1:].copy()
        col_map = {}
        for c in df.columns:
            val = str(c).lower().strip()
            if "isin" in val: col_map[c] = "ISIN"
            elif "name" in val and "instrument" in val: col_map[c] = "Stock Name"
            elif "quantity" in val: col_map[c] = f"Qty_{month}_{year}"
        df = df.rename(columns=col_map)
        valid_rows = []
        for _, row in df.iterrows():
            isin = str(row.get("ISIN", "")).upper()
            if isin.startswith("INE"):
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
            elif fund_name == "Nippon India Small Cap": new_df = fetch_nippon_data(month, YEARS[0])
            elif fund_name == "HDFC Nifty 50 Index": new_df = fetch_hdfc_data(month, YEARS[0])
            else: new_df = None
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
    st.image("https://cdn-icons-png.flaticon.com/512/1077/1077114.png", width=42) # Generic Icon
    st.markdown("### Workspace")
    
    selected_fund = st.selectbox("Active Portfolio", list(FUND_CONFIG.keys()))
    current_file = FUND_CONFIG[selected_fund]["file"]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("↻ Sync", use_container_width=True):
            with st.spinner("Scraping..."):
                run_update(selected_fund)
                st.rerun()
    
    if os.path.exists(current_file):
        with open(current_file, "rb") as f:
            with col_sb2:
                st.download_button("↓ Export", f, file_name=current_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.markdown("---")
    
    st.markdown("### Timeline")
    available_months = []
    if os.path.exists(current_file):
        temp = pd.read_excel(current_file)
        available_months = [c.replace("Qty_", "").replace(f"_{YEARS[0]}", "") for c in temp.columns if "Qty_" in c]
    view_month = st.selectbox("Period", ["All Months"] + available_months) if available_months else "All Months"


# --- HEADER ---
st.markdown(f"""
    <div style="margin-bottom: 2rem; padding-top: 1rem;">
        <h1 style="font-size: 2rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px;">
            {selected_fund} <span class="live-badge">● Live</span>
        </h1>
        <p style="font-size: 1rem; opacity: 0.8;">Real-time portfolio disclosure tracking & analytics</p>
    </div>
""", unsafe_allow_html=True)


# --- MAIN VIEW ---
if os.path.exists(current_file):
    df = pd.read_excel(current_file)
    qty_cols = [c for c in df.columns if "Qty_" in c]
    for c in qty_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # ========================================================
    # 🧠 SMART FILTERING & METRIC CALCULATION
    # ========================================================
    
    # 1. Determine "Latest Column" (The most recent month available)
    present_qty_cols = [c for c in qty_cols if c in df.columns]
    if present_qty_cols:
        def get_month_index(col_name):
            m_name = col_name.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
            return MONTHS.index(m_name) if m_name in MONTHS else -1
        
        # Sort cols chronologically
        sorted_cols = sorted(present_qty_cols, key=get_month_index)
        latest_col = sorted_cols[-1]
    else:
        latest_col = None
        sorted_cols = []

    # 2. Logic based on Selection
    if view_month != "All Months":
        # === SINGLE MONTH VIEW ===
        # Restrict to one column, filter rows that are active in THAT month
        target_col = f"Qty_{view_month}_{YEARS[0]}"
        display_df = df[df[target_col] > 0][["Stock Name", "ISIN", target_col]].copy()
        view_cols = [target_col]
        active_holdings_count = len(display_df)
    else:
        # === ALL MONTHS VIEW ===
        # 1. Data Grid: Show ALL columns so user sees history
        view_cols = sorted_cols 
        
        # 2. Rows: Show stocks that were held at ANY point (Sum > 0)
        #    This brings back sold stocks into the grid/charts history
        if view_cols:
            mask = df[view_cols].sum(axis=1) > 0
            display_df = df[mask][["Stock Name", "ISIN"] + view_cols].copy()
        else:
            display_df = pd.DataFrame()

        # 3. METRIC: Active Holdings (Strictly Latest Month > 0)
        #    We calculate this separately from the grid view
        if latest_col:
            active_holdings_count = len(df[df[latest_col] > 0])
        else:
            active_holdings_count = 0

    # ========================================================

    # Metrics Calculation
    # Top Stock is based on the LATEST available data point for accuracy
    top_stock_name = "N/A"
    if latest_col and not df.empty:
        # Sort by latest month to find top holding
        top_series = df.sort_values(by=latest_col, ascending=False).iloc[0]
        if top_series[latest_col] > 0:
            top_stock_name = top_series['Stock Name']

    delta_pct = 0
    if len(qty_cols) >= 2 and view_month == "All Months":
        curr, prev = df[qty_cols[-1]].sum(), df[qty_cols[-2]].sum()
        delta_pct = ((curr - prev) / prev * 100) if prev > 0 else 0

    # METRIC CARDS
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Assets</div>
            <div class="metric-value">{active_holdings_count}</div>
            <div class="metric-delta delta-neu">Active Positions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Allocation</div>
            <div class="metric-value" style="font-size: 1.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{top_stock_name}</div>
            <div class="metric-delta delta-pos">Highest Weight</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        arrow = "↑" if delta_pct >= 0 else "↓"
        color_class = "delta-pos" if delta_pct >= 0 else "delta-neg"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Volume Velocity</div>
            <div class="metric-value">{abs(delta_pct):.1f}%</div>
            <div class="metric-delta {color_class}">{arrow} MoM Change</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if latest_col:
        tab1, tab2, tab3 = st.tabs(["Overview", "Data Grid", "Analytics"])

        # TAB 1: TREEMAP (Warm Gradient)
        with tab1:
            # Treemap always uses LATEST data to show current composition
            top_stocks = df[df[latest_col]>0].nlargest(30, latest_col)
            fig = px.treemap(
                top_stocks, 
                path=['Stock Name'], 
                values=latest_col,
                color=latest_col,
                color_continuous_scale='Oranges' # Warm Orange Gradient
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#57534E", # Stone-600
                margin=dict(t=0, l=0, r=0, b=0),
                coloraxis_showscale=False,
                hoverlabel=dict(bgcolor="white", bordercolor="#D6D3D1")
            )
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2: GRID (Warm Table - SHOWS HISTORY)
        with tab2:
            if "Stock Name" in display_df.columns:
                agg_dict = {col: "sum" for col in view_cols}
                if "ISIN" in display_df.columns: agg_dict["ISIN"] = "first"
                grid_df = display_df.groupby("Stock Name", as_index=False).agg(agg_dict).set_index("Stock Name")
            else: grid_df = display_df
            
            # Warm Orange gradient for the table
            st.dataframe(
                grid_df.style.background_gradient(cmap="Oranges", subset=view_cols)
                             .format("{:,.0f}", subset=view_cols),
                use_container_width=True,
                height=500
            )

        # TAB 3: TRENDS (Warm Line Chart)
        with tab3:
            c_search, _ = st.columns([1, 2])
            with c_search: 
                stock = st.selectbox("Inspect Asset", sorted(df["Stock Name"].unique().tolist()))
            
            trend_data = df[df["Stock Name"] == stock].melt(id_vars=["Stock Name"], value_vars=qty_cols, var_name="Month", value_name="Qty")
            trend_data["Month"] = trend_data["Month"].str.replace("Qty_", "").str.replace(f"_{YEARS[0]}", "")

            # Custom Warm Area Chart
            fig_area = go.Figure()
            fig_area.add_trace(go.Scatter(
                x=trend_data['Month'], 
                y=trend_data['Qty'],
                fill='tozeroy',
                mode='lines+markers',
                line=dict(color='#EA580C', width=3, shape='spline'), # Orange-600
                marker=dict(size=6, color='#EA580C', line=dict(width=2, color='white')),
                fillcolor='rgba(234, 88, 12, 0.1)' # Warm orange fill
            ))

            fig_area.update_layout(
                title=dict(text=f"{stock} Trajectory", font=dict(size=14, color="#57534E")),
                template="plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter, sans-serif", color="#57534E"),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='#E7E5E4', zeroline=False), # Light stone grid
                hovermode="x unified"
            )
            st.plotly_chart(fig_area, use_container_width=True)

else:
    # --- WELCOME SCREEN (Latte Style) ---
    st.markdown(f"""
    <div style="
        display: flex; 
        flex-direction: column; 
        align-items: center; 
        justify-content: center; 
        height: 60vh; 
        text-align: center;
        border: 1px dashed #D6D3D1;
        border-radius: 16px;
        background: #F5F5F4;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">☕</div>
        <h2 style="color: #292524; margin-bottom: 0.5rem;">Ready to Track {selected_fund}</h2>
        <p style="color: #78716C; max-width: 400px; line-height: 1.5;">
            No local data found. Initialize the database to scrape the latest disclosures and build your dashboard.
        </p>
        <br>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button(f"Initialize Database", use_container_width=True):
             with st.spinner(f"Connecting to fund registry..."):
                run_update(selected_fund)
                st.success("Sync Complete!")
                st.rerun()