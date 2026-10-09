# 실제 작물 RHS의 짧은 실행 중단·재시작 수용

2026-10-05 KST. [순수 provider](../backend/app/crop_cycle_continuation.py),
[모듈 계약](../contracts/crop-cycle-continuation-v1.md),
[집중 시험](../backend/tests/test_crop_cycle_continuation.py),
[별도 Python 복원 대사](artifacts/crop-cycle-continuation-reference-20261005.json),
[CLI·검토·집중 검증 영수증](artifacts/crop-cycle-continuation-implementation-reference-20261005.json).
**현재 짧은 합성 프로그램의 실제 RHS continuation을 로컬 수용**했다.
전체 작기/농장 예측이나 물리 저장·게시 관문 수용은 아니다.

## 사용자 산출물과 통과한 검증

- 불변 context가 원 입력/121성분 seed·Fraction clock·계산 경계와 새 engine/code·기존 RHS/
  profile/policy/environment를 고정한다. caller 입력의 이후 변경은 실행을 바꾸지 않는다.
- chunk는 원 RK4 완료 또는 원 경계 commit에서 양보한다. 원 격자에 경계를 추가하지 않고,
  전역 steps/event·16누적/수지와 확인된 과거를 보존한다. `step-end`의 사건/output은 아직 pending이다.
- checkpoint JSON은 UTF-8/64KiB 이하의 닫힌 형식이다. 원 root/seed/clock/위치·counters·domain/
  ledger·hash를 검사하며 checkpoint 읽기는 RHS 재적분을 하지 않는다. 인증/현재 권리는 후속 경계다.
- 새101개와 기존 startup 적분56개, **총157개/70.91초·skip0**를 통과했다.
  원6프로그램×예산1/2/7/64/10,000의 **30가지 실제 모델 분할·JSON 복원**에서
  전체 state·16누적/4수지·진단·사건·steps/planned_steps가 원 solver와 정확히 같았다.
  원 여섯 프로그램은630걸음/23출력이며 단순 scalar/grouping 시험을 이 결과로 대체하지 않았다.
- t0/forcing/event/output 충돌·전량 제거·원7초 걸음/나머지·빈 과거/확인 과거 hold와
  **RK4 중간 00:29:59.500000Z의 실패 시각**도 같다. failed trial은 정상 checkpoint로 내지 않는다.
  예산/위치/형식/seed/clock/수지·변경된 code/profile/policy/environment와 완료 재실행은 거부한다.
  외부 process 예외는 숫자 hold로 바꾸지 않는다.
- 추가 [연구 script](crop-cycle-continuation-reference.py)는 **6개 별도 Python 프로세스**를
  직렬 실행했다. `initial-ready`, t0 commit, 내부 step-end, 제거 사건 직전 step-end를
  원 program/profile에서 복원해 끝까지 계산했다. **726개 float64 `.hex()`**와 원 전체 물리
  payload, 분할 없는 새 실행의 최종 y/seed·counters/clock·output/event prefix가 정확히 같다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_continuation.py \
  tests/test_crop_plant_startup_integration.py
```

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-continuation-reference.py \
  --output /tmp/ossf-cycle-continuation-recheck.json
```

별도 프로세스 대사는 **17.607초**, parent 최대RSS24.77MiB·최대 child24.40MiB다.
이는 해당 시험 프로세스의 수치이며 WSL 전체 사용량이 아니다. 선택한 복원6개 checkpoint의
최대는2,963bytes다. tempfile directory/child는 모두 종료·정리했고 새 DB/상주 서버0개다.
기존 잠금 파일/계수/원 수학·저장/조회 API34파일의 hash를 보존했다.

## CLI·검토와 수용 범위

현재 실제 CLI turn_context **2026-10-05T05:44:31.122Z**, **gpt-6.1-sol / xhigh**에서
설계·구현·검토했다. context line hash와 실제 출력 source/log hash를 영수증에 기록했다.
Codex CLI 재귀 실행0회이며 별도 Python은 수치 복원 시험이다. 제품 런타임 CLI 수용은 별도다.

검토에서 UTF-16 JSON 수용과 context root 누락의 실패 시험을 재현해 수정했다.
원 격자/전역 operation budget, 사건 적용 전후의 phase, 초기 hold의 빈 과거,
원 clock의 정확한 prefix/slope와 seed·누적 보존을 확인했다. 동결된 legacy 함수/파일을
재구성하지 않고 point calculator·guard/ledger/update를 재사용한 새 실행 제어다.
중복된 snapshot/RHS 제어 표현은 원 immutable source hash를 유지하기 위한 이 별도 판본의 범위다.

SHA/수지 일치는 checkpoint의 진본·parent ancestry·현재 farm/program/source 권리를 증명하지
않는다. durable atomic delta commit/HMAC·worker lease/취소·HTTP/3D는 실행하지 않았다.
현재 v1은128 forcing/128 event·512 output·10,000 step·1일을 유지한다. 긴 입력을 이
context에 넣거나 기존 API/manifest의 한도를 올리는 방식으로 전체 작기를 주장하지 않는다.
첫 별도 복원 영수증의 contract hash는 `c422e4b`의 당시 구현 중 계약이다. 현재 수용 문구의
hash와 Git 초안 대사는 별도 implementation 영수증에 보존하며 첫 증거는 덮어쓰지 않는다.

새 API/client/3D와 실행 계약을 포함한 hosted SHA `1555610`은4workflow가 성공했고
Backend는 확인 중이다. 이번 continuation 코드는 그 SHA에 없으며 로컬3커밋으로 검증했다.
기존92cade3의5workflow/3,408개·별도UID4개 수용과 구분한다. live CI를 후속 push로 취소하지 않는다.

## 다음 단계와 외부 의존성

다음은 **`crop-cycle-input-stream`**의 bounded immutable root/forcing·anchor/event reader다.
source/hash/index·원 UTC/단위/연속성·exact clock·cursor를 닫힌 계약으로 고정하고 원47,809시점
형태 이상의 자작 합성 입력을 분할해 읽는다. 최대 window/메모리·별도 재시작·gap/overlap/
변조/권리·QC 미충족 거부가 수용 기준이다. 실제 archive나 품종 채택을 만들지 않는다.
root/provider2–3시간, 독립 격자/clock·큰 형태/복원/실패 검증·보고2–3시간으로 **4–6 집중시간**,
하루4시간/CI 대기 제외 기준 **10월5–7일 KST 잠정**이다. 실제 실적 뒤 갱신한다.

이어 **`crop-cycle-stream-execution`**에서 그 reader를 실제 RHS/전역 continuation에 연결하는
별도 판본을 검증한 뒤, 불변 결과 저장/조회·같은 UTC 3D → 실제 RHS 작기 부하 → 생과 환산을
진행한다. 입력 reader의 수용을 긴 실제 모델 실행으로 표시하지 않는다. 긴 실행/저장 일정은
provider 실적·구체적인 전역 budget 분해 뒤 추정한다.
실제 품종/UTC·QC/forcing/초기·관리 채택0개, 국내 독립 자료0건·actual crop Run0개다.
자료 확보와 개발은 병행하고 실제 생과·구매 자원·경제·예측/추천 및 G0–G4는 보류한다.
외부 자료 확보 날짜가 없는 실제 생산 예측·추천의 완료 날짜는 아직 산정하지 않는다.
