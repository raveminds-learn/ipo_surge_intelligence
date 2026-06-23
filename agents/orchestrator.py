import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.pre_ipo_agent import run_pre_ipo_analysis
from agents.live_surge_agent import run_live_analysis, generate_live_metrics
from agents.post_ipo_agent import run_post_ipo_analysis


class SurgeState(TypedDict):
    company: str
    event_id: str
    phase: str
    expected_max_volume: float
    current_volume: float
    pre_ipo_result: Optional[dict]
    live_result: Optional[dict]
    post_ipo_result: Optional[dict]
    error: Optional[str]


def pre_ipo_node(state: SurgeState) -> SurgeState:
    try:
        result = run_pre_ipo_analysis(
            company=state["company"],
            expected_max_volume=state["expected_max_volume"]
        )
        return {**state, "pre_ipo_result": result, "phase": "pre_ipo_complete"}
    except Exception as e:
        return {**state, "error": str(e), "phase": "error"}


def live_surge_node(state: SurgeState) -> SurgeState:
    try:
        metrics = generate_live_metrics(state["current_volume"])
        result = run_live_analysis(
            event_id=state["event_id"],
            volume_multiplier=state["current_volume"],
            metrics=metrics
        )
        return {**state, "live_result": result, "phase": "live_complete"}
    except Exception as e:
        return {**state, "error": str(e), "phase": "error"}


def post_ipo_node(state: SurgeState) -> SurgeState:
    try:
        peak_volume = state.get("current_volume", 0)
        if state.get("live_result"):
            peak_volume = state["live_result"].get("volume_multiplier", peak_volume)

        result = run_post_ipo_analysis(
            event_id=state["event_id"],
            company=state["company"],
            peak_volume=peak_volume
        )
        return {**state, "post_ipo_result": result, "phase": "post_ipo_complete"}
    except Exception as e:
        return {**state, "error": str(e), "phase": "error"}


def route_phase(state: SurgeState) -> str:
    phase = state.get("phase", "")
    if phase == "pre_ipo_complete":
        return "live_surge"
    elif phase == "live_complete":
        return "post_ipo"
    elif phase in ["post_ipo_complete", "error"]:
        return END
    return END


def build_surge_graph():
    graph = StateGraph(SurgeState)
    graph.add_node("pre_ipo", pre_ipo_node)
    graph.add_node("live_surge", live_surge_node)
    graph.add_node("post_ipo", post_ipo_node)

    graph.set_entry_point("pre_ipo")
    graph.add_conditional_edges("pre_ipo", route_phase, {
        "live_surge": "live_surge", END: END
    })
    graph.add_conditional_edges("live_surge", route_phase, {
        "post_ipo": "post_ipo", END: END
    })
    graph.add_conditional_edges("post_ipo", route_phase, {END: END})

    return graph.compile()


def run_full_pipeline(company: str, expected_max_volume: float = 100,
                      current_volume: float = 45) -> dict:
    graph = build_surge_graph()
    initial_state = SurgeState(
        company=company,
        event_id=f"IPO_{company.upper()}",
        phase="start",
        expected_max_volume=expected_max_volume,
        current_volume=current_volume,
        pre_ipo_result=None,
        live_result=None,
        post_ipo_result=None,
        error=None
    )
    final_state = graph.invoke(initial_state)
    return final_state
