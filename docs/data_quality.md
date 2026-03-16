# 데이터 품질

## dbt 테스트

모든 테스트는 GitHub Actions 파이프라인에서 `dbt test`를 통해 실행됨.

| 모델 | 컬럼 | 테스트 | 기대 결과 |
|---|---|---|---|
| stg_manga_clean | manga_id | not_null | 0 실패 |
| stg_manga_clean | manga_id | unique | 0 실패 |
| stg_manga_clean | title | not_null | 0 실패 |
| fct_manga | manga_id | not_null | 0 실패 |
| fct_manga | manga_id | unique | 0 실패 |
| fct_manga | title | not_null | 0 실패 |
| dim_status | status_key | not_null | 0 실패 |
| dim_status | status_key | unique | 0 실패 |
| dim_status | status_label | not_null | 0 실패 |
| dim_rating | rating_key | not_null | 0 실패 |
| dim_rating | rating_key | unique | 0 실패 |
| dim_rating | rating_label | not_null | 0 실패 |
| dim_genre | genre_id | not_null | 0 실패 |
| dim_genre | genre_id | unique | 0 실패 |
| dim_genre | genre_name | not_null | 0 실패 |
| bridge_manga_genre | manga_id | not_null | 0 실패 |
| bridge_manga_genre | genre_id | not_null | 0 실패 |

## 검증 쿼리 (BigQuery 콘솔에서 실행)

### 행 수 확인
```sql
SELECT COUNT(*) AS row_count
FROM `manga_analytics.manga_bronze`;
-- 기대값: ~67,273
```

### 점수 범위 확인
```sql
SELECT
    MIN(score) AS min_score,
    MAX(score) AS max_score,
    COUNT(*) AS scored_count
FROM `manga_analytics_staging.stg_manga_clean`
WHERE score IS NOT NULL;
-- 기대값: min >= 1.0, max <= 10.0
```

### 참조 무결성: fct_manga -> dim_status
```sql
SELECT COUNT(*) AS orphaned_rows
FROM `manga_analytics_marts.fct_manga` AS f
LEFT JOIN `manga_analytics_marts.dim_status` AS s
    ON f.status_key = s.status_key
WHERE f.status_key IS NOT NULL
    AND s.status_key IS NULL;
-- 기대값: 0 (고아 행 없음)
```

### 참조 무결성: fct_manga -> dim_rating
```sql
SELECT COUNT(*) AS orphaned_rows
FROM `manga_analytics_marts.fct_manga` AS f
LEFT JOIN `manga_analytics_marts.dim_rating` AS r
    ON f.rating_key = r.rating_key
WHERE f.rating_key IS NOT NULL
    AND r.rating_key IS NULL;
-- 기대값: 0 (고아 행 없음)
```

### 브릿지 테이블 커버리지
```sql
SELECT
    COUNT(DISTINCT manga_id) AS manga_with_genres,
    (SELECT COUNT(*) FROM `manga_analytics_marts.fct_manga`) AS total_manga
FROM `manga_analytics_marts.bridge_manga_genre`;
-- 기대값: manga_with_genres가 total_manga에 근접
```

### NULL 비율 리포트
```sql
SELECT
    COUNTIF(score IS NULL) AS null_scores,
    COUNTIF(members IS NULL) AS null_members,
    COUNTIF(start_date IS NULL) AS null_start_dates,
    COUNTIF(genres IS NULL) AS null_genres,
    COUNT(*) AS total_rows
FROM `manga_analytics_staging.stg_manga_clean`;
```

### Silver 레이어에서 제외된 컬럼 확인
```sql
SELECT
    COUNTIF(publishing IS NOT NULL) AS has_publishing,
    COUNTIF(themes IS NOT NULL) AS has_themes,
    COUNTIF(synopsis IS NOT NULL) AS has_synopsis
FROM `manga_analytics.manga_bronze`;
-- 참고: 이 3개 컬럼은 Silver에서 의도적으로 제외됨
```
