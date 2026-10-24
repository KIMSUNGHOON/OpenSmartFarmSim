# 기존 잎의 동적 기온·면적과 공동 짧은 계산 — 연구 v1

상태: **사건 없는 짧은 연속 구간 수용**. [236검사·독립1,542수치/간격 축소](../research/crop-growing-geometry-climate-20261024.md).
[연속 결합5](crop-geometry-carbon-coupling-research-v1.md)의 사건 없는 첫 구간이다.
[같은 stage 공동 RHS](crop-explicit-lai-climate-rhs-v1.md)와 기존 자체 logistic 면적/율을 재사용한다.
[원문 대조](../research/dynamic-air-growing-geometry-primary-sources-20261024.md)는 원 일별 기온과 새 연속 가정을 구분한다.
기존 정확 Fraction 시계/잎 상태/모델/결과는 바꾸지 않는다. 실제 품종·물질/열/공급 검증이나 생산 승인은 아니다.

## 필수 선언과 새 상태

`evaluate_rhs(program=..., **profiles)`와 `integrate(program=...,step_seconds=...,step_count=...,**profiles)`를 제공한다.
program의 정확한 필드는 input_id, origin=synthetic, normalization, thermal_age_policy, capacity_policy,
model_floor_area, capacity_outflow, scenario, leaves다. ID는 기존 ASCII1–200이다.
normalization=zero_lower_asymptote_sigmoid_v1,
thermal_age_policy=dynamic_indoor_air_no_clip_v1,
capacity_policy=declared_outflow_plus_area_capacity_derivative_v1를 **반드시** 명시한다. 다른/누락 정책은 hold다.
이름 있는 마지막 정책은 이번 새 프로젝트 회계 가정이다. 기존 독립 gross 흐름을 받는 RHS의 기본값으로 추가하지 않는다.

scenario는 기존 공동 RHS의 input_id/origin과8개 수량 블록이며 geometry/capacity_transport를 받지 않는다.
scenario.input_id/origin은 program과 같고 Tin/Tout는 forcing에 모두 명시한다. 원 profile4종/기타 단위/배열50개를 유지한다.
floor는 양수 m2_floor, 독립 선언 gout는0 이상 J/m2_floor/K/s이며0도 명시한다.
leaves는 고정 순서의1–512개 {leaf_id,thermal_age,base_temperature,initial_area,curve}다.
ID는 고유 ASCII, age는0 이상 degC_day의 binary64 수량, Tbase는 명시 degC, initial_area는 양수 m2,
curve는 기존 {profile_id,origin=synthetic,values={maximum_area,steepness,inflection_age}}다.
원 exact-age/UTC/출현 checkpoint를 이 입력으로 자동 변환하지 않는다. 실제 농장/전체 수관 대표성은 승인하지 않는다.
모든 수량은 닫힌 {value,unit}, bool/비유한/누락/여분/다른 단위를 거부한다. 입력/결과는2MiB 이하다.

요청 초기 면적은 canonical F(age)와 상대1e-12/절대0 이내여야 한다. 실제 초기 A는 기존 정책처럼
binary64 canonical F로1회 정규화하고 요청/정규화 면적을 기록한다. 이후 A를 F로 resnap하지 않는다.
새 ODE 상태는 기관5/과실C/N100/기후3에 잎별 a와 A를 더한다. a는 근사 연속 열적 나이이며 기존 exact 상태가 아니다.

```text
a_i' = (Ta-Tbase_i)/86400                     # 현재 동적 실내 공기 온도
A_i' = logistic_derivative(a_i)*a_i'
LAI = sum(A_i)/floor; Ldot = sum(A_i')/floor
C = k*LAI; Cdot = k*Ldot
gout = independently declared gross capacity outflow
gin = gout+Cdot                              # 반드시 선택한 새 회계 정책 안에서만
```

