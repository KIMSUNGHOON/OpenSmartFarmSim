# 저장 material 창과 명시 자원 비용 기간의 연구 결속 v1

상태: [신규67·기존78=고유145검사/실제 SCRAM·원 저장 창/비용 조회 수용](../research/supply-material-resource-cost-scope-binding-20261106.md). 수용된 material quantity reader와 현재 비용 결과를 함께 검증하는 첫 연구용 중간 단계다.
[기존 전체 결속 계획](supply-material-resource-economics-binding-v1.md)은 보존한다. 이 계약은 현재 schema4/v10·선언 생산 batch를 사용하며 수확이 없는 선언 batch도 기존 원장이 허용하는 그대로 받는다.
원 Cost.purpose·batch/sale·발생/지급과 숫자 모델을 바꾸지 않는다. 실제 Farm/current custody→불변 접수/현재 조회→HTTP/strict SDK/같은 선택3D의 제품 결속은 계속 필수 후속이다.

## 서버 조립과 호출

새 모듈은 `app.crop_supply_material_cost_scope_binding`이다.

```python
MaterialCostScopeBinding(directory, access, root_sha256, cost_query,
                        *, material_provenance).prepare(tenant, request_raw) -> bytes
```

`access`는 정확한 ContentAccess, `cost_query`는 정확한 EconomicCostResultQuery,
`material_provenance`는 아래 MaterialSourceProvenance다. 디렉터리·한 root·provenance는 trusted producer/고정 inventory를 선택한 서버/operator가 생성 시 고정한다.
요청은 경로·repository·provider·callback·tenant를 공급하거나 다른 root를 선택하지 않는다.
이 파일 정책은 tenant ACL이나 Farm custody가 아니다. 비용 조회의 현재 tenant/읽기 권한은 실제 query authority가 검사한다.
`MaterialCostScopeHold(ValueError)`가 잘못된 선언/불일치/변조/사용 불가의 고정 실패다. 권한 거부 PermissionError는 유지한다.
반환은 새 canonical bytes이며 DB/CAS 게시·HTTP 설치·작업 실행을 하지 않는다.
기존 CostQuery의 실제 PG transport/읽기는 허용한다. 추가 외부 network·CLI/자식 프로세스·SQL/CAS 쓰기는 없다.

## 닫힌 요청

`MaterialCostScopeRequest`는 아래 키만 받는다. 모든 필드는 필수이며 묵시 기본값은 없다.
입력은 1–131072bytes의 canonical JSON 객체다. canonical은 UTF-8·sort_keys=True·separators=(',', ':')·ensure_ascii=True·allow_nan=False다.
중복 키/비표준 숫자/미지 필드·잘못된 타입을 거부한다. 이름은 앞뒤 공백 없는 비어 있지 않은 200자 이하 문자열, SHA는 소문자64hex, UUID는 canonical 소문자 형식이다.

| 객체 | 정확한 필드 |
|---|---|
| 최상위 | `schema_version='supply-material-resource-cost-scope-request-v1'`, `declaration`, `material`, `economic`, `costs` |
| declaration | `declaration_id`, `revision`, `origin='user'`, `evidence_level='assumed'`, `relation='independent_user_assumption'`, `source_ref`, `assumption_scope`, `available_at` |
| material | `root_sha256`, `projection_code_sha256`, `quantity_sha256`, `first_frame`, `last_frame` |
| economic | `job_id`, `input_sha256`, `artifact_sha256`, `trace_id`, `publication_id` |
| costs의 각 항목 | `category`, `cost_id`, `cost_sha256`, `quantity_input`, `unit_cost_input`, `resource_kind`, `period`, `included_items`, `excluded_items`, `unknown_items` |
| quantity_input / unit_cost_input | `input_id`, `revision` |
| period | `kind`, `boundary='half_open'`, `calendar='Asia/Seoul'`, `start_at`, `end_at` |

`first_frame`/`last_frame`은 bool 아닌 정수이며 0≤first≤last<512다. 둘 다 명시한다.
`costs`는 1–128개의 선언이다. 같은 Cost.id를 반복하거나 variable/fixed 양쪽으로 중복 선택하지 않는다.
`category`는 variable/fixed다. 각 items 배열은 명시한 이름의 목록으로 최대32개이며 included는 최소1개다.
각 배열의 중복과 세 배열 사이 겹침을 거부한다. 빈 excluded/unknown 배열은 명시한 빈 선언이며 누락/전체 완전성을 자동 승인하지 않는다.

원 quantity 결과 SHA는 기존 material reader의 canonical bytes에 대한 SHA다.
Cost SHA는 원 저장 JSON의 `line.cost`를 기존 경제 canonical serializer로 인코딩한 SHA다.
이 두 원 serializer를 서로 바꾸거나 원 금액을 Decimal 문자열로 다시 만들지 않는다.

## 자원과 비용의 의미

| resource_kind | 원 quantity.unit / unit_cost.unit |
|---|---|
| electricity | kWh_e / KRW/kWh_e |
| fuel | L / KRW/L |
| water | L / KRW/L |

