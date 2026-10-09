# 작물·기후 결합의 단계와 첫 동적 자식 v1

상태: 전체 `crop-climate-coupling`은 미완료다. 첫 구현 경계는
**`crop-canopy-air-dynamics`의 고정 LAI 수관·공기·수증기 연구 계산**이다.
[순간 교환 계약](crop-canopy-exchange-v1.md)과
[인터페이스 조사](../research/crop-climate-interface-audit-20261009.md)를 선행 근거로 삼는다.
실제 품종/농장 적용·관문과 사용자 실행/실시간 UI는 별도다.

## 첫 자식의 핵심 파일과 입력

핵심 5파일은 `backend/app/crop_canopy_air_dynamics.py`,
`backend/tests/test_crop_canopy_air_dynamics.py`, 이 계약,
`research/crop-canopy-air-dynamics-reference.py`,
`fixtures/crop-canopy-air-dynamics-reference-cases-v1.json`이다.
기존 해시 고정 순간 교환 프로필·BSD 고지를 재사용한다. 새 패키지/DB/API/장면을 추가하지 않는다.

`evaluate_rhs(scenario=..., profile=...)`와
`integrate(scenario=..., profile=..., step_seconds=..., step_count=...)`를 제공한다.
닫힌 scenario는 `input_id`, `origin=synthetic|reference_calculation`,
`state`, `parameters`, `forcing`을 갖는다. 모든 수치는 명시 `{value, unit}`이다.
합성 입력의 ID/표시가 실제 자료 권리·QC·관문 승인을 대신하지 않는다.

| 블록 | 필드 | 단위·경계 |
| --- | --- | --- |
| state | canopy_temperature, air_temperature | degC; 기존 합성 창 10–34, 현장 정확도 범위 아님 |
| state | air_vapor_mass | kg_water/m2_floor; 유한 0 이상 |
| parameters | leaf_area_index | m2_leaf/m2_floor; **고정 양수**, 0 대체 금지 |
| parameters | leaf_heat_capacity | J/m2_leaf/K; 명시 고정 양수, 실제 품종 값으로 승인하지 않음 |
| parameters | air_volume_per_floor_area | m3/m2_floor; 명시 고정 양수, V/A |
| parameters | air_capacity_density | kg_air/m3; 명시 고정 양수; 동적 밀도/건공기 밀도와 동일시하지 않음 |
| parameters | canopy_vapor_resistance | s/m; 명시 고정 양수; 기공 폐쇄식 없음 |
| parameters | vapor_gas_constant | J/kg_water/K; 명시 고정 양수, 숨은 기본값 없음 |
| forcing | canopy_external_heat, air_external_sensible_heat | W/m2_floor; 각각 저장소에 들어오는 부호 외부 열 |
| forcing | air_external_vapor | kg_water/m2_floor/s; 공기로 들어오는 부호 외부 수증기 |

외부 forcing은 이 작은 구간 동안 일정하다. `canopy_external_heat`는 수관의
흡수 복사/외부 열을 **명시 가정**으로 준 값이다. 기상 일사에서 자동 생성하지 않는다.
`air_external_sensible_heat`에는 수관 H/LE를 다시 넣지 않는다.
음의 외부 수증기는 명시 질량 유출이며 그에 대응하는 잠열 장부도 함께 유출된다.
환기·커버·바닥·히터·PAR/CO₂·기공·배지·구매량은 아직 계산하지 않는다.

## 상태 방정식과 보존 경계

기존 `thermal-v1`은 수관까지 포함한 하나의 `C_eff`와 잠열 차감으로 정의됐다.
그 `euler_step`/`C_eff`를 별도 공기 저장소로 사용하지 않는다.
새 식은 원 GreenLight Chapter8의 수관/공기 현열·증산 항을 사용하지만
**아래의 축소 저장소·경계와 질량 상태는 프로젝트 선택**이다.
원 전체 온실 모델의 재현이나 현장 생산 모델로 표시하지 않는다.

고정 `LAI`, `capLeaf`, `h=V/A`, `rhoAirCap`, 원 프로필의 `cp`, `L`에 대해

