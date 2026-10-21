# 명시 출현 사건의 새 잎 계산 — 연구 v1

상태: [새38/관련94·독립5프로그램 수용](../research/crop-declared-leaf-births-20261022.md). [잎 전용 시계/면적](crop-rational-leaf-area-v1.md)의 별도 순수 자식이다.
잎 출현 시각·leaf ID/부착 ID·곡선/정규화·기준온도/초기 면적은 모두 자체 합성 입력이다.
작물의 잎 출현을 예측하지 않는다. phytomer/leaf/truss 자동 분류·문턱/간격·계수 기본값은 없다.

`create_declared_leaves` 입력은 input_id/origin/time_origin_utc/segments/births의 닫힌 객체다.
origin=synthetic, 원 UTC는 whole-second Z,1–512개 forcing은 canonical 정확 초와 유한 degC의
양수·연속 구간이다. births는0–512개이며 각 객체는 leaf_id/attachment_internode_id/
emerged_elapsed_seconds_exact/base_temperature/curve/normalization/initial_area다.
출현은 forcing의 **(시작, 끝]** 안이고 시각 오름차순(같은 시각 허용)이며 ID는 중복되지 않는다.
시작 시점 기존 잎은 기존 초기 inventory의 범위다. 분할 호출자는 각 사건을 해당 반열린 구간에 한 번만 제공한다.
이 함수는 이전 호출의 사건 이력·중복을 저장하지 않으며 다중 호출 목록 결속은 후속이다.

새 잎은 원점/명시 출현 초에서 나이0으로 초기화한다. 입력 초기 면적은 명시 sigmoid F(0)와 일치해야 한다.
면적0이나 출현 전 기온 누적을 자동 적용하지 않는다. 출현 뒤 남은 기온 구간만 정확하게 잘라 전진한다.
끝 경계 출현은 초기화만 하며 advance 호출0이다. 출현 전 저온을 출현 후 저온으로 취급하지 않는다.
출현 이후 기준온도 미만·부적합 입력/단위·수치/용량은 기존 hold를 유지한다.
부착 ID의 ASCII 형식만 검사한다. 실제 stem 존재/그 시각의 부착 가능성은 이 모듈의 수용이 아니다.

출력은 model/scope/claim/gates/input SHA·원 UTC/시작/끝·new_leaves와 합계 면적이다.
각 잎은 원 부착 ID·전용 state와 초기화/전진 입력 SHA를 갖고 입력 순서를 유지한다.
버전 `declared-leaf-births-research-v1`, software_research_only/synthetic_crop_math_only/not_assessed다.
전체 입력/출력2MiB 상한·입력 불변을 요구한다.0사건은 면적 합계0이며 기존 잎 면적을 뜻하지 않는다.

## 수용 기준

모듈 부재 RED 뒤 독립 Fraction/Decimal100 참조의 출현/나이/초기·끝 면적과 원 입력 불변을 확인한다.
분수 초·온도 전환 경계·끝 경계/동시 출현·구간 분할 뒤 같은 leaf state,0사건과512/513·2MiB를 검사한다.
누락/추가 필드·순서/중복/범위·잘못된 초기면적/단위·forcing gap/역방향/기준온도 미만은 hold다.
원7root/원 자료·동결 화면과 WSL512MiB/1GiB/.25초/600초 상한을 지킨다.
기존 초기 inventory/40blob/사용자 화면은 변경하지 않는다. 저장/reader/API/새 잎3D는 별도 자식이다.
실제 Axiany 관측/계수·독립 검증은 병행 외부 의존성이고 G0–G4를 진행시키지 않는다.
