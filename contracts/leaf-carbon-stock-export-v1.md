# 저장 C_i/a/A 결과의 strict export — 연구 v1

상태: 합성 연구 소프트웨어 수용 — [20검사·독립102시점/두 출력552파일](../research/leaf-carbon-stock-export-20261025.md). [수용된 저장 경로](crop-leaf-carbon-stock-artifact-v1.md)의 외부에서 신뢰한 root만 내보낸다.
`research/export-leaf-carbon-stock-replay.py`의 `export(directory,root_sha256,output)`을 사용한다.
새 서비스/계산을 추가하지 않고 생장/재개/producer를 import하거나 호출하지 않는다.

자체 source 선언의 use/display/redistribute=True를 출력 디렉터리 생성 전과 index 게시 전에 확인한다.
private False는 거부하고 원 자료/메타데이터를 보존한다. 공개 자체 합성 예시는 별도 선언·새 root여야 한다.
입력·모델/profile·notice에 대한 실제 농장 권리나 G0–G4 승인을 발급하지 않는다.

새 절대 nonsymlink 디렉터리는 원 저장소/하위/상위와 겹치지 않고 소유자·그룹/쓰기 정책을 따른다.
원 root.json/source/NOTICE.txt·checkpoint-i.json과 계산 없는 원 frame-i.json을 bytes/SHA/길이와 함께 내보낸다.
입력/source/DTO/index 2MiB, 원 raw checkpoint 512KiB와 512frame 이하·원 scalar/시간 한도를 유지한다.
schema_version=`leaf-carbon-stock-public-fixture-v1`의 index는 원 source/권리/notice·모든 CP/DTO·원 정확 격자/ID/단위를 결속한다.
원 source/current file policy·원 bytes/출력 file set/identity·exporter code를 재확인하고 index를 마지막에 게시한다.
부분 실패에서 index를 게시하지 않으며 기존 디렉터리/원 저장 객체를 덮어쓰지 않는다.

수용: 6조건/102frame의 모든 source/CP/DTO bytes·hash·권리/notice·반복 출력 일치를 대사한다.
private False 사전 거부/원 metadata 보존, 늦은 권리·원본/code/출력/디렉터리 변조와 쓰기/게시 실패,
source/상위/하위/기존/symlink 출력 거부·1/512잎/동적 장부·상한을 확인한다.
별도 프로세스에서 무생장 import·DB/CLI/network0과 출력 외 쓰기0·원 private168blob/4root/WSL 보존을 계측한다.
strict SDK와 같은 상태3D는 후속이며 C_i로 면적/키/과실을 추론하거나 시간 보간하지 않는다.
