# 출현 잎의 접수·완료 참조와 현재 조회 — v1

상태: [E1 제어12/실제 SCRAM2](../research/crop-leaf-population-execution-admission-20261023.md) 수용.
[E2 참조9/실제 SCRAM7](../research/crop-leaf-population-execution-worker-20261023.md)도 수용했다.
[E3 집중16/실제 SCRAM6·fresh](../research/crop-leaf-population-execution-query-20261023.md)도 수용했다.
선행은 [signed leaf 계산/조회](crop-leaf-population-signed-artifact-v1.md)다.
기존 deterministic simulation의 jobs/attempts/events/publications/outcomes를 사용하며 새 큐/표·역할은 추가하지 않는다.
자동 consumer 및 보호 HTTP/사용자 화면은 후속 수용이다.

## E1 접수

`LeafPopulationExecutionService(authority,input_resolver=...)`는 정확한 leaf authority와
판본 고정 trusted resolver를 받는다. resolver는 tenant/닫힌 leaf input 참조에서 원 program/source/evidence bytes만 반환한다.
사용자 파일 경로/키/임의 callback은 요청에서 받지 않는다.
simulation_create·현재 farm/parent job·양쪽 자료의 계산/표시 권리를 확인한 뒤 현재 binding을 기존 소유 store에 보관한다.

job input은 `leaf-population-execution-input-v1`/원 request/binding SHA/resolver 판본,
authority issuer/key ID·현재 code와 별도 admission intent HMAC이다. 원 자료/키 없이64KiB 안에 참조만 둔다.
study/revision의 versioned idempotency key로 같은 요청은 같은1행/job에 귀속하고 다른 원 입력은 충돌로 거부한다.
기존 submit의 commit_guard가 원 bytes/현재 binding·권한/검토를 다시 확인하며, 실패 시 job/event 삽입을 롤백한다.
남은 private binding blob을 결과/승인 Run으로 세지 않는다. 접수에서 생장/producer·CLI 계산은 없다.

`current_input(...,write=False)`는 intent·서명/binding bytes와 현재 resolver 원본/parent·표시 권리를 검증한다.
write=True는 현재 계산 권리도 요구한다. 조회는 새 simulation_create 권한 없이 가능하되 현재 read scope를 유지한다.
resolver/authority/code·원 입력/판본/parent 또는 현재 권리 불일치에는 대체 입력을 사용하지 않는다.

## E2 worker와 E3 현재 조회

E2는 정확 tenant/input_version만 claim하고 실제 signed producer1회·lease/cancel/current input을
게시 전후 확인해 같은 거래에서 opaque 참조/publication/outcome/events·terminal을 게시한다.
다른 queued 모델은 보존하며 실패/취소/만료 때 private 자료가 남아도 결과 참조를 게시하지 않는다.
`LeafPopulationExecutionWorker(...).run_once(job_id)`의 계획 출력 수는 현재 binding의 원 parent manifest에서 읽는다.
계산은 job 잠금 밖에서 수행한다. 완료 artifact는 `leaf-population-execution-result-link-v1`의4KiB 이내 참조이며
publication/version·worker code·attempt와 실제 시작/완료 사건을 대사한다. CLI invocation을 위조하지 않는다.
만료된 시도의 unclosed는 완료가 아니며 기존 임대 회복 정책의 대상으로 남는다.
이 v1의 계산 중 프레임/checkpoint 재개·기존 foreground consumer의 정확 worker/outcome 등록은 별도다.
E3는 실제 job/publication/opaque 참조·현재 signed 결과를 대사해 status/manifest/frame/replay를 제공한다.
원 result/root/계산 시각·UTC/12frame을 유지하고 조회에서 계산/쓰기/CLI0, 철회 때 fallback 없이 보류한다.
`LeafPopulationExecutionQuery.read(tenant,job_id,view='status'|'manifest'|'frame'|'replay',index=None)`는
닫힌 `leaf-population-execution-read-v1` 응답에 실제 job/cancel_requested·관측 시각과 원 parent lineage를 담는다.
완료 응답은 동일 signed authority의 원 `_load`를 전후 실행하며 그 사이에 원 manifest/frame reader·출처 결속을 검증한다.
같은 payload/binding/packet과 양쪽 현재 권리·검토를 대사하며, 별도 중복 public reader 호출이나 요청 간 권리 cache를 만들지 않는다.
job input의 intent HMAC/현재 resolver 원 bytes는 조회 양 끝에서 확인한다. 미완료 status는 현재 입력 결속을 전후 검증한다.
job/publication/events/outcomes/invocations는 한 SQL statement의 같은 snapshot으로 읽는다.
원자 publication/시도·원 job/input/시작·완료/CLI 비위조 증거를 확인하고 전후 DB 묶음이 바뀌면 Pending으로 재조회한다.
frame만0이상 정수 index를 받고, 전체 응답은2MiB 이내다. 실제 HTTP30초 예산은 별도 전송 검증 전까지 미수용이다.
이후 보호 API/runtime·같은 job의 실제3D·메뉴/reload 복원을 수용한다.

E1 수용: intent/판본·원 byte bound/키·resolver·원 참조 변조 거부,
실제 SCRAM의 같은 접수1행·충돌/현재 조회·read/write 권한과 source/parent·늦은 commit 철회 rollback,
생장/producer/CLI0·기존 parent/leaf 결과 행/파일·원2서비스/WSL 상한·소유 정리다.
실제 품종/자료와 G0–G4, E2/E3·제품 전체 수용을 접수 성공으로 대신하지 않는다.