```text
Ccan = capLeaf * LAI                   [J/m2_floor/K]
Cair = h * rhoAirCap * cp              [J/m2_floor/K]
e_air = m_v * R_v * (Tair+273.15) / h   [Pa]
E, H, LE = same-stage canopy exchange; LE = L*E
dTcan/dt = (Qcan - H - LE) / Ccan       [K/s]
dTair/dt = (Qair + H) / Cair           [K/s]
dm_v/dt = E + Fv                       [kg_water/m2_floor/s]
```

원 `/Capacities/capVpAir`의 선언 단위/식 차원 불일치와 온도 변화 항 생략을
그대로 가져오지 않는다. 수증기 **질량**을 적분하고 기온과 함께 압력을 매번 유도한다.
고정 `M_da/A`가 있을 때 `m_v=(M_da/A)*w`와 동등한 저장 표현이다.
이 모델은 실제 건공기 질량/총압을 계산하지 않는다. 두 열용량은 일정하며
수증기/액수의 현열과 질량 이동의 현열은 생략한 축소 모형이다.

한 RHS/stage에서 E/H/LE를 한 번 평가하여 양쪽 항에 같이 사용한다.
공기 **현열**에 LE를 더하지 않는다. 잠열은 `L*m_v` 장부에 저장된다.
고정 기준온도 Tref에 대한 축소 열·수증기 에너지의 변화는

```text
d[Ccan*(Tcan-Tref) + Cair*(Tair-Tref) + L*m_v]/dt
    = Qcan + Qair + L*Fv
```

다. 수관 물 경계 장부는 `-E`이며, `dm_v/dt - E - Fv=0`을 대사한다.
**이는 수증기 저장과 외부 물 전달의 수지**다. 계산하지 않은 수관 액수 저장·급액
충분성·농장 전체 물 보존을 증명하지 않는다. 외부 수관 물은 고갈을 계산하지 않는 경계다.
모든 상태/열/질량 장부는 바닥면적 기준이다. 총량 변환에는 같은 A를 단 한 번 곱해야 한다.

부호 E<0는 원 순간식의 역교환 연구만 허용한다. 잎 결로/액막·재흡수의 예측이 아니다.
각 초기/stage/종료 상태에서 같은 고정 포화압 식으로 `e_air >= satVp(Tair)`면
`BULK_SATURATION_HOLD`다. 음수 질량/비유한/온도 창 이탈도 중단한다.
RH clamp·온도 대체·누락값 0 대체 없이 결과를 거부한다.
bulk 불포화가 차가운 잎/커버의 결로 부재를 보장하지 않는다.
LAI=0은 `EMPTY_CANOPY_HOLD`; 빈 수관의 별도 온도 상태 전환은 후속 계약이다.

## 적분·수용

적분은 결정적 고정 걸음 RK4다. 동일 stage의 세 상태를 함께 평가한다.
`step_seconds`는 명시 유한 양수, `step_count`는 bool이 아닌 정수 1–4096이며
총 구간은 600초 이하의 합성 연구 창이다. 이 상한은 정확도/안정성 보장이 아니다.
각 확정 종료 상태를 elapsed seconds로 반환하며 UTC/농장 작기/기존 checkpoint를 발급하지 않는다.
중간 stage가 부적합하면 전체 호출을 hold한다. 출력은 입력/코드/원 프로필 해시,
수치 설정 해시, 원 상태·누적 E/H/LE·외부 경계와 수지 잔차를 보존한다.

1. 원 순간 교환의 고정 6식/9계수·고지와 새 상태/단위/열용량/질량 선택을 대사한다.
2. app을 import하지 않는 Decimal80 참조로 양/역방향 교환·등온·외부 경계의
   독립 RHS와 짧은 궤적을 비교한다. 온도만 바꾼 고정 질량 압력도 확인한다.
3. 수관/공기 온도가 서로 다르게 움직이고 새 수증기 저장/온도가 다음 E를 바꾸는지 확인한다.
   H/LE 중복·공기 현열에 LE 주입·고정 vpAir·LAI=0 대체의 반례를 검사한다.
