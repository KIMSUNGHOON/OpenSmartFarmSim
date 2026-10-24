# 명시 LAI의 공동 탄소·현열·공기·수증기 순간 RHS v1

상태: **순간 조립 수용**. [391검사·fresh40사례/5,280독립 수치](../research/crop-explicit-lai-climate-20261024.md).
[연속 결합4](crop-geometry-carbon-coupling-research-v1.md)의 순간 조립이다.
[명시 C/N](crop-explicit-lai-carbon-cohorts-v1.md), [면적 현열](crop-area-canopy-energy-v1.md),
[기존 교환](crop-canopy-exchange-v1.md)의 고정 식/프로필을 재사용한다. 기존 SLA 공동 모델/저장 결과를 바꾸지 않는다.
실제 조직/물성·물 공급/기후 feedback/생산 검증이나 시간 전진·농장/UTC 계보·저장/3D 승인은 아니다.

`evaluate_rhs(*,scenario,growth_profile,cohort_profile,transport_profile,exchange_profile)`는 기존4타입의
정확한 고정 bytes 프로필과 닫힌 scenario를 받는다. scenario는 ASCII input_id1–200, origin=synthetic와
기존 [공동 계약](crop-climate-joint-rhs-v1.md)의8개 수량 블록 및 geometry/capacity_transport를 가진다.
기존 plant_state/cohort_state/relative_growth_rate/climate_state/parameters/removals/fruit_entry의 필드/단위를 유지한다.
forcing에는 기존6필드와 outgoing_capacity_temperature(degC)를 **모두** 명시한다.
geometry={model_floor_area(m2_floor),leaf_area_index(m2_leaf/m2_floor),leaf_area_index_rate(m2_leaf/m2_floor/s)}다.
floor/LAI는 양수, Ldot는 signed다. floor는 같은 stage의 고정 합성 모델 범위 선언이며 실제 수관 대표성 증거가 아니다.
각 per-floor 재고/열/물과 LAI/Ldot는 이 같은 모델 범위를 따른다고 선언한다. 면적을 곱해 총량/질량을 만들지 않는다.
capacity_transport={capacity_inflow,capacity_outflow}, 각각 J/m2_floor/K/s의0 이상 독립 총 흐름이다.
Tin/Tout/총 흐름은 Ldot/탄소에서 역산하지 않고 유량0에서도 빠짐없이 받는다.
수량은 정확히 {value,unit}; bool/비유한·누락/여분·다른 단위·배열50개 이외를 hold한다.
입력/출력은 각각128KiB 이하다. 원 입력을 복사해 해시한 뒤 정규화한다.

Tc는 **저장된 signed Uref**와 명시 LAI/k에서 `Tref+Uref/(k*LAI)`로 복원한다.
caller Tc/수증기압/PAR·NIR 유도값을 추가하지 않는다. Tc/Ta/Tin/Tout는 기존10–34°C,
T24/Tsum·fruit startup/광학 domain은 원 기준을 유지한다. k와 나머지 물성은 이 판본 안의 명시 고정 가정이다.
0 LAI/용량, 불가한 기준 온도 복원(2e-13 K), 비유한/곱·나눗셈 소실, 공기 포화 이상을 hold한다.
공기 수증기 재고는0 이상이며0 재고의 최종 미분이 음수면 고갈 hold다. 실제 물 공급/응결 정책은 추가하지 않는다.

한 stage에서 새 plant C/N, 기존 canopy exchange, 새 면적 현열 함수를 각각1회 호출한다.
같은 Tc/LAI와 명시 Ldot/gross 흐름을 전달한다. 원 SLA 공동/전체 plant RHS를 호출하고 덮어쓰지 않는다.
공기 열용량/수증기압은 기존 `h*rho*cp`, `(m_v/h)*Rv*(Ta+273.15)`를 그대로 계산한다.

```text
Qnonmaterial = Qcan_external-H-LE
Uref' = Qnonmaterial+Qmaterial
Ta' = (Qair_external+H)/Cair
m_v' = E+Fv_external
Uref' + Cair*Ta' + latent_heat*m_v'
  = Qcan_external + Qair_external + latent_heat*Fv_external + Qmaterial
canopy_water_boundary = -E
```

H/LE/E는 **같은 exchange의** 현열/잠열/수증기이며 각 내부 장부에1회 사용한다.
공기 현열에 LE/Qmaterial/유출 열을 더하지 않는다. 호흡의 화학 에너지를 현열로 바꾸지 않는다.
Qmaterial/순 용량/chain-rule은 면적 현열 부품의 원 예산을 유지한다. C/N도 원 부품 예산을 유지한다.
새 수관/공기/증기/reduced-energy 장부는 실제 항 절댓값 합의3e-13, 최소값1 같은 바닥 없이 검사한다.
이 수지는 수관/공기·공기 증기의 축약 장부이며 식물 액수/조직·온실 구조의 전체 에너지 수지가 아니다.

출력은 새 model/schema/정책·code/component/profile SHA, raw/정규 input 및 component input/calculation SHA,
원 stage 선언·모든 원 부품, Tc/LAI/Ldot·Ccan/Cair/vpAir·Tc', 기관5/과실C/N100/기후3 미분과
각 장부 잔차/예산·-E를 보존한다. 입력 snapshot과 반환 수량은 별도 복사본이다.
scope=software_research_only, claim_scope=synthetic_explicit_lai_joint_rhs_only,
G0_G4=not_assessed, time_coordinate=derivatives_per_second_no_time_advance다.

수용은 app 없는 독립 Decimal120의 crop/startup/광학·열/증기 기준과 기존10공동 조건 대사,
같은/다른 LAI·공급/빈 과실·역 교환/명시 제거·순0 총 회전·Tin/Tout/Tref/Q의 signed 변화,
같은 전달 값/각1회와 중복 잠열/유출 열·반쪽 보정의 반례/단위·영역/고갈/수치 hold다.
비교는 max(32ulp(reference),5e-12*abs(reference))다. 합/차로 작은 재고 미분을 만드는 곳은
독립 원 항 절댓값 합의64ulp도 허용한다. 큰 항의 상쇄에 작은 결과 상대 오차만 요구하지 않는다.
이는 해당 합/차에만 적용하며 전체1 같은 임의 바닥은 없다. 원 항도 모두0인 독립 참조0은 정확0,
복원 Tc는2e-13 K이며 현장 오차/적분 수렴 기준이 아니다.
fresh에서 참조 bytes 재생·동일 재실행/입력 불변·기존 전체 RHS/적분/DB/CLI/network/쓰기0,
WSL/원 자료·4root 보존을 확인한다. 다음은 고정 기관의 짧은 구간→정확 사건→다음 구간/분할 재개다.
새 태양/PAR/NIR·환기/CO2 조립·출현 질량/공급/관리·현재 farm/서명·같은 UTC3D는 별도다.
