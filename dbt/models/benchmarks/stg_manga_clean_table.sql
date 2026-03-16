{{ config(materialized='table') }}

WITH source AS (
    SELECT
        manga_id,
        title,
        title_english,
        title_japanese,
        type AS manga_type,
        SAFE_CAST(score AS FLOAT64) AS score,
        SAFE_CAST(scored_by AS INT64) AS scored_by,
        status,
        SAFE_CAST(volumes AS INT64) AS volumes,
        SAFE_CAST(chapters AS INT64) AS chapters,
        genres,
        demographics AS demographic,
        serializations AS serialization,
        authors,
        SAFE_CAST(members AS INT64) AS members,
        SAFE_CAST(favorites AS INT64) AS favorites,
        SAFE_CAST(start_date AS DATE) AS start_date,
        SAFE_CAST(end_date AS DATE) AS end_date,
        CURRENT_TIMESTAMP() AS ingested_at
    FROM {{ source('manga_analytics', 'manga_bronze') }}
),

cleaned AS (
    SELECT
        manga_id,
        NULLIF(TRIM(title), '') AS title,
        NULLIF(TRIM(title_english), '') AS title_english,
        NULLIF(TRIM(title_japanese), '') AS title_japanese,
        NULLIF(TRIM(manga_type), '') AS manga_type,
        CASE WHEN score = 0 THEN NULL ELSE score END AS score,
        scored_by,
        NULLIF(TRIM(status), '') AS status,
        volumes,
        chapters,
        NULLIF(TRIM(genres), '') AS genres,
        NULLIF(TRIM(demographic), '') AS demographic,
        NULLIF(TRIM(serialization), '') AS serialization,
        NULLIF(TRIM(authors), '') AS authors,
        members,
        favorites,
        start_date,
        end_date,
        ingested_at
    FROM source
)

SELECT
    manga_id,
    title,
    title_english,
    title_japanese,
    manga_type,
    score,
    scored_by,
    status,
    volumes,
    chapters,
    genres,
    demographic,
    serialization,
    authors,
    members,
    favorites,
    start_date,
    end_date,
    ingested_at
FROM cleaned
WHERE manga_id IS NOT NULL
