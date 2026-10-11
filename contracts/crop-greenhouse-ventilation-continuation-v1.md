# 환기 공동 계산의 분할 실행·체크포인트 v1

선행은 [관리 사건·선택 출력 program](crop-greenhouse-ventilation-program-v1.md)의 로컬 수용이다.
핵심3은 `backend/app/crop_greenhouse_ventilation_continuation.py`, 해당 tests, 이 계약이다.
기존22장부 [continuation](crop-climate-joint-continuation-v1.md)의 canonical/hash와 환경 identity helper만 재사용한다.
새 frozen Context/Checkpoint·모델/체크포인트 판본이며 기존 타입과 상호 대체하지 않는다.
농업 식/계수·RK4/사건 계산은 변경하지 않는다.

## 입력·identity·공개 함수

`prepare_context(scenario=...,ventilation=...,events=...,output_steps=...,step_seconds=...,step_count=...,four_profiles)`는
원 닫힌 program 입력을 정규화한다. 다른 고정 forcing의 source scenario와 실외 입력을 별도로 보관한다.
입력 검증 RHS1회와 현재 환기/공동 RHS1회로 초기 값·진단을 고정한다.
program/초기 RHS·환기 결과/manifest는 canonical immutable bytes이며 합2MiB 이하이다.
manifest는 코드/의존 코드·정책/4프로필/source·notice SHA, Python/platform/float 환경,
원 program/seed hash,108상태·25장부 판본·elapsed clock과 수치 정책을 결속한다.
단계별 환기를 원 다른 forcing에 한 번만 합성하며 combined forcing을 다음 source로 쓰지 않는다.
원4,096걸음/600초·128사건/512선택 출력 제한을 유지한다.

- `start(context)`: 경계0 사건/출력 전 initial-ready checkpoint.
- `advance_chunk(context,checkpoint,boundary_budget)`: 원 경계1–128개를 처리한다. 경계0도 예산1개다.
- `checkpoint_bytes(context,checkpoint)`: 불변 canonical UTF-8 bytes.
- `restore_checkpoint(context,raw_bytes,expected_sha256=...)`: 외부에서 신뢰한 raw digest를 필수로 받는다.

공개 property는 JSON 복사본이다. 외부 checkpoint는64KiB 이하·닫힌 canonical JSON이며
중복 key/비유한 값/판본·context 혼합/단위·cursor·원 격자/현재 상태·진단/전역 수지를 검사한다.
내용을 다시 해시한 것만으로 진본을 증명하지 않는다. trusted expected digest의 서버 custody/서명은 후속이다.
Python 내부 객체/코드를 공격자가 재작성하는 환경의 인증 경계가 아니다.

## 실행·복원·실패

원 program과 같은 순서로 한 걸음 현재 환기 RK4→전역10수지→원자 관리→현재 환기/전역10수지→journal→선택 출력을 수행한다.
25연속/6사건 합계를 각 원 걸음/사건의 원 순서로 더한다. chunk 합계를 다시 더하지 않는다.
checkpoint에는 version/context hash·next_index·output/event cursor와 각 record의 canonical prefix chain,
마지막 확정108상태/25연속/6사건·유도량/환기 진단/10잔차·예산·phase를 담는다.
initial-ready(next_index0)와 경계0 완료(next_index1)를 구분한다. 초기/중간/마지막 사건을 정확히 한 번 처리한다.
chunk grouping·벽시계·호출 수를 checkpoint identity에 넣지 않는다.
같은 원 program의 임의 분할에서 모든 samples/events/last_confirmed와 최종 checkpoint bytes/prefix가 정확히 같아야 한다.

복원/각 advance의 검사는 현재 endpoint의 환기1회/공동 RHS1회와 seed 대비10수지만 확인한다.
과거 구간 적분/관리 재실행은0이다. 과거 원량/온도 이력은 trusted digest에 묶인 producer 기록이다.
완료된 새 걸음당 joint RHS6회/환기5회, 관리당 joint3회/환기1회를 확인된 계산 호출로 보고한다.
실패 trial 호출은 이 confirmed 횟수에 포함하지 않는다. 준비 호출과 checkpoint 검사는 별도다.

반환은 `yielded|completed|hold`·manifest/context hash·steps/planned_steps·output_start/event_start,
이번 samples/events·last_confirmed·checkpoint·hold이다.
checkpoint는 전체 해당 경계의 사건/출력까지 완료했을 때만 발급한다.
실패는 checkpoint=None·global step/elapsed/phase/reason/inner_failed_stage와 완료된 이번 prefix를 반환한다.
관리 후 환기/수지 실패는 같은 시각 사건 전 step-end를 보존하고 실패 사건/journal/선택 출력을 commit하지 않는다.
원 checkpoint 재시도는 결정적이다. 완료 checkpoint 재실행과 입력/context/transport/budget 오류는 typed `ContinuationRejected`다.
취소/crash/외부 예외는 정상 yield로 바꾸지 않는다.

## 수용 기준

1. 독립 참조로 수용한10program을 예산1/2/3/7/128 및 혼합 분할로 원 program과 정확 대사한다.
   모든108상태/25장부/6합계/10잔차·예산/환기 진단·사건 순서와 최종 canonical bytes/prefix를 포함한다.
2. 초기/사건 전후/마지막/완료 checkpoint를 fresh Python에서 trusted digest로 복원한다.
   복원은 현재 endpoint만 확인하며 이후에도 과거 step/event 재실행0을 실제 호출로 확인한다.
3. 원 identity·새/구 타입·실외 입력/다른 forcing/단위·schema/cursor/장부/진단·JSON/digest·상한 변조를 거부한다.
   실제 domain/수치 hold와 step/event/환기 trial 실패의 마지막 확정 상태·prefix를 원 program과 대사한다.
4. 최대512출력/128사건·chunk128/체크포인트64KiB·context2MiB를 실제 완료한다.
   관련 구 checkpoint/program 회귀·원본/frozen 두 서버·원 종료/FD/소유 정리와512MiB/합1GiB를 확인한다.

범위는 `software_research_only`, `synthetic_joint_ventilation_continuation_only`, G0_G4=`not_assessed`다.
UTC·불변 저장/현재 권리 API·worker/3D/사용자 배포·전체 작기/실제 품종/생산·경제 관문은 후속이다.
