# 실제 전체 작기 부하·복원 — v1 후보

상태: **작업 분해·측정 후보, 구현/전체166일 수용 전**, 2026-10-06 KST.
착수 선행은 `web-crop-cycle-browser`, `web-crop-cycle-replay`, `crop-cycle-result-pages`의
실제 수용이다. [native 재검증](../research/web-crop-cycle-native-implementation.md)은
1통과/2044.35초·원27시점/5사건·실제21 HTTPS와 정리를 확인해 선행을 로컬 수용했다.
이 부하 후보의 driver/전체166일은 아직 미구현이다.
[stream 실행](crop-cycle-stream-execution-v1.md), [불변 artifact](crop-cycle-artifact-v1.md),
[원천 감사](../research/crop-forcing-audit.md)를 따른다. 이 작업은 작물 모델 개발과
국내 독립 자료 확보를 병행하는 기존 경로에 놓인다.

## 측정할 대상

실제 모델의 연속121성분 상태·전역 seed/누적/clock/사건을 원 격자에서 계산한다.
원47,809시점/47,808 interval·166일은 입력 형태 참고다. archive의 미채택 UTC/QC·초기/관리·
권리를 소유 합성 입력으로 바꿨다고 표시하지 않는다. 자작 입력은 별도 ID/root와 합성 범위를 가진다.
같은 raw input·code/profile·solver/grid·원 시점 선택·사건에서 실행/복원 결과를 대사한다.
표시 선택을 바꾸어 계산 경계를 바꾸거나 기존 출력 행을 반복한 것을 실제 RHS 실행으로 세지 않는다.

현재 순수 `advance_chunk`는 각 예산1..10,000, artifact는 steps1..10,000/transition1..128이다.
artifact는16,384 commit·512MiB·65,536파일, 공개 응답은30초/2MiB와 sample64/event8을 유지한다.
한도를 높이거나 걸음/출력/검증을 줄이는 수정은 이 후보의 기본 해결책이 아니다.
실측 결함이 있으면 해당 코드의 작은 후속 수정과 동일성·변조/철회·예산 회귀를 따로 정의한다.

25시간 선행 측정은 순수 독립 control-flow108.310281초와 farm/server advance1,193.680637초다.
두 경로는 검증/저장의 범위가 다르며 같은 성능 지표가 아니다.
자작300초 interval/8초 max-step의 형태 산술은47,808×ceil(300/8)=1,816,704걸음이다.
이 수를11,400걸음 측정에 단순 비례한4.79/52.84시간은 **전체 작기 측정·완료 날짜·안전한 상한이 아니다**.
해당 solver 간격의 농업적 정확도도 수용하지 않는다. 누적 artifact 검증·파일/byte budget의
증가 비용과 원 경계/관리 사건에 따른 실제 planned_steps를 먼저 측정한다.

## 작은 구현 순서와 수용

| 단계 | 선행·예상 core 범위 | 수용 증거 |
| --- | --- | --- |
| `crop-cycle-burden-profile` | 실제 result-pages 수용. 측정 driver·집중 검증·기록 형식3파일 | 같은 고정 입력의 순수 RHS/serialize·artifact append/verify·farm/current rights·DB put·원 page 읽기 비용을 분리하고 source/data root·실제 step/transition/byte/file·CPU/wall·process/child RSS·FD/정리를 기록한다. 예산을 달리한 실행과 재시작은 원 값/UTC/사건/seed·clock·수지가 같아야 한다. |
| `crop-cycle-burden-full-rhs` | profile 수용 및 관측된 결함의 집중 수정 수용. source 형태 자작 입력 generator/runner·검증3파일 | 고정된 전체166일 입력을 실제 RHS로 끝까지 실행하고 모델/입력/원 격자·예정/실제 걸음·모든 저장 출력/사건 hash·전역 수지·peak/시간·현재 권리·정리를 기록한다. 실제 농장/품종 검증으로 보고하지 않는다. |
| `crop-cycle-burden-replay-restore` | 전체 RHS와 저장 수용. 중단/복원 runner·실제 조회/화면 검증3–4파일 | 실제 중단 후 같은 원 context/seed/누적/clock/sequence를 복원해 연속 결과와 대사한다. 완전 저장 결과의 시작/중간/끝·실제 byte-short 경계·관리 전후·같은 ID/UTC의 공개 page/3D와30초/2MiB·권리 철회/변조·서버/DB/role/비밀번호/FD 정리를 확인한다. |

profile의 예정 core파일은 `research/crop-cycle-burden-profile.py`,
`backend/tests/test_crop_cycle_burden_profile.py`, 이 계약의 측정 기록 형식 보완이다.
현재 driver/시험은 미구현이다. 기존 입력/저장 모듈을 호출하고 제품 계산식을 바꾸지 않는다.

profile의 짧은 측정은 다음 예산을 정하는 근거이며 전체166일 수용의 대체물이 아니다.
시험 조건·Python/PG/browser·CPU nice·관측 RSS 범위와 비동시 실행을 기록한다.
emulator/child RSS를 실제 저사양 장비·WSL 전체·GPU driver 메모리로 바꾸어 설명하지 않는다.
global wall/step/byte budget은 profile 증거와 원 planned_steps에서 고정하며 예산 만료 시
안전한 checkpoint/명시적 hold를 남긴다. 다음 실행은 같은 상태를 이어가며 새 초기 상태로 재시작하지 않는다.

수치/domain/권리/resource hold가 전체 작기 전에 발생하면 마지막 확인 상태와 reason·미완료 범위를
보존한다. 해당 hold 처리를 검증했다고 전체 작기 부하 부모를 체크하지 않는다.
출력/사건을 누락하거나 이미 계산한 행을 복제해 남은 기간을 채우지 않는다.
부분 결과만 저장됐거나 완전 결과를 응답 예산 내 읽지 못하면 해당 수용은 열어 둔다.

## 사용자 산출물·외부 의존성·날짜

사용자는 비용 분해/한도 표, 실제 실행/복원 receipt, 전체/현재 범위를 구분한 같은 UTC의 화면을 확인한다.
관측된 위험이 해결된 뒤 세 자식의 증거를 모아 `crop-cycle-burden` 부모를 체크한다.
profile 구현/집중 검증은 **2–3집중시간 잠정**이다. 실제 전체 실행/복원 및 저장/조회 완료 날짜는
profile 수용과 global 예산 고정 전에는 추정하지 않는다. 추가 수정은 실제 결함 근거와 함께 산정한다.

실제 품종/작기 입력·국내 독립 검증 자료·crop Run은0건이다. source/검증 데이터 확보는 병행한다.
생과 질량·자원 구매·Decimal 경제 연결은 이 작업 뒤의 별도 계약/자료 근거를 따른다.
G0–G4와 예측·추천 게시 조건은 유지한다. 현재 CLI `gpt-6.1-sol / xhigh`의 실제 문맥과
관측 code/측정 hash는 [계획 receipt](../research/artifacts/crop-cycle-burden-planning-20261006.json)에 있다.
재귀 CLI0회이며 이 계획을 독립 농장 검증이나 실제166일 성공 증거로 취급하지 않는다.
