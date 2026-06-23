import streamlit as st
import plotly.graph_objects as go
from agents.post_ipo_agent import run_post_ipo_analysis


def render_post_ipo(event_id: str, company: str):
    st.subheader("Post-IPO Event Analysis")

    peak_volume = st.number_input("Peak Volume Reached (x normal)", min_value=1.0,
                                   max_value=200.0, value=45.0, step=1.0)

    if st.button("📊 Generate Post-Event Report", type="primary"):
        with st.spinner("Auditing predictions and generating report..."):
            result = run_post_ipo_analysis(
                event_id=event_id,
                company=company,
                peak_volume=peak_volume
            )
        _render_post_result(result)


def _render_post_result(result: dict):
    accuracy = result.get("accuracy", {})
    incidents = result.get("incident_summary", {})
    lessons = result.get("lessons", [])
    llm_report = result.get("llm_report", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Peak Volume", f"{result.get('peak_volume', 0):.0f}x")
    with col2:
        acc_pct = accuracy.get("accuracy_pct", 0)
        st.metric("Prediction Accuracy", f"{acc_pct}%")
    with col3:
        st.metric("Critical Incidents", incidents.get("critical_count", 0))
    with col4:
        grade = llm_report.get("overall_grade", "N/A")
        st.metric("Event Grade", grade)

    st.markdown("---")
    _render_accuracy_chart(accuracy)
    st.markdown("---")
    _render_llm_report(llm_report, result.get("company", ""))
    st.markdown("---")
    _render_lessons(lessons)
    st.markdown("---")
    _render_memory_update(result)


def _render_accuracy_chart(accuracy: dict):
    st.subheader("Prediction vs Reality")
    details = accuracy.get("details", [])

    if not details:
        st.info("No prediction data available for this event.")
        return

    systems = [d["system"].replace("_", " ").title() for d in details]
    correct = [1 if d["was_correct"] else 0 for d in details]
    colors = ["#10B981" if c else "#EF4444" for c in correct]

    fig = go.Figure(go.Bar(
        x=systems,
        y=[1] * len(systems),
        marker_color=colors,
        text=["✅ Correct" if c else "❌ Missed" for c in correct],
        textposition="inside"
    ))
    fig.update_layout(
        title="Prediction Accuracy by System",
        yaxis=dict(showticklabels=False, showgrid=False),
        height=250,
        margin=dict(t=40, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_llm_report(llm_report: dict, company: str):
    st.subheader("Event Report")

    if not llm_report:
        st.info("Report unavailable.")
        return

    with st.expander("📋 Executive Summary", expanded=True):
        st.write(llm_report.get("executive_summary", ""))

    with st.expander("🔧 Ops Technical Summary"):
        st.write(llm_report.get("ops_summary", ""))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top Lessons:**")
        for lesson in llm_report.get("top_lessons", []):
            st.markdown(f"- {lesson}")
    with col2:
        st.markdown("**Next Event Recommendations:**")
        for rec in llm_report.get("next_event_recommendations", []):
            st.markdown(f"- {rec}")


def _render_lessons(lessons: list):
    st.subheader("Lessons Learned")
    type_icons = {
        "success": "✅", "partial": "⚠️",
        "improvement": "🔧", "gap": "❌", "memory": "🧠"
    }
    for lesson in lessons:
        icon = type_icons.get(lesson.get("type", ""), "•")
        st.markdown(f"{icon} {lesson.get('lesson', '')}")


def _render_memory_update(result: dict):
    st.subheader("LanceDB Memory Update")
    if result.get("memory_updated"):
        st.success(f"✅ {result.get('company', '')} IPO surge pattern saved to LanceDB. Future simulations will reference this event.")
        st.caption("Next IPO analysis will automatically include this event as a historical precedent.")
    else:
        st.warning("Memory update pending.")
