# 조달된 새 잎 저장 결과의 strict export — 연구 v1

상태: **합성 strict export 수용** — [21검사·fresh114시점/동일648파일](../research/leaf-funded-birth-export-20261026.md). [수용한 저장/조회](crop-leaf-funded-birth-artifact-v1.md)의 신뢰한 root를
`research/export-leaf-funded-birth-replay.py`의 `export(directory,root_sha256,output)`으로 내보낸다.
생장/조달점/재개/producer를 import/호출하지 않는다.

source 권리의 use/display/redistribute=True를 출력 생성 전과 index 게시 전에 확인한다.
private False는 사전 거부한다. 공개 예시는 별도 자체 공개 선언·새 합성 원본/새 root로 준비하고
기존 private False132blob의 권리/bytes/metadata를 보존한다. 원 패킷의 권리 플래그를 올리지 않는다.
실제 농장 자료/기상·시장 자료의 권리나 G0–G4 승인을 발급하지 않는다.

새 절대 nonsymlink 출력은 원 저장소/상·하위와 겹치지 않고 기존 경로를 덮어쓰지 않는다.
소유 output directory FD를 고정하고 매 write/read/publish 때 현재 path/inode·owner/group/mode/ACL을 확인한다.
파일은 그 FD에 상대적으로 exclusive/nofollow로 만들고 원 bytes/hash/길이·단일 링크/정책을 재확인한다.
source·출력·exporter code를 최종 확인한 뒤 .index.pending→index.json을 같은 directory FD로 rename/fsync한다.
부분 실패에서는 index를 게시하지 않는다. 계산과 새 서비스/DB/키를 추가하지 않는다.

원 root.json/source-*.json/NOTICE.txt와 event-i.json/context-i.json,
checkpoint-i.json/계산 없는 frame-i.json을 그대로 내보낸다.
새 index schema=`funded-leaf-public-fixture-v1`는 원 권리/코드/profile/notice,
source/point/context·CP/DTO 지문·global step/exact 시각/phase/event_sequence를 결속한다.
source/root/DTO/index2MiB·원 raw CP1MiB와 기존512frame/32,768scalar/600초 한계를 유지한다.
서로 다른 같은 시각의 출현을 병합/보간하거나 C_i로 위치/키/과실/수확/마진/순위를 만들지 않는다.

수용: 원6조건의 모든 source/point/context/CP/DTO bytes·hash·권리/notice·원 수량과 2회 동일 출력을 대사한다.
private False 사전 거부·원 metadata 보존, late source/rights/code/output·directory 교체와 쓰기/게시 실패,
상/하위/기존/symlink 경로 거부·1→2/512경계를 확인한다. 별도 프로세스에서 생장 import/DB/CLI/network0,
출력 외 쓰기0과 기존 private132blob/GUI·source/protected roots/WSL을 계측한다.
strict SDK/같은 상태 실제 새 잎3D·원 clock/attachment·실제 품종/자료·G0–G4/R2와 제품 통합은 후속이다.
