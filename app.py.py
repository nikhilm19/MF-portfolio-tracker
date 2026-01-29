import streamlit as st
import pandas as pd
import os
import warnings
import re
from config import FUND_CONFIG, YEARS, MONTHS
import scrapers
import ui
import analysis

warnings.filterwarnings("ignore")

# ===========================
# 1. SETUP & CONFIGURATION
# ===========================
st.set_page_config(page_title="FundFlow Analytics", layout="wide", page_icon="☕")
ui.apply_clean_saas_theme()

# --- SESSION STATE INITIALIZATION ---
if "dashboard_active" not in st.session_state:
    st.session_state["dashboard_active"] = False
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "Single View"

def activate_dashboard():
    """Callback to activate dashboard when user selects a fund"""
    st.session_state["dashboard_active"] = True

def go_home():
    """Reset to home state and navigate back to Single View"""
    st.session_state["dashboard_active"] = False
    st.session_state["run_compare"] = False
    st.session_state["app_mode"] = "Single View"
    st.rerun()

#Helper: Normalize Stock Names
def normalize_names(df):
    if "Stock Name" in df.columns:
        df["Stock Name"] = df["Stock Name"].astype(str)
        df["Stock Name"] = df["Stock Name"].str.replace(r'\s+Limited\s*$', '', case=False, regex=True)
        df["Stock Name"] = df["Stock Name"].str.replace(r'\s+Ltd\.?\s*$', '', case=False, regex=True)
        # Remove special characters but keep alphanumeric, spaces, hyphens, and ampersand
        df["Stock Name"] = df["Stock Name"].str.replace(r'[^\w\s\-&]', '', regex=True)
        df["Stock Name"] = df["Stock Name"].str.replace(r'\s+', ' ', regex=True)  # Collapse multiple spaces
        df["Stock Name"] = df["Stock Name"].str.strip()
    return df

# ===========================
# 2. LOGIC CONTROLLER (SYNC)
# ===========================
def run_update_process(fund_name):
    conf = FUND_CONFIG[fund_name]
    output_file = conf["file"]
    status = st.empty()
    bar = st.progress(0)
    
    if os.path.exists(output_file):
        master_df = pd.read_excel(output_file)
        if "ISIN" in master_df.columns:
            master_df["ISIN"] = master_df["ISIN"].astype(str).str.strip()
    else:
        master_df = pd.DataFrame(columns=["ISIN", "Stock Name"])

    for i, month in enumerate(MONTHS):
        col_name = f"Qty_{month}_{YEARS[0]}"
        if col_name not in master_df.columns:
            status.text(f"📥 Fetching {month} for {fund_name}...")
            new_df = None
            if fund_name == "PPFAS Flexi Cap": new_df = scrapers.fetch_ppfas(month, YEARS[0])
            elif fund_name == "Nippon India Small Cap": new_df = scrapers.fetch_nippon(month, YEARS[0])
            elif fund_name == "HDFC Nifty 50 Index": new_df = scrapers.fetch_hdfc(month, YEARS[0])
            
            if new_df is not None:
                new_df["ISIN"] = new_df["ISIN"].astype(str).str.strip()
                master_df = pd.merge(master_df, new_df, on="ISIN", how="outer", suffixes=("", "_new"))
                
                # Handle Stock Name
                if "Stock Name_new" in master_df.columns:
                    master_df["Stock Name"] = master_df["Stock Name"].fillna(master_df["Stock Name_new"])
                    master_df.drop(columns=["Stock Name_new"], inplace=True)
                st.toast(f"✅ Secured data for {month}  ", icon="✨")
                # Handle Qty column
                if f"{col_name}_new" in master_df.columns:
                    master_df[col_name] = master_df[f"{col_name}_new"]
                    master_df.drop(columns=[f"{col_name}_new"], inplace=True)
                
                # Handle MarketValue column
                market_val_col = f"MarketValue_{month}_{YEARS[0]}"
                if f"{market_val_col}_new" in master_df.columns:
                    master_df[market_val_col] = master_df[f"{market_val_col}_new"]
                    master_df.drop(columns=[f"{market_val_col}_new"], inplace=True)
                
                # Handle NavPct column
                nav_pct_col = f"NavPct_{month}_{YEARS[0]}"
                if f"{nav_pct_col}_new" in master_df.columns:
                    master_df[nav_pct_col] = master_df[f"{nav_pct_col}_new"]
                    master_df.drop(columns=[f"{nav_pct_col}_new"], inplace=True)

            else:
                st.toast(f"⚠️ Data for {month} not found. Skipping.", icon="⚠️")
        bar.progress((i + 1) / len(MONTHS))
    
    master_df = normalize_names(master_df)
    master_df.to_excel(output_file, index=False)
    status.empty()
    bar.empty()
    return master_df

