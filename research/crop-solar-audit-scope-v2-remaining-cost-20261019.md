# 감사 scope v2 이후 실제 청크 비용 — 2026-10-19 KST

[선행116검사/원 독립22/64 미완료](market-current-reference-audit-scope-v2-implementation-20261019.md) ·
[관측 계약](../contracts/crop-solar-current-binding-cost-v1.md) ·
[기계 증거](artifacts/crop-solar-audit-scope-v2-remaining-cost-20261019.json).

## 현재 코드의 실제 관측

29243:0에서 기존 소유 합성16단계 fixture의 초기0/1단계를 계산한 뒤 실제1→2단계를
한 번 계측했다. 원 독립64 입력/actor를 바꾼 실행이 아니다. 관측1검사를 통과했으며
기존116개 컴포넌트 검사 수에는 더하지 않는다. 제품 코드는 변경하지 않았다.

| 항목 | 실제 관측 |
| --- | ---: |
| current / 등록 / 전체 재구성 |12 / 24 / 1|
| 원천 읽기 |1,824|
| DB 연결 / 전체 role 감사 |144 / 183|
| SQL execute 횟수 / 누적 초 |7,113 / 3.930564|
| 실제 advance 벽시계 초 |9.707024|
| 등록 read 포함 초 |7.575253|
| 반복 참조 verify 포함 초 |4.544744|
| 전체 role 감사 포함 초 |2.934992|

감사 호출자는 JobStore.connect72회, ThermalRunStore.connect48회,
connect_market24회, source read_scope24회, candidate reference_guard13회와
candidate read_scope2회였다. 작업/열 연결의120감사 포함 시간은 각각1.226098/0.799068초다.
시간은 중첩·profiler/SQL 관측 overhead를 포함하므로 합산하거나 native 처리량으로 해석하지 않는다.

원천1,824회의 중복/순서 SHA와 원 UTC `00:00:02.123456Z`→`00:00:04.123456Z`,
1→2/yielded, 이전 확정 proof3개의 dev/inode/mode/크기/시각/hash와 directory identity를 보존했다.
source pin은 현재 v2와 같다. guard43.480초·합 RSS984,326,144bytes·FD4→4·소유 비좀비/PG/
임시/passfile0, 원5root·2,148항목·frozen source/assets·두 UI·512MiB/PID/합1GiB를 확인했다.
SQL/매개변수·접속정보·개인 자료는 기록하지 않았다.

## 다음 한 단계: 실제 전체 실행 경로 관측

원 독립 CI39190518816은 원360초 제한/감독382.909초·종료 뒤22/64로 미완료다.
앞선25/64와의 차이를 이 한 청크 표본으로 설명하거나 개선/회귀로 판정하지 않는다.
이 관측은 custody advance이며 전체 worker의 확인/채택/재시도와 동시 API 비용을 포괄하지 않는다.

다음은 [기존 제한된 단계 계측](../contracts/crop-solar-worker-progress-diagnostics-v1.md)의
`worker-api` 선택을 현재 코드에 적용하는 단일 진단이다. 새 계산·권한·저장 구조를 먼저 추가하지 않는다.
원 actor 본문/입력64/chunk1/조회·재시도/360초/RSS를 유지하고 기존 선택 계측 header만 붙인다.
실제 head/app hash·header hash·worker 단계별 호출/종료/중첩 시간·확인/전진/채택/결과,
API 상태/허용 오류 코드·예외 타입/위치와 실제 종료/자원을 기록한다.
관측은 제한된 journal이며 원문 body/인증/SQL·개인 자료는 수집하지 않는다.

수용 기준은 정확한 source/원 본문/선택 계측, bounded journal과 artifact 검증,
실제 단계/HTTP/종료·정리 증거로 **최소 다음 수정 범위를 정하는 것**이다.
계측에 따른 overhead가 있어 정상 완료나 처리량 수용에 쓰지 않는다. 계측에서 완료돼도
원 계측 OFF64 정상은 별도로 통과해야 한다. 같은 실패 normal CI를 반복하지 않는다.

현재 native `gpt-6.1-sol/xhigh`에서 관측·판단을 수행했으며 재귀 CLI/서브에이전트는 없다.
현재 전체 backend/browser 회귀·새 Solar 배포·실제 농장 Run/권리·G0–G4·전체 완료일은
미실행/미수용/미정이다. 실제 농장 Run0/G0–G4 미평가·goal active를 유지한다.

33338:0에서 실제22/64 미완료·현재 관측/다음 진단을5173/5174에 no-store 동일 bytes로 게시했다.
현재 source/문서 링크·원 actor/query/probe/역할/worker·HTML/환기 frozen2,173파일,
5root/원본/상한/FD·소유 정리를 확인했다. UI 코드·DOM/WebGL은 변경하거나 재검사하지 않았다.
