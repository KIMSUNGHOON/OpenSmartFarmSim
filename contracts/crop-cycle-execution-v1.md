# 전체 작기 연구 실행·연속 상태 계약 — v1

상태: **명세 초안, 독립 경계 대사 전**, 2026-10-05 KST.
작업 ID `crop-cycle-execution-contract`. 근거는 [현재 코드 감사](../research/crop-cycle-execution-inspection-20261005.md),
[관문/품종 범위](../docs/PROJECT_SPEC.md), [불변 저장·worker 계약](../docs/ARCHITECTURE.md)이다.
현재 CLI `gpt-6.1-sol / xhigh`에서 판단하고 CLI를 재귀 실행하지 않는다.
기존 짧은 모델/원 입력·결과·관문 증거를 수정하지 않는다.

## 목적·개발 범위

사용자는 한 작기의 계산 결과를 같은 UTC의 3D·표에서 확인해야 한다. 현재 startup은
1일·128 forcing/128 event·512 output·10,000 step으로 한정된다. 원 공개 참조의47,809시점/
후보166일을 처리할 연구 실행은 **원 forcing·관리·계산 해상도와 연속 상태**를 보존해야 한다.
본 단계의 산출물은 아래 실행 의미·provider 경계·독립 대사와 작은 후속 작업이다.
계약 수용은 새 driver·전체 작기·생과·자원/경제·G0–G4 수용이 아니다.
자동 착과/pre-onset·RGR·초기 품종/생과 환산 근거도 이 실행 계약으로 해결하지 않는다.
국내 자료/G2는 순수 개발의 선행이 아니며 실제 입력 채택·게시에는 기존 관문이 필요하다.

| 모듈/작업 | 책임 | 선행 |
| --- | --- | --- |
| crop-cycle-execution-contract | 실행 의미·현재 코드/독립 경계 대사·후속 수용 기준 | startup 적분, 원천 형태 감사 |
| crop-cycle-continuation | 짧은 입력으로 실제 RHS의 중단/재시작·전역 상태/clock/사건 보존 | 이 계약 |
| crop-cycle-input-stream | 고정 원 입력의 bounded 분할 읽기·cursor·원천/전체 hash·연속 forcing/clock | continuation |
| crop-cycle-result-pages | 새 cycle artifact의 불변 chunk/index·현재 권리·재적분 없는 조회/같은 UTC 3D | 입력 stream/continuation |
| crop-cycle-burden | 실제 RHS로 긴 합성 프로그램의 부하/재현·source 형태 규모·별도 프로세스 재시작 | 위 세 구현 |

구현 순서: continuation → input-stream → result-pages → burden. 실제 참조 작기 실행은
그 소프트웨어 수용과 별개로 원 UTC/QC·초기/관리·해당 품종 입력 채택 뒤다.
새 queue/상주 service·Framework는 이 순수 실행의 선행이 아니다.

## 원 계산 격자와 출력 선택

1. 시작/end, forcing 끝, 관리 사건, **고정 계산 anchor**의 순서 있는 합집합을 원 계산 경계로
   고정한다. 짧은 기존 입력의 변환에서는 원 output_times가 모두 계산 anchor에 들어간다.
2. 인접 원 경계 a→b 사이의 걸음은 a에서 시작해 max_step_seconds 길이로 진행하고,
   마지막 걸음만 b까지의 나머지 정수 초다. 모든 RK4 trial/종료 검사는 원 순서와 같다.
   원 경계 직후에는 다시 그 경계를 기준으로 다음 걸음을 만든다.
3. chunk 예산은 이 원 순서의 이미 검증된 걸음/경계 뒤에서 실행을 양보한다. chunk 끝을
   새 forcing/output/계산 anchor로 넣지 않는다. 메모리·wall-time 예산이 계산 격자를 바꾸지 않는다.
4. 저장/display 선택은 고정 계산 anchor의 부분집합이다. 선택을 바꾸어 계산 경계를 지우거나
   새 시각을 넣지 않는다. 다른 계산 해상도/anchor가 필요하면 새 프로그램/manifest다.
   forcing 해상도는 그대로다. 중간 상태를 보간해 정상 output으로 추가하지 않는다.
5. `steps`는 전역 RK4 완료 수, `event_count`는 전역 commit 사건 수다. roundoff budget의
   operations=steps+event_count를 chunk별로 초기화하지 않는다. 예정 걸음 수/전체 예산도 전역이다.

긴 root 입력은 해당 원 구간·anchor와 hash/index를 담는 새 판본이다. 기존 bounded
v1/v2/v3 입력·artifact/API decoder에 긴 cycle을 넣거나 기존 한도를 올리지 않는다.
최대 전체 step/입력/출력 bytes·worker wall-time의 production 값은 실제 부하 뒤 고정한다.
caller가 무한 입력/예산을 지정할 수 없도록 각 구현 계약에서 명시적 유한 resource budget을 받는다.

