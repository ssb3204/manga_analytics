WITH yearly_scores AS (
    SELECT
        EXTRACT(YEAR FROM start_date) AS start_year,
        AVG(score) AS avg_score,
        COUNT(manga_id) AS title_count
    FROM `manga_analytics_marts.fct_manga`
    WHERE start_date IS NOT NULL
        AND score IS NOT NULL
        AND EXTRACT(YEAR FROM start_date) >= 1990
    GROUP BY start_year
)

SELECT
    start_year,
    ROUND(avg_score, 2) AS avg_score,
    title_count
FROM yearly_scores
ORDER BY start_year
