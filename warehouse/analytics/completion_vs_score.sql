WITH status_metrics AS (
    SELECT
        s.status_label,
        AVG(f.score) AS avg_score,
        COUNT(f.manga_id) AS title_count,
        COUNT(f.manga_id) * 100.0 / SUM(COUNT(f.manga_id)) OVER () AS pct_of_total
    FROM `manga_analytics_marts.fct_manga` AS f
    INNER JOIN `manga_analytics_marts.dim_status` AS s
        ON f.status_key = s.status_key
    WHERE f.score IS NOT NULL
    GROUP BY s.status_label
)

SELECT
    status_label,
    ROUND(avg_score, 2) AS avg_score,
    title_count,
    ROUND(pct_of_total, 1) AS pct_of_total
FROM status_metrics
ORDER BY avg_score DESC
