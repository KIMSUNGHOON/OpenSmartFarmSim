# 저장 cycle 결과의 원 시점 조회 API — v1 후보

상태: **projection/route/runtime 로컬 소프트웨어 수용**, 2026-10-06 KST.
[최종 runtime/API 수용](../research/api-crop-cycle-runtime-implementation.md)은 원25시간 전체
HTTPS11응답·최대15.839875초/64,785bytes·원27시점/5사건·재시작/RHS0/정리를 확인했다.
아래 최초 예상은 이 실제 수용으로 대체하며 hosted CI·화면/실제3D 수용은 별도다.
작업 `api-crop-cycle-pages`. [DB 게시 계약](crop-cycle-db-custody-v1.md),
[불변 파일](crop-cycle-artifact-v1.md), [기존 startup 공개 형식](api-crop-startup-replay-v1.md)을 따른다.
현재 Codex CLI `gpt-6.1-sol / xhigh`에서 판단했다. 최초13:06:32.226Z 기록에 이어
실제14:26:49.152Z turn_context 원 line SHA
`793bb59cb62be2a7b9061570b6b52c6140fd7a6f306af549e1cf64cd3395e8d8`에서
실제 저장 형식과 다시 대조했다. 재귀 CLI0회다.
서버 저장의 현재 참조·권리 대사를 유지하고 긴 결과를 한 HTTP 응답에 모으지 않는다.

## 요청과 한 읽기 경로

`GET /v1/crop-cycle-research-results/{result_id}`는 `crop-cycle-result-v1:<64 lowercase hex>`와
필수 farm query `scenario_id/scenario_revision/registration_sha256/crop_id`를 받는다.
`view`는 `summary`(기본)/`samples`/`events`다. summary는 offset/limit를 받지 않는다.
samples/events는 canonical ASCII 정수 offset(기본0)과 limit(기본 각각64/8)을 받으며
상한은 각각64/8이다. offset은 저장 total 이하, total과 같으면 빈 마지막 페이지다.
알 수 없는·중복 query와 본문, tenant 교체·파일 경로·새 program/계수·계산 요청은 거부한다.

한 요청은 **현재 권리가 확인되는 한 서버 읽기 context**에서 원 DB packet·선택된
서명 HEAD와 필요한 summary 또는 page를 대사하고 공개 DTO를 만든다.
DTO/전체 bytes를 만든 뒤 현재 farm/source/input·principal/flag/grants와 선택 progress를
다시 확인한다. get와page를 별도 service open 두 번으로 조립하지 않는다.
RHS/advance/재적분0회이며 임의 보간·미래 시점을 생성하지 않는다.

exact `CycleCropResultStore`와 동일 JobStore/FarmAuthoringService/principal, 명시 flag 및
optional factory가 필요하다. 다른 객체·flag/factory 불일치는 기동 시 거부한다.
기본 비활성은503이며 기존 startup API의 기본 권한·bytes를 보존한다.
새 worker·queue·schema/role 설치는 이 조회 경로의 선행이 아니다.

인증 실패401, 요청 권한 거부403, 같은 tenant의 없는 결과404, 잘못된 요청/작물 근거 보류422,
기본 비활성·운영 서비스 오류503을 따른다. live DB grant audit의 `RolePolicyHold`는
작물 수치 hold와 다른 운영 설정 오류이며 고정503으로 거부한다. 현재 권리 오류나 운영 오류에서
과거 payload를 반환하지 않는다. 최초 실제 TLS 시험의422 기대/503 관측과 자원 정리는
[별도 실패 증거](../research/artifacts/crop-cycle-api-runtime-tls-hold-20261006.json)에 남겼다.

## 공개 형식과 정보 경계

응답 판본은 `crop-cycle-replay-v1`이다. 닫힌 top-level은
schema_version/result_id/recorded_at/study_id/revision/farm/reference/summary/page다.
DB 최초 recorded_at과 원 UTC를 보존한다. summary view는 page=null,
page view는 summary=null이며 서로 다른 ID/참조를 합치지 않는다.

