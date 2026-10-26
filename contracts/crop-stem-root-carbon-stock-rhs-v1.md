# 기관별 줄기·뿌리 탄소 재고 RHS — 연구 v1

상태: [신규278/관련255·533검사와 독립 fresh72조건/1,944수치 수용](../research/stem-root-carbon-stock-rhs-20261027.md)의 합성 순간 재고 RHS. [같은 stage 배분](crop-stem-root-partition-climate-rhs-v1.md)의 다음 자식이며 시간 전진/기관 출현/길이 feedback은 후속이다.

`evaluate_rhs(*, scenario, leaf_stocks, stem_root_stocks, growth_profile, cohort_profile, transport_profile, exchange_profile)`.
scenario는 [명시 잎 재고](crop-leaf-carbon-stock-rhs-v1.md)의 입력에서 plant_state.stem_root와 removals.stem_root도 제외한다. 두 집계를 중복 입력하면 값이 같아도 거부한다. 잎 재고·나머지 원 상태/forcing/geometry 계약은 유지한다.

stem_root_stocks는 닫힌 input_id/origin/policy/model_floor_area/compartments다. 같은 input_id, synthetic origin, `stem-root-stocks-uniform-maintenance-explicit-removal-v1`, 양의 공통 m2_floor를 요구한다. 원 순서의1–512행은 compartment_id/kind/carbon/sink_weight/removal이다. 고유 bounded ID, internode 또는 root_system과 정확히 하나의 root_system을 요구한다. C_i는 mg_CH2O/m2_floor, 상대 sink는1, R_i는 mg_CH2O/m2_floor/s의 유한 비음수 정상 binary64 또는0다. 선언 목록이 이 새 합성 상태의 완전한 재고이며 기존 저장 형태/실제 초기 C를 역산하지 않는다.

정확한 binary64 C_i와 R_i 합계를 각각 한 번 반올림해 원 aggregate 상태/제거를 조립한다. 원 상대 sink·같은 floor와 함께 source RHS를 한 번 평가한다. 원 code/profile/input/output hash와 scope·조립된 집계/기관 ID를 대사한다. source hold는 복구하지 않는다. G/유입·성장 원가·buffer 조정·잎/과실/기후를 다시 계산하거나 두 번 차감하지 않는다.

원 고정 profile의 유지호흡 식은 공통 온도에서 aggregate C에 선형이다. 원 M을 `M_i=M*C_i/(정확 ΣC_i)`로 보존 분배하는 명시 연구 정책을 선택한다. 이는 실제 기관별 호흡 검증이 아니다. 합계 C>0이면 원 M>0과 양의 각 C에 양의 정상 M_i가 필요하다. 합계 C=0이면 원 M도 정확히0이어야 하며 모든 M_i=0인 별도 분기를 사용한다. 균등 나눔/0나눗셈/새 계수는 없다.

각 C_i′=g_i−M_i−R_i이며 C_i=0에서 미분<0은 DEPLETED_STATE_HOLD다. 양의 재고에서 음의 순간 미분과0에서 유입으로 충당되는 연속 flow-through는 허용한다. 제거를 clipping하거나 임의 dt로 현재 재고와 비교하지 않는다. 각 미분 합계를 한 번 반올림한 stem_root 미분은 파생 진단이며 별도 독립 입력/적분 상태가 아니다.

원 결과 전체는 source_stage에 보존한다. stem_root_rates/총 현재 C·유입·유지호흡·제거·미분, 원 aggregate와의 반올림 잔차/예산을 기록한다. 새 최상위 미분과 adjusted_carbon.derivatives는 같은 파생 합계다. 실제 개별 미분/유지호흡/제거 합계와 원 잎·과실·성장호흡·buffer/P를 써 전체 C/줄기·뿌리 수지를 다시 대사한다. 마지막 기관에 잔차를 몰거나 전체 기관을 rescale하지 않는다. 원 비탄소 수지/나머지 값은 유지한다.

원/새 코드와4profile·정책·raw/정규 입력·계산 SHA, 원 ID/순서·common floor·입력/출력 각512KiB를 결속한다. 성장 profile의 사용 계수 사전 전체도 고정 원문과 같아야 한다. 원 잎 목록 타입은 JSON capture 전에 검사해 tuple의 암묵적 배열 변환을 거부한다. 양수의0/subnormal 유실, overflow·원 변조·단위/중복 집계/수지 불일치는 hold다. 행 상한512가 전체512잎/전체 최대 요청 수용이라는 뜻은 아니다. 실제 같은 짧은 ID 입력의256기관 출력362,168bytes는 통과했고512기관 출력은 이 새512KiB 한도로 보류됐다. caps/원 ID를 바꾸지 않았다. 반올림 예산64(n+8)ulp는 수치 대사 허용치이며 생물학적 오차가 아니다.

수용 기준: 원6조건·다양한/부분0/전체0 재고와 sink·명시 제거/고갈/flow-through·중복 집계/순서/분모/단위·원 코드/profile/hash·집계/양수 underflow/bytes 경계, 독립 Decimal 기관/전체 C 수지와 호출당 원 구성 함수1회·입력/원 결과 불변·fresh/자료·GUI/WSL 보존이다.

scope=software_research_only, claim=synthetic_individual_stem_root_carbon_rhs_only, G0_G4=not_assessed, derivatives_per_second_no_time_advance다. 같은 재고의 공동 적분/재개·새 기관 초기 비용·초기 source 계보/잔량·공급 제한 길이/면적→불변 저장/같은 상태3D는 후속이다. 실제 품종/독립 농장 검증과 예측·추천 게시 관문은 별도다.
