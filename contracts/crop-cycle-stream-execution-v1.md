# 분할 입력의 실제 작물 연구 계산 — v1

상태: **실제 분할 입력/RHS 연구 실행의 로컬 수용**, 2026-10-05 KST.
[144개 집중/25시간11,400걸음·별도 Python7개·검토](../research/crop-cycle-stream-execution-implementation.md),
[실제 실행/복원](../research/artifacts/crop-cycle-stream-execution-reference-20261005.json),
[CLI·최종 파일/초안·검증 영수증](../research/artifacts/crop-cycle-stream-execution-implementation-reference-20261005.json).
작업 `crop-cycle-stream-execution`.
현재 Codex CLI `gpt-6.1-sol / xhigh`의 실제 turn metadata를 기록한다. CLI를 재귀 실행하지 않는다.
[원 실행 의미](crop-cycle-execution-v1.md), [짧은 continuation](crop-cycle-continuation-v1.md),
[입력 packet](crop-cycle-input-stream-v1.md)의 수용된 코드와 한도/hash를 보존한다.

## 범위와 다음 단계

이 단계는 사전 검증된 자작 합성 packet을 실제 고정 startup RHS에 연결한다.
1일/10,000걸음 초과 실행을 검증하되 실제 농장·품종·전체 작기·생과 kg·구매 자원·수익·추천을
승인하지 않는다. scope는 `software_research_only`다. 국내 독립 농장 자료는 병행 확보하며
개발의 선행으로 잠그지 않는다. 실제 자료 채택/게시에는 기존 G0–G4를 유지한다.

산출물은 새 순수 실행 모듈·집중 시험·이 계약이다. 후속은 불변 cycle 결과 저장/reader,
현재 farm/source 권리 custody/API, 같은 저장 ID/UTC의 3D, 실제 RHS 전체 작기 부하,
생과/자원/경제 연결 순서다. 새 queue/service/Framework는 이 단계의 선행이 아니다.

## 고정 context와 bounded 원 격자 index

`prepare_context(reader, growth_profile=…, cohort_profile=…, transport_profile=…)`는 정확한
profile형·hash와 열려 있는 수용된 `InputPacket`만 받는다. full preflight는 packet open 때
수행하며 HTTP 조회/각 chunk에서 전체 입력을 다시 읽지 않는다. caller가 reader를 닫는다.

원 경계는 segment 끝 ∪ 계산 anchor ∪ event다. 출력은 anchor 부분집합이다.
128경계마다 원 input cursor/직전 경계/누적 예정 RK4걸음/전역 경계 offset만 index에 둔다.
각 stream 최대131,072이므로 index 최대3,072페이지다. 상세 경계는 한 페이지≤128개,
RHS adapter는 한 forcing 구간만 보관한다. index 작성 때 예정 걸음/경계/종료 cursor를
reader의 원 계획과 대사한다. index hash를 새 manifest/root에 고정한다.
출력 선택 변경은 input/root를 바꾸며 계산 ID/원 grid는 유지한다.

기존 `_Evaluator`를 별도 고정 adapter로 사용한다. adapter의 segment/clock은 현재 원 구간,
seed와 calculated-state ID는 전체 프로그램 초기 상태다. adapter 내부 segment index0을
checkpoint의 전역 active index와 구분한다. 원 physical closure를 추출/수정하지 않는다.

manifest는 실행/physical/rate 판본, input root/계산 hash, grid index hash, 새 실행·기존
continuation/reader/physical code hashes, 3개 profile hashes, 정책 hashes, solver,
Python 판본, UTC/정확한 온도 clock 규칙을 포함한다. root는 이 manifest의 canonical SHA다.
SHA는 진본·권한·현재 권리·과거 chain 승인 증거가 아니다.
context는 이 모듈이 생성한 신뢰된 process 내부 객체다. Python 내부 필드/함수를 공격자가
재작성할 수 있는 실행 환경의 인증 경계가 아니다. 외부 입력은 닫힌 packet/checkpoint를 검증한다.

## 새 checkpoint와 chunk

`start(context)`는 아직 확인된 과거가 없는 `initial-ready`다.
`advance_chunk(context, checkpoint, {max_steps, max_transitions})`의 각 예산은 정수1..10,000이다.
각 transition은 원 RK4걸음 또는 원 경계 commit이다. chunk에 새 시간 경계를 추가하지 않는다.
delta는 transition 수로 제한되며 최대10,000 sample/event다. 이 메모리 상한은 production
페이지/API 상한이 아니다. production wall-time/입력·출력 배치는 후속 실제 부하/저장에서 고정한다.
전체 예정/완료 steps는 원 solver max_steps≤40,000,000 이내다. 기간≤366일의 reader 한도는
연구 입력의 유한 상한이며 해당 규모의 RHS 성능/정확도 수용을 뜻하지 않는다.

