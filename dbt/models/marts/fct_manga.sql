WITH manga AS (
    SELECT
        m.manga_id,
        m.title,
        m.title_english,
        m.title_japanese,
        m.manga_type,
        m.score,
        m.scored_by,
        m.volumes,
        m.chapters,
        m.members,
        m.favorites,
        m.start_date,
        m.end_date,
        m.ingested_at,
        s.status_key
    FROM {{ ref('stg_manga_clean') }} AS m
    LEFT JOIN {{ ref('dim_status') }} AS s
        ON m.status = s.status_label
)

SELECT
    manga_id,
    title,
    title_english,
    title_japanese,
    manga_type,
    score,
    scored_by,
    volumes,
    chapters,
    members,
    favorites,
    start_date,
    end_date,
    status_key,
    ingested_at
FROM manga