# ===========================
# 3. SIDEBAR NAVIGATION
# ===========================
with st.sidebar:
    st.markdown("""
        <div style="padding-top: 20px;">
            <h1 class="hero-title">
                Welcome <span class="hero-gradient">back!</span>
            </h1>
            
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Mode")
    mode_index = 0 if st.session_state.get("app_mode", "Single View") == "Single View" else 1
    app_mode = st.radio("Navigation Mode", ["Single View", "Compare Funds"], index=mode_index, label_visibility="collapsed")
    st.session_state["app_mode"] = app_mode
    st.markdown("---")

    if app_mode == "Single View":
        st.markdown("### Workspace")
        # ADDED on_change callback to activate dashboard instantly
        selected_fund = st.selectbox(
            "Active Portfolio", 
            list(FUND_CONFIG.keys()), 
            on_change=activate_dashboard 
        )
        current_file = FUND_CONFIG[selected_fund]["file"]
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("↻ Sync"):
                with st.spinner("Scraping & Cleaning..."):
                    run_update_process(selected_fund)
                    activate_dashboard() # Ensure dashboard shows after sync
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
        
    else: 
        st.markdown("### ⚔️ Compare")
        st.caption("Select two funds to find overlapping holdings.")
        fund_a = st.selectbox("Base Fund (A)", list(FUND_CONFIG.keys()), index=0)
        fund_b = st.selectbox("Target Fund (B)", list(FUND_CONFIG.keys()), index=1)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Analyze Overlap", type="primary"):
            if fund_a == fund_b:
                st.error("❌ Please select two different funds to compare.")
            else:
                st.session_state['run_compare'] = True
                activate_dashboard() # Switch to view on click

# ===========================
# 4. MAIN VIEW CONTROLLER
# ===========================

if app_mode == "Single View":
    # 1. CHECK: Is the dashboard explicitly active?
    # 2. CHECK: Does the file exist?
    
    show_dashboard = st.session_state["dashboard_active"] and os.path.exists(current_file)

    if show_dashboard:
        # --- HOME BUTTON AT TOP ---
        if st.button("← Back to Home", key="home_btn"):
            go_home()
        
        st.markdown("---")
        
        # --- RENDER DASHBOARD ---
        st.markdown(f"""
            <div style="margin-bottom: 2rem; padding-top: 1rem;">
                <h1 style="font-size: 2rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px;">
                    {selected_fund} <span class="live-badge">● Live</span>
                </h1>
                <p style="font-size: 1rem; opacity: 0.8;">Real-time portfolio disclosure tracking & analytics</p>
            </div>
        """, unsafe_allow_html=True)

        df = pd.read_excel(current_file)
        df = normalize_names(df)
        
        qty_cols = [c for c in df.columns if "Qty_" in c]
        for c in qty_cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        present_qty_cols = [c for c in qty_cols if c in df.columns]
        latest_col = None
        
        if present_qty_cols:
            def get_month_index(col_name):
                m_name = col_name.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
                return MONTHS.index(m_name) if m_name in MONTHS else -1
            sorted_cols = sorted(present_qty_cols, key=get_month_index)
            latest_col = sorted_cols[-1]

        if view_month != "All Months":
            target_col = f"Qty_{view_month}_{YEARS[0]}"
            display_df = df[df[target_col] > 0][["Stock Name", "ISIN", target_col]].copy()
            view_cols = [target_col]
            active_count = len(display_df)
        else:
            mask = df[present_qty_cols].sum(axis=1) > 0
            display_df = df[mask][["Stock Name", "ISIN"] + present_qty_cols].copy()
            view_cols = present_qty_cols
            active_count = len(df[df[latest_col] > 0]) if latest_col else 0

        top_stock = "N/A"
        top_nav_pct = 0
        if latest_col and not df.empty:
            top_series = df.sort_values(by=latest_col, ascending=False).iloc[0]
            if top_series[latest_col] > 0: 
                top_stock = top_series['Stock Name']
                # Get corresponding NavPct column
                nav_pct_col = latest_col.replace("Qty_", "NavPct_")
                if nav_pct_col in df.columns:
                    top_nav_pct = top_series[nav_pct_col]
        
        delta_pct = 0
        if len(qty_cols) >= 2 and view_month == "All Months":
            curr, prev = df[qty_cols[-1]].sum(), df[qty_cols[-2]].sum()
            delta_pct = ((curr - prev) / prev * 100) if prev > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1: ui.render_metric_card("Total Assets", active_count, "Active Positions", "neu")
        with col2: ui.render_metric_card("Top Allocation", top_stock[:15]+"..", f"{top_nav_pct*100:.2f}% of NAV", "pos")
        with col3: 
            arrow = "↑" if delta_pct >= 0 else "↓"
            ui.render_metric_card("Volume Velocity", f"{abs(delta_pct):.1f}%", f"{arrow} MoM Change", "pos" if delta_pct >= 0 else "neg")

        st.markdown("<br>", unsafe_allow_html=True)

        if latest_col:
            new_entries_df = pd.DataFrame()
            exits_df = pd.DataFrame()
            
            # Determine which month to show in Fund Flow
            if view_month != "All Months":
                current_month_col = f"Qty_{view_month}_{YEARS[0]}"
                # Find previous month
                current_idx = MONTHS.index(view_month) if view_month in MONTHS else -1
                if current_idx > 0:
                    prev_month = MONTHS[current_idx - 1]
                    prev_month_col = f"Qty_{prev_month}_{YEARS[0]}"
                    if prev_month_col in df.columns and current_month_col in df.columns:
                        mask_new = (df[prev_month_col] == 0) & (df[current_month_col] > 0)
                        new_entries_df = df[mask_new][["Stock Name", current_month_col]].rename(columns={current_month_col: "Qty"})
                        mask_exit = (df[prev_month_col] > 0) & (df[current_month_col] == 0)
                        exits_df = df[mask_exit][["Stock Name", prev_month_col]].rename(columns={prev_month_col: "Qty"})
                        fund_flow_label = view_month
                    else:
                        fund_flow_label = view_month
                else:
                    fund_flow_label = view_month
            else:
                # Use latest months for "All Months" view
                if len(sorted_cols) >= 2:
                    curr_col = sorted_cols[-1]
                    prev_col = sorted_cols[-2]
                    mask_new = (df[prev_col] == 0) & (df[curr_col] > 0)
                    new_entries_df = df[mask_new][["Stock Name", curr_col]].rename(columns={curr_col: "Qty"})
                    mask_exit = (df[prev_col] > 0) & (df[curr_col] == 0)
                    exits_df = df[mask_exit][["Stock Name", prev_col]].rename(columns={prev_col: "Qty"})
                    fund_flow_label = latest_col.replace("Qty_", "").replace(f"_{YEARS[0]}", "")
                else:
                    fund_flow_label = "N/A"

            tab1, tab2, tab3, tab4 = st.tabs(["Fund Flow", "Overview", "Data Grid", "Analytics"])
            
            with tab1:
                if view_month != "All Months" and MONTHS.index(view_month) == 0:
                    st.warning("⚠️ January has no previous month for Entry/Exit comparison.")
                elif len(sorted_cols) < 2 and view_month == "All Months":
                    st.warning("⚠️ Need at least 2 months of data to calculate Entry/Exit flows.")
                else: ui.render_fund_flow(new_entries_df, exits_df, fund_flow_label)

            with tab2: ui.render_treemap(df[df[latest_col]>0].nlargest(30, latest_col), latest_col)
            
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
        # --- SHOW LANDING PAGE (Default State) ---
        start_clicked = ui.render_landing_page()
        
        if start_clicked:
            activate_dashboard() # Set state to True
            with st.spinner("Connecting & Cleaning Database..."):
                run_update_process(selected_fund)
                st.rerun()

else: # Compare Mode View
    # --- HOME BUTTON AT TOP ---
    if st.button("← Back to Home", key="home_btn_compare"):
        go_home()
    
    st.markdown("---")
    
    st.markdown(f"""
        <div style="margin-bottom: 2rem; padding-top: 1rem;">
            <h1 style="font-size: 2rem; margin-bottom: 0.5rem;">Overlap Tool</h1>
            <p style="font-size: 1rem; opacity: 0.8;">Analyze diversification and common bets between {fund_a} and {fund_b}.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('run_compare', False):
        results = analysis.compare_portfolios(fund_a, fund_b)
        ui.render_comparison_dashboard(fund_a, fund_b, results)
    else:
        st.info("Select two funds from the sidebar and click 'Analyze Overlap'.")

# ===========================
# FOOTER - SUPPORTED FUNDS
# ===========================
st.markdown("---")
with st.expander("ℹ️ Supported Funds"):
    st.caption("The following funds are currently supported for auto-syncing:")
    for fund in FUND_CONFIG.keys():
        st.markdown(f"**• {fund}**")