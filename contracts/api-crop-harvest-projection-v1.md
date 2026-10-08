# 등록 수확 산술의 공개 투영 — v1

2026-10-08. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[현재 조회 수용](../research/crop-harvest-current-query-implementation-20261008.md) 뒤 계약·
`backend/app/api_crop_harvest_replay.py`·`backend/tests/test_api_crop_harvest_replay.py`의3 core파일로 구현한다.

`project_harvest_result(value, *, view='summary', limit=None)`는 검증 query의 record/summary/page/identity를
닫힌 `HarvestReplay`로 투영한다. 판본은 `crop-harvest-replay-v1`이다.
summary는 page/limit 없이, records는1~64행의 현재 선택 page와 명시 limit으로 요청한다.
이 순수 투영은 현재 계정·권리나 HMAC 진본을 승인하지 않는다. 후속 route는 exact query의 open context
안에서 투영/직렬화한 뒤 권리·파일 종료 검사를 통과한 bytes만 반환해야 한다.

공개 필드는 result ID/DB UTC 시각·농장 참조·reference·summary 또는 page다.
reference는 원 result/source·원문/계수/배정·artifact/행 순서·실제 코드/현재 query 판본과
`software_research_only`/`synthetic_research_program`/`not_assessed`·승인false를 보존한다.
summary와 원 선택 행은 저장된 구조/값을 보존한다. 모든 객체는 unknown field를 거부하며
유한 수량/정확 유리수·단위·UTC·음수 허용 범위·배정/미배정·판본/source/hash를 확인한다.
정확 분자/분모는 문자열로 유지하고 반올림 float64 값과 일치시킨다. 금액 계산은 하지 않는다.
계수·수확 행/summary를 새로 계산하지 않는다. 저장 값의 수지/해시 일치 검사는 수행한다.

HMAC·tenant ID·서버 저장 key/path·key/DSN·권리 선언 원문을 공개 필드로 내보내지 않는다.
자료의 `evidence_id` 등 명시적 식별자는 그대로 보존하며 실제 농장/권리 자료로 승격하지 않는다.
summary/page 전체 응답2MiB, page64행·전체 행262,144개 상한을 유지한다.
없는/혼합/잘못된 입력은 `HarvestProjectionHold`이며 일반화한 메시지만 노출한다.
source_status hold는 그대로 전달하며 미완료 이후의 생산량을 만들지 않는다.

## 수용

1. 선행 실제 SCRAM 조회 영수증의6행과 summary/전체·분할·빈 끝 page가 원 ID/UTC/수량/단위를 보존한다.
2. 닫힌 JSON schema와 중첩 unknown·혼합 source/계수/행 hash·잘못된 단위/숫자/유리수/시간·승인true·범위를 거부한다.
3. 반올림/정확 수량·미배정·관측 비교/미완료·source hold를 유지하고 입력을 변경하지 않는다.
4. 원 증거/코드 hash와 public bytes를 대사하고 재계산/등록/proof 함수를 금지한 상태로 검증한다.
   전체2MiB·import/FD·한정 자원/정리·실제 CLI/출력 hash를 기록한다.

이는 소유 합성 응답 투영 수용이다. 새 실제 DB 조회/HTTP/SDK/3D 실행을 대신하지 않는다.
후속 명시 runtime/factory·인증 route/실제 TLS30초·SDK·같은 UTC 표/3D와 전체 작기 질량 부하를 별도 검증한다.
실제 품종/계수·국내 독립 자료/실측 농장 작물 Run0건, G0–G4·생산/미래 마진/추천 보류를 유지한다.

## 로컬 수용과 다음 인증 route

2026-10-08 22:24 KST [검증 보고서](../research/crop-harvest-public-projection-implementation-20261008.md)로
새70개/선행 query 순수23개·집중93개·원 종료0·431 source/정리를 수용했다.
원 저장6행·summary/전체/3+3행·빈 끝·명시 owned hold probe와 닫힌 schema/거부·whole2MiB·
재계산0·별도 import DB/network0/FD4→4를 확인했다. 시험 당시3 core파일 snapshot/hash는 영수증에 보존한다.
summary12,406bytes/6행59,463bytes는 공개 직렬화 크기이며 실제 HTTP 지연/수용은 아니다.
새 DB/HTTP/SDK/3D는0건이다. 투영 자식만 체크하고 API/SDK·replay·관문은 미완료다.

다음은 계약·`backend/app/api_crop_harvest_route.py`·집중 ASGI/OpenAPI 시험3 core파일이다.
exact reader/current query·기존 jobs/farm/principal·읽기 scope·닫힌 요청,
query open 안의 투영/직렬화·종료 뒤 현재 계정·no-store·401/403/404/422/503을 검증한다.
그 뒤 명시 설정/factory/App 조립·실제 SCRAM/HTTPS30초·2MiB→SDK→같은 UTC 표/3D로 진행한다.
