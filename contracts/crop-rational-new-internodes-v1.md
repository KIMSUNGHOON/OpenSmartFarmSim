# 정확 출현 사건에서 새 절간 상태 — 연구 v1

상태: [450검사/독립22길이 수용](../research/crop-rational-new-internodes-20261022.md).
기존 [timeline](crop-shoot-air-event-timeline-v1.md)과
[유리수 길이 상태](crop-rational-internode-length-state-v1.md)의 후속이다.

`create_rational_internodes_from_shoot_events(inputs=...)`는 닫힌
`input_id,timeline_state,segments,curve,initial_length`를 받는다. timeline/whole-second UTC AIR
forcing과 명시 synthetic 곡선·F(0) 초기 길이는 기존 계약대로 검증한다.
기존 v1의 소수 초 hold를 바꾸지 않고 별도 판본으로 만든다.

`rational_air_segments_from_utc(time_origin_utc=...,segments=...)`는1–512개의 닫힌
`start_utc,end_utc,air_temperature`를 같은 whole-second UTC 원점으로부터 정확 초에 옮긴다.
원점≤시작, 연속/전진·finite degC를 검증한다. 온도 차/열적 나이를 계산하지 않는 형식 adapter다.
이 함수의 판본은 `whole-second-utc-to-rational-air-segments-research-v1`이다.

각 새 기관은 timeline의 정확 출현 offset을 그대로 사용한다. 남은 forcing은 정확 Fraction에서
출현 시각으로 자르며 끝 출현이면 초기화만 한다. 시계 원점은 shoot started_at이며 근사 출현 UTC는 없다.
각 기관 끝 나이=shoot 끝 나이−출현 나이를 검사한다.
ID는 기존 의미(shoot/development_origin/schedule/started_at/sequence/출현 나이)의 SHA로 만든다.
분할 호출/다른 요청 ID에도 같은 기관이며 whole-second 기존 ID와 대응한다.
이는 phytomer 출현의 연구 절간 해석이며 잎/꽃/화방·생산량을 추론하지 않는다.

출력은 `model_version=shoot-rational-new-internodes-research-v1`,
`scope=software_research_only,claim_scope=synthetic_crop_math_only,gates=not_assessed`,
입력/하위 timeline 지문·원점/adapter 판본, timeline checkpoint와 sequence/출현 나이·새 길이 상태/초기화·전진 지문 목록이다.
결과 전체는2MiB 이하다. 새 기관만 반환하며 기존 기관 목록/전체 키·저장/3D/농장 custody는 다음이다.

수용: 기존 독립6프로그램의 whole-second ID/길이/정확 나이 대응,1/3·2/3초 출현/끝 사건·변온/정체,
독립 Decimal 길이·원점 결속/분할 재개·형식/초기값/용량 hold와 입력 불변, 기존423검사/6root다.
실제 Axiany 계수/기관·독립 측정 확보와 게시 관문은 별도다.
