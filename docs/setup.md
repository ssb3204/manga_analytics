# 설정 가이드

## 사전 요구사항

- GCP 프로젝트가 생성된 Google 계정
- GCP 프로젝트에서 BigQuery API 활성화
- BigQuery Data Editor + Job User 역할이 부여된 GCP 서비스 계정
- Python 3.11+
- dbt-bigquery 설치 (`pip install dbt-bigquery`)
- Kaggle에서 MyAnimeList manga CSV 다운로드 -> `data/raw/manga.csv`에 배치

## 1. GCP 설정

1. GCP 프로젝트 생성, 프로젝트 ID 기록
2. BigQuery API 활성화
3. 데이터셋 생성: `manga_analytics` (위치: US)
4. 서비스 계정 생성 -> JSON 키 다운로드
5. 환경 변수 설정:
   ```bash
   export GCP_PROJECT_ID=your-project-id
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

## 2. 인제스천 실행 (Bronze)

```bash
python ingestion/fetch_raw.py
```

예상 출력:
```
Loaded 67273 rows into your-project-id.manga_analytics.manga_bronze
```

이 스크립트는 `data/raw/manga.csv`를 BigQuery의 `manga_analytics.manga_bronze` 테이블에 WRITE_TRUNCATE 방식으로 적재함. 반복 실행해도 동일한 결과 보장 (멱등성).

## 3. dbt 실행 (Silver + Gold)

```bash
cd dbt
dbt run --select staging --profiles-dir .
dbt run --select marts --profiles-dir .
dbt test --profiles-dir .
```

- staging 실행: `manga_analytics_staging.stg_manga_clean` 뷰 생성
- marts 실행: `manga_analytics_marts` 데이터셋에 fct_manga, dim_status, dim_rating, dim_genre, bridge_manga_genre 테이블 생성
- test 실행: not_null, unique 테스트 통과 확인

모든 모델은 `[OK]`, 모든 테스트는 `Pass`가 표시되어야 함.

## 4. 분석 쿼리 확인

BigQuery 콘솔을 열고 `warehouse/analytics/` 폴더의 각 파일 실행:

| 파일 | 설명 |
|---|---|
| top_manga_by_score.sql | 점수 기준 상위 작품 순위 반환 |
| genre_performance.sql | 장르별 평균 점수 반환 |
| score_trend_by_year.sql | 연도별 평균 점수 반환 |
| completion_vs_score.sql | 연재 상태별 점수 비교 반환 |
| member_score_correlation.sql | 회원 수 구간별 평균 점수 반환 |
| publishing_distribution.sql | NTILE 십분위 분포 반환 |

> **참고:** 분석 SQL 파일들은 `manga_analytics.fct_manga`를 참조하지만, dbt가 생성하는 실제 데이터셋은 `manga_analytics_marts`임. 실행 전에 데이터셋 이름을 `manga_analytics_marts`로 변경 필요.

## 5. GitHub Actions

GitHub 저장소에 다음 시크릿 추가:
- `GCP_PROJECT_ID` -- GCP 프로젝트 ID
- `GCP_SERVICE_ACCOUNT_KEY` -- 서비스 계정 JSON 키 전체 내용

파이프라인은 매주 월요일 06:00 UTC에 자동 실행되거나, `workflow_dispatch`를 통해 수동 실행 가능.

### 파이프라인 구조
1. **ingest** 잡: Python 환경 설정 -> GCP 인증 -> `fetch_raw.py` 실행
2. **dbt_run** 잡 (ingest 완료 후 실행): dbt-bigquery 설치 -> GCP 인증 -> staging 실행 -> marts 실행 -> 테스트 실행

## 6. Looker Studio 대시보드

1. lookerstudio.google.com 접속
2. 새 보고서 생성 -> 데이터 소스 추가 -> BigQuery
3. `manga_analytics_marts` 데이터셋 선택
4. fct_manga, dim_genre, bridge_manga_genre 연결
5. 대시보드 페이지 구성:
   - **개요 페이지**: KPI 카드 (총 작품 수, 평균 점수, 총 회원 수, 완결 비율), 상위 장르 막대 차트, 상태 분포 원형 차트
   - **점수 분석 페이지**: 점수 분포 히스토그램, 회원 수 vs 점수 산점도, 연도별 평균 점수 추이선
   - **장르 심층 분석 페이지**: 장르 x 상태 히트맵, 상위 장르별 회원 수 막대 차트, 등급/상태 필터
6. 게시 -> 공유 -> 링크가 있는 모든 사용자에게 공개

## 문제 해결

### fetch_raw.py 실행 시 인증 오류
- `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수가 올바른 JSON 키 경로를 가리키는지 확인
- 서비스 계정에 BigQuery Data Editor + Job User 역할이 있는지 확인

### dbt run 시 데이터셋 미발견
- `GCP_PROJECT_ID` 환경 변수가 설정되어 있는지 확인
- `manga_analytics` 데이터셋이 BigQuery에 존재하는지 확인 (staging, marts 데이터셋은 dbt가 자동 생성)

### dbt test 실패
- `dbt run`이 성공적으로 완료된 후 테스트 실행
- BigQuery 콘솔에서 해당 테이블의 데이터를 직접 확인
