# Cycle 원 입력과 현재 등록 농장의 결합 — v1

상태: **구현 중**, `crop-cycle-farm-binding`, 2026-10-05 KST.
[제품 관문](../docs/PROJECT_SPEC.md), [농장 등록](farm-authoring-storage-v1.md),
[원 입력 reader](crop-cycle-input-stream-v1.md), [불변 저장 schema/명시 role](crop-cycle-storage-v1.md)를 따른다.
현재 Codex CLI `gpt-6.1-sol / xhigh`로 판단하며 같은 CLI 세션에서 재귀 실행하지 않는다.

## 저장 부모를 나누는 근거

기존 crop v1/v3 `_references`는 inline program의 segments에서 기간을 읽고 program SHA 권리를 대사한다.
긴 입력은 최대512MiB의 private POSIX pages와1MiB root다. 이를 요청/20MiB 이전 row에 복사하지 않는다.
닫힌 root 권리 선언을 실제 preflight한 입력/기간과 현재 농장/crop/floor/source binding에 연결하는
작은 경계가 필요하다. 이3파일은 module/test/이 계약이며 RHS/파일 게시/DB row를 만들지 않는다.
이어 서버가 실제 writer를 실행하고 서명한 진행 상태/완료 결과 → DB HMAC/atomicity를 검증한다.
`crop-cycle-result-storage`는 세 자식의 증거가 모두 있을 때만 수용한다.

## 신뢰된 서버 경계

`CycleFarmBinding(farms,growth_profile,cohort_profile,transport_profile,notice_raw,*,input_rights)`는
기존 정확한 FarmAuthoringService·authority SCRAM JobStore/전체 grant 감사와 새 explicit cycle flag를 요구한다.
farms/jobs/profile/provider/policy_version/연결/identity의 최초 고정 참조와 현재 코드/고지 hash를 매 호출 대사한다.
운영자가 설치한 input_rights callback은 `(tenant,declaration,input_root_sha256,intended_use)`를 받아
exact True일 때만 허용하며 명시 policy_version을 가진다. root 전용 선언을 이전 inline program 선언으로 읽지 않는다.
이 callback의 실제 정책 자료/승인은 외부 의존성이며 synthetic 시험 provider는 자료 승인 증거가 아니다.

`prepare(tenant,request_raw,reader)`는 계산 준비의 현재 권리, `current(tenant,request_raw,reader,
expected_binding_raw,*,write=False)`는 과거 결합/현재 권리의 재검사를 수행한다.
reader는 신뢰 서버가 root hash와 세 프로필로 실제 `open_input_packet`한 열린 exact InputPacket이다.
요청에서 filesystem path나 caller 계산 결과를 받지 않는다. 검증한 binding은 canonical UTF-8 bytes다.
읽기/RHS/authority 파일·별도 process의 소유권 격리는 후속 storage/API가 이 경계를 올바르게 사용해 증명한다.

## 닫힌 요청/선언

요청은128KiB 이하 canonical UTF-8 JSON이며 top key는 study_id/revision/farm/input/rights다.
farm은 scenario_id/scenario_revision/registration_sha256/crop_id이고 input은
schema_version=`crop-cycle-input-packet-v1`, root_sha256, program_id다.
identifier는 기존 crop Identifier 정책1..200자, hash는64자리 소문자 hex다.
권리 선언은 schema_version=`crop-cycle-input-rights-v1`, declaration_id/revision,
input_root_sha256/available_at, ownership_asserted/access/store/transform/use/display=true,
redistribute=false다. 누락/extra/null/잘못된 타입·중복 key/비 canonical bytes를 거부한다.
원 요청/입력/프로필/권리의 해석은 deterministic server가 검증한다.

reader의 root/program/version/profile/code/Python/period/plan과 원 root 파일 bytes를 대사한다.
현재 canonical root와 reader 내부 root의 일치·input preflight/블록 hash를 다시 검사한다.
reader 계약의 synthetic origin/256자 이하 원 block input_id 범위를 보존한다. 요청 identifier는1..200자다.
현재 농장 등록의 request SHA/job/source binding과 crop을 다시 읽고 입력 기간이 농장 달력/occupancy 안에 있는지 검사한다.
rights.available_at≤farm.decision_at이며 floor 면적 단위/zone/crop/batch는 원 농장 값이다.
관측된 profile_applicability는 `unvalidated_for_registered_crop`, normalization은 `per_m2_floor`다.
prepare/write는 research_calculation와 research_display, read는 research_display를 현재 provider에 확인한다.
callback 뒤 농장/source/scope를 다시 검사해 중간 철회를 검출한다.

binding은 version/scope/tenant_id/request/registration/input/rights_policy_version/binding_code_sha256의
닫힌 객체다. input은 root_sha256/calculation_sha256/program_id/period/plan/profile_sha256/normalization_sha256/
python_version이다. 최초 바이트를 수정하지 않으며 expected binding과 정확히 같아야 한다.
binding SHA는 crop 계산의 인증 서명이나 G0–G4 관문 증거가 아니다.

## 수용 기준

1. 실제 SCRAM 등록 농장/완료 원천의 현재 권리와 preflight 입력 root/기간/crop·zone/floor/batch를 대사한다.
2. canonical closed 요청/root/선언·동일 tenant/farm/crop/기간·availability·profile/code·open reader를 검사한다.
3. scopes·농장 원천·input provider 철회, 잘못된 callback 반환/선언 변경과 current expected binding 변조를 거부한다.
4. rights callback 중간 철회·단계별 재접속/별도 Python 결합 일치·입력 파일 변조를 확인한다.
5. RHS/advance/작물 row/Run0개와 원44개 hash·DB/role/schema/비밀번호/FD 정리를 확인한다.

계약/기존 provider 대사0.5–1시간+module0.5–1시간+실제 SCRAM/철회/파일/재시작·정리1시간의
**2–3집중시간**, 하루4시간/CI·자료 대기 제외 **10월5–6일 KST 잠정**이다.
후속 server execution/서명된 progress는3–5시간, DB custody는2–3시간의 잠정치며
기존 단일5–8시간을 세 자식 총7–11시간/10월5–8일 KST로 분해한다. 실제 수용 뒤 갱신한다.
실제 자료/국내 독립 측정0개·G0–G4 hold·예측/추천 게시 날짜 보류를 유지한다.
