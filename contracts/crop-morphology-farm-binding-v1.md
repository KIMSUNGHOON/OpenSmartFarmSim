# 형태 입력과 등록 농장·현재 권리 — v1

상태: [제어28·실제 SCRAM3/집중 회귀623 수용](../research/crop-morphology-farm-binding-20261022.md).
마이크로초 경계는 같은 scope 함수의 순수 제어, 실제 등록/current·철회/새 exec는 별도 SCRAM 검증이다.

선행: [형태 입력의 현재 출처 검토](crop-morphology-input-evidence-v1.md).
기존 FarmAuthoringService·authority SCRAM 로그인/권한 감사와 현재 crop read/write scopes를 사용한다.
기존 명시 crop_cycle_result_storage=True를 요구하며 새 표/역할·Run/결과를 생성하지 않는다.

`MorphologyFarmBinding(farms,input_authority,input_rights=...)`의 prepare/current는 tenant/request bytes와
서버가 읽은 원 program/source/evidence bytes를 받는다. 요청에 경로/키를 받지 않는다.
request≤128KiB, binding≤2MiB, 기존 program16MiB/source1MiB/evidence2MiB 상한이다.
current는 원 expected_binding_raw와 같아야 하고 write=False는 display 권리만, True/prepare는
calculation·display를 모두 현재 resolver에서 재검사한다. farm/입력/current review·scope/정책·code를 전후 확인한다.

닫힌 요청은 study_id/revision/farm/input/rights다. farm은 scenario_id/scenario_revision/registration_sha256/crop_id,
input은 source schema/program_id/program_sha256/source_sha256/evidence_sha256다.
rights는 별도 morphology-input-rights-v1/declaration_id/revision/input_source_sha256/available_at,
ownership_asserted/access/store/transform/use/display=True, redistribute=False다.
원 합성 프로그램의 재배포 선언과 농장 문서의 비공개 사용 선언은 다른 범위다.

등록 농장·작물/배치·zone/면적·원 registration/job/source binding을 대사한다.
SourceRecord/권리 available_at은 farm.decision_at 이전이어야 하고 input evidence의 decision도 그 값과 일치한다.
모델 기간은 초기 timeline.at부터 마지막 output UTC까지이며 crop occupancy/KST 재배 달력 안이어야 한다.
원점/기관 shoot ID와 모델/코드·provenance·입력/초기 상태/forcing/schedule·검토 지문을 보존한다.
normalization은 per_tracked_shoot다. 토지 면적으로 늘리거나 식물 수/수량을 추정하지 않는다.
scope=synthetic_morphology_input_binding_only, profile_applicability=unvalidated_for_registered_crop,
numerical_initial_state_validation=False/rights_or_gate_approval=False/G0_G4=not_assessed다.

미래 판단용 자료를 소급 발급하지 않는다. 현재 자료로 과거 모델 구간을 계산하는 합성 연구 검증은
명시적인 **현재 판단의 retrospective replay**로 구성하고, 과거 당시 예측 검증이라고 표시하지 않는다.
동일 bytes/각 현재 검사를 수용해도 서로 다른 저장소의 원자 snapshot이나 수치 producer의 서명을 증명하지 않는다.
후속 server custody가 계산/서명 게시 전후에 다시 확인한다.

수용: 실제 SCRAM 등록/prepare/read/write·새 exec의 같은 bytes와 현재 철회, 원 날짜/UTC·59단위/provenance와
1마이크로초 가용성·점유 경계, 다른 tenant/crop/기간/등록·원 bytes/서명/정책/코드/현재 권리·늦은 scope/등록 변경 거부다.
원 공개15파일·기존 DB 행/결과와6root, 계산/CLI/새 Run·결과 row0·FD/소유 PG/schema/role/passfile 정리를 대사한다.
실제 농장/품종/G0·수치/생산·추천 승인과 DB/API/제품 UI는 남는다.
