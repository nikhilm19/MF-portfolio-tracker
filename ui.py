# ui.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def apply_latte_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
            .stApp { background-color: #F5F5F4; color: #292524; }
            [data-testid="stSidebar"] { background-color: #292524; border-right: 1px solid #44403C; }
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #E7E5E4 !important; }
            h1, h2, h3 { color: #292524 !important; font-weight: 700; }
            p, label, .stMarkdown { color: #57534E !important; }
            
            /* CARDS */
            .metric-card {
                background: #FFFFFF; border: 1px solid #E7E5E4; border-radius: 12px;
                padding: 24px; box-shadow: 0 4px 6px -1px rgba(68, 64, 60, 0.05);
            }
            .metric-label { font-size: 0.75rem; text-transform: uppercase; color: #A8A29E; font-weight: 600; margin-bottom: 8px; }
            .metric-value { font-size: 2rem; font-weight: 700; color: #292524; }
            .metric-delta { display: inline-flex; align-items: center; font-size: 0.875rem; font-weight: 500; margin-top: 8px; padding: 2px 8px; border-radius: 6px; }
            .delta-pos { color: #15803D; background: #DCFCE7; }
            .delta-neg { color: #B91C1C; background: #FEE2E2; }
            .delta-neu { color: #57534E; background: #F5F5F4; }
            
            /* BUTTONS & TABS */
            .stButton > button { background: #EA580C; color: white; border: none; border-radius: 8px; font-weight: 500; width: 100%; }
            .stButton > button:hover { background: #C2410C; }
            
            /* --- FIXED TAB STYLING --- */
            .stTabs [data-baseweb="tab-list"] { 
                background-color: transparent; 
                padding: 0px; 
                gap: 8px; /* Added spacing between tabs */
                border-bottom: 1px solid #E7E5E4;
                margin-bottom: 20px;
            }
            .stTabs [data-baseweb="tab"] { 
                height: 40px; 
                border-radius: 8px; 
                background-color: #FFFFFF; /* White background for inactive */
                color: #78716C; 
                font-weight: 500; 
                border: 1px solid #E7E5E4; 
                flex: 1;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            .stTabs [aria-selected="true"] { 
                background-color: #FEF3E2; /* Light orange highlight */
                color: #EA580C !important; 
                border: 2px solid #EA580C;
            }
            /* ------------------------- */

            [data-testid="stDataFrame"] { border: 1px solid #E7E5E4; border-radius: 8px; background: white; }
            
            /* HEADER */
            .live-badge { background: #FFEDD5; color: #C2410C; padding: 2px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; border: 1px solid #FED7AA; margin-left: 10px; }
            #MainMenu, footer { visibility: hidden; }
            [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
        </style>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, delta=None, delta_color="neu"):
    delta_html = f'<div class="metric-delta delta-{delta_color}">{delta}</div>' if delta else ""
    st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div>{delta_html}</div>""", unsafe_allow_html=True)

def render_treemap(df, col_name):
    fig = px.treemap(df, path=['Stock Name'], values=col_name, color=col_name, color_continuous_scale='Oranges')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#57534E", margin=dict(t=0, l=0, r=0, b=0), coloraxis_showscale=False, hoverlabel=dict(bgcolor="white", bordercolor="#D6D3D1"))
    st.plotly_chart(fig, use_container_width=True)

def render_trend_chart(df, stock_name, qty_cols, years):
    trend_data = df[df["Stock Name"] == stock_name].melt(id_vars=["Stock Name"], value_vars=qty_cols, var_name="Month", value_name="Qty")
    trend_data["Month"] = trend_data["Month"].str.replace("Qty_", "").str.replace(f"_{years[0]}", "")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_data['Month'], y=trend_data['Qty'], fill='tozeroy', mode='lines+markers', line=dict(color='#EA580C', width=3, shape='spline'), marker=dict(size=6, color='#EA580C', line=dict(width=2, color='white')), fillcolor='rgba(234, 88, 12, 0.1)'))
    fig.update_layout(title=dict(text=f"{stock_name} Trajectory", font=dict(size=14, color="#57534E")), template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Inter, sans-serif", color="#57534E"), xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor='#E7E5E4', zeroline=False), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# --- RENAMED & IMPROVED RENDERER ---
def render_fund_flow(entries_df, exits_df, current_month):
    """Renders the Fund Flow Analysis dashboard"""
    st.markdown(f"#### 🌊 Fund Flow: {current_month} Activity")
    st.caption("Track new positions and complete exits relative to the previous month.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div style="background-color: #DCFCE7; padding: 12px; border-radius: 8px; border: 1px solid #86EFAC; color: #166534; font-weight: 600; margin-bottom: 12px;">🟢 Fresh Entries ({len(entries_df)})</div>""", unsafe_allow_html=True)
        if not entries_df.empty:
            for _, row in entries_df.iterrows():
                st.markdown(f"""<div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #E7E5E4; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><span style="font-weight: 600; color: #292524;">{row['Stock Name']}</span><span style="font-size: 0.85rem; color: #15803D; background: #DCFCE7; padding: 2px 8px; border-radius: 4px;">+{row['Qty']:,.0f}</span></div>""", unsafe_allow_html=True)
        else: st.info("No new positions added.")

    with col2:
        st.markdown(f"""<div style="background-color: #FEE2E2; padding: 12px; border-radius: 8px; border: 1px solid #FCA5A5; color: #991B1B; font-weight: 600; margin-bottom: 12px;">🔴 Complete Exits ({len(exits_df)})</div>""", unsafe_allow_html=True)
        if not exits_df.empty:
            for _, row in exits_df.iterrows():
                st.markdown(f"""<div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #E7E5E4; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; opacity: 0.7;"><span style="font-weight: 500; color: #57534E; text-decoration: line-through;">{row['Stock Name']}</span><span style="font-size: 0.85rem; color: #B91C1C; background: #FEE2E2; padding: 2px 8px; border-radius: 4px;">Sold Out</span></div>""", unsafe_allow_html=True)
        else: st.info("No positions sold off completely.")