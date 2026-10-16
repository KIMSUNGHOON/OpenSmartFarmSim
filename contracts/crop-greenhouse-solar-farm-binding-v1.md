# 일사 입력의 현재 농장·자료 권리 결속 v1

선행: [일사 입력 증거](crop-greenhouse-solar-input-evidence-v1.md),
[불변 일사 계산 파일](crop-greenhouse-solar-storage-v1.md), 기존 등록 농장.
현재 108상태/41장부 context와 원 UTC를 등록 의도에 묶는 소프트웨어 계약이다.

## 경계

`SolarFarmBinding(farms, input_authority, input_rights=...)`는 정확한 기존
`FarmAuthoringService`, 새 `SolarInputEvidenceAuthority`, 현재 자료 권리 resolver를
받는다. 기존 authority SCRAM 로그인·전체 grant 감사와 명시
`crop_cycle_result_storage=True`, 현재 read/write scopes를 요구한다.
새 schema/role/service/Run/작물 결과를 생성하지 않는다.

`prepare(tenant, request_raw, directory, evidence_raw)`와
`current(tenant, request_raw, directory, evidence_raw, expected_binding_raw, write=False)`를
제공한다. 경로·키·evidence는 신뢰한 서버 조립이 공급한다. 요청에 임의 경로를
받지 않는다. canonical UTF-8 JSON 요청과 반환값의 상한은 각각 128KiB다.

top keys는 `study_id, revision, farm, input, rights`다. farm은 기존
`scenario_id, scenario_revision, registration_sha256, crop_id`다. input은
`schema_version=joint-solar-input-source-v1, program_id, source_sha256,
context_sha256, time_binding_sha256, evidence_sha256`다. ID는 기존 ASCII 200자
한도, 네 hash는 원 SHA256이며 program ID는 검증된 scenario input ID와 일치한다.

rights는 `schema_version=joint-solar-input-rights-v1, declaration_id, revision,
input_source_sha256, available_at, redistribute, ownership_asserted, access, store,
transform, use, display`다. 여섯 grant는 exact True, redistribute는 exact False다.
이 사용자 선언의 재배포 금지와 원 SourceRecord의 합성 작성자 선언 권리는
서로 다른 범위다. 현재 resolver는 source SHA에 대해 write의
`research_calculation, research_display`, read의 `research_display`를 exact True로
판단해야 한다. 선언만으로 실제 권리/G0가 승인되지 않는다.

## 등록·시각·현재성

등록 tenant/farm revision/job/hash·source binding·crop/batch/zone/floor 면적을
현재 농장과 대사한다. 원 마이크로초 UTC 구간은 crop occupancy와 KST 재배일
구간 안에 있어야 한다. 종료일 다음 자정이 재배일 구간의 끝이다.
권리 선언과 **원 SourceRecord 각각의 `available_at <= farm.decision_at`**를
검사한다. 수집 시각과 자료 가용 시각을 구분하며 1마이크로초 초과도 거부한다.
합성 가정의 미래 시뮬레이션 시각은 실제 미래 관측 자료라는 뜻이 아니다.

검증된 전체 provenance와 그 canonical SHA, source/context/UTC/evidence/초기 상태
SHA·현재 review·원 41장부 model/profile/code identity를 반환값에 보존한다.
등록 판단 시각도 명시한다. profile applicability는
`unvalidated_for_registered_crop`, scope는 `synthetic_joint_solar_math_only`,
version은 `joint-solar-farm-binding-v1`, `G0_G4=not_assessed`,
`rights_or_gate_approval=False`다. 등록 품종의 실제 생장 적합성을 승인하지 않는다.

권리 관측 두 번과 입력/current review·등록·scope 재검사를 반환 전에 수행한다.
resolver의 선언 변조, authority/provider/정책/DB identity/code 의존 변경을 거부한다.
current는 원 expected bytes와 같아야 한다. 서로 다른 저장소의 원자 snapshot을
증명하는 계약은 아니므로 후속 custody가 계산·서명 게시 전후에 다시 검사한다.
구 22/25장부 source/authority/rights/binding 판본과 혼합하지 않는다.

## 수용

실제 SCRAM prepare/current/read/write, 별도 fresh exec의 같은 bytes와 현재 철회,
microsecond UTC/가용 시각/점유 구간, 원 provenance/hash·crop/batch/zone/면적을
확인한다. 다른 tenant/crop/기간/등록/source/context/time/evidence/판본, 현재 권리·검토
철회, 늦은 scope/source/bytes/선언 변경, 실제 등록 DB 변조와 grant 변경을 거부한다.
context/UTC 생성·solar/PAR/NIR/환기/RHS·적분·관리·복원·CLI와 새 Run/작물 row는
prepare/current/fresh에서 0회다. 원 결과/5root/FD/소유 PG·schema·role·passfile 정리와
WSL 512MiB/PID·동시 합 1GiB를 확인한다.

후속은 서명 custody → 결과 DB 등록/현재 조회 → API/자동 worker → 같은 UTC3D와
사용자 정상/보류/취소 수용이다. 실제 자료/독립 검증/생산·경제·추천 관문은 별도다.
