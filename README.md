# MyAnimeList 만화 데이터 파이프라인

MyAnimeList 만화 데이터셋(67,273건)을 활용한 데이터 엔지니어링 포트폴리오 프로젝트.

## 아키텍처

```
[Kaggle CSV]
     │
     │  fetch_raw.py (WRITE_TRUNCATE)
     ▼
[BigQuery: manga_bronze]          ── Bronze (원시)
     │
     │  dbt: stg_manga_clean (VIEW)
     ▼
[BigQuery: stg_manga_clean]       ── Silver (정제)
     │
     ├──► dim_status     (MD5 해시 키)
     ├──► dim_genre      (UNNEST + MD5)
     ├──► bridge_manga_genre (다대다)
     │
     │  dbt: fct_manga (TABLE)
     ▼
[BigQuery: fct_manga]             ── Gold (비즈니스)
     │
     ▼
[Superset 대시보드]
```

## 기술 스택

| 구분 | 도구 | 버전 |
|---|---|---|
| 웨어하우스 | BigQuery (GCP 무료 티어) | - |
| 모델링 | dbt CLI (bigquery adapter) | 1.11.7 |
| 오케스트레이션 | Apache Airflow (Docker) | 2.10.0 |
| 시각화 | Apache Superset (Docker) | 4.1.1 |
| CI/CD | GitHub Actions | - |
| 인프라 | Docker Compose | - |

> 기술 스택 선택 이유와 진행 중 만난 문제 해결 과정은 [docs/architecture_decisions.md](docs/architecture_decisions.md) 참고.

## 프로젝트 구조

```
├── ingestion/              CSV → BigQuery 적재 스크립트
├── warehouse/
│   ├── schema.sql          Bronze DDL 정의
│   └── analytics/          분석 쿼리 6종
├── dbt/
│   ├── models/
│   │   ├── staging/        Silver 레이어 (stg_manga_clean)
│   │   ├── marts/          Gold 레이어 (fct_, dim_, bridge_)
│   │   └── benchmarks/     A/B 성능 테스트 변형 모델
│   └── seeds/              벤치마크 결과 CSV
├── benchmarks/             성능 벤치마크 러너
├── airflow/                Airflow DAG + Dockerfile
├── superset/               Superset Dockerfile + 설정
├── docs/                   프로젝트 문서 (한국어)
└── .github/workflows/      CI 파이프라인
```

## 데이터 레이어

| 레이어 | 스키마 | 구체화 | 테이블 |
|---|---|---|---|
| Bronze | `manga_analytics` | TABLE | `manga_bronze` (21개 컬럼) |
| Silver | `manga_analytics_staging` | VIEW | `stg_manga_clean` (20개 컬럼) |
| Gold | `manga_analytics_marts` | TABLE | `fct_manga`, `dim_status`, `dim_genre`, `bridge_manga_genre` |

## 파이프라인

### Airflow (로컬 오케스트레이션)

DAG 3개 태스크가 순차 실행:

```
ingest_bronze → dbt_run → dbt_test
```

- `ingest_bronze`: CSV → BigQuery `manga_bronze` (WRITE_TRUNCATE, 멱등성 보장)
- `dbt_run`: Silver(staging) + Gold(marts) 모델 빌드
- `dbt_test`: not_null, unique 등 14개 데이터 품질 테스트

### GitHub Actions (CI)

`dbt/` 디렉토리 변경 시 자동 실행:

```
dbt run staging → dbt run marts → dbt test
```

- Bronze 데이터는 BigQuery에 이미 적재되어 있으므로 CI에서는 dbt만 실행
- 수동 실행(`workflow_dispatch`)도 가능

## A/B 성능 테스트

67K rows 규모에서 두 가지 최적화 전략을 비교 실험:

| 테스트 | Variant A (현재) | Variant B (대안) |
|---|---|---|
| Materialization | VIEW | TABLE |
| Partitioning | 없음 | start_date 월별 파티션 + 클러스터링 |

- `INFORMATION_SCHEMA.JOBS`에서 `total_bytes_processed`, `total_slot_ms` 수집
- 각 variant 3회 반복 실행, 캐시 비활성화
- 결과: [docs/architecture_decisions.md](docs/architecture_decisions.md)의 성능 테스트 섹션 참고

## 실행 방법

### 사전 요구사항

- Docker + Docker Compose
- GCP 프로젝트 (BigQuery API 활성화)
- GCP 서비스 계정 JSON 키

### 1. 환경 설정

```bash
cp .env.example .env
# .env 파일에 GCP_PROJECT_ID 입력
# secrets/gcp-key.json에 서비스 계정 키 배치
```

### 2. 데이터 준비

Kaggle에서 [MyAnimeList manga dataset](https://www.kaggle.com/datasets/dbdmobile/myanimelist-dataset) 다운로드 → `data/raw/manga.csv`에 배치.

### 3. Docker 실행

```bash
docker-compose up -d
```

| 서비스 | URL | 인증 |
|---|---|---|
| Airflow | http://localhost:8081 | admin / admin |
| Superset | http://localhost:8088 | admin / admin |

### 4. 파이프라인 실행

Airflow UI에서 `manga_pipeline` DAG 수동 실행 (▶ 버튼).

## 대시보드

Superset에서 4개 차트 구성:

| 차트 | 유형 | 인사이트 |
|---|---|---|
| Score Distribution | Histogram | 점수 분포 — 대부분 6~8점대에 집중 |
| Genre Popularity vs Quality | Bubble | 장르별 인기도 × 품질 × 작품 수 |
| Score Trend by Year | Line | 연도별 평균 점수 추이 |
| Members vs Score | Scatter | 회원 수와 점수의 상관관계 |

## 문서

| 파일 | 내용 |
|---|---|
| [data_catalog.md](docs/data_catalog.md) | 테이블/컬럼 정의 |
| [business_glossary.md](docs/business_glossary.md) | 지표 및 비즈니스 용어 |
| [lineage.md](docs/lineage.md) | 데이터 흐름도 |
| [data_quality.md](docs/data_quality.md) | dbt 테스트 매트릭스 |
| [architecture_decisions.md](docs/architecture_decisions.md) | 기술 선택 이유 + 문제 해결 과정 |
| [setup.md](docs/setup.md) | 설치 가이드 |
| [project_status.md](docs/project_status.md) | 프로젝트 현황 |
