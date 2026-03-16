# 프로젝트 현황 정리

## 프로젝트 개요
MyAnimeList 만화 데이터셋(67,273건) 기반 데이터 엔지니어링 포트폴리오.
목표: 네이버 웹툰 Analytics Engineer 인턴십 지원용.

## 기술 스택
| 구분 | 도구 |
|---|---|
| 웨어하우스 | BigQuery (GCP 무료 티어) |
| 모델링 | dbt CLI (bigquery adapter) |
| 오케스트레이션 | Airflow (Docker) |
| 시각화 | Apache Superset (Docker) |
| 인프라 | Docker Compose (5개 서비스) |

## 완료된 작업

### 1. 데이터 파이프라인 (완료)
- CSV → BigQuery `manga_bronze` 적재 (WRITE_TRUNCATE)
- Airflow DAG 3개 태스크: `ingest_bronze` → `dbt_run` → `dbt_test`
- 전체 파이프라인 테스트 통과 (2026-03-11)

### 2. dbt 모델링 (완료)
| 레이어 | 모델 | 설명 |
|---|---|---|
| Silver | `stg_manga_clean` | 타입 캐스팅, NULL 처리, TRIM |
| Gold | `fct_manga` | 팩트 테이블 (manga당 1행) |
| Gold | `dim_status` | 상태 디멘션 (MD5 키) |
| Gold | `dim_genre` | 장르 디멘션 (UNNEST) |
| Gold | `bridge_manga_genre` | 다대다 브릿지 테이블 |

### 3. Docker 인프라 (완료)
- `docker-compose up`으로 전체 스택 실행
- Airflow UI: http://localhost:8081
- Superset UI: http://localhost:8088
- 인증: admin/admin

### 4. 문서화 (완료)
- `docs/data_catalog.md` — 테이블/컬럼 정의
- `docs/business_glossary.md` — 지표 및 비즈니스 용어
- `docs/lineage.md` — Bronze → Silver → Gold 흐름도
- `docs/data_quality.md` — dbt 테스트 매트릭스
- `docs/setup.md` — 설치 가이드

### 5. Superset 설정 (부분 완료)
- BigQuery 연결 완료
- 데이터셋 4개 등록 + `fct_manga_scored` 가상 데이터셋 생성

---

## 미완료 작업 (순서대로)

### 1단계: Superset 차트 (5개)
| 차트 | 유형 | 데이터셋 |
|---|---|---|
| 장르별 평균 점수 | Bar | genre_performance (SQL Lab) |
| 장르 인기도 vs 품질 | Bubble | genre_performance |
| 연도별 점수 추이 | Line | fct_manga_scored |
| 상태 분포 | Pie | status_distribution (SQL Lab) |
| Top 10 만화 | Table | fct_manga_scored |

### 2단계: 대시보드
- 5개 차트를 하나의 Superset 대시보드로 통합

### 3단계: A/B 성능 비교 테스트
| 테스트 | A (현재) | B (대안) |
|---|---|---|
| Materialization | view | table / incremental |
| Partitioning | 없음 | start_date 파티션 + 클러스터링 |
| Ingestion | full truncate | incremental merge |

- 측정 지표: bytes_scanned, slot_time_ms, execution_time_s
- 데이터 소스: `INFORMATION_SCHEMA.JOBS` (무료)
- 결과 → `fct_perf_comparison` dbt 모델 → Superset 차트

### 4단계: 마무리
- GitHub repo 정리
- README 작성
- 포트폴리오 문서

---

## 알려진 이슈
| 이슈 | 영향 | 상태 |
|---|---|---|
| Analytics SQL 접두어 오류 (`manga_analytics.` → `manga_analytics_marts.`) | 분석 쿼리 실행 실패 | 미수정 |
| GitHub Actions에서 CSV 없음 (gitignored) | CI 파이프라인 실패 | 미수정 |
| `dim_rating.sql` 삭제됨 | 없음 (참조하는 모델 없음) | 무시 가능 |

---

마지막 업데이트: 2026-03-14
