import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from pathlib import Path

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPO Surge Intelligence — RaveMinds",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean white background */
    .stApp { background-color: #F8FAFC; }
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }

    /* Header bar */
    .rm-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%);
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .rm-header-text { color: white; }
    .rm-header-title { font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.3px; }
    .rm-header-sub { font-size: 13px; opacity: 0.85; margin: 2px 0 0; }

    /* Badges */
    .rm-badges { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
    .rm-badge {
        font-size: 11px; padding: 3px 10px;
        border-radius: 20px; font-weight: 500;
        background: rgba(255,255,255,0.18); color: white;
        border: 1px solid rgba(255,255,255,0.3);
    }

    /* Phase tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #F1F5F9;
        padding: 4px; border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; font-size: 14px;
        padding: 8px 20px; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #F1F5F9; }
    .sidebar-section {
        background: white; border-radius: 10px;
        padding: 14px; margin-bottom: 12px;
        border: 1px solid #E2E8F0;
    }
    .sidebar-label { font-size: 11px; font-weight: 600;
        color: #64748B; text-transform: uppercase;
        letter-spacing: 0.05em; margin-bottom: 6px; }

    /* Status indicators */
    .status-stable { color: #10B981; font-weight: 600; }
    .status-warning { color: #F59E0B; font-weight: 600; }
    .status-critical { color: #EF4444; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Logo helper ───────────────────────────────────────────────────────────────
def get_logo_b64() -> str:
    logo_path = Path(__file__).parent / "assets" / "rm_logo.png"
    if logo_path.exists():
        import base64
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# ── Header ────────────────────────────────────────────────────────────────────
logo_b64 = get_logo_b64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="48" style="border-radius:50%;">' if logo_b64 else "🚀"

st.markdown(f"""
<div class="rm-header">
    <div>{logo_html}</div>
    <div class="rm-header-text">
        <p class="rm-header-title">IPO Surge Intelligence Agent</p>
        <p class="rm-header-sub">RaveMinds Series 2 · Project 3 · Predictive + Adaptive AI</p>
        <div class="rm-badges">
            <span class="rm-badge">🤖 Mistral 7B</span>
            <span class="rm-badge">🗄️ LanceDB</span>
            <span class="rm-badge">📊 DuckDB</span>
            <span class="rm-badge">🔗 LangGraph</span>
            <span class="rm-badge">💰 $0 API Cost</span>
            <span class="rm-badge">🔒 100% Local</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(f"""
        <div style="text-align:center; padding: 12px 0 16px;">
            <img src="data:image/png;base64,{logo_b64}" width="56" style="border-radius:50%;">
            <p style="font-size:13px; font-weight:600; color:#1E293B; margin:8px 0 2px;">RaveMinds</p>
            <p style="font-size:11px; color:#64748B; margin:0;">Series 2 · Project 3</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">IPO Configuration</p>', unsafe_allow_html=True)
    company = st.text_input("Company Name", value="SpaceX", help="Enter the IPO company name")
    event_id = f"IPO_{company.upper().replace(' ', '_')}"
    expected_volume = st.slider("Expected Peak Volume (x)", 10, 150, 100)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">Stack</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12px; color:#475569; line-height:2;">
        🤖 <b>LLM:</b> Mistral 7B via Ollama<br>
        🗄️ <b>Vector:</b> LanceDB<br>
        📊 <b>Analytics:</b> DuckDB<br>
        🔗 <b>Orchestration:</b> LangGraph<br>
        📐 <b>Embeddings:</b> all-MiniLM-L6-v2
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">Series 2 Progress</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12px; color:#475569; line-height:2;">
        ✅ Trade Compliance Copilot<br>
        ✅ Settlement Alert Agent<br>
        🚀 IPO Surge Intelligence
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-label">About</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px; color:#64748B; line-height:1.6;">
        Predictive + Adaptive AI for<br>high-volume IPO events.<br><br>
        Three phases: Pre-IPO preparation,<br>Live surge monitoring,<br>
        Post-IPO memory update.<br><br>
        <a href="https://raveminds.ai" style="color:#2563EB;">raveminds.ai</a>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Main tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🔍 Pre-IPO Preparation",
    "📡 Live Surge Monitor",
    "📊 Post-IPO Report"
])

with tab1:
    st.markdown(f"""
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
        <b style="color:#1D4ED8;">Phase 1 — Pre-IPO Preparation</b>
        <span style="color:#3B82F6; font-size:13px; margin-left:8px;">
            Simulate surge scenarios · Predict failure points · Generate readiness score
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"🚀 Run Pre-IPO Analysis for {company}", type="primary", key="run_pre"):
        with st.spinner(f"Simulating {company} IPO surge scenarios..."):
            from agents.pre_ipo_agent import run_pre_ipo_analysis
            result = run_pre_ipo_analysis(company=company, expected_max_volume=expected_volume)
            st.session_state["pre_ipo_result"] = result
            st.session_state["event_id"] = event_id

    if "pre_ipo_result" in st.session_state:
        from ui.components.pre_ipo_view import render_pre_ipo
        render_pre_ipo(st.session_state["pre_ipo_result"])

with tab2:
    st.markdown(f"""
    <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
        <b style="color:#15803D;">Phase 2 — Live Surge Monitor</b>
        <span style="color:#16A34A; font-size:13px; margin-left:8px;">
            Adaptive thresholds · Real-time triage · Genuine vs expected surge classification
        </span>
    </div>
    """, unsafe_allow_html=True)

    from ui.components.live_surge_view import render_live_surge
    render_live_surge(event_id=event_id)

with tab3:
    st.markdown(f"""
    <div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
        <b style="color:#C2410C;">Phase 3 — Post-IPO Analysis</b>
        <span style="color:#EA580C; font-size:13px; margin-left:8px;">
            Prediction audit · Lessons learned · LanceDB memory update
        </span>
    </div>
    """, unsafe_allow_html=True)

    from ui.components.post_ipo_view import render_post_ipo
    render_post_ipo(event_id=event_id, company=company)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:8px; font-size:12px; color:#94A3B8;">
    RaveMinds Series 2 · IPO Surge Intelligence Agent · Mistral 7B via Ollama · $0 API Cost · 100% Local
    · <a href="https://raveminds.ai" style="color:#2563EB;">raveminds.ai</a>
</div>
""", unsafe_allow_html=True)
