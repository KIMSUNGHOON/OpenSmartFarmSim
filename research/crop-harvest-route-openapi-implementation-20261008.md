# 등록 수확의 인증 route·OpenAPI 개발 수용

2026-10-08 22:40 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 영수증](artifacts/crop-harvest-route-openapi-implementation-reference-20261008.json)에
원 명령/종료·436 source·기록된 원값의 ASGI 응답·권한 오류 주입·OpenAPI·자원 정리를 결속했다.
선행 [현재 DB 조회](crop-harvest-current-query-implementation-20261008.md)와
[공개 투영](crop-harvest-public-projection-implementation-20261008.md)은 보존한다.

## 구현과 사용자 확인 산출물

[인증 route](../backend/app/api_crop_harvest_route.py)는
`GET /v1/crop-harvest-research-results/{result_id}`의 별도 installer다.
정확한 reader/query와 기존 jobs/farm/principal을 결속하고 읽기 scope·닫힌 농장/ID/view/offset/limit을 검사한다.
한 query.open 안에서 공개 투영·직렬화를 수행하고 종료 검사가 통과한 뒤 현재 계정을 재검사한다.
없는 결과404·인증401·권한403·자료 보류422·미구성/내부 장애503과 일반 메시지·no-store를 제공한다.
계산·등록·직접 SQL을 실행하지 않는다. 기존 App/runtime에 아직 자동 설치하지 않았다.

사용자는 영수증에서 summary·원6행 전체·3+3행/빈 끝의 응답 JSON/bytes/hash,
조회 후 철회 거부와 새 OpenAPI operation을 확인할 수 있다.
이는 소유 Bearer와 선행 실제 DB 조회 기록을 사용한 ASGI 제어 흐름이다.
현재 query의 권한 경계는 명시적으로 stub/오류 주입했으며 새 DB·실제 TLS·배포 검증은 아니다.

## 통과한 검증

| 대상 | 실제 범위 |
| --- | --- |
| 집중 시험 | [새 route 시험](../backend/tests/test_api_crop_harvest_route.py)72개+선행 공개 투영70개·고유142개/16.50초·원 종료0 |
| 원값·순서 | 선행 공개 응답과 summary/전체6행의 bytes까지 동일·원 result/농장/UTC/단위/정확 수량/미배정/승인false 유지·분할=전체·빈 끝/초과 offset 거부 |
| 권한·현재성 | 읽기 scope·인증·다른 tenant/없는 결과·혼합 reader/부모/jobs/farm/principal 거부. 한 context에서 투영/bytes→종료 검사→close→현재 계정 순서 확인 |
| 변경·오류 | 투영 중 source/credential/tenant/scope의 소유 철회 probe·read/종료/투영/직렬화 오류에 준비된 bytes 비공개·일반 오류·401/403/404/422/503·no-store |
| 요청 | unknown/중복 query·빠진/빈 농장·잘못된 ID·summary paging·body·비정규 정수·offset/limit 범위 거부·query 미진입 |
| OpenAPI | 설치 전 cache 뒤 무효화·새 한 경로·ServiceBearer/READ_SCOPES·요청/응답/오류 한도·기존49 path/156 schema·저장 계약 bytes 보존 |
| 부작용·자원 | 정상 ASGI의 FD12→12·RHS/행 생성/등록/proof 금지·별도 Python import 종료0/connection0/FD4→4·436 source 불변·자식/임시 경로 정리 |

최종 실행22:39:16→22:39:33 KST, 준비부터17.662초였다. 원120초 상한·nice19·0.1초 감시166표본에서
primary RSS212,389,888bytes≤512MiB, controller/자식 포함 RSS 합297,623,552bytes≤1GiB였다.
공유 page를 중복 계산할 수 있는 RSS 합이며 WSL 전체/production 부하 수용은 아니다.
22:40:40 KST 별도 감사에서 선행 공개 bytes·원6행/summary/분할·UTC·종료 검사 순서·철회·
기존 OpenAPI/정리와 시험된3 core파일 snapshot을 대사했다.

초기 실행은70통과/2실패·원 종료1이었다. 시험 observer가 직렬화1회를 기대했으나 선행 투영의
bytes 검사와 route 직렬화가 모두 실행되는 구조였다. 실제 두 정상 응답은200/원값 동일였고,
모든 encoding이 종료 검사 전에 원 bytes와 같음을 요구하도록 시험만 수정했다. 초기 종료 기록을 보존했다.

## 다음 한 단계와 남은 의존성

[route 계약](../contracts/api-crop-harvest-route-v1.md)의 자식만 체크한다. runtime/API·SDK·3D와 replay 부모는 미완료다.
다음은 명시 operator/runtime/factory의 같은 DB·reader·원 query·farm·private DSN/key와 기존 App 조립이다.
default deny/명시 활성·잘못된 결합 거부·새 프로세스 복원·기존 계약/비밀 정리를 검증한 뒤,
실제 SCRAM/HTTPS의 summary/원6행·split·권리/계정·30초/2MiB/자원·정리로 API 부모를 평가한다.
기존 내부 query page약23초는 HTTPS 수용이 아니며 한도를 올리거나 원 행을 생략하지 않는다.
이후 SDK→같은 UTC 표/3D→기후/물·양분/구매 에너지→Decimal 경제 연결을 진행한다.

이번 route 자식의 완료 시각만 위 실측으로 확정한다. 후속 완료 추정은 실제 작업 분해/검증에 따라 갱신한다.
새 실제 DB/TLS·SDK/WebGL·전체166일 질량 조회 부하·전체 backend/web suite·hosted CI/push·제품 CLI는 실행하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`, 생산/미래 마진/추천·
원격 Backend·구형 native25시간 원 종료 기록 보류를 유지한다. 최종 production 날짜는 독립 자료 확보 일정이 없어 확정하지 않는다.
