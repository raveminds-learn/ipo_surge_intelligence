"""
Seed script — initialises LanceDB and DuckDB with historical IPO surge data.
Run once before starting the dashboard: python scripts/seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_lancedb, init_duckdb

if __name__ == "__main__":
    print("RaveMinds — IPO Surge Intelligence Agent")
    print("Seeding historical data...\n")

    print("Initialising LanceDB with historical IPO surge patterns...")
    db = init_lancedb()
    table = db.open_table("ipo_surge_patterns")
    count = len(table.to_pandas())
    print(f"✅ LanceDB ready — {count} historical events loaded")

    print("Initialising DuckDB schema...")
    con = init_duckdb()
    tables = con.execute("SHOW TABLES").fetchall()
    print(f"✅ DuckDB ready — {len(tables)} tables created: {[t[0] for t in tables]}")

    print("\n✅ Seed complete. Run: streamlit run ui/app.py")
