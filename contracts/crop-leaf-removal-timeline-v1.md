# 한 잎의 기온 구간과 명시 제거 시각 — 연구 v1

상태: [297검사/원47상태 fresh 수용](../research/crop-leaf-removal-timeline-20261024.md). [point 제거](crop-declared-leaf-removal-v1.md)와 기존 rational leaf clock/area를 사용한다.
기존 판본·사용자 runtime을 바꾸지 않는 `declared-leaf-removal-timeline-research-v1`이다.

`initialize_leaf_removal_timeline(inputs={input_id,leaf_state,removal})`는 현재 존재하는 한 잎과
명시 제거 선언 또는 명시 `null`을 받는다. 선언은 point의 전체 잎 제거 schema를 그대로 사용하며
잎 ID/원점이 같고 정확 시각이 초기 현재 시각 이후여야 한다. 초기 시각과 같으면 즉시 제거한다.
미래 선언은 실행 입력의 가정이며 제거 시기 예측이 아니다. 이후 선언을 바꾸거나 추론하지 않는다.

state는 model_version/initial_leaf_state/initial_leaf_state_sha256/removal_declaration/
removal_declaration_sha256/at_elapsed_seconds_exact/leaf_state/removal_receipt다.
전체 진행 시각과 잎의 마지막 상태 시각을 구분한다. active일 때 둘이 같고, 제거 뒤에는 마지막 상태가 제거 시각에 고정된다.
원 초기 상태·anchor/curve·원점/ID·제거 선언을 유지한다. 자기 hash가 인증된 이력/권리 승인을 뜻하지 않는다.
receipt는 declaration_sha256/last_leaf_state_sha256/at_elapsed_seconds_exact/area의 닫힌 객체이며 마지막 상태에 결속한다.

`advance_leaf_removal_timeline(inputs={input_id,state,segments})`는 기존과 같은1–512개 연속 기온 구간을 받는다.
모든 구간의 단위/finite Celsius·정확 초/연속성을 먼저 검사하고 시작 시각은 전체 현재 시각과 같아야 한다.
제거가 구간 안 또는 끝에 있으면 그 정확 시각까지만 원 구간을 절단해 기존 leaf advance를 호출한다.
구간 경계의 제거는 앞 구간까지의 나이/면적을 사용한다. 뒤 구간은 그 잎의 생장에 기여하지 않는다.
제거 후에도 전체 진행 시각은 끝까지 이동하지만 잎의 나이/면적·receipt는 바뀌지 않고 leaf advance 호출은0이다.
제거 전 active prefix의 기온이 기준온도 미만이면 기존 unsupported domain을 유지한다.
제거 뒤의 finite 기온은 잎 생장으로 해석하지 않는다. 잘못된 단위/공백 등은 제거 뒤에도 거부한다.

출력은 state/input_sha256와 active/removed 상태, active_leaf_count/removed_leaf_count,
active_leaf_area/removed_leaf_area/last_leaf_area(`m2`)다. 제거된 잎의 마지막 면적을 현재 active 면적으로 표시하지 않는다.
같은 forcing/선언의 일괄·분할 재개는 같은 마지막 state/receipt를 낸다. 시작/끝/분수 초를 반올림하지 않는다.
기존2MiB·정확 숫자 문자열/forcing 상한을 유지한다. 입력/출력은 분리하며 부분 결과를 반환하지 않는다.

software_research_only/synthetic_crop_math_only/not_assessed를 유지한다. 여러 잎·새 출현,
원천 자료/농장 결속·서명 저장/조회·3D·자연 노화/적엽 추천·질량/생산/경제는 후속이다.
수용은 독립 정확 나이/면적·선정한 모든 내부/경계 분할, 제거 뒤 advance0·원 상태 고정,
forged 상태/선언·단위/범위/용량 거부와 기존 관련 회귀다.
