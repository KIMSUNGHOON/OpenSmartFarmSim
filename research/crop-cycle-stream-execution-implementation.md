# 분할 입력을 실제 생장 계산에 연결한 결과

2026-10-05 KST. [순수 실행 모듈](../backend/app/crop_cycle_stream_execution.py),
[계약](../contracts/crop-cycle-stream-execution-v1.md),
[집중 시험](../backend/tests/test_crop_cycle_stream_execution.py),
[실제 RHS/별도 Python 대사](artifacts/crop-cycle-stream-execution-reference-20261005.json),
[CLI·수용 파일/초안·검토 영수증](artifacts/crop-cycle-stream-execution-implementation-reference-20261005.json).
**불변 입력 reader와 실제 고정 RHS의 긴 연구 실행을 로컬 수용**했다.

## 사용자가 확인할 수 있는 산출물

새 driver가 원 입력의 forcing 끝/anchor/event 합집합과 RK4걸음을 읽어121상태·16누적·
원 seed/Fraction clock·전역 counter/수지·사건과 hold를 이어 계산한다.
128경계마다 bounded 원 cursor/누적 걸음 index를 두고 상세 경계는 한128페이지,
RHS adapter는 현재 한 forcing만 보관한다. checkpoint JSON은≤64KiB이며 같은 원 root와
격자 위치/phase를 검증하고 복원한다. chunk 끝을 새 계산/화면 시각으로 넣지 않는다.
원 short solver/continuation/reader·profile·fixture·기존 API의38개 hash를 보존했다.

보고서/영수증은 계산과 재시작이 실제 수행됐음을 확인하는 산출물이다. 이번 긴 결과는
웹에 저장/재생되지 않았다. 그 연결은 아래 후속 작업이며 기존 짧은 startup 성장 연구
3D의 수용 범위는 유지한다. 임의 animation/실제 품종 생산 결과로 표시하지 않는다.

## 통과한 검증

- 새88개+기존 startup56개의 **144개/65.41초·skip0**. 기존6프로그램×3예산 조합의
  실제 RHS·JSON 복원에서 원 상태/16누적·수지/진단/사건/걸음이 동일하다.
  forcing/event/output 충돌과 pending 경계의 사건을 한 번만 적용한다.
- 원7초 걸음/나머지 구간의 실제 k1–k4 시각, 출력 선택 변경의 동일 계산 grid/최종 상태,
  261경계/3index페이지의 전역 걸음·seed, unread block 변경의 hash 거부를 통과했다.
- 원7종 hold(유입/생식기 이전/N없는C/underflow/t0 제거/후속 제거/fractional RK4)와
  hold/last_confirmed/과거가 동일하다. root/code/profile/policy/environment·typed counters,
  grid/seed/clock/vector·ledger·closed JSON/UTF-8/중복 key/NaN/budget/닫힌 reader를 거부한다.
  취소/외부 예외는 수치 hold로 바꾸지 않는다.
- 실제 **별도 Python7개/847 float64** 복원. 짧은6개는 초기/t0 commit/내부 걸음/pending 사건에서
  복원 후 원 solver의 **canonical 전체 물리 payload**와 일치했다.
- 자작 긴 합성 프로그램은 **300 forcing 구간·90,000초(25시간)·303경계·11,400 실제 RK4걸음**,
  27 sample/5 event다. 원 합성 fixture의20°C/PAR400/CO₂800과 명시 관리 사건을 사용한 소프트웨어
  시험이며 실제 온실/품종 forcing이 아니다. clock-only 대규모 packet(.1/.3/20.1°C)을 사용하지 않았다.
- 원 함수의 정규화/고정 rates를 사용하되 새 driver/cursor/index를 사용하지 않는 독립 전체 제어
  루프와 **canonical sample/event/진단·누적량 및 최종 y/seed `.hex()`·전역 수지/두 prefix hash**가 같다.
  4,864걸음/forcing index127의10:40:00Z `step-end`에서 별도 Python으로 복원해
  forcing 변경/전량 과실 제거/출력 경계를 처리했다. parent5+child68 chunk에서 사건 중복이 없었다.
- 별도25시간/60초 원 걸음의 **1,502걸음** 프로그램은 마지막 제거가 저장량을 넘어서
  `2026-01-02T01:00:00Z`/event hold다. 과거26 sample/4 event·동일 시각 `step-end`
  last_confirmed만 남고 checkpoint=None이며 독립 참조의 canonical 전체 payload와 같다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_stream_execution.py \
  tests/test_crop_plant_startup_integration.py
```

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-stream-execution-reference.py \
  --output /tmp/ossf-cycle-stream-recheck.json
```

