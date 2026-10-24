# 개별 잎 탄소·나이·면적 결과의 불변 저장 — 연구 v1

상태: 합성 연구 소프트웨어 수용 — [102신규/191관련·독립102시점](../research/crop-leaf-carbon-stock-artifact-20261025.md). [원 재개 계약](crop-leaf-carbon-stock-continuation-v1.md)의 완료 결과만 게시한다.
기존 MorphologyBlobStore/ContentAccess를 재사용하며 별도 서비스나 농장 Run을 만들지 않는다.

`produce_leaf_carbon_stock_artifact(directory, access, *, inputs_raw, **profiles)`는 canonical UTF-8 JSON bytes를 받는다.
입력의 닫힌 필드는 schema_version=`leaf-carbon-stock-artifact-input-v1`, input_id, origin=`synthetic`,
rights, time_origin_utc, step_seconds, step_count, program이다. 원 program의 input_id·정책·4개 profile과 일치해야 한다.
rights는 기존 자체 합성 선언의 declaration_id/revision/declared_at_utc와 ownership_asserted/access/store/use/transform/display=True,
명시 redistribute(bool)를 보존한다. False를 public export 권한으로 올리지 않는다.
UTC 기준은 합성 표시 기준일이며 관측·농장 시각이나 available_at을 발급하지 않는다.

원 요청/정규 program/context/seed·초기 영수증, profile4개·notice와 각 시점의 **원 checkpoint bytes**를 CAS에 저장한다.
완료 root는 source/code/profile/권리/notice·초기/최종 상태 SHA, 원 순서 sample/prefix/이전 checkpoint SHA와
float elapsed 및 dt×index의 정확 분수 초를 결속한 뒤 마지막에 게시한다. 실패한 계산의 완료 root를 반환하지 않는다.
입력/단일 source/root 2MiB, checkpoint 512KiB, frame 512개 이하, 원 32,768 scalar/600초·store64MiB/4096파일 한도를 유지한다.
새 schema는 `leaf-carbon-stock-research-artifact-v1`이며 기존 저장 객체를 덮어쓰지 않는다.

`read_leaf_carbon_stock_manifest(directory, access, root_sha256)`와
`read_leaf_carbon_stock_frame(directory, access, root_sha256, *, index)`는 외부에서 신뢰한 private root를 받는다.
생장/재개 모듈을 import하거나 계산하지 않고 원 bytes/hash·닫힌 schema/ID/단위/shape/격자/prefix·기록된 QC를 검사한다.
원 file policy·source rights·code를 반환 직전에 다시 확인한다. 실제 현재 farm 권리/서명은 후속 상위 계층의 책임이다.
새 root의 해시 재작성만으로 과거·방정식·권리 진본을 증명하지 않는다.

DTO `leaf-carbon-stock-replay-frame-v1`은 원 sample·107+3n state/layout·21+3n 누적량과 잔차/예산,
원 leaf ID/현재 C_i/a/A·초기 면적 영수증·curve SHA, plant/cohort/climate 수량을 그대로 복사한다.
aggregate leaf는 원 파생 진단만 보존하며 별도 상태로 만들지 않는다.
면적은 저장된 A가 권위다. C_i→면적/키/생과·수확/마진/순위를 추론하거나 보간하지 않는다.
줄기/부착/형상은 별도 제작 asset이며 strict export/SDK와 같은 시점의 사실적3D 연결은 후속이다.

수용: 6조건의 모든 저장 시점/원 checkpoint·state/개별 장부·권리/notice/코드/정확 시각을 대사한다.
반복/다른 디렉터리 동일 root, 1/512잎, fractional dt, canonical/중복 key/상한·단위/ID/shape/권리 거부,
현재/늦은 file policy·code/원본 변조, 부분 쓰기·domain hold/완료 미게시와 caller copy/FD 보존을 검사한다.
별도 producer 뒤 독립 reader에서 전체 DTO/raw bytes를 대사하고 생장/재개 import·계산/DB/CLI/network/쓰기0을 계측한다.
scope=`software_research_only`, claim_scope=`synthetic_leaf_carbon_stock_replay_only`, G0_G4=`not_assessed`다.
실제 품종/독립 농장 자료·조달된 출현·전체 작기/경제/자율 선정과 R2/G0–G4 승인은 별도다.
