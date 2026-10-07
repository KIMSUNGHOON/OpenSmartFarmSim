# 검증 계산 작기 결과의 공개 투영 — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 현재 코드를 대조했다.
재귀 CLI0회다. 선행 [현재 농장 조회](crop-cycle-calculation-current-query-v1.md)의 실제 수용 뒤
`crop-cycle-calculation-api-runtime` 부모를 아래 작은 순서로 구현한다. 이 계약은 구현 수용이 아니다.

## 현행 코드와 의존성

`api_crop_cycle_replay.py`의 닫힌 공개 형식은 구형 result/artifact ID·engine과
6필드 server dependency만 받는다. 새 결과는 별도 ID·공식 계산 manifest의 input validation,
7필드 server dependency와 runtime role code를 갖는다. 구형 manifest로 변환하면 실제 계산 증명을 잃는다.
기존 API와 응답을 보존하고 새 공개 형식을 추가한다.

`operator_config.py`는 구형·새 server custody의 서명된 `file_helper` dependency다.
그 파일의 선택 필드를 바꾸면 기존 이력의 source 대사가 달라진다.
후속 명시적 설정 연결은 원 loader/file helper를 보존하는 별도 loader에서 처리한다.
현재 `RuntimeLoginPolicy`의 `crop_cycle_calculation_result_storage`는 이미 존재하며 기본 false다.
새 서비스·queue·DB 표·권리 정책을 추가할 근거는 없다.

## 다음 한 단계: 순수 공개 투영

core3파일은 `backend/app/api_crop_cycle_calculation_replay.py`,
`backend/tests/test_api_crop_cycle_calculation_replay.py`, 이 계약이다.
`project_calculation_cycle_result(record, terminal, *, view='summary', page=None, limit=None)`는
새 store의 검증된 기록과 query의 원 terminal/page만 받는다. 농장 권리나 관문을 승인하지 않는다.

공개 schema는 `crop-cycle-calculation-replay-v1`, result ID는 `crop-cycle-verified-result-v1`,
artifact ref는 `crop-cycle-verified-artifact-v1`이다. 실제 상수와 schema를 대사하며 구형 값으로 재표시하지 않는다.
새 manifest는 공식 계산 engine/version/code와 원 `input_validation`을 닫힌 형식 그대로 보존한다.
reference는 새 DB binding의 validation8필드를 보존해 원 validated context SHA,
실제 계산 context SHA와 원 input proof SHA를 각 페이지에서 구분할 수 있어야 한다.
server dependency7필드·runtime role code도 현재 새 store 선언과 대사한다.

기존 단위·50구획 C/N·누적량·진단·UTC·hold/확인 과거와 sample/event 구조는 재사용한다.
sample64/event8·전체 JSON2MiB, 원 cursor·빈 끝 페이지와 byte-short 의미를 유지한다.
관리 사건의 비공개 `input_id`를 제외하는 기존 공개 규칙도 유지한다.
private checkpoint/seed·키/HMAC·증명 원문·경로·tenant/등록 job ID·권리 선언은 공개하지 않는다.
`stored_unpublished_research`, `synthetic_crop_math_only`, `not_assessed`,
`synthetic_research_program`, `unvalidated_for_registered_crop`를 보존한다.

### 수용 기준

1. 자체 소유의 새 공식 계산 artifact와 새 store packet을 정상·관리 사건·수치 hold로 만들고,
   원 summary/manifest와 전체 sample/event·단위/UTC·확인 과거를 공개 JSON과 대사한다.
2. 다른 result/artifact/engine/schema·validation SHA/code/dependency·context/기간/개수·cursor 혼합,
   잘못된 형식/추가 필드·수지·hold 경계와 크기 초과를 거부한다. 기본 계수나 대체 결과는 만들지 않는다.
3. 공개 JSON schema와 실제 canonical 원 행을 검증하고 비공개 필드 비노출을 확인한다.
   입력 객체를 변경하지 않으며 parser/context/terminal QC/RHS를 끈 상태에서 투영한다.
4. 구형 공개 투영 집중 회귀와 새 집중 시험의 실제 명령/종료/출력·source SHA/CLI를 기록한다.
   이 단계는 순수 투영이며 실제 farm/HTTPS/WebGL 수용으로 보고하지 않는다.
5. `operator_config → api_runtime → api → 공개 module`의 기존 import 경로를 보존한다.
   server/store/query 결속 import는 실행 시점에 두고 새 공개 module·operator config·api의
   세 시작 순서를 실제 별도 Python에서 확인한다. import가 계산/파일 쓰기나 authority 생성을 실행하지 않아야 한다.

## 후속 연결과 수용 경계

순수 투영 뒤 명시적 operator 설정/factory → 인증 route/실제 runtime·HTTPS 순서다.
새 loader는 기존 보안 파일 검사와 닫힌 형식을 유지하고 별도 config 판본에서 새 flag를 명시적으로 받는다.
같은 jobs/farm service의 exact 새 store/query만 조립하며 flag/factory 누락·혼합·교체를 거부한다.
새 route는 `/v1/crop-cycle-calculation-research-results/{result_id}`로 기존 경로와 구분한다.
별도 계약에서 OpenAPI·Bearer/Scope·401/403/404/422/503·no-store와 투영 후 철회 검사를 구체화한다.
공개 bytes는 query의 `open(...)` 안에서 준비하고 종료 후 현재 계정도 확인한다.
query 판본/code는 기존과 같은 이름의 응답 헤더로 표시한다.

실제 SCRAM/TLS의 모든 작은 출력·관리 사건·hold·재구성/원량·철회/변조·정리와
전체 응답30초/2MiB를 통과해야 API/runtime 부모를 수용한다. 기존 내부 get39.668745초는 그대로 보존한다.
원 `operator_config.py`·서명 이력과 보존 source를 대사하고, 새 config 지원을 위해 원 proof를 재발행하지 않는다.

380줄의 기존 투영/route와 현행 loader/runtime 경계를 근거로 순수 투영 이식·검증1–2집중시간,
명시적 설정/factory·회귀2–4시간, route·실제 TLS1–2시간의 **총4–8집중시간 잠정**이다.
각 자식의 실제 비용으로 갱신한다. CI 대기·전체166일 등록 prefix 비용/3D·외부 자료 확보는 제외한다.
현재 실제 품종 입력·국내 독립 검증 자료·실제 작물 Run0건, G0–G4 `not_assessed`다.
