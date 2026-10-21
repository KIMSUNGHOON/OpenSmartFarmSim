# 명시 초기 잎 목록과 같은 시점의 면적 합계 — 연구 v1

상태: [22집중/독립4프로그램 수용](../research/crop-leaf-inventory-20261022.md). [전용 잎 시계/면적](crop-rational-leaf-area-v1.md) 뒤의 자식이다.
초기부터 존재한다고 명시된1–512개 잎만 추적한다. 잎 수/새 출현·화방·소엽 분류나 적엽/노화를 예측하지 않는다.

`backend/app/crop_leaf_inventory.py`의 초기 입력은 input_id/time_origin_utc/at_elapsed_seconds_exact/leaves다.
각 leaf는 attachment_internode_id/initialization이고 initialization은 수용된 전용 잎 초기화 입력이다.
attachment는1–200자 ASCII 참조이며 실제 저장 줄기의 해당 ID/UTC와 결속하는 검증은 게시/reader 단계에서 수행한다.
같은 attachment의 여러 명시 잎을 생물학적 오류로 추론하지 않는다. 고유 leaf ID와 순서는 그대로 유지한다.
모든 잎은 같은 UTC 원점/현재 정확 초여야 한다. 나이·초기 곡선/기준온도는 각 잎의 명시 입력이다.

상태 버전은 `declared-leaf-inventory-research-v1`이며 필드는 model_version/origin/time_origin_utc/
at_elapsed_seconds_exact/initial_inventory/leaves다. 각 저장 leaf는 attachment_internode_id/state다.
initial_inventory는 초기 현재 초와 순서대로 선언한 leafID/attachment 목록을 보관한다.
정규화는 원 목록과 동일한 ID/순서/참조·각 잎의 clock/area anchor·같은 시점을 확인한다.
순수 일관성 검사이며 변경 이력/원 관측의 인증은 별도다.

`advance_leaf_inventory`는 input_id/state/segments를 받아 같은 명시 공기 구간으로 각 잎을 전진한다.
count/참조·원 목록은 바꾸지 않는다. output은 연구/합성/미평가·입력 SHA/state와
tracked_leaf_count/tracked_leaf_area(m2), 전진에는 per-leaf 변화와 tracked_area_change(m2)를 추가한다.
합계는 추적 잎의 면적이며 LAI·농장 전체/탄소 모델의 잎 면적을 대신하지 않는다.
양수 면적의 합계가 비유한이면 hold이며 결과/정규화 상태가2MiB를 넘으면 hold다.

## 수용

제품 부재 RED 뒤 독립 고정 Fraction/Decimal의 개별 면적·합계/변화와 같은 정확 나이/초를 대사한다.
분할 같은 상태/원 목록, 고유ID·시점/원점 혼합·참조 변조/단일 추가·삭제/재정렬과512/513·합계 overflow를 확인한다.
기존 source/원7root·자료/동결3D와 WSL 상한을 유지한다.
새 잎 사건/관리·줄기 참조의 실제 게시 결속·불변 저장/계산 없는 조회/같은 UTC3D와 실제 품종/관문은 후속이다.