reference는 원 artifact/header/input/calculation/context/binding/selected HEAD/proof/payload의
hash, 저장·서버·schema/dependency/notice의 코드 hash, 등록 farm/source binding hash와
batch/zone/면적·per_m2_floor·profile 적용성, 원 period/status/steps/planned_steps/counts/commit 및
storage bytes/file count를 제공한다. 현재 정책의 판본은 노출할 수 있으나 선언 원문은 숨긴다.
`stored_unpublished_research`, `synthetic_crop_math_only`, `software_research_only`,
`unvalidated_for_registered_crop`, `synthetic_research_program`, `gates=not_assessed`를 유지한다.
tenant·HMAC/key·내부 job ID·파일 경로·원 forcing/초기 입력/권리 선언·계수/profile 원문을 내보내지 않는다.

공개 reference의 출처와 닫힌 필드는 다음과 같다. 이름은 새 cycle 판본에만 적용한다.

| 닫힌 필드 | 실제 출처·대사 |
| --- | --- |
| storage_status/claim_scope/scope/gates/temporal_provenance | packet의 저장·claim, 원 engine scope, 위 고정 연구 표시 |
| batch_id/zone_id/floor_area/farm_sha256/source_binding_sha256/normalization/profile_applicability | 현재 binding.registration의 같은 crop/batch/zone·원 면적 문자열/단위·hash |
| start_utc/end_utc | binding.input.period의 원 start/end |
| artifact_ref/artifact_sha256/header_sha256/input_root_sha256/calculation_sha256/context_sha256/binding_sha256/intent_sha256/head_sha256/proof_sha256/payload_sha256 | 원 packet/progress/input과 실제 row bytes의 대응 hash; 선택된 journal progress도 전체 bytes가 같아야 함 |
| storage_code_sha256/server_custody_code_sha256/schema_code_sha256/server_dependency_sha256/binding_code_sha256/notice_sha256 | 실제 고정 packet/code/binding/policies; server_dependency_sha256는 단일 digest가 아니라 artifact/farm_binding/input_stream/execution/directory_helper/file_helper의 닫힌6개 digest map |
| input_rights_version/resolver_version | packet.policies의 고정 판본 이름; 선언 원문/사용자 개인정보 제외 |
| status/steps/planned_steps/sample_count/event_count/commit_count/storage_bytes/file_count | packet.artifact와 같은 terminal progress; completed의 steps=planned_steps, 엄격한 정수·원 수용 상한 |

farm은 원 요청의 닫힌4개 필드다. reference의 sample/event count와 offset/total은
최대131,072이며 기존 short API의512/128 한도를 상속하지 않는다. planned/actual steps는
원 cycle의최대40,000,000을 따르되 공개 API가 그 부하나 전체 작기를 수용했다고 표시하지 않는다.

summary의 닫힌 status/manifest/hold는 원 terminal 증거에서 선택한다.
실제 writer._summary는 status/steps/hold/last_confirmed 등의 commit metadata이며 manifest를
저장하지 않는다. manifest는 검증된 원 header/context.manifest에서 읽어야 한다.
DB summary의 최초 누락은 원 context.manifest를 함께 반환하도록 수정했고,
실제 정상/hold·요약 중 권리 철회 검증까지 [저장 수용](../research/crop-cycle-db-custody-implementation.md)으로 확인했다.
manifest는 cycle의 원 엔진/물리 프로그램/율 모델 판본, input/calculation/grid hash,
planned_steps/boundary_count/grid page size, 실행3개/물리 코드9개/profile3개 hash,
policy/allocation policy, solver/실제 Python/time/temperature-sum 규칙을 대사한다.
전체 작기 수렴이나 품종 검증을 완료했다고 표시하지 않는다.
hold는 고정 reason code·정확한 solver UTC/phase·last_confirmed를 보존한다.
실패 trial/확인 과거를 정상 sample 또는 장면 시점에 추가하지 않는다.

