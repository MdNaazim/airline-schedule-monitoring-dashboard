-- SQLite schema + reporting view for the airline schedule monitoring project
DROP TABLE IF EXISTS master_schedule;
DROP TABLE IF EXISTS distributed_output;
DROP TABLE IF EXISTS parity_post_publish;
DROP VIEW  IF EXISTS v_schedule_status;

CREATE TABLE master_schedule (
    schedule_id INTEGER PRIMARY KEY, schedule_date TEXT, carrier TEXT, flight_no INTEGER,
    origin TEXT, destination TEXT, sched_dep TEXT, sched_arr TEXT, aircraft_type TEXT, master_updated_ts TEXT);
CREATE TABLE distributed_output (
    schedule_id INTEGER PRIMARY KEY, schedule_date TEXT, carrier TEXT, flight_no INTEGER,
    origin TEXT, destination TEXT, sched_dep TEXT, sched_arr TEXT, aircraft_type TEXT,
    master_updated_ts TEXT, publish_latency_min REAL, publish_ts TEXT);
CREATE TABLE parity_post_publish (
    stage TEXT, schedule_id INTEGER, schedule_date TEXT, carrier TEXT, field TEXT,
    master_value TEXT, output_value TEXT, issue_type TEXT);
CREATE INDEX idx_parity_id ON parity_post_publish(schedule_id);

-- One row per scheduled flight with its parity status after publishing
CREATE VIEW v_schedule_status AS
SELECT m.schedule_id, m.schedule_date, m.carrier, m.origin, m.destination,
       d.publish_latency_min,
       CASE WHEN d.schedule_id IS NULL THEN 'MISSING'
            WHEN p.schedule_id IS NOT NULL THEN 'MISMATCH'
            ELSE 'MATCH' END AS parity_status
FROM master_schedule m
LEFT JOIN distributed_output d ON d.schedule_id = m.schedule_id
LEFT JOIN (SELECT DISTINCT schedule_id FROM parity_post_publish) p ON p.schedule_id = m.schedule_id;
