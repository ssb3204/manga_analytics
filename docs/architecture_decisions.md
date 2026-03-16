# 아키텍처 결정 기록

## 기술 스택 선택 이유

### BigQuery — 왜 BigQuery인가?

| 후보 | 장점 | 단점 | 결정 |
|---|---|---|---|
| **BigQuery** | 무료 티어 1TB/월, 서버 관리 불필요, SQL 표준 지원 | DML(MERGE/UPDATE) 무료 티어 불가 | **채택** |
| DuckDB | 완전 무료, 로컬 실행, 빠른 OLAP | 클라우드 경험 증명 불가 | 기각 |
| Snowflake | 업계 표준 | 무료 크레딧 소진 후 과금 | 기각 |

**핵심 이유:** 네이버 웹툰은 GCP 기반 인프라를 사용할 가능성이 높다. BigQuery 경험은 면접에서 직접적인 가치가 있다. DuckDB는 기술적으로 우수하지만, "클라우드 웨어하우스를 다뤄본 적 있다"는 증명이 안 된다.

### dbt — 왜 dbt인가?

SQL 기반 변환 도구 중 사실상 표준. 선택의 여지가 없었다.

- Bronze → Silver → Gold 레이어 구분이 자연스러움
- `ref()`, `source()`로 의존성 자동 관리
- 테스트(`not_null`, `unique`) 내장
- `profiles.yml`로 로컬/Docker 환경 분리 가능

### Airflow — 왜 Airflow인가?

| 후보 | 장점 | 단점 | 결정 |
|---|---|---|---|
| **Airflow** | 업계 표준, Python 기반, UI 제공 | Docker 설정 복잡 | **채택** |
| Prefect | 간편한 설정, 현대적 API | 인지도 낮음 | 기각 |
| GitHub Actions만 | 추가 설정 불필요 | 오케스트레이터라 보기 어려움 | 보조 역할 |

**핵심 이유:** 면접관이 "오케스트레이션 경험 있나요?" 물으면 Airflow가 가장 명확한 답이다.

### Superset — 왜 Superset인가?

| 후보 | 장점 | 단점 | 결정 |
|---|---|---|---|
| **Superset** | 오픈소스, Docker 배포, SQL Lab 지원 | 차트 커스터마이징 제한적 | **채택** |
| Looker Studio | 무료, Google 통합 | 공유 링크 필요, 포트폴리오 재현 어려움 | 기각 |
| Power BI | 강력한 시각화 | Windows 전용, 라이선스 | 기각 |

**핵심 이유:** Docker 하나로 전체 스택을 재현 가능해야 한다. `docker-compose up`으로 Airflow + Superset + BigQuery 연결까지 보여줄 수 있다.

---

## 진행 과정에서 만난 문제와 해결

### 1. 포트 8080 충돌

**문제:** Airflow 기본 포트(8080)가 Oracle TNS Listener(TNSLSNR, PID 5336)에 의해 점유됨.

**해결:** `docker-compose.yml`에서 Airflow 포트를 `8081:8080`으로 변경.

**배운 점:** 로컬 개발 환경에서는 포트 충돌이 흔하다. 기본 포트를 그대로 쓰지 말고 항상 확인할 것.

### 2. Docker 내부 GCP 인증 실패

**문제:** `profiles.yml`에 `method: oauth`만 있었는데, Docker 컨테이너 안에서는 브라우저 기반 OAuth가 불가능.

**해결:** `docker` 타겟을 추가하고 `method: service-account` + `keyfile: /secrets/gcp-key.json` 설정.
DAG에서 `--target docker` 플래그 사용.

```yaml
docker:
  type: bigquery
  method: service-account
  keyfile: /secrets/gcp-key.json
```

**배운 점:** 로컬 개발용 인증과 컨테이너/CI 인증은 반드시 분리해야 한다.

### 3. GCP 키 파일 혼동 (ADC vs Service Account)

**문제:** `gcloud auth application-default login`으로 생성된 ADC 자격증명 파일을 서비스 계정 키로 착각.
BigQuery 클라이언트가 인증 실패.

**해결:** GCP Console에서 서비스 계정 JSON 키를 직접 다운로드하여 `secrets/gcp-key.json`에 배치.

**배운 점:** ADC(`application_default_credentials.json`)와 서비스 계정 키(`*.json`)는 포맷이 다르다.
ADC는 개인 개발용, 서비스 계정 키는 자동화/CI용.

### 4. Superset 관리자 생성 실패

**문제:** `docker-compose.yml`의 startup command에서 `fab create-admin`이 에러 없이 조용히 실패.

**해결:** 컨테이너에 직접 접속하여 수동 생성:
```bash
docker-compose exec superset superset fab create-admin \
  --username admin --firstname Admin --lastname Admin \
  --email admin@example.com --password admin
```

