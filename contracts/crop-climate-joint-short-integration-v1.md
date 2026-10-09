# 작물·기후의 짧은 공동 적분 v1

선행: [공동 순간 RHS](crop-climate-joint-rhs-v1.md)의 로컬 수용.
이 core5는 사건 없는 한 구간의 초 단위 합성 계산이다. 전체 작기/온실·실제 품종/관문은 별도다.
핵심 파일: `backend/app/crop_climate_joint_integration.py`,
`backend/tests/test_crop_climate_joint_integration.py`, 이 계약,
`research/crop-climate-joint-integration-reference.py`,
`fixtures/crop-climate-joint-integration-reference-cases-v1.json`.
기존 모델/프로필/작기 결과·새 패키지/DB/API/3D를 변경하지 않는다.

## 입력·상태·시간

`integrate(scenario=..., step_seconds=..., step_count=..., growth_profile=...,
cohort_profile=..., transport_profile=..., exchange_profile=...)`를 제공한다.
scenario는 기존 공동 RHS의 닫힌 입력과 4개 고정 프로필을 그대로 사용한다.
기관5·과실 C/N100·기후3의 108상태를 **함께** 진행한다.
부호 있는 수관 Uref를 독립 상태로 두고 매 stage의 leaf/LAI/C에서 Tc를 유도한다.
RGR50·parameters·forcing·continuous removals·fruit entry는 이 구간 동안 명시 상수다.
RGR의 자동 갱신·CO₂/일사/시설 제어를 새로 계산하지 않는다.

`step_seconds`는 bool/문자열이 아닌 명시 유한 양수,
`step_count`는 bool이 아닌 정수 1–4096이며 총 구간은 600초 이하다.
이 예산은 안정성/정확도를 보장하지 않는다. dt/count는 입력 identity에 결속한다.
시간은 시작0부터 `step_index*step_seconds`의 elapsed seconds다.
T24/Tsum은 동적 Tc의 RHS와 함께 적분하며 상수 Tcan의 Fraction/analytic override를 쓰지 않는다.
UTC·checkpoint/seed/continuation·농장 Run을 발급하지 않는다.
관리 사건/구간 forcing 변경은 다음 별도 계약이다. 사건을 이 입력에 추가하면 거부한다.

## 공동 RK4와 실패

결정적 fixed-step RK4의 같은 stage에서 승인된 RHS를 한 번 평가한다.
상태 미분과 아래 장부 유량은 **같은 stage/가중치**를 사용한다.
확정 endpoint의 RHS를 다음 k1으로 재사용하여 `4*step_count+1`회 평가한다.
초기·모든 trial·확정 endpoint에서 기존 crop·온도·빈 수관·포화·numeric domain을 확인한다.
상태 전체를 0 이상으로 검사하지 않는다. Uref는 부호를 허용하고 나머지 domain은 해당 RHS가 검사한다.
비영 increment가 underflow/반올림으로 사라지거나 비유한 상태/장부면 hold한다.
실패 시 step/stage와 마지막 확정 시각/108상태·유도량을 보존하며 partial success를 반환하지 않는다.

## 22개 누적 장부

각 순간 RHS의 실제 crop/교환/용량 유량만 사용하며 generated prose 값을 넣지 않는다.

| 누적 필드 | 단위 |
| --- | --- |
| photosynthesis, growth_respiration, maintenance_leaf, maintenance_stem_root, maintenance_fruit, removal_leaf, removal_stem_root, terminal_fruit_carbohydrate | mg_CH2O/m2_floor |
| fruit_number_inflow, terminal_fruit_number | fruits_equivalent/m2_floor |
| canopy_to_air_sensible, canopy_to_vapor_latent, incoming_capacity_heat, maintenance_capacity_heat, removal_capacity_heat, canopy_external_heat, air_external_sensible_heat | J/m2_floor |
| canopy_to_air_vapor, air_external_vapor | kg_water/m2_floor |
| capacity_allocation, capacity_maintenance, capacity_removal | J/m2_floor/K |

