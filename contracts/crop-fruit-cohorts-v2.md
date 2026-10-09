# 명시적 착과 과실 구획의 순간 결합 — v2

상태: **순간 수요/구획 결합의 로컬 소프트웨어 수용; 시간 적분 수용 전**.
[v1](crop-fruit-cohorts-v1.md)의 원식/이동과
[별도 명시적 배분](crop-fruit-allocation-v1.md)을 결합한다.
이 판본은 `explicit-entry-fruit-cohort-rates-research-v1`이다.
원 자동 착과/W1 적분/seed를 추정하거나 Axiany 보정으로 표시하지 않는다.

## 고정 문헌식과 명시 입력

Vanthoor 9.38–9.42/9.45·Table9.1의 값/단위는
[원천 등록부](../research/crop-fruit-source-register.json)에서 가져온다.
원 PDF/권리/hash와 값의 십진 표현을 고정 cohort 프로필에 보존한다.
기존 고정 transport 프로필도 전달받고 같은 nDev/cDev1/cDev2인지 대사한다.
지원 범위는 nDev=50, T24=17–23°C, temperature_sum>0인 piecewise 생식기다.
시간 적분이나 전체 작기를 수용한 범위가 아니다.

    rDev = cDev1+cDev2*T24
    FGP = 1/(rDev*86400)  # day
    M = -4.93+0.548*FGP  # day
    B = 1/(2.44+0.403*M)  # 1/day
    t_j = (j-0.5)/50*FGP  # day
    GR_j = GMax*B*exp(-B*(t_j-M))*exp(-exp(-B*(t_j-M)))
    w_j = N_j*GR_j

GR 단위는 mg_CH2O/fruit_equivalent/day, w 단위는 mg_CH2O/m2_floor/day다.
GMax는 원 잠재 탄수화물 질량이며 생과 과중/현재 과실 질량이 아니다.
대표 나이는 분포 구획의 평가 위치이며 실제 과실의 정확한 나이/숙기가 아니다.
`calculate_demand_rates`는 같은 상태/프로필로 GR/대표 나이/가중 수요만 반환한다.

상태는 닫힌 input_id/origin/values다. values에는 정확히 50개씩의
fruit_number·fruit_carbohydrate·fruit_relative_growth_rate와
temperature_filtered_24h·temperature_sum이 있다. 단위는 기존 N/C/온도 단위와
RGR의 1/s다. 모든 값은 유한·비음수이며 C>0,N=0은 hold다.
ID 1–256문자/연구 origin enum은 증거 표시일 뿐 G0 승인이 아니다.

유입은 같은 닫힌 block의 fruit_carbohydrate_inflow F,
fruit_number_inflow S, fruit_entry_carbohydrate W1 세 quantity다.
F/S/W1의 단위와 budget/empty-sink/entry hold는 기존 배분 계약 그대로다.
실제 전체 생장 결합은 해당 기관 유입 코드에서 계산한 F를 전달해야 한다.
합성 검사는 명시한 수식 입력을 사용하고 이를 실제 forcing/착과로 표시하지 않는다.

RGR은 구획별 명시 입력이다. 현재 GreenLight의 고정 3e−6이나 Greenhouses의
`GR/GMax/86400`을 자동 적용하지 않는다. 이 두 값은 실측 RGR이나 원 저자의
추가 정의가 아니다. 초기 C=0의 log 비율/음의 RGR·추정 정책은 별도 판본이다.
본 양의 유지 호흡 범위에서 음수/표현 불가능한 RGR 입력은 hold다.

## 호흡과 순간 수지

구획 유지 호흡은 원 9.45의 단위/온도 범위로 한 번 계산한다.

    maintenance_j = cFruitM*C_j*(1-exp(-cRgr*RGR_j))*Q10**((T24-25)/10)
    dC_j = transport_dC_j+A_j-maintenance_j
    dN_j = transport_dN_j+[S,0,...,0]_j
    fruit_growth_respiration = cFruitG*F
    fruit_buffer_debit = F+fruit_growth_respiration

기존 total fruit는 sum(C_j)에서 한 번 파생한다. 후속 전체 생장 호출에서는
기존 fruit 유지 호흡/미분을 위 구획 값으로 교체하고 기존 buffer의 성장 호흡을
한 번만 사용한다. 위 debit을 기존 F+성장 호흡에 다시 더하지 않는다.

    sum(dC)+terminal_C+sum(maintenance)-F = 0
    sum(dN)+terminal_N-S = 0
    sum(dC)+terminal_C+sum(maintenance)+growth_respiration-buffer_debit = 0

각 합계는 50구획의 명시적 ULP 예산으로 대사하며 예산 밖/비유한·양의 유량
underflow/overflow는 hold다. 입력/계수·배분을 clip하거나 수지 잔차를 재배분하지 않는다.
수치 예산은 number=104×ulp(최대 개수 유입/이동/절대 미분), carbon=308×ulp(최대
탄소 유입/debit·성장/유지 호흡·배분/이동/절대 미분)이다. 50구획의 곱셈/차감·
3항 미분/합계와 외부 경계의 반올림 예산이며 농장 예측 정확도의 기준이 아니다.
최종 유출은 연구 terminal quantity이며 실제 수확·생과·판매량이 아니다.

## 작은 구현·수용과 후속

첫 묶음: `backend/app/crop_fruit_cohorts.py`, `backend/tests/test_crop_fruit_cohorts.py`,
`fixtures/crop-fruit-cohort-reference-parameters-v1.json`,
`fixtures/crop-fruit-cohort-reference-cases-v1.json`와 독립 Decimal 생성 코드다.
모델/프로필/정책/transport/원 input hash를 실제 결과에 연결한다.
17/20/23°C·0/다중/균일 구획·0/명시 RGR을 독립 참조로 대사한다.
고정 계수/입력 불변, 원 단위·호흡 0/양수/한 번 차감, 세 수지와 영역/양/배열/
empty-sink·budget·비유한/underflow/overflow를 시험하고 실제 명령/출력을 남긴다.

이어 `crop-fruit-cohort-integration`에서 구획 N/C와 buffer/기관의 시간 적분·
관리 사건·수렴/동일 재현·누적 terminal/호흡·개수/탄소 보존을 검증한다.
현재 명시적 배분은 첫 구획의 기존 수요를 추가로 받지 않으며 새 작기의
빈 tail·양의 남은 유입은 hold다. 이는 전체 작기 착수/초기 발달을 지원했다고
주장하지 않기 위한 실제 모델 한계다. 초기/자동 정책은 근거를 보완한 별도 판본으로
해소해야 최종 전체 작기 생산 모델에 접근할 수 있다.
저장/3D는 그 새 시계열/결과 판본을 받은 뒤 연결한다.
실제 품종/생과 변환과 [G0–G4](../docs/PROJECT_SPEC.md#6-검증과-수용-관문)는 유지한다.
