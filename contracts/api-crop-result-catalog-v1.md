# 보호 저장 작물 연구 결과 목록 API v1

선행은 [metadata 목록](crop-result-catalog-v1.md)이다. 상위 U1의 API 자식이며 웹 목록/선택은 후속이다.
핵심 작성 파일5개: `backend/app/api_crop_result_catalog.py`, `backend/tests/test_api_crop_result_catalog.py`,
`backend/app/api.py`, `backend/tests/test_api_openapi.py`, 이 계약.
생성 OpenAPI snapshot과 수동 실제 DB/HTTPS 수용 harness·증거를 함께 보존한다.
기존 생장 API 조립/지연 import 호환 회귀와 실제 다수 목록에서 필요해진 metadata 모듈/시험의 비용 보완을 포함한다.
현재 query/runtime graph를 재사용하며 새 factory/DB role/queue를 추가하지 않는다.

## HTTP 계약

`GET /v1/crop-research-result-catalog`, operation `listCropResearchResults`.
기존 `READ_SCOPES` 전부와 Bearer 인증을 요구한다. tenant는 인증 주체에서만 가져온다.

필수 query: `kind=calculation_cycle_v1|harvest_v1`, `scenario_id`, `scenario_revision`,
`registration_sha256`, `crop_id`. 선택: `limit`(정수1–20, 기본10),
`before_recorded_at`(UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ`), `before_result_id`.
cursor 두 필드는 함께 주고 ID 판본은 kind와 일치해야 한다.
알 수 없는/중복 query·비정규 숫자·비어 있지 않은 GET body를 422로 거부한다.
SDK는 next_cursor를 그대로 전달하며 로컬 시각/offset으로 바꾸지 않는다.

200은 두 kind의 닫힌 응답 union이다. 생장 항목은 원 ID/저장 시각·study/판본·작기·
완료/hold·시점/사건 수, 수확은 원 ID/저장 시각·부모 ID·상태/행 수다.
목록은 `stored_research_metadata_only`, `selection_validation_required=true`,
`rights_or_gate_approval=false`를 유지한다. 빈 결과도200이며 전체 개수를 추정하지 않는다.
응답은 최대64KiB, `Cache-Control: no-store`와 목록/투영 코드 판본 header를 갖는다.
선택한 결과의 파일/원 수치·현재 권리는 기존 검증 query/API로 다시 확인한다.

401 인증 실패, 403 scope/주체 불일치, 422 요청 오류 또는 `crop_catalog_hold`,
503 kind/reader 미구성 또는 `crop_catalog_unavailable`이며 기존 ErrorEnvelope로 상세를 숨긴다.
미구성 기능도 인증부터 검사한다. 완료 여부를 꾸미거나 다른 판본/자료로 대체하지 않는다.

현재 목록 context 안에서 typed 투영·canonical bytes 직렬화를 마친 뒤 context의 등록/권리/서명
재검사를 통과해야 한다. 그 후 현재 인증 tenant/scope를 다시 확인하며 기존 middleware의
Bearer 재검사도 유지한다. 투영 뒤 철회·주체 변경·실패는 준비한200 bytes를 게시하지 않는다.

## 수용 기준

1. ASGI에서 두 kind·빈/마지막/동률 페이지, 닫힌 query와 typed 응답/크기·오류/주체 변경·
   투영 뒤 철회를 확인한다. schema는 기존 endpoint/operation/응답의 의미를 보존한다.
2. 별도 복원 SCRAM DB와 실제 인증 HTTPS의 원 생장/수확 metadata를 대사하고 기본/최대 페이지,
   실제 다수 행의 cursor 경계/중복·누락과 권리/계정/변조·미구성 거부를 검증한다.
   시험용 추가 결과는 소유 합성 입력의 정상 producer로 준비하고 원 보존 결과는 재서명하지 않는다.
   동률 시각 fixture를 따로 만들면 그 시험 범위와 원 저장 시각 대사를 구분한다.
3. 완료 응답을 끝까지 읽어 bytes/hash·시간을 기록한다. 기존30초 client 예산·64KiB 안의 실제 범위만
   수용하며 초과하면 원인과 수정 증거를 남긴다. 조회 단계의 RHS/파일 생성·게시·증명 발행은0이다.
4. 소유 DB/서버/FD·제어 파일/자원 정리와 원 입력/artifact·고정 producer/미리보기 보존을 확인한다.
5. 실제 제품 CLI·UI 목록/3D 선택·실시간 진행 연동·실제 자료/관문을 완료 처리하지 않는다.

로컬 수용 범위와 실패/수정 기록은 [구현 검증](../research/crop-result-catalog-api-implementation-20261009.md)에 둔다.
실제 생장21건/최대20건 페이지와 수확1건을 확인했다. 서로 다른20개 period/권리 시각이나
수확20건의 운영 용량을 이 수용으로 확대하지 않는다.
