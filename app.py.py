# app.py
import streamlit as st
import pandas as pd
import os
import warnings
from config import FUND_CONFIG, YEARS, MONTHS
import scrapers
import ui

warnings.filterwarnings("ignore")

# 1. Setup
st.set_page_config(page_title="Portfolio Tracker", layout="wide", page_icon="☕")
ui.apply_latte_theme()

# 2. Logic Controller
def run_update_process(fund_name):
    """Orchestrates scraping and excel merging"""
    conf = FUND_CONFIG[fund_name]
    output_file = conf["file"]
    status = st.empty()
    bar = st.progress(0)
    
    # Load or Create Master
    if os.path.exists(output_file):
        master_df = pd.read_excel(output_file)
        master_df["ISIN"] = master_df["ISIN"].astype(str).str.strip()
    else:
        master_df = pd.DataFrame(columns=["ISIN", "Stock Name"])

    # Loop Months
    for i, month in enumerate(MONTHS):
        col_name = f"Qty_{month}_{YEARS[0]}"
        if col_name not in master_df.columns:
            status.text(f"📥 Fetching {month} for {fund_name}...")
            
            # Select Scraper
            new_df = None
            if fund_name == "PPFAS Flexi Cap": new_df = scrapers.fetch_ppfas(month, YEARS[0])
            elif fund_name == "Nippon India Small Cap": new_df = scrapers.fetch_nippon(month, YEARS[0])
            elif fund_name == "HDFC Nifty 50 Index": new_df = scrapers.fetch_hdfc(month, YEARS[0])
            
            # Merge Logic
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

# 3. UI Layout
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1077/1077114.png", width=42)
    st.markdown("### Workspace")
    selected_fund = st.selectbox("Active Portfolio", list(FUND_CONFIG.keys()))
    current_file = FUND_CONFIG[selected_fund]["file"]
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("↻ Sync"):
            with st.spinner("Scraping..."):
                run_update_process(selected_fund)
                st.rerun()
    if os.path.exists(current_file):
        with open(current_file, "rb") as f:
            c2.download_button("↓ Export", f, file_name=current_file)

    st.markdown("---")
    st.markdown("### Timeline")
    
    available_months = []
    if os.path.exists(current_file):
        temp = pd.read_excel(current_file)
        available_months = [c.replace("Qty_", "").replace(f"_{YEARS[0]}", "") for c in temp.columns if "Qty_" in c]
    view_month = st.selectbox("Period", ["All Months"] + available_months) if available_months else "All Months"

# 4. Main View
st.markdown(f"""<div style="margin-bottom: 2rem; padding-top: 1rem;"><h1 style="font-size: 2rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px;">{selected_fund} <span class="live-badge">● Live</span></h1><p style="font-size: 1rem; opacity: 0.8;">Real-time portfolio disclosure tracking & analytics</p></div>""", unsafe_allow_html=True)

