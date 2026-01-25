import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def apply_clean_saas_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
            .stApp { background-color: #F5F5F4; color: #292524; }
            [data-testid="stSidebar"] { background-color: #292524; border-right: 1px solid #44403C; }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #E7E5E4 !important; }
            h1, h2, h3 { color: #292524 !important; font-weight: 700; }
            p, label, .stMarkdown { color: #57534E !important; }
            
            /* 5. CARDS (Soft & Floating) */
            .metric-card {
                background: #FFFFFF;
                border: none; 
                border-radius: 20px; 
                padding: 24px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.05); 
                transition: transform 0.2s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.08);
            }
            
            .metric-label { 
                font-size: 0.85rem; 
                text-transform: uppercase; 
                color: #9CA3AF; 
                font-weight: 600; 
                margin-bottom: 8px; 
                letter-spacing: 0.5px;
            }
            .metric-value { 
                font-size: 2.5rem; 
                font-weight: 800; 
                color: #111827; 
                letter-spacing: -0.5px;
            }
            .metric-delta { 
                display: inline-flex; 
                align-items: center; 
                font-size: 0.9rem; 
                font-weight: 600; 
                margin-top: 10px; 
                padding: 4px 12px; 
                border-radius: 99px; 
            }
            .delta-pos { background: #ECFDF5; color: #059669; } 
            .delta-neg { background: #FEF2F2; color: #DC2626; } 
            .delta-neu { background: #F3F4F6; color: #4B5563; } 
            
            /* 6. BUTTONS (Pill Shaped & Gradient) */
            .stButton > button {
                background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%);
                color: white;
                border: none;
                border-radius: 99px; 
                font-weight: 600;
                padding: 0.6rem 1.5rem;
                box-shadow: 0 4px 15px rgba(255, 107, 0, 0.25);
                transition: all 0.2s ease;
            }
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 20px rgba(255, 107, 0, 0.35);
            }
            
            /* Secondary/Ghost Buttons */
            .stDownloadButton > button {
                background: #F3F4F6;
                color: #374151;
                box-shadow: none;
            }
            .stDownloadButton > button:hover {
                background: #E5E7EB;
                color: #111827;
                box-shadow: none;
            }

            /* 7. TABS (Segmented Control) */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #F3F4F6; 
                padding: 4px;
                border-radius: 99px; 
                gap: 5px;
                margin-bottom: 25px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 40px;
                border-radius: 99px; 
                background-color: transparent;
                color: #6B7280;
                font-weight: 600;
                border: none;
                flex: 1;
            }
            .stTabs [aria-selected="true"] {
                background-color: #FFFFFF !important;
                color: #FF6B00 !important; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }

            /* 8. GRID & TABLES */
            [data-testid="stDataFrame"] {
                border: none;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.05);
                background: white;
                overflow: hidden;
            }
            
            /* 9. HEADER BADGE */
            .live-badge { 
                background: linear-gradient(135deg, #FF6B00 0%, #FF9900 100%);
                color: white; 
                padding: 4px 12px; 
                border-radius: 99px; 
                font-size: 0.75rem; 
                font-weight: 700; 
                margin-left: 10px;
                box-shadow: 0 2px 10px rgba(255, 107, 0, 0.3);
            }

            /* Remove Cruft */
            #MainMenu, footer { visibility: hidden; }
            [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
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
    colors = ['#FF6B00', '#FF9900', '#FFB74D', '#FDBA74', '#9CA3AF']
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
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);"><div style="color: #059669; font-weight: 700; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span style="background: #ECFDF5; padding: 4px 10px; border-radius: 99px;">FRESH ENTRIES</span><span style="color: #9CA3AF;">{len(entries_df)}</span></div>""", unsafe_allow_html=True)
        if not entries_df.empty:
            for _, row in entries_df.iterrows():
                st.markdown(f"""<div style="border-bottom: 1px solid #F3F4F6; padding: 10px 0; display: flex; justify-content: space-between; align-items: center;"><span style="font-weight: 600; color: #111827;">{row['Stock Name']}</span><span style="font-size: 0.85rem; color: #059669; background: #ECFDF5; padding: 2px 10px; border-radius: 99px;">+{row['Qty']:,.0f}</span></div>""", unsafe_allow_html=True)
        else: st.markdown("<div style='color: #9CA3AF; font-style: italic; padding: 10px 0;'>No new entries this month.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);"><div style="color: #DC2626; font-weight: 700; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;"><span style="background: #FEF2F2; padding: 4px 10px; border-radius: 99px;">COMPLETE EXITS</span><span style="color: #9CA3AF;">{len(exits_df)}</span></div>""", unsafe_allow_html=True)
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
        st.markdown(f"""<div style="background: white; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); height: 100%;"><div style="text-align: center; border-bottom: 1px solid #F3F4F6; padding-bottom: 15px; margin-bottom: 15px;"><div style="color: #9CA3AF; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px;">{title}</div><div style="color: #111827; font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">{subtitle}</div><div style="background: {pill_color}; color: {text_color}; font-size: 0.8rem; font-weight: 600; padding: 2px 10px; border-radius: 99px; display: inline-block;">{count} Stocks</div></div><div style="max-height: 400px; overflow-y: auto;">""", unsafe_allow_html=True)
        for item in items: st.markdown(f"<div style='border-bottom: 1px solid #FAFAFA; padding: 6px 0; font-size: 0.9rem; color: #4B5563;'>{item}</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    with c1: render_list_column("ONLY IN", fund_a.split()[0].upper(), len(unique_a_list), "#F3F4F6", "#374151", unique_a_list) 
    with c2: render_list_column("COMMON", "BOTH FUNDS", len(common_list), "#FFF7ED", "#C2410C", common_list) 
    with c3: render_list_column("ONLY IN", fund_b.split()[0].upper(), len(unique_b_list), "#F3F4F6", "#374151", unique_b_list) 

def render_landing_page():
    """Renders the informative Landing Page for new users."""
    st.markdown("""
        <div style="text-align: center; padding: 40px 20px 60px 20px;">
            <h1 style="font-size: 3.5rem; margin-bottom: 10px; background: -webkit-linear-gradient(135deg, #FF6B00 0%, #FF9900 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Master Your Portfolio
            </h1>
            <p style="font-size: 1.2rem; color: #6B7280; max-width: 600px; margin: 0 auto; line-height: 1.6;">
                Turn raw monthly disclosures into actionable insights. Track fund overlaps, spot fresh entries, and analyze historical trends instantly.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); height: 100%; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 15px;">🌊</div>
            <h3 style="margin-bottom: 10px;">Fund Flow</h3>
            <p style="font-size: 0.9rem;">Instantly spot what the Fund Manager is buying and selling. Don't wait for the news.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); height: 100%; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 15px;">⚔️</div>
            <h3 style="margin-bottom: 10px;">Overlap Analysis</h3>
            <p style="font-size: 0.9rem;">Compare any two funds to find hidden redundancies in your portfolio. Optimize diversification.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); height: 100%; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 15px;">📈</div>
            <h3 style="margin-bottom: 10px;">Trend Tracker</h3>
            <p style="font-size: 0.9rem;">Visualize the historical trajectory of any stock quantity over time with clean spline charts.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CTA
    st.markdown("""
    <div style="text-align: center;">
        <p style="font-weight: 600; color: #111827;">Ready to get started?</p>
        <p style="font-size: 0.9rem; color: #6B7280;">Select a fund from the sidebar or click 'Sync' to fetch the latest data.</p>
    </div>
    """, unsafe_allow_html=True)