import streamlit as st
import plotly.graph_objects as go
import time
from agents.live_surge_agent import run_live_analysis, generate_live_metrics


def render_live_surge(event_id: str):
    st.subheader("Live Surge Monitor")

    col1, col2 = st.columns([2, 1])
    with col1:
        volume = st.slider("Simulate Current Volume Multiplier", 1.0, 120.0, 10.0, 0.5)
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

    if st.button("📡 Analyse Current Surge", type="primary") or auto_refresh:
        with st.spinner("Analysing live conditions..."):
            result = run_live_analysis(event_id=event_id, volume_multiplier=volume)
        _render_live_result(result)

        if auto_refresh:
            time.sleep(5)
            st.rerun()


def _render_live_result(result: dict):
    overall = result.get("overall_status", "stable")
    volume = result.get("volume_multiplier", 0)
    band = result.get("volume_band", "normal")
    confidence = result.get("confidence", 1.0)

    status_colors = {
        "stable": "🟢", "watch": "🟡",
        "elevated": "🟠", "high": "🔴", "critical": "🚨"
    }

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Volume", f"{volume:.0f}x")
    with col2:
        st.metric("Volume Band", band.title())
    with col3:
        icon = status_colors.get(overall, "⚪")
        st.metric("Overall Status", f"{icon} {overall.title()}")
    with col4:
        st.metric("AI Confidence", f"{int(confidence * 100)}%")

    if confidence < 0.7:
        st.warning(f"⚠️ Confidence decay active — volume ({volume:.0f}x) exceeds historical data range. Predictions less reliable.")

    st.markdown("---")

    thresholds = result.get("thresholds", {})
    st.caption(f"🔧 Adaptive thresholds active: Kafka lag limit → {thresholds.get('kafka_lag_threshold', 'N/A'):,} msgs | Latency limit → {thresholds.get('latency_threshold_ms', 'N/A')}ms")

    st.markdown("---")
    _render_system_status(result)
    st.markdown("---")
    _render_triage(result)

    llm_summary = result.get("llm_summary")
    if llm_summary:
        st.markdown("---")
        _render_llm_situational(llm_summary)


def _render_system_status(result: dict):
    st.subheader("System Status")
    classifications = result.get("classifications", [])

    status_display = {
        "genuine_failure": ("🔴", "Genuine Failure"),
        "expected_surge_behaviour": ("🟢", "Expected Surge"),
        "investigate": ("🟡", "Investigate")
    }

    if not classifications:
        st.info("No system data available.")
        return

    cols = st.columns(len(classifications))
    for i, cls in enumerate(classifications):
        with cols[i % len(cols)]:
            classification = cls.get("classification", "investigate")
            icon, label = status_display.get(classification, ("⚪", "Unknown"))
            st.markdown(f"**{icon} {cls.get('system', '').replace('_', ' ').title()}**")
            st.caption(label)
            st.caption(cls.get("explanation", "")[:80])


def _render_triage(result: dict):
    st.subheader("Ops Triage — Fix in This Order")
    triage = result.get("triage", [])

    if not triage:
        st.success("✅ No active issues requiring triage.")
        return

    for item in triage:
        priority = item.get("priority_rank", 0)
        status = item.get("status", "")
        color = "🔴" if status == "critical" else "🟠"

        with st.expander(f"{color} Priority {priority} — {item.get('display_name', '')} ({status.title()})", expanded=priority <= 2):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Action:** {item.get('action', '')}")
                st.write(f"**Est. fix time:** {item.get('estimated_fix_minutes', '?')} minutes")
            with col2:
                st.write(f"**Volume band:** {item.get('volume_band', '').title()}")
                st.write(f"**Threshold adapted:** {'Yes' if item.get('threshold_adapted') else 'No'}")
                if item.get("escalate"):
                    st.error("⚡ Escalation recommended")


def _render_llm_situational(llm_summary: dict):
    st.subheader("AI Situational Summary")
    st.info(llm_summary.get("situation", ""))
    st.error(f"⚡ Immediate action: {llm_summary.get('immediate_action', '')}")
    est = llm_summary.get("estimated_stabilisation_minutes")
    if est:
        st.caption(f"⏱️ Estimated stabilisation: {est} minutes")