**배운 점:** Docker entrypoint에서 초기화 명령은 실패해도 컨테이너가 정상 시작될 수 있다.
중요한 초기화는 로그를 확인하거나 별도로 검증해야 한다.

### 5. Airflow 403 오류 (Secret Key 불일치)

**문제:** Webserver와 Scheduler가 서로 다른 `secret_key`를 사용하여 세션 검증 실패. 로그에 403 에러 다수 발생.

**해결:** `AIRFLOW__WEBSERVER__SECRET_KEY` 환경변수를 공통 설정에 추가하여 모든 서비스가 동일한 키 사용.

### 6. BigQuery 무료 티어 DML 제한

**문제:** A/B 테스트 중 ingestion 테스트(MERGE 쿼리)가 `403 Billing has not been enabled` 에러로 실패.
BigQuery 무료 티어에서는 DML(MERGE, INSERT, UPDATE, DELETE) 사용 불가.

**해결:** ingestion 테스트를 제거하고, materialization + partitioning 2개 테스트로 축소.

**배운 점:** 무료 티어의 제약을 미리 파악하지 못했다. SELECT + DDL(CREATE TABLE AS SELECT)은 가능하지만, DML은 결제 계정이 필요하다.

### 7. dim_genre 장르명에 특수문자 포함

**문제:** `dim_genre.genre_name`에 `['Action']` 형태로 대괄호와 따옴표가 포함됨.
Superset 차트에서 라벨이 지저분하게 표시.

**해결:** SQL Lab에서 `REPLACE()` 3중 적용:
```sql
REPLACE(REPLACE(REPLACE(g.genre_name, '[', ''), ']', ''), "'", '') AS genre_name
```

### 8. dbt seed DATETIME 파싱 실패

**문제:** 벤치마크 결과 CSV의 `measured_at` 컬럼이 ISO 8601 형식(`2026-03-16T10:45:53+00:00`)인데,
BigQuery DATETIME 타입이 타임존 오프셋(`+00:00`)을 인식하지 못함.

**해결:** `seeds.yml`에서 `column_types: { measured_at: string }`으로 지정.
`fct_perf_comparison` 모델에서 `CAST(measured_at AS TIMESTAMP)`로 변환.

---

## A/B 성능 테스트 결과

### 테스트 1: Materialization (VIEW vs TABLE)

staging 모델(`stg_manga_clean`)을 VIEW와 TABLE로 각각 구체화한 후, 동일한 집계 쿼리를 실행.

| 지표 | VIEW | TABLE | 차이 |
|---|---|---|---|
| 쿼리 시 bytes_processed | 1,775,935 | 1,257,271 | TABLE이 29% 적음 |
| 쿼리 시 slot_ms (평균) | ~52 | ~36 | TABLE이 31% 적음 |
| 쿼리 시 실행시간 | < 1초 | < 1초 | 체감 차이 없음 |

**해석:** TABLE이 bytes와 slot 사용량을 줄여주지만, 67K rows 규모에서는 실행시간 차이가 없다.
대규모 데이터(수백만 rows 이상)에서는 TABLE 구체화가 비용 절감에 유의미할 것.
빌드 시 TABLE은 19.8MB를 스캔하지만, 반복 조회가 많다면 총 비용은 TABLE이 유리하다.

### 테스트 2: Partitioning (없음 vs start_date 파티션 + 클러스터링)

`fct_manga`에 `start_date` 월별 파티션과 `manga_type`, `status_key` 클러스터링을 적용한 후,
날짜 범위 필터(`WHERE start_date BETWEEN '2015-01-01' AND '2023-12-31'`) 쿼리를 실행.

| 지표 | 파티션 없음 | 파티션 적용 | 차이 |
|---|---|---|---|
| 쿼리 시 bytes_processed | 1,242,207 | 0 | 100% 감소 |
| 쿼리 시 slot_ms (평균) | ~29 | ~10 | 66% 감소 |

**해석:** 파티션 프루닝이 정상 작동하여 불필요한 파티션을 완전히 건너뜀.
`bytes_processed = 0`은 BigQuery가 메타데이터만으로 결과를 반환했다는 의미.
날짜 기반 필터가 자주 사용되는 쿼리 패턴이라면 파티셔닝은 규모에 관계없이 효과적이다.

### 결론

67K rows 규모에서 실행시간 차이는 미미하지만, bytes_processed와 slot_ms에서는 명확한 차이가 확인됨.
대규모 환경에서는 이 차이가 비용과 성능에 직접적인 영향을 준다.

**"최적화가 필요한 시점"과 "불필요한 시점"을 데이터로 판단할 수 있는 것이 핵심.**
