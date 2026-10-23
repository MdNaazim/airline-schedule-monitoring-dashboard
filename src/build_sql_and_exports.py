"""Load data into SQLite, run the SQL KPI queries, export CSVs for Power BI.
Run: python src/build_sql_and_exports.py
"""
import re
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "outputs" / "airline.db"
db_path.parent.mkdir(exist_ok=True)
exp = ROOT / "powerbi_exports"
exp.mkdir(exist_ok=True)

con = sqlite3.connect(db_path)
con.executescript((ROOT / "sql" / "schema.sql").read_text())
pd.read_csv(ROOT / "data" / "master_schedule.csv").to_sql("master_schedule", con, if_exists="append", index=False)
pd.read_csv(ROOT / "data" / "distributed_output.csv").to_sql("distributed_output", con, if_exists="append", index=False)
pd.read_csv(ROOT / "outputs" / "parity_post_publish.csv").to_sql("parity_post_publish", con, if_exists="append", index=False)

blocks = re.split(r"-- name: (\w+)\n", (ROOT / "sql" / "queries.sql").read_text())[1:]
for name, sql in zip(blocks[::2], blocks[1::2]):
    df = pd.read_sql_query(sql, con)
    df.to_csv(exp / f"{name}.csv", index=False)
    print(f"--- {name} ({len(df)} rows) ---\n{df.head(8).to_string(index=False)}\n")

pd.read_sql_query("SELECT * FROM v_schedule_status", con).to_csv(exp / "fact_schedule_status.csv", index=False)
pd.read_csv(ROOT / "outputs" / "parity_post_publish.csv").to_csv(exp / "parity_discrepancies.csv", index=False)
con.close()
