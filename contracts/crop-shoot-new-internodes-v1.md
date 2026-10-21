# 출현 사건에서 새 절간 길이 상태 생성 — 연구 v1

상태: 새 절간 합성 결속 새18/기존232검사 수용. [정확 기온 timeline](crop-shoot-air-event-timeline-v1.md)과
[명시 초기 절간 길이](crop-internode-length-state-v1.md)를 결속한다.
기존 기관 목록/전체 식물의 계산은 이 함수가 맡지 않는다.

`create_internodes_from_shoot_events(*, inputs)`는 `input_id`, `timeline_state`, `segments`,
`curve`, `initial_length`만 받는다. 앞선 명시 합성 계약을 따르며 단일 curve/초기 길이는
이번에 생성되는 기관에 사용할 **명시 합성 template**다. 품종/기관 rank의 실제 동일 반응을 가정하지 않는다.
곡선의 출현 나이0 초기 길이를 먼저 검사한다. 이 검사용 prototype는 기관 목록에 넣지 않는다.

같은 기온 프로그램에서 원 timeline을 계산하고 출현 사건마다 새 절간을 초기화한다.
기관 ID는 shoot/발달 원점/schedule·UTC 원점과 순번/출현 열적 문턱을 hash하여 정한다.
요청 ID/구간 분할에 따라 기관 ID가 바뀌지 않는다. 초기 길이는 상대1e-12/절대0 대조와 정규 곡선을 따른다.
출현 후 남은 기온 구간만 원 절간 적분기에 제공하고 `절간 나이=공통 끝 나이−출현 문턱`을 대사한다.
마지막 시각에 출현한 기관은 명시 초기 상태를 그대로 유지하며 가짜 길이 증가 구간을 만들지 않는다.

whole-second가 아닌 출현이 하나라도 있으면 **SUBSECOND_EMERGENCE_HOLD**로 전체 결과를 보류한다.
소수 초 반올림·원 출현 나이 reset·실제 관측으로의 표시는 없다. 다음 절간 clock 판본의 지원은 별도다.

출력은 `model_version=shoot-new-internodes-research-v1`, 합성/연구/미평가 표식,
입력/원 timeline SHA-256, `timeline_checkpoint`, `new_internodes`다.
각 항목은 `sequence`, `birth_age_exact`, `length_state`, 초기/전진 입력 SHA-256을 보존한다.
출현이 끝 시각일 때 전진 입력 SHA는 null이다. 전체 생성 결과는 UTF-8 JSON2MiB 상한이며 초과는 전체 hold다.
기존 문턱/구간/정확 문자열의 처리 상한도 유지한다.

독립 손계산 timeline의 문턱과 Decimal800 직접 logistic 끝 길이를 대사한다.
끝 시각/flat기온·윤일·분할 후 기존 기관만 별도 전진한 결과·동일 ID/정확 나이/길이,
초기 불일치/곡선·단위·소수 초 보류와 입력 불변·기존232검사/6root를 확인한다.
저장·현재 권리/전체 기관 목록·줄기 길이/키·3D·생식기관·품종 계수와 G0–G4는 별도다.

[원 수용/첫 시험 입력 수정 기록](../research/crop-shoot-new-internodes-20261021.md).
