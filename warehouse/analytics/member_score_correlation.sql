WITH member_buckets AS (
    SELECT
        CASE
            WHEN members < 1000 THEN '1_lt_1K'
            WHEN members < 5000 THEN '2_1K-5K'
            WHEN members < 10000 THEN '3_5K-10K'
            WHEN members < 50000 THEN '4_10K-50K'
            WHEN members < 100000 THEN '5_50K-100K'
            ELSE '6_100K+'
        END AS member_bucket,
        score
    FROM `manga_analytics_marts.fct_manga`
    WHERE score IS NOT NULL
        AND members IS NOT NULL
)

SELECT
    SUBSTR(member_bucket, 3) AS member_bucket,
    ROUND(AVG(score), 2) AS avg_score,
    COUNT(*) AS title_count
FROM member_buckets
GROUP BY member_bucket
ORDER BY member_bucket