## continuation provider의 상태·위치

순수 provider는 같은 고정 context에 대해 `start(context)`와
`advance_chunk(context, checkpoint, budget)`를 제공한다. 반환은 다음 세 가지다.

- `yielded`: 유효 checkpoint와 이번 chunk의 확인된 output/event delta.
- `completed`: 같은 전역 결과와 마지막 checkpoint/delta.
- `hold`: 기존 numeric/domain/balance/resource 이유와 확인된 과거·마지막 확인 진단.

형식/판본/해시/예산 불일치는 시작 전에 typed rejection이다. 계산 중 hold는 완료나
재시도 가능한 yielded로 바꾸지 않는다. 보정된 forcing/계수/관리 입력은 새 판본이다.
확인된 과거 뒤의 실패 trial을 정상 checkpoint나 output으로 쓰지 않는다.

| checkpoint 항목 | 의미·검사 |
| --- | --- |
| schema/engine/model/profile/policy/code/원 프로그램·농장/입력 참조 hashes | 고정 context와 일치; 단순 SHA는 권한/승인/진본 증거가 아님 |
| `y` | 기관·온도5, N50, C50, FLUX16 순서의121성분; finite/단위·기관/구획 영역·수지 검사 |
| `seed` | 원 프로그램 초기121성분; 누적 초기0; chunk 초기 상태로 교체하지 않음 |
| `at`, steps, event_count, active segment, next boundary/event/output cursor | 전역 위치; 계획된 도착 시각/누락·중복/범위·진행량 검사 |
| `phase` | `initial-ready`, `step-end`, `boundary-committed`의 명시 상태; RK4 중간 trial 없음 |
| 정확한 온도 clock | 원 initial temperature_sum, active forcing의 정확한 Fraction prefix/slope 또는 이를 동일하게 재생하는 원 context/cursor; 반올림된 현재 온도 합으로 prefix를 새로 만들지 않음 |
| 출력/사건 sequence와 parent checkpoint/hash | commit된 prefix; 재시작 시 중복/순서·다른 root/chunk 혼합 거부 |

입력 `_quantity`가 정규화한 수치는 Python float64다. checkpoint canonical JSON의 round-trip
후 `.hex()`를 포함한 binary 동일성을 확인한다. units/순서/원 identity와 solver/환경을 고정한다.
이 보존은 money 계산 형식을 바꾸지 않으며 경제에는 기존 Decimal 계약을 유지한다.
정확한 Fraction을 저장할 구현은 reduced numerator/positive denominator의 bounded 문자열과
해당 root의 원 clock 정의를 대사한다. source/hash/cursor로 재생하는 구현도 동일성 시험이 필요하다.

### 걸음 끝과 경계 commit

원 단계 순서는 다음과 같다.

1. 원 h의 RK4 k1–k4 → update → 정확한 clock → step-end RHS/영역·수지 확인.
2. 완료 steps 증가·step-end last_confirmed. 여기서 양보하면 같은 원 boundary가 아직 pending일 수 있다.
3. 경계 도착 시 active forcing 변경 → 제거 후보 → boundary RHS/영역·모든 수지 확인.
4. 성공한 사건 journal/event_count 증가 → y/last_confirmed 확정 → 선택된 원 output 기록.
5. `boundary-committed`와 다음 cursor로 진행.

`step-end`로 경계에 도착한 checkpoint는 재시작 시3–4를 정확히 한 번 처리한다.
`boundary-committed`는 이미 적용한 사건/output을 다시 처리하지 않는다. 초기 t0의 사건도
같은 규칙을 적용한다. 경계 검증/사건·output delta와 checkpoint의 durable commit은 후속
저장 provider가 원자적으로 수행한다. 요청 취소나 crash를 수치 hold로 위장하지 않는다.

## stream·저장·권리 경계

순수 driver는 내부 검증된 segment/anchor/event provider와 checkpoint 객체만 받는다.
file path·테넌트·Bearer/DSN·farm raw를 수치 kernel에 넣지 않는다. 초기 짧은 adapter는 기존
공개 합성 입력으로 검증한다. 긴 provider는 원 입력을 hash/index로 분할하고 bounded window를
읽으며, gap/overlap/같은 시각 사건 중복·UTC/단위·RGR/초기/QC·권리를 시작 전에 검사한다.
원 block/input ID와 시작 seed/clock·원 계산 ID를 유지한다. 축약/평균/보정은 새 입력 판본이다.

