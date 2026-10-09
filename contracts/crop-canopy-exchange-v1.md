# 수관·공기 순간 교환 연구 계산 v1

상태: [순수 순간식의 로컬 수용](../research/crop-canopy-exchange-implementation-20261009.md).
`crop-climate-coupling`의 첫 계산 자식이며 전체 결합 수용이 아니다.
선행은 [고정 원문·매개변수 검토](../research/crop-canopy-exchange-baseline-20261009.md)다.
수확 writer/DB·외부 농장 자료를 기다리지 않고 순수 식을 개발할 수 있다.
전체 기후·자원 연결은 기존 생산/저장·수확 단계 뒤에 진행한다.

## 핵심 파일과 입력

핵심 5파일: `backend/app/crop_canopy_exchange.py`,
`backend/tests/test_crop_canopy_exchange.py`, 이 계약,
`fixtures/crop-canopy-exchange-reference-parameters-v1.json`,
`fixtures/crop-canopy-exchange-reference-cases-v1.json`.
새 의존성·DB·API·Run·3D 장면을 추가하지 않는다.

`calculate_exchange(forcing=..., profile=ReferenceParameters(raw_bytes))`는
닫힌 `input_id`, `origin`, `values` 블록과 해시 고정 참조 프로필을 받는다.
`origin`은 `synthetic` 또는 `reference_calculation`이다. 입력 ID가 자료 권리를 승인하지 않는다.

| 입력 | 단위 | 이 판본의 계산 경계 |
| --- | --- | --- |
| leaf_area_index | m2_leaf/m2_floor | 유한, 0 이상; 임의 0.01 대체 없음 |
| canopy_temperature, air_temperature | degC | 프로젝트 합성 계산 창 10–34; 검증된 정확도 범위가 아님 |
| air_vapor_pressure | Pa | 유한, 0 이상; 상대습도로 자동 변환하지 않음 |
| air_capacity_density | kg_air/m3 | 명시 유한 양수; 고도/동적 밀도로 대체하지 않음 |
| canopy_vapor_resistance | s/m | 명시 유한 양수; 광/CO₂·기공 폐쇄식을 추정하지 않음 |

기공 저항 0은 이 판본에서 거부한다. source `rSMin=82`를 모든 입력의 승인된
최솟값으로 적용하지 않는다. 계수·표현식 9개는 프로필의 원문 포인터를 따른다.
`alfaLeafAir`의 잎 면적 해석과 온도 창의 프로젝트 판단을 원문 명시와 구분한다.

## 출력·방향과 수지 경계

`svp = a * exp(b*Tcan/(Tcan+c))`, `dvp = svp-vpAir`,
`vec = 2*rhoAirCap*cPAir*LAI/(L*gammaPsych*(rB+rS))`,
`E = vec*dvp`, `H = 2*alfaLeafAir*LAI*(Tcan-Tair)`, `LE = L*E`다.
프로필의 고정 원식 `sensible(abs(hec),...)`에서 이 판본의 계수는 양수다.

출력은 입력/프로필·모델 해시, 포화압/압력차/전달계수, E(kg_water/m2_floor/s),
H·LE(W/m2_floor), 아래의 부호 쌍과 합 잔차를 포함한다.
양수는 수관→공기다. 음의 E/LE를 0 또는 양의 증산으로 바꾸지 않는다.
음수는 원식의 역방향 수증기 교환이며 검증된 잎 결로/액막/흡수 모델이 아니다.

| 전달 | 수관 쪽 항 | 공기 쪽 항 |
| --- | --- | --- |
| 물 | −E | +E |
| 현열 | −H | +H (공기 현열) |
| 잠열 | −LE (수관 열) | +LE (수증기 에너지 장부) |

이 부호 쌍은 **연결 시 사용할 국소 교환 장부**다. 실제 저장소/온도를 적분하지 않는다.
공기 현열에 +LE를 다시 더하지 않으며 기존 `thermal-v1`의 잠열 차감과 중복 적용하지 않는다.
LAI=0의 유한 입력에는 E/H/LE=0이다. 이 사실은 `capCan=capLeaf*LAI`가 0인
전체 수관 온도 ODE를 해소하지 않는다. 수관 온도를 기온으로 대체하지 않는다.

## 수용 기준

1. 고정 원본 SHA·6개 식 포인터·9개 계수/차원·BSD 고지·실제 native CLI 판단을 대사한다.
2. 구현을 import하지 않는 Decimal 80자리 참조의 고정 사례로 증발/역방향·등온·빈 수관을 비교한다.
   binary64 대조 허용치는 상대 `2e-14`·0은 정확한 0; 현장 정확도의 합격선이 아니다.
3. 단위/닫힌 스키마·bool/비유한·음수·프로필 변경·온도 경계 이탈·계산 overflow/underflow를 거부한다.
   부호·LAI 선형성·저항 증가 효과·현열 방향·잠열 관계와 국소 부호 합을 검증한다.
4. 같은 입력의 canonical 해시/값 재현, 입력 불변, 기존 작물/열 계산 회귀와 원 종료·소유 자원을 기록한다.
5. 결과의 `software_research_only`, `synthetic_exchange_math_only`, `G0_G4=not_assessed`를 유지한다.
   수관 온도/기공/CO₂·물/영양 스트레스의 동적 해, 급액/구매 용수·에너지·비용은 산출하지 않는다.

```sh
PYTHONPATH=backend nice -n 19 backend/.venv/bin/python -m pytest -q backend/tests/test_crop_canopy_exchange.py
```
