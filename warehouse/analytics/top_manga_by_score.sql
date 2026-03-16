WITH ranked_manga AS (
    SELECT
        manga_id,
        title,
        score,
        members,
        scored_by,
        RANK() OVER (ORDER BY score DESC) AS score_rank
    FROM `manga_analytics_marts.fct_manga`
    WHERE score IS NOT NULL
        AND scored_by > 100
)

SELECT
    score_rank,
    manga_id,
    title,
    score,
    members
FROM ranked_manga
WHERE score_rank <= 100
ORDER BY score_rank
