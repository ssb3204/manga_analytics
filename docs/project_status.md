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
| CI/CD | GitHub Actions |
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
- `docs/architecture_decisions.md` — 기술 선택 이유 + 문제 해결 + A/B 결과

### 5. Superset 대시보드 (완료)
- BigQuery 연결 완료
- 데이터셋 4개 등록 + SQL Lab 가상 데이터셋 2개
- 차트 4개 완성, 2개 의도적 제외

| 차트 | 유형 | 상태 |
|---|---|---|
| Score Distribution | Histogram | ✅ 완료 |
| Genre Popularity vs Quality | Bubble | ✅ 완료 |
| Score Trend by Year | Line | ✅ 완료 |
| Members vs Score | Scatter | ✅ 완료 |
| Genre Bar (장르별 평균 점수) | Bar | ⏭️ 제외 (값 차이 미미) |
| Status Breakdown (상태 분포) | Pie | ⏭️ 제외 (인사이트 부족) |

### 6. A/B 성능 테스트 (완료)
| 테스트 | Variant A | Variant B | 결과 |
|---|---|---|---|
| Materialization (VIEW vs TABLE) | 1,775,935 bytes | 1,257,271 bytes | TABLE 29% 절감 |
| Partitioning (없음 vs 파티션) | 1,242,207 bytes | 0 bytes | 100% 절감 |

- ingestion 테스트(MERGE)는 BigQuery 무료 티어 DML 제한으로 제거

### 7. GitHub + CI/CD (완료)
- GitHub repo: https://github.com/ssb3204/manga_analytics
- 브랜칭: GitHub Flow (main + feature branches)
- GitHub Actions: dbt 변경 시 자동 빌드 + 테스트
- README 작성 (한국어)

---

## 미완료 작업

| 작업 | 상태 |
|---|---|
| Superset A/B 차트 필터 수정 (`_query` 행만 표시) | ⬜ |
| Notion 포트폴리오 페이지 작성 | ✅ 완료 (2026-03-19) |

---

## 해결된 이슈
| 이슈 | 해결 방법 | 해결일 |
|---|---|---|
| Analytics SQL 접두어 (`manga_analytics.`) | 이미 `manga_analytics_marts.`로 수정됨 확인 | 2026-03-19 |
| GitHub Actions CSV 없음 (CI 실패) | ingest job 제거, dbt만 실행하도록 변경 | 2026-03-19 |
| `dim_rating.sql` 삭제됨 | 참조하는 모델 없음, 무시 가능 | - |

---

마지막 업데이트: 2026-03-19
