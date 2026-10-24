# 고정 출현/제거 선언의 잎 생애 계산 — 연구 v1

상태: [522검사/원47상태 fresh 수용](../research/crop-leaf-lifecycle-20261024.md). [기존 제거 목록](crop-leaf-removal-inventory-v1.md),
[출현 선언](crop-declared-leaf-births-v1.md)과 [한 잎 시간 경계](crop-leaf-removal-timeline-v1.md)를 재사용한다.
기존 판본/runtime을 바꾸지 않는 `declared-leaf-lifecycle-research-v1`이다.

`initialize_leaf_lifecycle(inputs={input_id,population_state,births,removals})`는 기존 population checkpoint와
앞으로의 명시 출현/전체 잎 제거 목록을 받는다. 없는 목록도 `[]`로 명시한다.
출현/제거는 이번 실행의 고정 입력 가정이며 예측/관리 추천이 아니다. 변경은 새 초기 입력이다.
기존 자동 출현 정책의 선언도 같은 schema로 받을 수 있지만 이 모듈이 그 정책을 새로 추론하지 않는다.

births는 기존 schema의 출현 시각 비감소 목록이며 모두 source 현재 시각보다 뒤여야 한다.
leaf ID는 source 전체와 births 사이에서 고유하다. 제거된 ID도 재사용할 수 없다.
removals는 기존 whole-leaf schema이고 leaf/event ID가 각각 고유하다. source 잎 또는 명시 births에만 연결한다.
기존 잎의 source 시각 전 제거와 새 잎의 출현 전 제거는 거부한다. 출현과 같은 시각 제거는 허용한다.
기존 전체 잎+예약한 출현은1–512개, 제거/forcing은 각각 최대512개이며 전체2MiB 입력/정규화 출력 제한도 적용한다.

state는 model_version/existing_inventory_state/birth_declarations/birth_declarations_sha256/
removal_declarations/removal_declarations_sha256/new_leaf_checkpoints다.
기존 inventory는 원 source/SHA·초기 부착/출현/제거 이력을 그대로 보존한다.
전체 시각과 원점은 기존 inventory에서 읽으며 별도 시계로 복제하지 않는다.
new_leaf_checkpoints는 출현 선언 순서의 `{state,removal_receipt}`다. 출현 전 두 값은 null이다.
출현 후 원 선언에서 재구성한 나이0/원 면적 anchor와 같은 한 잎 timeline으로 검증한다.
출현 전 선언 검증을 위한 초기 상태 재구성은 가능하지만 현재 목록에는 넣지 않는다.
선언 목록/SHA·개수/순서·현재/마지막 시각·receipt를 대사한다. 자기 SHA는 인증된 이력/권리 승인이 아니다.

`advance_leaf_lifecycle(inputs={input_id,state,segments})`는 같은 전체 시각에 이어지는 원 forcing을 받는다.
모든 구간은 연속·유한 degC/정확 초이며 pending/제거 상태에서도 검증한다.
새 출현은 `(현재,끝]`에서 한 번 초기화한다. 새 잎은 출현 뒤 forcing만 받고 제거 시각에서 멈춘다.
끝 시각 출현은 초기화만 한다. 출현과 같은 시각 제거는 나이0의 마지막 상태를 보존하며 leaf advance0이다.
분할의 왼쪽 끝에서 출현한 잎은 오른쪽에서 다시 생성하지 않는다. 이미 제거된 잎은 전진하지 않는다.
빈 active 뒤 새 출현을 허용한다. 출현 전 저온은 새 잎의 thermal age에 더하지 않는다.
살아 있는 잎의 기준온도 미만은 기존 unsupported hold다. 부분 결과/입력·출력 alias는 없다.

출력은 state/input_sha256·원점/전체 정확 시각, declared/tracked/active/removed_leaf_count,
scheduled_birth_count/emerged_new_leaf_count/pending_leaf_count·active/removed/pending_leaf_ids와
active/removed/last_tracked_leaf_area(`m2`)다. pending은 현재 수/면적 합에 포함하지 않는다.
removed와 last_tracked는 다른 제거 시각의 마지막 값을 포함하며 이를 현재 수관/LAI·질량으로 표시하지 않는다.

수용은 원 출현 무제거 결과·독립 Fraction/고정밀 면적/개수/합계, 동시/분수/끝 경계·빈 active 뒤 출현,
모든 선정 분할의 같은 state·출현 전/제거 뒤 전진0·ID/이력/단위/시간/용량/변조 거부다.
software_research_only/synthetic_crop_math_only/not_assessed를 유지한다. 실제 stem 부착 가능성·원 입력/농장 결속,
불변 저장/현재 조회/3D·품종 생물학/질량/생산/자원/경제와 관문은 후속이다.
