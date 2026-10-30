# 한 작기 계산을 위한 현재 상태·이력·forcing 계약 v1

상태: **설계 수용, 구현 미완료 — 2026-10-31 KST.**
[실제 코드/자료 대조와 제한 수치 탐색](../research/supply-season-state-history-forcing-design-20261031.md)을 근거로 한다.
기존 모델·Context·CP·reader·화면과 그 수용 증거는 변경하지 않는다.
이 계약은 새 연구 family의 구현 조건이며 기존 512초나 옛 166일 결과의 수용 범위를 넓히지 않는다.
제품 주장/관문은 [PROJECT_SPEC](../docs/PROJECT_SPEC.md), 실행/현재 권리는
[ARCHITECTURE](../docs/ARCHITECTURE.md)를 따른다.

## 선택한 interface

호출자는 다음 두 연산과 닫힌 결과 상태를 배운다. 아래 이름은 **구현 예정**이다.

```python
open_season(source_or_cursor_ref, definition_ref, owned_workspace) -> SeasonHandle
advance(handle, request, *, material=None) -> AdvanceOutcome
```

`source_or_cursor_ref`는 검증된 원 artifact의 명시 frame/CP 또는 새 family의 불변 cursor다.
`definition_ref`는 원 계보, 코드/프로필, 정확 시각/격자, 합성 forcing 범위와 자원 정책을 고정한다.
같은 원본이라도 다른 정의는 다른 branch다. 문자열 SHA만으로 실행 권한을 주지 않는다.
`owned_workspace`는 기존 `ContentAccess`와 소유 POSIX CAS의 구체 설정이다.
새 handle은 새 family만 발급하며 기존 `_TOKEN`/Context/CP를 만들거나 가장하지 않는다.

`request`는 정확 stop 시각과 시도할 적분 구간·RHS 평가·기록 수/bytes·wall/cancel 예산을 가진다.
작업 예산과 수치 격자, 화면 출력 간격을 분리한다. 예산 때문에 시계를 초기화하거나 격자를 바꾸지 않는다.
`material`은 반환된 pending descriptor에 정확히 대응하는 명시 입력만 허용한다.
자동 계수/기관 seed 생성은 이 interface에 포함하지 않는다.

결과는 `yielded`, `awaiting_material`, `completed`, `hold` 중 하나다.
각 결과에는 확정된 시각/phase·cursor/history 참조·진행 계측을 두며 `hold`에는 최초 원인/실패 stage를 둔다.
`completed`는 선언한 **합성 계산 끝**만 의미한다.
계산기에서 replay/UI, 외부 자료 수집, 농장 등록, gate 승인을 실행하지 않는다.
새 paged 결과의 무계산 reader는 후속 별도 module이다.

## 현재 상태와 이력

| 현재 상태: 다음 계산과 수지 검증에 필요한 값 | 분리한 불변 이력 |
|---|---|
| 순서 있는 전체 binary64 벡터·기관 ID/layout·program/organs/costs | 원 root/Context/CP와 실제 이전 입력 bytes |
| 원 UTC·정확 elapsed·전역 격자 위치와 분수 잔여 | 이전 구간의 stage trace/기록·before/after frame |
| shoot/기관 시계·다음 threshold/sequence·소비 사건 ID | 출현 후보·물질 전이 영수증·입력/권리 검토 |
| 원 root 상태/derived와 각 birth·geometry·transfer origin | 각 판본의 정의·프로필·forcing·관리 기록 |
| branch anchor/steps와 **binary64 누산기**·lifetime/point/global 장부/예산 | 이전 페이지 hash와 cursor 전후 hash를 가진 제한된 페이지 |
| 코드/프로필/원 자료/현재 권리·definition/history 참조 | 범위·순서·phase를 검증하는 페이지 index/manifest |

현재 상태는 과거 영수증 bytes와 개수에 비례해 커지지 않아야 한다.
활성 기관 수·수지 항목 수·정확 유리수 정밀도에 따른 크기 증가는 남는다.
현재 상태의 충분성을 실제 RHS/장부의 필드 목록 및 cold 재개로 입증한다.
hash 참조만 남겼다는 이유로 원 수치/권리/전이 검증을 생략하지 않는다.

