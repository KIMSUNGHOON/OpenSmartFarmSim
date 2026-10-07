# 새 계산 판본의 현재 등록 농장·권한 결속

2026-10-07 KST. 구현 전 고정한 계약이다. 첫 authority 자식은
[로컬 소프트웨어 수용](../research/crop-cycle-calculation-farm-authority-implementation-20261007.md)을 완료했다.
선행은 [계산 문맥](crop-cycle-calculation-context-v1.md),
[불변 artifact](crop-cycle-calculation-artifact-v1.md), [원 농장 결속](crop-cycle-farm-binding-v1.md)의 수용이다.
현재 작업 `crop-cycle-calculation-farm-binding`은 아래 세 자식의 실제 수용 뒤에만 완료한다.

## 분해 근거와 순서

현재 `CycleFarmBinding._input`은 exact `InputPacket`, `CycleServerCustody`는 exact 원 binding과
원 reader/engine, `CycleCropResultStore`는 exact 원 custody를 요구한다.
DB schema는 `crop-cycle-result-v1` ID·payload와 `crop-cycle-artifact-v1` ref를 SQL로 고정한다.
새 계산 문맥이나 artifact의 판본만 바꾸거나 원 token/type으로 위장하면 이 경계를 우회한다.
따라서 현재 농장권한만 수용한 결과를 DB 저장/서명된 실행으로 표시하지 않는다.
기존 원55 source/입력/spec/과거 결과를 보존하며 다음 순서로 진행한다.

1. `crop-cycle-calculation-farm-authority`: 새 context/서버 입력 authority와 현재 등록/권한의 결속.
2. `crop-cycle-calculation-server-custody`: 그 결속을 실제 계산/HEAD·서명된 이력의 전후에 적용.
3. `crop-cycle-calculation-db-custody`: 새 판본 이력의 실제 DB HMAC/참조/원자 게시·재조회.

서버/DB 자식은 착수 시 각3–4 core파일·판본/예산/이전 자료 공존과 수용 절차를 별도로 고정한다.
schema/role 변경은 실제 새 판본 게시에 필요한 SQL/권한 대조를 근거로 제한한다.
별도 queue/service·운영 기반 확장이나 출처 없는 계수/생과 환산은 이 작업에 포함하지 않는다.

## 첫 자식: 농장 authority

첫 구현 core는3개다.

1. `backend/app/crop_cycle_calculation_farm_binding.py`
2. `backend/tests/test_crop_cycle_calculation_farm_binding.py`
3. 이 계약.

공개 API는 다음과 같다.

```python
CalculationFarmBinding(farms, input_authority, *, input_rights)
service.prepare(tenant, request_raw, context)
service.current(tenant, request_raw, context, expected_binding_raw, *, write=False)
```

정확한 기존 `FarmAuthoringService`와 authority SCRAM JobStore·전체 grant 감사,
명시 `crop_cycle_result_storage=True`를 요구한다. 기존 등록을 읽을 뿐 새 작물 row/Run을 만들지 않는다.
`input_authority`는 정확한 서버 `InputEvidenceAuthority`다. 새 context의 발행 authority 객체와
동일해야 하며 issuer/key/고지/프로필·정책/서비스·연결/identity의 고정 참조·소스 SHA를 재확인한다.
다른 키로 임의 발행한 proof나 조회 타입/원 reader는 계산 결속에 허용하지 않는다.
caller의 context는 빌리며 정상 반환/권한 거부만으로 healthy context를 닫지 않는다.
현재 입력 불일치는 context 자체의 `recheck` 실패 정리를 따른다.

