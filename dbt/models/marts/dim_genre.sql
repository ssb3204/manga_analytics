WITH genre_strings AS (
    SELECT DISTINCT
        TRIM(genre) AS genre_name
    FROM {{ ref('stg_manga_clean') }},
    UNNEST(SPLIT(genres, ',')) AS genre
    WHERE genres IS NOT NULL
        AND TRIM(genre) != ''
)

SELECT
    TO_HEX(MD5(genre_name)) AS genre_id,
    genre_name
FROM genre_strings
