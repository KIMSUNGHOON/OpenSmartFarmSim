# 과실 탄수화물 배분 연구 정책 — v1

상태: **명시적 착과·진입 질량의 개발 정책; 제품 구현/실제 품종 수용 전**.
원식과 차이·권리/수치 근거는 [판단 보고서](../research/crop-fruit-allocation-policy.md)에
기록한다. 정책 ID는 `explicit-entry-fruit-allocation-research-v1`이다.
원 Vanthoor 전체 착과 모델이나 Axiany 보정 모델로 이름을 붙이지 않는다.

## 첫 개발 범위

50구획의 원 순간 이동과 함께 사용할 **순간 탄소/개수 유입**을 정의한다.
착과 수율 S와 신규 과실 한 개의 진입 탄수화물 W1은 출처/단위를 가진 명시적
입력이다. 자동 9.29 착과·W1 Gompertz 적분 경계/seed 추정은 이 판본에 없다.
초기 N/C는 사용자가 제공한 연구 입력이며 임의 N1>0이나 전체 기관량 50등분은 없다.
생식기의 piecewise h=1 및 현재 공동 연구 영역 17–23°C 안에서 후속 결합한다.
온도 조건만으로 실제 개화/관리·품종이나 G0 적용성을 승인하지 않는다.

이 모듈 경계의 필수량:

| 양 | 의미와 단위 | 개발 입력/계산 |
| --- | --- | --- |
| F | 기관으로 보유되는 전체 과실 탄소 유입, mg_CH2O/m2_floor/s | 기존 기관 유입 계산의 명시적 값; 성장 호흡 전 buffer 차감과 구분 |
| S | 첫 구획에 들어오는 연속 과실 수, fruits_equivalent/m2_floor/s | 명시적 연구 관리/계산 입력, 자동 착과 아님 |
| W1 | 새 과실 1개의 진입 탄수화물, mg_CH2O/fruit_equivalent | 명시적 입력, 문헌식의 불명확한 적분 경계를 대신 추정하지 않음 |
| w_j | 구획별 잠재 탄소 수요, mg_CH2O/m2_floor/day | N_j × GR_j; 합성 검사에서는 명시적 합성 수요, 전체 모델에서는 고정 Gompertz 코드의 출력과 hash |

모든 양은 유한·비음수, 정확한 단위와 origin/input ID가 필요하다. 길이 50을 고정한다.
S>0이면 W1>0이 필요하다. 실제 품종/관측이라고 입력에 표시해도 G0 증거가 되지 않는다.
수요 배열은 코드가 만들거나 검증한 양이어야 하며 생성 문장으로 채우지 않는다.

## 명시적 보존 변형

원 9.35의 A1=W1×S와 뒤 구획의 상대 수요를 유지한다. 원 9.37의 분모는
첫 구획을 제외하는 D2로 **명시적으로 변경**한다. 저자 승인 정정은 아니다.

    A1 = W1*S
    R = F-A1
    D2 = sum(w_j, j=2..50)
    A_j = R*w_j/D2, j=2..50, if R>0 and D2>0
    number_inflow = [S,0,...,0]

R=0이면 뒤 구획의 A_j는 0이고 D2=0도 허용한다. F=0,S=0은 모든 유입 0이다.
R>0,D2=0은 `EMPTY_FRUIT_SINK_HOLD`; A1>F는 `FRUIT_ENTRY_BUDGET_HOLD`다.
S>0,W1=0은 `FRUIT_ENTRY_STATE_HOLD`다. 빈 sink에서 탄소를 첫 구획에 추가하거나
buffer로 돌려보내고, S/질량을 clip하거나 분모에 epsilon을 넣지 않는다.
성장/유지 호흡·초기 배열·열매 손실을 자동 생성하지 않는다.

허용된 경우 sum(A_j)=A1+R=F이고 sum(number_inflow)=S다.
50구획 중 첫 구획의 기존 w1은 D2에 사용하지 않는다. 새 착과 질량은 S×W1이며
기존 첫 구획의 생장 수요를 추가로 보장하는 정책은 아니다. 이는 이 변형의
구조적 제약으로 명시한다. 해당 생리 정확도는 독립 자료로 별도 검증해야 한다.

## 제품 코드와 후속 수용

다음은 `crop-fruit-allocation-rates`의 작은 순수 구현이다.
`backend/app/crop_fruit_allocation.py`, `backend/tests/test_crop_fruit_allocation.py`로
닫힌 입력·단위/길이/유한성·hash/불변·위 hold와 순간 유입을 구현한다.
생물 계수/기본 W1/S는 추가하지 않는다. 정책 식/판본은 코드와 manifest에 고정한다.

독립 [Decimal 증거](../research/artifacts/crop-fruit-allocation-policy-reference-20261005.json)의
정상·원식/epsilon 보존 반례·hold를 제품 함수와 대사한다. 수지 허용치는
50항 반올림의 명시적 ULP 예산이며 예산 밖·양의 유입 underflow/비유한은 hold다.
정규화 잔차를 특정 구획에 몰아넣지 않는다. 입력 origin을 실제 승인으로 취급하지 않는다.

뒤 `crop-fruit-cohorts`는 고정 Gompertz GR 계산과 위 배분·이동·유지 호흡을
개수/탄소 적분에 연결한다. 기존 총 fruit=sum(C_j)는 한 번만 파생하고
buffer의 F/성장 호흡과 구획 유지 호흡을 각각 한 번만 차감한다.
명시적 관리 사건은 N/C를 함께 바꾸고 누적 보존·사건 순서/동일 재현을 확인한다.
실제 한 작기와 생과/경제/추천의 수용은 기존 해당 입력과 G0–G4가 필요하다.

자동 착과 정책이 필요하면 W1/seed/빈 sink와 원/평활 gate를 추가 근거와
독립 초기/과실 자료로 결정한 **별도 판본**을 만든다. 본 입력형 계산 통과가
자동 착과·품종 생산 예측의 수용을 대신하지 않는다.
