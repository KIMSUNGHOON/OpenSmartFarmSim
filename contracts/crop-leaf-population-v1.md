# 기존 잎과 명시 새 잎의 목록 — 연구 v1

상태: [새43/관련137·독립26면적 수용](../research/crop-leaf-population-20261022.md). [초기 inventory](crop-leaf-inventory-v1.md)가 아니라 [명시 출현](crop-declared-leaf-births-v1.md) 뒤의 새 판본이다.
기존 v1/원40blob·사용자 화면은 유지한다. 자동 출현·관리/노화·품종 분류/예측은 없다.

`initialize_leaf_population`은 input_id/initial_inventory만 받으며 기존 초기 inventory 입력을 그대로 초기화한다.
state는 model_version/time_origin_utc/at_elapsed_seconds_exact/initial_inventory_state/new_leaves/birth_inventory다.
원 초기 inventory anchor는 그대로 유지하고 새 잎은 개별 출현 시각의 leaf clock/area anchor를 유지한다.
새 item은 declaration/declaration_sha256/state다. 원 event 선언 hash와 나이0 초기화·현재 상태의
ID/원점/곡선/정규화/초기면적/출현·기준온도를 대사한다. hash가 인증/권리·관문 승인을 뜻하지 않는다.
birth_inventory의 leaf ID/선언 SHA와 현재 새 잎 목록을 대사해 독립 추가/제거를 거부한다.
새 잎 순서는 출현 순서(동시 허용)이며 초기 선언 이후 출현한 잎만 받는다.

`advance_leaf_population`은 input_id/state/segments/births만 받는다.
원 초기 잎과 이미 출현한 잎은 같은 전체 forcing으로 전진한다.
이번 (현재,끝]의 명시 사건만 새 잎을 만들고 남은 forcing으로 전진한다.
전체 초기/새 leaf ID는 유일하며1–512개, 모든 현재 시각과 원 UTC는 같아야 한다.
출력 tracked_leaf_area는 전체 현재 면적의 m2 합계다. 차분을 광합성/탄소량으로 변환하지 않는다.
별도 new_leaf_count는 이번 사건 수이며 누적 전체 잎 수를 대신하지 않는다.
모델 `declared-leaf-population-research-v1`, 연구/합성/관문 미평가 표식을 유지한다.
전체 입력/출력2MiB 상한을 둔다. empty 초기 inventory·적엽/노화는 지원하지 않는다.
실제 stem 존재/부착 가능 시각 검증·서명/불변 저장·같은 UTC3D는 후속이다.

수용: 부재 RED→독립 Fraction/Decimal의 초기/새 면적·정확 시계/개수·합계,
선정한 내부 분할/분수 초·전환/끝/동시 경계의 같은 state·추가/제거/중복/변조·범위/단위/초기조건 hold,
입력 불변·512/513·2MiB와 원7root/자료·동결 화면/WSL 상한을 확인한다.
실제 Axiany 계수/초기관측·독립 현장 자료는 별도이며 G0–G4를 진행시키지 않는다.
