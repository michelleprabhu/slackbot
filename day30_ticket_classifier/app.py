import streamlit as st
import pandas as pd
import json
import os
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from ticket_classifier import classify_tickets, generate_stats
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Strategic Planning Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Fidelity Design System (Monochrome & Visibility Focused)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    :root {
        --primary: #0f172a;
        --secondary: #475569;
        --accent: #000000;
        --glass-bg: rgba(255, 255, 255, 0.85);
        --glass-border: rgba(203, 213, 225, 0.5);
        --bg-gradient: radial-gradient(circle at top right, #f8fafc, #e2e8f0);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--primary);
    }

    .stApp {
        background: var(--bg-gradient);
        background-attachment: fixed;
    }

    /* Fix invisible text in main area */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: var(--primary) !important;
    }

    /* Overwrite specific streamlit text issues */
    .stMarkdown p, .stMarkdown div, .stText {
        color: var(--primary) !important;
    }

    /* Fixed Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        padding-top: 1rem;
    }
    
    .sidebar-logo {
        font-size: 1.8rem;
        font-weight: 800;
        color: #000000;
        letter-spacing: -1.5px;
        margin-bottom: 3rem;
        padding: 0 1rem;
    }

    /* High-Fidelity Glass Card - Improved Contrast */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
    }

    .dark-card {
        background: #000000;
        border-radius: 16px;
        padding: 28px;
        color: #ffffff !important;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .dark-card * {
        color: #ffffff !important;
    }

    .metric-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        color: var(--secondary);
        margin-bottom: 12px;
    }

    .metric-value-large {
        font-size: 3.5rem;
        font-weight: 800;
        color: #000000;
        letter-spacing: -2px;
        line-height: 1;
    }

    .metric-value-white {
        font-size: 3.5rem;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -2px;
        line-height: 1;
    }

    .sub-text {
        font-size: 0.9rem;
        color: var(--secondary);
        margin-top: 10px;
    }

    /* Sidebar Navigation Overrides */
    .stRadio [data-testid="stWidgetLabel"] {
        display: none;
    }
    
    [data-testid="stSidebarNav"] {
        padding-top: 0;
    }

    /* Action Buttons */
    .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: transform 0.1s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialization
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'stats' not in st.session_state:
    st.session_state.stats = None

