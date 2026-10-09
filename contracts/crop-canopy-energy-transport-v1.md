# 가변 수관 열용량의 운반·적엽 계산 v1

상태: `crop-climate-variable-canopy-energy`의 작은 순수 계산 계약이다.
[고정 LAI 동적 자식](crop-climate-coupling-v1.md)의 의미·프로필·저장 결과를 바꾸지 않는다.
전체 작물·기후 RHS/적분·사용자 실행·실시간 UI는 후속이다.

## 경계와 핵심 파일

핵심 5파일은 `backend/app/crop_canopy_energy_transport.py`,
`backend/tests/test_crop_canopy_energy_transport.py`, 이 계약,
`research/crop-canopy-energy-transport-reference.py`,
`fixtures/crop-canopy-energy-transport-reference-cases-v1.json`이다.
원문과 현재 생장식 검토는 별도 research 기록으로 남긴다.
새 물성·농장 자료·패키지·DB/API·checkpoint·3D를 등록하지 않는다.

현재 생장 모델의 `leaf`는 탄수화물 환산량이고 `LAI=sla*leaf`다.
이 계약은 그 **표현된 잎 면적에 부여한 열용량 재고**의 일관된 회계다.
탄수화물 질량을 실제 잎의 수분/건물 질량으로 동일시하지 않는다.
호흡 탄소 손실의 대사열·실제 잎 수분/현열·뿌리로부터의 물 운반은 계산하지 않는다.
원 Chapter8의 `capCan=capLeaf*LAI`만으로 아래 유입 온도나 이 경계가 증명되지는 않는다.
`capLeaf`, 유입 온도는 명시 합성 가정이며 실제 품종 물성/농장 적용은 hold다.

기존 `crop_growth_rates.ReferenceParameters`의 고정 원 bytes와 `sla`만 재사용한다.
그 프로필의 SHA/단위/출처/고지는 바꾸지 않는다. 신규 계수를 숨은 기본값으로 넣지 않는다.

## 닫힌 입력과 출력

`calculate_transport(forcing=..., profile=...)`와
`calculate_leaf_removal(event=..., profile=...)`를 제공한다.
두 입력 모두 정확히 `input_id`, `origin=synthetic|reference_calculation`, `values`다.
ID는 1–200자의 비어 있지 않은 문자열이고 각 값은 정확히 `{value, unit}`다.
bool/문자열 수치·비유한·누락·여분·다른 단위/프로필은 거부한다.

| 필드 | 연속 운반 | 적엽 사건 | 단위·경계 |
| --- | --- | --- | --- |
| leaf_carbohydrate | 필수 | 필수 | mg_CH2O/m2_floor; 양수 |
| leaf_allocation, leaf_maintenance, leaf_removal | 필수 | 없음 | mg_CH2O/m2_floor/s; 각각 0 이상, 순변화량으로 대체 금지 |
| leaf_heat_capacity | 필수 | 필수 | J/m2_leaf/K; 명시 양수 |
| canopy_temperature | 필수 | 없음 | degC; 합성 창 10–34 |
| incoming_capacity_temperature | 필수 | 없음 | degC; 합성 창 10–34, allocation=0이어도 명시 |
| reference_temperature | 필수 | 필수 | degC; 고정 회계 기준, 물리 온도 창과 별개 |
| leaf_removed | 없음 | 필수 | mg_CH2O/m2_floor; 0 이상이며 leaf보다 작음 |
| canopy_sensible_energy | 없음 | 필수 | J/m2_floor; **부호 있는** Uref |

온도차와 유도 온도를 binary64로 표현하지 못하거나 기준온도 왕복 오차가
2e-13 K를 넘으면 `NUMERIC_HOLD`다. 극단적 기준온도에 의한 정보 소실을 허용하지 않는다.
각 함수는 정규화 입력/입력 SHA·코드 SHA·모델 판본·생장 프로필 SHA와 단위 있는 결과를 반환한다.
입력을 변경하지 않으며 계산 접수/승인 Run/새로운 영속 사건은 만들지 않는다.
출력은 `software_research_only`, `synthetic_canopy_capacity_inventory_only`,
`G0_G4=not_assessed`다.

## 연속 용량·에너지 경계

각 shared trial에서 생장 RHS가 내놓은 **총** allocation/maintenance/continuous removal을 사용한다.
`capLeaf`와 `sla`는 이 모델 판본에서 일정하다. 단위는 바닥면적 기준이다.

