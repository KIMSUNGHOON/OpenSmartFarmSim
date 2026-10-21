# 유리수 출현 시각의 절간 길이 상태 — 연구 v1

상태: [423집중 검사/독립5길이 수용](../research/crop-rational-internode-length-state-20261022.md).
[정확 기관 시계](crop-rational-morphology-clock-v1.md)와
[길이 point](crop-internode-length-point-v1.md)를 재사용한다. 기존 whole-second 상태의 판본을 바꾸지 않는다.

`initialize_rational_internode_length(inputs=...)`의 닫힌 입력은
`input_id,clock_state,curve,initial_length {value,unit:m}`다. 시계/곡선은 명시 synthetic다.
초기 길이는 같은 정확 나이의 canonical F(a)와 relative1e-12/absolute0으로 일치해야 한다.
요청 길이는 anchor 영수증에 남기고 현재 길이는 canonical 값으로 저장한다. 자동0/기본 곡선은 없다.

상태의 닫힌6필드는 `model_version,clock_state,curve,curve_sha256,length,anchor`다.
anchor의 닫힌4필드는 `clock_state,curve_sha256,requested_length,canonical_length`다.
정규화 때 현재/초기 F(a), 곡선 지문, 같은 기관/원점/출현·기준온도를 확인한다.
현재 경과 초/나이는 anchor보다 작을 수 없고 경과 초가 같으면 나이도 같아야 한다.
초기 이력을 인증하는 서명/custody는 이 순수 상태의 범위 밖이다.

`advance_rational_internode_length(inputs=...)`는 `input_id,state,segments`만 받는다.
현재 상태 검증→정확 유리수 시계 전진→끝 나이의 canonical point 순서다.
같은 forcing의 분할/전체 전진은 같은 최종 state/anchor를 갖는다.
시간 원점과 유리수 경과 초를 보존하며 근사 UTC/출현 시각은 만들지 않는다.
양 끝 float 길이 차를 ΔL로 게시하지 않으며 증가량 적분 영수증을 암시하지 않는다.

envelope는 `model_version=internode-rational-length-state-research-v1`,
`scope=software_research_only,claim_scope=synthetic_crop_math_only,gates=not_assessed`,
정규 입력 SHA, state와 사용한 point/clock 판본·입력 지문이다. 요청 ID/전진 영수증은 state 밖에 둔다.
점 길이의 finite normal binary64/최대 M 수치 경계와 시계의 단위/정확 분수·구간/용량 보류를 유지한다.

수용: 독립 Decimal F(a)·1/3초 출현/변온·분할 동일 state·명시 초기값/기관/곡선/anchor 변조 보류,
입력 불변/결정적 지문, 기존385검사와6root/WSL 상한이다.
새 기관 adapter/목록·새 저장 판본/계산 없는 조회·같은 UTC3D는 다음 자식이다.
기존 v1의 소수 초 hold와 공개12프레임은 수용 후에도 그대로 둔다. 실제 품종/생산·관문 수용이 아니다.