Ta<Tbase는 hold이며0 절단·수관 Tc/외기/결측 대체가 없다. 모든 stage에서 age>=0, 0<A<=M를 유지한다.
gin/gout/Tin/Tout는 실제 잎 질량/물성/엔탈피의 추론이 아니다. k는 기존 명시 고정 면적당 용량 가정이다.
새 gross 매개변수화는 추가 자유도 gout와 각 온도를 독립 명시해 미정계를 닫는 프로젝트 연구 정책이다.
큰 gout 때문에 gin−gout가 Cdot를 표현하지 못하면 기존 순량8ulp 검사를 그대로 적용해 hold한다.
새 정책을 선택하지 않은 기존 함수/자료/실행에는 이 매개변수화를 적용하지 않는다.

A와 a를 함께 적분해 C가 적분된 A의 선형 재고가 되게 한다. F(a)와의 차이를 단순 roundoff로 숨기지 않는다.
연속식의 불변량 D=A−F(a)의 초기값/현재값/차이를 기록하고 독립 해/간격 축소로 수치 절단 오차를 검증한다.
canonical 재맞춤으로 차이를 지우거나 저장 열을 고치지 않는다. 초기 허용 오차/수치 정규화도 관측 보정이 아니다.

## 공동 적분·수지·수용

같은 stage에서 원 joint RHS를1회 호출한다. 현재 Ta→a'/A'→LAI/Ldot/선택된 gross 정책→joint 순서다.
fixed RK4는 모든 상태와 원 유량을 같은 가중치로 적분하고 확정 endpoint를 다음 k1으로 재사용한다.
4*step_count+1회 평가, dt>0/정수 count1–4096·총600초 이하, sample의 상태/진단 scalar 총32,768개 이하다.
sample은 상태 벡터와 한 번 제공하는 단위/잎ID layout·elapsed seconds다. UTC/관리/새 출현·저장/API는 발급하지 않는다.
비영 increment 소실/비유한·trial domain/원 장부 실패는 마지막 확정 sample과 step/stage를 담은 hold이며 부분 성공이 아니다.

누적 장부는 광 동화/생장·기관별 유지 호흡/제거/과실 terminal C/N·진입N,
H/LE/Qin/Qout·외부 수관/공기열·E/외부 증기·gin/gout와 실내 Ta 시간 적분을 보존한다.
기관/과실 C/N·signed Uref·공기 현열·증기·C 및 reduced-energy를 초기/최종 재고와 대사한다.
각 age 변화는 (적분Ta−Tbase*duration)/86400과 대사한다.
기존 짧은 적분과 같은 64*(steps+1)*ulp(max(abs(initial),abs(final),sum(abs(terms)))) roundoff 예산이며 바닥1은 없다.
이는 F(a) companion 오차/적분 절단 오차/생물학적 오차의 허용치가 아니다.

app 없는 독립 Decimal100 이상의 원식/전체 벡터 RK4와 같은 간격 상태/장부를 상대5e-12,
온도 절대2e-10 K·구조적0 정확0으로 대사한다. 합/차의 상쇄에는 원 항64ulp를 별도 명시한다.
양/역 교환·성장 면적·서로 다른 기준/유입/유출 온도·명시0/양의 gout·기준 동일/미만·빈/양의 과실을 검증한다.
대표32초 구간 dt8/4/2와 독립 dt0.25 이하를 비교해 비불변량의 반분 오차8배 초과 감소를 확인한다.
나이/A·D−D0가 roundoff 바닥이면 비율을 꾸미지 않고 독립 오차와 그대로 기록한다.
간격 반분의 비교에서 finer 오차가 해당 독립 최종량의128ulp 이하면 roundoff 바닥으로 기록하고 비율을 주장하지 않는다.
companion 진단의 구현−독립 참조 차이는 64*(steps+1)*ulp(max(abs(initial_area),abs(final_area),abs(canonical_area)))로
대사한다. D−D0 자체의 절단 오차를 이 반올림 예산으로 대체하거나0으로 강제하지 않는다.
source/입력 불변·각 stage 값/호출·실패 직전 상태·참조 재생/fresh의 옛 joint/옛 advance/DB/CLI/network/쓰기0,
원 자료/4root·WSL을 유지한다. 통과한 사례 범위만 수용하며 실제 품종/기후·작기/경제·추천/G0–G4는 not_assessed다.
