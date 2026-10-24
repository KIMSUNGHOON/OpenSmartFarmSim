# 독립 면적·명시 총 용량 흐름의 현열 경계 v1

상태: **순간 연구 커널 수용**. [260검사·fresh100사례](../research/crop-area-canopy-energy-20261024.md).
[1차 대조](../research/explicit-area-canopy-energy-primary-sources-20261024.md)와
[연속 결합 설계](crop-geometry-carbon-coupling-research-v1.md)의 순수 순간 부품이다.
새 프로젝트의 **표현된 열용량 회계**이며 실제 잎 물성·질량/엔탈피·온실 feedback 검증이 아니다.
기존 SLA/탄수화물 운반 모델·프로필·저장 결과는 바꾸지 않는다.

`calculate_area_energy(*, inputs)`는 닫힌 `{input_id,origin=synthetic,values}`를 받는다.
ID는1–200 ASCII이며 모든 quantity는 닫힌 `{value,unit}`·bool 제외 finite int/float다.
필드는 leaf_area_index(m2_leaf/m2_floor, 양수), leaf_area_index_rate(m2_leaf/m2_floor/s, signed),
leaf_heat_capacity(J/m2_leaf/K, 양수), capacity_inflow/outflow(J/m2_floor/K/s, 각각0 이상),
canopy_temperature/incoming_capacity_temperature/outgoing_capacity_temperature/reference_temperature(degC),
nonmaterial_heat(W/m2_floor, signed)다. 누락/여분·단위/비유한·0 LAI/용량을 hold한다.
Tc/Tin/Tout는 기존 합성10–34°C 창이며 고정 회계 Tref는 유한·온도 복원이 가능해야 한다.
유량0이어도 Tin/Tout/Q를 명시하며 알려지지 않은 값을0·Tc·기온으로 채우지 않는다.

L과 Ldot는 같은 순간의 고정 footprint/추적 범위다. k=leaf_heat_capacity는 이 판본/후속 실행에서 고정된 명시 가정이며
kdot·다른 상태에 따른 물성 변화는 미지원이다. 이 함수 자체가 연속 실행의 k 고정을 승인하지 않는다.
입력/출력은128KiB 이하이고 SLA·leaf C·질량당 cp나 분배/제거 탄소를 받거나 역산하지 않는다.

```text
C = k*L
Cdot_geometry = k*Ldot
Cdot_transport = gin-gout
Uref = C*(Tc-Tref)
Qin = gin*(Tin-Tref); Qout = gout*(Tout-Tref)
Qmaterial = Qin-Qout; Udot = Qnonmaterial+Qmaterial
Tdot = [Qnonmaterial+gin*(Tin-Tc)-gout*(Tout-Tc)]/C
C*Tdot+(Tc-Tref)*Cdot_geometry = Udot
```

두 Cdot 차이는 순량 규모 `8*ulp(max(abs(Cdot_geometry),abs(Cdot_transport)))`만 허용한다.
gin−gout는 fsum으로 계산하며 큰 총 유량으로 허용 오차를 키우지 않는다. 주어진 Ldot/총 유량을 보정하지 않는다.
에너지 잔차는 실제 온도·용량/총열 항 규모의64ulp로 검사한다. 이는 binary64 회계 기준이며 생리 오차가 아니다.
곱/나눗셈의 비유한·양수/음수 소실과 기준 온도 왕복 오차>2e-13 K는 hold다.
Tdot는 기준 온도와 무관한 온도차 식으로 계산하고, 별도 chain-rule 총열과 대사한다.

모든 U/Qin/Qout/Qmaterial/Udot는 signed다. Tout=Tc를 명시하면 기존 잘 섞인 유출 경계가 되고,
다른 Tout는 별도 용량 저장소/선택 유출의 합성 가정이다. 실제 수관 온도분포를 검증했다는 뜻이 아니다.
gin=gout>0·Ldot0인 순0 회전에서도 열 이동이 있을 수 있다. 유출을 자동으로 공기 열에 더하지 않는다.
비물질 열은 현재 경계의 순열 입력이며 히터/구매 에너지·잠열/증산을 별도로 계산하지 않는다.

출력은 model/code/numeric-component·raw/정규 input/calculation SHA, 원 입력 복사본, L/Ldot·C/Cdot·Uref,
각 총 용량/현열·운반/비운반/합계 열률·Tdot·chain-rule 항과 용량/에너지 잔차/예산이다.
scope=software_research_only/claim_scope=synthetic_area_capacity_bookkeeping_only/G0_G4=not_assessed를 고정한다.

수용은 app 없는 독립 Decimal 참조의 고정/증가/감소·큰 총 회전/순0·유입/유출 온도 차이·양/0/음 열,
Tref 이동의 signed 에너지와 Tdot 불변·기존 SLA 운반의 같은 조건 대사,
큰 총 유량 속 잘못된 순량/단위·빈 수관/물성·missing/NaN/소실·기준 온도 실패의 거부다.
fresh에서 원 참조 byte 재생/동일 결과·입력 불변·기존 SLA 운반/탄소·적분/DB/CLI/network/쓰기0,
WSL/원 자료 보존을 확인한다. 다음 공동 RHS/짧은 궤적·사건/재개·실제 물/조직/물성·G0–G4는 별도다.

독립 참조는 Decimal120자리와 자체 dyadic 입력100사례다. 구현의 중심 온도차 식과 달리
`[Udot-(Tc-Tref)*Cdot]/C`를 직접 계산한다. 원량 비교는 `max(32ulp(reference),3e-13*abs(reference))`,
독립 참조0은 정확0이다. 총 유량2^40의 순0 회전도 포함한다. 이는 소프트웨어 수치 기준이며 현장 정확도가 아니다.