cycle artifact는 별도 schema/version/root manifest다. 원 입력/프로필·계산 격자/환경·결정 ID,
checkpoint chain·output/event index·수지/hold/확인 과거와 내용 hash를 보존한다. 각 chunk와
목록은 불변이며 수정은 새 root다. HMAC/현재 권리·farm/source/program binding과 원자성은
후속 실제 custody 검증의 대상이다. 브라우저가 checkpoint를 생성하거나 임의 숫자를 업로드하지 않는다.
조회는 current rights 검사를 통과한 저장 결과만 페이지로 읽고 GET에서 적분하지 않는다.
기존 API의30초/2MiB와 원값/같은 UTC 표·3D 안전 규칙을 새 페이지에서도 유지한다.
전체 실행 기한과 한 페이지의30초를 혼동하지 않는다.

worker는 기존 lease/취소/heartbeat와 권한 제공자를 재사용한다. 실제 조립은 pure driver의
부하/실패 증거 뒤 별도 작업으로 수용한다. 실행/각 durable commit 전후의 현재 권리·입력 연결이
유효하지 않으면 게시를 보류한다. 과거 정상 checkpoint가 현재 권리/관문 승인을 대신하지 않는다.

## 구현·검증 산출물과 명령

현재 스택의 Python3.12.13/stdlib·기존 고정 rates/profile과 pytest를 사용한다.
새 의존성이나 설치는 없다. 각 구현은3–5개 파일 이하의 작은 작업으로 수행한다.

| 작업 | 예상 파일·수용 증거 |
| --- | --- |
| 계약/독립 대사 | 이 파일, research reference/script·receipt, tasks plan/todo. 실제 짧은 solver의 원 걸음/사건 순서, 추가 경계 반례·vector/clock 보존 위험을 대사 |
| continuation | backend/app/crop_cycle_continuation.py, tests/test_crop_cycle_continuation.py, 모듈 계약. 실제 기존6프로그램과 분할/별도 Python 복원·동일 상태/16누적/수지/사건·boundary 전후/t0/event+output/hold·변조/예산·정리 |
| input-stream | 입력 provider/시험·계약. 실제 source 형태47,809/47,808을 넘는 자작 합성 입력, bounded read/hash/clock/연속성·큰 입력/gap·권리/QC 거부; 실제 archive 채택 주장 없음 |
| result-pages | 먼저 불변 파일/reader, 이어 custody/API와 같은 UTC 3D를 각3–5파일 작업으로 분해. 같은 원 출력/sequence·현재 권리/혼합/원자성/재시작/GET 재계산 금지·페이지 전체 본문·실제 SCRAM/TLS/browser·정리 |
| burden | source 형태 규모의 실제 RHS 실행·부하/메모리·중단/재개/순서·저장/조회와 원 수지. synthetic only이며 실제 전체 crop/생과 검증이 아님 |

먼저 실행하는 독립 대사 명령:

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-execution-reference.py \
  --output research/artifacts/crop-cycle-execution-reference-20261005.json
```

future continuation 구현의 집중 명령(해당 파일 생성 뒤):

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_continuation.py \
  tests/test_crop_plant_startup_integration.py
```

형식은 기존 module의 닫힌 입력·typed hold와 원 단위/고정 상수를 따른다. 가령
`advance_chunk(context, checkpoint, budget)`는 입력을 변경하지 않고 `status/next_checkpoint/outputs/events`
하나를 반환한다. pseudo 결과나 품종값을 채운 stub를 제품에 넣지 않는다.

## 이 계약 단계의 수용과 남은 의존성

- 실제 소스의 두 판본 한도/원 격자·121벡터·seed/clock·사건 위치와 독립 경계 대사 기록이 존재한다.
- 추가 output/chunk 경계의 위험과 serialization/온도 clock 위험을 재현하며, 그 시험 범위가
  실제 새 model continuation/G0–G4가 아님을 명시한다. 후속 실제 복원·current rights/저장·부하 검증표를 고정한다.
- 코드/계수·단위/기존 manifest를 보존하고, 후속 작업의 dependency/파일·사용자 산출물·수용 기준과
  외부 자료0건/UTC·초기/관리·품종 보류, 실제 부하 전 미정 budget/완료 날짜를 plan/todo에 기록한다.

현재의 계약/대사는2–4 집중시간 잠정, continuation은 실제 코드/시험 분해 뒤 다시 추정한다.
actual forcing/독립 국내 자료·crop Run은0이다. 실제 생과·구매 자원·경제/예측/추천 게시는
해당 출력의 독립 검증/G0–G4와 별도다. 소프트웨어 규모 시험을 실제 생산 정확도로 표시하지 않는다.