checkpoint는 닫힌 JSON 객체로 다음 항목만 허용한다.

| 항목 | 검사/의미 |
| --- | --- |
| version/root_sha256/calculated_state_id | 새 실행 context와 동일 |
| y/seed | 기관5+N50+C50+누적16의121 float64; finite/nonnegative, 원 seed 동일 |
| at/phase/boundary_cursor | initial-ready, step-end, boundary-committed; cursor는 commit된 원 경계 수 |
| steps/event_count/active_segment/output_cursor/event_cursor/sequence | 원 index/페이지로 재생한 전역 위치와 동일; sequence=steps+commit 경계 수 |
| clock | active 원 구간의 exact Fraction prefix/slope/start와 동일; y의 온도 합은 정확한 clock과 binary 동일 |
| parent_sha256/output_prefix_sha256/event_prefix_sha256 | 명시 SHA/빈 prefix 규칙; 저장 chain/진본 검증은 후속 |
| checkpoint_sha256 | canonical closed payload SHA;≤64KiB UTF-8, 중복 key/nonfinite 상수 거부 |

cursor 위치·걸음 수는 전체 경계를 다시 실행하지 않고 해당128페이지와 prefix로 검사한다.
step-end의 at는 직전 commit 경계에서 원 h 배수 또는 다음 경계의 나머지 걸음 끝이다.
boundary-committed는 직전 경계와 같은 at다. counters는 commit된 prefix까지만 센다.
현재 active forcing와 사건/출력의 prefix를 새 chunk seed로 초기화하지 않는다.
guard/전역 ledger는 operations=global steps+global event_count와 원 seed를 사용한다.

## 실제 단계 순서와 실패

원 k1–k4/update/정확한 clock/step-end RHS·수지 순서를 보존한다. 경계에서는 forcing 변경,
제거 후보, boundary RHS·수지 확인, 사건 journal/counter, 선택 output, 다음 cursor 순서다.
t0 사건, forcing/event/output 충돌, pending 경계의 복원을 정확히 한 번 처리한다.

반환은 `yielded`/`completed`/`hold`, scope/manifest, 전역 steps/planned_steps,
output_start/event_start, 이번 samples/events, checkpoint다. hold는 checkpoint=None,
원 hold(at/phase/reason), 확인된 과거와 last_confirmed만 담는다. 실패 trial은 정상 checkpoint가 아니다.
typed `CycleStreamExecutionRejected`는 잘못된 context/checkpoint/budget이다.
입력 hash/파일 오류는 reader의 typed rejection이 전파된다. 취소/crash/외부 예외를 수치 hold로 바꾸지 않는다.
순수 단계에서 atomic commit/current rights/lease/cancel 저장을 승인하지 않는다.

## 수용 절차

1. 기존6프로그램×복수 step/transition 예산에서 전체 sample/state/16누적/4수지·진단,
   사건·steps/planned/hold/last_confirmed를 원 solver와 정확 대사한다.
2. JSON binary roundtrip와 별도 Python process 복원; initial/t0 commit/내부 걸음/pending event,
   forcing/event/output 충돌과 중복 없는 prefix/전역 seed·clock·counter를 검사한다.
3. root/profile/code/policy/environment/clock/typed counters/grid/vector/hash/JSON/budget/닫힌 reader
   변조를 거부하고, 새 경계 추가·출력 선택에 따른 격자 변경이 없는지 확인한다.
4. 적법한 자작 합성 forcing으로 실제 RHS를 **1일과10,000걸음 모두 초과**해 실행한다.
   대규모 clock-only(.1/.3/20.1°C) packet을 정상 작물 시나리오로 사용하지 않는다.
   동일 원 grid의 별도 루프/분할/프로세스 복원·전역 수지·사건·hold와 자원/FD/tempfile 정리를 측정한다.
5. 원 코드/fixture/profile/short continuation/reader36개 hash 보존, 집중 회귀/검토,
   public receipt와 실제 CLI metadata·별도 프로세스 증거 뒤 task checkbox를 갱신한다.

최초7–10집중시간/10월5–8일 예상은 **10월5일 KST 로컬 완료**의 실제 증거로 대체한다.
다음 `crop-cycle-result-artifact`는 contract/budget1–2시간 + writer/reader2–3시간 +
대사/변조·복원/검토2–3시간의5–8집중시간, 하루4시간/CI 대기 제외10월5–7일 KST 잠정이다.
저장 custody/API/client/3D와166일 실제 부하·실제 품종/예측 날짜는 각각의 실적/자료 확보 뒤 갱신한다.
