import json
from core.database import search_similar_events, save_prediction, init_lancedb, init_duckdb
from core.surge_simulator import run_full_simulation, generate_readiness_score
from core.llm_client import query_mistral_json, SYSTEM_PRE_IPO


def run_pre_ipo_analysis(company: str, expected_max_volume: float = 100) -> dict:
    init_lancedb()
    init_duckdb()

    query = f"{company} IPO high volume surge failure prediction capital markets"
    similar_events = search_similar_events(query, top_k=3)

    simulation = run_full_simulation(company)
    readiness = generate_readiness_score(simulation, similar_events)

    llm_analysis = _get_llm_analysis(company, expected_max_volume, simulation, similar_events)

    predictions = _extract_predictions(simulation)
    for pred in predictions:
        save_prediction(
            event_id=f"IPO_{company.upper()}",
            system=pred["system"],
            pred_volume=pred["predicted_failure_volume"],
            pred_type=pred["failure_type"],
            confidence=pred["confidence"]
        )

    recommendations = _generate_recommendations(simulation, llm_analysis)

    return {
        "company": company,
        "event_id": f"IPO_{company.upper()}",
        "expected_max_volume": expected_max_volume,
        "readiness": readiness,
        "simulation": simulation,
        "similar_events": similar_events,
        "llm_analysis": llm_analysis,
        "predictions": predictions,
        "recommendations": recommendations,
        "phase": "pre_ipo"
    }


def _get_llm_analysis(company: str, expected_volume: float, simulation: dict, similar_events: list) -> dict:
    sim_summary = {}
    for mult, scenario in simulation.get("scenarios", {}).items():
        failures = [
            s["system"] for s in scenario["systems"].values()
            if s["status"] in ["failure", "critical"]
        ]
        sim_summary[mult] = {
            "status": scenario["overall_status"],
            "failures": failures
        }

    historical_summary = [
        {
            "company": e.get("company"),
            "peak_volume": e.get("peak_volume"),
            "outcome": e.get("outcome"),
            "lessons": e.get("lessons")
        }
        for e in similar_events
    ]

    prompt = f"""
Analyse pre-IPO readiness for {company} IPO.
Expected peak volume: {expected_volume}x normal.

Simulation results:
{json.dumps(sim_summary, indent=2)}

Similar historical events:
{json.dumps(historical_summary, indent=2)}

Return JSON with:
{{
  "risk_summary": "2-3 sentence overall risk assessment",
  "top_failure_risks": [
    {{"system": "system_name", "risk": "description", "confidence": 0.0-1.0}}
  ],
  "critical_actions": ["action 1", "action 2", "action 3"],
  "confidence_note": "note about prediction confidence"
}}
"""
    result = query_mistral_json(prompt, SYSTEM_PRE_IPO)
    if "error" in result:
        return _fallback_llm_analysis(company, sim_summary)
    return result


def _fallback_llm_analysis(company: str, sim_summary: dict) -> dict:
    failure_systems = set()
    for scenario in sim_summary.values():
        failure_systems.update(scenario.get("failures", []))

    return {
        "risk_summary": f"Based on simulation, {company} IPO faces elevated risk across {len(failure_systems)} systems at high volume.",
        "top_failure_risks": [
            {"system": s, "risk": "Predicted to fail under surge conditions", "confidence": 0.75}
            for s in failure_systems
        ],
        "critical_actions": [
            "Scale all systems to 2x capacity before market open",
            "Pre-warm Kafka consumer groups",
            "Enable circuit breakers on all critical paths"
        ],
        "confidence_note": "Fallback analysis — LLM unavailable. Based on simulation data only."
    }


def _extract_predictions(simulation: dict) -> list:
    predictions = []
    for mult_str, scenario in simulation.get("scenarios", {}).items():
        mult = int(mult_str.replace("x", ""))
        for sys_name, sys_data in scenario["systems"].items():
            if sys_data["status"] == "failure":
                predictions.append({
                    "system": sys_name,
                    "predicted_failure_volume": mult,
                    "failure_type": sys_data.get("failure_type", "unknown"),
                    "confidence": sys_data.get("confidence", 0.8),
                    "time_to_fail_minutes": sys_data.get("time_to_failure_minutes")
                })
                break
    return predictions


def _generate_recommendations(simulation: dict, llm_analysis: dict) -> list:
    recs = []
    scenarios = simulation.get("scenarios", {})

    if scenarios.get("10x", {}).get("overall_status") != "stable":
        recs.append({
            "priority": "critical",
            "action": "System not ready for even 10x volume — immediate infrastructure review required",
            "system": "all"
        })

    for sys_name, sys_data in scenarios.get("50x", {}).get("systems", {}).items():
        if sys_data["status"] in ["failure", "critical"]:
            recs.append({
                "priority": "high",
                "action": f"Pre-scale {sys_data.get('display_name', sys_name)} — failure predicted at 50x",
                "system": sys_name
            })

    for action in llm_analysis.get("critical_actions", []):
        recs.append({
            "priority": "high",
            "action": action,
            "system": "ai_recommended"
        })

    return recs[:6]
