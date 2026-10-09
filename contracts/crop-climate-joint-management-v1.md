# 작물·기후의 원자적 관리 사건 v1

선행: [공동 RHS](crop-climate-joint-rhs-v1.md),
[짧은 공동 적분](crop-climate-joint-short-integration-v1.md),
[수관 용량 제거](crop-canopy-energy-transport-v1.md)의 로컬 수용.
핵심5: `backend/app/crop_climate_joint_management.py`, 해당 tests,
이 계약, `research/crop-climate-joint-management-reference.py`,
`fixtures/crop-climate-joint-management-reference-cases-v1.json`.

## 원자 적용과 경계

`apply_management(scenario=..., event=..., growth_profile=..., cohort_profile=...,
transport_profile=..., exchange_profile=...)`는 같은 순간의108상태를 새 후보로 변환한다.
scenario/프로필과 온도·작물 domain은 기존 공동 RHS 계약을 따른다.
event는 정확히 `input_id`, `origin=synthetic|reference_calculation`, `values`다.
ID는 비어 있지 않은1–200자 문자열, values는 leaf/stem_root 두 명시 제거량과
50개 `fruit_fraction`뿐이다. 각 값은 닫힌 `{value,unit}`다.
leaf/stem_root는 mg_CH2O/m2_floor의0이상, fraction은 unit1의0–1이다.
bool/문자열·비유한·누락/여분·다른 단위/배열·권리 채택을 거부한다.

과실은 기존 [구획 사건](crop-plant-cohort-integration-v1.md)의 명시 연구 규칙처럼
각 구획의 C와 N에 같은 fraction을 적용한다. 새 수확량/숙기·등급을 추정하지 않는다.
leaf/stem_root 초과 제거는 hold, 전량 적엽은 기존 빈 수관 hold다.
과실 전량/줄기0 후보도 공동 RHS의 현재 domain을 통과해야 한다.
기존 상태/프로필/입력·결과·서버와 DB/API/UI는 보존한다.

1. 사건 전 공동 RHS로 원 상태를 확인한다.
2. 복사한 후보에서 leaf/stem_root와50 C/N을 함께 제거한다.
3. 공개 수관 용량 제거 함수로 leaf/LAI/C와 signed Uref를 함께 갱신한다.
4. 사건 후 공동 RHS·온도 보존·탄소/개수/열/용량 수지를 확인한다.
5. 모두 통과한 경우만 새 상태·제거 장부를 반환한다. 실패는 원 입력을 변경하지 않고
   phase와 마지막 확인된 사건 전 상태/유도량을 남긴다. 부분 성공은 없다.

양의 제거량/분율 곱이 underflow하거나 실제 상태 감소가 반올림으로 사라지면 hold한다.
과실은 정규화 숫자의 decimal 문자열을 정확한 유리수로 계산한 제거량/잔량을 각각 binary64로 반올림한다.
서로 같은 명시 잔량이 곱/뺄셈 경로의 오차로 갈라지는 것을 방지한다.
잎/줄기 제거량은 명시 binary64 수량이며 잎/용량 계산은 기존 공개 함수의 동일 연산을 따른다.
`cohort-decimal-rational-removal-v1`을 identity에 결속한다.
이는 순간 수량 연산이며 온도 이력은 기존 동적 RK4다. Fraction 온도 clock을 도입하지 않는다.
수관 열 유출의 부호를 유지한다. 공기 온도/수증기·buffer/T24/Tsum은 순간 사건에서 변하지 않는다.
stem/fruit의 열 상태는 이 모델에 없으므로 그 제거 열을0으로 계산했다고 주장하지 않는다.
수관 용량 경계와 해당 작물 탄수화물/개수만 대사한다.

## 수지·identity·시간

```text
C_before-C_after = removed_leaf+removed_stem+sum(removed_fruit_C)
N_before-N_after = sum(removed_fruit_N)
U_before-U_after = removed_canopy_sensible_energy   (signed)
Ccan_before-Ccan_after = capLeaf*sla*removed_leaf
Tc_after = Tc_before
```

각 재고 잔차는 `64*ulp(max(abs(before_stock),abs(after_stock),sum(abs(balance_terms))))`,
온도 보존은 기존2e-13 K를 사용한다. 이는 binary64 합성 회계 기준이다.
모델/코드·의존 RHS/용량 코드,4개 프로필/정책, 사건/사건 전후 입력·계산 SHA를 결속한다.
출력 scope는 `software_research_only`, `synthetic_joint_crop_climate_management_only`,
G0_G4는 `not_assessed`다. 물성·품종/농장 입력을 채택하지 않는다.

이 primitive는 시간 진행/사건 중복 처리/영속 게시를 맡지 않는다.
작은 구성 검증은 같은 초 경계에서 이전 구간 적분→원자 사건→사건 후 출력→다음 구간 적분 순서다.
처음/마지막 시각에도 사건 후 출력이며 사건 journal에는 전/후가 둘 다 있어야 한다.
분할 구간의 연속22장부와 사건 제거 장부를 따로 합산해 초기–최종의7수지를 대사한다.
새 연속 실행기는 이 규칙을 소유하며 checkpoint/UTC·forcing 변경·중복 없는 사건/출력을 별도 수용한다.
기존121상태/Fraction clock의 자동 재사용이나 불변 원 결과의 갱신은 없다.

## 사전 수용

1. app import 없는 Decimal80의 독립 제거 전후값: 상태108·기관/구획 제거량·signed 열/용량·유도 Tc/LAI.
   0/부분/줄기·과실/혼합·음/0 Uref·과실 전량을 포함한다.
   상대5e-12/절대5e-14, 온도 절대2e-13 K와 사건 수지의
   탄소1e-7 mg/m²·개수1e-12 N/m²·열1e-8 J/m²·용량1e-8 J/m²/K를 확인한다.
2. 32초의 낮/밤·역 교환에서16초 사건을 포함한 같은 dt2 궤적/장부를 독립 참조와 대사한다.
   처음/마지막 사건도 확인한다. 상태/장부 상대5e-12/절대5e-14,
   온도/온도 이력 절대2e-10 K, 전역7수지는 짧은 적분의 사전 절대 기준을 유지한다.
3. 낮/밤·역 교환의 dt8/4/2, 같은16초 사건을 독립 dt0.25 해와 비교한다.
   Tc/Tair/m_v/T24/Tsum·buffer/과실 C합·H/LE/E의 각 반분 오차는8배 넘게 줄어야 한다.
   빈 과실 첫 진입의 기존 시간 수렴/착과 불확실성은 유지한다.
4. 사건 후 LAI/Tc 피드백·공기/clock 불변, Tref 변환·0 사건 항등, 폐쇄 입력/원량/입력 불변,
   초기/후 domain·초과/전량/수치 실패와 마지막 확인 상태를 시험한다.
5. 원 source/미리보기·원본2,148항목, 실제 종료·FD/정확한 소유 정리·단일512MiB/소유+보호1GiB와 비용을 기록한다.

이번 수용은 순수 사건과 작은 수동 구성까지다. 관리가 포함된 자동 연속 실행/재개·온실 경계·새 저장/3D와
물/구매 에너지·경제/실시간 U3·실제 자료/관문 수용은 후속이다.
