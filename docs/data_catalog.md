# 데이터 카탈로그

## 레이어 개요

| 레이어 | 위치 | 구체화 방식 |
|---|---|---|
| Bronze (원시) | `manga_analytics.manga_bronze` | BigQuery 테이블 (WRITE_TRUNCATE) |
| Silver (정제) | `manga_analytics_staging.stg_manga_clean` | BigQuery 뷰 |
| Gold (비즈니스) | `manga_analytics_marts.*` | BigQuery 테이블 |

---

## Bronze: manga_bronze

Kaggle에서 다운로드한 CSV를 변환 없이 그대로 적재한 원시 테이블.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| manga_id | INT64 | MyAnimeList 고유 식별자 |
| title | STRING | 기본 제목 |
| title_english | STRING | 영어 제목 |
| title_japanese | STRING | 일본어 제목 |
| manga_type | STRING | 형식: Manga, Manhwa, Manhua, Novel 등 |
| score | FLOAT64 | 커뮤니티 점수 1~10 (0 = 미평가) |
| scored_by | INT64 | 점수를 매긴 사용자 수 |
| status | STRING | 연재 상태 |
| volumes | INT64 | 권수 (연재 중이면 NULL) |
| chapters | INT64 | 화수 (연재 중이면 NULL) |
| publishing | BOOL | 현재 연재 중 여부 |
| genres | STRING | 쉼표로 구분된 장르 목록 |
| themes | STRING | 쉼표로 구분된 테마 목록 |
| demographic | STRING | 대상 독자층 |
| serialization | STRING | 연재 잡지 또는 플랫폼 |
| authors | STRING | 작가 및 작화가 이름 |
| synopsis | STRING | 작품 줄거리 |
| members | INT64 | 리스트에 추가한 사용자 수 |
| favorites | INT64 | 즐겨찾기로 등록한 사용자 수 |
| rating | STRING | 콘텐츠 등급 |
| start_date | DATE | 최초 연재 시작일 |
| end_date | DATE | 최종 연재 종료일 (연재 중이면 NULL) |

---

## Silver: stg_manga_clean

Bronze 테이블을 기반으로 정제 및 타입 변환을 수행하는 뷰.

### Bronze에서 변경된 사항
- `score = 0`인 경우 NULL로 대체 (미평가 작품)
- 모든 STRING 필드: 빈 문자열을 NULL로 대체, 앞뒤 공백 제거 (TRIM)
- 모든 숫자 필드: SAFE_CAST 적용 (파싱 실패 시 NULL)
- `ingested_at TIMESTAMP` 컬럼 추가
- `manga_id IS NULL`인 행 필터링 (제거)

### Bronze에서 제외된 컬럼
다음 3개 컬럼은 Silver 레이어에서 의도적으로 제외됨:
- `publishing` -- `status` 컬럼과 중복되는 불리언 값
- `themes` -- 분석 범위 외 (장르로 충분)
- `synopsis` -- 텍스트 분석 미사용, 저장 비용 절감

### Silver 컬럼 목록

| 컬럼 | 타입 | 설명 |
|---|---|---|
| manga_id | INT64 | MyAnimeList 고유 식별자 |
| title | STRING | 기본 제목 |
| title_english | STRING | 영어 제목 |
| title_japanese | STRING | 일본어 제목 |
| manga_type | STRING | 형식 (Manga, Manhwa 등) |
| score | FLOAT64 | 커뮤니티 점수 (미평가 시 NULL) |
| scored_by | INT64 | 점수를 매긴 사용자 수 |
| status | STRING | 연재 상태 |
| volumes | INT64 | 권수 |
| chapters | INT64 | 화수 |
| genres | STRING | 쉼표로 구분된 장르 목록 |
| demographic | STRING | 대상 독자층 |
| serialization | STRING | 연재 잡지 또는 플랫폼 |
| authors | STRING | 작가 및 작화가 이름 |
| members | INT64 | 리스트에 추가한 사용자 수 |
| favorites | INT64 | 즐겨찾기 사용자 수 |
| rating | STRING | 콘텐츠 등급 |
| start_date | DATE | 최초 연재 시작일 |
| end_date | DATE | 최종 연재 종료일 |
| ingested_at | TIMESTAMP | 데이터 적재 시각 |

---

## Gold 테이블

### fct_manga
작품당 1행. 디멘전 테이블에 대한 외래 키 포함.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| manga_id | INT64 | 기본 키 |
| title | STRING | 기본 제목 |
| title_english | STRING | 영어 제목 |
| title_japanese | STRING | 일본어 제목 |
| manga_type | STRING | 형식 |
| score | FLOAT64 | 커뮤니티 점수 (미평가 시 NULL) |
| scored_by | INT64 | 점수를 매긴 사용자 수 |
| volumes | INT64 | 권수 |
| chapters | INT64 | 화수 |
| members | INT64 | 리스트 추가 사용자 수 |
| favorites | INT64 | 즐겨찾기 사용자 수 |
| start_date | DATE | 최초 연재 시작일 |
| end_date | DATE | 최종 연재 종료일 |
| status_key | STRING | FK -> dim_status.status_key |
| rating_key | STRING | FK -> dim_rating.rating_key |
| ingested_at | TIMESTAMP | 데이터 적재 시각 |

### dim_status
연재 상태 디멘전.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| status_key | STRING | status_label의 MD5 해시 (PK) |
| status_label | STRING | 상태 텍스트 (Finished, Publishing 등) |

### dim_rating
콘텐츠 등급 디멘전.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| rating_key | STRING | rating_label의 MD5 해시 (PK) |
| rating_label | STRING | 콘텐츠 등급 (PG-13, R+ 등) |

### dim_genre
장르 디멘전.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| genre_id | STRING | genre_name의 MD5 해시 (PK) |
| genre_name | STRING | 장르명 (Action, Romance 등) |

### bridge_manga_genre
작품-장르 다대다 관계를 위한 브릿지 테이블.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| manga_id | INT64 | FK -> fct_manga.manga_id |
| genre_id | STRING | FK -> dim_genre.genre_id |
