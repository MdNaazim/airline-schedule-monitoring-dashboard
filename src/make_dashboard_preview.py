"""Static preview of the dashboard (matplotlib) so the repo shows results without opening Power BI.
Run: python src/make_dashboard_preview.py
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
exp = ROOT / "powerbi_exports"
carrier = pd.read_csv(exp / "kpi_by_carrier.csv")
daily = pd.read_csv(exp / "daily_kpi.csv", parse_dates=["schedule_date"])
field = pd.read_csv(exp / "discrepancies_by_field.csv")
fact = pd.read_csv(exp / "fact_schedule_status.csv")
overall = pd.read_csv(exp / "overall_kpi.csv").iloc[0]

fig, ax = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle(f"Airline Schedule Monitoring (synthetic data) | Accuracy {overall.schedule_accuracy_pct:.2f}% | "
             f"Avg publish latency {overall.avg_publish_latency_min:.1f} min | SLA breaches {overall.sla_breach_pct:.1f}%",
             fontsize=12, fontweight="bold")
ax[0, 0].bar(carrier["carrier"], carrier["schedule_accuracy_pct"], color="#1f77b4")
ax[0, 0].set_ylim(95, 100); ax[0, 0].set_title("Schedule accuracy by carrier (%)")
ax[0, 1].plot(daily["schedule_date"], daily["schedule_accuracy_pct"].rolling(7, min_periods=1).mean(), color="#2ca02c")
ax[0, 1].set_title("Daily schedule accuracy (7-day avg, %)"); ax[0, 1].tick_params(axis="x", rotation=30)
ax[1, 0].hist(fact["publish_latency_min"].dropna(), bins=40, color="#ff7f0e")
ax[1, 0].axvline(30, color="red", ls="--", label="30-min SLA"); ax[1, 0].legend()
ax[1, 0].set_title("Publish latency distribution (min)")
lab = field["field"] + " / " + field["issue_type"].str.replace("_", " ").str.lower()
ax[1, 1].barh(lab, field["discrepancy_count"], color="#d62728"); ax[1, 1].invert_yaxis()
ax[1, 1].set_title("Post-publish parity discrepancies by field")
plt.tight_layout(rect=[0, 0, 1, 0.94])
out = ROOT / "docs" / "dashboard_preview.png"
plt.savefig(out, dpi=130)
print("saved", out)
