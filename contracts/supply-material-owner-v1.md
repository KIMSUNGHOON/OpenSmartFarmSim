# 물질 전이의 불변 채택·원 격자 재개 v1

상태: **합성 저장/재개 수용 — 2026-10-31 KST.** [58검사·실제 세 사례/fresh·보존](../research/supply-material-owner-20261031.md)을 근거로 한다.
[물질 전이 산술](supply-material-point-v1.md) 뒤의 별도 local research family다.
이 계약의 `completed`는 선언한 forcing 구간의 끝이며 제품 전체·실제 품종 한 작기 완료가 아니다.

## 접수와 첫 채택

`crop_supply_material_owner.adopt_material(genuine_forcing_handle, pending_page_sha256,
time_tolerance_seconds_exact, *, inputs, expected_point_sha256, workspace,
cancelled=None, wall_seconds=60)`는 기존 산술을 실제35/36RHS로 다시 계산한다.
caller가 제공한 전이 DTO를 권한으로 사용하지 않는다. expected hash와 입력 snapshot을 전후 대사한다.
`Workspace`는 실제 forcing workspace·별도 archive·ContentAccess이며 원 store와 같은 경로를 거부한다.
새 `Handle`/token/schema/version을 사용하며 이전 Context/CP를 만들지 않는다.

새 불변 definition은 source definition/cursor·pending·허용 폭·입력·기대 계산 hash와 point blob·코드를 결속한다.
첫 채택은 실제 point에서 새 program/organs/costs/layout, birth/geometry baseline,
initial state/derived·정확 lifetime/point totals·global 잔차/예산을 도출한다.
source schedule의 첫 사건을 consumed로 기록하고 sequence를 한 번 올린다.
shoot age는 실제 선택 upper-bound 시각의 원 적분값이며 문턱에 맞추지 않는다.

새 branch 적분량은0이고 그 초기 수지 잔차와 예산도0이다. 기존 global 예산을 늘리지 않는다.
같은 source 사건은 해당 계보에서 다시 적용할 수 없다. 동일 접수의 재시도는 같은 cursor이고,
다른 합성 입력을 선택한 분기는 별도 definition이다. 전역 농장 작업 중복 방지를 구현한 것은 아니다.
새 physical/geometry origin record는 원 origin hash·point hash·확장한 실제 baseline을 연결한다.
원점/과거 기관·정확 누적량/기원·권리 AND를 보존한다. 입력 true로 source false 권리를 승격하지 않는다.

## 저장과 복구

basis·origin record·current·history page를 저장한 뒤 cursor를 마지막에 쓴다.
모든 현재 검증이 통과한 뒤에만 새 handle/cursor를 반환한다. 중간 실패 때 참조 없는 blob이 남을 수 있지만
실패한 상태를 확정 결과로 반환하지 않는다. 가변 전역 HEAD나 Farm/DB 작업 게시의 원자성을 주장하지 않는다.

`open_material(CursorRef, definition_ref, workspace)`는 실제 source validator와 고정 code/profile을 연다.
저장된 pending의 원 RK4 trace/공유 열적 다항식·정확 bisection/upper bound·전체 dense 상태와 적분량/수지,
순수 point 조달 산술/수지·metadata·새 basis·모든 current/page/cursor/origin을 재검사한다.
저장된 RHS/derived는 local producer witness다. 복구는 과거 RHS 평가나 시간 재적분을 하지 않으며,
대수·수지를 검증한다. 독립 농업/ODE 오차 검증이나 외부 서명된 농장 권한을 대신하지 않는다.

복구는 해시만 믿지 않고 상태/적분량·clock·수지/예산·phase와 prefix를 다시 도출한다.
boolean을 int로, int를 binary64로 허용하지 않는다. 단위·root의 주장 범위/원 계측·현재 자료가 변하면 보류한다.
원 source와 불변 archive를 수정해 복구하거나 기본값으로 결측을 메우지 않는다.

## 원 격자의 남은 구간

`advance(handle, AdvanceRequest)`는 같은 활성 forcing의 원 RHS/flux·one-round RK4·clock/수지 식을 사용한다.
새 point의 branch origin에서 시작하되 다음 원 격자·선언 forcing edge·계획 끝 중 가장 이른 경계까지만 적분한다.
임의 중간 stop으로 수치 partition을 바꾸지 않는다. 원격 조회나3D는 이 계산을 대신 실행하지 않는다.

forcing 경계는 before → after를 같은 시각에 기록한다. stock·clock·점/누적량·수지/기원은 같고
입력에 따른 derived만 바뀔 수 있다. 다음 미소비 출현 문턱을 만나면 새 pending을 저장하고 멈춘다.
이 v1은 그 다음 사건의 조달 정책/반복 채택을 승인하지 않는다.

요청당 최대128step/128record·1024RHS·2MiB 출력·wall1–60초, current512KiB와 record2MiB,
최대256개 local cursor history를 유지한다. 기존 source 한도는 그대로다.
계산 중 취소/도메인·게시 실패는 마지막 확정 prefix를 유지한다. 현재 source/권리·code/basis가 바뀌면
handle과 반환 prefix를 제거하고 historical cursor와 hold 이유만 남긴다.

수용은 실제 source 사건 한 번 소비·seed/layout/origin/point 예산·정확 remainder,
모든 상태/적분량의 독립 반올림·global 예산, forcing zero jump·full/split/fresh 같은 cursor,
타입/재해시 변조·권리/취소/게시 실패/늦은 변경·원 자료/기존 preview/WSL 보존이다.
다음은 게시권리가 확인된 원본으로 새로 계산한 첫 확정 결과의 무계산 reader/export → strict SDK →
같은 시각/phase의 실제 mesh·표/그래프다. 긴 작기 완료를 첫3D의 선행으로 묶지 않는다.
