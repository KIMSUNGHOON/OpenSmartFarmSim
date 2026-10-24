# 저장 면적·기후 결과의 웹 전달 — v1

상태: [export18/SDK41·타입/fresh 수용](../research/growing-geometry-web-replay-20261024.md). 3D 수용은 후속이다. [불변 결과](crop-growing-geometry-artifact-v1.md)를 전달한다.
원 모델·private 결과를 수정하지 않으며 export→strict SDK→기존 사실적3D 순서다.

`research/export-growing-geometry-replay.py`의 `export(directory,root_sha256,output)`은
신뢰한 원 root를 기존 reader로 검사하고 자체 입력의 use/display/redistribute=True를 요구한다.
private redistribute=False를 변경하지 않는다. 별도 자체 합성 공개 선언으로 새 입력/결과를 만든다.
4프로필의 원 출처/권리/연구 범위 metadata·기존 notice를 보존하며 원 논문/PDF·그림·표의 전문은 포함하지 않는다.
실제 농장/현재 tenant 권리/서명 custody·G0 승인은 기존 상위 작업이다.

output은 새 소유 디렉터리이며 source 안/상위/같은 경로·심볼릭 링크를 거부한다.
index는 마지막에 게시한다. 원 root.json, source-{role}.json(9개 JSON), NOTICE.txt,
checkpoint-{i}.json의 원 bytes와 frame-{i}.json의 reader DTO bytes를 보존한다.
10개 source role은 inputs/request/program/seed/context/4profile/license_notice다.
17시점이면11원본+17checkpoint+17DTO+index=46파일이다. 각 파일2MiB/원 checkpoint256KiB,
원 최대512시점과 CAS 경계를 유지하며 overwrite/임의 경로를 허용하지 않는다.

index schema=growing-geometry-public-fixture-v1이다. 원 scope/claim_scope/G0_G4/status/time_kind/
parameter_scope/display_policy·artifact_sha256/input_id/source_rights·exporter_sha256,
sources(role/path/sha256/bytes), checkpoints(원 descriptor+path/sha256/bytes),
frames(index/at/context/checkpoint/sample/state SHA+path/sha256/bytes)를 가진다.
정확 at/원 elapsed/leaf ID/a/A/114상태/21장부를 그대로 전달한다. 초기화/생장/재개 import·계산/DB/CLI/network0이다.
작성 파일/디렉터리 정책·모든 원 blob/권리/원 root를 마지막에 재확인한다. 실패는 완료 index0이다.
같은 root를 새 output에 다시 export하면 bytes/index SHA가 같다. 부분 파일은 완료 묶음이 아니다.

SDK는 고정 자체 합성6개 사례의 index/root 지문을 코드에 pin하고 요청 중단·무자격 no-store GET·redirect 거부/파일2MiB를 유지한다.
source/CP/DTO의 모든 raw bytes 길이·SHA와 role/path·원 root/context/seed·권리/정확 grid·원 leaf IDs/상태/layout/단위/범위를 대사한다.
DTO의 sample/누적량/수지/초기 영수증·투영을 원 CP/source와 대사한다. 저장값을 보간/재계산하지 않는다.
자가 재해시 임의 index는 허용하지 않는다. 이것은 signed farm Run의 신뢰 체계를 대체하지 않는 고정 연구 fixture 소비자다.

수용: 여섯 원 프로그램의6×17시점·원 bytes/권리/프로필/notice/시간·불가한 정책/단위/형상·변조/늦은 변경/부분 쓰기 거부,
독립 exporter의 생장/재개 import·계산/DB/CLI/network0·출력 밖 쓰기0·원 자료/4root/WSL 보존.
SDK는 모든102 DTO/원 상태·21장부·단위/시각·복사/취소·bad response/경계·원 파일 변조 거부를 검증한다.
같은 상태의 실제3D mesh/표/그래프·URL/메뉴/reload·hold/유휴 자원과 최종 디자인/브라우저는 뒤따르는 수용이다.
32초의 변화량을 확대하거나 기존24시간 저장 줄기를 같은 생장 계산으로 표시하지 않는다.
