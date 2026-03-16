WITH genre_scores AS (
    SELECT
        g.genre_name,
        AVG(f.score) AS avg_score,
        COUNT(DISTINCT f.manga_id) AS title_count,
        SUM(f.members) AS total_members
    FROM `manga_analytics_marts.fct_manga` AS f
    INNER JOIN `manga_analytics_marts.bridge_manga_genre` AS b
        ON f.manga_id = b.manga_id
    INNER JOIN `manga_analytics_marts.dim_genre` AS g
        ON b.genre_id = g.genre_id
    WHERE f.score IS NOT NULL
    GROUP BY g.genre_name
)

SELECT
    genre_name,
    ROUND(avg_score, 2) AS avg_score,
    title_count,
    total_members
FROM genre_scores
ORDER BY avg_score DESC
