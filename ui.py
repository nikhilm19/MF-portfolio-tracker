import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def apply_clean_saas_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

            /* 1. GLOBAL RESET & TYPOGRAPHY */
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', sans-serif;
                -webkit-font-smoothing: antialiased;
                color: #111827;
            }
            
            /* 2. BACKGROUND */
            .stApp {
                background-color: #FAFAFA;
                background-image: radial-gradient(#F3F4F6 1px, transparent 1px);
                background-size: 20px 20px;
            }

            /* 3. SIDEBAR */
            [data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid #F3F4F6;
            }
            
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
                color: #111827 !important;
                font-weight: 500;
            }

            /* --- CRITICAL NAVIGATION FIX --- */
            /* 1. Force the Header to be visible but transparent so buttons show */
            [data-testid="stHeader"] {
                background-color: transparent !important;
                z-index: 999999 !important; /* Always on top */
            }

            /* 2. Color the icons BLACK */
            [data-testid="stSidebarCollapsedControl"] svg,
            [data-testid="stHeader"] button[kind="header"] svg {
                fill: #000000 !important;
                color: #000000 !important;
                stroke: #000000 !important;
            }
            
            /* 3. Force the container to be visible */
            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
                color: #000000 !important;
            }
            /* ------------------------------- */

            /* 4. LANDING PAGE STYLES */
            .hero-container {
                padding: 40px 0;
            }
            .hero-pill {
                background: #FFF7ED;
                color: #C2410C;
                padding: 6px 16px;
                border-radius: 99px;
                font-size: 0.8rem;
                font-weight: 700;
                border: 1px solid #FFEDD5;
                display: inline-block;
                margin-bottom: 20px;
            }
            .hero-title {
                font-size: 3.5rem;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 20px;
                color: #111827;
                letter-spacing: -1px;
            }
            .hero-gradient {
                background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .hero-subtitle-main {
                font-size: 1.6rem;
                color: #1F2937;
                font-weight: 700;
                line-height: 1.3;
                margin-bottom: 10px;
            }
            .hero-subtitle-desc {
                font-size: 1.1rem;
                color: #6B7280;
                line-height: 1.6;
                margin-bottom: 30px;
                max-width: 90%;
            }
            
            /* Glass Card */
            .glass-card {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border: 1px solid #FFFFFF;
                border-radius: 24px;
                padding: 25px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.08);
                transform: rotate(-2deg);
                transition: transform 0.3s ease;
            }
            .glass-card:hover {
                transform: rotate(0deg) scale(1.02);
            }
            .glass-metric { font-size: 2rem; font-weight: 800; color: #111827; }
            .glass-label { font-size: 0.85rem; color: #9CA3AF; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

            /* Bento Cards */
            .bento-card {
                background: #FFFFFF;
                border-radius: 24px;
                padding: 30px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
                border: 1px solid #F3F4F6;
                height: 100%;
                transition: all 0.2s ease;
            }
            .bento-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
                border-color: #FED7AA;
            }
            .bento-icon {
                font-size: 2rem;
                margin-bottom: 15px;
                background: #FFF7ED;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 12px;
            }

            /* 5. METRIC CARDS */
            .metric-card {
                background: #FFFFFF;
                border: none; 
                border-radius: 20px; 
                padding: 24px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.05); 
                transition: transform 0.2s ease;
                margin-bottom: 20px;
            }
            .metric-card:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.08); }
            .metric-label { font-size: 0.85rem; text-transform: uppercase; color: #9CA3AF; font-weight: 600; margin-bottom: 8px; letter-spacing: 0.5px; }
            .metric-value { font-size: 2.5rem; font-weight: 800; color: #111827; letter-spacing: -0.5px; }
            .metric-delta { display: inline-flex; align-items: center; font-size: 0.9rem; font-weight: 600; margin-top: 10px; padding: 4px 12px; border-radius: 99px; }
            .delta-pos { background: #ECFDF5; color: #059669; } 
            .delta-neg { background: #FEF2F2; color: #DC2626; } 
            .delta-neu { background: #F3F4F6; color: #4B5563; } 
            
            /* 6. BUTTONS */
            .stButton > button {
                background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%);
                color: #FFFFFF !important; 
                border: none;
                border-radius: 12px; 
                font-weight: 600;
                padding: 0.6rem 1.5rem;
                box-shadow: 0 4px 15px rgba(255, 107, 0, 0.25);
                transition: all 0.2s ease;
            }
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 20px rgba(255, 107, 0, 0.35);
                color: #FFFFFF !important;
            }
            
            /* PULSE ANIMATION */
            @keyframes pulse-glow {
                0% { box-shadow: 0 0 0 0 rgba(255, 107, 0, 0.7); }
                70% { box-shadow: 0 0 0 12px rgba(255, 107, 0, 0); }
                100% { box-shadow: 0 0 0 0 rgba(255, 107, 0, 0); }
            }
            div[data-testid="stButton"] button[kind="primary"] {
                animation: pulse-glow 2s infinite;
                font-size: 1.1rem;
                padding: 0.8rem 2.5rem;
            }

            .stDownloadButton > button {
                background: #F3F4F6; color: #374151 !important; box-shadow: none;
            }
            .stDownloadButton > button:hover {
                background: #E5E7EB; color: #111827 !important; box-shadow: none;
            }

            /* 7. TABS */
            .stTabs [data-baseweb="tab-list"] { background-color: #F3F4F6; padding: 4px; border-radius: 99px; gap: 5px; margin-bottom: 25px; }
            .stTabs [data-baseweb="tab"] { height: 40px; border-radius: 99px; background-color: transparent; color: #6B7280; font-weight: 600; border: none; flex: 1; }
            .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%) !important; color: #FFFFFF !important; box-shadow: 0 4px 15px rgba(255, 107, 0, 0.25); }

            /* 8. DATAFRAME */
            [data-testid="stDataFrame"] { border: none; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); background: white; overflow: hidden; }
            
            /* 9. BADGE */
            .live-badge { background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%); color: white; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; margin-left: 10px; box-shadow: 0 2px 10px rgba(255, 107, 0, 0.3); }

            #MainMenu, footer { visibility: hidden; }
            
            /* REMOVE this if it was hiding the mobile menu */
            /* [data-testid="stHeader"] { background-color: rgba(0,0,0,0); } */
        </style>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, delta=None, delta_color="neu"):
    delta_html = f'<div class="metric-delta delta-{delta_color}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_treemap(df, col_name):
    fig = px.treemap(df, path=['Stock Name'], values=col_name, color=col_name, color_continuous_scale='Oranges')
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#4B5563"),
        margin=dict(t=0, l=0, r=0, b=0), coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="white", bordercolor="white", font=dict(family="Plus Jakarta Sans, sans-serif", color="#111827"))
    )
    fig.update_traces(marker=dict(line=dict(width=0)))
    st.plotly_chart(fig, use_container_width=True)

