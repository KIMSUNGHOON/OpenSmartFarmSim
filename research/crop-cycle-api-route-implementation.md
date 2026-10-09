# 긴 작물 연구 결과의 인증 조회 경로

상태: **2026-10-06 KST 로컬 route 소프트웨어 수용**. 판본
`9c414b3d19d48e2ffefb08363365997c061ec9e1`과
[영수증](artifacts/crop-cycle-api-route-reference-20261006.json)을 고정했다.
[공개 투영](crop-cycle-api-projection-implementation.md) 다음 자식이다.
실제 DB 권리·TLS 응답 예산 수용은 다음 runtime 자식에 남는다.

## 구현과 검증

새 GET `/v1/crop-cycle-research-results/{result_id}`는 summary/sample/event를 분리해 읽는다.
한 원 저장 문맥에서 선택 progress와 terminal/manifest를 대사하고, 전체 DTO bytes를 만든 뒤
현재 권리·progress를 재검사한다. threadpool 복귀 뒤 HTTP principal을 다시 확인한다.
중첩 get/page/summary 호출 없이 원 UTC·양을 보존하며 GET 생장 RHS는 실행하지 않는다.
닫힌 query·본문 거부, 기본 비활성503, 인증·권한 오류와 private 이유 비노출을 구현했다.

검증은 **고유146개 분할**이다. 최초141개(초기 route36/OpenAPI63/짧은 투영42)는69.16초,
추가 import/페이지5개는6.44초, 최종 route41개는7.76초였다. 중복36개를 합계에 더하지 않았다.
이 변경은 계산식에 손대지 않았으며 이전25시간 투영 시험을 다시 실행하지 않았다.
선택 offset/limit·마지막 빈 page, source 철회·Bearer 만료·오류 이후 문맥 정리와 원량을 확인했다.

첫 RED는 기본 앱의404 대신503 요구를 위반한 실제 실패1개였다.
API 등록 뒤 `api → cycle storage → operator_config → api_runtime → api`의 순환 import도
실제 OpenAPI 실행에서 발견했다. 저장 모듈 import를 실제 사용 시점으로 옮겨 수정했으며,
새 Python의 api/storage/server 우선3가지 import와 schema-only 기동을 확인했다.
OpenAPI `--check`를 통과했고 모든 기존 path/schema는 이전 저장 수용 판본과 같았다.
새 endpoint만 추가했다. 기존 고정53개 중 계산·저장 등50개는 현재 hash 그대로,
갱신한 API/OpenAPI 인터페이스3개의 이전 hash는 Git `4bb6e53`에 보존했다.

route 시험은 실제 합성 artifact와 실제 Bearer middleware를 사용하되 exact custody 객체의
DB/현재 권리 내부를 stub으로 연결했다. 실제 서버 HMAC·농장 권리·TLS/SCRAM 수용으로
표시하지 않는다. PG cluster0개, native 시험 순차/nice10이며 RSS는 별도 측정하지 않았다.
개발 판단은 실제 Codex CLI `gpt-6.1-sol / xhigh`, 재귀 실행0회였다.

## 다음 한 단계: runtime

`api_runtime.py`·조립 시험·실제 TLS 시험의3 core파일에서 명시 flag/factory 짝과
동일 farm/jobs/principal의 exact store를 조립한다. 실제 SCRAM 등록·서명 저장 결과를
Bearer/TLS로 받아 원 ID/UTC/모든 양을 대사하고, 전체 응답30초/2MiB·재시작/hold·철회/
변조와 서버/DB/FD/lock/비밀 파일 정리를 확인한다. 통과 전 API 부모는 열어 둔다.

그 뒤 client → 같은 저장 ID/UTC 성장 연구3D → 작기 부하 → 생과·자원·경제 순서다.
새 긴 결과 연구3D의10월6–10일 KST 잠정 추정은 실제 TLS 예산/CI 실적으로 갱신한다.
실제 품종/작기 입력·국내 독립 농장 자료0건이며 생산 예측/추천 및 G0–G4는 미수용이다.
