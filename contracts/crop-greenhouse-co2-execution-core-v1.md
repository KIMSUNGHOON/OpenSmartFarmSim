# CO₂·일사 모델의 접수·자동 계산 핵심 — v1

Status: admission/checkpoint/worker core functionality accepted; independent consumer/restart pending.
[worker core 기능 수용](../research/crop-greenhouse-co2-worker-core-20261021.md)은 source0bca8cd/CI39527128812의
20검사·실제 SCRAM11·원 계산/UTC/원자 저장·취소/만료·늦은 fence와311지문/정리를 확인했다.
독립 자동 발견·fresh/SIGKILL은 후속 자식이며 worker 부모/공통 WSL·새 사용자 적용은 미완료다.
[consumer 사전 증거](../research/artifacts/crop-greenhouse-co2-worker-consumer-preflight-20261021.json)는
exact 입력/결과 쌍 등록 뒤 로컬 새17/기존 Solar14=31통과와 전체34수집을 확인했다.
독립 정상/hold·fresh 원 결과/권리·실제 SIGKILL3경로는 호스팅 검증 전이며 미수용이다.
[worker core 사전 증거](../research/artifacts/crop-greenhouse-co2-worker-core-preflight-20261021.json)는
로컬 제어9통과/전체20수집(실제 DB11 미실행)과 원 자료/서비스/상한 보존을 확인했다.
실제 계산/원자 저장은 위 호스팅 집중 검증으로 수용했으며 자동 발견·독립 프로세스·SIGKILL은 후속 자식이다.
[접수 기능 수용](../research/crop-greenhouse-co2-admission-20261021.md)은 source43c0a98/CI39520744344의
17검사·실제 SCRAM13과 원 입력/멱등·접수/취소 rollback·17계측0/정리를 확인했다.
전체 core/worker·공통 WSL 용량/새 사용자 적용은 미완료다.
[checkpoint 기능 수용](../research/crop-greenhouse-co2-checkpoint-20261021.md)은 sourcea8cc095/CI39524881613의
26검사·실제 SCRAM13·308지문과 원 상태/시각·현재/늦은 fence·계측/정리를 대사했다.
[첫 CI의 불변성 시험 준비 수정](../research/artifacts/crop-greenhouse-co2-checkpoint-immutable-test-fix-20261021.json)은
기존 DB의 이력/입력 UPDATE 거부를 보존한다. 잘못된 새 metadata와 최종 읽기 결과의 fault injection은
실제 DB 변경과 구분했고 같은26개를 재검증했다.
선행은 [명시 조회 runtime 기능 수용](crop-greenhouse-co2-runtime-v1.md)이다.
[기존 Solar 실행 핵심](crop-greenhouse-solar-execution-core-v1.md)의 임대/현재성/원자 게시 경계를 재사용한다.
공통 WSL 용량은 사용자 적용 전 조건이며 아래 개발의 별도 중복 장애로 계산하지 않는다.

## 구현 순서

1. **접수/취소:** `Co2ExecutionService`, `joint-co2-solar-execution-input-v1`과 별도
   `ossf-joint-co2-solar-execution-intent-v1` domain을 사용한다. 현재 Co2FarmBinding의 닫힌 원 요청,
   검증된 입력 증거/농장 결속 bytes·resolver 판본을 기존 simulation 작업에 고정한다.
   tenant·study/revision의 같은 의도는 같은 작업, 다른 입력은 충돌이다. 실제 commit guard에서 현재
   입력/권리·계정/범위·원 bytes를 다시 검사해 접수 중 철회 시 작업/사건/내용을 모두 rollback한다.
   접수는 적분/context 생성·결과 등록/worker를 실행하지 않는다. 취소는 원 입력 판본/tenant·현재 cancel
   범위로 제한하고 자료 이용권 철회 뒤에도 가능해야 한다. queued는 canceled, 실행 중은 cancel_requested다.
   기존 job의 원64KiB 요청/입력 한도를 유지한다. 취소는 자체 계약/code 지문도 검사하되 철회된 자료의
   binding.current를 호출하지 않는다. claimed 시험의 ack는 기존 JobStore이며 CO₂ worker 수용이 아니다.
