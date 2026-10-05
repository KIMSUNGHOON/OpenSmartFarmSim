# 순수 작물 실행 중단·재시작 — v1

상태: 구현/검증 중, 2026-10-05 KST. 상위는 [작기 실행 계약](crop-cycle-execution-v1.md)이다.
현재 CLI `gpt-6.1-sol / xhigh`에서 설계한다. 새 운영 service/의존성/농장 자료는 없다.
현재 startup의 닫힌 짧은 입력과 정확한 세 profile만 받는다. 한도는 그대로128 forcing,
128 event,512 output,10,000 RK4 step,1일이다. 긴 입력·전체 작기·G0–G4 수용은 별도다.

## 경계와 형식

`prepare_context(**startup_program_and_profiles)`는 기존 정규화를 재사용하고, 불변 JSON bytes의
program/manifest·원 boundary/seed/Fraction clocks를 고정한 내부 `CycleContext`를 만든다.
caller 입력의 이후 변경은 실행을 바꾸지 않는다. 입력/정확한 profile 실패는 `CycleContinuationRejected`다.
manifest는 새 engine/source hash, 기존 RHS/helpers의 원 hash, profile/policy·solver/환경·root를 고정한다.

`start(context)`는 `initial-ready` checkpoint를 반환한다. 아직 정상 sample/last_confirmed가 없다.
`advance_chunk(context, checkpoint, budget)`의 닫힌 budget은
`max_steps`, `max_transitions`의 두 정수(각1–10,000, bool 제외)다. 둘 중 먼저 소진된 뒤
양보한다. transition은 원 RK4 완료 또는 원 경계 commit 한 번이다. 새 시간 경계를 만들지 않는다.
최종 원 경계 commit은 `completed`; 이미 완료한 checkpoint의 재실행은 typed rejection이다.
반환은 `status`, `scope`, `manifest`, `checkpoint`, 전역 `steps/planned_steps`,
`output_start/event_start`, 이번 `samples/events`이다. hold에는 기존 `hold/last_confirmed`를
추가하고 checkpoint는 null이다. 취소/예외를 숫자 hold로 바꾸지 않는다.

checkpoint의 닫힌 JSON에는 판본/root/calculated state ID,121성분의 finite float64 `y/seed`,
UTC `at`, 전역 steps/event_count, `active_segment`, `boundary_cursor`, `output_cursor/event_cursor`,
`phase`, 전역 transition `sequence`, `parent_sha256`, output/event prefix hash,
원 segment clock의 시작·reduced Fraction prefix/slope와 `checkpoint_sha256`를 넣는다.
phase는 `initial-ready|step-end|boundary-committed`다. 원 grid의 위치에서만 복원 가능하다.
경계 끝 step-end는 event/output 이전이며 다음 호출이 경계를 한 번 commit한다.
초기 t0 사건·forcing 변경·경계 수지/확인 과거는 원 solver와 같은 순서다.

`checkpoint_bytes(context, checkpoint)`와 `restore_checkpoint(context, raw_bytes)`는 닫힌 형식,
원 context/hash·seed/clock·counters/cursors/grid·domain/ledger를 검사한다. UTF-8 JSON≤64KiB,
중복 key/NaN/잘못된 JSON은 거부한다. float64 binary round-trip을 보존한다. prefix Fraction은
원 context와 같아야 하므로 임의 큰 정수/새 반올림 clock을 받아 계산하지 않는다.
검증은 RHS 재적분으로 과거 전체를 재실행하지 않는다. SHA/유효 수지는 인증·진본·권리 증명이 아니다.
현재 권리/HMAC·prefix 원자 게시/물리 저장과 worker lease/cancel은 후속 custody 계약에서 수용한다.
브라우저/HTTP가 checkpoint를 만들거나 이 provider를 직접 실행하지 않는다.

## 수용 기준과 명령

- 기존 실제 RHS6프로그램: 각 chunk 예산1/2/7/64/10,000과 중간 JSON 복원에서도 원 sample의
  전체 state/16누적·4수지/진단·사건·전역 steps/hold/last_confirmed가 정확히 같다.
- 원 RK4 step/h 순서, t0·forcing/event/output 충돌과 경계 전후의 phase·prefix 순서/중복 없음.
- 빈 과거 hold/기존 과거 hold와 fractional RK4 실패 시각이 같다. failed trial을 checkpoint로 내지 않는다.
- 형식/예산·root/code/profile/policy/seed/clock·phase/position/counters·범위/finite/domain/수지 변조를 거부한다.
  단순 재해시가 원 위치/clock/seed 검사나 수지를 우회하지 않는다. parent ancestry/authenticity는 후속 범위다.
- 실제 별도 Python 프로세스에서 normalized program/profile로 context를 다시 만들고 JSON checkpoint를
  복원해 실행한다. t0/중간/경계 commit에서 끝까지 기존 solver의 물리 payload를 대사한다.
- 원 source/profile/fixture hash와 caller 입력을 보존한다. 새 no-server 순수 검증의 시간/RSS·정리를 기록한다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_continuation.py \
  tests/test_crop_plant_startup_integration.py
```

사용자 산출물은 이 계약, 순수 provider/집중 시험, 실제 복원·수치 대사 보고서다.
현재 소프트웨어 검증을 실제 품종/forcing 채택·독립 농장 검증/생과 예측으로 표시하지 않는다.
