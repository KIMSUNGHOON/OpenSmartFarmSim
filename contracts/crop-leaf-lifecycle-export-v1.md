# 불변 잎 생애 결과의 연구 export — v1

상태: 계약/검증 중. [불변 결과/reader](crop-leaf-lifecycle-artifact-v1.md)를 사용한다.
`research/export-leaf-lifecycle-replay.py`의 `export(directory,root_sha256,output)`은 신뢰된 private root의
자체 합성 자료만 내보낸다. 농장 SourceRecord/계정 권한·서명/G0나 제품 Run 게시 승인은 아니다.

원 appearance/관리/stem의 use/display/redistribute=True를 각각 확인한다. 권리3종은 별도로 보존하며
내부 조회에 허용된 redistribute=False를 공개 허가로 바꾸지 않는다.
기존 output을 덮어쓰지 않고 source 내부에도 작성하지 않는다. 생장/준비/producer import·재계산·DB/CLI/network0이다.

원 canonical bytes의7파일은 root.json/input.json/management.json/preparation.json/initial-state.json/
stem-root.json/stem-input.json이다. 각 path/sha256/bytes를 sources에 담는다.
원 `leaf-lifecycle-replay-frame-v1` DTO는 frame-0.json…으로 저장하며 current/last·active/removed/pending,
UTC/기관 ID/나이/면적/개수·같은 UTC stem과 display policy를 그대로 보존한다.

완료 index schema는 `leaf-lifecycle-public-fixture-v1`이다. scope/claim_scope/gates·time_kind/parameter_scope,
model_versions/display_policy·artifact_sha256·두 program/preparation/initial_state/stem root/program SHA,
source_rights3종과 sources/frames를 가진다. frame descriptor는 index/at/path/sha256/bytes,
result_sha256/input_state_sha256/state_sha256/input_sha256/stem_result_sha256이다.
각 파일은2MiB 이내며 원 최대64시점이다.12시점이면7원문+12frame+index로20파일이다.

원 manifest/권리·모든 source/result bytes와 작성한19파일의 길이/hash를 마지막에 확인한다.
output 디렉터리 identity/owner/mode와 파일 목록도 확인한다. index는 임시 파일을 fsync/rename해 마지막에 게시한다.
권리 거부·늦은 원본/권리·출력 변조·부분 쓰기/rename 실패는 완료 index0이다.
부분 파일은 승인된 묶음이 아니다. 같은 root를 다른 새 output에 내보내면 모든 bytes/index SHA가 같다.

수용은 실제 두31blob 결과의 각12 DTO/47상태·원 SHA/UTC/권리3종·20파일 동일성,
재배포False/늦은 변경/부분 실패·입출력 경계, 별도 fresh 프로세스의 생장 import/재계산·DB/CLI/network0,
출력 밖 쓰기0·원62파일/기존 자료·화면/WSL 보호다. strict SDK/같은 UTC3D는 별도 후속이다.