품목은 반드시 선언한다. Cost.id/source_ref/단위 L만 보고 연료/물을 추정하지 않는다.
kg/month·열량·연료 발열량·m3나 다른 단위는 이 자원 결속에서 지원하지 않는다. 단위를 바꾸어 통과시키지 않는다.
원 비용의 purpose·batch/sale link·quantity/unit_cost/payment 입력 판본/등급·incurred_at/paid_at과 원 trace 금액/null을 그대로 둔다.
원 incurred_at 또는 paid_at이 새 period 안에 있어야 한다는 규칙을 만들지 않는다. 비용 인식/지급 시각은 서비스·구매/청구 범위와 서로 다른 명시 사실이다.
같은 Cost의 새 period는 원 v10의 발생/현금 기간을 재분류하거나 생산 직접비를 period 비용으로 바꾸지 않는다.

period.kind는 purchase/billing/usage 중 하나다. 이 판본은 Cost마다 그 한 종류만 표현한다.
다른 두 종류의 기간이나 물리적 사용량이 확인되었다는 뜻이 아니며 결과에 그 미확립 상태를 남긴다.
included/excluded/unknown은 원 비용에 대해 사용자가 선언한 범위다. 기본/수요/세금 등 빠진 품목을 시스템이 생성하거나 전체 청구서라고 승인하지 않는다.

## 정확 시각과 완전한 관계

start_at/end_at/available_at와 provenance의 알려진 시각은 명시 offset 또는 Z를 가진 ISO datetime이다.
`YYYY-MM-DDTHH:MM:SS[.1–6자리](Z|±HH:MM)`만 받으며 naive/날짜만/float epoch를 거부한다. period는 start<end다.
원 offset 문자열을 보존하고 비교할 때만 UTC로 바꾼다. period.calendar는 표시/결산의 Asia/Seoul을 명시하며 offset 없는 시각에 timezone을 채우는 기본값이 아니다.
declaration.available_at은 원 경제 decision_at 이하이어야 한다. 이 검사는 사용자 선언의 일관성 검사이며 실제 과거 이용 가능성/권리·소유권을 승인하지 않는다.

`_utc_fraction(aware_datetime) -> Fraction`은 UTC epoch와의 정수 일/초/microsecond로 정확 값을 만든다.
timestamp()/total_seconds()/float를 사용하지 않는다. material 절대 시각은 원 origin의 정확 UTC값+원 elapsed_seconds_exact Fraction이다.
origin의 microsecond도 보존하며 material의 더 작은 분수를 datetime으로 반올림하지 않는다.

원 frame 선택은 inclusive first/last이며 원 phase/state/cursor/event sequence를 보존한다.
비교용 시간 지지 W=[a,b)는 a<b인 경우에만 사용한다. a=b인 한 frame/같은 시각 before→after 선택은 빈 구간이 아니라 point다.
독립 선언 기간 C=[c,d)는 항상 c<d다. `_coverage(a,b,c,d) -> {'relation': ..., 'coverage': ...}`는 정확 Fraction 네 개만 받는다.

| interval relation: W 대 C | 조건 |
|---|---|
| before | b<c |
| meets | b=c |
| overlaps | a<c<b<d |
| starts | a=c, b<d |
| during | c<a<b<d |
| finishes | c<a, b=d |
| equal | a=c, b=d |
| finished_by | a<c, b=d |
| contains | a<c<d<b |
| started_by | a=c, d<b |
| overlapped_by | c<a<d<b |
| met_by | a=d |
| after | a>d |

interval coverage는 C가 W 전체를 포함하면 whole_window, 양의 교집합이 있지만 전체가 아니면 partial_window, 나머지는 no_overlap이다.
접하는 meets/met_by는 no_overlap이다. 이13관계는 유효한 두 양의 구간을 빠짐없이 구분한다.
point a=b는 point_before(a<c), point_at_start(a=c), point_inside(c<a<d), point_at_end(a=d), point_after(a>d)다.
coverage는 c≤a<d이면 point_covered, 아니면 point_not_covered다. period 끝과 같은 점은 포함하지 않는다.

모든 유효한 관계는 연구 결속 결과를 낸다. 부분·별도·서로 떨어진 기간이라는 이유만으로 요청 전체를 거부하지 않는다.
coverage는 그 기간 종류와 시간 관계뿐이다. billing coverage가 usage coverage나 같은 농장의 실제 구매를 의미하지 않는다.
원 Cost 전체 금액을 표시하고 `amount_scope='original_cost_line_only'`, `allocated_window_cost=null`을 항상 붙인다.
equal/whole_window라도 창 비용을 계산·배분했다고 바꾸지 않는다. 구매량 추정·요금 곱·부분 기간 안분·단순 합/새 소계는0이다.

## provenance와 현재 fence

