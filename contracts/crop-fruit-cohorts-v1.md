# 과실 구획 연구 계약 — v1

상태: **조사/개발 경계와 고립된 순간 이동의 로컬 소프트웨어 수용**.
[92개 새 시험·기존 포함 238개·독립 참조 3,090수치](../research/crop-fruit-transport-implementation.md)를 확인했다.
전체 배분/착과·적분/생과 생산량의 구현/수용은 후속이다.
[원식과 보류](../research/crop-fruit-cohorts-baseline.md),
[계수/권리 등록부](../research/crop-fruit-source-register.json)를 따른다.
모델/설계 판단은 동일 `gpt-6.1-sol / xhigh` CLI에서 수행했다. 이 계약은
기존 [G0–G4](../docs/PROJECT_SPEC.md#6-검증과-수용-관문)를 변경하지 않는다.

## 상태·단위와 분리

50구획 `N_j`는 `fruits_equivalent/m2_floor`, `C_j`는
`mg_CH2O/m2_floor`다. 연속적인 상태이며 실제 개별 과실의 정수 개수가 아니다.
미계산 키·숙기·열매 모양/색·생과 kg를 만들거나 기존 3D에 배치하지 않는다.
실제 원천의 모집단/면적 변환과 모든 초기 구획 값은 별도 원천/QC가 필요하다.

후속 결합 시 기존 kernel의 `fruit`는 `sum(C_j)`에서 한 번만 파생한다.
총 과실 저장소를 별도로 적분해 구획 질량과 이중 보유하지 않는다. 전체 과실
buffer 유입 F는 `sum(A_j)`와 같아야 하며 성장 호흡은 기존 buffer에서 한 번,
유지 호흡은 구획에서 한 번 차감한다. 기존 총 fruit 유지 호흡을 다시 빼지 않는다.
수확/적과 사건은 해당 구획의 개수·탄소량을 함께 제거하고 누적/기관 수지를 남긴다.

## 다음 작은 구현: crop-fruit-transport

첫 코드는 **생식기의 순간 구획 이동**만 계산한다. 배분/착과/호흡 유입은 없는
고립된 합성 수식 사례이며 전체 작물 모델이 아니다. 원 9.31/9.34가 일치하는
piecewise `h=1`, 온도 합이 원 onset 0을 초과한 범위다. 평활 gate나 생식기
이전의 서로 다른 개수/질량 gate를 첫 계산에 섞지 않는다.

구현 파일: `backend/app/crop_fruit_transport.py`,
`backend/tests/test_crop_fruit_transport.py`,
`fixtures/crop-fruit-transport-reference-parameters-v1.json`,
`fixtures/crop-fruit-transport-reference-cases-v1.json`.
`research/crop-fruit-transport-reference.py`를 추가해 독립 Decimal 기대값의
생성 코드/버전·해시와 byte-identical 재실행을 보존했다.

입력은 origin/input ID가 명시된 상태와 고정 profile bytes다. 정확히 50개씩의
N/C quantity 배열, `temperature_filtered_24h` °C, `temperature_sum` °C day를
받는다. 각 quantity는 정확한 value/unit 객체이며 상태는 input_id/origin/values의
닫힌 객체다. ID는 1–256문자, origin은 synthetic/reference_calculation/reference_observation이다.
이 표시가 실제 관측이나 권리 승인을 입증하지 않는다.
수치 타입/단위·유한/비음수·범위를 검증하며 C_j>0,N_j=0은 일관성
hold다. 초기 상태를 자동 생성하지 않는다. 양수 온도 합의 선언은 생리/자료
G0 승인을 뜻하지 않는다. 계수는 nDev=50, cDev1=−7.64e−9 s⁻¹,
cDev2=1.16e−8 s⁻¹/°C의 고정 일반 참조 판본이다.

T24는 기존 생장 kernel과 공동 연구 범위 17–23°C를 사용한다. 원 회귀의
17–27°C와 구분하고 Axiany 보정 범위로 표시하지 않는다. `r=cDev1+cDev2*T24`,
`lambda=50*r`; `S_j=lambda*N_j`, `K_j=lambda*C_j`다.

    dN_1 = -S_1; dN_j = S_(j-1)-S_j, j>=2
    dC_1 = -K_1; dC_j = K_(j-1)-K_j, j>=2
    terminal_number_outflow = S_50
    terminal_carbohydrate_outflow = K_50

출력은 위 순간 유량/변화율과 합계 개수/탄소 수지 잔차,
model/profile/input SHA-256·고정 `software_research_only` 범위다.
마지막 유출은 `terminal` 연구량이며 실제 수확·생과·판매량으로 이름을 바꾸지 않는다.
원식/계수·profile 불일치, 지원 단계/범위 밖, 잘못된 quantity/배열, 수치 오류는
명시적 hold다. clipping·기본 계수·자동 배열 복구·재정규화는 없다.
새 `vanthoor-fruit-transport-research-v1` 판본을 사용하며 기존 rates/integration/
crop-result-v1 해시·불변 입력/저장 결과를 변경하지 않는다. API·3D 연결은 후속이다.

구현의 N/C 배열 이름은 fruit_number/fruit_carbohydrate다. 미분은 동일한
`lambda*(이전 상태-현재 상태)`로 평가해 큰 edge 유량의 차감 손실을 줄인다.
원식/계수를 변경한 것이 아니다. 수지 예산은 두 상태별로 `2*(50+1)*ulp(max(edge))`
이며 50항의 차감/곱셈 반올림과 합계의 보수적인 예산이다. 양의 edge 또는
0이 아닌 구획 차이가 표현 불가능하게 0으로 떨어지면 NUMERIC_HOLD다.
유량/총량의 비유한·합계 overflow와 예산 밖 수지는 각각 hold로 남긴다.

### 순간 이동 수용 기준

1. 모든 값/식에 원 페이지·단위·원 hash/권리·참조 적용 범위가 있고 고정 profile
   byte hash를 검사한다. 50구획 수와 기존 성장 kernel의 공통 온도 영역을 유지한다.
2. 독립 고정 Decimal 참조는 제품 함수 import 없이 원식으로 만든다. 17/20/23°C와
   전부 0, 첫 구획만 양수, 다중/마지막 구획의 N/C를 포함한다. dN/dC·terminal
   대조는 이진 유량 relative 5e−12/absolute 5e−14의 초기 연구 오차 예산에서
   실제 조건수/ULP를 확인한다. 이는 농장 생산 정확도의 합격선이 아니다.
3. `sum(dN)+terminal_number=0`, `sum(dC)+terminal_carbohydrate=0`의
   telescoping 보존, N/C 스케일 변화·0 상태/마지막 경계, 잘못된 단위/타입/NaN/
   음수·온도/onset 영역 밖·50길이/고지/profile 불일치와 원 입력 불변을 시험한다.
4. 실제 명령/결과·원/코드/profile/case/output hash와 수치 실패/hold를 기록한다.
   시험 통과는 순간 이동에 한정한다. 새 시계열/수확/자원/금액/G1 Run을 만들지 않는다.

## 뒤 단계와 필수 보류

`crop-fruit-allocation-policy`는 인쇄 9.36/9.37의 분모/탄소 보존 불일치,
W1의 적분 경계·D=0/빈 sink·착과/초기 seed·piecewise/평활 gate를 먼저 결정한다.
원식과 수정/가정은 독립 판본/근거로 분리한다. 원/수정식의 대수/독립 수치,
`sum(A_j)=F`와 새 착과·빈/고갈 경계를 통과하기 전 전체 배분을 구현하지 않는다.

`crop-fruit-cohorts`는 위 이동·배분 정책 뒤 새 적분 상태/초기조건/관리 사건으로
전체 생장과 연결한다. 독립 일정 계수의 해석해/시간 간격 수렴, 사건의 개수/질량
보존·마지막 유출 누적·재시작/manifest와 기존 buffer/기관 수지를 대사한다.
관련 모델/프로필/solver/저장·출력 계약은 새 판본이며 기존 결과를 수정하지 않는다.

`crop-harvest-conversion`은 품종/시점별 탄수화물→건물→생과중·등급/제거의
근거와 독립 실측을 받는다. 원 DM 계수 1·잠재 GMax·공개 품질 DMC 표본을
생과 변환/실제 수확의 기본값으로 쓰지 않는다. boxcar의 연속 유출을 특정
날짜의 상업 수확 사건으로 자동 바꾸지 않는다.

실제 Axiany 적용에는 [UTC/면적·수관/초기상태/관리/형식/QC 보류](../research/crop-forcing-audit.md)의
해소와 해당 G0/G1, 전체 작기 처리 수용이 필요하다. 국내 독립 농장 G2와
미래 작기 G3a 전 국내 생산/경제 예측은 보류, 후보 비교 G3b 전 순위는 보류,
G4 전 공개 production은 보류한다. 국내 자료 확보와 위 순수 개발은 병행한다.