요청과 권리 선언은 원 닫힌 schema/128KiB·canonical UTF-8·기간/availability 정책을 보존한다.
원 `_request`/`_registration` helper를 명시적으로 재사용하고 원 소스 SHA를 dependency에 결속한다.
실제 입력은 공식 factory가 검증한 새 context의 root/program/plan·단위/프로필/정규화/Python과
현재 증명/모든 bytes를 진입/반환 경계에서 확인한다. 최초 parser/preflight/prepare를 반복하지 않는다.
input에는 원8개 필드와 닫힌 `input_validation`8개를 추가한다:
`context_sha256/evidence_sha256/validated_context_sha256/engine_version/input_evidence_version/`
`calculation_code_sha256/input_evidence_code_sha256/input_evidence_dependency_sha256`.
이 provenance는 농장 계산 출처의 인증 서명이나 자료/G0 승인 자체가 아니다.

현재 등록의 job/SHA/source binding·tenant/crop/zone/floor/batch·기간/occupancy와
`available_at <= decision_at`을 대사한다. write는 research_calculation+research_display,
read는 research_display만 exact True로 허용한다. 권리 provider를 두 번 관측하고 선언 불변을 대사해
첫 callback 뒤의 철회를 재확인한다. 두 관측 뒤 입력·등록·scope를 다시 검사한다.
이는 여러 외부 정책과 동시 변경을 원자적으로 잠근다는 주장이 아니다. 계산/게시 전후와
DB 원자 거래의 추가 검사는 뒤의 자식에서 수용한다.

binding은 `crop-cycle-verified-farm-binding-v1`/`synthetic_crop_math_only`의 canonical bytes다.
원8개 top key에 `binding_dependency_sha256`을 추가하고 module/helper/context/evidence source를 고정한다.
`current`는 expected bytes와 정확히 같아야 한다. 과거 원 binding을 재발급하지 않는다.

## 첫 자식 수용 기준

1. 실제 SCRAM 등록 농장과 새 공식 context/proof·root/기간/crop/zone/floor/batch를 대사한다.
   RHS/advance/새 작물 row/Run은0개이고 DB 등록의 기존 bytes를 보존한다.
2. prepare/read/write의 정상 current bytes와 두 입력 검사·두 권리 관측, parser/prepare 재호출0을 계측한다.
3. raw/closed schema·다른 tenant/등록/crop/기간/availability·wrong authority·원/조회/닫힌 타입·
   key/issuer/고지/profile/code/policy/expected binding·root/blob/mode/symlink를 거부한다.
4. 실제 callback 중 권리/원천/scope/등록/입력·선언 변경을 거부하고 read 권리와 write 권리를 구분한다.
5. 새 서비스 재접속·별도 Python 프로세스의 같은 binding bytes, FD/cache·DB/schema/role/passfile/PG 정리를 확인한다.
   fork 기반 실제 프로세스를 쓰면 fresh exec와 구분해 기록한다.
6. 집중/실제 SCRAM·소스/CLI·수용 영수증/검토·문서 링크가 존재한 뒤 이 authority 자식만 체크한다.

산출물은 현재 결속의 원량/권한·거부/정리 보고서다. 첫 자식의 착수 분해는
원150줄/helper 재사용·새 입력 검사1시간 내외, 실제 SCRAM 검증·수정/정리1–2시간,
**총1–3집중시간/10월7–8일 KST 잠정**이다. 기존 원 결속54개 분할·정상5.56/5.82초와
새 계산/저장158개/151.23초가 근거다. 서버/DB 자식과CI·전체166일·외부 자료 시간은 포함하지 않는다.
실제 품종 입력/국내 독립 자료0건·G0–G4 `not_assessed`, 생산 예측·추천 보류를 유지한다.

첫 자식은10월7일에 실제 SCRAM 고유12개를 분할 수용했다. 12개/242.84초 뒤 조회 타입 거부를
추가한 해당1개/21.46초를 다시 통과했으며 제품 소스는 동일하다. fork 후 새 서비스/현재 DB 결속,
RHS/새 작물 row/Run0·세 번의 PG/역할/비밀 정리를 확인했다. fresh exec·서버 서명·DB 게시는 후속이다.
