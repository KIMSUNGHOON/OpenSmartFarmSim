# 자동 출현 원 입력의 접수·멱등성 — v1

상태: [E1 신규13/순수185·실제 SCRAM2 수용](../research/crop-leaf-appearance-execution-admission-20261024.md).
E2는 [참조9/순수·관련203·실제 SCRAM9](../research/crop-leaf-appearance-execution-worker-20261024.md)로 수용했다.
E3는 [신규25/순수·관련244·실제 SCRAM7과 독립 fresh](../research/crop-leaf-appearance-execution-query-20261024.md)로 수용했다.
기존 자동 consumer 연결도 신규12/제어·관련148·실제 SCRAM1로 수용했다.
선행은 [appearance 서버 계산/현재 조회](crop-leaf-appearance-signed-artifact-v1.md)다.
기존 deterministic simulation의 jobs/attempts/events/publications/outcomes를 재사용한다.
새 큐/표·역할이나 수치 모델/원 결과·사용자 runtime 변경은 없다.

`LeafAppearanceExecutionService(authority,input_resolver=...)`는 정확한 appearance authority와
판본 고정 trusted resolver를 받는다. resolver는 tenant/닫힌 원 input 참조에서 program/source/evidence bytes만 반환한다.
요청은 사용자 경로/키·임의 callback을 받지 않는다.
simulation_create와 현재 farm/완료 parent·양쪽 계산/표시 권리를 확인하고 원 binding을 별도 소유 store에 보관한다.

64KiB job input은 `leaf-appearance-execution-input-v1`의 원 request/binding SHA/resolver 판본,
authority issuer/key ID·현재 code와 새 admission domain의 intent HMAC이다. 원 program/source/evidence나 키를 넣지 않는다.
study/revision의 versioned idempotency key로 같은 원 요청을 같은1행/job에 귀속한다. 다른 원 입력은 충돌이다.
기존 submit의 commit_guard가 원 bytes·현재 binding/검토·권한·판본을 다시 확인하며 실패하면 job/event 삽입을 롤백한다.
남은 private binding 객체는 게시 결과가 아니며 접수에서 생장/producer·CLI 계산을 실행하지 않는다.

`current_input(...,write=False)`는 intent·서명/binding·현재 resolver 원본과 parent/표시 권리를 대사한다.
write=True는 현재 계산 권리도 요구한다. simulation_create 없이 현재 read scope로 조회할 수 있다.
resolver/authority/code·원 입력/parent/판본이나 권리가 다르면 대체 입력을 쓰지 않는다. 조회의 작업/SQL·파일쓰기는 없다.

E1 수용: 원 byte bound/닫힌 참조·HMAC/판본·키·resolver/authority 변조 거부,
실제 SCRAM의 같은 접수1행·현재 입력 read/write 권한/충돌과 양쪽 현재/늦은 commit 철회 rollback,
생장/producer/CLI0·원 parent/서명 자료·행/파일·3root/WSL 상한·소유 DB/역할/임시 파일 정리다.

E2는 정확 tenant/input_version의 worker가 실제 signed producer1회와 lease/cancel/현재 입력을 확인해
같은 거래에서 opaque 참조·publication/outcome/events/terminal을 게시해야 한다.
E3는 그 원 job/publication/참조·현재 signed 결과의 status/manifest/frame/replay를 읽어야 한다.
E2/E3·자동 loop/보호 HTTP/같은 job3D, 실제 품종/자료·G0–G4 수용은 접수 성공과 별도다.

## E2 실제 계산과 원자 게시

`LeafAppearanceExecutionWorker(service,tenant_id=...,lease_seconds=600).run_once(job_id)`는
명시한 tenant/appearance input_version의 simulation만 claim한다. 현재 원 입력/parent·binding과
live lease/cancel을 확인한 뒤 실제 signed appearance producer를 job 잠금 밖에서 실행한다.
시작 사건의 planned_outputs는 현재 binding에 결속된 원 parent manifest의 samples에서 읽는다.
새 appearance manifest의 sample_count를 parent의 samples로 오인하지 않는다.

