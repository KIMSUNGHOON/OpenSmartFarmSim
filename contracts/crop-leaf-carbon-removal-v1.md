# 같은 순간의 잎 제거·탄소/열용량 전이 — 연구 v1

상태: [순간 계산 고유234검사·fresh16사례 수용](../research/crop-leaf-carbon-removal-20261024.md). [결합 경계](../research/crop-leaf-canopy-basis-20261024.md),
[잎 생애](crop-leaf-lifecycle-v1.md), [기존 공동 관리](crop-climate-joint-management-v1.md)를 따른다.
이 계약은 **명시된 합성 순간 상태**의 결속이며 전체 작기/실제 농장·시간 적분이나 예측 승인이 아니다.

`apply_leaf_carbon_removals(*, inputs, growth_profile, cohort_profile, transport_profile, exchange_profile)`.
inputs의 닫힌 필드는 schema_version=`leaf-carbon-removal-input-v1`, input_id, origin=`synthetic`,
case_id, shoot_id, lifecycle_state, joint_state, mass_basis, event_ids다.
joint_state는 `{time_origin_utc,at_elapsed_seconds_exact,scenario}`이며 기존 공동 RHS의 명시 순간 scenario다.
원점과 정규 정확 초는 lifecycle의 전체 현재 시각과 같아야 한다. 분수 초도 그대로 결속하되 시간을 전진시키지 않는다.
기존 정수 UTC 실행/적분의 분수 초 지원 증거로 쓰거나 가짜 반올림 UTC를 만들지 않는다.

lifecycle_state는 기존 정규화가 검증한 **현재 사건 후 checkpoint**다.
event_ids는 현재 정확 시각에 제거된 전체 batch의 원 event ID를 원 선언 순서로 나열한다.
이미 과거에 제거된 잎/다른 시각/누락·중복 batch·pending은 이번 사건으로 다시 제거할 수 없다.
이 순간의 제거 마지막 상태를 현재 active에 더해 사건 직전 목록을 재구성한다. 과거 제거는 더하지 않는다.
출현 전이나 제거 뒤 forcing을 새로 계산하지 않으며 원 anchor/출현/부착·제거 receipt를 유지한다.

mass_basis의 닫힌 필드는 schema_version=`explicit-leaf-carbon-basis-v1`, case_id, shoot_id,
origin=`synthetic`, evidence_level=`assumed`, evidence_id, lifecycle_state_sha256, joint_state_sha256,
floor_area와 leaf_carbohydrate다. case/shoot/두 원 state SHA가 inputs와 일치해야 한다.
floor_area는 명시 양수 `m2_floor`; 기본값/밀도·식물 복제는 없다.
case/shoot ID는 이 합성 입력 안의 일치 표지이며 현재 원 수치 state만으로 실제 shoot·농장/작기 계보를 증명하지 않는다.
leaf_carbohydrate는 사건 직전 추적 잎의 정확한 순서/고유 ID를 가진 `{leaf_id,carbohydrate:{value,unit=mg_CH2O}}` 목록이다.
각 질량은 별도의 양수 정상 binary64 가정이다. 면적·SLA를 역산해 질량을 만들지 않는다.
동일 명시 mass/floor를 Fraction(binary64) 합·나눗셈 후 한 번 binary64로 반올림해 mg_CH2O/m2_floor로 변환한다.
직전 질량 합은 joint leaf stock과 정확히 같아야 하며, 어느 재고도 보정하지 않는다.
입력/출력은 각 2MiB, ID1–200 ASCII·기존512기관 한도를 유지한다.

기존 모델의 `SLA×C_leaf`와 추적 면적/floor를 사건 전후 각각 대조한다.
허용 차이는 `64*ulp(max(abs(x),abs(y)))`의 binary64 대사뿐이며 생물학적 오차 허용치가 아니다.
불일치·비유한/underflow·초과/전량 적엽은 hold다. 현재 연속 leaf 제거율이 0이 아니면
같은 사건의 연속/순간 이중 차감을 배제할 근거가 없어 보수적으로 hold한다.

모든 명시 제거 C를 합쳐 기존 관리 함수에 한 번 전달한다. stem 제거0·50 fruit fraction0을 명시한다.
buffer/stem·50과실 C/N·공기 상태와 필터 온도는 순간 사건에서 바뀌지 않는다.
기존 수관 열용량·동반 signed sensible energy/온도·C/N 수지를 통과해야 결과를 반환한다.
실패 시 입력/원 상태를 바꾸지 않으며 부분 성공을 내지 않는다.
원 source/입력·mass basis/코드·프로필·제거 receipt와 기존 원자 전이 결과를 출력에 결속한다.
같은 입력 재실행은 동일 결과다. 원 mass basis에 사건 후 joint state를 넣어 재차 차감하면 SHA/재고 대사로 거부한다.
이것은 영속 작업의 exactly-once/농장 승인 증거가 아니며 해당 외부 실행 계약은 별도다.

수용은 질량을 먼저 선언한 자체 합성 paired case의 Decimal/Fraction 독립 전후 C/LAI·열용량/유출/Tc,
부분/동시 batch·정확 분수 초·기존 과거 제거 제외·원 입력 불변/동일 재실행,
초과/소진·SLA 불일치·중복/누락/다른 ID·시각·단위·출처 SHA·연속 제거/늦은 변조 거부,
기존 joint management/leaf lifecycle 회귀와 원 저장 입력의 올바른 불일치 hold다.
생장 advance/적분·DB/CLI/network/쓰기0, 관리1회·공동 RHS2회와 WSL/원 자료 보존을 확인한다.
출력은 software_research_only/synthetic_leaf_carbon_removal_math_only/G0_G4=not_assessed다.
실제 전체 수관 대표성·질량 계측, 연속 탄소 분배/출현 질량·면적 feedback, 원 실행/서명·3D 게시,
과실/수확·자원/경제/추천과 G0–G4는 후속이다.
