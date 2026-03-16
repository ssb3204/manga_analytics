# 데이터 리니지

## 파이프라인 흐름

```
[Kaggle CSV: data/raw/manga.csv]
     |
     | fetch_raw.py (WRITE_TRUNCATE)
     v
[BigQuery: manga_analytics.manga_bronze]   <- Bronze (21개 컬럼)
     |
     | dbt: stg_manga_clean (view)
     | publishing, themes, synopsis 컬럼 제외
     | score=0 -> NULL, 빈 문자열 -> NULL, SAFE_CAST 적용
     v
[BigQuery: manga_analytics_staging.stg_manga_clean]   <- Silver (20개 컬럼)
     |
     +---> dbt: dim_status (table)
     |       status에서 DISTINCT + MD5 해시
     |
     +---> dbt: dim_rating (table)
     |       rating에서 DISTINCT + MD5 해시
     |
     +---> dbt: dim_genre (table)
     |       genres를 SPLIT + UNNEST + MD5 해시
     |          |
     |          +---> dbt: bridge_manga_genre (table)
     |                     manga_id x genre_id 다대다 매핑
     |
     +---> dbt: fct_manga (table)   <- Gold
               dim_status, dim_rating과 LEFT JOIN
```

## 오케스트레이션

```
GitHub Actions (매주 월요일 06:00 UTC / 수동 실행)
     |
     +-- Job: ingest
     |     fetch_raw.py -> manga_bronze
     |
     +-- Job: dbt_run (needs: ingest)
           dbt run --select staging
           dbt run --select marts
           dbt test
```

## 소스-타겟 매핑

| 소스 (Bronze) | 변환 | 타겟 (Silver/Gold) |
|---|---|---|
| manga_bronze.score | score=0 -> NULL, SAFE_CAST FLOAT64 | stg_manga_clean.score |
| manga_bronze.genres | NULLIF(빈 문자열), TRIM | stg_manga_clean.genres |
| manga_bronze.publishing | Silver에서 제외 | -- |
| manga_bronze.themes | Silver에서 제외 | -- |
| manga_bronze.synopsis | Silver에서 제외 | -- |
| stg_manga_clean.status | DISTINCT + MD5 해시 | dim_status.status_key |
| stg_manga_clean.rating | DISTINCT + MD5 해시 | dim_rating.rating_key |
| stg_manga_clean.genres | SPLIT(',') + UNNEST + MD5 | dim_genre.genre_id |
| stg_manga_clean.manga_id x dim_genre.genre_id | JOIN on genre_name | bridge_manga_genre |
| stg_manga_clean.* + dim 키 | LEFT JOIN dims | fct_manga |

## 분석 쿼리 (warehouse/analytics/)

Gold 레이어 테이블을 사용하는 분석 SQL 파일 6개:

| 파일 | 설명 | 사용 테이블 |
|---|---|---|
| top_manga_by_score.sql | 점수 기준 상위 작품 순위 (RANK 윈도우 함수) | fct_manga |
| genre_performance.sql | 장르별 평균 점수 및 회원 수 | fct_manga, bridge_manga_genre, dim_genre |
| score_trend_by_year.sql | 연도별 평균 점수 추이 | fct_manga |
| completion_vs_score.sql | 연재 상태별 점수 비교 | fct_manga, dim_status |
| member_score_correlation.sql | 회원 수 구간별 평균 점수 | fct_manga |
| publishing_distribution.sql | 회원 수 기준 NTILE 십분위 분포 | fct_manga |

> **참고:** 현재 analytics SQL 파일들은 `manga_analytics.fct_manga`를 참조하고 있으나, dbt에 의해 생성되는 실제 데이터셋 이름은 `manga_analytics_marts`임. BigQuery 콘솔에서 실행 시 데이터셋 이름을 `manga_analytics_marts`로 변경해야 함.
