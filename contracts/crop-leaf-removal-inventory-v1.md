# 기존 여러 잎의 명시 제거와 시간 전진 — 연구 v1

상태: 계약/검증 중. [한 잎 시간 경계](crop-leaf-removal-timeline-v1.md)를 재사용하며
기존 population/point/timeline 판본과 runtime을 바꾸지 않는다.

`initialize_leaf_removal_inventory(inputs={input_id,population_state,removals})`는
유효한 기존 population checkpoint와 명시 제거 선언 목록(없으면 `[]`)을 받는다.
초기 잎과 이미 출현한 새 잎을 모두 기존 잎으로 취급한다. 아직 출현하지 않은 ID는 거부한다.
각 선언은 기존 whole-leaf schema이며 원 UTC/leaf ID에 결속하고 source 현재 시각 이후여야 한다.
같은 시각의 제거는 즉시 고정한다. leaf ID와 event ID는 목록 안에서 각각 고유하다.
목록 순서는 보존하며 시각 순 정렬이나 관리 시기 추론을 하지 않는다.

state는 model_version/source_population/source_population_sha256/removal_declarations/
removal_declarations_sha256/at_elapsed_seconds_exact/leaf_checkpoints다.
원 population 전체와 SHA, 초기 부착/출현 선언·birth_inventory를 보존한다.
leaf_checkpoints는 원 초기 잎→원 새 잎 순서의 `{state,removal_receipt}` 목록이다.
각 항목은 원 source의 동일 잎과 전체 진행 시각으로 한 잎 timeline을 재구성해 검증한다.
초기 상태·선언을 항목마다 다시 복제하지 않는다. 자기 SHA는 인증된 이력/권리 승인이 아니다.

`advance_leaf_removal_inventory(inputs={input_id,state,segments})`는 원 forcing을 먼저 검사한다.
기존과 같은1–512개 연속 finite Celsius 구간이며 시작은 전체 진행 시각과 같아야 한다.
각 잎은 그 제거 시각까지만 전진하며 마지막 나이/면적/receipt를 고정한다.
제거된 잎의 마지막 시각은 전체 진행 시각보다 이전일 수 있다. 생존 잎은 전체 시각과 같아야 한다.
모두 제거된 뒤에도 전체 시각은 forcing 끝으로 이동하며 leaf advance는0회다.
그때도 단위/연속성/finite 값은 검사한다. 생존 잎에 적용되는 below-base는 기존 보류다.

출력은 state/input_sha256와 tracked/active/removed_leaf_count, active/removed_leaf_ids,
active/removed/last_tracked_leaf_area(`m2`)다. 제거 면적은 각 제거 시각의 마지막 면적 합이며
last_tracked 합은 생존 현재 면적+제거 마지막 면적이다. 이를 같은 시각의 전체 수관 면적이나 LAI로 표시하지 않는다.
전 목록은1–512개이며 active0을 허용한다. 잎/사건/forcing 개수와2MiB 입력·출력 제한을 각각 적용한다.
512개 이하여도 전체 bytes를 넘으면 원자적으로 보류한다. 일괄/분할의 마지막 state는 같아야 한다.
입력·출력 alias/부분 성공은 허용하지 않는다. 외부 농장/저장 결속 전 선언 수정은 새 초기 입력이다.

수용은 독립 Fraction 나이/고정밀 면적·개수/면적 합, 동시/분수 경계·분할 재개,
모두 제거된 뒤 시간 전진/leaf advance0, 원 ID/부착/출현 이력·변조/단위/용량 거부다.
software_research_only/synthetic_crop_math_only/not_assessed를 유지한다.
새 출현·자연 노화/관리 추천·질량/생산/경제·새 저장/API/3D는 후속이다.
