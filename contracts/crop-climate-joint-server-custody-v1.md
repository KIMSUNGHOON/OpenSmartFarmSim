# 공동 작물·기후 계산의 서버 소유 이력 v1

선행은 [현재 농장/자료 결속](crop-climate-joint-farm-binding-v1.md),
[원 입력 증거](crop-climate-joint-input-evidence-v1.md), [분할 실행](crop-climate-joint-continuation-v1.md),
[UTC](crop-climate-joint-time-v1.md), [불변 저장](crop-climate-joint-storage-v1.md)이다.
새108상태 producer와 원 프로필/입력/UTC를 사용한다. 기존121상태의 authority/context/reader로 위장하지 않는다.
서버 내부 Python 경계이며 DB 결과 등록·HTTP API·3D·사용자 실행/U3·전체 작기는 후속이다.
합성 소프트웨어 계산만 대상으로 하며 G0–G4는 `not_assessed`다.

## 서버 조립과 호출

`JointServerCustody(binding, directory, input_resolver=..., integrity_key=...)`는 정확한 새 `JointFarmBinding`,
소유자 전용700 POSIX root,32–4096byte 서버 비밀키, 고정 `version`을 가진 trusted resolver를 받는다.
resolver는 `(tenant, source_sha256, evidence_sha256)`에서 `(input_directory, evidence_raw)`를 반환한다.
임의 경로·비밀키·resolver는 사용자 요청에 포함하지 않는다. 입력 원본의0400/단일 링크/소유자·검토/코드/원 해시는 선행 authority가 다시 검사한다.
기존 농장 authority SCRAM/scopes/grant 감사 정책을 재사용하며 새 DB/역할/서비스를 만들지 않는다.

`advance(tenant, request_raw, budget=1..128)`는 한 번에 원 격자의 제한된 boundary를 계산한다.
`inspect(tenant, request_raw)`는 서버가 확정한 현재 이력을 읽는다.
`page(tenant, request_raw, expected_progress_raw, kind, start=0, limit=None)`는 완료/hold의 불변 root에서
기존64sample/8event 및2MiB 제한 페이지를 읽는다. 미완료 prefix의3D 조회는 이 계약의 게시 범위가 아니다.
읽기는 Context/Binding 준비·checkpoint 복원·RHS·적분·사건 실행을 하지 않는다.
write 준비의 초기 RHS1회와 저장 endpoint 복원 RHS1회는 새로운 경계 계산과 구분한다.
이미 final root가 있는 `advance` 재호출은 현재 write 권한을 확인하고 같은 상태를 반환하며 재계산하지 않는다.

## 이력과 복원

tenant/study/revision의 새 domain SHA 이름 아래 원 요청 SHA·농장 결속·resolver/code/의존성/상한을
새 intent domain HMAC으로 서명한다. 같은 revision의 다른 요청은 conflict, 잘못된 HMAC/현재 권리·원량은 hold다.
root/intent의 기존 비차단 file lock과 nofollow·정확한 소유자/모드/단일 링크 검사를 재사용한다.
file helper의 기존 용량 상한을 고정하고 공동 저장의 페이지/commit 상한은 별도로 유지한다.
계산 전 원 source로 공식 Context/UTC를 만들고 원 서명 evidence의 record와 byte 대사한다.
재개는 서명된 선택 HEAD의 원 checkpoint만 공식 복원하며 이미 확정한 prefix를 재적분하지 않는다.

각 HEAD의 새 domain HMAC은 intent/binding SHA, 원 storage HEAD, 직전 HEAD/proof SHA, 순서, initialize/advance/finalize를 묶는다.
선택 HEAD 전에0400 proof를 fsync하며 HEAD는 기존 storage의 원자 교체/디렉터리 fsync를 사용한다.
입력·현재 농장/자료/검토 권리는 intent 생성, 준비, 계산, proof/HEAD 게시, 조회 반환의 전후에 다시 확인한다.
HEAD 전 실패는 직전 확정 prefix, HEAD 후 실패는 새 확정 prefix에서 재개한다. 선택되지 않은 내용 주소 파일은 결과로 제시하지 않는다.
현재 권리는 여러 저장소에 대한 하나의 원자 snapshot이 아니며, 해당 호출의 전후 관측을 의미한다.

진행 bytes에는 원 context/UTC/source·intent/binding/HEAD/proof/root SHA, 확정 걸음/전체 걸음·행 수,
원 checkpoint/last_confirmed/hold 및 같은 UTC를 기록한다. `ready/yielded/completed/hold`를 구분한다.
실시간 HTTP 상태 API·실제 벽시계 최종 갱신 시각·프론트 구독을 구현했다는 주장은 하지 않는다.
계산 hold는 실패한 trial을 정상값으로 게시하지 않고 원 마지막 확정 상태와 실패 시각을 저장한다.

## 수용 조건

작은 실제 SCRAM 농장에서 정상 원 producer의 분할 계산/서명 HEAD/root·원108상태/UTC/관리 사건을 대사한다.
읽기 수치 호출0, 현재 계정/권리/source/review/파일 철회, 다른 model/tenant/source·HMAC/HEAD/페이지 변조,
같은 revision 충돌·잠금, 실제 fresh exec 재접속/재개와 원 prefix·현재 거부, 실제 정상/hold를 확인한다.
원 종료 코드·FD·PG/schema/role/passfile/임시 자료 정리, 원본/기동 미리보기 보존 및 WSL RSS 상한을 기록한다.
완료 checkbox는 이 증거를 확보한 후 갱신한다. 기존 전체166일 결과·수치 회귀는 불필요하게 재실행하지 않는다.
