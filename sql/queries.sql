-- name: kpi_by_carrier
SELECT carrier,
       COUNT(*)                                                         AS scheduled_flights,
       SUM(parity_status = 'MATCH')                                     AS matched,
       ROUND(100.0 * SUM(parity_status = 'MATCH') / COUNT(*), 2)        AS schedule_accuracy_pct,
       ROUND(AVG(publish_latency_min), 1)                               AS avg_publish_latency_min,
       ROUND(100.0 * SUM(publish_latency_min > 30) / COUNT(publish_latency_min), 2) AS sla_breach_pct
FROM v_schedule_status
GROUP BY carrier
ORDER BY schedule_accuracy_pct DESC;

-- name: daily_kpi
SELECT schedule_date,
       COUNT(*)                                                  AS scheduled_flights,
       ROUND(100.0 * SUM(parity_status = 'MATCH') / COUNT(*), 2) AS schedule_accuracy_pct,
       ROUND(AVG(publish_latency_min), 1)                        AS avg_publish_latency_min
FROM v_schedule_status
GROUP BY schedule_date
ORDER BY schedule_date;

-- name: discrepancies_by_field
SELECT field, issue_type, COUNT(*) AS discrepancy_count
FROM parity_post_publish
GROUP BY field, issue_type
ORDER BY discrepancy_count DESC;

-- name: overall_kpi
SELECT COUNT(*) AS scheduled_flights,
       SUM(parity_status = 'MATCH')    AS matched,
       SUM(parity_status = 'MISMATCH') AS mismatched,
       SUM(parity_status = 'MISSING')  AS missing,
       ROUND(100.0 * SUM(parity_status = 'MATCH') / COUNT(*), 2) AS schedule_accuracy_pct,
       ROUND(AVG(publish_latency_min), 1) AS avg_publish_latency_min,
       ROUND(100.0 * SUM(publish_latency_min > 30) / COUNT(publish_latency_min), 2) AS sla_breach_pct
FROM v_schedule_status;