page의 닫힌 kind/offset/limit/next_offset/total/records는 원 reader 순서와 count를 따른다.
reader의 start/next를 offset/next_offset으로 옮기며 마지막 next=total만 null로 표시한다.
원 byte budget 때문에 limit보다 적은 record가 나올 수 있으므로, nonempty page는
1≤len(records)≤min(limit,total-offset), next=offset+len(records), 마지막 빈 page만 offset=total이다.
page를 검증할 때도 같은 문맥의 원 terminal metadata를 확인해 hold 이후 sample/실패 trial을
거부한다. page view에 summary를 복제하거나 다른 읽기 context를 열지 않는다.
sample은 기존 startup의 기관·온도/50 N·50 C·LAI·16누적량/수지/diagnostics를 그대로 제공한다.
event는 UTC·before/after/removed만 제공하고 원 input ID는 숨긴다.
fruits_equivalent/m2_floor와 mg_CH2O/m2_floor를 생과 kg·실제 과실 개수로 환산하지 않는다.
게시된 reference가 바뀌거나 부분/혼합 결과이면 hold다.

## 다음 한 단계의 수용 기준

API는 `projection` → `route` → `runtime`의 작은 자식으로 구현한다.
최초 판본의 투영 module/시험/이 계약3파일에서 원량과 닫힌 형식을 먼저 수용한다.
route는 module/api.py/route 시험/기존 OpenAPI 시험/기계 snapshot의5파일,
runtime은 api_runtime.py/조립 시험/실제 TLS 시험의3파일이다.
현재 test_api_openapi.py의 정확한 전체 route 목록·기계 snapshot 동일성 검사가
필수 갱신 범위이므로 한5파일 작업에 묶지 않는다. 자세한 선행·수용은 [todo](../tasks/todo.md)를 따른다.
이 분해는 실제15:22:59.870Z의 같은 exact CLI turn_context 원 line SHA
`64d6817d930e89560e9115aed2df48cbe9c1e0bdaeb18f5cc358e10ccbd73a78`에서 판단했다.

1. 닫힌 DTO와 실제 저장 packet/summary/page의 ID/hash/UTC/모든 원량을 대사한다.
   잘못된 타입·nonfinite·추가 필드·잘못된 page/total·혼합 참조·미래 시점을 거부한다.
2. 실제 Bearer/TLS/SCRAM 경로에서 summary와 순차 sample/event 전체 본문을 받는다.
   각 응답은 **30초·2MiB 이하**, 유한 페이지이며 독립 원 계산과 같고 GET RHS0회다.
3. 읽기/DTO 생성 중 권리 철회·flag/grant drift·다른 tenant/farm/root/key·변조/없는 참조와
   numerical hold의 확인 과거/빈 페이지를 검증한다. 권리 오류에 stale payload를 반환하지 않는다.
4. 원 기본 비활성·기동 조립·동일 principal/store, 인증과 OpenAPI를 확인하고 기존 startup을 보존한다.
   실제 TLS/DB/roles/password/FD/lock/temp와 순차 자식 RSS 정리를 기록한다.
5. 수용 후 API child만 완료로 표시한다. client → 같은 저장 ID/UTC의 표/그래프/성장 연구3D와
   실제 PG/TLS/WebGL 수용 전 `crop-cycle-result-pages` parent는 열어 둔다.

작업량은 닫힌 DTO/오류·권한2–3시간 + 실제 조립/TLS/예산·정리2–3시간의
**4–6집중시간**, 하루4시간 기준 **2026-10-06–08 KST 잠정**이다.
DB 최종 수용·CI 대기와30초 실제 측정에서 발견되는 수정은 날짜를 갱신할 근거다.
뒤 client2–3시간/3D·실제 브라우저4–6시간까지 합쳐 새 긴 결과 연구3D는10–15집중시간/
10월6–10일 KST 잠정이다. 실제166일 부하·품종/입력·생과·자원/경제·G0–G4와 생산 예측/추천
완료 날짜는 해당 자료/측정과 실행 실적 뒤 정하며 이 합성 연구3D 날짜에 포함하지 않는다.
