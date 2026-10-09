# 작물·기후 공동 순간 RHS v1

상태: [전체 결합](crop-climate-coupling-v1.md)의 다음 작은 core5 계약이다.
[가변 용량 경계](crop-canopy-energy-transport-v1.md)와 기존 고정 LAI·startup/구획 식을 재사용한다.
이 문서의 구현은 시간 진행·사건 처리·checkpoint·저장/API·3D·실시간 U3를 수행하지 않는다.

핵심5파일: `backend/app/crop_climate_joint_rhs.py`,
`backend/tests/test_crop_climate_joint_rhs.py`, 이 계약,
`research/crop-climate-joint-rhs-reference.py`,
`fixtures/crop-climate-joint-rhs-reference-cases-v1.json`.
기존 코드/프로필/작기 결과는 변경하지 않는다. 새 패키지는 없다.

## 닫힌 trial 입력

`evaluate_rhs(scenario=..., growth_profile=..., cohort_profile=...,
transport_profile=..., exchange_profile=...)`는 한 trial의 입력만 평가한다.
4개 프로필은 기존 정확한 고정 bytes의 공개 타입이어야 한다.
scenario는 `input_id`(비어 있지 않은 1–200자),
`origin=synthetic|reference_calculation`과 아래 정확한 8개 블록을 가진다.
블록에는 metadata를 중복하지 않고 수치에는 정확히 `{value,unit}`만 쓴다.
각 단위와 배열 길이는 기존 해당 프로필/계약을 따른다.

| 블록 | 정확한 필드 | 의미 |
| --- | --- | --- |
| plant_state | buffer, leaf, stem_root, temperature_filtered_24h, temperature_sum | 기존 기관 상태 5개; 탄수화물/degC/degC_day |
| cohort_state | fruit_carbohydrate, fruit_number | 각 50개의 단위 있는 C/N; T24/Tsum은 plant_state 하나만 사용 |
| climate_state | canopy_sensible_energy, air_temperature, air_vapor_mass | signed J/m2_floor, degC, kg_water/m2_floor |
| parameters | leaf_heat_capacity, air_volume_per_floor_area, air_capacity_density, canopy_vapor_resistance, vapor_gas_constant, reference_temperature | 명시 고정 capLeaf/h/rho/rS/Rv/Tref; 앞5개 양수, Tref는 회계 기준 |
| forcing | canopy_external_heat, air_external_sensible_heat, air_external_vapor, incoming_capacity_temperature, par_above_canopy, co2 | W/m2_floor, W/m2_floor, kg_water/m2_floor/s, degC, umol_photons/m2_floor/s, ppm |
| removals | leaf, stem_root | 기존 명시 연속 제거율 mg_CH2O/m2_floor/s |
| fruit_entry | fruit_number_inflow, fruit_entry_carbohydrate | 기존 명시 진입 S/W1; 자동 착과 아님 |
| relative_growth_rate | fruit_relative_growth_rate | 단위 1/s의 50개 **명시 진단 forcing**; 적분 상태/새 추정식 아님 |

기관/구획의 질량/개수·제거·진입·RGR은 0 이상이고 leaf는 양수다.
T24는 기존 startup의 17–23°C, Tsum>0 등 원 domain을 유지한다.
derived Tc, Ta, Tin은 합성 창 10–34°C다. Uref·외부 열/수증기·Tref는 부호를 허용한다.
bool/문자열 수치·누락/여분·다른 단위·비유한·표현 불가능한 산술은 hold다.
caller의 Tcan/LAI/수증기압을 입력으로 추가하지 않는다. 같은 trial에서 유도한 값만 사용한다.

현재 crop 적분의 RGR은 명시 구간 forcing이므로 여기에도 그 진단 입력을 둔다.
새 적분은 별도 계약에서 sampling/고정 구간/관리 사건을 정해야 한다.
이 RHS가 과실 RGR이나 온실 CO₂·PAR/복사를 자동으로 예측하지 않는다.
PAR와 Qcan은 각각 명시 강제 입력이다. 두 값의 물리적 원천 일치는 온실 경계의 후속 수용이다.

## 한 stage의 계산과 장부

```text
LAI = sla*leaf
Ccan = capLeaf*LAI
Tc = Tref + Uref/Ccan
Cair = h*rho*cp
vpAir = (m_v/h)*Rv*(Ta+273.15)

crop = existing startup RHS(Tc, plant, 50 C/N, T24/Tsum, PAR/CO2, S/W1, RGR, removals)
exchange = existing canopy exchange(Tc, Ta, LAI, vpAir, rho, rS)
material = accepted capacity policy(actual allocation_leaf, maintenance_leaf, removal_leaf, Tc, Tin, Tref)

Uref' = Qcan-H-LE+Qmaterial
Ta' = (Qair+H)/Cair
m_v' = E+Fv
T24' = (Tc-T24)/seconds_per_day
Tsum' = Tc/seconds_per_day
Tc' (diagnostic) = [Uref'-(Tc-Tref)*Ccan']/Ccan
```

