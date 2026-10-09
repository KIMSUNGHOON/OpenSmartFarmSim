# 작물·기후의 현재 농장·자료 권리 결속 v1

선행은 [새 원 입력 검증](crop-climate-joint-input-evidence-v1.md)과 [불변 공동 저장](crop-climate-joint-storage-v1.md)이다.
원121상태 CalculationContext로 위장하지 않는다. 현재 입력 authority와 등록 farm/source 권리의 결속만 수용한다.
서버 서명 실행/DB 결과 등록/API/3D·실시간 U3는 후속이며 실제 G0–G4를 승인하지 않는다.

## 공개 경계

`JointFarmBinding(farms, input_authority, input_rights=...)`는 정확한 기존 `FarmAuthoringService`,
새 `JointInputEvidenceAuthority`, 현재 자료 권리 resolver를 받는다. 기존 authority SCRAM JobStore,
전체 grant 감사·명시 `crop_cycle_result_storage=True`와 현재 read/write scopes를 요구한다.
별도 DB schema/role/service를 만들지 않으며 기존 농장 등록을 읽을 뿐 작물 결과/Run을 생성하지 않는다.

`prepare(tenant, request_raw, directory, evidence_raw)`와
`current(tenant, request_raw, directory, evidence_raw, expected_binding_raw, write=False)`를 제공한다.
directory·HMAC 키·evidence bytes는 신뢰한 서버 조립이 제공하며 사용자 요청의 임의 경로를 받지 않는다.
원본과 검토를 전후 검증한 서명 evidence에서 입력을 읽는다. fresh 조회에 Context/Binding 생성·RHS·적분·사건·복원은 없다.
발급 초기 RHS1회는 선행 입력 검증에서 수행한 별도 사실이다.

## 닫힌 요청과 등록

canonical UTF-8 JSON128KiB 요청의 top key는 `study_id, revision, farm, input, rights`다.
farm은 기존 `scenario_id, scenario_revision, registration_sha256, crop_id`다.
input은 `schema_version=joint-crop-climate-input-source-v1, program_id, source_sha256, context_sha256,
time_binding_sha256, evidence_sha256`이며4개 SHA는 신뢰한 caller의 원 저장 값이다.
program_id는 원 scenario input_id와 정확히 일치하고 프로젝트 identifier 규칙(ASCII 최대200자)을 따른다.

rights는 `schema_version=joint-crop-climate-input-rights-v1, declaration_id, revision, input_source_sha256,
available_at, redistribute, ownership_asserted, access, store, transform, use, display`다.
6개 grant는 exact True, redistribute는 exact False이며 root 대신 새 원 source SHA에 결속한다.
선언 자체는 권리의 증거가 아니며 신뢰한 현재 resolver가 실제 승인 여부를 다시 판단해야 한다.
write는 research_calculation+research_display, read는 research_display만 exact True를 요구한다.

기존 `FarmAuthoringService`와 등록/availability/점유 기간의 정책을 유지한다. 원 `CycleFarmBinding._registration`은
초 단위 UTC만 받으므로 함수 객체를 재사용하지 않는다. 새 binding의6자리 UTC를 정밀도 손실 없이 비교한다.
등록 tenant/farm revision/job/hash·source binding,
crop/batch/zone/floor·KST 재배일 및 crop occupancy와 원 UTC 구간을 대사한다.
`available_at <= decision_at`을 보존하고 profile_applicability는 `unvalidated_for_registered_crop`다.
등록 품종 의도를 실측/검증된 품종으로 표시하지 않는다. 기존 입력 schema/parser/authority는 재사용하지 않는다.

권리 resolver를 두 번 관측하고 입력/current review·등록·scope를 반환 전에 다시 검사한다.
입력 원본·명시 검토자/결정/증거 ID와 model/profile/code/environment·UTC SHA를 canonical binding에 결속한다.
서비스/authority/provider/정책/DB identity·현재 코드의 고정 참조를 검사하며 current는 원 expected bytes와 정확히 같아야 한다.
이것은 여러 독립 저장소를 하나의 원자 snapshot으로 잠그는 증명이 아니다. 후속 custody는 계산/서명 게시 전후에 다시 검사한다.

## 수용

실제 SCRAM 등록 농장의 정상 prepare/current/read/write와 원량·마이크로초 UTC·crop/batch/zone/권리·review를 대사한다.
종료1마이크로초 초과는 반올림/절단해 허용하지 않는다.
현재 입력 검사2회/권리 관측2회, 계산/초기 context 생성/새 작물 row/Run0회를 확인한다.
다른 tenant/기간/crop/등록/source/model/time/evidence·권리/검토 철회·scope/provider/source/원 bytes/설정/서명/선언 변경을 거부한다.
현재 DB에 새 서비스로 재접속하고 별도 프로세스에서 같은 binding bytes 및 현재 거부를 확인한다.
fresh exec와 fork를 구분하고 원본/FD/실제 종료/PG·schema·role·passfile 정리와 WSL 자원을 기록한다.