별도 process 증거 전체 **263.879초**, parent 최대RSS **45.44MiB**, 긴 child **39.36MiB**다.
독립11,400걸음109.322초, driver parent+child111.658초다. 긴 packet722,057bytes,
index3페이지/child 마지막 경계 window47개·입력 cache103개, 관측한 긴 checkpoint 최대4,039bytes다.
첫 영수증의 `max_short_selected_checkpoint_bytes` 필드는 선택된 긴 resume도 포함한 값3,988bytes다.
이를 짧은 전용 최대치나 전체 checkpoint 최대치로 해석하지 않는다; 전체 관측 긴 최대는4,039bytes다.
프로세스 측정이며 WSL 전체 메모리가 아니다. tempfile/response/child/FD를 정리했고 DB/서버0개다.

## 발견·수정과 검토

첫 긴 대사는 물리 값이 같지만 `event_prefix_sha256`가 달라 실패했다. 독립 참조가 원 입력의
정수→float64 정규화 순서를 누락해 사건 JSON의10과10.0이 다른 hash를 만들었다.
고정 legacy 정규화를 독립 루프 앞에 적용하고 canonical payload/prefix/최종 `.hex()` 검사를
추가했다. 해당 회귀1개/3.38초와 전체144개, 다시 실행한 긴/별도 process 대사가 통과했다.
실패 log hash/원인도 영수증에 보존하며 실패 실행을 수용 증거로 계산하지 않는다.

현재 CLI turn_context **2026-10-05T06:58:16.864Z**, **gpt-6.1-sol / xhigh**에서
설계/구현/검토했다. actual line SHA·입력/source/output log hashes를 보존했다.
재귀 Codex CLI0회다. Python 복원 시험은 제품 runtime CLI 호출 증거가 아니다.

검토는 원 closure/격자·정규화·clock/seed/global ledger·phase와 확인 과거, closed identity/counter,
resource/input hash·단일 window·예외/FD·owned cleanup을 확인했다. context는 신뢰된 process
내부 객체이며 SHA/수지는 진본·현재 권리/HMAC·승인/재시작 ancestry를 증명하지 않는다.
새 dependency/일반 운영 service·agent Framework 없이 별도 모듈을 추가했다.
새 연구 입력의366일/40,000,000step 상한은 그 부하/농업 정확도 수용이 아니다.

첫 실행 증거의 contract hash는 `cb034ce`에 보존된 구현 중 계약이다. 최종 수용 문구/파일 hash와
Git 초안 대사는 별도 implementation 영수증에 기록하며 첫 실행 증거를 덮어쓰지 않는다.
Hosted SHA1555610의 [5workflow/백엔드3,456개·UID4개](artifacts/crop-startup-replay-ci-20261005.json),
6개 동일 inventory·DB/password 정리·집계를 실제 terminal 로그로 수용했다.
이번 continuation/reader/stream 실행은 그 SHA에 없으며 그 terminal 증거 뒤 한 번에 push한다.

## 다음 한 단계와 외부 의존성

다음 **`crop-cycle-result-artifact`**는3파일(module/test/contract)로 원 결과·checkpoint의
bounded 불변 chunk/index와 재적분 없는 reader를 구현한다. 수용 기준은6원 프로그램과
1일/10,000걸음 초과 자작 합성 결과의 저장/별도 Python 읽기·같은 UTC/원값,
≤2MiB 페이지/유한 전체 byte·record budget, 원 counter/chain·순서/중복/혼합 root/변조,
pending event·partial commit/실패·atomic 게시/재시작·tempfile/FD 정리다.
현재 farm/source 권리·HMAC/DB/HTTP는 그다음 custody 단계다.

contract/budget1–2시간 + writer/reader2–3시간 + 대사/변조·복원/검토2–3시간의
**5–8집중시간**, 하루4시간/CI 대기 제외 **10월5–7일 KST 잠정**이다.
기존 실행7–10시간/10월5–8일 예상은10월5일 로컬 수용으로 대체했다.
[todo](../tasks/todo.md)의 artifact → schema → 권리 custody → API → client → 같은 UTC3D로
저장/조회 부모를 분해했다. 저장/3D 날짜는 artifact의 실제 크기/검증 실적 뒤 갱신한다.

source 형태166일/1,440,002걸음의 실제 RHS 부하, durable cycle 결과/조회/3D,
실제 초기/자동 착과·pre-onset/RGR·품종/생과kg/자원·경제와 G0–G4는 미수용이다.
실제 forcing/초기·관리·품종 채택0개·국내 독립 자료0건·actual crop Run0개다.
독립 농장 자료 확보를 개발과 병행하며 미래 생산 예측·추천 날짜는 확보 전에 산정하지 않는다.
