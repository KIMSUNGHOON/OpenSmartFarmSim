# 작물 계산과 UI 연결의 코드 대조·구현 경계

2026-10-10. **경계/작업 분해만 수용하며 실행 연동은 미구현이다.**
[후속 계약](../contracts/crop-execution-link-v1.md)의 근거와
[감사 artifact](artifacts/crop-execution-link-boundary-reference-20261010.json)를 남긴다.
기준 source는 `eb4db01b9238f79a579394ed59936c6587cb596a`다.

## 현재 사용자가 보는 것

localhost:5173은 완료된 합성166일의 생장47,809시점/수확47,813행을 실제 DB/API에서 읽는다.
저장 시점 재생과 계산 중 checkpoint 자동 갱신은 다른 기능이다. 후자는 미구현이다.
이번 조사에서 보호 controller/service/PostgreSQL의 기존 PID 시작 identity를 확인했고,
frontend는HTTP200/원 HTML SHA 동일이었다. 사용자 서버·원 결과·고정 bundle은 교체하지 않았다.
새 joint 표/그래프/3D는 전 단계의 격리 검증을 통과했지만 현재5173에 배포하지 않았다.

## 코드에서 확인한 연결 지점과 누락

| 기존 코드/계약 | 확인한 사실 | 필요한 후속 변경 |
| --- | --- | --- |
| [JobStore](../backend/app/job_store.py), [jobs](../backend/app/jobs.py) | simulation 접수/임대·갱신·취소/재시도·불변 입력. canonical64KiB | joint 전용 입력·farm 결속; 같은 intent의 중복 작업 방지 |
| [DB schema](../backend/app/db.py) | job_events는 append-only이며 recorded_at 있음. job_publications는 job당 하나 | 확인 checkpoint의 닫힌 사건/단조 sequence; 별도 큐 불필요 |
| [JobStatus](../backend/app/api_contracts.py), [현재 API](../backend/app/api.py) | 상태 GET은 metadata만. checkpoint/취소 요청 HTTP 경로 없음 | 전용 접수/진행/취소 route; 기존 DTO 유지 |
| [farm binding](../backend/app/crop_climate_joint_farm_binding.py) | prepare/current는 현재 농장·input/rights를 결속. 최대128KiB | 접수에서 수치 계산 없이 검증; job64KiB를 넘으면 거부 |
| [custody](../backend/app/crop_climate_joint_server_custody.py) | 서명 HEAD/원 checkpoint/UTC·분할 advance 있음. job 임대 fence·벽시계 checkpoint 게시 시각 없음 | 현재 임대가 HEAD를 DB 사건에 수용; 파일/DB 원자성 주장 금지 |
| [result store](../backend/app/crop_climate_joint_result_store.py) | terminal 연구 결과만 자체 transaction으로 put | caller transaction hook; job 완료/결과를 같은 DB transaction에 게시 |
| [authored thermal worker](../backend/app/farm_authored_simulation_worker.py) | 현재 임대/취소 검증과 Run/완료의 같은 transaction 패턴 | 패턴만 재사용. joint를 열 Run으로 저장하지 않음 |
| [discovery](../backend/app/deterministic_job_discovery.py), [consumer](../backend/app/deterministic_work.py) | 허용 input/worker/outcome이 닫혀 있으며 joint는 미등록 | joint 판본·정확한 worker/outcome을 명시 등록 |
| [웹 transport](../web/src/api.ts), [joint reader](../web/src/jointCropClimateReplay.ts) | 저장 결과/기존 job 조회. fetch 취소는 서버 작업 취소가 아님 | typed 진행/취소 client·자동 갱신/재접속 |
| [custody 계약](../contracts/crop-climate-joint-server-custody-v1.md) | page는 완료/hold root만. 미완료 prefix는 미게시 | 첫 UI는 진행 수치→terminal 저장3D; 계산 중3D는 별도 수용 |

