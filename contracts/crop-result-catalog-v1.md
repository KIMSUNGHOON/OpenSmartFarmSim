# 저장 작물 연구 결과 목록 v1

`product-ui-result-catalog`(U1)의 서버 목록 자식이다. 현재 작성 농장 목록에서 선택한
농장/판본·등록 hash·crop_id로 저장된 생장 또는 수확 결과를 찾는다.
상태: [metadata 서버 자식의 로컬 수용](../research/crop-result-catalog-metadata-implementation-20261009.md).
전체 U1은 이후 보호 API/웹 SDK·목록 선택·실제 브라우저까지 수용해야 완료한다.

## 경계와 핵심 파일

핵심 4파일: `backend/app/crop_result_catalog.py`, `backend/tests/test_crop_result_catalog.py`,
`backend/tests/crop_result_catalog_preserved_smoke.py`, 이 계약.
기존 verified calculation 결과 표/authority와 별도 harvest registry reader를 사용한다.
새 표·DB role·증명·결과 생성·요청 간 캐시는 추가하지 않는다. 진행 중인 전체 producer와 기존 UI 서버는 보존한다.

`CropResultCatalog(calculation_query, harvest_query=None)`는 같은 계산 query에 결속된
실제 타입만 받는다. `open(tenant, kind, farm_ref, limit=10, before=None)`의 context 안에서
응답을 투영하고 직렬화한다. 반환 직전/직후 현재 권리·등록과 원 metadata를 다시 검사한다.

- kind: `calculation_cycle_v1` 또는 `harvest_v1`; 이 두 판본의 결과를 먼저 연결한다.
  기존 기관/구획/startup 판본의 목록은 별도 후속이며 기존 개별 조회는 유지한다.
- farm_ref: 기존 `scenario_id`, `scenario_revision`, `registration_sha256`, `crop_id`의 닫힌 객체.
  빈 목록에서도 현재 등록·작물과 계정/범위를 확인한다.
- limit: 정수 1–20. `before`는 null 또는 닫힌 `{recorded_at: aware datetime, result_id}`다.
  UTC로 정규화하고 `(recorded_at, result_id)` 내림차순 keyset으로 limit+1개만 읽는다.
  cursor는 서버 권한이 아니다. 매 페이지에 계정·농장/등록·작물 필터를 다시 적용한다.

## 표시와 권한의 의미

목록은 서명된 **저장 metadata**만 제공한다. 계산 상태 `completed/hold`, 최초 저장 시각,
생장 연구 ID/판본·명시 작기/시점 개수 또는 수확 ID/부모 ID·행 개수를 표시한다.
원 payload/서명·키·credential·개인 농장 원문은 반환하지 않는다. 전체 개수/예측·추천을 추정하지 않는다.

계산 표의 HMAC/hash·column 결속을 기존 store로 확인한다. 원 farm/등록·현재 display 권리,
입력 policy/resolver/고지 판본을 대사한다. 수확은 별도 reader role로 확인하고 서명된 원 부모의
ID/payload/input/artifact hash·상태와 결속한다. 현재 권리가 없거나 변조된 행은 조용히 건너뛰지 않고
페이지 전체를 거부한다. 빈 목록도 등록/계정 검사를 생략하지 않는다.

### 실제 다수 목록 비용의 보완

보호 API의 실제20건이30초를 넘은 근거로, 각 검사 단계 안에서 동일한 등록 조회를 한 번만 수행한다.
묶는 키는 tenant·닫힌 farm 참조·권리 `available_at`·원 입력 period 전체다.
기존 `CycleFarmBinding._registration` 구현 파일 SHA를 명시적으로 고정하며, 구현 변경은 새 검토 전 거부한다.
이 키는 고정 구현이 참조하는 모든 요청/원 입력 필드를 포함한다. study/입력 root가 달라도
현재 display 권리는 각각의 원 선언/root로 매번 검사한다. 서명 metadata/부모/column 대사도 생략하지 않는다.
초기 읽기·직렬화 전 재검사·직렬화 후 재검사마다 별도 묶음을 만들고 현재 농장 전체 비교를 유지한다.
서로 다른 권리 시각/period/농장/tenant는 합치지 않는다. 요청 사이 또는 검사 단계 사이에 재사용하지 않는다.
실제 같은 period/권리 시각20건에서만 측정한 개선이며 임의의20개 서로 다른 등록 조건의 운영 지연 수용은 아니다.

`selection_validation_required=true`, `rights_or_gate_approval=false`다.
이 조회는 원 artifact/입력 파일이나 수치행을 읽어 검증하지 않는다. 선택할 때 기존 현재 query/API가
파일·원 서명·입력·현재 권리·적용 범위를 다시 검증해야 한다. 파일 유실이 목록의 숫자를
실행 가능한 결과로 승격하지 않는다. 결과 목록을 실제 품종·G0–G4 승인 또는 진행 중인 실행으로 표시하지 않는다.

응답은 `crop-research-result-catalog-v1`, `stored_research_metadata_only`, kind/farm_ref,
항목과 nullable next_cursor를 포함하며 canonical JSON 64KiB 이하다.
조회 중 삽입된 새 결과는 다음 첫 페이지에서 보일 수 있고 이미 읽은 스냅샷의 항목을 바꾸지 않는다.
선택 변경·계정/권리 실패·취소 때 목록/이전 결과 제거와 늦은 응답 거부는 웹 자식에서 검증한다.

## 이번 자식의 수용 기준

1. 닫힌 필터/limit/cursor·UTC/동률 경계, 두 kind의 안정된 키 순서·페이지/빈 목록을 확인한다.
2. 실제 별도 SCRAM 복원 DB의 기존 생장/수확 ID·최초 저장 시각·부모/단위 없는 metadata를 대사한다.
   정상 producer의 결과를 복사해 재계산하거나 새 서명으로 바꾸지 않는다.
3. foreign 계정/현재 scope·등록/작물·display 철회, HMAC/metadata 변조 및 투영 뒤 철회를 거부한다.
   원문/서명키/프로필/입력·artifact 파일 생성·게시/RHS 호출은 0이다.
4. 소유 별도 DB/role/passfile/프로세스·FD/WSL 자원과 원 producer·미리보기/보존 자료의 불변을 확인한다.
   수용한 SQL/현재 권리 조회 시간은 실제 사례의 범위로 기록하며 전체 목록 운영 용량으로 확대하지 않는다.
5. 보호 API/OpenAPI·SDK·목록 화면·실제 선택/새로고침·진행 상태/3D 자동 연결은 미완료로 남긴다.