완료 결과의 현재 서명/binding과 원 입력·권리/검토·lease/cancel을 게시 전후에 확인한다.
기존 거래 안에서 publication·결과/성공 events·attempt outcome·terminal을 함께 저장한다.
`leaf-appearance-execution-result-link-v1`은 원 job/input/result에 결속된4KiB 이내 참조이며
원자료·수치 프레임·키를 담지 않는다. publication은 별도 appearance 판본/worker code/attempt를 대사한다.
새 큐/표·역할이나 CLI invocation을 만들지 않는다.

완료 재실행은 계산하지 않는다. 취소/만료/늦은 변경으로 private signed/참조 파일이 남아도
publication·성공 사건·조회 가능한 결과 참조를 게시하지 않는다. 만료 시 unclosed는 완료나
자동 재개 수용이 아니다. 계산 중 프레임/checkpoint 재개와 기존 자동 consumer의 명시 등록,
E3 현재 조회·보호 API/runtime/같은 job3D는 별도 단계다.

## E3 같은 작업의 현재 조회

`LeafAppearanceExecutionQuery.read(tenant,job_id,view='status'|'manifest'|'frame'|'replay',index=None)`는
닫힌 leaf-appearance-execution-read-v1/합성 FLAGS에 실제 job/cancel_requested·관측 시각과 원 parent lineage를 담는다.
frame만0이상 정수 index를 받고 전체 응답은2MiB 이내다. 조회에서 계산·CLI·작업/SQL·파일쓰기는 하지 않는다.

원 job/input/publication/outcome/events/invocations를 한 SQL statement의 같은 snapshot으로 읽는다.
원자 publication·현재 attempt/시작/성공·worker 판본·CLI 비위조 증거와 opaque 참조를 대사한다.
원 job과 signed 결과의 request/binding·parent·최초 시각을 유지하고 현재 양쪽 권리/검토를 전후 확인한다.
job input의 intent HMAC/현재 resolver 원 bytes도 조회 양 끝에서 검사한다.
완료 결과는 signed authority의 원 _load를 전후 실행하며 그 사이에 원 manifest/frame reader와 출처 결속을 확인한다.
새 sample_count로 재생하고 선택 frame·마지막 frame의 원 기간은 signed._frame_scope로 검사한다.
status/manifest도 마지막 시점이 원 기간 끝에 해당하는지 확인한다.

미완료 status는 현재 입력을 전후 검사하며 원 DB 묶음이 바뀌면 Pending으로 재조회한다.
원 result/root/calculated_at·UTC/12frame/47면적을 재계산 없이 유지하고 철회 때 부분 응답/fallback 없이 보류한다.
등록 읽기 scope는 요청 내부에 한정되며 요청 간 권리 cache를 만들지 않는다.
내부 단독 관측은 HTTP30초/U1 수용과 구분한다. 자동 consumer의 정확 판본/worker/outcome 등록,
보호 API/runtime·같은 job3D·메뉴/reload와 실제 자료/G0–G4는 후속이다.

## 기존 자동 consumer 연결

leaf-appearance-execution-input-v1과 정확 LeafAppearanceExecutionWorker/LeafAppearanceExecutionOutcome을
기존 discovery 허용 목록과 DeterministicWorkerLoop에 명시 등록한다.
구성은 비어 있거나 다른 모델/혼합 판본일 수 없으며 기본 구성에서 실행하지 않는다.
기존 전경 명령은 operator factory를 요구한다. 구성 생성 자체는 계산을 시작하지 않는다.
다른 타입/다른 job/미종결 outcome은 종료 메타데이터로 게시하지 않는다.

실제 discovery→1계산/원자 완료·같은 원12frame/47면적과 현재 두 Scope 철회 거부,
다른 두 queued 판본/원25표 행·parent18파일 보존·완료 재선택0을 확인했다.
새 큐/서비스나 수치 모델은 추가하지 않았다. 보호 API/owned runtime·같은 job3D는 후속이다.