Cold open은 필요한 계보/페이지를 제한된 메모리로 검증한다. 검증 비용의 이력 길이 비례는 허용하며
과거 RHS 적분/물질 전이 실행은 하지 않는다. Warm advance도 현재 source/code/profile/권리/저장소
검사를 시작 전과 게시 전에 한다. 권리나 원 bytes가 달라지면 캐시로 우회하지 않는다.
최초 연구 자식에는 mutable HEAD나 새 DB/queue/server가 필요하지 않다.

## 시간·forcing·관리 순서

1. 원 UTC, 기관 탄생 시각·원 geometry/account anchor를 유지한다. 새 정의의 실행 끝은 별도로 선언한다.
   기존 `original_numerical`/512초 완료 CP를 수정하지 않고 새 family로 가져온 사실과 격자 연결을 기록한다.
2. 현재 RHS는 canopy 에너지/면적으로 canopy 온도를 계산하고 실내 기온을 적분한다.
   옛 cycle의 직접 canopy 온도 forcing/해석적 적산 시계를 현재 시계 대신 사용하지 않는다.
3. 첫 구현은 현재 합성 forcing의 명시적인 일정 구간만 허용한다. 다음 구현은 정확 유리수 elapsed의
   연속·비중첩 half-open 구간으로 확장한다. 결측/겹침/범위 밖 외삽은 hold다.
   일곱 forcing 채널의 기존 이름/단위를 보존한다. `fruit_entry`도 유량을 바꾸는 입력이므로
   별도로 고정하며 변경하려면 명시된 새 span/관리 계약과 그 시점의 수지 검증이 필요하다.
4. **동일한 불변 active program view를 RHS와 flux 모두에 전달한다.** 현재 flux도 program의
   external heat/vapor와 fruit entry를 읽는다. RHS만 forcing을 바꾸는 구현은 수용하지 않는다.
   원 program bytes는 변경하지 않는다.
5. 적분 구간은 forcing edge를 가로지르지 않는다. 왼쪽 구간으로 edge까지 계산한 뒤
   stock jump 없이 오른쪽 forcing을 적용하고 원 전역 격자의 잔여를 진행한다.
   구간 끝의 왼쪽 RHS와 이후 오른쪽 RHS를 구분해 기록한다.
6. 출현 threshold를 넘는 시도는 확정 CP로 게시하지 않는다. 마지막 확정 prefix와 bracket을 보존하고
   새 family의 근 정밀화·명시 물질 입력·조달/호흡/열용량·순서/수지 검증 후에만 사건을 소비한다.
   같은 시각의 before/after phase와 event ID는 독립 기록이다. 미선언 사건을 건너뛰지 않는다.
7. forcing edge·물질 사건·관리의 동시 처리는 초기 판본에서 `ORDER_HOLD`다.
   후속 구현에서 순서와 수지/분할 일치를 검증하기 전에는 half-open 규칙만으로 처리하지 않는다.
8. 적엽/적심/수확/식물 교체는 현재 zero-removal 법칙의 지원 범위가 아니다.
   새 사건의 대상/단위·제거 물질/열·새 layout/clock·수지·자료 근거가 있어야 별도 판본으로 도입한다.
   야간/저온, 빈 수관, 포화/응축, CO₂ stock/control도 실제 지원 여부를 먼저 확인한다.

## 산술·저장·실패

같은 step과 같은 입력의 full/split/cold 경로는 동일 binary64 계산 순서와 누산기를 사용한다.
구간별로 먼저 반올림한 유량을 더하는 방식으로 바꾸지 않는다. 실제 185항 중18항에서 그 재그룹화가
원 누산기와 달랐다. 첫 구현은 원 branch anchor/누산기/steps를 보존해 기존512초의 수지124개와
누적185개를 정확히 대사한다. 다른 dt의 수렴은 별도 오차 조건이며 byte 동일을 요구하지 않는다.
전역 residual은 원 장부와 새 구간 residual의 정확 조합이며 예산을 임의로 늘리지 않는다.

현재 Context2MiB·CP512KiB, CAS의 blob16MiB/전체64MiB/4096파일 상한은 그대로다.
첫 자식은 이 상한 안의 작은 자료로 검증한다. 더 큰 archive 분할/페이지 정책과 기관 상한은
별도 측정/계약이며, 이 설계만으로 한 작기가 저장된다고 주장하지 않는다.

