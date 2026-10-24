# 원 출현/줄기와 관리 선언의 생애 입력 결속 — 연구 v1

상태: 계약/검증 중. [생애 계산](crop-leaf-lifecycle-v1.md)을 기존
[출현 프로그램](crop-leaf-appearance-program-v1.md)의 원 준비 결과에 결속한다.
기존 판본/실행·저장/화면은 바꾸지 않는다.

별도 canonical 관리 JSON은 schema_version=`leaf-lifecycle-management-program-v1`, origin=`synthetic`,
program_id/rights/appearance_program_sha256/removals/display_policy의 닫힌 객체다.
rights는 기존 명시 소유 합성 권리 schema이며 내부 준비에는 redistribute=False도 허용한다.
원 appearance bytes의 SHA가 같아야 한다. removals는 기존 whole-leaf schema의0–512개이며
원점/정확 초·고유 leaf/event ID를 검사한다. display_policy는 active만의 현재 수/형상,
pending 제외·제거 마지막 상태 보존을 명시하며 기존 제작 외형/면적 범위는 그대로다.
parser는 생장 모델을 import/전진하지 않는다. 실제 leaf ID/출현/기간은 다음 준비에서 검사한다.

`prepare_leaf_lifecycle_program(stem_directory,access,*,appearance_program_raw,management_raw)`는
기존 appearance preparation을 그대로 수행하고 원 source/generated/initial/derivation SHA,
초기 부착/자동 출현 선언·stem root/program/원점/정확 forcing을 유지한다.
같은 원 준비 결과에서 초기 population과 lifecycle 초기 입력/상태 SHA를 만든다.
원 출현과 관리의 권리를 합치거나 추정하지 않으며 stem 권리도 별도 보존한다.

제거 대상은 원 초기 잎/자동 출현 잎이어야 한다. 출현 전 제거·원점 차이·다른 appearance SHA는 거부한다.
제거 시각은 원 준비의 leaf forcing 시작~끝 안이어야 한다. 빈 목록도 명시한다.
기존 준비의 전 구간 초기 잎 기준온도 보류를 우회하지 않는다. 초기화/검증은 허용하며
새 lifecycle/leaf/shoot 전진·producer·DB/CLI 호출·파일쓰기는0이다.

출력은 model/scope/claim/gates/input_sha256/model_versions/code_sha256,
appearance_program_sha256/bytes·management_program_sha256/bytes/id,
appearance_preparation/appearance_preparation_sha256,
lifecycle_initialization/lifecycle_initialization_sha256/initial_state_sha256,
stem/time_origin_utc/start_elapsed_seconds_exact/end_elapsed_seconds_exact/forcing/source_rights/display_policy다.
raw와 준비 결과·초기화 입력·초기 state 각각의 SHA를 구분한다. output은2MiB 이하여야 한다.
원 준비를 전후에 대사하고 전체 호출 동안 같은 source 디렉터리를 보유한다.
원본/현재 file policy·코드·준비 결과의 늦은 변화는 반환 전에 보류한다.
현재 SourceRecord/농장 권한·서명은 후속이며 이것이 실제 자료/관문 승인을 뜻하지 않는다.

수용은 실제 원 준비 결과의 동일성·정확 forcing/ID/부착/단위·현재/늦은 권리·원본/판본·기간·용량 거부,
별도 fresh/성장 parser import0·준비 전진/producer/DB/CLI/쓰기0·입력/출력 분리·원 자료 보존이다.
software_research_only/synthetic_crop_math_only/not_assessed를 유지한다.
별도 불변 생애 결과/계산 없는 조회·농장/현재 권리 결속과 같은 UTC3D는 후속이다.
