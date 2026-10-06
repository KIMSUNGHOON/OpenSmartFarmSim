# 원 계산 판본을 보존하는 입력 조회 문맥 — v1

상태: **구현 후보**, 2026-10-06 KST. 선행: [원 검사 영수증](crop-cycle-input-evidence-v1.md)의 로컬 수용.
원 reader/engine의 exact type·private token·code SHA를 바꾸지 않으며 실행 중인53개 source를 보존한다.
3 core파일: `backend/app/crop_cycle_input_read_context.py`, 집중 시험, 이 계약.

## 인터페이스·판본

`open_input_read_context(directory, root_sha256, evidence_raw, *, authority)`는 정확한 서버 영수증
authority로 현재 전체 bytes/서명을 확인하고, 새 **조회 전용** `InputReadContext`를 연다.
현재 root를 별도 no-follow FD에서 다시 확인하고 같은 디렉터리 inode와 원 증명/모든 bytes를
재대사한 뒤에만 반환한다. 정상/실패/close에서 FD와 현재 page/grid cache를 정리한다.

`context_record`와 `manifest`는 인증된 원 계산 기록/manifest의 사본이다. 원 initial/121 seed·
Fraction clock·plan·grid index·계산 manifest SHA를 보존한다. `identity`에는 별도 조회 판본/코드 SHA·
영수증 SHA·원 input root/계산 context SHA를 기록한다. 새 조회 코드가 원 계산을 수행했다고
재표시하지 않는다. 원 `InputPacket`/`StreamContext` 객체/token을 구성하거나 주입하지 않는다.
원 engine/start/advance와 v1 farm/artifact의 exact type 검사는 이 새 타입을 거부한다.

`record(kind,index)`, `segment(index)`, `boundary_page(cursor,limit)`, `cursor_bytes/restore_cursor`,
`boundary(index)`는 원 record/단위·Fraction clock·경계/cursor·전역 step/position 규칙을 재사용한다.
현재 block 읽기는 기존 server 파일의 소유권/0400/단일 링크/ACL·metadata·크기·SHA와
원 JSON/schema/정규화/시각 index를 확인한다. kind별 한 block/grid 한 page만 cache한다.
cache hit에서도 현재 파일 metadata/보안 조건을 확인하고 바뀌면 다시 읽어 SHA를 검사한다.
이 metadata cache는 SHA를 대체하는 승인이나 미래 불변성 증명이 아니다.

`recheck()`는 현재 원 디렉터리 inode·proof/source/profile/config·전체 root/blob bytes를 다시 대사한다.
공개 결과를 반환하기 직전에 호출해야 하며, 호출 사이의 미래 변경이나 메모리/키 침해를 보장하지 않는다.
current farm/Scope/등록/권리의 전후 검사와 결과 artifact/custody 검증은 후속 연결에서 별도로 유지한다.
`rights_or_gate_approval`은 false다. 현재 v1 factory/worker/runtime/API/3D에는 연결하지 않는다.

## 수용과 후속

- 최초 전체 parser/preflight/prepare_context/RHS 없이 영수증을 받아 정상 조회; 원 context/index/plan을 보존.
- 작은 자체 소유 사례의 모든 records·segment clock·boundary page/cursor·step/position을 원 reader/engine과 대사.
- 같은 input의 별도 Python 재시작에서도 같은 조회; 잘못된 proof/code/authority·물리 변조/교체·
  cache 이후 변경·미지원 cursor/범위·닫힌 문맥을 거부하고 FD/cache를 정리.
- 고정166일 입력에서 실제 open/recheck·시작/중간/끝·관리 전후 원 경계/clock·모든 경계/step 대사와
  시간/CPU/RSS/FD/RHS0·source53 보존을 기록. 원 전체 계산/수지·30초 HTTP·실제 품종 검증으로 확대하지 않음.
- 원 engine가 새 타입을 거부함을 확인. 이 문맥은 입력의 조회 증명이며 계산 완료/결과 검증을 승인하지 않음.

사용자는 새 타입/원 계산 판본의 대응 계약·실제 조회 검증/비용 보고서와 불변 receipt를 확인한다.
다음은 원 전체166일 종료/수지/복원 수용 뒤 결과 검증·현재 farm 권리·공개 조회에 이 조회 판본을
명시적으로 연결하는 작업이다. legacy 경로의 code/type 검사를 우회하거나 기존 결과/manifest를 수정하지 않는다.
replay-restore/부하 부모·G0–G4는 미수용이며 실제 품종/독립 국내 자료0건·예측/추천 보류를 유지한다.