위 사실은 source/계약 읽기와 AST/route 대조로 확인했다. 새 worker/API의 실행 검증이 아니다.
`jobs.updated_at`은 renew에서도 변경되므로 checkpoint의 진척 시각으로 사용할 수 없다.
DB 사건의 recorded_at을 수용 시각으로 따로 제공하고 원 계산 UTC/상태 조회 시각과 구분한다.
custody HEAD 후 DB 전 crash는 새 임대에서 원 HEAD를 검증·수용하며, 취소된 작업을 재개하지 않는다.
전용 current reader가 사건과 HEAD의 차이를 만나면 갱신 대기를 보이고 새 물리값을 추측하지 않는다.

## 결정과 순서

기존 self-hosted PostgreSQL/파일 저장·worker·FastAPI/typed React를 유지한다.
작물/자원 모듈 전체가 완성될 때까지 합성 실행 접수를 막지 않는다. 준비된 joint 모델/불변 결과와
현재 farm 연결로 착수하고 물/양분·구매 에너지는 그 결과 계약/근거가 준비된 뒤 같은 실행에 연결한다.
독립 농장 자료 확보와 실제 제품 CLI/관문 작업은 별도 경로로 계속한다.

E1 접수 → E2 checkpoint 수용/E3 transaction hook → E4 worker → E5a discovery/E5b consumer →
E6a 현재 진행 DTO/E6b HTTP/E6c runtime → E7 typed client → E8 화면 → E9 실제 DB/TLS/browser 순이다.
E2/E3와 E6a 일부는 의존성이 독립적이지만 WSL에서 수치/DB 시험은 순차 실행한다.
각 task의 최대5 core파일·수용·확인 명령은 [todo](../tasks/todo.md)에 고정했다.
E1–E4 뒤 원 checkpoint/취소/재개·원자 게시를 먼저 검증하고, E6–E9 뒤 사용자 흐름을 검증한다.

첫 작은 합성 실행/UI 연결의 잠정량은 **10–18집중시간**이다. 이전 단계의 실제14–47분 범위와
새로운 임대/파일·DB 결속/재접속 검증의 미관측 비용을 함께 반영한 계획치다.
1일6시간이면2–3집중일이며 자료/모델/기동이 준비됐다는 조건의 단순 달력 구간은10월12–13일이다.
E1/E4/E9 실측 뒤 갱신한다. 현재5173 연결 완료일이나 전체 U3/최종 제품 출시일을 확정한 것이 아니다.
전체 U3의 지역 조사/수집/검토·실제 CLI, U1/U2, 전체 작기·자원/경제와 독립 자료 확보는 별도다.

## 판단과 검증 기록

실제 native Codex CLI의 `2026-10-10T00:20:38.384Z` turn context에서
모델 `gpt-6.1-sol`, effort `xhigh`를 확인했다. 원 LF 행 SHA는
`f0cc7b804c62e57d382b7247c66328224149c770c94fe01f3b999ba11feed5cf`다.
현재 CLI 안에서 재귀 실행은0회다. 모델/effort 확인은 판단 환경의 증거이며 자료/관문 승인이 아니다.

이번 변경은 계약/계획/증거 문서뿐이다. 구현 시험·빌드·hosted CI·전체166일 계산은 재실행하지 않았다.
집중 검증은 source/전이표 대조, 변경 파일/로컬 링크, diff 공백, 보호 PID/기동 HTML 보존이다.
원 handle `6c23bd`는 종료0으로 코드 대조14항목·로컬 링크1,729개·원본2,148항목의 metadata/SHA 일치,
보호3프로세스 identity와5173 HTTP200/원 HTML SHA 보존을 확인했다.
앞선 `c64acc` 종료1은 renew wrapper에서 직접 SQL을 찾은 감사 assertion 오류였다.
실제 `_renew_in_transaction` 위임을 확인해 감사만 수정했고 앱 source는 변경하지 않았다.
처음 schema 검색의 없는 glob과 `python` alias 부재는 수정해 `db.py`/`python3`로 확인했다.
전체 파일 출력의 truncation은 확인이 필요한 범위를 나누어 다시 읽었다.
새 runtime/배포·자동 갱신/취소·원자 완료 게시·미완료 prefix3D는 수용하지 않았다.
실제 품종/농장 작물 Run/독립 국내 자료0건과 G0–G4/생산/미래 마진/추천 hold를 유지한다.