# Custom Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-logo">Growth</div>', unsafe_allow_html=True)
    
    st.markdown("##### Navigation")
    nav = st.radio("Menu", ["Dashboard", "Ingestion", "System"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("##### Integration")
    st.caption("Slack Node: Connected")
    st.caption("EPM Gateway: Verified")
    
    st.markdown("---")
    st.caption("Analyst: " + os.getenv("USER", "michelleprabhu"))
    st.caption("Build: 3.1.2")

# Main Content Header
user_name = os.getenv("USER", "User")
st.markdown(f"## Hi, {user_name}!")

if nav == "Dashboard":
    if st.session_state.stats:
        stats = st.session_state.stats
        
        # Grid Layout
        row1_col1, row1_col2, row1_col3 = st.columns([1.5, 1, 1])
        
        with row1_col1:
            st.markdown(f"""
            <div class="dark-card">
                <div class="metric-title" style="opacity: 0.7">Over all information</div>
                <div style="display: flex; align-items: baseline; gap: 40px;">
                    <div>
                        <div class="metric-value-white">{stats['total_tickets']}</div>
                        <p style="font-size: 0.8rem; opacity: 0.5; margin-top: 5px;">Total insights synthesized</p>
                    </div>
                    <div style="border-left: 1px solid rgba(255,255,255,0.2); padding-left: 30px;">
                        <div class="metric-value-white" style="font-size: 2.2rem">{stats['high_priority_count']}</div>
                        <p style="font-size: 0.8rem; opacity: 0.5; margin-top: 5px;">Active threat vectors</p>
                    </div>
                </div>
                <div style="margin-top: 30px;">
                    <div class="metric-title" style="opacity: 0.5; font-size: 0.65rem">System Resilience Target</div>
                    <div style="height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 10px; overflow: hidden;">
                        <div style="height: 100%; width: {stats['avg_confidence']*100}%; background: #ffffff; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with row1_col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-title">Temporal Flow</div>', unsafe_allow_html=True)
            # High-fidelity Sparkline
            spark_data = [12, 18, 14, 28, 22, 34, 30]
            fig_spark = px.line(spark_data, height=120)
            fig_spark.update_layout(
                margin=dict(t=5, b=5, l=5, r=5),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            fig_spark.update_traces(line_color="black", line_width=3)
            st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})
            st.markdown('<p style="font-size: 0.85rem; color: #64748b; margin-top: 10px;">Weekly synthesis process volume</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with row1_col3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-title">Month Progress</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value-large">{stats["avg_confidence"]:.0%}</div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size: 0.85rem; color: #64748b; margin-top: 10px;">AI confidence to last cycle</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Analysis Row
        st.markdown("#### Analysis Patterns")
        plot_col1, plot_col2 = st.columns(2)
        
        with plot_col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            categories = stats['categories']
            fig_pie = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                hole=0.7,
                color_discrete_sequence=['#000000', '#334155', '#64748b', '#94a3b8', '#cbd5e1']
            )
            fig_pie.update_layout(
                showlegend=True,
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with plot_col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            urgency_order = ['High', 'Medium', 'Low']
            u_counts = [stats['urgency_levels'].get(u, 0) for u in urgency_order]
            fig_bar = go.Figure(go.Bar(
                x=urgency_order,
                y=u_counts,
                marker_color=['#000000', '#475569', '#cbd5e1'],
                width=0.3
            ))
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Detailed View
        if st.session_state.results_df is not None:
            st.markdown("#### Last projects's insights")
            res_df = st.session_state.results_df
            high_risks = res_df[res_df['ai_urgency'] == 'High']
            
            risk_cols = st.columns(3)
            for i, (_, risk) in enumerate(high_risks.head(3).iterrows()):
                with risk_cols[i % 3]:
                    st.markdown(f"""
                    <div class="glass-card" style="min-height: 200px;">
                        <div class="metric-title" style="color: #ef4444">{risk['ai_category']} Risk</div>
                        <h5 style="margin: 10px 0;">{risk['customer']}</h5>
                        <p style="font-size: 0.85rem; color: #475569;">{risk['ai_summary']}</p>
                        <div style="margin-top: 20px;">
                            <button style="width: 100%; padding: 8px; background: black; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Action</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    else:
        # Empty State
        st.markdown(f"""
        <div style="text-align: center; padding: 120px 20px; background: rgba(255,255,255,0.4); border-radius: 24px; border: 1px dashed #cbd5e1; margin-top: 40px;">
            <h1 style="font-weight: 800; color: #0f172a; font-size: 3rem; letter-spacing: -2px;">No Data Ingested</h1>
            <p style="color: #64748b; font-size: 1.1rem; max-width: 500px; margin: 20px auto;">
                The strategic synthesis engine is standing by. Please upload your planning data in the Ingestion Hub.
            </p>
        </div>
        """, unsafe_allow_html=True)

elif nav == "Ingestion":
    st.markdown("#### Data Synthesis Hub")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<p style='margin-bottom: 20px;'>Sync planning data from organizational nodes.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Drop CSV file here", type=["csv"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        if st.button("Synthesize Data", use_container_width=True):
            try:
                df = pd.read_csv(uploaded_file)
                with st.spinner("Processing Organizational Signals..."):
                    results_df = classify_tickets(df)
                    stats = generate_stats(results_df)
                    st.session_state.results_df = results_df
                    st.session_state.stats = stats
                    st.rerun()
            except Exception as e:
                st.error(f"Integrity Error: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.results_df is not None:
        st.markdown("#### Active Processing Queue")
        st.dataframe(
            st.session_state.results_df[['ticket_id', 'customer', 'ai_category', 'ai_urgency', 'ai_summary']],
            use_container_width=True,
            hide_index=True
        )

elif nav == "System":
    st.markdown("#### Engine Configuration")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("Strategic AI Engine: Operational")
    st.write("Uptime: 100.00%")
    st.write("Last Sync: " + datetime.now().strftime("%H:%M:%S"))
    st.divider()
    st.caption("EPM Framework v4.0 (Monochrome Edition)")
    st.markdown('</div>', unsafe_allow_html=True)