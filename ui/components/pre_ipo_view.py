import streamlit as st
import plotly.graph_objects as go
import json


def render_pre_ipo(result: dict):
    if not result:
        st.info("Run Pre-IPO analysis to see results.")
        return

    readiness = result.get("readiness", {})
    simulation = result.get("simulation", {})
    recommendations = result.get("recommendations", [])
    similar_events = result.get("similar_events", [])
    llm_analysis = result.get("llm_analysis", {})

    score = readiness.get("score", 0)
    risk_level = readiness.get("risk_level", "Unknown")

    col1, col2, col3 = st.columns(3)
    with col1:
        color = {"Low": "normal", "Medium": "normal", "High": "inverse", "Critical": "inverse"}.get(risk_level, "normal")
        st.metric("Readiness Score", f"{score} / 100")
    with col2:
        st.metric("Risk Level", risk_level)
    with col3:
        safe_mult = simulation.get("max_safe_multiplier", 0)
        st.metric("Max Safe Volume", f"{safe_mult}x")

    st.markdown("---")
    _render_readiness_gauge(score)
    st.markdown("---")
    _render_simulation_results(simulation)
    st.markdown("---")
    _render_llm_analysis(llm_analysis)
    st.markdown("---")
    _render_recommendations(recommendations)
    st.markdown("---")
    _render_similar_events(similar_events)


def _render_readiness_gauge(score: int):
    st.subheader("Readiness Gauge")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Pre-IPO Readiness Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#2563EB"},
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 60], "color": "#FEF3C7"},
                {"range": [60, 80], "color": "#D1FAE5"},
                {"range": [80, 100], "color": "#A7F3D0"}
            ],
            "threshold": {
                "line": {"color": "#1E40AF", "width": 3},
                "thickness": 0.75,
                "value": score
            }
        }
    ))
    fig.update_layout(height=280, margin=dict(t=30, b=10, l=20, r=20),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#1E293B"))
    st.plotly_chart(fig, use_container_width=True)


def _render_simulation_results(simulation: dict):
    st.subheader("Surge Simulation Results")
    scenarios = simulation.get("scenarios", {})

    status_icons = {
        "stable": "✅", "elevated": "⚠️",
        "warning": "🟠", "critical": "🔴"
    }

    cols = st.columns(3)
    for i, (mult, scenario) in enumerate(scenarios.items()):
        with cols[i]:
            icon = status_icons.get(scenario["overall_status"], "❓")
            st.markdown(f"**{icon} {mult} Volume**")
            st.caption(f"Status: {scenario['overall_status'].title()}")
            st.caption(f"Failures: {scenario['failure_count']}")
            for sys_name, sys_data in scenario["systems"].items():
                status = sys_data["status"]
                if status in ["failure", "critical"]:
                    st.caption(f"⚠️ {sys_data.get('display_name', sys_name)}: {status}")


def _render_llm_analysis(llm_analysis: dict):
    st.subheader("AI Risk Analysis")
    if not llm_analysis or "error" in llm_analysis:
        st.warning("LLM analysis unavailable — running in fallback mode.")
        return

    st.info(llm_analysis.get("risk_summary", ""))

    risks = llm_analysis.get("top_failure_risks", [])
    if risks:
        st.markdown("**Top Failure Risks:**")
        for risk in risks:
            conf = risk.get("confidence", 0)
            conf_pct = int(conf * 100)
            st.markdown(f"- **{risk.get('system', '')}**: {risk.get('risk', '')} *(confidence: {conf_pct}%)*")

    note = llm_analysis.get("confidence_note", "")
    if note:
        st.caption(f"ℹ️ {note}")


def _render_recommendations(recommendations: list):
    st.subheader("Pre-Event Recommendations")
    if not recommendations:
        st.success("No critical recommendations — system appears ready.")
        return

    priority_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡"}
    for rec in recommendations:
        priority = rec.get("priority", "medium")
        icon = priority_colors.get(priority, "🔵")
        st.markdown(f"{icon} **{priority.title()}:** {rec.get('action', '')}")


def _render_similar_events(similar_events: list):
    st.subheader("Historical Precedents")
    if not similar_events:
        st.info("No similar historical events found.")
        return

    for event in similar_events:
        with st.expander(f"📋 {event.get('company', 'Unknown')} — Peak {event.get('peak_volume', '?')}x"):
            st.write(f"**Outcome:** {event.get('outcome', '')}")
            st.write(f"**Lessons:** {event.get('lessons', '')}")
