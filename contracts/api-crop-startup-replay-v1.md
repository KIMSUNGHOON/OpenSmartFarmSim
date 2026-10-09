# 저장 시작 유보 모델의 페이지 조회 API — v1

상태: **합성 연구 API 로컬 수용; 원격 CI 수용은 별도**. 2026-10-05 KST.
구현 `7d4d310`의 [252개 고유 분할 검증/실제 HTTPS·SCRAM](../research/api-crop-startup-replay-implementation.md)과
[파일/응답·정리 증거](../research/artifacts/api-crop-startup-replay-reference-20261005.json)를 확인한다.
개발 선행은 [v3 farm custody](crop-result-v3.md)의 실제 SCRAM 수용이다.
현재 Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 CLI를 재귀 실행하지 않는다.
기존 [v2 조회](api-crop-coupled-replay-v1.md)와 저장 bytes/권한은 유지한다.

## 한 읽기 경로와 조립

`GET /v1/crop-startup-research-results/{result_id}`는 정확한
`crop-result-v3:<64 lowercase hex>` 및 네 필수 farm query
`scenario_id/scenario_revision/registration_sha256/crop_id`를 받는다.
추가 query는 sample_offset(0–512, 기본0), sample_limit(1–64, 기본64),
event_offset(0–128, 기본0), event_limit(1–8, 기본8)뿐이다.
각 query는 한 번만 허용하고 정수는 canonical ASCII decimal이다.
total을 넘는 offset은 422, 같은 offset은 빈 마지막 페이지다.
본문·새 program/계수·tenant 교체·계산/재적분/관문 게시를 받지 않는다.

페이지 전체 JSON은 2 MiB 이하이며 모든 페이지는 같은 result ID/등록 및
payload/result/artifact/raw·normalized input hash를 유지한다.
저장 순서·정확한 UTC를 그대로 읽고 결과를 축약하거나 미래 시점을 추가하지 않는다.
현재 READ scopes/farm/source/program display 권리와 HMAC를 다시 검사한다.
같은 FarmAuthoringService/JobStore/principal에 묶인 exact StartupCropResultStore와
새 optional factory, 명시 crop_startup_result_storage=true가 함께 필요하다.
flag/factory 불일치·다른 store/service는 기동 시 거부하며 기본 비활성은 503이다.

## 닫힌 공개 응답

`crop-startup-replay-v1` 응답은 study/revision·첫 DB UTC, farm/crop/batch/zone/면적,
등록/farm/source hash·기간/status/step count, profile3개/notice·정책2개/code9개 및
artifact/dependency/storage/binding 코드 hash, solver/manifest 판본을 제공한다.
convergence=`not_evaluated_for_this_program`와 startup 전환/수지 규칙을 유지하며
작기 수렴·실제 품종 적용·독립 검증을 완료한 것으로 바꾸지 않는다.
tenant/key/HMAC·원 program/forcing/S/W1/RGR·권리 선언/profile/비공개 source 원문은 공개하지 않는다.
고정 연구 설명에는 명시적 착과·진입 질량, 빈 sink의 buffer 유보, 초기 전환과
미세 구획 수치 오차의 한계를 포함한다.

`stored_unpublished_research`, `synthetic_crop_math_only`, `software_research_only`,
`unvalidated_for_registered_crop`, `per_m2_floor`, `synthetic_research_program`,
`gates=not_assessed`를 유지한다. 승인 Run·생과 kg·수확/가격/마진·추천은 제공하지 않는다.

sample은 v2의 기관/온도·정확한 50 N/C·LAI/총 과실 C와 탄소·개수 수지를 보존한다.
누적은 기존12개에 requested/realized/deferred fruit carbohydrate와 fruit growth
respiration 4개를 더한 16개다. startup_diagnostics의 requested/growth_respiration
각 residual/budget 4개를 원값/단위로 제공한다. mg_CH2O/m2_floor와
fruits_equivalent/m2_floor를 실제 생과중·과실 개수로 환산하지 않는다.

event의 정확한 UTC·전/후 상태·기관/같은 구획 N/C 제거를 보존하고 input ID는 숨긴다.
hold의 고정 reason code·solver UTC/phase·last_confirmed를 별도 진단으로 제공한다.
소수 초 hold도 datetime으로 비교하고 확인된 과거 sample/event만 조회한다.
실패 trial/last_confirmed를 정상 관리 후 sample이나 장면 시점으로 추가하지 않는다.
페이지의 offset/limit/total/next_offset은 원 저장 count와 일치해야 한다.

## 작은 구현 구획과 수용 기준

새 API 모듈/집중 시험과 기존 api.py·api_runtime.py의 optional store/factory,
고정 OpenAPI·권한·기본 조립 시험만 연결한다. 필요 시 실제 TLS 시험을 별도 파일로 둔다.
새 계산 접수·큐/작업자·설비·UI 변경은 이 API의 개발 선행이 아니다.

1. 닫힌 OpenAPI/typed 응답·UTC/단위·50구획·16누적/4진단을 저장 원값과 대사한다.
2. 512 sample/최대 event의 모든 페이지를 같은 ID/hash/순서로 누락/중복 없이 읽는다.
   빈 초기/전량 제거 후 재유입·완료/hold/빈 과거와 소수 초 실패 경계를 확인한다.
   적분을 실패 함수로 교체해 GET의 재적분 부재를 검증한다.
3. 중복/잘못된 query/body·판본/farm/tenant 혼합·현재 권리/scope 철회 및
   DB/HMAC/manifest/단위/수지 변조는 닫힌 ErrorEnvelope로 거부한다.
   기존 인증/Bearer/no-store·보안 헤더와 기본/다른 factory 조립을 유지한다.
4. 실제 표준 HTTPS/Bearer·SCRAM에서 최대 sample/event 페이지의 **전체 본문을
   30초 안에 수신**하고 같은 저장 값/재시작/현재 권리·DB/password 정리를 확인한다.
   artifact reader의 로컬 시간이나 ASGI 검증으로 이를 대신하지 않는다.
5. 실제 파일/시험/응답 hash와 미수용 사항을 기록한 뒤 API child만 체크한다.
   parent인 새 저장→같은 UTC 표/그래프/50구획 성장 3D는 실제 브라우저 수용 뒤 체크한다.

사용자 산출물은 페이지 JSON·원값 대사와 HTTPS 영수증이다. 새 API47개를 포함한
252개 고유 시험을 분할 수용했으며 실제 HTTPS19개 전체 본문은 최대14.248425초/
700,084 bytes였다. API는 10월5일 KST 로컬 완료다. 다음은
[같은 result ID/UTC 성장 3D 계약](web-crop-startup-replay-v1.md)의 decoder/순차 페이지 결합,
그 뒤 장면/표/그래프·실제 브라우저 수용이다. 국내 독립 자료0건/actual forcing·Run0개,
전체 작기·생과 환산·자원/경제·G0–G4 수용과 실제 예측/추천 날짜는 별도다.
