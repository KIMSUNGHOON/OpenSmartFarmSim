# 같은 시점의 명시 전체 잎 제거 — 연구 v1

상태: 계약/검증 중. [원문 경계](../research/crop-declared-leaf-removal-primary-sources-20261024.md)와
[기존 population](crop-leaf-population-v1.md)을 사용한다. 기존 판본·사용자 runtime은 변경하지 않는다.

`initialize_leaf_removal(inputs={input_id,population_state})`는 기존 정규화기로 검증한 같은 시점의
전체 population snapshot을 새 `declared-leaf-removal-point-research-v1` state에 보존한다.
state는 model_version/population_snapshot/population_snapshot_sha256/removals/removals_sha256이다.
최초 removals는 빈 목록이다. snapshot의 원점/정확 초·초기 anchor·출현 선언/목록은 남는다.

`apply_leaf_removals(inputs={input_id,state,events})`는 해당 시점의 명시 사건만 처리한다.
event는 schema_version=`declared-whole-leaf-removal-event-v1`, origin=`synthetic`, action=`remove_whole_leaf`,
event_id/leaf_id/time_origin_utc/at_elapsed_seconds_exact의 닫힌 객체다. ID는 기존 제한을 따른다.
사건의 원점·기약 분수 초는 snapshot과 같아야 한다. 입력 순서로 전체 잎만 제거하며 시각을 전진하지 않는다.
미존재/이미 제거된 잎·재사용 event ID, 다른 시점/원점·출현 전·다른 action/부가 필드는 거부한다.

제거 기록은 declaration/declaration_sha256/last_leaf_state_sha256이다. 마지막 상태는 보존된 snapshot의
해당 leaf state와 결속되므로 같은 큰 객체를 다시 저장하지 않는다. 순서 있는 기록 전체의 SHA도 확인한다.
정규화는 기록과 snapshot/시계·마지막 상태를 대사한다. 해시는 자기 일관성 검사이며 인증된 이력·권리 증명이 아니다.
일관되게 새로 작성한 입력의 출처/이력 승인은 후속 farm authority/서명 단계의 책임이다.

출력은 state/input_sha256, snapshot_leaf_count/active_leaf_count/removed_leaf_count/new_removed_leaf_count,
원 snapshot 순서의 active_leaf_ids와 snapshot_leaf_area/active_leaf_area/removed_leaf_area다.
세 면적은 `m2`이며 기존 finite `fsum`을 재사용한다. 별도 부분합의 부동소수점 반올림을 정확 수지로 위장하지 않는다.
마지막 잎 제거 후 active_leaf_ids는 빈 목록, active_leaf_area는0이다. 전체 snapshot과 제거 이력은 지우지 않는다.
빈 사건 목록은 같은 state를 반환한다. 같은 순서의 사건을 같은 시점에서 나눠 적용하면 마지막 state/합계가 같다.
닫힌 입력/출력의 기존2MiB·전체 잎/사건512 상한을 유지하며 초과 상태를 부분 결과로 반환하지 않는다.

기존 anchor/면적 상태 정규화는 실행하지만 forcing/시계 전진·생장 적분·DB/CLI는 호출하지 않는다.
과거/미래 관리 사건의 적용, 자연 노화·적엽 필요성/순서 예측, 면적→LAI/탄소·수확량 변환은 없다.
software_research_only/synthetic_crop_math_only/not_assessed를 유지한다.
수용은 독립 기존 참조 면적/합계, 마지막 잎·초기/새 잎/분수 초·같은 시점 분할과 기록/입력 불변,
삭제/변조·단위/시계·용량 거부 및 관련 회귀다. 새 저장/같은 UTC3D와 실제 품종·독립 자료는 후속이다.
