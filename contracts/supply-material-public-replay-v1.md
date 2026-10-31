# 새 기관 저장 창의 producer·reader·공개 export v1

상태: **합성 저장/공개 데이터 수용 — 2026-10-31 KST.**
[39검사·실제 새 계산/fresh export·보존](../research/supply-material-public-replay-20261031.md)을 근거로 한다.
[원자 채택/재개](supply-material-owner-v1.md) 뒤의 첫 화면용 데이터 경계다. UI/SDK 수용은 별도다.

## 새 공개 계산과 저장

원 공개 합성 source의 권리·코드·raw hash/NOTICE를 검증하고 새 base/forcing/material 정의로 계산한다.
기존 private false 결과의 권리를 바꾸거나 그 결과를 공개용으로 복사하지 않는다.
매개변수는 명시 자체 QA 가정과 그 provenance이며 실제 품종 계수/관측을 채택하지 않는다.

`produce_material_artifact(directory, access, *, handle)`는 genuine material handle만 받는다.
모델의 실제 session/restore·source/profile/code/권리 검증 뒤 원본/base/forcing/material의
**선택된 읽기 witness**만 수집한다. 저장소 전체를 나열해 다른 분기나 사용하지 않은 자료를 복사하지 않는다.
출력은 모든 원 저장소와 분리된 절대 경로이며 관련 상하위 경로/심볼릭 링크를 거부한다.

새 root는 원 public root/선택 frame, 각 family의 definition/cursor, 선택 blob의 hash/bytes,
고정 code·권리 AND·NOTICE·실제 frame descriptor를 결속한다. 원본들을 먼저 쓰고 root를 마지막에 쓴다.
source 변경이나 실패 때 완료 root를 반환하지 않는다. 같은 handle은 같은 root를 만든다.

창은 채택된 point의 실제 dense-before와 이후 확정 current 이력이다. 이번 공개본은
before/after/528/536초의4시점·722좌표다. before는 checkpoint가 아니며
`dense_before_from_adopted_point`, 나머지는 `confirmed_material_current`로 구분한다.
없는 구간을 보간하거나 긴 작기 완료로 표시하지 않는다. `covers_whole_season`은 false다.

## 저장 조회

`read_material_manifest(directory, access, root_sha256)`와
`read_material_frame(directory, access, root_sha256, *, index)`는 trusted producer가 반환했거나
고정 공개 inventory에서 선택한 root를 읽는다. 임의 외부 root의 농장 권한/서명을 승인하는 인터페이스가 아니다.

reader는 모델/성장 진입 모듈을 import하지 않는다. 원 source validator·code/raw identity,
선택된 계보/현재·point/basis/origin 참조와 내장 권리, vector/기관 ID/layout·단위·같은 시각을 대사한다.
추가/결측 blob·틀린 frame hash/시각/claim·재해시한 자료형/상태/단계/수지 예산은 보류한다.
기록된 네 RK4 단계의 상태/시각·one-round 끝 상태/누산기와 lifetime/clock 증가를 대수적으로 검증한다.
새 global 잔차/예산은 원 point 기원과 branch의 정확 합이어야 한다.

조회는 저장 RHS를 재평가하거나 시간 전진 함수를 실행하지 않는다. 저장 trace/수지·정확 clock의
검증 산술은 수행한다. RHS/derived는 local producer witness이며 독립 모델 오차/현장 검증을 대신하지 않는다.
DB/network/CAS 쓰기·CLI 실행이 없다. 파일/코드/권리의 전후 fence를 검사하고 display가 없으면 반환하지 않는다.

source/manifest/frame은2MiB, store는 기존64MiB/4096파일, group은1024descriptor,
family 이력은256cursor 안에서 처리한다. 범위 밖/boolean/잘못된 frame index를 다른 시점으로 바꾸지 않는다.
불변 root·서버 Farm custody/현재 외부 권리와 G0–G4는 서로 다른 경계다.

## 공개 내보내기

`research/export-material-replay.py`의 `export(directory, root_sha256, output)`은
use/display/redistribute가 모두 true일 때만 출력 폴더를 만든다. 출처의 제한을 입력 true로 승격하지 않는다.
출력은 source/상위/하위/상대/심볼릭 링크 경로와 분리하고 기존 폴더를 덮어쓰지 않는다.

canonical raw blob·원 NOTICE·frame DTO를 고정 FD writer로 쓴다. 개별2MiB/전체64MiB 안에서
모든 파일의 hash/bytes·현재 source/코드/권리·frame을 다시 대사한 뒤 index를 마지막에 게시한다.
늦은 source/output 변경이나 한도 실패 때 완료 index는 없다. 독립 프로세스의 export도 같은 index hash다.

[공개 inventory](../research/fixtures/supply-material-public-20261031.json)는106파일·13,985,230bytes와
source/root/index/각 파일 hash를 고정한다. 데이터의 실제 mesh/표/그래프 연결과 브라우저 검증,
긴 작기·생산/자원/경제·실제 품종·관문 승인은 후속이다.