if os.path.exists(current_file):
    df = pd.read_excel(current_file)
    qty_cols = [c for c in df.columns if "Qty_" in c]
    for c in qty_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Filtering Logic
    present_qty_cols = [c for c in qty_cols if c in df.columns]
    latest_col = None
    if present_qty_cols:
        def get_month_index(col_name):
            m_name = col_name.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
            return MONTHS.index(m_name) if m_name in MONTHS else -1
        latest_col = sorted(present_qty_cols, key=get_month_index)[-1]

    if view_month != "All Months":
        target_col = f"Qty_{view_month}_{YEARS[0]}"
        display_df = df[df[target_col] > 0][["Stock Name", "ISIN", target_col]].copy()
        view_cols = [target_col]
        active_count = len(display_df)
    else:
        # All Months: Grid shows all, Metric shows current
        mask = df[present_qty_cols].sum(axis=1) > 0
        display_df = df[mask][["Stock Name", "ISIN"] + present_qty_cols].copy()
        view_cols = present_qty_cols
        active_count = len(df[df[latest_col] > 0]) if latest_col else 0

    # Metrics
    top_stock = "N/A"
    if latest_col and not df.empty:
        top_series = df.sort_values(by=latest_col, ascending=False).iloc[0]
        if top_series[latest_col] > 0: top_stock = top_series['Stock Name']
    
    delta_pct = 0
    if len(qty_cols) >= 2 and view_month == "All Months":
        curr, prev = df[qty_cols[-1]].sum(), df[qty_cols[-2]].sum()
        delta_pct = ((curr - prev) / prev * 100) if prev > 0 else 0

    # Render Components
    col1, col2, col3 = st.columns(3)
    with col1: ui.render_metric_card("Total Assets", active_count, "Active Positions", "neu")
    with col2: ui.render_metric_card("Top Allocation", top_stock[:15]+"..", "Highest Weight", "pos")
    with col3: 
        arrow = "↑" if delta_pct >= 0 else "↓"
        ui.render_metric_card("Volume Velocity", f"{abs(delta_pct):.1f}%", f"{arrow} MoM Change", "pos" if delta_pct >= 0 else "neg")

    st.markdown("<br>", unsafe_allow_html=True)

   # ... [Previous code remains the same] ...

    st.markdown("<br>", unsafe_allow_html=True)

    if latest_col:
        # 1. FUND FLOW LOGIC 🧠
        new_entries_df = pd.DataFrame()
        exits_df = pd.DataFrame()
        all_qty_cols = sorted(present_qty_cols, key=get_month_index)
        
        if len(all_qty_cols) >= 2:
            curr_col = all_qty_cols[-1]
            prev_col = all_qty_cols[-2]
            
            mask_new = (df[prev_col] == 0) & (df[curr_col] > 0)
            new_entries_df = df[mask_new][["Stock Name", curr_col]].rename(columns={curr_col: "Qty"})
            
            mask_exit = (df[prev_col] > 0) & (df[curr_col] == 0)
            exits_df = df[mask_exit][["Stock Name", prev_col]].rename(columns={prev_col: "Qty"})

        # 2. TABS RENDER
        # RENAMED TAB HERE vvv
        tab1, tab2, tab3, tab4 = st.tabs(["🌊 Fund Flow", "Overview", "Data Grid", "Analytics"])
        
        with tab1:
            if len(all_qty_cols) < 2:
                st.warning("⚠️ Need at least 2 months of data to calculate Entry/Exit flows.")
            else:
                current_month_name = latest_col.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
                ui.render_fund_flow(new_entries_df, exits_df, current_month_name)

        with tab2:
            ui.render_treemap(df[df[latest_col]>0].nlargest(30, latest_col), latest_col)
        
        with tab3:
            if "Stock Name" in display_df.columns:
                agg = {c: "sum" for c in view_cols}
                if "ISIN" in display_df.columns: agg["ISIN"] = "first"
                grid = display_df.groupby("Stock Name", as_index=False).agg(agg).set_index("Stock Name")
            else: grid = display_df
            st.dataframe(grid.style.background_gradient(cmap="Oranges", subset=view_cols).format("{:,.0f}", subset=view_cols), use_container_width=True, height=500)
            
        with tab4:
            c_s, _ = st.columns([1, 2])
            with c_s: stock = st.selectbox("Inspect Asset", sorted(df["Stock Name"].unique().tolist()))
            ui.render_trend_chart(df, stock, qty_cols, YEARS)
else:
    # Welcome Screen
    st.markdown(f"""<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:60vh; text-align:center; border:1px dashed #D6D3D1; border-radius:16px; background:#F5F5F4;"><div style="font-size:4rem; margin-bottom:1rem;">☕</div><h2 style="color:#292524; margin-bottom:0.5rem;">Ready to Track {selected_fund}</h2><p style="color:#78716C; max-width:400px; line-height:1.5;">No local data found. Initialize the database.</p><br></div>""", unsafe_allow_html=True)
    _, c2, _ = st.columns([1,1,1])
    if c2.button("Initialize Database"):
        with st.spinner("Connecting..."):
            run_update_process(selected_fund)
            st.rerun()