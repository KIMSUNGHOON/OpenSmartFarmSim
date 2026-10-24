# 불변 잎 생애 결과와 계산 없는 조회 — 연구 v1

상태: [소프트웨어 범위 수용](../research/crop-leaf-lifecycle-artifact-20261024.md). [입력 결속](crop-leaf-lifecycle-preparation-v1.md)의 두 원문과 준비 결과를 사용한다.
기존 artifact/reader/runtime을 바꾸지 않는 별도 `leaf-lifecycle-research-artifact-v1`이다.

`produce_leaf_lifecycle_artifact(directory,access,*,stem_directory,appearance_program_raw,management_raw)`는
서로 다른 source/target 디렉터리와 기존 ContentAccess/MorphologyBlobStore를 사용한다.
준비 결과·원 appearance/관리 bytes·원 stem graph·초기 lifecycle state를 그대로 보관한다.
원 stem sample UTC/기관 ID 순서에서 producer만 lifecycle을 전진한다.
각 결과는 원 입력 state SHA/실제 입력 SHA/출력 state SHA·원 stem result SHA와 byte 수에 결속한다.
원 준비/원본·현재 file policy·코드를 전후 검사한 뒤 완료 manifest를 마지막에 저장한다.
중간 실패는 완료 root를 게시하지 않는다. 별도 농장/서명/Run custody는 후속이다.

manifest는 scope/claim/gates·시간/매개변수 범위·model/display policy,
두 program SHA/bytes·preparation SHA/bytes·source_rights3종,
stem root/program·code_sha256·원점/초기 정확 초·초기 state SHA/bytes·terminal state SHA·samples다.
각 sample은 index/at/result_sha256/result_bytes/input_state_sha256/state_sha256/input_sha256/stem_result_sha256다.
입력/초기 state/결과/manifest를 각각 구분하며 입력 및 결과의 기존 bytes·개수 한도를 유지한다.
관리 redistribute=False를 True로 합치지 않는다. 최대64MiB/4096파일의 기존 file store 한도도 유지한다.

`read_leaf_lifecycle_manifest(directory,access,root_sha256)`와
`read_leaf_lifecycle_frame(directory,access,root_sha256,*,index)`는 신뢰된 private root를 받는다.
서명/농장 권한을 새로 부여하지 않는다. 생장/준비 모델을 import/호출하지 않으며 DB/CLI·파일쓰기0이다.
원 stem typed reader와 단위/schema/hash·고정 정책/선언 검증만 사용한다. 저장된 면적을 재계산하지 않는다.
원 준비의 source/generated/initial/derivation·정확 forcing과 source 권리3종을 원 graph에 대사한다.
manifest는 source graph/descriptor 지문을 검증하며 선택한 frame에서 state의 원 초기/출현/제거 선언·receipt/시각·개수/면적 합계를 검증한다.
source/결과 graph를 반환 전 재검사하여 늦은 권리·원본/페이지 변경을 보류한다.

frame은 `leaf-lifecycle-replay-frame-v1`과 원 artifact/result/input SHA·index/원 UTC/원점/정확 현재 초,
declared/tracked/active/removed/pending 수와 scheduled/emerged 수·면적3종,
active_leaves/removed_leaves/pending_leaves·같은 UTC stem·두 program/preparation SHA·display_policy다.
active_leaves는 그 frame의 현재 잎이며 원 attachment/leaf ID·출현/나이·면적/curve SHA를 그대로 제공한다.
removed_leaves는 마지막 면적/나이와 `last_at_elapsed_seconds_exact`·제거 선언을 보존한다.
pending_leaves는 예약 ID/부착·정확 출현 초만 제공하고 현재 면적/형상을 만들지 않는다.
3D는 active만 사용한다. removed/last_tracked 합을 같은 시각 수관 면적이나 LAI/질량으로 표시하지 않는다.

수용은 무제거 원12시점/47상태·제거 독립 나이/면적/합계·분할/재실행·원 code/자료 보존,
재지문을 붙인 변조·현재/늦은 권리·코드/원본·저장 실패/완료0·용량·입력 불변,
독립 producer/무계산 reader의 원 bytes/UTC·성장 import/전진·DB/CLI/쓰기0이다.
software_research_only/synthetic_crop_math_only/not_assessed를 유지한다.
실제 품종/독립 검증·생산/자원/경제·농장/HTTP/SDK/제품3D와 관문은 후속이다.
