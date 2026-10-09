# 작물·기후의 bounded 자동 구간/사건 실행 v1

선행: [짧은 공동 적분](crop-climate-joint-short-integration-v1.md)과
[원자 관리](crop-climate-joint-management-v1.md)의 로컬 수용.
핵심5는 `backend/app/crop_climate_joint_boundary.py`, 해당 tests, 이 계약,
`research/crop-climate-joint-boundary-reference.py`, `fixtures/crop-climate-joint-boundary-reference-cases-v1.json`이다.

## 입력·격자·출력

`integrate_events(scenario=..., events=..., output_steps=..., step_seconds=...,
step_count=..., growth_profile=..., cohort_profile=..., transport_profile=..., exchange_profile=...)`를 제공한다.
scenario와4프로필은 기존 공동 RHS의 닫힌 입력이다. forcing/RGR·연속 제거/fruit entry·parameters는 전 구간 명시 상수다.
dt는 bool/문자열이 아닌 유한 양수, count는1–4096의 bool 아닌 정수이며 총600초 이하다.
시간은 정수 step index와 `index*dt` elapsed seconds다. UTC·Fraction 온도 clock·forcing 변경은 없다.

events는 list 최대128개, 각 행은 정확히 `{step_index,event}`다.
index는0–count의 정수·엄격 증가이며 한 경계에 한 사건이다. event는 기존 원자 관리 입력 그대로이며
목록 내 input_id도 유일하다. schema/수량/분율은 실행 전에 검증한다.
output_steps는 list 최대512개·엄격 증가 정수·범위0–count이며0/count를 모두 포함한다.
임의 시점을 보간하거나 사건을 다른 격자로 이동하지 않는다. 모든 입력/선택/수치 정책을 해시에 결속한다.

## 자동 순서와 전역 확인

초기 공동 RHS로 seed108상태를 확인하고0사건을 처리한 뒤 요청한 첫 출력을 확정한다.
각 걸음은 수용한 짧은 kernel의 한 걸음 RK4다. 다음 k1 재평가를 포함해
완료 호출 수는 `1+5*step_count+2*event_count`다. 중복 식/새 RK4를 구현하지 않는다.
각 걸음에서 연속22장부를 누적하고 seed 대비7수지를 검사한 뒤 step-end를 확정한다.
같은 index의 사건은 원자 적용→사건6합계/전역7수지 확인→journal 확정→사건 후 선택 출력 순서다.
처음/마지막 경계에도 같다. 한 호출 안에서 사건/출력을 정확히 한 번 처리한다.
서버의 영속 멱등·취소·재개 기능을 제공한다고 주장하지 않는다.

event_totals는 leaf/stem_root/fruit_carbohydrate [mg_CH2O/m2_floor],
fruit_number [fruits_equivalent/m2_floor], canopy_sensible_energy [J/m2_floor, signed],
canopy_capacity [J/m2_floor/K]의6필드다. 연속22장부와 혼합하지 않는다.
seed→현재의 탄소/개수·수관/공기 현열·수증기/외부 물·용량·축소 열7수지에서
기존 연속 식에 해당 사건 제거 항을 한 번 더한다. 공기 현열/수증기에는 사건 열을 넣지 않는다.
runtime roundoff는 `64*(confirmed_steps+confirmed_events+1)*ulp(max(abs(seed_stock),abs(current_stock),sum(abs(balance_terms))))`다.
비영 누적이 반올림으로 사라지거나 비유한 값/단위·수지 실패면 hold한다.

각 확정 snapshot은 step/elapsed·108상태/유도량·연속22/사건6·event_count·7잔차/예산·phase를 담는다.
selected samples는 요청 index의 사건 후 값이다. journal은 같은 index의 원 전후·제거량/해시를 담는다.
입력/seed·model/code/RHS/두 kernel/프로필/정책·계산 identity와 실제 결과 payload SHA를 반환한다.
`completed`는 이 연구 호출의 끝이며 농장 Run/G1/미래 생산 예측 완료가 아니다.

## 실패·수용

실패는 `BoundaryHold`이며 step/phase, 마지막 확정 snapshot와 elapsed,
이미 확정한 selected samples/event journal prefix를 남긴다. 부분 성공/재개 checkpoint는 반환하지 않는다.
입력/schema 실패는 확정 상태가 없고, step/global 실패는 이전 확인 상태를 보존한다.
event/global 실패는 같은 시각의 사건 전 확인 상태를 유지하며 실패 사건을 journal에 추가하지 않는다.
샘플 선택 이전의 확인 상태와 화면 출력 prefix를 구분한다. 입력은 변경하지 않는다.

사전 수용:

1. app import 없는 Decimal80·별도130벡터 RK4/사건 경계로9합성 프로그램의
   108상태·연속22/사건6·유도량·전후 journal·선택 시각을 대사한다.
   무사건/낮·밤·역 교환·초기/마지막/다중·음/0 Uref를 포함한다.
   상대5e-12/절대5e-14, 온도/이력 절대2e-10 K를 유지한다.
2. 32초 낮/밤·역 교환의16초 사건을 고정한 dt8/4/2 해 대 독립0.25 해에서
   Tc/Tair/m_v/T24/Tsum·buffer/과실 C합·H/LE/E의 각 반분 오차가8배 넘게 감소해야 한다.
   7수지의 기존 절대 기준: 탄소1e-7 mg/m²·개수1e-12 N/m²·열1e-7 J/m²·물1e-13 kg/m²·용량1e-8 J/m²/K.
3. 실제 kernel/RHS 호출·현재 forcing/RGR·동적 clock/과실 수량 정책·signed 참조 변환,
   동일 격자 no-event/선택 변경 불변과 처음/마지막/다중 사건 순서를 검사한다.
4. 범위/중복/정렬/폐쇄 입력·profiles·step/event/domain/수지/수치 실패의 마지막 상태/prefix·입력 불변,
   512선택/128사건의 최대 출력 구성과 reject 상한을 검증한다.
5. 원 소스/프로필/결과·미리보기/원본2,148항목과 실제 종료·FD/정확한 소유 정리,
   단일512MiB/소유+보호1GiB·실행 비용을 기록한다.

scope는 `software_research_only`, `synthetic_joint_crop_climate_boundary_driver_only`, G0_G4는 `not_assessed`다.
전체 작기/온실·실측 물성/품종·빈 과실 전환 수렴·UTC/forcing segments·continuation/저장/API/3D·실시간 U3는 후속이다.
