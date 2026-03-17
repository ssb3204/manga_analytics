WITH raw_results AS (
    SELECT
        test_name,
        variant,
        run_number,
        bytes_scanned,
        slot_time_ms,
        execution_time_s,
        row_count,
        CAST(measured_at AS TIMESTAMP) AS measured_at
    FROM {{ ref('benchmark_results') }}
),

aggregated AS (
    SELECT
        test_name,
        variant,
        COUNT(run_number) AS total_runs,
        AVG(bytes_scanned) AS avg_bytes_scanned,
        AVG(slot_time_ms) AS avg_slot_time_ms,
        AVG(execution_time_s) AS avg_execution_time_s,
        MIN(execution_time_s) AS min_execution_time_s,
        MAX(execution_time_s) AS max_execution_time_s,
        AVG(row_count) AS avg_row_count
    FROM raw_results
    GROUP BY test_name, variant
)

SELECT
    test_name,
    variant,
    total_runs,
    ROUND(avg_bytes_scanned, 0) AS avg_bytes_scanned,
    ROUND(avg_slot_time_ms, 0) AS avg_slot_time_ms,
    ROUND(avg_execution_time_s, 2) AS avg_execution_time_s,
    ROUND(min_execution_time_s, 2) AS min_execution_time_s,
    ROUND(max_execution_time_s, 2) AS max_execution_time_s,
    CAST(avg_row_count AS INT64) AS avg_row_count
FROM aggregated
