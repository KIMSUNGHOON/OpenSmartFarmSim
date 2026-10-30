# 환경 입력이 바뀌는 한 구간의 수치 계산 v1

상태: **수치 핵심 자식 수용, forcing 저장/복구 부모 미완료 — 2026-10-31 KST.**
[상위 순서](supply-season-current-continuation-v1.md#다음-판본과-보류)를
수치 핵심 → 불변 plan/실행 owner·저장/cold로 나눴다.
[59집중검사/별도 실행](../research/supply-forcing-interval-kernel-20261031.md)을 근거로 한다.
기존 module/입력·horizon과 source/grant는 변경하지 않는다.

구현은 [crop_supply_forcing_interval.py](../backend/app/crop_supply_forcing_interval.py)의 다음 함수다.

```python
advance_interval(
    *, basis, current, profiles, span, end,
    cancelled=None, wall_seconds=60,
) -> dict
```

이는 **이미 검토/검증된 입력에 대한 내부 수치 함수**다.
source/현재 권리·완전한 forcing plan·실행 handle·worker·게시 권한은 caller의 책임이다.
기존 genuine source 검증을 생략하거나 DTO/hash만으로 농장 권한을 부여하지 않는다.
원 Context/CP/owner token을 만들거나 새 계산을 기존512초 모델의 완료 CP로 가장하지 않는다.

## 입력과 계산

`basis`는 검증한 원 seed/program/root 상태·birth/geometry/transfer origin과 profile 참조다.
`current`는 genuine v1 원 격자 상태의 수치 값 또는 이번 kernel의 명시적 interval 상태다.
네 profile은 고정 reference class/원 bytes/전체 값/hash가 일치해야 한다.
원 누산기·시계·장부/point·사건 sequence와 grid 위치가 일치해야 하며 잘못된 위치를 보정하지 않는다.

`span`은 `input_id`, `origin=synthetic`, 정확 `start/end`, `forcing`, `fruit_entry`의 closed record다.
일곱 forcing 채널과 fruit entry의 원 이름/단위, 유한 binary64 값을 검증한다.
입력 변경은 명시 합성 가정이며 실제 기상/제어 자료 채택이나 권장 운전값이 아니다.
바뀐 값은 span 시작에서만 적용하며 source가 이미 지난 시점으로 소급 변경하지 않는다.
입력/current/basis bytes와 원 program을 변경하지 않는다.

`end`는 current 뒤이며 span 안/다음 원 격자 endpoint 이하여야 한다.
원 dt와 정확 elapsed는 보존한다. 분수 구간은 남은 격자를 잃지 않고 재개한다.
물질/주야/포화·응축/기관 제거 등 원 법칙의 미지원 domain을 이 함수가 확장하지 않는다.

같은 불변 active program view를 기존 pure stage와 flux 모두에 전달한다.
공통 RK4/누산 순서를 그대로 사용하고 original-clock/branch/global·geometry 장부를 검증한다.
입력 변경 순간은 같은 state hash와 point 전이0, 전후 derived로 기록한다.
양의 구간 계산은5RHS(현재1/새4)이며 source 과거 구간을 다시 적분하지 않는다.
단일 구간·입출력2MiB/current512KiB·wall1–60초/선택 취소 probe로 제한한다.
source 전체/plan 권리와 늦은 저장소 검사는 후속 owner가 추가해야 한다.

## 결과와 한계

`interval_ready`는 실제 구간 state/원점·clock·누산기/수지·grid 잔여와 trace를 담은
**미게시 수치 후보**다. current에는 output cursor/prefix를 만들지 않는다.
top-level의 `checkpoint_issued=False`, `history_committed=False`, `material_consumed=False`를 유지한다.
source/코드·span/입력 지문과 RHS/flux 순서·정확 clock certificate를 남긴다.
`forcing_transition`의 before/after는 stock jump 없이 같은 시점이다.

다음 material threshold를 만나면 `awaiting_material`·`current=None`과 미소비 bracket만 반환한다.
trial endpoint를 확정 crop state로 사용하지 않는다. forcing/material 순서 해결도 승인하지 않는다.
잘못된 입력/물리 domain/취소는 ValueError 등으로 거부하고 caller가 기존 확정 prefix를 보존한다.
scope는 software research, G0–G4/R2는 미수용이다.

이 함수 자체는 partition 선택이나 계획 전체의 gap/overlap 검사, 순서 있는 before/after 저장,
full/split worker·cold owner 복구, rights propagation, manifest/cursor 게시를 구현하지 않는다.
고정 partition의 JSON 수치 재계산 일치는 새 owner의 cold 복구 수용과 다르다.

## 남은 부모의 다음 수용

작업 `supply-season-forcing-edge-continuation`은 **미완료**다.
다음 구현은 genuine v1 source cursor/정의/현재 권리를 검증해 시작하는 별도 owner다.
새 plan의 권리는 source와 AND하며 original public grant로 source의 private:false 제한을 우회하지 않는다.
정확 span/격자/끝으로 partition을 고정하고 UI 선택·작업 budget으로 적분 격자를 바꾸지 않는다.
격자 일치/분수 edge의 전후 phase·stock 연속, 별도 현재/이력·cursor 내구 게시,
full/split/fresh-cold 같은 수치/장부·단위/원점·실패 prefix·원 자료/WSL 보존을 통과해야 한다.
완전 plan의 결측/겹침/범위 밖·변경/코드/현재 권리/늦은 거부를 검사하고,
미해결 material/forcing 순서는 명시 hold로 남긴다.

남은 공수 초안은 source/권리·plan0.5–1h + owner/phase/저장0.75–1.5h +
독립/full-split/cold·실패/보존0.75–1.5h = **2–4집중시간**이다.
이후 실제 material 근/조달·새 layout, paged 반복/600초 초과·긴 작기/관리/검증,
같은 저장 상태3D·생산/자원·Decimal 경제/거시·수급·대응 후보 자율 비교를 계속한다.
실제 국내 자료/첫 품종은 병행 확보하며 전체 제품 완료일은 미정이다.