MaterialSourceProvenance의 필드는 `source_ref`, `metadata_sha256`, `published_at`, `available_at`이다.
뒤 두 필드는 각각 명시 aware datetime 또는 null이며, 이 값은 서버가 선택한 별도 provenance 선언으로만 취급한다.
원 root/index에 없는 시각을 model origin·mtime·보고서 observed_at에서 추정하지 않는다.
현재 공개 합성 fixture의 index/root에는 published_at/available_at가 없다. 10월31일 수용 기록과 10월1일 합성 model clock을 구분한다.
별도 self-authored 시험 provenance가 제공되면 그 선언을 그대로 보존하고, null이면 unknown이다. 실제 root 게시/이용 시각의 검증이나 ex-ante 승인이 아니다.
원 경제 decision_at과 material published/available 시각의 관계는 각각 before_or_at_decision/after_decision/unknown으로 기록하며 ex_ante_eligibility는 not_established다.

실제 `read_material_quantity_window`와 `EconomicCostResultQuery.read`를 전후에 다시 호출하여 같은 원 결과 bytes/선택/SHA·처음 publication ID/시각을 확인한다.
query는 원 입력/source/현재 권한·근거·코드 검사를 그대로 담당하며 execute scope가 필요하지 않다.
material reader는 기존 소유 파일 정책·현재 embedded use/display·코드/원 source fence를 담당한다.
조립 시 고정한 root/path/access/provenance/query 객체와 함수 identity, 현재 권한·새 모듈/의존 코드가 늦게 바뀌면 결과를 반환하지 않는다.
live callback으로 검사를 대체하지 않는다. 기존 source/metadata/current 읽기 범위를 복제하거나 금액/worker를 호출하지 않는다.
이 전후 대사는 서로 다른 저장소의 원자 Farm snapshot/외부 현재 권리 승인이 아니다.

## 반환과 수용

반환은 위 canonical JSON의 최대2097152bytes다. `binding_id`는 자신을 뺀 반환 객체 canonical SHA다.
최상위 필드는 schema_version=`supply-material-resource-cost-scope-binding-v1`, binding_id,
scope=`software_research_only`, claim_scope=`independent_user_resource_cost_scope_only`, tenant_id,
request_sha256, declaration, material, economic, costs, unselected_costs, resource_kinds_not_selected,
product_holds, as_of_decision, code_sha256, dependency_sha256, G0_G4=`not_assessed`, R2=`not_approved`다.

material의 정확한 키는 quantity, quantity_sha256, provenance, temporal_support다. quantity는 원 reader 결과 전체다.
temporal_support는 kind(interval/point), boundary(half_open/point), start_utc_exact/end_utc_exact이며
각 exact 값은 numerator/denominator 십진 정수 문자열과 unit=`s_since_unix_epoch`다.
economic의 정확한 키는 job_id, input_sha256, artifact_sha256, result_sha256, trace_id, code_sha256,
environment_sha256, publication_id, published_at, scenario_id, scenario_revision, scenario_sha256,
scenario_source_job_id, decision_at, period_start, period_end다. 모두 현재 원 결과/입력·첫 publication에서 복사한다.
costs 각 행은 `reference`(원 요청 cost 선언), `original_line`(원 raw의 전체 line), amount_scope,
allocated_window_cost, `temporal_relation`(_coverage 결과), `period_semantics_established`(선언 kind),
`other_period_kinds_not_established`를 갖는다. 요청 순서를 유지한다.
unselected_costs는 원 trace 순서의 category/cost_id/cost_sha256 참조이며 원 원장과 다시 합산하지 않는다.
resource_kinds_not_selected는 electricity/fuel/water 순서의 미선택 종류다. 선택 subset을 전체 필수 비용이라고 표시하지 않는다.
product_holds는 farm_current_custody_unverified, resource_cost_declaration_unregistered, window_cost_allocation_not_established다.
as_of_decision의 정확한 키는 material_published_relation, material_available_relation, ex_ante_eligibility다.
dependency_sha256은 crop_supply_material_quantities.py, economic_cost_query.py, economic_batch_query.py,
content_access.py의 생성 시 로드한 SHA를 기록하고 전후에 다시 검사한다.

수용은 순수 요청/단위·정확 UTC/Fraction·13관계/5point의 독립 표와 실제 trusted material+실제 SCRAM 게시 Cost/current query를 모두 사용한다.
목록/해시/판본/tenant/중복/미지 기간·품목·단위, 목적 보존·미지 지급 null, 전후 source/권한/함수/코드/metadata drift·한도/방어 복사를 검증한다.
원 model advance·worker·금액/안분·SQL/CAS쓰기0과 원 source/입력/산출물/과거 manifest 보존을 확인한다.
구현 전 actual RED와 이후 고정 source의 실제 focused 검사를 남긴다. Farm association·불변 등록/제품 조회·HTTP/runtime/SDK/UI 수용은 이 결과로 대체하지 않는다.
원 signed counter는 원 단위/부호/floor basis를 유지하며 구매 전력·연료·물이나 작물 생산/마진/추천으로 바꾸지 않는다.
