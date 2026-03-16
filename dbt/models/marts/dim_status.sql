WITH statuses AS (
    SELECT DISTINCT
        status
    FROM {{ ref('stg_manga_clean') }}
    WHERE status IS NOT NULL
)

SELECT
    TO_HEX(MD5(status)) AS status_key,
    status AS status_label
FROM statuses
