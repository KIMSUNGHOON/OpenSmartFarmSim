# 줄기/잎 조달 뒤 같은 전역 격자의 가변 기관 재개 — research v1

상태: [신규283/관련123·12Context/24CP·독립710장부 수용](../research/crop-organ-funded-continuation-20261027.md). [개별 기관 CP](crop-stem-root-stock-continuation-v1.md)·[잎 점](crop-stem-root-funded-leaf-point-v1.md)·[절간 점](crop-stem-root-funded-internode-point-v1.md)과 [기존 잎 재개](crop-leaf-funded-birth-continuation-v1.md)의 검증 패턴을 별도 module/version으로 확장한다. 실제 품종/자동 출현/공급 제한 형상/생산·추천 승인은 없다.

`prepare_context(parent_context,raw_parent_checkpoint,expected_parent_sha256,kind,inputs,**source_selection)`는 실제 고정 Root Context/외부 신뢰 raw CP와 현재 원 crop/stem source·초기 연결을 검증하고 kind=leaf/internode의 수용한 public point를 적용한다. 원 선택/선언·Root identity/현재 source binding hash·point 전 CP/동일 시각 after state·원 dt/count·원 D0/새 초기 영수증/기관별 birth baseline·누적량·입력/권리/point 이력을 immutable bytes에 결속한다. source_selection은 두 directories/access·원 crop/stem roots/index·binding_declaration이며 공개 snapshot에 로컬 경로/자격을 넣지 않는다.

`adopt_births(context,raw_checkpoint,expected_sha256,kind,inputs)`는 새로운 typed 현재 CP를 검증한 뒤 해당 재료점 `_jump`를 호출한다. old Context/token/CP를 가장하지 않는다. 실제 현재 internode 부모·같은 floor/정확 step×dt·원 initial binding hash와 권리/입력 schema를 유지한다. 두 종류에 걸쳐 이전 event ID를 다시 차감할 수 없고 같은 시각의 다른 batch는 호출 순서/event_sequence/phase/prefix로 구별한다. root는 원 하나를 보존하며 새 internode/leaf ID는 각 목록에서 고유하다.

현재 상태를 after program으로 다시 prepare하지 않는다. 원106+3n+m의 현재 C_i/A/나이/과실·기후와 anchors/D0·원 초기 요청/새 canonical F(0)·개별 탄소의 birth C, leaf age/air-temperature integral 기준을 보존한다. 새 원가/면적→C/SLA/기본 질량을 만들지 않고 cLeafG/cStemG·명시 입력과 기존 점의 K/U 산술을 재사용한다.

`context_bytes`/`restore_context(root_context,raw_bytes,expected_sha256,crop_directory,stem_directory,access)`는 외부 신뢰 canonical snapshot SHA와 실제 Root/현재 source를 결속한다. strict closed units/범위/순서/이력·code/profile/환경/원 grid·source/권리와 영수증/초기 상태 hash를 검증하고 과거 RHS/point 재계산/초기 면적 정규화는0이다. 자체 재해시·Python 내부 필드 재작성·선언 권리는 진본/농장/G0 승인 경계가 아니다. 독립 server custody/서명은 후속이다.

`start`, `checkpoint_bytes`, `restore_checkpoint`, `advance_chunk`가 실제 재개를 제공한다. 현재 검증 RHS1회+새 걸음마다4stage, 같은 원 shared RK4/전역 시각이며 과거 전진/현재 C/A/나이 재초기화0이다. 마지막 point 전까지의 lifetime prefix와 새 segment의 적분량을 따로 보존하고 한번 더해 현재 lifetime을 파생한다. leaf/stem 새 유량은 point 이전0, 기존 leaf/stem key와 현재 inventory 순서를 보존한다. 원 root부터의 C/과실수/수관·공기 현열/물/열용량·reduced energy와 기관별 C·leaf 나이를 검사한다. stem 총 C는 별도 point 구조 유입을 반영하고 전체 C에는 점 성장호흡만 외부 유출로 반영한다. U/K는 leaf 점 유입, internode 점은0이다.

새 typed Context/CP/schema·source/code/profile hash·global index/local segment index/정확 elapsed·event_sequence/phase·원 output prefix/cursor를 결속한다. chunk 경계로 최종 CP bytes/값/장부가 바뀌면 실패다. 원/point/segment 예산과64ULP 집계만 사용하고 임의 absolute epsilon을 추가하지 않는다. 완료 CP 복원은 허용하고 더 전진할 수 없다. stage/domain/장부/late source/code 실패는 마지막 확정 prefix/sample/장부와 hold, CP=None을 남기고 미확정 후보를 발급하지 않는다. 예기치 않은 RuntimeError/취소는 정상 hold로 숨기지 않는다.

Context/response2MiB·CP512KiB·remaining32768scalar·600s/4096steps·chunk1..128·leaf/stem 각512와 모든 하위 byte cap/원 최대 요청 hold를 유지한다. 소프트웨어 이력 검증이며 자동 thermal threshold/분수 후보·형상 feedback·새 불변 결과/3D/API/worker는 후속이다. DB/CLI/network/write0, software_research_only/time_kind=synthetic_model_clock_not_observation/G0–G4=not_assessed다.

수용: 실제 원 source6조건/양쪽 point·초기/중간/완료/동일 시각 복수 채택·반복 거부, 원 state/D0/birth/권리/code/단위 보존, 실제 양쪽 core 이후의 같은 RK4, 모든 수용한 분할/최종 bytes·trusted raw context/CP 복원0replay·개별/전체/segment/point 장부·실패 prefix/late source/한도·fresh/독립 산술·원 자료/GUI/WSL 보존이다.
