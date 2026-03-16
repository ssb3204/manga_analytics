-- BigQuery DDL: manga_analytics dataset
-- Bronze layer — raw CSV ingested as-is

CREATE TABLE IF NOT EXISTS `manga_analytics.manga_bronze` (
    manga_id      INT64,
    title         STRING,
    title_english STRING,
    title_japanese STRING,
    manga_type    STRING,
    score         FLOAT64,
    scored_by     INT64,
    status        STRING,
    volumes       INT64,
    chapters      INT64,
    publishing    BOOL,
    genres        STRING,
    themes        STRING,
    demographic   STRING,
    serialization STRING,
    authors       STRING,
    synopsis      STRING,
    members       INT64,
    favorites     INT64,
    rating        STRING,
    start_date    DATE,
    end_date      DATE
);
