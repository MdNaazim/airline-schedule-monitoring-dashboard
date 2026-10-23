# Building the Power BI dashboard

The repo ships the cleaned, SQL-generated tables in `powerbi_exports/`. Power BI Desktop (free) is Windows-only;
build the report with the steps below and save the `.pbix` into this folder as `Airline_Schedule_Dashboard.pbix`.

## 1. Load data
**Home > Get data > Text/CSV**, load these files from `powerbi_exports/`:

| File | Use |
|---|---|
| `fact_schedule_status.csv` | One row per flight with `parity_status` and `publish_latency_min` (main fact table) |
| `parity_discrepancies.csv` | One row per discrepancy (field, master value, output value) |
| `daily_kpi.csv`, `kpi_by_carrier.csv`, `discrepancies_by_field.csv` | Optional pre-aggregated checks |

Relationship (Model view): `fact_schedule_status[schedule_id]` 1 -> * `parity_discrepancies[schedule_id]`.
Change `schedule_date` to **Date** type in Power Query.

## 2. DAX measures
```DAX
Scheduled Flights = COUNTROWS(fact_schedule_status)

Matched Flights =
CALCULATE([Scheduled Flights], fact_schedule_status[parity_status] = "MATCH")

Schedule Accuracy % = DIVIDE([Matched Flights], [Scheduled Flights])

Parity Discrepancies = COUNTROWS(parity_discrepancies)

Avg Publish Latency (min) = AVERAGE(fact_schedule_status[publish_latency_min])

SLA Breaches =
CALCULATE([Scheduled Flights], fact_schedule_status[publish_latency_min] > 30)

SLA Breach % =
DIVIDE([SLA Breaches], COUNT(fact_schedule_status[publish_latency_min]))
```

## 3. Report page layout (matches `dashboard_preview.png`)
1. **KPI cards:** Schedule Accuracy %, Avg Publish Latency (min), SLA Breach %, Parity Discrepancies
2. **Clustered bar:** Schedule Accuracy % by `carrier`
3. **Line chart:** Schedule Accuracy % by `schedule_date`
4. **Histogram (column chart on binned latency):** publish latency, with a constant line at 30 min
5. **Bar chart:** Parity Discrepancies by `field`
6. **Slicers:** carrier, origin, destination, date range
7. Conditional formatting: accuracy < 98% in red on the carrier visual

## 4. Refreshing
Re-run `python src/parity_check.py` and `python src/build_sql_and_exports.py`, then **Refresh** in Power BI.
