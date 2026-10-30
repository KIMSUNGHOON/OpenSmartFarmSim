# 현재 source에 결속한 새 기관 물질 전이 산술 v1

상태: **합성 산술 수용 — 2026-10-31 KST.** [64검사·실제 세 사례와 보존](../research/supply-material-point-20261031.md)을 근거로 한다.
[상태 후보](supply-forcing-threshold-state-v1.md)를 사용하는
`crop_supply_material_point.apply_material_point(handle, pending_page_sha256,
time_tolerance_seconds_exact, *, inputs, cancelled=None, wall_seconds=60)`의 계약이다.
결과는 미채택 전이 제안이며 checkpoint/일정 소비/저장 승인과 다르다.

## 원 source와 명시 입력

`describe_material_source(handle)`는 genuine forcing owner/cursor를 복원하고 최초 binding의
실제 timeline·emergence profile·소비된 사건 ID를 대사한다. 첫 미소비 sequence/문턱,
원 timeline identity에서 유도한 새 사건/기관 ID, 실제 parent 목록을 반환한다.
이 조회는 RHS/쓰기/일정 소비가 없다. basis에 없는 timeline을 합성해 이전 authority를 만들지 않는다.

입력 schema는 `supply-season-material-point-input-v1`, policy는
`explicit-compatible-seed-on-active-forcing-v1`이다. definition/cursor/pending/candidate/initial-binding hash,
정확 시각·첫 source 사건/sequence/문턱·parent, 실제 공통 floor와 명시 신규 internode/선택 leaf를 받는다.
새 ID는 원 source에서 유도한 값과 같고 아직 사용되지 않아야 한다.

현재 매개변수 범위는 자체 합성 software fixture다. source/product URI·시각·available/retrieved·
vintage/revision·reviewer·단위·raw hash·QC와 권리를 입력에 기록한다. 관측/출판 시각은
자체 선언에 맞게 null이며 실제 품종 관측으로 표시하지 않는다. source·계획·모든 span·입력 권리를 AND한다.
원 redistribution:false를 입력의 true로 바꿀 수 없다. G0 자료 승인 절차를 대체하지 않는다.

구조 탄소·sink·초기 길이·construction cost와 선택 잎의 선언·incoming temperature를 명시한다.
seed 구조 탄소×원 floor가 선언된 기하 비용 이상인지 정확 연산/추가 예산0으로 검사한다.
길이는 실제 emergence profile 한도 안이고, 신규 제거량은0이다. 초기 면적 함수는 새 잎에만 적용한다.
성장 호흡 비용은 원 고정 profile의 `cStemG/cLeafG`를 그대로 사용한다.

## 같은 시각의 전이

source/입력을 사전 검증하고 writer session을 닫은 뒤 독립 후보 계산34RHS를 실행한다.
다시 source를 열어 처음 접수한 basis/current/source bytes와 입력·profile을 대사한다.
중첩 writer lock을 사용하거나 기존 store의 잠금을 약화하지 않는다.

candidate hash·upper-bound 시각·source current가 정확히 같아야 한다. 선택된 시각은
다음 forcing 경계보다 엄격히 앞서야 한다. 참 다항식 근이 앞서더라도 거친 upper bound가
경계에 닿으면 `ORDER_HOLD`이며 먼저 근 범위를 좁혀야 한다. 정확한 물리 출현 시각으로 표시하지 않는다.
표현된 shoot age는 첫 미소비 문턱 이상·다음 문턱 미만이어야 한다.

원 순수 material apply/book 함수를 일반 수치 view와 `context=None`으로 재사용한다.
이 함수들의 context 인자는 사용되지 않는다. 이전 Context/CP/token을 만들어 권한을 이전하지 않는다.
순서는 internode → 선택 leaf이며 각 stage 뒤 실제 도메인 RHS를 한 번 검사한다.
buffer에서 구조 탄소와 성장 호흡을 한 번씩 조달하며 부족하면 전체 제안을 보류한다.
선언 잎의 incoming heat/capacity만 반영하고 기존 좌표·시계·과거 기관을 재초기화하지 않는다.
두 전이의 시간 경과는0이며 원 cumulative transfers에 연속시간 flux를 추가하지 않는다.

11개 point 식·원 ULP 예산과 기존 root에 대한 global preview를 검사한다.
source 잔차/예산에 point 잔차/예산을 정확 합성하고 새 lifetime channel만0으로 확장한다.
기존 birth/geometry 기원·누적량·원 point는 보존한다. 실제 full-leaf 사례의 상태는176→182,
global 계정134/누적 channel199이며 stem-only는176→179·129/192다. 이는 관측된 shape이지 품종 상수가 아니다.

## 결과와 실패

`point_ready`는 before dense, after state/program/organs/costs/layout/RHS,
조달/성장 비용·point/global preview·새 기원·source 사건/일정·입력/코드/계산 hash를 담는다.
후보 전체를 다시 내장하지 않고 후보 hash와 검증에 필요한 before 상태를 결속한다.
`checkpoint_issued`, `history_committed`, `material_consumed`는 false,
`schedule_adoption`은 `not_performed`다. 원 source archive는 그대로다.

후보34+point1또는2=35/36RHS, 과거 확정 구간 재적분0, 계산기 CAS/DB/API/network/CLI 쓰기0이다.
입력128KiB·결과2MiB·전체 wall1–60초·기존 inventory 상한을 유지한다.
권리/ID/조달/수지/도메인·취소·입력/profile/source의 늦은 변경은 after state와 부분 전이를 제거한다.
private 관찰 결과를 제품 게시나 실제 생산 예측으로 승격하지 않는다.

다음 수용은 새 current/page/cursor의 원자 채택·source 일정 한 번 소비·새 basis/layout/origins·
원 격자 잔여/같은 forcing 재개와 full/split/fresh 일치다. 그 뒤 게시권리가 확인된 첫 확정 결과의
무계산 조회·같은 상태3D를 연결한다. 긴 작기 완료는 첫 연결의 선행 조건이 아니다.
