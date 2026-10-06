# 실제 전체 작기 부하·복원 — v1 후보

상태: **비용 profile·작은 runner/재개 전략 로컬 수용, 실제 전체166일 RHS/저장 조회는 수용 전**, 2026-10-06 KST.
착수 선행은 `web-crop-cycle-browser`, `web-crop-cycle-replay`, `crop-cycle-result-pages`의
실제 수용이다. [native 재검증](../research/web-crop-cycle-native-implementation.md)은
1통과/2044.35초·원27시점/5사건·실제21 HTTPS와 정리를 확인해 선행을 로컬 수용했다.
[profile 수용](../research/crop-cycle-burden-profile-implementation.md)은 고유15개 분할·
실제 SCRAM/별도 worker 복원·자작166일 input plan으로 확인했다.
[runner/작은 재개 전략](../research/crop-cycle-full-rhs-small-strategy-implementation.md)은 집중17개·
자작5시간61출력/2사건·별도 Python의 정확한 checkpoint 재개·terminal RHS0·정리로 수용했다.
실제 전체166일 종료/수지 검증은 미수용이다.
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

profile의 구현 core파일은 `research/crop-cycle-burden-profile.py`,
`backend/tests/test_crop_cycle_burden_profile.py`, 이 계약의 측정 기록 형식 보완이다.
순수/shape14개·native1개로 원행/상태·함수 원복·hold·128 transition 한도를 확인했다.
자작5시간2,280걸음의 예산 비교·모든300초 출력61개, 실제 등록 농장120걸음/SCRAM/worker와
166일 input plan을 수용했다. [원 측정/소스/정리](../research/artifacts/crop-cycle-burden-profile-reference-20261006.json)를
보존했다. 기존 입력/저장49파일과 제품 계산식은 그대로다. profile 수용으로 전체 부하 부모를 체크하지 않는다.

### 측정 기록 형식

`crop-cycle-burden-profile-v1`은 관측 UTC·실제 Python/nice와 driver SHA, input root·원 manifest,
각 실제 budget/step·출력/사건 count·원행 SHA·전체 semantic checkpoint를 기록한다.
checkpoint 비교에서는 chunk별로 달라지는 `checkpoint_sha256`/`parent_sha256`만 제외하고
seed/121상태·원 UTC/phase·global counters·clock/root/격자·원 prefix는 보존한다.
계산 경계/원값이 다른 실행을 같은 재현 결과로 묶지 않는다.

`costs`의 각 이름은 호출 수·포함 wall/CPU초와 직접 관찰 자식 시간을 뺀 exclusive초를 가진다.
포함 시간은 서로 중첩되므로 합산하지 않는다. wrapper/관찰 자체의 overhead와 준비된 context/cache,
미관측 함수의 범위를 표시하고 같은 값의 비계측 기준 실행을 함께 둔다.
JSON canonical 관찰은 driver가 열거한 module alias 범위이며 모든 JSON/시스템 I/O 비용이라고 표시하지 않는다.

artifact는 실제 commit마다 원 step·byte/file 수·advance시간의 growth curve와 재개 횟수,
전체 원 페이지 count/SHA·최대 byte·읽기 RHS 수를 기록한다. 첫 구간 뒤 writer를 닫고 같은
원 HEAD로 재개하므로 누적 prefix 검증 비용을 측정한다. 많은 row/파일의 형식 fixture는 별도로 표시한다.
process peak RSS는 해당 Python 프로세스의 Linux 관측값이며 추가 사용량이나 동시 child 합계가 아니다.
등록 농장/current rights·DB/공개 페이지와 실제 worker는 부모/child별 costs·checkpoint·progress·
exit/FD/PG/role/schema/password 정리를 기록한다. 공개 투영 함수의 시간은 실제 TLS latency가 아니다.
166일 shape는 input plan/bytes/index만 기록하며 RHS0회·실제 계산 미수용을 명시한다.

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
profile의2–3집중시간 잠정은 실제 수용 기록으로 대체했다. 원166일 plan은1,816,704걸음/
1,864,515transition이며 pure10000/10000의187chunk·artifact10000/128의14,567commit 계획이다.
다음 자작 수치 실험의 global wall6시간은 [실행 계약](crop-cycle-full-rhs-v1.md)/집중 검증에서
고정한 **실험 예산**이며 날짜/완료 상한이 아니다. 자작 수치 실험의 성공과 등록 농장의
전체 저장/현재 권리/API·3D 수용을 구분하고 두 범위의 증거를 부모 수용 전에 모은다.
전체 입력 열기21.902006초+context9.171754초와 짧은 native의 반복 input/등록 확인이 관측됐다.
전체 공개 조회 수용에는 byte/hash·검증·현재 권리/변조 거부를 유지하는 비용 개선이 추가로 필요하다.
실제 전체 실행/복원 및 저장/조회 완료 날짜는 해당 수정과 실측 종료 상태 뒤 산정한다.

실제 품종/작기 입력·국내 독립 검증 자료·crop Run은0건이다. source/검증 데이터 확보는 병행한다.
생과 질량·자원 구매·Decimal 경제 연결은 이 작업 뒤의 별도 계약/자료 근거를 따른다.
G0–G4와 예측·추천 게시 조건은 유지한다. 현재 CLI `gpt-6.1-sol / xhigh`의 실제 문맥과
관측 code/측정 hash는 [계획 receipt](../research/artifacts/crop-cycle-burden-planning-20261006.json)에 있다.
재귀 CLI0회이며 이 계획을 독립 농장 검증이나 실제166일 성공 증거로 취급하지 않는다.
