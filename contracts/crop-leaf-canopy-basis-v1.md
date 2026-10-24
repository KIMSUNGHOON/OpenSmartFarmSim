# 저장된 추적 잎의 바닥 면적 환산 — 연구 v1

상태: [고유202검사·원24시점/48환산 수용](../research/crop-leaf-canopy-basis-20261024.md). [생산 연결 조사](../research/leaf-lifecycle-production-primary-sources-20261024.md)의
단방향 면적 경계다. [저장 생애 결과](crop-leaf-lifecycle-artifact-v1.md)를 재사용한다.

`calculate_stored_leaf_canopy_basis(directory, access, *, inputs)`는 생장 계산 없이 원 frame을 읽고
`active_leaf_area / floor_area`만 계산한다. 원 shoot를 식물 수나 농장 전체로 복제하지 않는다.
현재 artifact에는 전체 실제 수관을 대표한다는 증거가 없다. 따라서 출력은
`tracked_leaf_area_index`이며 생산 RHS의 `leaf_area_index`를 대체하지 않는다.

inputs는 닫힌 객체다: `schema_version=leaf-canopy-basis-input-v1`, `input_id`, `origin=synthetic`,
`evidence_level=assumed`, `evidence_id`, `artifact_sha256`, `index`, `floor_area={value,unit=m2_floor}`.
evidence_id는 자체 합성 면적 가정의 식별자이며 SourceRecord 승인이나 실제 농장 면적 증거가 아니다.
명시 ID는 1–200 ASCII 식별자, SHA는 64자리 소문자 hex, index는 bool을 제외한 0–511 정수다.
floor_area는 bool을 제외한 int/float의 유한 양수·정상 binary64 범위이며 기본값은 없다.
서로 다른 artifact/index/면적 가정은 서로 다른 입력 해시다. 정규 JSON 원 입력을 해시하고
출력에 그 원 입력 복사본을 남긴다. 임의 SLA·밀도·shoot/plant 배수·면적 보정은 허용하지 않는다.

원 reader의 SHA/권리/원 준비·UTC/부착·개수/면적 검증을 그대로 통과해야 한다.
현재 active 면적만 사용한다. removed는 제거 당시 마지막 면적이며 현재 LAI에 넣지 않고,
pending에는 현재 면적을 만들지 않는다. 빈 active의 환산값은 정확히 0이다.
양수 면적의 환산이 0/subnormal이 되거나 유한 범위를 넘으면 `NUMERIC_HOLD`이며 clamp하지 않는다.
자체 합성 입력·출력은 각각 128 KiB 이하로 제한한다.

출력은 연구 버전/코드·reader SHA, 원 입력/SHA, 원 artifact/result/input·appearance/management/preparation SHA,
index/UTC/원점/정확 경과 초, 원 active/removed/pending ID·개수와 현재 면적,
명시 floor_area 및 `tracked_leaf_area_index(m2_leaf/m2_floor)`를 보존한다.
`software_research_only`, `synthetic_tracked_leaf_lai_math_only`, `gates=not_assessed`,
`canopy_use=tracked_inventory_comparison_only`를 고정한다. 생산·질량·수확·자원·마진/추천 값은 내지 않는다.
호출은 새 DB/작업/서명/API·저장 artifact를 만들지 않는다. 기존 물리 모델과 기존 3D는 유지한다.

수용은 RED 후 새/관련 집중 검사, 두 원 결과의 24시점×서로 다른 자체 합성 바닥 면적 2개를
독립 Fraction 나눗셈과 대사하고 원 UTC/면적/ID/해시·빈 현재 목록을 확인하는 것이다.
단위/누락/상태/비유한·underflow/overflow/변조와 현재 저장 권한 거부,
fresh 조회의 생장 import/계산·DB/CLI/network/쓰기 0 및 원 파일/WSL 보존을 확인한다.

후속 생산 연결은 같은 농장/작기·온실 floor/유인 shoot와 전체 초기 잎/출현/제거의 표현 범위,
같은 원점/정확 사건 시각과 carbon forcing, 잎별 CH2O·DM 구분/질량 배분·관리 제거 원장,
생애 면적 곡선과 SLA 기반 질량 성장의 양립 또는 명시 결합 모델을 요구한다.
기존 연속 제거율과 같은 잎의 순간 제거를 이중 차감하지 않으며 canopy 열용량/동반 에너지를 함께 대사한다.
과실 50구획/수확→명시 DM/CH2O·DM/FW→등급/판매·구매 에너지/요금·Decimal 경제와
G0–G4 게시 조건은 기존 명세를 따른다. 이 작은 환산의 수용으로 해당 조건을 해제하지 않는다.
