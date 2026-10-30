# 환경 입력 계획·확정 상태·복구 owner v1

상태: **합성 연구 owner 수용 — 2026-10-31 KST.** [82검사/별도 실행·보존](../research/supply-forcing-owner-20261031.md)을 근거로 한다.
[수치 kernel](supply-forcing-interval-kernel-v1.md)의 caller 책임을 별도 연구 실행 owner가 수행한다.
기존 v1 source/정의·수치 모듈과 kernel은 변경하지 않는다. 제품 농장 권한/API/worker 계약은 아니다.

구현은 `backend/app/crop_supply_forcing_owner.py`다. `Workspace`는 실제 v1 `source_workspace`,
새 `archive_directory`, 서버가 정한 `ContentAccess`를 받는다. source와 새 archive의 alias는 거부한다.
`open_season(SourceRef(definition_sha256, cursor_sha256) | CursorRef(sha256), definition_ref, workspace)`와
`advance(handle, base.AdvanceRequest(...), material=None)`로 나눈다.
새 handle/token/정의·basis/current/page/cursor schema를 사용한다. 이전 handle/Context/CP를 꾸며 만들지 않는다.

## 입장과 입력 계획

변경하지 않은 v1 `_session/_restore`에 실제 정의·cursor와 held store를 전달해 source를 검증한다.
기존 horizon을 늘리거나 source를 수치 DTO로 갈아 끼우지 않는다. 원 상태·시계·누적·기원은 그대로 시작한다.
원 입력/프로필·정의/선택된 source 이력 및 새 코드/저장소의 fence를 게시 전후 다시 확인한다.

새 정의는 `supply-forcing-definition-v1`이며 정확 owner/kernel code, source 두 참조,
고정 partition `original_grid_and_declared_forcing_edges_v1`, 정확 `stop_at`, bounded spans와 권리를 담는다.
span은 kernel의 입력/단위 검사를 통과해야 하고, 원 source 시점부터 끝까지 gap/overlap 없이 덮어야 한다.
각 span은 source product/URL·관측/발행 시각(null인 합성 기록)·available/retrieved UTC·vintage/revision,
단위/QC/raw SHA/reviewer와 use/display/redistribute를 담는다. QC는 software_fixture_only다.
이 합성 provenance는 실제 기상/농장 자료 승인이나 G0 수용이 아니다.

최종 세 권리는 실제 source 정의·새 정의·모든 span의 AND다. use:false면 RHS 전에 거부한다.
source의 redistribute:false를 원 public root나 새 plan의 true로 올리지 않는다.
새 불변 정의를 선택하면 새 실행 identity이며 기존 cursor를 다른 계획에 재사용할 수 없다.

## 고정 격자와 순서 있는 저장

적분 경계는 원 격자 tick·선언 forcing edge·선언 끝의 합집합으로 고정한다.
UI 선택/작업 budget은 그 사이 적분점을 추가하지 않는다. 분수 초는 유리수로 보존한다.
각 양의 구간은 수용된 kernel의 같은 active RHS/flux 계산을 사용한다.

원 source는 `source_before_forcing`으로 저장한다. 첫 입력과 매 edge의 오른쪽 입력은
stock/시계·누적/point 전이 없이 derived만 갱신하는 `forcing_after` 기록이다.
edge 왼쪽 구간은 `forcing_before`, 일반 격자는 `original_grid_endpoint`, 끝은 `declared_end`다.
record/RHS/byte budget으로 forcing_before에서 멈춰도 다음 호출이 같은 순서를 이어간다.
material threshold bracket이 forcing edge에 닿으면 순서가 불확실하다는 ORDER_HOLD를 남긴다.
이를 정확한 동시 사건으로 단정하거나 원 material 일정을 소비하지 않는다.

현재 DTO에는 numeric/state·원점·계정·span/phase·integration count와 자체 cursor/prefix만 둔다.
이력은 별도 불변 page로 연결한다. current→page→cursor를 각각 durable CAS에 쓰고,
마지막 cursor 참조를 성공적으로 반환한 때만 새 확정 결과다. 별도 mutable HEAD는 없다.
취소/부분 저장 실패는 마지막 반환된 확정 cursor를 보존한다. 남은 고립 CAS 객체는 확정 이력이 아니다.
늦은 source/권리·저장소 검증 실패면 current handle/새 emitted를 제거하고 과거 참조와 사유만 반환한다.

## 복구와 자원

cold 조회는 genuine source부터 자체 cursor/page/코드·참조를 검사하고 저장 RK4 trace의 상태/순서,
flux·누산/수지·시계 certificate와 phase/prefix를 대사한다. 과거 RHS와 interval kernel을 다시 실행하지 않는다.
외부 호출자가 임의 hash를 제공하는 것만으로 tenant/farm 권한을 얻는 공개 API는 아니다.

plan은 최대128 적분 구간/128 spans, 이력은 최대256 operations다. 이는 긴 작기 수용이 아니다.
요청은 기존 `AdvanceRequest`의 step≤128/RHS≤1024/record≤128/합계 byte≤2MiB/wall≤60초와 취소 probe를 쓴다.
current≤512KiB, 각 객체≤2MiB이며 kernel에는 owner의 남은 wall만 전달한다.
첫 zero-time switch는1RHS, 양의 구간은 현재1+새4RHS를 예약/계측한다.
실패한 kernel의 실제 부분 RHS 횟수를 알 수 없으면 unreported로 남기고 숫자를 만들어 보고하지 않는다.
WSL 검증은 별도 단일 guard의 PID512MiB/합계1GiB/600초와 고정 preview 보호를 따른다.

## 수용과 남은 경계

genuine source/현재 권리·완전 plan/단위/코드·범위 검증, 격자 일치·0.5초/1/3초 edge와
전후 phase/stock 연속·불변 원점/계정, full/split/fresh-process cold의 같은 cursor,
결측/겹침/손상·취소/저장 실패/늦은 source 변경·원 자료/WSL 보존이 이번 수용 범위다.
실제 검증 결과와 source pin은 별도 보고서/기계 증거로 고정한다.

다음은 실제 material 근의 refinement/순서 증명과 명시 조달·새 기관/계정의 원자 채택이다.
이후 paged 반복/600초 초과·주야/포화·응축/관리/기관 수명·긴 합성 작기, 같은 저장 상태3D,
생산·자원 사용/구매량과 Decimal 경제·거시/수급·대응 후보 자율 비교·최종 제품 UI를 진행한다.
독립 국내 자료/실제 품종·매개변수/권리 확보는 병행하며, G0–G4/R2와 실제 게시 조건을 유지한다.
N은 fruit-number equivalent이며 생과 kg/수확이 아니고 net heat/vapor는 구매/급액이 아니다.
