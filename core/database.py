import json
import os
import numpy as np
import lancedb
import duckdb
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LANCEDB_PATH = str(BASE_DIR / "data" / "lancedb")
DUCKDB_PATH = str(BASE_DIR / "data" / "surge_events.duckdb")
HISTORICAL_PATH = str(BASE_DIR / "data" / "historical_events.json")

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_lancedb():
    return lancedb.connect(LANCEDB_PATH)


def get_duckdb():
    return duckdb.connect(DUCKDB_PATH)


def init_lancedb():
    db = get_lancedb()
    model = get_embedding_model()

    with open(HISTORICAL_PATH) as f:
        events = json.load(f)

    records = []
    for e in events:
        text = (
            f"{e['company']} IPO {e['date']}. "
            f"Peak volume {e['peak_volume_multiplier']}x. "
            f"Failures: {', '.join(f['system'] for f in e['failures']) if e['failures'] else 'none'}. "
            f"Outcome: {e['actual_outcome']}. Lessons: {e['lessons']}"
        )
        embedding = model.encode(text).tolist()
        records.append({
            "event_id": e["event_id"],
            "company": e["company"],
            "date": e["date"],
            "peak_volume": e["peak_volume_multiplier"],
            "outcome": e["actual_outcome"],
            "lessons": e["lessons"],
            "failures_json": json.dumps(e["failures"]),
            "actions_json": json.dumps(e["resolution_actions"]),
            "readiness_score": e["readiness_score_pre"],
            "text": text,
            "vector": embedding
        })

    if "ipo_surge_patterns" in db.table_names():
        db.drop_table("ipo_surge_patterns")

    db.create_table("ipo_surge_patterns", data=records)
    return db


def init_duckdb():
    con = get_duckdb()
    con.execute("""
        CREATE TABLE IF NOT EXISTS surge_events (
            event_id VARCHAR,
            company VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            phase VARCHAR,
            volume_multiplier DOUBLE,
            system_name VARCHAR,
            metric_name VARCHAR,
            metric_value DOUBLE,
            threshold_value DOUBLE,
            status VARCHAR,
            notes VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id VARCHAR,
            event_id VARCHAR,
            system_name VARCHAR,
            predicted_failure_volume DOUBLE,
            predicted_failure_type VARCHAR,
            confidence DOUBLE,
            actual_failure_volume DOUBLE,
            was_correct BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS triage_log (
            triage_id VARCHAR,
            event_id VARCHAR,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER,
            system_name VARCHAR,
            issue VARCHAR,
            recommended_action VARCHAR,
            status VARCHAR
        )
    """)
    return con


def search_similar_events(query: str, top_k: int = 3) -> list:
    db = get_lancedb()
    model = get_embedding_model()

    if "ipo_surge_patterns" not in db.table_names():
        init_lancedb()

    table = db.open_table("ipo_surge_patterns")
    query_vec = model.encode(query).tolist()
    results = table.search(query_vec).limit(top_k).to_list()
    return results


def log_surge_metric(event_id: str, phase: str, volume: float,
                     system: str, metric: str, value: float,
                     threshold: float, status: str, notes: str = ""):
    con = get_duckdb()
    con.execute("""
        INSERT INTO surge_events
        (event_id, phase, volume_multiplier, system_name, metric_name,
         metric_value, threshold_value, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [event_id, phase, volume, system, metric, value, threshold, status, notes])


def get_surge_history(event_id: str) -> pd.DataFrame:
    con = get_duckdb()
    return con.execute("""
        SELECT * FROM surge_events
        WHERE event_id = ?
        ORDER BY timestamp
    """, [event_id]).df()


def save_prediction(event_id: str, system: str, pred_volume: float,
                    pred_type: str, confidence: float):
    import uuid
    con = get_duckdb()
    con.execute("""
        INSERT INTO predictions
        (prediction_id, event_id, system_name, predicted_failure_volume,
         predicted_failure_type, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [str(uuid.uuid4()), event_id, system, pred_volume, pred_type, confidence])


def audit_predictions(event_id: str) -> pd.DataFrame:
    con = get_duckdb()
    return con.execute("""
        SELECT * FROM predictions WHERE event_id = ?
    """, [event_id]).df()
