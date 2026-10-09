# 새 검증 계산 결과의 서명 DB 게시·현재 조회 — 로컬 수용

2026-10-07 KST. [DB 계약](../contracts/crop-cycle-calculation-db-custody-v1.md)의
`crop-cycle-calculation-result-publication`을 소유 합성 등록 농장의 작은 소프트웨어 범위에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-result-publication-reference-20261007.json)에 실제 호출/출력,
판본별 source SHA·실패/정정·비용·정리를 보존했다. native Codex CLI `gpt-6.1-sol / xhigh`이며 재귀 CLI0회다.

## 구현

[새 store](../backend/app/crop_cycle_calculation_result_store.py)는266줄이며 exact 새 서버/공식 계산 문맥과
별도 결과 ID·artifact ref·HMAC domain을 사용한다. 원242줄 store의 명시적인 이름/판본 이식 뒤
21함수 중17함수 AST가 같고4함수의 새 binding/code pin/flag/context 결속을 검토했다.
구형 표·행·서명·원55 source와 모든 이전 artifact bytes를 보존한다.

- DB key는 서버 key와 다른32..4096bytes다. 기본False의 명시 새 역할 flag·현재 authority가 필요하다.
- 닫힌9필드 binding·input9개/validation8개와 storage/server/schema/dependency/runtime-role code5개를 대사한다.
  context·입력 proof 코드/해시와 원 signed progress/HEAD·result ID·DB HMAC/column을 확인한다.
- 원 nonblocking root/journal·DB advisory transaction lock 아래 terminal만 원자 게시한다.
  동일 요청은 원 bytes/hash/최초 recorded_at으로 돌아오며 다른 결과·미완료·잘못된 key/tenant는 거부한다.
- commit 직전 철회는 rollback, commit 직후 철회는 반환 hold와 비공개 audit row 보존이다.
  get/page/summary는 원량·UTC·manifest/수치 hold를 현재 권리 아래 반환하고 RHS를 실행하지 않는다.

새 service/queue/framework는 추가하지 않았다. fresh 역할을 사용하는 시험이며 배포된 DB 역할 migration이나
operator-config/API runtime의 새 판본 선택 연결을 수용한 것은 아니다.

## 실제 검증과 실패 정정

| 실행 | 실제 결과 |
| --- | --- |
| 최종 순수 metadata 시험 | 81통과/0.99초·종료0 |
| 첫 실제 SCRAM 전체15개 | 14통과/재개 fixture1실패·1,104.60초·종료1 |
| 해당 재개 시험 수정 후 | 1통과/14제외·98.13초·종료0 |

**동일 제품 module에서 고유96개(순수81·실제 DB15)를 분할 수용**한다.
첫 farm 실패는 최초 경계만 처리하는 `max_transitions=1`로 실제0걸음인데7걸음을 기대한 시험 오류다.
이 시험 예산만11로 바꿔 실제7걸음 중단/동일 체크포인트 재개를 검증했다.
다른 시험 함수의 AST와 제품 source는 그대로다. 다른14개를 재실행하거나 단일 전체96개 성공으로 표시하지 않는다.
앞75개 순수·초기 정상1개/140.39초는 중복 합산하지 않는다.
초기 module 부재는 수집 오류이고, 초기 이식판의 새9필드 binding 거부는 실제 정상 경로 실패로 기록했다.
계약의 수용 상태 문서는 시험 후 갱신했으며 시험 당시7 source와 현재 코드/계약 SHA를 따로 보존한다.

실제 PostgreSQL16.15/SCRAM에서 다음을 확인했다.

- 등록 계산120걸음·3시점/0사건의 put/retry/get/sample/event/summary 원값·UTC와 단일 새 row.
- 새 서비스 재구성과 실제 fork child의 동일 결과/페이지·종료0/정리. fork는 fresh exec가 아니다.
- 실제7→120걸음 중단 재개·전체121상태/clock/counter 체크포인트 동일성과 연속 기준 원 페이지.
  등록 농장 재개는 같은 Python의 새 서비스이며 별도 exec로 보고하지 않는다.