H/E/물질 현열·외부 경계의 부호를 유지한다. 공기 현열에 잠열/물질 열을 다시 넣지 않는다.
과실 terminal outflow는 합성 구획의 경계이며 검증된 수확량/생과 kg가 아니다.
수관 물 경계는 `-integral(E)`로 별도 표시한다. 액수 저장/급액 충분성·실제 잎 수분은 계산하지 않는다.
초기/종료 상태와 적분 장부에서 다음을 별도로 대사한다(`I`는 해당 누적량).

```text
delta(total carbohydrate) = Iphoto-Igrowth-Imaint_leaf-Imaint_stem-Imaint_fruit-Iremove_leaf-Iremove_stem-IterminalC
delta(total fruit number) = IentryN-IterminalN
delta(Uref) = IQcan-IH-ILE+IQin-IQout_m-IQout_r
Cair*delta(Tair) = IQair+IH
delta(m_v) = IE+IFv
delta(Ccan) = Ig-Idm-Idr
delta(Uref)+Cair*delta(Tair)+L*delta(m_v) = IQcan+IQair+L*IFv+IQin-IQout_m-IQout_r
```

stock은 fsum으로 합산하며 각 잔차의 runtime 예산은
`64*(step_count+1)*ulp(max(abs(initial_stock),abs(final_stock),sum(abs(balance_terms))))`다.
이는 명시 binary64 소프트웨어 roundoff 한도이며 물리 정확도/시간 절단 오차 허용치가 아니다.
부호 있는 Uref를 직접 적분하므로 수관 저장 열의 endpoint 곱 절단 오차를 잔차로 숨기지 않는다.
온도·기관/구획 궤적의 적분 오차는 별도 독립 궤적과 간격 축소로 검사한다.

## 사전 수용

1. app import 없는 Decimal80의 고정 독립 crop/startup·열/용량 원식과 별도 RK4로
   같은 dt의 전체108상태·22장부를 대사한다. 32초 낮/밤·양/역 교환과 signed 기준온도를 포함한다.
   상태/장부 상대5e-12, 0값 절대5e-14, 온도 절대2e-10 K를 사전 기준으로 사용한다.
2. 해당 합성 사례의 에너지 잔차 절대1e-7 J/m2_floor,
   탄소1e-7 mg_CH2O/m2_floor·개수1e-12 fruits_equivalent/m2_floor,
   수증기1e-13 kg_water/m2_floor·용량1e-8 J/m2_floor/K 이내와 runtime 예산을 확인한다.
3. 양의 tail 낮/밤·역 교환의32초 dt8/4/2 해를 독립 Decimal dt0.25 해와 비교한다.
   Tc/Tair/m_v·T24/Tsum과 buffer/과실 탄소 합·H/LE/E 장부의 각 반분 오차가
   8배 넘게 줄어드는지 확인한다. 0/불변량을 수렴 비율로 보고하지 않는다.
   다중 시간 규모/부동소수 오차 바닥에 도달하면 독립 참조 오차와 함께 hold로 기록하고 수용 기준을 낮추지 않는다.
4. 빈 과실 첫 진입의 알고리즘 동등성과 원량은 같은 dt 참조로 확인하되,
   기존 초기 전환 불확실성을 유지하고 그 사례의 시간 수렴/실제 착과 정확도를 승인하지 않는다.
5. signed 기준온도 변경은 Tc/crop/교환/물리 궤적을 보존하고
   Unew=Uold-C*delta·누적 물질 열의 대응 변환을 따른다.
6. 공동 stage/호출 수·feedback·동적 T24/Tsum·입력 불변/identity,
   schema/unit/profile/budget/domain/numeric 실패·마지막 확정 상태를 시험한다.
   기존 결과/미리보기·source/FD/정확한 소유 정리·단일512MiB/소유+보호1GiB를 보존하고 실제 비용을 기록한다.

출력은 모델/코드/RHS·프로필·입력/수치 해시, 원 sample/유도량·누적 장부/잔차/예산과
`software_research_only`, `synthetic_joint_crop_climate_short_integration_only`, `G0_G4=not_assessed`다.
관리 사건·온실 경계·새 continuation/저장/API/3D·물/구매 에너지·경제·UI/U3는 후속이다.
