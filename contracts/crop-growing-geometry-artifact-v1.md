# 합성 면적·기후 결과의 불변 저장과 생장 계산 없는 조회 — 연구 v1

상태: 연구 소프트웨어 수용 — [89집중검사/독립102시점](../research/crop-growing-geometry-artifact-20261024.md). [분할 계산](crop-growing-geometry-continuation-v1.md)의 완료 상태를 저장한다.
기존 MorphologyBlobStore/ContentAccess의 POSIX CAS·현재 파일 정책을 재사용한다. 새 DB/queue/service나 farm Run을 만들지 않는다.
기존 모델/정확 상태·저장 결과/3D를 바꾸지 않는 별도 growing-geometry-research-artifact-v1이다.

`produce_growing_geometry_artifact(directory,access,*,inputs_raw,**profiles)`는 canonical JSON bytes를 받는다.
입력은 schema_version=growing-geometry-artifact-input-v1, input_id, origin=synthetic,
rights, time_origin_utc, step_seconds, step_count, program이다. input_id는 원 program과 같은 ASCII1–200이다.
time_origin_utc는 명시 whole-second UTC이며 자체 합성 표시 기준일 뿐 관측/available_at/농장 시각이 아니다.
dt/count/program/profile4종은 원 연속 계산 경계를 따른다. 입력/단일 blob/root는 각각2MiB 이하,
checkpoint는 원256KiB, frame은512개 이하이고 원32,768 sample scalar/600초·store64MiB/4096파일 한도를 유지한다.

rights는 기존 자체 합성 선언 형식을 쓴다: declaration_id/revision(ASCII), declared_at_utc,
ownership_asserted/access/store/use/transform/display=True와 redistribute(bool)를 모두 명시한다.
redistribute=False는 내부 표시를 막지 않고 그대로 보존하며 향후 public export 권한으로 바꾸지 않는다.
이는 자체 입력의 주장/파일 정책이며 실제 SourceRecord·테넌트/법적 권한·G0를 새로 승인하지 않는다.
원 profile JSON의 출처/권리/연구 범위 metadata도 그대로 보존하며 원문/그림/표의 권리를 추가 부여하지 않는다.

## producer와 마지막 완료 root

producer만 Context를 한 번 준비하고 각 원 걸음을 진행한다. 원 요청/정규 program·context manifest/seed,
초기 영수증/D0·4고정 profile bytes/기존 license notice·각 원 checkpoint bytes를 각각 content hash로 저장한다.
validated Context의 정규/seed 데이터를 복사하며 현재 상태를 새 초기화하거나 면적을 재맞추지 않는다.
root는 고정 scope/model/display policy·원 inputs/source descriptors·code pins·time origin·sample descriptors와
최초/최종 checkpoint/state 및 context SHA를 가진다. descriptor는 index·정확 grid offset·원 checkpoint/sample/state SHA/bytes와 이전 checkpoint를 결속한다.
모든 source/checkpoint 원 bytes·권리/코드·graph를 전후 확인한 뒤 완료 root를 마지막에 저장/반환한다.
실패한 producer는 완료 root를 반환하지 않는다. 중간 blob은 승인된 완료 graph가 아니다.
같은 입력/코드/profile을 다시 계산하면 같은 graph/root bytes이며 producer의 영속 exactly-once를 주장하지 않는다.

`offset_exact=i*Fraction.from_float(dt)`를 보존하고 원 sample.elapsed_seconds도 변경하지 않는다.
둘은 float 변환으로 일치해야 한다. 분수 격자를 ISO microsecond로 반올림해 원 시각으로 표시하지 않는다.
frame의 at는 {time_origin_utc,elapsed_seconds_exact}이며 canonical reduced fraction(s)을 쓴다.

## reader와 화면 투영

`read_growing_geometry_manifest(directory,access,root_sha256)`와
`read_growing_geometry_frame(directory,access,root_sha256,*,index)`는 **신뢰한 private root**만 받는다.
생장/초기화/재개 모듈을 import/호출하지 않고 DB/CLI/network/파일쓰기0이다. 단위/shape/hash·grid/prefix/QC만 검사한다.
원 입력↔정규 수량↔Context/seed/profile/code↔checkpoint의 ID/정책·단위/범위와 원 SHA를 대사한다.
현재 파일 정책과 저장된 source rights·코드를 반환 직전 다시 검사한다. 실제 현재 farm 권리 조회/서명은 후속 상위 계층이다.
자체 해시로 재작성된 임의 root의 진본/방정식 정확성을 증명하지 않으며 원 producer/권한 있는 불변 root가 신뢰 경계다.

DTO growing-geometry-replay-frame-v1은 원 root/input/context/checkpoint/sample/state SHA·index,
원 elapsed/정확 at·leaf ID/현재 a/A·초기 영수증/curve SHA·108+2n state/layout·기후/derived/21누적량·잔차/예산을 제공한다.
저장된 sample/수량을 그대로 복사한다. curve나 SLA로 면적/탄소를 다시 만들거나 시간 보간/새 생장 계산을 하지 않는다.
geometry authority는 stored leaf area이며 줄기/부착/형상은 향후 별도 제작 asset과 구분한다.
생과/키/수확/마진/순위의 geometry를 이 결과에서 자동 생성하지 않는다.

scope=software_research_only, claim_scope=synthetic_growing_geometry_replay_only, G0_G4=not_assessed,
status=completed_software_fixture, time_kind=synthetic_model_clock_not_observation,
parameter_scope=synthetic_inputs_with_pinned_research_reference_profiles를 고정한다.

## 수용

원6프로그램의 모든17frame/leaf ID·a/A/114상태·21장부/원 sample/checkpoint bytes와 시각/해시·seed/profile/권리·원 graph 보존을 대사한다.
분수 dt의 exact grid와 원 float elapsed를 구분하며 반복/새 디렉터리의 같은 root를 확인한다.
누락/여분·단위/형상/불가한 정책·권리 거부/redistributeFalse 보존·root/원본/재지문 변조·현재/늦은 파일 정책/코드·쓰기 실패/완료 반환0,
입출력 상한·잘못된 index와 caller copy/FD/원 source/WSL을 검증한다.
별도 producer 뒤 독립 reader에서 원 bytes/모든 DTO를 대사하고 생장/재개 import·계산/DB/CLI/network/쓰기0을 계측한다.
export/strict SDK/기존 사실적3D는 뒤따르는 단계이며 실제 품종/기후·작기/자원/경제/추천/G0–G4는 이번에 해제하지 않는다.
