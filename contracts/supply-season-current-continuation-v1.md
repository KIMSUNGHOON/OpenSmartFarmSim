# 현재 상태에서 실제 계산·저장·복구 v1

상태: **자체 합성의 작은 수치 경로 수용 — 2026-10-31 KST.**
[상위 설계](supply-season-state-history-forcing-v1.md)의 첫 자식을
[실제47검사/별도 실행](../research/supply-season-current-continuation-20261031.md)으로 구현했다.
전체 작기·실제 품종/농장·생산 환산·제품 게시의 수용이 아니다.

구현: [crop_supply_season.py](../backend/app/crop_supply_season.py).
기존 pure RHS/공통 RK4 산술·flux·장부를 사용하며 기존 Context/CP를 생성하지 않는다.
기존512초 horizon은 원 자료에 그대로 두고 새 정의의 원점·격자 연결/끝을 고정한다.

## 실제 interface

```python
workspace = Workspace(source_directory, archive_directory, content_access)
handle = open_season(SourceRef(artifact_sha256, frame_index), definition_sha256, workspace)
outcome = advance(handle, AdvanceRequest(stop_at, step_budget=2))
restored = open_season(CursorRef(outcome.handle.cursor_sha256), definition_sha256, workspace)
```

source와 새 archive는 별도 소유 POSIX CAS다. 기존 `ContentAccess`/hash/metadata/단일 link·symlink
검사와 내구 writer를 사용한다. 이는 tenant ACL/농장 custody나 서명 서비스가 아니다.
`SourceRef`는 기존 strict graph reader가 검증한 **원 격자 CP frame**만 받는다.
분수 시점·material before/after frame의 import와 새 material 채택은 이번 판본의 지원 범위가 아니다.
`CursorRef`는 소유 계산기가 발급한 hash를 신뢰하는 로컬 복구 참조다.
임의 hash만으로 실제 농장 자료/예측/추천 승인 권한을 얻지 않는다.

`definition_sha256`는 새 archive에 미리 저장한 canonical closed JSON을 가리킨다.
필수 필드는 `schema_version`, 원 `source`, 현재 `code_sha256`, 원 `method`, 정확 `stop_at`,
`forcing_span`, `rights`, `scope/G0_G4/R2`다.
`forcing_span`은 시작/끝과 원 일곱 forcing/fruit entry 묶음의 SHA를 고정한다.
시작은 실제 source CP이며 끝은 원 dt의 격자 endpoint다. 원 값을 이후 구간에 일정하게 두는
**명시 합성 가정**이다. 관측 외삽이나 실제 날씨/제어 입력 채택으로 표시하지 않는다.
`rights.use`가 필요하고 원 자료보다 redistribution을 확대할 수 없다.

`AdvanceRequest`는 정확 `stop_at`, step1–128, RHS1–1024, record1–128,
byte1–2MiB, wall1–60초와 선택적인 **신뢰한 로컬** 취소 probe를 받는다.
기본값은 코드의 고정 자원 정책이며 작물 계수가 아니다. wall은 admission을 포함해 검사한다.
이 판본의 정의는 source 뒤 최대128개 원 격자 endpoint를 선언할 수 있다.
실제 수용한 경로는504→512→520초이고528초는 pending이다.
기존 blob16MiB/전체64MiB/4096파일·current512KiB/page2MiB 한도를 유지한다.

결과는 `AdvanceOutcome(status, handle, hold, failed_stage, pending, progress, ...)`다.
`handle.current`/`basis`는 복사된 값이며 원 bytes를 바꾸지 않는다.
`yielded`는 작업/출력 예산 또는 정의 끝 이전의 요청 끝이다.
`completed`는 **정의한 합성 끝**이다. `awaiting_material`은 마지막 확정 cursor와 미소비 bracket을 준다.
미지원 `material` 인수는 `MATERIAL_HOLD`다.
일반 수치/취소 실패는 마지막 확정 prefix를 남긴다.
현재 source/code/저장소의 늦은 검사가 실패하면 `handle=None`으로 새/과거의 현재 승인 표시를 거부한다.
저장 I/O 실패는 내부 경로를 노출하지 않는 `STORAGE_HOLD`/errno와 게시 단계를 반환한다.
`historical_cursor_sha256`는 역사 참조이며 `authority_hold`에 별도 늦은 원인을 기록한다.
잘못된 입력/파일의 open은 ValueError/OSError로 거부한다.

## 상태·이력과 복구

고정 basis는 원 seed/program/root 상태·birth/geometry/transfer origin·profile/source 참조다.
현재 record는 원 ordered176상태, 정확 시각/clock·격자/branch 위치, binary64 누산기,
lifetime/point/global 장부와 geometry diagnostics를 보존한다. 누적 receipts는 넣지 않는다.
새 current → stage/history page → cursor 순서로 내구 저장하고 전후 fence를 통과한 참조만 반환한다.
이전 cursor를 덮어쓰거나 mutable HEAD를 만들지 않는다.

각 step page는 앞 cursor·앞/뒤 current·실제 RK4 state/rates/flux·정확 시각·clock certificate를 묶는다.
원 branch 누산기와 연산 순서를 유지하며 구간별 반올림 유량을 나중에 합치지 않는다.
같은 source/definition의2step,1+1step 및 fresh-process 재개는 같은 최종 cursor를 낸다.
새 정의가 달라지면 prefix/cursor가 달라질 수 있으므로 다른 정의끼리 hash 동일을 주장하지 않는다.

Cold open은 원 graph/코드/권리, 실제 basis, cursor 연결·범위, stage 조합/flux 순서·시계/수지를
검증한다. 과거 RHS/물질 사건은 다시 실행하지 않는다.
이는 신뢰한 저장 cursor의 복구이며 각 과거 RHS를 새로 재연산했다는 증명이 아니다.
다음 advance에서 현재 RHS를 검증하고 새 단계만 계산한다.
이력은 페이지별로 읽고 전체 raw 이력을 메모리에 모으지 않는다. 현재 source의 불변 graph와
제한된 방문 metadata는 별도로 유지한다.

## 다음 판본과 보류

다음 자식은 정확 유리수 forcing edge에서 원 격자의 잔여를 유지하고, 같은 불변 active view를
RHS와 flux 모두에 적용하는 것이다. 격자 일치/분수 edge, 상태 연속/phase, full/split/cold 및
carbon/heat/vapor·fruit-entry 수지·gap/overlap/늦은 변경/기존 자료 보존을 수용한다.
현재 module/자료는 보존하고 별도 판본으로 구현한다. 잠정2–5집중시간이며 구현 전에 실제 분해로 갱신한다.
그 뒤 실제 pending 근/명시 물질 전이 → paged 반복/600초 초과 → 주야/응축/관리·기관 수명 →
긴 합성 작기/같은 시점3D → 생산/자원·Decimal 경제/거시·수급/대응 후보 비교·최종 UI다.

독립 국내 raw0·실제 품종/forcing/관리 및 생산 환산/구매 에너지/급액·가격/수급 근거 확보는 병행한다.
제품 farm/worker·현재 외부 권리와 G0–G4, 최종 사실감 R2는 미수용이다. 전체 완료일은 미정이다.
