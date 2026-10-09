# 공동 작물·기후 결과의 현재 조회 v1

`JointCropClimateCurrentQuery(store).read(tenant, result_id, farm_ref, view='summary', offset=0, limit=None)`은
정확한 새 result store만 받고 `joint-crop-climate-current-query-v1`로 원 결과를 직렬화한다.
응답은 [닫힌 API 투영](api-crop-climate-joint-replay-v1.md)의 UTF-8 bytes 또는 현재 계정에 없는 결과의 None이다.
새 authority/key/서비스를 만들지 않는다. 원 store/custody·입력 authority·권리 resolver·farm/jobs를 재사용한다.

## 같은 읽기 세션

store `_read`가 현재 농장/자료/계정, DB metadata/HMAC와 서명 intent/HEAD/proof를 검증하고 원 custody 잠금을 유지한다.
그 세션 안에서 같은 root의 artifact reader가 원 manifest/UTC·summary/페이지 소속과 bytes를 검사한다.
투영 직전과 직렬화 뒤 DB row·원 record/packet·컬럼/HMAC를 다시 대사한다.
반환 전에 reader의 HEAD/root/header, custody의 현재 입력/자료 권리와 원 progress를 재확인하고 모든 FD/잠금을 닫는다.
중간의 권리 철회·계정 비활성/권한 회수·원 파일/DB 변조·다른 농장·코드/조립 변경은 응답을 내보내지 않는다.
HTTP에서 실제 송신 전 계정 재검사와 연결 종료 처리는 후속 route 계약의 책임이다.

summary/samples/events의 원108상태·장부·단위·마이크로초 UTC·completed/hold·마지막 확정값을 바꾸지 않는다.
summary는 offset0/limit없음, samples64/events8·정확한 정수 offset·최대 직렬화2MiB다.
소속 페이지를 원 reader에서 받으며 caller가 page/terminal/raw metadata를 주입하는 인자는 없다.
조회 중 Context/RHS/관리/적분·UTC binding/새 행 생성·자료 검토/관문 승격을 실행하지 않는다.
미존재는 None, 계정/역할 거부와 custody Pending은 원 예외를 유지하고 그 밖의 실패는 일반 JointCurrentQueryHold다.
private 오류문/자격증명·raw 입력은 응답에 포함하지 않는다.

## 수용과 범위

실제 SCRAM에 등록한 소유 completed/hold를 원 투영 응답과 대사한다. 별도 exec도 같은 bytes/SHA를 읽어야 한다.
투영 중/직렬화 뒤 권리 철회, 원 DB/HMAC/컬럼·페이지/HEAD 변조, 계정·다른 농장·한도/조립 거부를 확인한다.
조회 계산0·원본/기존 UI·WSL 한도·FD/PG/schema/role/passfile/소유 프로세스 정리를 확인한다.
소유 합성32초/16걸음의 소프트웨어 범위다. HTTP/runtime·새3D/U3·실제 품종/작기·G0–G4는 별도 수용이다.
