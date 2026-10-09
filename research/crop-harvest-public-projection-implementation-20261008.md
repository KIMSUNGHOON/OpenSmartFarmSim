# 등록 수확의 닫힌 공개 응답 개발 수용

2026-10-08 22:24 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 영수증](artifacts/crop-harvest-public-projection-implementation-reference-20261008.json)에
원 명령/종료·431 source·실제 저장 조회 기록의 투영·보류 probe·응답 bytes와 정리를 결속했다.
선행 [실제 DB 현재 조회](crop-harvest-current-query-implementation-20261008.md)는 보존한다.

## 구현과 산출물

[공개 투영](../backend/app/api_crop_harvest_replay.py)은 닫힌 `HarvestReplay`/summary/page를 제공한다.
원 result/부모·농장·DB 시각의 UTC 변환·source/계수/배정/code 판본·단위·정확 유리수·미배정·
관측 비교/미완료·source hold·승인false를 보존한다. 모든 중첩 객체는 unknown field를 거부한다.
정확 분자/분모 문자열과 반올림 값·수지/행 hash/원문/전체 행 순서를 검사하며 생장/수확 행을 새로 계산하지 않는다.
HMAC·tenant·raw metadata·서버 key/path·권리 원문은 공개 필드에 넣지 않는다.
이 순수 함수는 현재 표시 권리나 HMAC 진본을 승인하지 않는다. 후속 route가 query open context 안에서
투영/직렬화하고 종료 검사를 통과한 뒤 bytes를 반환해야 한다.

사용자는 영수증에서 summary·6행 전체·3+3행/빈 끝 page와 명시 owned hold probe의 JSON/bytes/hash를 확인할 수 있다.
이는 기존 소유 합성 실제 DB 조회 기록의 공개 투영이며 새 DB/HTTP/SDK/3D 실행은0건이다.

## 통과한 검증

| 대상 | 실제 범위 |
| --- | --- |
| 집중 시험 | [새 시험](../backend/tests/test_api_crop_harvest_replay.py)70개+선행 현재 query 순수23개·고유93개/2.07초·원 종료0. 실제 DB 시험1개 명시 제외, 개발 중 실행은 중복 합산하지 않음 |
| 원 저장 값 | 선행 SCRAM 영수증 hash 고정·6행/summary의 모든 값/단위·원 result/부모·farm·계수/배정·정확 수량·UTC 보존·입력 불변 |
| 페이지 | 전체6행=3+3행·offset6 빈 끝·중복/범위/limit/bool/혼합 거부 |
| 닫힌 구조 | 모든 JSON schema 객체 additionalProperties=false·중첩 unknown/승인true 또는0·출처/계수/code/행 hash 변경 거부 |
| 수량/시간 | 잘못된 단위·음수/무한/bool·분모0/비정규 유리수/반올림 불일치/underflow·배정/미배정·cohort 길이·잘못된 UTC/소수초 거부 |
| 보류/관측 | 별도 owned source-status hold probe의6행과 summary 유지. 관측 차이 음수 허용/미완료 null 유지. 실제 hold 농장 자료는 아님 |
| 재계산/import | 투영 중 RHS/수확 행 생성/등록/proof 함수를 금지. 별도 Python import 종료0·psycopg.connect/socket.create_connection 금지·지정 API 호출0·FD4→4 |
| 응답/자원 | summary12,406bytes·6행59,463bytes·split32,659/29,355/빈2,556bytes·전체2MiB 거부·FD13→13·431 source/자식/임시 경로 정리 |

최종 실행22:22:34→22:22:37 KST, 준비부터2.585초였다. 원120초 상한·nice19·0.1초 감시24표본에서
primary RSS114,249,728bytes≤512MiB, controller/자식 포함 RSS 합198,819,840bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS/WSL 전체/production 부하 수용은 아니다.
22:24:32 KST 별도 감사에서 원 저장/공개 행·summary/UTC·페이지·private 제외·431 source/정리를 대사하고3파일 snapshot을 보존했다.

첫 실행은 backend 외부 cwd로 import 실패2였다. 이후 시험의 KST→UTC 기대값 변환 누락 실패1,
추가 시험의 두 줄 삽입 위치 오류 실패1을 각각 수정했다. 제품 UTC 변환은 유지했으며 초기 실제 종료와 원인은 영수증에 보존했다.

## 다음 한 단계와 외부 의존성

[투영 계약](../contracts/api-crop-harvest-projection-v1.md)의 자식만 체크한다. HTTP/SDK·같은 UTC3D와 replay 부모는 미완료다.
다음 API runtime 부모의 첫 자식은 계약·인증 route module·ASGI/OpenAPI 집중 시험3 core파일이다.
exact 현재 query/reader와 기존 jobs/farm/principal을 결속하고 닫힌 farm/ID/view/offset/limit·읽기 scope,
query open 안의 투영/직렬화·종료 후 현재 계정·no-store·401/403/404/422/503을 검증한다.
그 뒤 명시 설정/factory·실제 SCRAM/HTTPS30초·2MiB/철회/자원 정리→SDK→같은 UTC 표/3D로 진행한다.
현재 내부 page약23초는 HTTP 수용이 아니며 한도를 높이거나 원 행을 생략해 통과시키지 않는다.

이번 공개 투영의 완료 시각만 위 실측으로 확정한다. route·runtime/TLS·SDK·3D 완료 시각/추정은 각 실제 검증 뒤 갱신한다.
전체166일 새 질량 조회·새 DB/HTTP/SDK/3D·전체 Backend/web suite·hosted CI·실제 제품 CLI/품종 검증은 실행하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`, 생산/미래 마진/추천·
원격 Backend/push·구형 native25시간 원 종료 기록 보류를 유지한다. 최종 production 완료일은 독립 자료 확보 일정이 없어 확정하지 않는다.
