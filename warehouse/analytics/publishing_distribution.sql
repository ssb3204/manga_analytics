WITH deciles AS (
    SELECT
        manga_id,
        title,
        members,
        NTILE(10) OVER (ORDER BY members) AS member_decile
    FROM `manga_analytics_marts.fct_manga`
    WHERE members IS NOT NULL
)

SELECT
    member_decile,
    MIN(members) AS min_members,
    MAX(members) AS max_members,
    ROUND(AVG(members), 0) AS avg_members,
    COUNT(manga_id) AS title_count
FROM deciles
GROUP BY member_decile
ORDER BY member_decile
