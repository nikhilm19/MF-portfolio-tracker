import streamlit as st
import pandas as pd
import plotly.express as px
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
st.set_page_config(page_title="Mutual Fund Portfolio Tracker", layout="wide", page_icon="📈")

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
# 🧠 SCRAPER ENGINES (Backend)
# ===========================
# ... [Keep your existing get_ppfas_url, fetch_ppfas_data, get_nippon_url, fetch_nippon_data functions exactly as they were] ...

# (Paste the Scraper Engine functions here from the previous code)
# For brevity, I am assuming you have the fetch functions defined above.
# If you need them repeated, just let me know, but they haven't changed! 
# ...

# --- Re-including Scraper Logic for completeness to avoid errors ---
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
    print(f"PPFAS URL for {month} {year}: {url}")
    if not url: return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        try: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='openpyxl')
        except: all_sheets = pd.read_excel(BytesIO(resp.content), header=None, sheet_name=None, engine='xlrd')
        
        full_df = pd.concat(all_sheets.values(), ignore_index=True)
        valid_holdings = []
        #print(full_df.head(20))
        for idx, row in full_df.iterrows():
            row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
            row_str = " ".join(row_vals).lower()
            print(f"Processing row {idx}: {row_str}")
            if "arbitrage" in row_str or "grand total" in row_str:
                if valid_holdings: break
            isin_match = re.search(r'\b(ine|inf)[a-z0-9]{9}\b', row_str)
            if isin_match:
                print(f"Found ISIN: {isin_match.group(0)}")
                isin = isin_match.group(0)
                name = next((s for s in row_vals if len(s) > 4 and s != isin and not re.search(r'\d', s)), "Unknown")
                qty = next((float(v.replace(",","")) for v in row_vals if v.replace(",","").replace(".","").isdigit() and float(v.replace(",","")) > 0), 0)
                if qty > 0: valid_holdings.append({"Stock Name": name, "ISIN": isin, f"Qty_{month}_{year}": qty})
        print(f"Valid holdings found: {valid_holdings}")
        if not valid_holdings: return None
        print(f"Fetched {len(valid_holdings)} holdings for {month} {year} from PPFAS.")
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

# ===========================
# 🔄 UNIFIED UPDATE MANAGER
# ===========================
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
st.title("📊 Mutual Fund Portfolio Tracker")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    selected_fund = st.selectbox("Select Fund", list(FUND_CONFIG.keys()))
    current_file = FUND_CONFIG[selected_fund]["file"]
    print(current_file)
    
    st.divider()
    if st.button(f"🔄 Check New Data"):
        with st.spinner(f"Scraping {selected_fund}..."):
            run_update(selected_fund)
            st.success("Sync Complete!")
            st.rerun()

    # DOWNLOAD BUTTON
    if os.path.exists(current_file):
        with open(current_file, "rb") as f:
            st.download_button(
                label=f"📥 Download {selected_fund} Excel",
                data=f,
                file_name=current_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.divider()
    available_months = []
    if os.path.exists(current_file):
        temp = pd.read_excel(current_file)
        available_months = [c.replace("Qty_", "").replace(f"_{YEARS[0]}", "") for c in temp.columns if "Qty_" in c]
    view_month = st.selectbox("📅 Month Filter", ["All Months"] + available_months) if available_months else "All Months"

# --- MAIN VIEW ---
if os.path.exists(current_file):
    print("Loading data from existing file.")
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

    # Top KPI
    col_kpi1, col_kpi2 = st.columns(2)
    col_kpi1.metric(f"Active Stocks ({view_month})", len(display_df))
    col_kpi2.metric("Fund", selected_fund)

    if latest_col:
        tab1, tab2, tab3 = st.tabs(["🌳 Holdings Treemap", "🔥 Data Grid", "📈 Trends & Analysis"])

        with tab1:
            st.subheader(f"Portfolio Composition: {view_month}")
            top_stocks = display_df.nlargest(25, latest_col)
            fig = px.treemap(
                top_stocks, 
                path=['Stock Name'], 
                values=latest_col,
                color=latest_col,
                color_continuous_scale='Mint',
                title=f"Top 25 Holdings by Quantity ({view_month})"
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Holdings Grid")
            st.caption("Tip: Stocks are grouped by name to prevent duplicates.")
            if "Stock Name" in display_df.columns:
                agg_dict = {col: "sum" for col in view_cols}
                if "ISIN" in display_df.columns: agg_dict["ISIN"] = "first"
                grid_df = display_df.groupby("Stock Name", as_index=False).agg(agg_dict).set_index("Stock Name")
            else:
                grid_df = display_df

            st.dataframe(
                grid_df.style.background_gradient(cmap="Greens", subset=view_cols)
                             .format("{:,.0f}", subset=view_cols),
                use_container_width=True,
                height=600
            )

        with tab3:
            st.subheader("Historical Trend Search")
            stock_list = sorted(df["Stock Name"].unique().tolist())
            stock = st.selectbox("Search Stock", stock_list)
            trend_data = df[df["Stock Name"] == stock].melt(
                id_vars=["Stock Name"], value_vars=qty_cols, var_name="Month", value_name="Qty"
            )
            trend_data["Month"] = trend_data["Month"].str.replace("Qty_", "").str.replace(f"_{YEARS[0]}", "")
            
            if len(trend_data) >= 2:
                curr_qty = trend_data.iloc[-1]['Qty']
                prev_qty = trend_data.iloc[-2]['Qty']
                delta = curr_qty - prev_qty
                delta_pct = (delta / prev_qty * 100) if prev_qty > 0 else 0
            else:
                curr_qty = trend_data.iloc[-1]['Qty']
                delta = 0
                delta_pct = 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Current Quantity", f"{curr_qty:,.0f}", f"{delta:,.0f} ({delta_pct:.1f}%)")
            m2.metric("Highest Holding", f"{trend_data['Qty'].max():,.0f}")
            m3.metric("Months Held", len(trend_data[trend_data['Qty'] > 0]))

            fig_area = px.area(
                trend_data, x="Month", y="Qty", 
                title=f"Holding Pattern: {stock}",
                markers=True,
                color_discrete_sequence=["#2ca02c"]
            )
            fig_area.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
            st.plotly_chart(fig_area, use_container_width=True)
else:
    # === NEW: WELCOME SCREEN (When file is missing) ===
    print("Displaying welcome screen for missing data file.")
    st.container().markdown(f"""
    <div style="text-align: center; padding: 50px;">
        <h1>Welcome to Portfolio Tracker 📊</h1>
        <p>You have selected <b>{selected_fund}</b>.</p>
        <p>No local data found. Please initialize the database by scraping the latest disclosures.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button(f"🚀 Initialize Data for {selected_fund}", use_container_width=True):
             with st.spinner(f"Scraping {selected_fund} website... This may take a minute."):
                run_update(selected_fund)
                st.success("Initialization Complete! Reloading...")
                st.rerun()