```text
LAI = sla*leaf
C = capLeaf*LAI                             [J/m2_floor/K]
g  = capLeaf*(sla*allocation_leaf)            [J/m2_floor/K/s]
dm = capLeaf*(sla*maintenance_leaf)           [J/m2_floor/K/s]
dr = capLeaf*(sla*continuous_removal_leaf)    [J/m2_floor/K/s]
Cdot = g-dm-dr
Uref = C*(Tc-Tref)                           [J/m2_floor]
Qin  = g*(Tin-Tref)                          [W/m2_floor]
Qout_maintenance = dm*(Tc-Tref)
Qout_removal = dr*(Tc-Tref)
Qmaterial = Qin-Qout_maintenance-Qout_removal
Tc'_material = g*(Tin-Tc)/C                  [K/s]
C*Tc'_material + (Tc-Tref)*Cdot = Qmaterial
```

유출은 현재 Tc의 용량을 제거한다는 **명시 경계 선택**이다.
Qout은 기준온도보다 차가운 용량에 대해 음수일 수 있다. 절댓값/0 clamp를 하지 않는다.
g=dm+dr>0이고 Tin≠Tc이면 순 LAI 변화는 0이어도 Tc'_material은 0이 아니다.
따라서 순 leaf/LAI 변화만으로 유입/유출 에너지를 구성하지 않는다.
`Qmaterial`은 생장/호흡 대사열을 뜻하지 않는다.

## 적엽 사건과 후속 공동 상태

사건 직전의 Uref와 leaf로 Tc를 유도한다. 유출 온도는 그 Tc다.

```text
leaf_after = leaf_before-leaf_removed
Cbefore = capLeaf*(sla*leaf_before)
Cafter  = capLeaf*(sla*leaf_after)
Tc_before = Tref+Ubefore/Cbefore
Uafter = Ubefore*(Cafter/Cbefore)
Uout = Ubefore-Uafter
Tc_after = Tref+Uafter/Cafter
```

0 제거는 항등이다. 제거 후 양의 수관은 같은 온도를 유지하며 Ubefore=Uafter+Uout을 대사한다.
Uout의 부호를 유지한다. 초과 제거는 `EVENT_HOLD`, 전량 제거/초기 leaf=0은
`EMPTY_CANOPY_HOLD`다. 빈 수관/재진입의 온도 상태 전환이 없으므로 자동 재설정하지 않는다.
양의 제거가 leaf/C에서 반올림으로 사라지거나 비영 에너지 변화가 표현되지 않으면 hold한다.

후속 공동 RHS는 **부호 있는 Uref를 기본 상태**로 하고 같은 stage의 leaf에서 C/Tc를 유도한다.
`Uref'=Qcan-H-LE+Qmaterial`과 기존 공기 현열·수증기 질량을 함께 적분한다.
Tc와 leaf를 별도로 RK4 적분하고 그 곱을 저장 열로 선언하면 곱의 절단 오차를
반올림 잔차라고 잘못 주장할 수 있다. 이 계약은 아직 공동 적분을 수행하지 않는다.
새 공동 모델은 기존 121상태의 전부 0 이상 검사·상수 Tcan Fraction clock·checkpoint와
호환되지 않는다. 새 상태/clock/수치/관리 순서/continuation 판본이 필요하다.

## 사전 수용 기준

1. app을 import하지 않는 Decimal80 참조로 같은/차가운/따뜻한 유입, 유지 손실,
   연속 제거, 순변화 0의 총 흐름, 여러 Tref와 음의 U/Qout, 부분/0 적엽을 대사한다.
2. 참조 스칼라 상대 오차 3e-13(기대값 0은 절대 2e-13), 온도/온도차 절대 2e-13 K다.
   물질 RHS 에너지 잔차는 총 절댓값 장부 합의 3e-13 이내다.
   사건 에너지 잔차는 총 절댓값 에너지 합의 3e-13 이내이며 Tc 보존은 2e-13 K다.
   이 합성 산술 기준은 실제 농업/물성 정확도 기준이 아니다.
3. Tref 이동에 대해 C/Cdot/Tc'_material/사건 Tc는 불변이고
   Uref_new=Uref_old-C*delta, Qmaterial_new=Qmaterial_old-Cdot*delta다.
   순변화만 쓴 오식·모든 Qout 양수 처리·적엽 U 고정의 반례를 포함한다.
4. 단위·닫힌 스키마·명시 provenance·프로필 변조·부호·온도 창·빈 수관·초과 제거·
   overflow/underflow/수치 정체를 거부한다. 승인된 입력/기존 모델/결과/미리보기는 보존한다.
5. 집중 시험과 기존 생장·열·순간 교환·고정 LAI 동적 회귀를 실행하고 실제 종료/FD/
   정확한 소유 정리·512MiB 단일/1GiB 소유+보호 프로세스 RSS 상한을 기록한다.
6. 이 자식만 수용한다. 전체 결합·물/양분·구매 에너지·경제·UI/U3·실제 G0–G4는 별도다.
