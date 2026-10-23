"""Generate SYNTHETIC airline schedule data (master -> staged -> distributed).

All data is simulated for portfolio purposes. No real airline data is used.
Run: python src/generate_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
N = 10_400
DATA = Path(__file__).resolve().parents[1] / "data"
DATA.mkdir(exist_ok=True)

CARRIERS = ["AX", "BY", "CZ", "DW", "EV"]          # fictional carrier codes
AIRPORTS = ["MAA", "BLR", "DEL", "BOM", "HYD", "CJB", "COK", "CCU"]
AIRCRAFT = ["A320", "A321", "B737", "ATR72"]
FIELDS = ["sched_dep", "sched_arr", "aircraft_type", "destination"]

dates = pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 90, N), unit="D")
dep_min = rng.integers(5 * 60, 23 * 60, N)
duration = rng.integers(60, 241, N)
origin = rng.choice(AIRPORTS, N)
dest = np.array([rng.choice([a for a in AIRPORTS if a != o]) for o in origin])
sched_dep = dates + pd.to_timedelta(dep_min, unit="m")

master = pd.DataFrame({
    "schedule_id": np.arange(1, N + 1),
    "schedule_date": dates.strftime("%Y-%m-%d"),
    "carrier": rng.choice(CARRIERS, N),
    "flight_no": rng.integers(100, 999, N),
    "origin": origin,
    "destination": dest,
    "sched_dep": sched_dep.strftime("%Y-%m-%d %H:%M"),
    "sched_arr": (sched_dep + pd.to_timedelta(duration, unit="m")).strftime("%Y-%m-%d %H:%M"),
    "aircraft_type": rng.choice(AIRCRAFT, N),
})
change_lead = rng.integers(60, 60 * 24 * 10, N)    # minutes before departure the master record changed
master["master_updated_ts"] = (sched_dep - pd.to_timedelta(change_lead, unit="m")).strftime("%Y-%m-%d %H:%M")


def corrupt(row):
    """Introduce one realistic discrepancy into a record."""
    f = rng.choice(FIELDS)
    if f in ("sched_dep", "sched_arr"):
        t = pd.to_datetime(row[f]) + pd.Timedelta(minutes=int(rng.choice([-60, -30, -15, -5, 5, 10, 15, 30, 60])))
        row[f] = t.strftime("%Y-%m-%d %H:%M")
    elif f == "aircraft_type":
        row[f] = rng.choice([a for a in AIRCRAFT if a != row[f]])
    else:
        row[f] = rng.choice([a for a in AIRPORTS if a not in (row[f], row["origin"])])
    return row


# Staged copy: ~1.5% of records carry an error before publishing
staged = master.copy()
bad = rng.random(N) < 0.015
for i in np.where(bad)[0]:
    staged.iloc[i] = corrupt(staged.iloc[i].copy())

# Distributed copy: 60% of staged errors get fixed, ~1% new errors, ~0.2% records never arrive
distributed = staged.copy()
for i in np.where(bad)[0]:
    if rng.random() < 0.60:
        distributed.iloc[i] = master.iloc[i]
new_bad = (rng.random(N) < 0.010) & ~bad
for i in np.where(new_bad)[0]:
    distributed.iloc[i] = corrupt(distributed.iloc[i].copy())
distributed = distributed[rng.random(N) >= 0.002].copy()

# Publish latency (minutes): lognormal body with a heavy tail
lat = rng.lognormal(mean=2.7, sigma=0.55, size=len(distributed))
tail = rng.random(len(distributed)) < 0.05
lat[tail] += rng.integers(30, 180, tail.sum())
distributed["publish_latency_min"] = np.round(lat, 1)
ts = pd.to_datetime(distributed["master_updated_ts"]) + pd.to_timedelta(distributed["publish_latency_min"], unit="m")
distributed["publish_ts"] = ts.dt.strftime("%Y-%m-%d %H:%M")

master.to_csv(DATA / "master_schedule.csv", index=False)
staged.to_csv(DATA / "staged_schedule.csv", index=False)
distributed.to_csv(DATA / "distributed_output.csv", index=False)
print(f"master={len(master):,}  staged={len(staged):,}  distributed={len(distributed):,}")
