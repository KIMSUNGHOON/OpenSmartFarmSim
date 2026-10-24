# 제거 전·직후·다음 구간의 불변 저장과 무계산 조회 — 연구 v1

상태: [81신규/89관련·fresh12root/216시점 수용](../research/growing-geometry-removal-artifact-20261024.md).
[실제 다음 구간](growing-geometry-removal-next-interval-v1.md)의 저장/조회 자식이다.
기존 CAS MorphologyBlobStore/ContentAccess와 원 growing-geometry 형식의 단위/구조 검사를 재사용한다.
새 DB/키·서비스나 기존 저장 형식/코드 변경은 없다. 실제 farm/서명 custody·G0–G4와 과학 검증은 별도다.

## 원 입력과 producer

`produce_removal_artifact(directory,access,*,inputs_raw,**profiles)`는 닫힌 원 JSON을 받는다.
schema_version=`growing-geometry-removal-artifact-input-v1`, input_id, origin=`synthetic`,
rights, time_origin_utc, step_seconds, step_count, program, event_step_index, point_inputs다.
앞의 원 program/권리/명시 합성 epoch·격자는 기존 artifact 계약을 따르며 새 입력의 모든 필드를 별도로 결속한다.
event_step_index는 bool 제외0..count 정수다. point_inputs는 이미 정의한 원 current C 분포/제거 C·용량/현열·정확 시각과
원 parent context/사건 직전 CP SHA를 가진 명시 제거 입력이다. 입력을 수정해 SHA/질량을 채우지 않는다.
원/새 scalar 한도32,768·600초·512잎·각 source/root2MiB/CP256KiB·기존64MiB/4,096파일 저장 한도를 유지한다.

producer는 원 parent를 초기화하고 사건 index까지 한 번 전진하며 각 원 CP를 저장한다.
제공한 point_inputs의 원 context/현재 CP를 검증해 post-context/point를 만들고, 새 engine을 완료까지 전진해 각 CP를 저장한다.
원 parent의 사건 후 미사용 구간을 계산하지 않는다. reader에서 이 과정을 재실행하지 않는다.
point 입력/결과와 parent request/program/context/seed, post program/context/seed/snapshot,
원4profile raw bytes/metadata와 Clear BSD notice를 불변 blob으로 보존한다.
입력/코드·프로필/권리/모든 원 bytes를 재확인한 뒤 completed root를 마지막에 저장한다.
부분 실패/hold는 완료 root를 반환하지 않으며 중간 blob을 승인된 결과로 표시하지 않는다.

전체 sample 수는 count+2다. index0..event는 `before_removal`이며 원 global index를 가진다.
다음 index는 `after_removal_before_next_step`이고 바로 앞과 **같은** global index/정확 시각이다.
나머지는 `post_removal_interval`이다. 새 local/global index·phase·정확 Fraction 경과 초와 원 float elapsed를 보존한다.
root는 전체 순서/이전 CP·sample/state SHA·source/모델/코드·권리와 양쪽 context/point 지문을 결속한다.
합성 epoch를 실제 관측이나 반올림한 UTC로 바꾸지 않는다.

## reader

`read_removal_manifest(directory,access,root_sha256)`와
`read_removal_frame(directory,access,root_sha256,*,index)`는 신뢰한 private root만 받는다.
reader는 생장/point/post-context/continuation/producer를 import/호출하지 않는다.
파일/권리·code/hash·닫힌 schema/단위/shape·원 source/context/영수증·진단/수지 범위와 양쪽 prefix를 검사한다.
실제 방정식이나 생장·질량/열을 다시 계산하지 않으며 DB/CLI/network/쓰기0이다.
현재 파일 정책·source rights/code를 반환 직전 다시 확인한다. 실제 tenant/farm 현재 권리·서명은 후속이다.
자체 재해시된 임의 graph의 진본이나 생물학적 정확도를 증명하는 경계가 아니다.

frame DTO는 원 sample/CP bytes의 state·기후/derived·원 leaf ID/현재 a/A·해당 원 영수증/curve SHA,
양쪽 state layout와 정확 at/phase·global index·원 수지/장부를 그대로 투영한다.
사건 전의 point/segment 장부는 `null`로 표시한다. 사건 후에는 원21·사건·새 segment21을 각각 표시한다.
원 전체 D0/초기 영수증·현재 active D0와 removed last state는 원 source와 결속하며 새 면적/시간 보간/과실·키를 만들지 않는다.
모든 view는 복사본이며 잘못된 index/단위/shape/시각/phase/source/권리·변조/상한/늦은 변경을 거부한다.

scope=`software_research_only`, claim_scope=`synthetic_growing_geometry_removal_replay_only`,
G0_G4=`not_assessed`, status=`completed_software_fixture`, time_kind=`synthetic_model_clock_not_observation`다.
geometry authority는 stored leaf area이며 줄기/attachment/pose는 별도 제작 자산이다.
실제 품종·작기/생산·자원/경제/추천과 R2를 이 저장 fixture로 승인하지 않는다.

수용은 합성6조건의 모든 pre/event/post CP·DTO bytes/원 수량·ID/a/A/정확 시각·각 장부와 같은 시각의 다른 phase,
초기/중간/완료 사건·한 잎/동시 제거·분수 dt, 동일 입력/새 디렉터리의 같은 root,
권리/단위/해시/코드·원 graph/late file policy·수지/부분 쓰기/hold·상한/index/FD/원 자료/4root/WSL이다.
별도 reader 프로세스에서 계산 모듈 import·성장/제거/재개 호출0, DB/CLI/network/쓰기0을 확인한다.
strict export/SDK/같은 phase의 사실적3D는 다음 단계다.
