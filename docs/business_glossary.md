# 비즈니스 용어집

## 지표 정의

| 지표 | 정의 | 출처 |
|---|---|---|
| avg_score | AVG(score) WHERE scored_by > 0 | fct_manga |
| total_members | SUM(members) | fct_manga |
| completion_rate | COUNT(*) WHERE status='Finished' / COUNT(*) | fct_manga + dim_status |
| top_genre_by_score | avg_score가 가장 높은 genre_name | dim_genre + bridge_manga_genre + fct_manga |
| publishing_ratio | COUNT(*) WHERE status='Publishing' / COUNT(*) | fct_manga + dim_status |
| score_distribution | COUNT(*) GROUP BY FLOOR(score) | fct_manga |

## 용어

**Manga** -- 일본 만화 형식. 오른쪽에서 왼쪽으로 읽음.

**Manhwa** -- 한국 만화 형식. 왼쪽에서 오른쪽으로 읽음.

**Score** -- MyAnimeList 사용자가 부여한 가중 평균 점수. 범위 1~10. 평가 인원(scored_by)이 약 100명 미만인 작품은 신뢰도가 낮음.

**Members** -- MAL에서 리스트에 추가한 사용자 수 (읽는 중, 완독, 중단 등 모든 상태 포함). 인기도의 대리 지표.

**Favorites** -- MAL에서 즐겨찾기로 등록한 사용자 수. Members보다 강한 관심 신호.

**Scored_by** -- 점수를 매긴 사용자 수. 저신호 데이터를 필터링하는 데 사용.

**Manga_type** -- 작품 형식 유형. Manga, Manhwa, Manhua, Novel, Light Novel, One-shot 등.

**Demographic** -- 대상 독자층. Shounen(소년), Shoujo(소녀), Seinen(청년), Josei(여성) 등.

**Serialization** -- 작품이 연재된 잡지 또는 플랫폼명.

**Authors** -- 원작자 및 작화가 이름.

**Status 값:**
- `Finished` -- 완결. 추가 연재 없음
- `Publishing` -- 현재 연재 중
- `On Hiatus` -- 일시 휴재
- `Discontinued` -- 완결 없이 중단
- `Not yet published` -- 발표되었으나 연재 미시작

**Rating 값:**
- `G` -- 전체 이용가
- `PG` -- 아동
- `PG-13` -- 13세 이상
- `R - 17+` -- 폭력 및 비속어 포함
- `R+` -- 경미한 노출
- `Rx` -- 성인 전용 콘텐츠

## 세그먼트 정의

**평가된 작품 (Scored titles)** -- manga_id WHERE score IS NOT NULL AND scored_by > 100

**인기 작품 (Popular titles)** -- manga_id WHERE members > 10,000

**완결 시리즈 (Completed series)** -- manga_id WHERE status = 'Finished' AND end_date IS NOT NULL
