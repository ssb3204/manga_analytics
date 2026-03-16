WITH exploded AS (
    SELECT
        manga_id,
        TRIM(genre) AS genre_name
    FROM {{ ref('stg_manga_clean') }},
    UNNEST(SPLIT(genres, ',')) AS genre
    WHERE genres IS NOT NULL
        AND TRIM(genre) != ''
)

SELECT
    e.manga_id,
    g.genre_id
FROM exploded AS e
INNER JOIN {{ ref('dim_genre') }} AS g
    ON e.genre_name = g.genre_name
