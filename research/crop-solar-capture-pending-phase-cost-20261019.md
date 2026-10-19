# HTTP Pending 수정 후 현재 검증 비용 — 2026-10-19 KST

[로컬58검사와 원 정상24/64 미완료](crop-solar-capture-pending-http-implementation-20261019.md) ·
[기존 진단 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) ·
[기계 증거](artifacts/crop-solar-capture-pending-phase-cost-20261019.json).

상태: **제한된 실제 관측 수용. 정상 실행·새 모델 배포는 미수용**.
판단은 현재 native `gpt-6.1-sol/xhigh`에서 수행했다. 재귀 CLI나 subagent는 실행하지 않았다.

## 실제 독립 단계 관측

CI39211556239/source `ae93637c2e945a1ce73839918f1daf7bbd9f68d2`는
원64/chunk1/조회·재시도360/RSS를 유지하고 기존 `phases` header만 적용했다.
원360초 기준으로 미완료였고 마지막 실제 반환 confirm/advance는15/64·yielded,
UTC `2026-10-01T00:00:30.123456Z`였다. outcome은 없다.

| 경로 | 완료 반환/호출 | 포함 시간(초) |
| --- | ---: | ---: |
| current binding |331/332|329.091|
| registration |665/666|286.174|
| farm read registration |665/666|261.260|
| session guard |263/264|250.486|
| worker confirm |16/16|125.579|
| model advance chunk |16/16|1.102|

시간은 중첩·관찰 overhead를 포함하므로 합산하거나 원 trace-OFF 처리량으로 비교하지 않는다.
기록된 phase exception events는0이며 무오류 전체 실행을 뜻하지 않는다.
마지막 활성 경로는 advance→session guard→current→registration→farm find였다.
최근 사건32개/활성9개를 확인했고 오래된 사건22,895개는 기존 제한에 따라 버렸다.

artifact12168022971/17,362bytes·SHA256
`0970763ade1fccd03b855ff757117a069c50b2da9261b480fe02a04babd5bc91`의
run/head/name/digest·허용5파일/경로/용량을 검증했다.
31594:0에서 원 API ab5a93a…/worker14fe24d… 본문·실제 worker/header/prototype 해시와15단계/UTC를 대사했다.
hosted guard381.921초·두 actor 정리-15·합산 RSS363,909,120bytes·단일126,742,528bytes,
FD7→7·소유 non-zombie/임시0을 확인했다. 정상/DB 정리 proof는 없으며 WSL 용량 수용이 아니다.

## 현재 한 청크의 내부 비용

20775:0은 기존 소유16단계 fixture의 초기0/1단계 후 실제1→2단계를 기존 profiler로 한 번 관측했다.
독립64 입력/actor나 제품 코드를 바꾸지 않았으며 로컬58에 추가 합산하지 않는다.

| 경로 | 호출 | 포함 시간(초) |
| --- | ---: | ---: |
| custody advance |1|10.029|
| current binding |12|9.595|
| registration |24|8.562|
| scoped registration current |23|7.198|
| market current reference verify |23|4.688|
| role audit |183|3.085|

벽시계10.029925초, runtime 연결144회·SQL7,113회/포함4.148578초였다.
current12/registration24/재구성1·원천1,824회와 기존 중복 순서 SHA를 유지했다.
원 UTC02.123456Z→04.123456Z·1→2/yielded, 기존 proof3개의 dev/inode/mode/size/mtime/ctime/hash와
디렉터리 identity를 보존했다. profiler 시간과 SQL 시간도 중첩되므로 합산하지 않는다.

role 감사의 실제 호출자는 JobStore.connect72, ThermalRunStore.connect48,
connect_market24, MarketSourceStore.read_scope24, candidate reference guard13/read_scope2였다.
가장 큰 개별 SQL 누적 위치는 source SELECT1,824회/0.586초였으며,
여러 role 감사 질의가 각각183회 반복됐다. SQL 문자열·매개변수/접속 정보는 공개하지 않았다.

guard43.480초·원본2,148항목/5root/frozen 두 화면·512MiB/PID/합1GiB를 보존했다.
합산 최대 RSS1,007,759,360bytes·FD4→4·소유 PG/임시/passfile0을 확인했다.

## 다음 한 단계와 수용 기준

이번 관측은 현재 등록 검증의 I/O 비용을 뒷받침한다. 다음 후보는 기존 역할 감사 안의
반복 SQL 왕복을 줄이는 작은 변경이다. **아직 구현·채택하지 않았다.** 새 운영 계층은 추가하지 않는다.

1. 기존 audit의 모든 역할/schema/관계/열/권한 사실과 거부 조건을 먼저 대조하고,
   같은 fresh 검사에서 질의를 묶을 수 있는 범위만 변경한다. 권한 결과 캐시나 검사 삭제는 금지한다.
2. 실제 SCRAM의 허용/직접 SQL 거부·변경된 권한/역할/소유자·검사 중 늦은 변경과
   source/principal/pointer/수명 검증을 유지한다. 기존 일반 경로도 보존한다.
3. current12/등록24/재구성1·원천1,824회/중복 순서·원 값/UTC/proof·조회 계산/SQL 변경0,
   worker 정상/hold/취소/임대·HTTP 분류와 5root/자원/정리를 확인한다.
4. 같은 fixture의 paired 실제 비용과 SQL 감소를 확인한 뒤 검토한다.
   감사 호출 수 감소만으로 속도나 원 정상 수용을 주장하지 않는다.
5. 변경 source 원 trace-OFF64가 원 기준·원 값/UTC·두 actor0·정상/DB 정리 proof를 통과해야
   독립 hold→HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용으로 진행한다.

현재 backend/browser 전체·fresh exec/SIGKILL은 이번 source에서 재실행하지 않았다.
실제 농장 Run0·권리/관문 승인False·G0–G4 미평가와 실제 자료/현장·미래·대응 비교 외부 의존성을 유지한다.
전체 제품 완료 날짜는 미정이며 goal은 active다.

93969:0에서 정상24/64 미완료·진단15/64/현재 청크 비용·다음 미구현 후보를 두 UI에 같은 no-store bytes로 게시했다.
두 제품 파일 pin/3syntax·로컬 링크2,318개·원 actor·frozen HTML/2,173파일·5root/상한/FD/소유 정리를 확인했다.
합산 RSS895,012,864bytes였다. UI 코드/DOM/WebGL은 변경·재검사하지 않았다.
