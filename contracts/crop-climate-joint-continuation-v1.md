# 작물·기후의 분할 실행과 체크포인트 v1

선행은 [자동 구간/사건 실행](crop-climate-joint-boundary-driver-v1.md)의 로컬 수용이다.
핵심3은 `backend/app/crop_climate_joint_continuation.py`, 해당 tests, 이 계약이다.
농업 식/계수나 수치 정책을 추가하지 않으며 기존 kernel·원 결과/121상태를 보존한다.

## 고정 context와 공개 함수

`prepare_context(scenario=...,events=...,output_steps=...,step_seconds=...,step_count=...,four_profiles)`는
기존 닫힌 scenario/격자·사건 입력을 정규화하고 초기 공동 RHS를 한 번 평가한다.
불변 canonical bytes의 program/초기 RHS, exact4프로필과 manifest를 process 내부 context로 고정한다.
manifest는 program/seed·초기 RHS 계산 hash, 모델/의존 코드/프로필/정책, 수치/clock/상태 판본과
Python/platform/float 환경을 결속한다. 최대 combined context bytes2MiB다.
원4,096걸음/600초·128사건/512출력 상한과 명시 상수 forcing/RGR를 유지한다.

- `start(context)`는 경계0 사건/출력 전 `initial-ready` checkpoint를 만든다.
- `advance_chunk(context,checkpoint,boundary_budget)`는 정수1–128개의 원 경계를 처리한다.
- `checkpoint_bytes(context,checkpoint)`는 불변 checkpoint의 canonical UTF-8 bytes를 반환한다.
- `restore_checkpoint(context,raw_bytes,expected_sha256=...)`는 **외부에서 신뢰한 raw bytes SHA**를 필수로 받는다.

context/checkpoint는 이 모듈이 만든 내부 frozen 객체다. 공개 property는 복사된 JSON만 반환한다.
Python 내부 필드/함수를 공격자가 재작성하는 환경의 인증 경계가 아니다.
외부 checkpoint는64KiB 이하의 닫힌 canonical JSON·중복 key/비유한 상수 거부·exact bytes hash를 검사한다.
내용을 다시 해시한 것만으로 진본을 증명하지 않는다. expected digest는 이후 서버의 권한 있는 불변 저장/서명 경로가 제공해야 한다.
이 순수 모듈은 서명/권한·영속 게시를 제공하지 않는다.

## 경계·장부·checkpoint

원 경계는0..step_count다. 경계0도 예산1개를 사용하며 dt/RK4 격자에 새 시간점을 넣지 않는다.
순서는 기존 한 걸음 RK4→seed 대비 전역7수지→같은 경계 관리→전역7수지→journal→사건 후 선택 출력이다.
연속22장부·사건6합계는 각 원 걸음/사건마다 같은 순서로 누적한다.
chunk 단위로 합쳐 다시 더하지 않는다. 초기/마지막 사건도 정확히 한 번 처리한다.
기존 `_add`/`_balances`/`_snapshot`과 짧은 적분/관리 kernel을 재사용하며 식/RK4를 복사하지 않는다.

checkpoint에는 version/context hash, `next_index`, output/event cursor·각 prefix SHA,
마지막 확정 snapshot(108상태/유도량·연속22/사건6·전역7잔차/예산·phase)을 고정한다.
cursor는 완료 경계의 선택/사건 수와 같고 elapsed는 원 index*dt다. initial-ready는 원 seed/0장부/빈 prefix 그대로다.
경계0 사건 전과 경계0 완료를 next_index0/1로 구분한다.
prefix SHA는 **각 출력/사건별** canonical chain이며 chunk grouping을 포함하지 않는다.
동일 프로그램의 임의 분할에서 최종 checkpoint bytes·상태/장부/순서/prefix가 정확히 같아야 한다.
chunk 수/실행 시각을 checkpoint identity에 넣지 않는다.

복원은 코드/환경/프로필·현재 상태의 공동 RHS·전역 수지·cursor/shape/단위를 검사한다.
과거 구간을 재적분하지 않는다. 저장 상태의 온도 이력은 trusted expected digest에 묶인 producer 값이지 역산한 값이 아니다.
각 advance의 checkpoint 검사는 현재 endpoint RHS1회이고, 이후 완료 걸음5회/관리2회다.
실패 trial의 실제 RHS 횟수는 확인된 호출 수와 구분한다.

반환은 `yielded|completed|hold`, scope/manifest/context hash, steps/planned steps,
output_start/event_start, 이번 samples/events, last_confirmed와 checkpoint다.
checkpoint는 **전체 해당 경계의 사건/출력까지 완료**한 위치에만 발급한다.
실패는 checkpoint=None과 실제 global step/phase/reason·완료된 이번 prefix/마지막 확정 상태를 반환한다.
관리 실패라면 같은 시각 step-end는 last_confirmed일 수 있으나 실패 사건/선택 출력을 commit하지 않는다.
입력/context/checkpoint/budget 오류는 typed `ContinuationRejected`이며 실행을 시작하지 않는다.
완료 checkpoint의 재실행도 거부한다. 취소/crash/외부 예외를 정상 yield로 바꾸지 않는다.

## 수용

1. 기존9프로그램×여러 경계 예산에서 원 자동 실행과 모든108상태/22장부/6합계·7잔차/예산,
   selected samples/10journal·처리 순서·마지막 상태가 정확히 같아야 한다.
   최종 checkpoint bytes/prefix도 임의 분할에 무관하다.
2. initial-ready/t0 완료·중간 사건 전후/마지막의 canonical roundtrip와 별도 Python 복원,
   현재 endpoint 이외 과거 RHS/관리 재실행0과 입력/원량 불변을 확인한다.
3. context/code/profile/environment·trusted digest/JSON/shape/cursor/unit/vector·budget/상한,
   실제 domain/수치·step/event global 수지 실패의 마지막 상태/prefix를 검증한다.
4. 원512출력/128사건 구성의 chunk 상한/체크포인트 크기·실제 비용, 기존648개 회귀와
   독립 참조값/코드 보존·원 종료/FD/정확한 소유 정리·단일512MiB/소유+보호1GiB를 확인한다.

범위는 `software_research_only`, `synthetic_joint_crop_climate_continuation_only`, G0_G4=`not_assessed`다.
UTC/forcing 경계·불변 저장/현재 권리 API/같은 시각3D·실시간 U3, 전체 작기/온실/품종·농장 검증은 후속이다.
