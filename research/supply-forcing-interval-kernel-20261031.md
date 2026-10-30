# 시간에 따른 환경 입력: 공유 RHS/flux 수치 핵심

2026-10-31 KST. **수치 자식 수용, forcing owner/저장·cold 부모 미완료.**
[계약](../contracts/supply-forcing-interval-kernel-v1.md),
[구현](../backend/app/crop_supply_forcing_interval.py),
[검사](../backend/tests/test_crop_supply_forcing_interval.py),
[기계 판독 증거](artifacts/supply-forcing-interval-kernel-20261031.json)를 연결한다.

## 이번 산출물

기존 [원 상태 진행](supply-season-current-continuation-20261031.md)은 일정 입력/원 격자만 지원한다.
후속 구현의 실제 위험은 RHS만 환경 입력을 바꾸고 flux는 원 program의 값을 읽는 불일치다.
이를 먼저 작은 내부 수치 함수로 검증하고, 다음 owner가 source/plan/권리·저장/복구를 담당하도록 나눴다.
부모 작업의 완료 범위는 줄이지 않았고 해당 checkbox도 미완료로 유지한다.

`advance_interval`은 검증한 basis/current와 고정 네 profile·명시 합성 span을 받아
같은 active view로 실제 stage/RK4/flux·시계/수지를 계산한다.
이전 Context/CP/handle을 만들지 않으며 새 crop checkpoint/cursor/prefix도 발급하지 않는다.
원 program/512초 horizon·birth/geometry/transfer origin과 source/grant는 그대로다.

별도 실행은 기존 genuine v1 cursor의512초 상태를 실제 `open_season`으로 검증해 시작했다.
일정 입력8초는 기존 저장520초의176state/185누산기/124branch/global·시계/phase와 일치했다.
source v1의 output prefix를 이번 후보의 prefix로 재사용하지 않는다.

512→512.5초 후 빛·CO₂·외부 열/수증기·fruit-number 유입을 변경한512.5→520초를 계산했다.
상태 vector는 입력 변경 순간 연속이고 전후 derived는 달라졌다.
남은 원 격자는 정확히7.5초였고520초에서 원 grid65로 복귀했다.
별도 비이진 분수인1/3초 경계도 검증해 남은23/3초를 유지했다.
이는 versioned 합성 제어 가정이며 실제 날씨/권장 운전/생장 예측의 채택이 아니다.

후보와 입력의 raw bytes는 source의 redistribution:false에 따라 private observer 파일에만 둔다.
공개 증거에는 raw crop 수치 값을 복사하지 않는다.
관찰 파일 저장은 제품 history/owner cursor 게시가 아니며 `history_committed=False`다.
현재 UI는 기존 원38시점이고 이번 후보는 연결하지 않았다.

## 실제 검증과 검토

| 범위 | 통과한 증거 |
|---|---|
| RED/구현 | 처음에는 module 부재로 import 실패. 실제 source를 사용하는 첫10검사를 구현/통과했다. |
| 격자 RED/수정 | 잘못된 source grid index가 처음에는 RHS에 도달했다. 원 index와 분수 잔여를 명시 검증해 보정하지 않고 거부한다. |
| 같은 입력 view | 각 실제 RHS 결과를 flux에 전달할 때 forcing/fruit-entry view가 같음을 확인했다. 새 heat/vapor/number의 stage 유량과 정확 누산 기대값을 별도로 대사했다. |
| 독립 수지 | 원512→변경520의124개 carbon/number/heat/vapor·기관/geometry/construction 잔차 변화를 Fraction으로 구성해 global 잔차 차와 모두 대사했다. Decimal2200자리로 잔차 예산,185lifetime 합성을 검증했다. |
| 경계/불변 | 0.5초 edge·원 격자 잔여, stock jump0/point 전이0·derived 변경, 고정 partition의 JSON 재계산 동일, 원 basis/current/span·horizon 불변을 검사했다. |
| 거부 | 단일 span의 gap/원 격자 넘김·단위 오류·소급 입력 변경·잘못된 grid를 RHS 전에 거부했다.520→528 material threshold는 미소비 bracket/현재 후보 없음으로 남겼다. |
| 회귀 | **신규12 + 기존 상태28 + terminal19 =59 passed**, pytest146.08초/guard147.67초. |
| 별도 실제 실행 | genuine source512→고정8초 원520 oracle,0.5초/1/3초 경계의 각각 두 구간·124global 예산/원 격자·JSON 재계산 일치, 원 source archive19파일 보존. |
| 전체 보존 | 이전483source/1output,479부모·UI470/4, CAS124/입력32·원4500항목/기존 두19파일/원 코드 snapshot과5175/5181/5182의 HTTP·고정 수명 보존. |

최종 회귀의 PID최대174,272,512bytes/합계328,060,928bytes, 별도 실행은85,803,008/190,193,664bytes였다.
0.25초 WSL 관측이며 Windows/전체 host RSS는 측정하지 않았다.
각 guard의 owned child0/FD4→4·원 소스 보존과 terminal을 확인했다.
새 forcing owner/full-split/fresh-cold·완전 plan·제품 전체 CI/배포/웹 검증은 실행하지 않았다.
현재 일정 입력 owner의 기존 cold 검사를 새 forcing owner 수용으로 이전하지 않는다.

root native Codex CLI `gpt-6.1-sol/xhigh`·CLI0.157.1에서 연구/설계/구현했다.
실제 session_meta/turn_context LF 줄 및 산출물 hash를 보관했고 재귀 CLI/새 subagent는0이다.
기존 단계별 구현/TDD·code review 기준으로 같은 source/helper 범위·입력 단위/불변·수지·계산/권한
seam을 자체 검토했다. 원 pure RHS/RK4/flux/장부를 재사용하고 새 계수/요금/농장 수치를 생성해 채택하지 않았다.
변경 입력은 합성 software fixture이며 관측 QC나 G0 자료 승인이 아니다.

## 다음 실행과 외부 의존성

다음은 같은 부모 `supply-season-forcing-edge-continuation`의 실제 새 owner다.
source cursor/정의/현재 권리 → 불변 forcing plan/coverage·고정 partition →
edge 전후 phase·현재/이력 내구 게시 → full/split/fresh-cold/실패 prefix·늦은 거부·보존 순서로 진행한다.
구현/수용은 [계약의 남은 부모 조건](../contracts/supply-forcing-interval-kernel-v1.md#남은-부모의-다음-수용)을 따른다.
수치 kernel은 수용했고, 남은 source/plan0.5–1h + owner/저장0.75–1.5h + 검증0.75–1.5h,
합계2–4집중시간으로 초안을 갱신했다. 실측 작업 분해에 따라 다시 산정한다.

그 뒤 실제 material 근/명시 조달, paged 반복/600초 초과·주야/포화/관리·긴 작기/수렴,
같은 저장 상태3D·생산/자원·Decimal 경제/거시·수급/대응 후보 자율 비교·최종 제품 UI를 이어간다.
N은 nitrogen이 아닌 fruit-number equivalent, CH2O는 생과 kg/수확이 아니며 net heat/vapor는 구매 에너지/급액이 아니다.
독립 국내 raw0·첫 실제 품종/forcing/관리·매개변수/권리는 병행 확보 대상이다.
G0–G4/R2·제품 farm/worker는 미수용이며 전체 제품 완료일은 미정이다.
