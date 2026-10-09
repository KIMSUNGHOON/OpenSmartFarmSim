# 원 저장 결과를 보존하는 조회 타입 — v1 후보

2026-10-07 KST. [결과 증명](crop-cycle-result-evidence-v1.md)과
[구현 계획](../tasks/todo.md)의 `crop-cycle-result-read-context`에 해당한다.
3 core파일: `backend/app/crop_cycle_result_read_context.py`,
`backend/tests/test_crop_cycle_result_read_context.py`, 이 계약.

## 인터페이스

`open_result_read_context(result_directory, artifact_sha256, input_directory, input_root_sha256,
input_evidence_raw, result_evidence_raw, *, authority)`는 정확한 `ResultEvidenceAuthority`로
현재 증명을 검증한 뒤 소유 no-follow result FD를 연다. 발행 시의 inode와 현재 경로/FD를 대사한다.
반환되는 `ResultReadContext`는 기존 `ArtifactReader`/`StreamContext`와 별도 타입이다.
원 private token·객체/캐시를 구성하거나 기존 계산/농장 저장 타입에 주입하지 않는다.

`summary`, `manifest`, `context_record`는 원 JSON 값의 독립 사본이다. `identity`는 새 조회
판본/code/dependency SHA와 결과 증명 identity·원 math context SHA를 함께 보존한다.
원 계산이 새 조회 code로 실행됐다고 재표시하지 않는다. `rights_or_gate_approval`은 false다.

`page(kind, start=0, limit=None, *, max_bytes=2097152)`는 원 `samples`/`events`의
`{kind,start,next,total,records}`를 반환한다. `start`는0..원total의 정수이며 `limit`는
sample1..64/event1..8의 정수다. 기본값은64/8이다. `max_bytes`는1..2MiB의 정수로,
더 작은 응답 예산과 byte-short 검증을 지원하며 원 공개 한도를 올리지 않는다.
같은 UTC·값·순서·관리 사건을 보존한다. 예산으로 짧아지면 `next`는 실제 반환 원 위치이며,
첫 record도 담을 수 없으면 hold다. 끝에는 같은 total/빈 records를 반환한다.

## 파일·현재 상태와 자원

page는 증명된 원 index의 blob만 읽는다. 현재 소유/0400 regular·단일 링크/ACL·no-follow·
읽기 전후 metadata·실제 SHA/canonical JSON/count/첫·끝 UTC를 대사한다.
cache는 sample/event 각각 한 원 page뿐이며 caller에 사본만 반환한다.
cache hit도 현재 파일 보안/metadata를 대사한다. 요청 한 번에서 같은 blob을 반복 해석하지 않는다.

각 summary/page/identity/context 반환 전 `recheck`로 현재 authority/source/키·모든 입력/결과
bytes·원 inode/index/summary/context를 대사한다. 조회 중 입력/result 교체·변조는 hold이며
FD/cache를 닫는다. `recheck`, context manager와 멱등 `close`를 제공하고 닫힌 뒤 조회를 거부한다.
판본/서명 거부·열기 실패·byte-short 실패·재시작의 FD 정리를 확인한다.
원 full parser/context 준비/QC/RHS를 실행하지 않는다. 미래 변조·메모리/키 침해를 증명하지 않는다.

## 수용 경계

원 작은 정상3사례/숫자 hold의 모든 page·summary/index·관리 전후/끝·다른 limit를 원 reader와 대사한다.
실제 작은 응답 예산의 byte-short/진행/원량 보존과 첫 record 초과 거부를 확인한다.
현재 파일/입력/HEAD·cache 후 변조/디렉터리 교체·코드/authority·잘못된 위치/한도·닫힘을 거부한다.
별도 Python의 같은 보존 키/증명·실제 원 checkpoint/manifest·FD/RHS0과 focused test를 기록한다.

이 개발 수용은 현재 농장 권리/등록·원 DB/custody trace·전체166일/HTTP/3D 수용이 아니다.
원166일의 [상태 유실](../research/crop-cycle-full-rhs-missing-state-20261007.md)을 유지하며,
다음은 실제 Farm/Scope/권리·원 server trace의 명시적 조회 연결이다. 복원/부하 부모·G0–G4는 별도다.
