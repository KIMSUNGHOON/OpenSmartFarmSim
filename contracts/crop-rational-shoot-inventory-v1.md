# 기존·새 절간의 정확 시각 목록 — 연구 v1

상태: [473검사/독립34길이·6합계 수용](../research/crop-rational-shoot-inventory-20261022.md).
[새 기관 adapter](crop-rational-new-internodes-v1.md) 후속이다.
`advance_rational_shoot_internode_inventory(inputs=...)`는 닫힌 `input_id,state,segments`를 받는다.
state의 닫힌 필드는 `timeline_state,inventory_start_sequence,internodes,emergence_profile`다.
기존 목록과 별도 판본이며 기존 v1/공개 저장을 자동 변환하지 않는다.

명시 시작 순번은0..2^31−1 정수이고 목록은512기관 이하다. 각 기관의 닫힌 필드는
`sequence,birth_age_exact,length_state`다. 시작+목록 수=timeline next_sequence, 각 순번은 연속/정렬되어야 한다.
기관의 정규 유리수 길이 state·고유 ID, 같은 shoot UTC 원점·현재 경과 초/기준온도를 검증한다.
기관 나이=shoot 현재 나이−출현 나이이며 출현 나이와 정확 출현 초는 각각 비감소 순서여야 한다.
초기/현재 상태의 실제 관측/서명 이력 인증은 이 순수 계산 밖이다.

emergence_profile의 닫힌 필드는 명시 synthetic `curve,initial_length`다.
새 기관 adapter를 검증하고 기존 기관을 같은 원 UTC forcing의 정확 초로 전진시킨다.
새/기존 기관을 합친 수는512 이하며 ID 중복/기관 나이 수지 불일치는 hold다.
최종 state에는 요청별 영수증을 넣지 않아 같은 forcing의 분할/전체 전진이 같은 state가 된다.
step_receipts에는 기존 전진/새 초기화·전진의 실제 입력 지문을 남긴다.

결과는 model_version=shoot-rational-internode-inventory-research-v1,
scope=software_research_only/claim_scope=synthetic_crop_math_only/gates=not_assessed,
정규 입력·하위 판본 지문, state/step_receipts와 `tracked_axis_length {value,unit:m}`다.
축 합계는 fsum의 유한 결과이며 overflow를 hold한다. 전체 결과2MiB 상한을 적용한다.
이 합계는 추적된 절간 축 길이이며 실제 키·총 식물 구조/잎/생산량이 아니다.

수용: 기존 독립5프로그램/22길이·5합계 대응, 소수 초 출현 뒤 기존 기관과 재개/독립 Decimal 합계,
원점/나이/순서·고유 ID/anchor 변조,512/513기관·합계 overflow/2MiB·입력 불변,
기존450검사/6root다. 새 저장 판본·계산 없는 조회→같은 UTC3D는 다음이며 실제 품종/농장 관문은 유지한다.
