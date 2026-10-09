# 저장 작물 연구 결과 조회 API v1

상태: [로컬 합성 조회 API 수용](../research/api-crop-replay-implementation.md),
집중 316개/실제 TLS·SCRAM. 기존 CLI `gpt-6.1-sol / xhigh` 세션에서 계약을
판단하며 재귀 CLI를 실행하지 않는다. 선행은 [불변 저장](crop-result-v1.md)이다.

## 조회와 조립

`GET /v1/crop-research-results/{result_id}`는 정확한 `crop-result-v1:<64 hex>`와
필수 query `scenario_id`, `scenario_revision`, `registration_sha256`, `crop_id`를
받는다. 식별자는 기존 ASCII 200자 규칙, digest는 소문자 64 hex다. query는
이 네 이름만 각 한 번 허용하며 본문/테넌트/모델 교체/새 계산은 받지 않는다.
인증 테넌트와 기존 농장 READ_SCOPES + `crop_result_read`를 요구한다.

`create_app(..., crop_result_store=...)`에는 같은 jobs/principal과 정확한
FarmAuthoringService의 CropResultStore만 전달한다. 기본 서비스 없음은 503이다.
표준 ApiRuntimeDependencies의 선택 `crop_result_store_factory`는 서버에서 만든
`farm_authoring_service`를 받아 같은 객체/JobStore에 묶인 저장소를 반환한다.
선택 factory와 `policy.crop_result_storage=true`는 함께 필요하다. factory가
명시적 프로필/고지/현재 권리 제공자/비밀 무결성 키를 보호하며 자동으로 만들지
않는다. 기존 API 조립의 기본 경로는 이 옵션 없이 계속 동작한다.

## 응답과 단위

200 응답 `CropResearchReplay`는 닫힌 typed 객체다. 불변 result ID/최초 저장 UTC,
study/revision, 같은 농장 등록/crop/batch/zone/농장·원천 hash, 입력/프로필/모델/
코드/solver/결과/저장 bytes/고지 hash와 계산 구간을 포함한다.
`storage_status=stored_unpublished_research`, `claim_scope=synthetic_crop_math_only`,
`scope=software_research_only`, `profile_applicability=unvalidated_for_registered_crop`,
`normalization=per_m2_floor`, `temporal_provenance=synthetic_research_program`,
`gates=not_assessed`를 항상 표시한다. 이는 승인 Run이나 실제 농장 예측이 아니다.

완료 sample은 저장한 UTC/6상태/LAI/탄소 누적/잔차와 계산 예산을 그대로 제공한다.
기관·buffer와 누적은 **mg_CH2O/m2_floor**, LAI는 **m2_leaf/m2_floor**, 필터 온도는
**degC**, 온도 적산은 **degC_day**다. 생과 kg·키·잎/과실 수·숙기·구매 자원·금액을
추가하지 않는다. 사건은 입력으로 선언한 기관 제거량과 전/후 상태이며 수확량이 아니다.
완료 시점은 요청한 output_times와 정확히 일치한다. 전체 결과 상한 20,000 sample/
event와 저장 packet 64 MiB를 유지한다. 별도 그래프/3D가 같은 result ID와 sample.at를 쓴다.

수치 `status=hold`도 유효 저장 자료면 200으로 읽되 완료 sample/event는 빈 목록이다.
고정 reason_code, 실패 solver 평가 시각/phase, 마지막 확인 sample과 실패 상태를
보존한다. 실패 상태의 음수/null은 진단이며 성장 장면의 정상 상태로 쓰지 않는다.
원문 reason/forcing ID/초기조건/권리 선언/프로필 원문/비밀 키·서명/테넌트·개인 농장
기록/비공개 source ID는 반환하지 않는다. 저장소는 현재 farm/source/program 권리와
HMAC를 검사하고, projection은 공개 타입/단위/해시·시간 연결만 확인한다.

## 오류와 검증

기존 ErrorEnvelope를 사용한다: 401 인증, 403 scope, 404 미저장/타 테넌트,
422 무효 query 또는 crop_research_hold(현재 권리/다른 농장·등록/무결성 불일치),
503 서비스/기타 store 실패. 모든 오류는 고정 문구이며 예외 세부를 출력하지 않는다.
기존 middleware의 no-store/보안 헤더와 Bearer 현재 유효성 검사를 적용한다.
조회는 저장 결과나 관문 판정을 바꾸지 않고 적분을 재실행하지 않는다.

수용: OpenAPI/스키마와 실제 stored sample의 단위/UTC/동일성, 변조·모델 혼합·
hold/권리 철회/현재 계정 경계, 기본 조립 호환/잘못된 factory 거부, 실제 TLS/SCRAM
전체 응답·재조회·정리. 합성 시험은 실제 CLI 런타임/독립 농장/G0–G4 수용이 아니다.