crop/startup·exchange·capacity 각 공개 계산을 **한 번씩** 호출한다.
같은 Tc/LAI를 공유하고 crop의 leaf 미분과 gross capacity의 Ccan'을 대사한다.
성장 호흡은 crop 원장 한 번, canopy 잠열은 `-LE` 한 번, vapor에 `+L*E` 한 번이다.
공기 현열에 LE나 물질 운반열을 추가하지 않는다.
`Tc'`는 진단이며 독립 적분 상태가 아니다. 부호 있는 Uref를 기본 상태로 고정한다.

```text
Uref' + Cair*Ta' + L*m_v' = Qcan + Qair + L*Fv + Qmaterial
m_v' = E+Fv; canopy_water_boundary=-E
Ccan' = capLeaf*sla*(allocation_leaf-maintenance_leaf-removal_leaf)
```

각 탄소/개수·수증기·열·용량 원장 잔차와 예산을 따로 반환한다.
실제 식물 액수 저장/수분 운반·조직 물성/호흡 대사열은 여전히 빠져 있다.
변경된 기준온도에 대해 `Uref_new=Uref_old-Ccan*delta`,
`Uref'_new=Uref'_old-Ccan'*delta`이고 Tc/Tc'/crop/exchange/air/vapor는 불변이다.
기준온도 왕복·Tc 복원 오차는 2e-13 K까지 허용하며 정보 소실은 hold한다.

각 초기 trial에서 `vpAir >= saturation(Ta)`면 `BULK_SATURATION_HOLD`다.
빈 수관/초과 domain/부적합 crop/cohort/profile/수치도 전체 RHS를 거부한다.
실패한 trial을 완료 sample·새 상태로 반환하지 않는다. 부분 적엽은 이 함수에서 수행하지 않는다.
후속 적분은 합의된 부분 적엽 정책을 원자적으로 적용하고 별도 trial 검사를 해야 한다.

## 출력 identity와 사전 수용

새 모델·stage-state schema·동적 온도 이력 미분 판본, 정규화 입력 SHA,
코드/의존 모듈 SHA·4개 프로필 SHA·startup 정책 SHA·component input SHA를 묶는다.
기관5·과실 C/N100·climate3의 단위 있는 미분, 유도 Tc/LAI/C/vp,
gross 용량/열·crop 진단과 개별 장부를 보존한다.
현재 clock은 **초당 미분만** 정의한다. 시간/UTC/seed/continuation을 발급하지 않는다.
기존121상태/checkpoint·상수 Tcan Fraction clock을 확장하지 않는다.

1. app import가 없는 Decimal80의 기존 독립 crop/startup 원식과 새 공동 에너지 장부를
   대사한다. 낮/밤·양/역 교환·빈/양의 과실 tail·명시 제거·다른 Tin/Tref·총 turnover를 포함한다.
2. 독립 스칼라 상대 5e-12/0 기대 절대 5e-14(기존 crop 참조 기준),
   Tc 절대 2e-13 K다. 기존 kernel의 원 잔차 예산을 유지하고 공동 열/용량/수증기 잔차는
   해당 총 절댓값 항 합의 3e-13 이내다. 실제 품종 정확도/시간 적분 수렴 기준이 아니다.
3. 같은 stage의 모듈 호출 수와 실제 전달된 Tc/LAI/leaf gross 흐름을 검사한다.
   leaf/U 변경이 교환·생장/온도 이력 미분을 바꾸는지, Tref 이동이 물리량을 보존하는지 확인한다.
4. 닫힌 입력/단위/배열·유도 온도/빈 수관/포화·profile·numeric hold, 입력 불변,
   identity 재현과 변화, 기존 모델·결과·미리보기 보존을 통과한다.
5. 집중 회귀·별도 참조/원 bytes·실제 종료/FD/소유 정리와 512MiB 단일/1GiB 소유+보호 RSS를 기록한다.

표시는 `software_research_only`, `synthetic_joint_crop_climate_rhs_only`, `G0_G4=not_assessed`다.
이 순간 RHS의 수용으로 공동 적분/온실/물·양분·구매 에너지/경제·생산·추천·UI를 체크하지 않는다.
