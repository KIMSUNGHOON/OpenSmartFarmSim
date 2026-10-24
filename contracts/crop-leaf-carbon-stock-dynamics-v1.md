# 개별 탄소·나이·면적과 기후의 짧은 공동 적분 — 연구 v1

상태: **고정 목록의 합성 짧은 적분 수용** — [58신규/289관련·별도6궤적/102시점](../research/crop-leaf-carbon-stock-dynamics-20261025.md). [개별 재고 RHS](crop-leaf-carbon-stock-rhs-v1.md)를 같은 동적 면적/기후 stage에 연결한다.
고정 목록의 합성 짧은 계산이며 출현/순간 제거·전체 작기/공급 제한 면적·실제 품종 예측을 제공하지 않는다.
분할 재개는 별도 후속 자식에서 같은 상태/누적량으로 검증한다.

## 입력과 상태

`evaluate_rhs(program=...,**profiles)` / `integrate(program=...,step_seconds=...,step_count=...,**profiles)`.
기존 [동적 면적](crop-growing-geometry-climate-v1.md)의 program 필드/3정책에
`leaf_stock_policy=leaf-stocks-uniform-maintenance-explicit-removal-v1`을 명시한다.
scenario는 geometry/capacity_transport를 받지 않으며 plant_state.leaf/removals.leaf도 받지 않는다.
각 고정 leaf는 원 leaf_id/curve/thermal_age/base_temperature/initial_area와
initial_carbon(`mg_CH2O/m2_floor`), sink_weight(`1`), carbon_removal(`mg_CH2O/m2_floor/s`)을 모두 명시한다.
원 ID/순서·양수 model floor·4profile과 동일 단위를 유지한다. 기본 균등 탄소·면적/SLA 역산은 없다.
입력/출력2MiB·고정1–512잎, 모든 재고/weight/제거는 유한 비음수 정상 binary64/0이다.

기존 면적 정규화 helper는 **초기에만** 사용한다. adapter의 aggregate leaf/제거는 명시 개별 입력의 파생 합계이며,
원 요청의 별도 상태가 아니다. 요청/실제 canonical 초기 A 영수증을 보존하고 이후 A를 F(age)에 맞추지 않는다.
old geometry의 `_evaluate/integrate`는 호출하지 않는다. 옛 scalar leaf C를 독립 상태에 넣지 않는다.

```text
0..3      buffer, stem_root, temperature_filtered_24h, temperature_sum
4..53     fruit_carbohydrate[50]
54..103   fruit_number[50]                 # 질소 아님
104..106  canopy_sensible_energy, indoor_air_temperature, air_vapor_mass
107..     thermal_age[n], area[n], leaf_carbon[n]
```

같은 stage의 현재 Ta로 a_i′=(Ta−Tbase_i)/86400, A_i′=F′(a_i)·a_i′를 평가한다.
원 동적 공기/무절단 정책과 명시 gout·gin=gout+k·Ldot 정책을 그대로 사용한다.
LAI=Σ현재 A/floor이고 C_leaf=Σ현재 C_i는 재고 RHS의 파생량이다.
개별 재고 RHS를1회 호출해 실제 C_i′와 나머지 기관/과실/기후 미분을 얻는다.
aggregate leaf 미분은 진단이며 독립 적분하지 않는다. 양의 A에0 C가 있을 때도 실제 조직/물성 검증으로 승격하지 않는다.
현재 A′는 C 공급을 읽지 않으므로 이 결합 자체가 탄소 제한 면적 생장 법칙은 아니다.

## 적분과 장부

고정 RK4로 상태와 같은 stage의 유량을 함께 적분한다. endpoint를 다음 k1으로 재사용해 성공 시4N+1회 평가한다.
원21 global 유량에는 새 실제 잎 유지호흡/제거와 조정된 생장호흡을 쓴다.
각 잎의 유입/유지호흡/제거3개 누적량도 보존해 `ΔC_i−∫g_i+∫M_i+∫R_i=0`을 대사한다.
원 순수 수지 helper에 **파생 aggregate의 임시 projection**을 주어 전체 C/fruit number·현열/증기/용량·나이 장부를 대사한다.
이 projection을 옛 모델 결과/hash/체크포인트로 발급하지 않는다. 새 state/schema/code/input/profile/정책 판본을 사용한다.
곡선 잔차 D=A−F(a)와 D−D0를 초기/현재 그대로 기록한다. 새 초기화나 canonical 재맞춤으로 지우지 않는다.

dt>0, 정수 count1–4096·총600초 이하, sample scalar `(N+1)*(107+3n+2n+8)≤32768`이다.
각 장부의 반올림 예산은 원64(N+1)ulp(재고/항 규모)이며 바닥1이나 생물학적 허용치를 추가하지 않는다.
0재고의 음의 미분/음수 trial·나이/면적/열/기후 domain·수지/비영 increment 소실·코드/profile 변경은 hold다.
실패 step/stage와 마지막 확정 sample/장부를 보존하고 부분 구간을 완료로 표시하지 않는다.
DB·CLI/network/쓰기0, scope=`software_research_only`, claim=`synthetic_leaf_carbon_stock_short_integration_only`, G0_G4=`not_assessed`.

수용: 독립 Decimal110 이상 전체 식/RK4의 모든 상태·누적량/파생량·곡선 잔차와 같은 격자 대사,
대표 간격 반분/명시 roundoff 바닥, 원6합성 조건의 양/0/부분 sink·일부0 C·명시 제거/흐름,
각 stage1회·원 geometry RHS/aggregate 적분/재초기화0·원 입력/값·512/크기·실패 prefix·fresh/4root/WSL.
분할 재개·신뢰 원 bytes/현재 C_i/A/D0/누적량의 보존은 후속 계약에서 별도 수용한다.
