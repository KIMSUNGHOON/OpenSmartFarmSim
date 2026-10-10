# 작물 계산 요청·확정 진행·완료 결과 연결 v1

상태: **E1 접수 service 로컬 수용; worker/API/UI 연결 미완료 — 2026-10-10.**
[코드 대조 근거](../research/crop-execution-link-boundary-20261010.md)와
[작업 순서](../tasks/plan.md#작물-계산과-ui의-실행-연결--2026-10-10)를 따른다.
대상은 현재 수용된 짧은 합성 joint 입력·108상태·UTC·서명 저장이다.
실제 자료/생산 게시 관문은 [제품 명세](../docs/PROJECT_SPEC.md)의 기존 조건을 따른다.

## 요청과 실행 의도

기존 `JobStore`의 simulation 작업, 임대·시도·취소·재시도·감사 테이블을 사용한다.
API의 전경 요청에서는 입력 권리·현재 농장 판본을 확인하고 작업만 접수한다.
`JointFarmBinding.prepare/current`와 서버 소유 input resolver를 사용하며 Context 생성,
RHS·적분·사건·custody.advance 또는 결과 등록을 접수 중에 호출하지 않는다.
열 계산용 `AuthoredSimulationService`나 승인 Run으로 공동 계산을 위장하지 않는다.

새 닫힌 입력 판본은 `joint-crop-climate-execution-input-v1`이다. 구성은 `input_version`,
`request`, `farm_binding`, `farm_binding_sha256`, `input_resolver_version`이며 tenant는
서버 인증 문맥과 검증된 binding에서만 얻는다. request는 기존 joint farm 요청 그대로다.
binding은 원 canonical bytes를 JSON 객체로 결속하고 SHA는 그 원 bytes의 SHA-256이다.
서버 경로·키·raw 원자료·CLI 출력은 요청에 받지 않는다.
기존 job의 canonical UTF-8 **64KiB 상한**을 적용한다. farm binding의128KiB 상한으로
job 상한을 넓히거나 잘라 저장하지 않는다. 초과 요청은 접수 전에 거부한다.

tenant/study/revision당 하나의 실행 의도를 만든다. 기존 jobs의 tenant/stage별 멱등 키에
`ossf-joint-crop-climate-execution-intent-v1\0` domain과 canonical `[study_id, revision]`의 SHA-256을 사용한다.
별도 caller 키로 같은
custody intent의 작업을 여러 개 만들지 않는다. 같은 입력 재요청은 원 job을 반환하고,
같은 revision의 다른 입력·binding·resolver는 conflict다. 취소/실패 뒤 새 의도로 시작하려면
새 revision을 사용한다. 임대 재시도는 같은 작업의 기존 시도 정책을 따른다.
접수 transaction의 commit guard에서 현재 binding/권한과 원 입력을 다시 확인한다.

## 작업 상태와 checkpoint의 의미

| 상태/전이 | 서버 근거와 화면 표시 | 수용 증거 |
| --- | --- | --- |
| 없음 → queued | 검증된 불변 요청과 job ID. checkpoint는 null | 실제 SCRAM 접수, 중복/충돌, 접수 계산0 |
| queued → simulating | 현재 임대/시도. 작업 시작만으로 계산 진척을 만들지 않음 | 다른 worker claim 거부, 현재 입력/권한 |
| simulating → 확정 checkpoint | 서명 HEAD/proof·원 steps/counts/UTC를 살아 있는 임대가 DB 감사 사건으로 수용 | 원 값 대사, 늦은 임대·취소·권리 변경 거부 |
| 임대 만료/일시 오류 → queued | 원 시도와 마지막 확정 checkpoint 유지. 재시도 대기 | 강제 종료 뒤 새 시도, 원 prefix 재적분0 |
| queued → canceled | 기존 JobStore.cancel의 즉시 취소 | worker claim/결과 등록0 |
| simulating → 취소 요청 → canceled | 요청 수락과 worker 확인을 구분. 기존 상태와 cancel_requested 표시 | chunk 도중/완료 직전 취소, 부분 결과 비게시 |
| simulating → succeeded | completed root·결과 등록·job publication·terminal 상태의 같은 DB transaction | 실제 저장 result ID/원 값/최초 시각, rollback |
| simulating → hold | 수치 hold의 마지막 확정 상태와 실패 진단. 검증된 terminal 연구 결과만 선택 가능 | 실패 trial 정상 행0, hold 결과/진단 대사 |
| simulating → failed/권리 hold | 안전한 reason code. 새 선택 가능한 결과 없음 | 잘못된 입력·최대 시도·현재 철회, 비밀 누출0 |

`jobs.updated_at`은 heartbeat·취소에도 바뀌는 **작업 갱신 시각**이다.
기존 custody progress의 `times`는 **계산 시간축**이며 실제 벽시계 게시 시각이 아니다.
둘을 계산 진척 갱신 시각으로 대체하지 않는다.

기존 불변 `job_events`에 닫힌 `joint_checkpoint_confirmed_v1` 사건을 기록한다.
내용은 version·서버가 부여한 단조 publication_sequence·원 HEAD/proof/binding/context/time SHA·
확정 steps/planned_steps·samples/events·계산 status·computed_through_utc다.
전체 checkpoint/상태 벡터·원자료를 reason JSON에 복사하지 않는다. 최대8KiB의 canonical snapshot을
검증하고 job 행을 잠근 transaction 안에서 현재 임대·취소·권한/원 입력을 확인한다.
같은 HEAD 재확인은 같은 사건/최초 recorded_at을 반환하며, 새 HEAD는 원 서명 계보를 검증한다.
시도 재시작 시 sequence/확정 걸음을 뒤로 돌리지 않고 heartbeat만으로 사건을 추가하지 않는다.
조회는 같은 kind의 검증된 sequence로 고르며 recorded_at 동률/UUID 정렬로 진척 순서를 추측하지 않는다.
별도 진행 테이블/큐/서비스는 현재 근거가 없다. 실제 비용 문제는 실측 뒤 별도 판단한다.

## 임대와 파일 저장의 경계

worker는 chunk 전후 현재 임대·취소·권한을 확인하고 원 예산1–128의 advance를 순차 호출한다.
하나의 긴 적분 동안 job 행 잠금을 보유하지 않는다. chunk 비용과 임대 갱신 주기는 실측한다.
기존 custody의 파일 lock과 서명된 원 checkpoint 복원을 사용한다.
현재 custody 자체에는 job 임대/취소 fence가 없으므로, 계산 도중 임대 상실/취소로
비공개 파일 HEAD가 생길 수 있다. **그 HEAD만으로 사용자 작업 진척/완료를 게시하지 않는다.**
worker가 현재 임대로 검증해 DB 사건에 수용한 checkpoint만 작업 진행으로 제공한다.
이 정책은 filesystem와 PostgreSQL 전체의 원자 transaction을 뜻하지 않는다.

HEAD 후 DB 사건 전 crash는 동일 작업의 새 임대가 원 HEAD/현재 권리를 검증해 수용한다.
원 prefix를 다시 적분하지 않는다. reader가 DB 사건과 현재 HEAD의 차이/잠금을 만나면
`checkpoint_status=unavailable`과 갱신 대기를 표시하고 새 HEAD를 계산 완료로 추측하지 않는다.
취소된 작업은 자동 재개하지 않는다. 취소/오류 시 선택되지 않은 파일은 private 이력으로 남는다.

## 결과 게시

현재 `JointCropClimateResultStore.put`은 자체 transaction이다. 결과를 먼저 commit하고 나중에
job을 완료시키는 방식은 허용하지 않는다. store의 기존 검증/삽입을 호출자 소유 transaction에서
사용할 수 있는 좁은 내부 hook으로 추출하고 기존 put은 그 경로를 재사용한다.
terminal root, 현재 farm/input/rights, 원 입력·임대·취소를 확인한 뒤 같은 DB 연결에서
결과 registry, 닫힌 publication manifest, terminal state/event/outcome을 함께 commit한다.
publication artifact SHA/size는 등록한 canonical 결과 packet의 SHA/bytes이며 root SHA와 구분한다.
manifest는 새 joint 판본·job/attempt·원 input SHA·result ID·packet/root/HEAD/proof SHA를 결속한다.
권리 거부/취소/임대 상실/예외면 이 DB 변경을 모두 rollback한다.
수치 hold에는 hold 결과를 연결할 수 있으나 실행 권리/자료 거부 hold에는 결과 ID가 없다.
연구 result의 status/scope/관문을 변경하거나 승인 Run/Assessment 통과로 표시하지 않는다.
store 변경으로 바뀌는 code pin/packet은 새 판본으로 취급한다. 기존 immutable metadata를 고치지 않고
기존 결과의 frozen reader/증거를 보존한다. 명시 호환 검증 없이 과거 결과를 새 worker에 채택하지 않는다.

## HTTP와 화면 경계

후속 경로는 `POST /v1/crop-climate-joint-executions`,
`GET /v1/jobs/{job_id}/crop-climate-joint-execution`,
`POST /v1/jobs/{job_id}/crop-climate-joint-execution/cancel`이다.
tenant는 인증 문맥에서만 얻는다. 새 기능은 명시적 runtime 조립이 있을 때만 활성화한다.
기존 generic JobStatus와 저장 결과 GET의 응답 형식은 유지한다.
읽기는 metadata+현재 작물 표시 권한, 접수는 simulation_create+현재 작물 쓰기 권한,
취소는 cancel+현재 대상 소유/접근 확인, worker는 simulation_execute+현재 작물 쓰기 권한을 요구한다.
현재 표시 권리 철회로 수치 조회가 거부돼도 소유자의 취소 권한까지 없애지 않는다.
취소는 과학 자료의 현재 사용 권리를 요구하지 않고 tenant/job/판본과 cancel scope를 검사한다.
누락/다른 tenant는404, scope 거부403, 잘못된 요청422, revision 충돌409,
현재 자료/검증 거부422, 일시 저장소/잠금 불가503으로 공개 reason만 반환한다.
terminal 취소 재요청은 실제 terminal 상태를 반환하며 성공 취소로 바꾸지 않는다.

진행 DTO의 allowlist는 version/scope/G0_G4, 기존 JobStatus,
cancel_requested, observed_at, checkpoint_status(`none/current/unavailable`),
checkpoint(null 또는 원 SHA/counts/status/computed_through_utc/checkpoint_recorded_at/publication_sequence),
result(null 또는 result ID/원 farm 참조/terminal status)다.
`checkpoint_recorded_at`은 **DB가 checkpoint를 수용한 시각**이며 HEAD 파일 생성 시각이 아니다.
`observed_at`은 상태 조회 시각이다. 식물 성장률·ETA·물리값을 steps 비율에서 만들어내지 않는다.
현재 조회에서 입력 hash/서명 계보·권한과 결과 ID의 같은 job/farm/batch/판본을 전후 대사한다.
조회 중 Context/RHS/restore/advance/행 생성/등록은0이어야 한다.

첫 UI 연결은 계산 접수·확정 걸음/계산 UTC·최종 갱신·재접속·취소·완료/hold 결과 선택이다.
bounded polling은 앞 요청 정산 뒤에만 시작하고 숨김/계정/선택 변경/해제 때 중단한다.
초기 대기10초, 일시 오류 시 최대60초까지 backoff하고 실제 응답 비용/최대 화면 지연을 보고한다.
근거는 작은 기존 reader의4.840–8.466초 관측이며 새 진행 API의 비용을 보장하지 않는다.
권리/인증 거부면 수치·장면을 지우고 자동 재시도를 멈춘다. epoch/Abort로 늦은 응답을 막는다.
끊김에서는 기존 수치를 현재값처럼 표시하지 않고 마지막 확인/연결 상태를 구분한다.

현재 custody/result page는 **terminal root만** 읽는다. 따라서 첫 연결에서는 계산 중
진행 정보만 갱신하고 완료/hold 결과를 기존 같은 UTC3D로 연다.
계산 중 새 prefix의3D에는 불변 prefix 페이지·HEAD 수용·현재 권리·동시 게시를 검증하는
별도 후속 계약이 필요하다. 미확정 trial/임의 보간·애니메이션을 생장 계산으로 표시하지 않는다.
기존 전체166일 결과는 이 짧은 joint 작업으로 소급 결속하지 않는다.

## 착수·검증

**E1 합성 실행 접수**는 [로컬 검증](../research/crop-climate-joint-execution-admission-implementation-20261010.md)으로 수용했다.
`JointCropClimateExecutionService(binding, input_resolver=...)`의 `submit(tenant, request_raw)`가
서버 내부 JobStore row를 반환한다. HTTP 응답은 후속 route의 명시 allowlist 투영을 거쳐야 한다.
변경은 새 service/test와 이 계약의 세 core파일이다. 현재 authority·principal provider·resolver와
입력 판본/domain/상한·코드 identity를 고정하고 commit guard에서 원 binding을 재검사한다.
입력 해석/검증 거부는 고정 `JointCropClimateExecutionHold`, 권한 거부는 고정 PermissionError,
같은 revision 충돌은 고정 JobIntentConflict다. 내부 경로/예외 원문을 메시지에 넣지 않는다.
정상 job 입력은7,827bytes였고 잘못된 요청/64KiB 초과와 oversized binding fault를 접수 전에 거부했다.
실제 SCRAM 새9/회귀8=고유17검사·동시 중복/충돌·현재 권한/권리·늦은 rollback·다른 tenant를 확인했다.
접수 중10종 수치 준비/적분/custody/결과 등록 호출0, 기존 job/store·원본2,148/미리보기 보존과
실제 종료/소유 정리를 기록했다. fixture가 입력 증거를 만드는 준비 단계의 계산은 이0회 주장에 포함하지 않는다.
아직 discovery/worker는 새 입력을 소비하지 않는다. 현재 API/UI에 접수·진행 경로를 노출하지 않는다.
다음은 **E2 확정 checkpoint 수용**, 독립적으로 준비할 수 있는 **E3 결과 transaction hook**이다.
worker/API/UI는 각자 [todo](../tasks/todo.md)의 증거가 있을 때만 수용한다.