4. 축소 물/에너지 수지는 RHS 상대 2e-13, 짧은 궤적 에너지 절대 1e-7 J/m2_floor,
   물 절대 1e-13 kg_water/m2_floor로 대사한다. RHS 참조 상대 3e-13,
   60초 궤적 온도 절대 2e-11 K/질량 절대 2e-14 kg_water/m2_floor다.
   해당 합성 사례의 binary64 오차 검사이며 현장 정확도 기준이 아니다.
5. warm/reverse/forced 60초 사례의 dt=4/2/1초와 독립 Decimal dt=0.25초 해를 비교해
   각 상태와 누적 E/H/LE의 오차가 각 반분에서 8배 넘게 줄어드는지 확인한다.
   RK4의 점근 16배보다 낮은 사전 수치 기준이며 zero equilibrium은 정확히 유지한다.
6. 닫힌 스키마·단위·비유한/bool·부호·빈 수관·bulk saturation·stage 실패·overflow/
   underflow/수치 정체·예산을 검사하고 원 입력/기존 작물·열·미리보기/소유 자원을 보존한다.
7. 출력은 `software_research_only`, `synthetic_canopy_air_dynamics_only`,
   `G0_G4=not_assessed`다. 생산·수확·급액·구매 에너지·마진·추천을 내지 않는다.

## 전체 결합으로 이어지는 의존성

첫 자식 수용 뒤에 **동적 온실 경계/복사·CO₂·기공**과 **작물 공동 적분**을 나눈다.
작물 공동 적분은 성장 RHS의 LAI를 돌려받고 동적 Tcan/PAR/CO₂를 같은 stage에 공급해야 한다.
현재 piecewise constant Tcan의 Fraction 온도합 clock·121상태 checkpoint를 재사용하지 않는다.
새 상태/clock/입력/수치·checkpoint 판본과 관리 사건의 순서를 고정한다.
LAI가 변할 때 `capCan=capLeaf*LAI`의 열용량 변화·새 잎/적엽의 현열 운반은
[가변 용량 계약](crop-canopy-energy-transport-v1.md)의 별도 작은 자식으로 고정했다.
[2026-10-10 로컬 수용](../research/crop-canopy-energy-transport-implementation-20261010.md)은
총 allocation/maintenance/removal, 명시 Tin/Tref, current-Tc 유출과 부분 적엽 U/C 비례다.
이는 실제 조직 물성/대사열을 검증한 경계가 아니며 미확인 실제 적용은 hold다.
후속 공동 RHS/적분의 수관 기본 상태는 **signed Uref**이고 `Tc=Tref+Uref/Ccan`을
같은 stage의 leaf에서 유도한다. `Uref'=Qcan-H-LE+Qmaterial`과 공기 현열/수증기·탄소를 함께 대사한다.
Tc와 leaf를 각각 적분한 뒤 곱의 절단 오차를 반올림 잔차라고 주장하지 않는다.
부호 있는 에너지를 기존 전부 0 이상 상태 검사에 넣거나 121상태 checkpoint에 덧붙이지 않는다.
`Ccan*dTcan`만으로 전 기간 에너지 보존을 주장하지 않는다.
그 뒤 물/양분·구매 에너지→같은 농장/배치 사용자 실행→Decimal 경제를 연결한다.
첫 자식만으로 부모 `crop-climate-coupling`이나 U3/생산 관문을 체크하지 않는다.

[새 공동 순간 RHS 계약](crop-climate-joint-rhs-v1.md)은2026-10-10
[새51/기존412·독립1,290스칼라](../research/crop-climate-joint-rhs-implementation-20261010.md)로 로컬 수용했다.
기관5·과실 C/N100·기후3의 새108상태와 초당 미분만 정의한다.
RGR50은 명시 forcing이고 새 적분 상태가 아니다. 다음 짧은 공동 적분에서
sampling·shared stage·dynamic T24/Tsum·signed U 검사·시간/장부를 계약한다.
원자적 적엽/과실 관리·새 continuation/저장·API·같은 UTC3D는 별도 수용한다.
