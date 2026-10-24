# 개별 잎 탄소 재고를 기준으로 한 공동 RHS — 연구 v1

상태: **합성 순간 재고 RHS 수용** — [101신규/394관련·fresh72조건/1,296수량](../research/crop-leaf-carbon-stock-rhs-20261025.md). [같은 stage 배분](crop-leaf-partition-climate-rhs-v1.md) 다음 자식이다.
선택한 상태는 잎별 C_i(`mg_CH2O/m2_floor`)이며 모든 행은 같은 명시 model footprint를 분모로 쓴다.
현재 C_leaf는 정확 binary64 C_i의 합계를 한 번 반올림한 파생량이다. 따로 입력/적분하거나 면적/SLA로 재맞추지 않는다.
현재는 순간 RHS만 계산하며 새 잎/개별 면적·전체 작기 예측은 하지 않는다.

`evaluate_rhs(*, scenario, leaf_stocks, growth_profile, cohort_profile, transport_profile, exchange_profile)`.
scenario는 기존 명시 공동 scenario에서 **plant_state.leaf와 removals.leaf를 제외**한 닫힌 구조다.
두 집계량을 중복 입력하면 값이 맞아도 거부한다. 원 나머지 상태/forcing·geometry/총 용량 흐름은 유지한다.
leaf_stocks는 닫힌 input_id/origin/policy/model_floor_area/leaf_ids/leaves다.
input_id는 scenario와 같고 origin=`synthetic`, policy=`leaf-stocks-uniform-maintenance-explicit-removal-v1`이다.
model_floor_area(`m2_floor`)는 scenario.geometry의 동일 값/단위여야 한다.
leaf_ids의 원 순서1–512개와 leaves의 leaf_id 순서를 완전히 일치시킨다.
각 행은 leaf_id/carbon(`mg_CH2O/m2_floor`)/sink_weight(`1`)/removal(`mg_CH2O/m2_floor/s`)다.
모든 수는 유한 비음수 정상 binary64 또는0이며 합계 C>0이다. 개별0은 허용하되 아래 고갈 조건을 적용한다.
이는 선언된 합성 재고이며 농장/저장 문맥 provenance나 실제 조직 질량의 승인이 아니다.

## 선택한 배분·유지호흡 정책

기존 `_non_optical`의 leaf 유지호흡은 공통 온도/고정 profile 계수에 선형인 `M=k(T24)·C_leaf`다.
이 선형 집계식을 모든 잎에 같은 질량당 비용으로 해석하는 **새 명시 연구 가정**을 선택한다.
원 joint가 계산한 M을 `M_i=M·C_i/(정확 ΣC_i)`로 나눠 각 항을 한 번 반올림한다.
새 온도/나이별 계수·균등 분배·면적/질량 역산은 없다. 개별 연령별 호흡을 검증한 모델이라는 뜻이 아니다.
기존 [근거/권리](../research/leaf-carbon-sink-primary-sources-20261024.md)와 원 고정 profile을 재사용하며 새 외부 자료를 채택하지 않는다.

R_i는 호출자가 명시한 연속 제거율이다. ΣR_i를 원 집계 제거에 한 번 전달하며 면적 감소나 나이에서 추정하지 않는다.
현재 ΣC_i와 ΣR_i로 원 배분 공동 RHS를 한 번 조립한다. 상대 sink에 따른 g_i·원 buffer/호흡 조정은 그대로 사용한다.
각 C_i′=g_i−M_i−R_i다. C_i=0에서 최종 미분<0이면 hold하며0으로 잘라내지 않는다.
0에서 유입이 제거를 충당하는 명시 연속 flow-through는 허용한다. 임의 dt로 제거율과 재고 값을 직접 비교하지 않는다.
양의 재고에서 음의 미분은 순간적으로 가능하며 시간 전진의 고갈/실패 prefix는 후속 적분에서 검증한다.
모든0 재고/빈 수관·원 buffer 고갈의 기존 domain/hold는 확대하지 않는다.

## 반환·수지·검증

원 배분 공동 결과는 원 hash/값 그대로 `source_stage`에 보존한다.
새 leaf_rates는 원 ID 순서의 g_i/M_i/R_i/미분이며, 최상위 leaf 미분은 그 미분 합계의 파생 진단이다.
후속 적분의 독립 상태는 C_i이며 이 파생 leaf 미분을 별도로 적분하지 않는다.
최상위 leaf_totals는 현재 C와 실제 반올림된 유입/유지호흡/제거/미분 합계다.
원 집계값과 기관 합계의 반올림 잔차를 보존하며 마지막 잎에 잔차를 몰아주지 않는다.
전체 C 수지는 실제 기관 미분 합계·실제 기관 유지호흡 합계와 원 buffer/stem/과실/성장호흡/P로 다시 대사한다.
원 과실 C/fruit number N·기후/열/물·다른 미분/계수는 바꾸지 않는다. N은 질소가 아니다.

입력/출력 각각512KiB,1–512행/원 순서/현재 stock·floor·4profile/원 코드·정책/input·calculation SHA를 보존한다.
양수 유지호흡/배분의0 또는 subnormal 유실·집계 overflow·단위/ID/분모·수지/코드/hash 불일치는 hold다.
합산 예산64(n+8)ulp와 원 장부/반올림 예산은 계산 허용 오차이며 생물학적 정확도가 아니다.
scope=`software_research_only`, claim=`synthetic_individual_leaf_carbon_rhs_only`, G0_G4=`not_assessed`.
DB·CLI/network/쓰기·시간 전진/재초기화0이다.

수용: 원 합성6조건·서로 다른/부분0 stock·sink/명시 제거·고갈/flow-through·단위/분모/중복 집계·512/상한,
독립 Decimal 잎별/전체 수지·원 나머지 값과 hash/입력 불변·각 component1회·실패/코드·fresh/4root/WSL.
후속은 같은 C_i의 짧은 적분/분할 재개·장부→조달된 출현→저장 결과/같은 상태3D다.
