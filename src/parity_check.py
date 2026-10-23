"""Automated parity checks: master data vs staged (pre-publish) and vs distributed (post-publish).

Flags field-level mismatches and missing records. Run it on every publish batch
(or schedule it with cron / Task Scheduler).
Run: python src/parity_check.py
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["carrier", "flight_no", "origin", "destination", "sched_dep", "sched_arr", "aircraft_type"]


def parity_check(master: pd.DataFrame, other: pd.DataFrame, stage: str) -> pd.DataFrame:
    """Return one row per discrepancy."""
    merged = master.merge(other, on="schedule_id", how="left", suffixes=("", "_out"), indicator=True)
    rows = []
    missing = merged[merged["_merge"] == "left_only"]
    for r in missing.itertuples():
        rows.append((stage, r.schedule_id, r.schedule_date, r.carrier, "RECORD", "present", "absent", "MISSING_IN_OUTPUT"))
    both = merged[merged["_merge"] == "both"]
    for f in FIELDS:
        # left-merge turns int columns into float when rows are missing, so cast back before comparing
        out_col = both[f + "_out"].astype(both[f].dtype)
        diff = both[both[f] != out_col]
        for r in diff.itertuples():
            rows.append((stage, r.schedule_id, r.schedule_date, r.carrier, f, getattr(r, f), getattr(r, f + "_out"), "FIELD_MISMATCH"))
    return pd.DataFrame(rows, columns=["stage", "schedule_id", "schedule_date", "carrier", "field",
                                       "master_value", "output_value", "issue_type"])


if __name__ == "__main__":
    master = pd.read_csv(ROOT / "data" / "master_schedule.csv")
    staged = pd.read_csv(ROOT / "data" / "staged_schedule.csv")
    dist = pd.read_csv(ROOT / "data" / "distributed_output.csv")
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    for name, df in [("pre_publish", staged), ("post_publish", dist)]:
        res = parity_check(master, df, name)
        res.to_csv(out / f"parity_{name}.csv", index=False)
        bad_records = res["schedule_id"].nunique()
        print(f"{name:13s} discrepancies={len(res):5d}  records affected={bad_records:5d} "
              f"({bad_records / len(master):.2%} of {len(master):,})")