새 페이지/참조를 먼저 내구 저장하고 마지막에 cursor/commit을 게시한다.
동일 입력 재시도는 동일 참조를 내며 누락 참조·깨진 페이지·부분 게시를 정상 완료로 읽지 않는다.
중단 시 미참조 blob이 남을 수 있지만 기존 확정 cursor를 덮어쓰지 않는다.
수치 domain 실패는 마지막 확정 prefix와 최초 실패 stage를 남긴다.
source/code/권리/저장소의 늦은 검사가 실패하면 새 결과를 게시하지 않는다.
이때 과거 참조는 역사적 증거이며 현재 표시 권한으로 간주하지 않는다.

## 첫 구현 자식: 현재 상태에서 실제 한 구간 계산

작업 ID: **`supply-season-current-state-continuation`**. 단순 codec만 완료하고 생장 계산을 완료로
표시하지 않는다. 같은 작은 자식에 새 판본의 원 상태 import·진행·저장/cold 재개를 포함한다.

| 검증 | 통과 조건 |
|---|---|
| 진짜 원 상태 | 공개 자체 합성 root `84daf00…4476`의 frame36/37을 기존 strict reader로 검증한다. 원504/512초의176상태·11잎/13stock/12절간·모든 origin/layout과124global/185lifetime/7point를 보존한다. |
| 기존 구간 oracle | 504→512초:176상태·derived·185branch/lifetime·124branch/global·정확 clock/phase가 저장 원값과 일치한다. 과거 구간의 별도 저장 결과를 oracle로 사용한다. |
| 새 실제 계산 | 새 family에서512→520초를 동일 pure law/RK4/8초로 진행하고 실제 상태 변화·185누적·124global 잔차/예산·clock/geometry를 검증한다. 원 모델 horizon을 수정하지 않는다. |
| 독립 산술 | 원 저장값과 별도로 clock·terminal C/N·carbon/energy/vapor·geometry/construction 수지의 합/차와 잔차 예산을 고정밀 산술로 대사한다. 새 helper의 자기 호출을 oracle로 쓰지 않는다. |
| full/split/cold | 504→520의2step,1+1step,별도 프로세스 저장 재개의 cursor 수치/누산기/장부가 동일하다. 저장 페이지 분할은 수치 결과를 바꾸지 않는다. cold는 과거 RHS/사건 재실행0이다. |
| pending/실패 | 요청이528초까지여도520→528의 실제 threshold bracket에서 멈추고520확정 prefix를 보존한다. 잘못된 source/model/권리·누락/변경 페이지·budget/cancel·수치 실패의 최초 원인과 게시 거부를 검사한다. |
| 이력·자원 | 새 현재 payload에 누적 영수증을 넣지 않는다. 원 증거 전체를 불변 참조로 보존한다. 작은 새 페이지/현재 상태 크기·RSS/FD/종료를 측정하고 기존 자료/화면/preview의 고정 수명을 보존한다. |
| 주장 | 연구 합성임을 고정한다. 새 family의2step 수용을 한 작기·품종 정확도·생과 kg/수확·구매 에너지/급액·마진·예측/추천 승인으로 표시하지 않는다. |

위 조건은 **아직 통과하지 않았다**. 설계 탐색의 pure RHS20회와 기존 수지 대사는 새 module의
handle/내구 저장/cold/실패/독립 수지 수용을 대신하지 않는다.
첫 자식의 잠정 공수는 import/상태·이력1–2h + 실제 step/장부1–2h + 독립/분할/cold/실패1–2h,
총 **3–6집중시간**이다. 초기 구현 결과에 따라 다시 산정한다.

## 이후 의존성

첫 자식 → forcing edge/일관된 RHS·flux → 실제 pending 근/명시 물질 사건/새 layout →
여러 사건의 paged 이력·측정한600초 초과 계산 → 주야/포화/관리·기관 수명 지원 →
선언한 긴 합성 작기의 수렴/수지·full/split/cold → 새 저장 결과와 같은 시점3D →
검증 가능한 생산/자원 환산 → Decimal 경제/거시·수급 → 대응 후보 비교·최종 제품 UI.
각 화살표마다 새 수용 증거를 남긴다. 옛166일 수용을 이전하지 않는다.

실제 품종·초기/forcing/관리 자료와 독립 국내 농장 자료 확보는 위 합성 개발과 병행한다.
농장 custody/worker·현재 외부 권리와 G0–G4는 제품 게시 조건이다.
첫 자식의 개발 착수 조건으로 확대하지 않는다. 실제 자료 도착일과 미지원 물리/관리 범위를
확정하지 못했으므로 **전체 제품 완료일은 미정**이다.
