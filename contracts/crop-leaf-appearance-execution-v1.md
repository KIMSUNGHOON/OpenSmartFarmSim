# 자동 출현 원 입력의 접수·멱등성 — v1

상태: E1 구현/수용 전. 선행은 [appearance 서버 계산/현재 조회](crop-leaf-appearance-signed-artifact-v1.md)다.
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