def render_trend_chart(df, stock_name, qty_cols, years):
    trend_data = df[df["Stock Name"] == stock_name].melt(id_vars=["Stock Name"], value_vars=qty_cols, var_name="Month", value_name="Qty")
    trend_data["Month"] = trend_data["Month"].str.replace("Qty_", "").str.replace(f"_{years[0]}", "")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data['Month'], y=trend_data['Qty'], fill='tozeroy', mode='lines+markers',
        line=dict(color='#FF6B00', width=4, shape='spline'),
        marker=dict(size=8, color='#FFFFFF', line=dict(width=3, color='#FF6B00')),
        fillcolor='rgba(255, 107, 0, 0.05)'
    ))
    fig.update_layout(
        title=dict(text=f"{stock_name} Trajectory", font=dict(size=18, family="Plus Jakarta Sans, sans-serif", color="#111827", weight=700)),
        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#6B7280"),
        xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor='#F3F4F6', gridwidth=1, zeroline=False),
        hovermode="x unified", hoverlabel=dict(bgcolor="white", font=dict(family="Plus Jakarta Sans, sans-serif", color="#111827"), bordercolor="#F3F4F6")
    )
    st.plotly_chart(fig, use_container_width=True)

def render_fund_flow(entries_df, exits_df, current_month):
    st.markdown(f"#### 🌊 Fund Flow: {current_month} Activity")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 20px;"><div style="color: #059669; font-weight: 700; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span style="background: #ECFDF5; padding: 4px 10px; border-radius: 99px;">FRESH ENTRIES</span><span style="color: #9CA3AF;">{len(entries_df)}</span></div>""", unsafe_allow_html=True)
        if not entries_df.empty:
            for _, row in entries_df.iterrows():
                st.markdown(f"""<div style="border-bottom: 1px solid #F3F4F6; padding: 10px 0; display: flex; justify-content: space-between; align-items: center;"><span style="font-weight: 600; color: #111827;">{row['Stock Name']}</span><span style="font-size: 0.85rem; color: #059669; background: #ECFDF5; padding: 2px 10px; border-radius: 99px;">+{row['Qty']:,.0f}</span></div>""", unsafe_allow_html=True)
        else: st.markdown("<div style='color: #9CA3AF; font-style: italic; padding: 10px 0;'>No new entries this month.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 20px;"><div style="color: #DC2626; font-weight: 700; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span style="background: #FEF2F2; padding: 4px 10px; border-radius: 99px;">COMPLETE EXITS</span><span style="color: #9CA3AF;">{len(exits_df)}</span></div>""", unsafe_allow_html=True)
        if not exits_df.empty:
            for _, row in exits_df.iterrows():
                st.markdown(f"""<div style="border-bottom: 1px solid #F3F4F6; padding: 10px 0; display: flex; justify-content: space-between; align-items: center; opacity: 0.6;"><span style="font-weight: 500; text-decoration: line-through; color: #6B7280;">{row['Stock Name']}</span><span style="font-size: 0.85rem; color: #DC2626; background: #FEF2F2; padding: 2px 10px; border-radius: 99px;">Sold</span></div>""", unsafe_allow_html=True)
        else: st.markdown("<div style='color: #9CA3AF; font-style: italic; padding: 10px 0;'>No exits this month.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_comparison_dashboard(fund_a, fund_b, analysis_result):
    if "error" in analysis_result:
        st.error(analysis_result["error"])
        return
    df = analysis_result["merged_df"]
    unique_a_list = df[df["Status"] == f"Unique to {fund_a}"]["Stock Name"].sort_values().tolist()
    unique_b_list = df[df["Status"] == f"Unique to {fund_b}"]["Stock Name"].sort_values().tolist()
    common_list = df[df["Status"] == "Overlap"]["Stock Name"].sort_values().tolist()

    st.markdown(f"### ⚔️ Portfolio Clash: <span style='color:#FF6B00'>{fund_a}</span> vs <span style='color:#FF6B00'>{fund_b}</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    def render_list_column(title, subtitle, count, pill_color, text_color, items):
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); height: 100%; margin-bottom: 20px;"><div style="text-align: center; border-bottom: 1px solid #F3F4F6; padding-bottom: 15px; margin-bottom: 15px;"><div style="color: #9CA3AF; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px;">{title}</div><div style="color: #111827; font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">{subtitle}</div><div style="background: {pill_color}; color: {text_color}; font-size: 0.8rem; font-weight: 600; padding: 2px 10px; border-radius: 99px; display: inline-block;">{count} Stocks</div></div><div style="max-height: 400px; overflow-y: auto;">""", unsafe_allow_html=True)
        for item in items: st.markdown(f"<div style='border-bottom: 1px solid #FAFAFA; padding: 6px 0; font-size: 0.9rem; color: #4B5563;'>{item}</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with c1: render_list_column("ONLY IN", fund_a.split()[0].upper(), len(unique_a_list), "#F3F4F6", "#374151", unique_a_list) 
    with c2: render_list_column("COMMON", "BOTH FUNDS", len(common_list), "#FFF7ED", "#C2410C", common_list) 
    with c3: render_list_column("ONLY IN", fund_b.split()[0].upper(), len(unique_b_list), "#F3F4F6", "#374151", unique_b_list) 

def render_landing_page():
    # --- HERO SECTION ---
    c1, c2 = st.columns([1.2, 1], gap="large")
    
    with c1:
        st.markdown("""
        <div style="padding-top: 20px;">
            <div class="hero-pill">🚀 Insights v2.0 is Live</div>
            <h1 class="hero-title">
                FundFlow <span class="hero-gradient">Analytics</span>
            </h1>
            <p class="hero-subtitle-main">
                Decode the strategy behind the NAV.
            </p>
            <p class="hero-subtitle-desc">
                We track every monthly buy and sell to educate you on exactly how funds manage your money.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- PRIMARY CTA BUTTON (Pulsing) ---
        if st.button("⚡ Initialize Database", type="primary"):
            return True

    with c2:
        # Floating Glass Mockup
        st.markdown("""
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div class="glass-label">Total Assets Analyzed</div>
                <div style="background:#ECFDF5; color:#059669; padding:2px 8px; border-radius:99px; font-size:0.8rem; font-weight:700;">+12.5%</div>
            </div>
            <div class="glass-metric">₹ 42,500 Cr</div>
            <div style="margin-top:20px; height:8px; background:#F3F4F6; border-radius:99px; width:100%;">
                <div style="height:100%; background: linear-gradient(90deg, #FF6B00, #FF9900); width:70%; border-radius:99px;"></div>
            </div>
            <div style="margin-top:20px; display:flex; gap:10px;">
                <div style="flex:1; background:#F9FAFB; padding:10px; border-radius:12px; text-align:center;">
                    <div style="font-size:0.7rem; color:#6B7280;">ACTIVE STOCKS</div>
                    <div style="font-weight:700;">45</div>
                </div>
                <div style="flex:1; background:#FFF7ED; padding:10px; border-radius:12px; text-align:center;">
                    <div style="font-size:0.7rem; color:#C2410C;">FRESH ENTRIES</div>
                    <div style="font-weight:700; color:#EA580C;">+3</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # --- BENTO GRID FEATURES ---
    st.markdown("<h3 style='text-align:center; margin-bottom:40px;'>Everything you need to analyze funds</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-icon">🌊</div>
            <h4 style="margin-bottom:10px;">Whale Watcher</h4>
            <p style="color:#6B7280; font-size:0.9rem; line-height:1.5;">Instantly spot fresh entries and complete exits. See what the fund manager is buying before the news reports it.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-icon">⚔️</div>
            <h4 style="margin-bottom:10px;">Overlap Clash</h4>
            <p style="color:#6B7280; font-size:0.9rem; line-height:1.5;">Run a Venn-diagram style analysis on any two portfolios. Identify hidden redundancies and optimize diversification.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="bento-card">
            <div class="bento-icon">📈</div>
            <h4 style="margin-bottom:10px;">Trend Trajectory</h4>
            <p style="color:#6B7280; font-size:0.9rem; line-height:1.5;">Visualize the historical conviction of a fund manager in specific stocks using our smooth spline analytics charts.</p>
        </div>
        """, unsafe_allow_html=True)

    return False