2. **확정 checkpoint:** 별도 `Co2ExecutionCheckpointStore`·판본/사건 이름과 원 provenance를 사용한다.
   exact admission/custody/같은 binding·resolver/jobs를 검증한다. 잠금 밖 현재 입력 검증 뒤 짧은 확정
   잠금에서 임대/취소/원 입력/최신 사건을 재확인한다. 중복 확인은 최초 사건/시각을 보존하며 계산0이다.
   판본은 `joint-co2-solar-execution-checkpoint-v1`, 사건은 `co2_checkpoint_confirmed_v1`이다.
   원8KiB metadata/저장 commits+2 사건 한도와 signed HEAD ancestry를 유지한다.
   private reader 종료 뒤 거래 commit 전 현재 execution 권한을 마지막으로 확인한다.
3. **worker/발견:** exact `Co2ExecutionWorker`/result store와 같은 graph를 사용한다. 구간 전 현재성·
   임대 갱신, 제한된 advance 뒤 독립 checkpoint 확인, 기존 확정 HEAD 채택 뒤 남은 구간만 계산한다.
   원 custody의 현재 읽기 entry와 진행 응답을 버리는 `_advance_for_checkpoint` 경계를 유지한다.
   result/link·attempt outcome·terminal은 같은 DB 거래이며 늦은 fence 실패는 부분 결과0이다.
   정상만 publication을 만들고 수치 hold는 원 prefix/사유를 보존한다. 기존 discovery/loop의 닫힌 목록에
   새 판본/정확한 타입만 추가해 ID 수동 전달 없이 소비한다. 다른 선택 판본은 그대로 보존한다.
   먼저 worker core의 실제 계산/원자 저장을 수용하고, 다음 별도 자식에서 discovery/loop·독립 정상/hold·
   fresh 읽기/실제 SIGKILL 재개를 검증한다. worker 부모는 둘 다 통과해야 완료한다.
   terminal UPDATE 뒤 commit 전에도 execution 권한을 마지막으로 확인한다.
4. **진행/HTTP/화면:** 현재 진행 조회→접수/취소 HTTP→명시 실행 runtime→typed web→같은 UTC3D→
   WSL/사용자 적용을 각각 수용한다. 비공개 파일 HEAD나 접수 성공을 사용자 확정 생장으로 표시하지 않는다.

## 단계별 수용 기준

접수 자식은 실제 SCRAM의 같은 의도/다른 revision·닫힌 입력/다른 family·late 철회와 DB 원자성,
queued/claimed 취소·현재 계정/권리·원 job/input/event/FD/소유 정리를 확인해야 한다.
모의 binding만으로 실제 농장/DB 수용을 대신하지 않는다.

checkpoint/worker는 정상/수치 hold 원109상태·44연속/6사건 장부·17수지/사건10수지·UTC를
직접 원 계산/불변 저장과 대사한다. 같은/분할 예산, 중복 확인·fresh 재개/실제 SIGKILL·취소/임대 만료,
권리/계정/resolver/입력·마지막 게시 fence 변화에서 원 값/시각과 rollback을 검증한다.
독립 Python 소비자와 fresh reader에서 원 bytes/UTC·과거 재적분0·다른 판본 queued 유지·현재 권리를 확인한다.
원 자료/두 UI/5root·600초·512MiB/PID/합1GiB 및 소유 PG/schema/role/passfile 정리를 유지한다.

합성32초 소프트웨어 기능 수용이며 전체 작기/생과 변환·물/성분/구매 에너지·경제 연결,
실제 CLI 종단 간·독립 농장 자료와 G0–G4/품종 예측·추천은 해당 기존 부모의 후속이다.
