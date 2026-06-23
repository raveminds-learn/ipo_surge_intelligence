import json
import uuid
from datetime import datetime
from core.database import get_duckdb, audit_predictions, get_surge_history, search_similar_events
from core.llm_client import query_mistral_json, SYSTEM_POST_IPO


def run_post_ipo_analysis(event_id: str, company: str, peak_volume: float) -> dict:
    predictions_df = audit_predictions(event_id)
    surge_history_df = get_surge_history(event_id)

    accuracy = _calculate_prediction_accuracy(predictions_df, surge_history_df)
    incident_summary = _summarise_incidents(surge_history_df)
    lessons = _extract_lessons(accuracy, incident_summary, company)
    llm_report = _generate_llm_report(company, peak_volume, accuracy, incident_summary, lessons)
    _update_lancedb_memory(event_id, company, peak_volume, accuracy, lessons)

    return {
        "event_id": event_id,
        "company": company,
        "peak_volume": peak_volume,
        "accuracy": accuracy,
        "incident_summary": incident_summary,
        "lessons": lessons,
        "llm_report": llm_report,
        "memory_updated": True,
        "phase": "post_ipo",
        "generated_at": datetime.now().isoformat()
    }


def _calculate_prediction_accuracy(predictions_df, history_df) -> dict:
    if predictions_df.empty:
        return {
            "total_predictions": 0,
            "correct": 0,
            "accuracy_pct": 0,
            "details": []
        }

    total = len(predictions_df)
    correct = 0
    details = []

    for _, pred in predictions_df.iterrows():
        system = pred.get("system_name", "")
        pred_volume = pred.get("predicted_failure_volume", 0)

        actual_failures = history_df[
            (history_df["system_name"] == system) &
            (history_df["status"] == "critical")
        ]

        was_correct = not actual_failures.empty
        if was_correct:
            correct += 1

        details.append({
            "system": system,
            "predicted_failure_volume": pred_volume,
            "predicted_type": pred.get("predicted_failure_type", "unknown"),
            "was_correct": was_correct,
            "confidence": pred.get("confidence", 0.8)
        })

    return {
        "total_predictions": total,
        "correct": correct,
        "accuracy_pct": round((correct / total * 100) if total > 0 else 0, 1),
        "details": details
    }


def _summarise_incidents(history_df) -> dict:
    if history_df.empty:
        return {"total_metrics_logged": 0, "critical_count": 0, "warning_count": 0, "systems_affected": []}

    critical = history_df[history_df["status"] == "critical"]
    warning = history_df[history_df["status"] == "warning"]

    return {
        "total_metrics_logged": len(history_df),
        "critical_count": len(critical),
        "warning_count": len(warning),
        "systems_affected": history_df["system_name"].unique().tolist(),
        "peak_volume_recorded": history_df["volume_multiplier"].max() if not history_df.empty else 0,
        "duration_datapoints": len(history_df)
    }


def _extract_lessons(accuracy: dict, incidents: dict, company: str) -> list:
    lessons = []

    if accuracy["accuracy_pct"] >= 80:
        lessons.append({
            "type": "success",
            "lesson": f"Pre-event simulation accurately predicted {accuracy['correct']} of {accuracy['total_predictions']} failure points."
        })
    elif accuracy["accuracy_pct"] >= 50:
        lessons.append({
            "type": "partial",
            "lesson": "Simulation was partially accurate. Refine volume threshold models for next event."
        })
    else:
        lessons.append({
            "type": "improvement",
            "lesson": "Prediction accuracy was low. Historical patterns may not have covered this volume range."
        })

    missed = [d for d in accuracy.get("details", []) if not d["was_correct"]]
    for miss in missed:
        lessons.append({
            "type": "gap",
            "lesson": f"{miss['system']} failure was not correctly predicted. Update baseline for this system."
        })

    if incidents.get("critical_count", 0) == 0:
        lessons.append({
            "type": "success",
            "lesson": "No critical incidents during live surge. Dynamic threshold adaptation was effective."
        })

    lessons.append({
        "type": "memory",
        "lesson": f"{company} IPO surge pattern saved to LanceDB. Future simulations will reference this event."
    })

    return lessons


def _generate_llm_report(company: str, peak_volume: float,
                          accuracy: dict, incidents: dict, lessons: list) -> dict:
    prompt = f"""
Generate a post-IPO event report for {company} IPO.

Peak volume reached: {peak_volume}x
Prediction accuracy: {accuracy['accuracy_pct']}%
Critical incidents: {incidents.get('critical_count', 0)}
Systems affected: {incidents.get('systems_affected', [])}

Lessons extracted:
{json.dumps([l['lesson'] for l in lessons], indent=2)}

Return JSON:
{{
  "executive_summary": "3-4 sentence summary for management",
  "ops_summary": "2-3 sentence technical summary for ops team",
  "top_lessons": ["lesson 1", "lesson 2", "lesson 3"],
  "next_event_recommendations": ["rec 1", "rec 2", "rec 3"],
  "overall_grade": "A/B/C/D based on how well the event was handled"
}}
"""
    result = query_mistral_json(prompt, SYSTEM_POST_IPO)
    if "error" in result:
        grade = "A" if accuracy["accuracy_pct"] >= 80 else "B" if accuracy["accuracy_pct"] >= 60 else "C"
        return {
            "executive_summary": f"{company} IPO processed at peak {peak_volume}x volume. Prediction accuracy was {accuracy['accuracy_pct']}%.",
            "ops_summary": f"{incidents.get('critical_count', 0)} critical incidents recorded. Systems performed within adaptive thresholds.",
            "top_lessons": [l["lesson"] for l in lessons[:3]],
            "next_event_recommendations": [
                "Update surge simulation baselines with this event data",
                "Review threshold adaptation parameters",
                "Pre-scale identified bottleneck systems earlier"
            ],
            "overall_grade": grade
        }
    return result


def _update_lancedb_memory(event_id: str, company: str, peak_volume: float,
                            accuracy: dict, lessons: list):
    import lancedb
    from sentence_transformers import SentenceTransformer
    from pathlib import Path

    BASE_DIR = Path(__file__).parent.parent
    db = lancedb.connect(str(BASE_DIR / "data" / "lancedb"))
    model = SentenceTransformer("all-MiniLM-L6-v2")

    lesson_text = " ".join([l["lesson"] for l in lessons])
    text = (
        f"{company} IPO surge event. Peak volume {peak_volume}x. "
        f"Prediction accuracy {accuracy['accuracy_pct']}%. {lesson_text}"
    )
    embedding = model.encode(text).tolist()

    new_record = {
        "event_id": event_id,
        "company": company,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "peak_volume": peak_volume,
        "outcome": f"Processed — accuracy {accuracy['accuracy_pct']}%",
        "lessons": lesson_text,
        "failures_json": "[]",
        "actions_json": "[]",
        "readiness_score": int(accuracy["accuracy_pct"]),
        "text": text,
        "vector": embedding
    }

    if "ipo_surge_patterns" in db.table_names():
        table = db.open_table("ipo_surge_patterns")
        table.add([new_record])
