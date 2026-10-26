# 개별 줄기·뿌리·잎 재고와 기후의 짧은 공동 적분 — 연구 v1

상태: [신규63/관련336·399검사, app-free Decimal110/별도6궤적·102시점 수용](../research/crop-stem-root-stock-dynamics-20261027.md)의 합성 짧은 적분. [기관 재고 RHS](crop-stem-root-carbon-stock-rhs-v1.md) 다음 단계다. 새 기관·checkpoint/재개·탄소 공급 제한 형상·실제 작기 예측은 후속이다.

`evaluate_rhs(program=...,**profiles)`와 `integrate(program=...,step_seconds=...,step_count=...,**profiles)`를 제공한다. [기존 개별 잎 동역학](crop-leaf-carbon-stock-dynamics-v1.md)의 프로그램에서 scenario.plant_state.stem_root와 scenario.removals.stem_root를 제외한다. 별도 집계를 입력하면 같은 값이어도 거부한다. stem_root_stock_policy=`stem-root-stocks-uniform-maintenance-explicit-removal-v1`과 stem_root_compartments를 추가한다. 각 행은 compartment_id/kind/initial_carbon/sink_weight/carbon_removal이며 원 재고 RHS와 같은 단위/정상수·비음수 조건, 고유 ID·원 순서·정확히 하나의 root_system을 요구한다. 기본 재고/가중치·과거 geometry/SLA 역산은 없다.

독립 상태는106+3n+m개다. buffer/T24/Tsum,50과실 C/50과실 수,수관 현열/실내 Ta/수증기, 잎 나이n/현재 면적n/잎 C_i n,줄기·뿌리 C_i m 순서다. leaf/stem_root aggregate는 입력/독립 적분 상태가 아니다. 현재 C_i의 정확 합계를 한번 반올림한 내부 projection만 초기 정규화/순수 장부 helper에 사용하고 옛 결과/hash/CP로 발급하지 않는다. 초기 요청 면적/정규 면적 영수증·D0는 유지한다. 이후 면적을 곡선에 재맞추지 않는다.

매 stage에서 현재 실내 Ta와 잎 나이/면적·원 곡선으로 a′/A′/LAI/LAI′·열용량 흐름을 만들고 **현재 모든 C_i와 명시 제거**로 새 재고 RHS를1회 호출한다. 원 source/잎 배분/줄기 배분·유지호흡/성장 원가도 각각1회다. 집계와 개별 C를 모두 전진하거나 원가를 두 번 차감하지 않는다. 현재 A′는 C 공급을 읽지 않는 선행 연구 가정이며 공급 제한 생장 법칙이 아니다.

고정 RK4의 같은 네 stage에서 전체 상태와21 global +3n 잎 +3m 줄기·뿌리 유입/M/제거 누적량을 함께 적분한다. endpoint를 다음 k1으로 재사용해 성공 때4N+1회 RHS다. global 성장호흡·유지호흡/제거는 실제 새 RHS의 조정/기관 합계를 쓴다. 기관별 ΔC_i−∫g_i+∫M_i+∫R_i와 stem/root 합계, 전체 C/fruit number·현열/수증기/용량/reduced energy·나이를 독립 대사한다. 원64(N+1)ulp의 규모별 반올림 예산을 유지하며 바닥1/생물학적 허용치를 추가하지 않는다.

명시 dt>0/count1–4096·총600초,1–512잎/1–512기관·입력/출력2MiB·sample `(N+1)*(106+3n+m+2n+9)≤32768`이다. 하위 RHS의512KiB/기존 caps도 유지하므로 전체 최대 조합 수용을 뜻하지 않는다. 각 stage/endpoint의 음수 trial/개별0재고 유출·열/기후/면적/나이 domain·비영 증분 유실·수지/code/profile/source/단위 불일치는 hold다. 실패 step/stage와 마지막 확정 sample/누적량·잔차/예산을 보존한다. clipping/재초기화/불완전 경로 완료 표시는 없다.

원 입력·정규 프로그램·초기 영수증·정책·source/code/4profile·계산 hash와 state layout·기관 ID/단위를 기록한다. DB/CLI/network/쓰기0, scope=software_research_only, G0_G4=not_assessed다. RHS claim=synthetic_individual_stem_root_dynamic_rhs_only, 적분 claim=synthetic_stem_root_stock_short_integration_only다.

수용: 원6합성 조건·다양한 stem/leaf sink/양·일부0·전체0 재고·명시 제거, app-free Decimal110 원 식/RK4 전체 상태/누적량/파생량·간격 반분/측정 roundoff 바닥, 각stage1회·원 geometry/leaf whole RHS/적분0·초기 정규화1회, 원 입력/초기 이력/현재 A/D0·고갈/부분 실패/caps·fresh/독립 장부·자료/GUI/WSL 보존이다. 실제 품종/독립 농장 자료와 예측/추천 게시 관문은 별도로 유지한다.
