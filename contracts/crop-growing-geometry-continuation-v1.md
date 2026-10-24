# 면적 companion을 보존하는 짧은 계산의 분할 재개 — 연구 v1

상태: **소프트웨어 범위 수용**. [211검사·별도 프로세스12복원](../research/crop-growing-geometry-continuation-20261024.md).
[연속 구간](crop-growing-geometry-climate-v1.md)의 수치 식/격자/입력 범위를 그대로 쓴다.
새 농업 계수·시계/운반 정책은 없다. 기존 exact/canonical 상태·SLA 모델/결과를 바꾸지 않는다.
현재 실제 a/A·기관/과실 C/N·signed Uref/공기/증기와21누적량을 복원하며 checkpoint에서 새 초기화를 하지 않는다.

## 공개 경계

`prepare_context(program=...,step_seconds=...,step_count=...,**profiles)`는 원 program을 처음에만 정규화하고
원 초기 면적 영수증·상태·D0·최초 RHS를 고정한다. 같은4개 고정 profile과 원 dt/count/600초/32,768 sample scalar 범위다.
Context는 원 요청/정규 program/seed/manifest의 불변 canonical bytes와 profile tuple을 담은 내부 frozen 객체다.
manifest는 각 bytes SHA, 새 engine/원 short/의존 code·profile/policy/상태·수치 판본과 Python/platform/float 환경을 결속한다.
합 context bytes2MiB 이하이며 `.program`은 **원 요청**의 복사본이다. 다른 프로세스에서 이 요청으로 같은 context를 만든다.

- `start(context)`는 이미 확정한 초기 sample(index0)·0장부와 그 sample을 포함한 prefix checkpoint를 만든다. 추가 RHS0이다.
- `advance_chunk(context,checkpoint,step_budget)`는 정수1–128개의 다음 RK4 걸음을 수행한다. 초기 sample은 다시 출력하지 않는다.
- `checkpoint_bytes(context,checkpoint)`는 동일 context의 불변 canonical UTF-8 bytes를 준다.
- `restore_checkpoint(context,raw_bytes,expected_sha256=...)`는 **외부의 신뢰한 원 bytes SHA**를 필수로 받는다.

체크포인트는256KiB 이하의 닫힌 canonical JSON이다. 비유한/중복 key/잘못된 UTF-8·누락/여분·잘못된 version/context/
벡터 길이/단위·float가 아닌 값·범위/시각/장부·예산·sample의 재계산 불일치를 거부한다.
해시를 다시 계산한 것만으로 진본을 증명하지 않는다. 이후 서버의 권한 있는 불변 저장/서명 경로가 expected SHA를 제공해야 한다.
이 모듈은 외부 인증/서명·자료/관문·영속 게시를 제공하지 않으며 Python 내부 필드 재작성 공격의 보안 경계가 아니다.

## 보존과 실패

payload는 version/context SHA, 현재 step_index, output_cursor=index+1, 각 sample의 누적 prefix SHA,
현재 원 sample·21누적량·원 seed 대비 장부 잔차/예산을 보존한다. leaf ID/순서·단위 layout와 D0/초기 영수증은 고정 context에 묶인다.
elapsed=index*dt다. chunk 크기/실행 시각/복원 횟수를 payload identity에 넣지 않는다.
현재 벡터는 원108+2n 값 그대로며 A를 F(age)로 재맞추거나 끝 상태를 requested initial_area로 바꾸지 않는다.
현재 RHS/곡선 차이·D−D0/전역 장부를 같은 short helper로 대사하며 과거 걸음을 다시 실행하지 않는다.

복원은 현재 endpoint RHS1회, advance도 endpoint 검증1회 뒤 완료 걸음당4회의 새 stage를 평가한다.
원 `_evaluate/_advance/_weighted/_flux/_sample/_balances`를 재사용해 같은 stage/가중치와 원 순서로 누적한다.
같은 격자의 전체/어떤 분할에서도 원 short의 모든 sample·상태·장부가 bit 단위로 같아야 한다.
각 sample별 canonical prefix이므로 최종 checkpoint bytes/SHA도 chunk grouping에 무관해야 한다.

advance 반환은 yielded/completed/hold, manifest/context SHA, 완료/계획 step, 이번 sample 시작 cursor/목록,
원 마지막 확정 sample·장부·checkpoint와 실제 시도 stage 수다. 완료 checkpoint는 읽기/복원할 수 있지만 다시 advance하지 않는다.
도메인/수치 실패는 실패 step/stage·이번 확정 prefix/마지막 상태와 checkpoint=None을 반환한다. 부분 계산을 완료로 표시하지 않는다.
입력/context/checkpoint/budget 오류는 `ContinuationRejected`이며 걸음 전진0이다.
취소/crash/외부 예외를 정상 yield/수치 hold로 바꾸지 않는다.

## 수용

기존 독립6프로그램의 원 short와 전체/다중 예산·모든 단일 분할 위치의 sample/114상태·21장부/잔차/예산,
초기/중간/완료 checkpoint의 canonical roundtrip·같은 최종 bytes를 대사한다.
초기 정규화 helper를 막은 복원/advance와 원 D0/영수증·a/A 보존, 별도 프로세스의 원 digest/새 context·과거 전진0을 검증한다.
원 요청/반환 JSON copy·typed handle/토큰·code/environment/profile/격자/curve/정책·shape/수치/단위/시간/해시/
중복/비유한·원 초기/완료/실패·1/512잎/256KiB·예산을 확인한다. 신규 농업 오차 기준/계수는 없다.
원 source/저장/UI·4root와 WSL512MiB PID/1GiB 합계를 보존한다.
scope=software_research_only, claim_scope=synthetic_growing_geometry_continuation_only, G0_G4=not_assessed다.
정확 제거 사건/출현·공급/현재 농장·불변 결과/같은 UTC3D·실제 작기/자원/경제/추천은 다음 검증이다.