- input/write-scope/source 각각의 실제 INSERT 전후 철회6경우, commit 전 rollback0/후 audit row1과 반환 거부.
- 실제 별도 DB 연결의 advisory lock pending, 없는 ID, default flag·서버 key/짧은 key/다른 tenant·yielded 거부.
- 유효 HMAC로 재작성한 proof/input validation/code/farm과 잘못된 DB key 거부.
- 원 수치 hold 이유/확인 과거·manifest 보존과 summary 복사 후 권리 철회의 반환 거부.
- 같은 tenant/study/revision의 원 signed DB row와 새 row 실제 공존, 원 bytes/hash/최초 시각과11개 파일 SHA/mode 보존.
  두 store의 혼합 생성도 거부한다. SQL 형식 fixture를 signed 결과로 대신한 시험이 아니다.
- 실제 DB 변조3개·HEAD/header/proof/input root 파일 변조4개와 새 SELECT grant 철회 거부,
  원 기록 복구·FD13→13. 모든 게시/조회에서 advance/RHS를 금지했다.

## 비용·자원과 남은 HTTP 기준

초기 정상 사례는 계산26.804025초·put23.591038초·retry23.645157초·get7.898755초,
sample7.914512초·event8.002783초·summary8.013024초, payload8,893bytes다.
다른 전체 실행의 정상 사례는 계산29.875422초·put25.791029초·retry24.153566초·
**get39.668745초**·sample8.170463초·event8.242983초·summary8.600019초였다.
이 관측 차이의 원인은 확정하지 않았으며 작은 내부 호출도30초를 넘은 사실을 보존한다.
이 저장 수용을 HTTP30초/2MiB나 전체 작기 성능으로 넓히지 않는다.

첫 전체 호출 wall1,105.302937초·주 pytest의200ms 표본 최대 VmRSS132,583,424bytes,
수정 재개 호출 wall98.619489초·표본126,803,968bytes다. PG/모든 자식 합계나 확정 peak는 아니다.
정상/fork의 모든 소유 context가 닫혔고 세 실제 PG 실행의 schema/role/passfile 잔존0,
PG PID/data·임시 test tree 부재를 확인했다. private 증거는0700 지속 경로/0400 기록으로 보존한다.

## 부모 수용과 다음 단계

선행 [새 schema/역할](crop-cycle-calculation-result-schema-implementation-20261007.md)과 함께
작은 DB 부모를 수용한다. [현재 농장 authority](crop-cycle-calculation-farm-authority-implementation-20261007.md),
[서버 계산/서명](crop-cycle-calculation-server-custody-implementation-20261007.md), 이 DB 수용으로
작은 `crop-cycle-calculation-farm-binding` 부모의 세 자식도 갖췄다.
전체 등록 작기의 누적 proof/재열기·저장·조회·복원 비용은 해당 부모와 구분해 기존 replay-restore에서 검증한다.

publication의1.5–3.5집중시간 잠정 추정은10월7일 수용으로 대체한다.
다음은 전체 등록 경로 비용 측정과 새 결과 proof/현재 조회·공개 projection/runtime 판본 연결이다.
원 출력/수지·현재 권리/변조 검사를 유지하며 실제 HTTPS30초/2MiB·같은 ID/UTC3D를 검증한다.
[순수166일 완료](crop-cycle-full-rhs-durable-completed-20261007.md)는 해당 수치 실험의 증거이며
이를 새 농장 DB 이력으로 바꾸지 않는다. 이후 수확/생과·물/양분/구매 에너지·Decimal 경제를 연결한다.

전체 backend·새 hosted CI·전체166일 등록 DB/API/3D, 이번 publication의 등록 농장 fresh Python exec는
실행하지 않았다. 이전 서버의 fresh exec 증거와 이번 fork/동일 프로세스 재구성을 구분한다.
채택 실제 품종 입력·독립 국내 자료·실제 작물 Run은0건이며 G0–G4 `not_assessed`, 생산 예측·미래 마진·추천은 보류다.
전체 경로와 외부 자료 확보의 실제 측정 전에는 최종 제품 완료 날짜를 확정하지 않는다.
