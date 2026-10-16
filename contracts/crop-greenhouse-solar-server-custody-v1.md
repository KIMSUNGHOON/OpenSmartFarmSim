# 현재 일사 공동 계산의 서버 소유 이력 v1

선행: [현재 농장/자료 결속](crop-greenhouse-solar-farm-binding-v1.md),
[입력 증거](crop-greenhouse-solar-input-evidence-v1.md),
[분할 실행/UTC](crop-greenhouse-solar-time-v1.md),
[불변 저장](crop-greenhouse-solar-storage-v1.md).
원108상태/41연속·6사건 장부/15수지와 PAR/NIR/환기의 현재 상태 합성을 보존한다.
서버 내부 Python 경계다. DB 등록·API/자동 worker·같은 UTC3D·사용자 실행은 후속이다.

## 조립·호출

`SolarServerCustody(binding, directory, input_resolver=..., integrity_key=...)`는
정확한 `SolarFarmBinding`, 소유자 전용0700 POSIX root,32–4096byte 서버 키,
고정 version을 갖는 trusted resolver를 받는다. resolver는
`(tenant, source_sha256, evidence_sha256)`에서 `(input_directory, evidence_raw)`를
반환한다. 사용자 요청에 경로/키/resolver를 받지 않는다. 기존 등록 농장 authority
SCRAM/scopes/grant 감사를 요구하며 새 DB/role/service를 만들지 않는다.

`advance(tenant, request_raw, budget=1..128)`는 원 격자의 제한된 boundary를
계산한다. `inspect(tenant, request_raw)`는 확정 이력을 읽는다.
`page(tenant, request_raw, expected_progress_raw, kind, start=0, limit=None)`는
완료/hold의 불변 root에서64sample/8event 및2MiB 이하 페이지를 읽는다.
계산 중 prefix의 HTTP/3D 게시와 임대/취소 API는 이 계약의 범위가 아니다.
조회와 final root의 advance 재호출은 현재 권한을 검사하되 context/UTC 생성,
checkpoint 복원·solar/PAR/NIR/환기/RHS/적분/관리/CLI 실행을 하지 않는다.

계산 준비는 원 source와 고정 profile로 공식 context/UTC를 만들고 검증된 receipt의
전체 record(원 provenance 포함)와 canonical bytes를 대사한다. 초기 합성 평가와
checkpoint endpoint 검증은 새 경계 계산과 분리해 계수한다. 원 other forcing과
solar/outdoor 입력을 각각 보존한다.

## 서명·현재 권리·재개

tenant/study/revision의 새 identity domain 아래 원 요청 SHA·전체 농장 결속
(provenance/hash·판단 시각·미검증 품종 적용성 포함)·resolver/code/의존성/한도를
새 intent HMAC으로 서명한다. 같은 revision의 다른 요청은 conflict다.
새 version은 `joint-solar-server-custody-v1`, intent는
`joint-solar-server-intent-v1`, proof는 `joint-solar-server-head-v1`이다.
intent/proof/identity domain은 각각 `ossf-joint-solar-server-*-v1\0`로 구 판본과
분리한다. scope는 `synthetic_joint_solar_math_only`,
`rights_or_gate_approval=False`, `G0_G4=not_assessed`다.

기존 비차단 root/intent file lock, nofollow·소유자·정확한 모드/단일 링크,
용량/파일 수 한도를 사용한다. intent192KiB/proof8KiB/progress128KiB와 기존
storage 한도를 별도로 유지한다. 각 HEAD proof는 intent/binding SHA, 원 storage
HEAD, 직전 HEAD/proof SHA, sequence와 initialize/advance/finalize를 묶는다.
선택 HEAD 전에0400 proof를 fsync하고, HEAD는 기존 원자 교체/디렉터리 fsync로
게시한다. 현재 입력/농장/권리/review는 준비·계산·proof/HEAD 게시·조회 반환의
전후에 다시 검사한다. 여러 저장소에 대한 하나의 원자 snapshot을 뜻하지 않는다.

서명된 선택 HEAD의 원 checkpoint만 공식 복원한다. 확정된 걸음·사건을 다시
적분/적용하지 않는다. HEAD 전 실패는 직전 확정 prefix, HEAD 후 실패는 새 확정
prefix에서 재개한다. 선택되지 않은 내용 주소 파일은 결과로 제시하지 않는다.
진행 bytes는 source/context/UTC/provenance/intent/binding/HEAD/proof/root SHA,
확정/전체 걸음·행 수, checkpoint/last_confirmed/hold와 원 UTC를 포함한다.
ready/yielded/completed/hold를 구분하며 실패 trial은 정상값으로 게시하지 않는다.

## 수용

실제 SCRAM에서 정상·hold, 직접 원 producer와 모든 상태/장부/수지·UTC·사건/
checkpoint 동일성, 읽기/terminal retry 계산0, 별도 fresh exec 재개와 현재 철회를
확인한다. 원 경계 호출 수는 독립된 직접 producer 경로와 대사해 초기 평가와
복원 평가를 구분한다. 다른 authority/domain/tenant/source, 서명/HEAD/페이지
변조, 요청 충돌·잠금·한도·늦은 철회를 거부해야 한다.

HEAD 직전·직후 실제 소유 자식 SIGKILL에서 원 prefix 선택과 최종 원량을
확인한다. 원 종료 코드·FD/PG/schema/role/passfile 정리, 원본/두 미리보기/5root와
512MiB/PID·동시 합1GiB를 보존한다. 전체 작기·실제 농장/미래 예측/권리/G0–G4
승인을 합성 fixture에서 주장하지 않는다.
