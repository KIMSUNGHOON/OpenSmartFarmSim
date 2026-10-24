# 명시 LAI의 기관·50과실 탄소 RHS — 연구 v1

상태: [고유324검사·fresh46사례 수용](../research/crop-explicit-lai-carbon-20261024.md). [연속 경계](crop-geometry-carbon-coupling-research-v1.md)의 두 번째 순간 부품이다.
[광 동화](crop-explicit-lai-photosynthesis-v1.md), [빈 sink 유보](crop-plant-startup-rates-v1.md)와
[50구획](crop-fruit-cohorts-v2.md)의 고정 식·프로필/정책을 따른다. 새 hybrid의 생물학/연속 궤적 승인이 아니다.

`calculate_plant_rates(*, state, cohort_state, forcing, removals, fruit_entry, geometry,
growth_profile, cohort_profile, transport_profile)`는 기존 plant-startup의 다섯 block과
닫힌 `{input_id,origin=synthetic,values:{leaf_area_index:{value,unit=m2_leaf/m2_floor}}}`를 받는다.
모든 block의 origin은 synthetic, ID는1–200 ASCII다. 상태/forcing의 단위·finite/nonnegative 검사,
T24=17–23°C/Tsum>0·두 상태의 같은 온도·정확50 N/C/RGR와 C>0⇒N>0를 유지한다.
입력/출력은 각각128KiB 이하이며 정확 세 고정 profile 타입/바이트와 공통 계수 일치를 요구한다.
양의 면적에0 leaf C인 관계는 이 연구 부품의 미지원 state hold이며 C를 생성하지 않는다.

호출 순서는 닫힌 입력/공통 상태→명시 광 동화1회→고정 비광학 분배/잎·줄기 유지 호흡→
명시 빈 sink 유보→유효 유입만 받는50과실→실제 생장 호흡·buffer/기관 미분·전체 C/N 대사다.
기존 전체 SLA carbon/startup RHS를 호출한 후 P를 덮어쓰거나 임시 leaf 질량/forcing을 만들지 않는다.
기존 파일/모델/프로필과 저장 결과를 바꾸지 않는다. 기존 비광학 식을 새 조립에 명시적으로 재사용하며 source/code SHA를 기록한다.

원 buffer/Tc/T24/Tsum의 분배식·잎/줄기 fixed RGR은 유지한다. requested fruit F는 startup policy로
effective/deferred에 나누고, buffer에 기존 `(1+cFruitG)×deferred`를 반영하며 fruit 성장 호흡은 effective에만 붙인다.
과실 총 C는50개에서 한 번 파생하고 유지 호흡/terminal C/N은 과실 kernel 값만 사용한다.
양수 총량/수치/정책/배분 불일치·0 저장량의 음의 최종 미분은 hold다. 부분 결과나 재고 전진은 없다.

전체 C 잔차는 dBuffer+dLeaf+dStemRoot+ΣdFruitC+실제 성장 호흡+잎/줄기/과실 유지 호흡+
명시 leaf/stem 제거+terminalFruitC−P다. N 잔차는 ΣdFruitN+terminalFruitN−명시S다.
과실/startup 기존 roundoff budget에 실제 전체 항 규모의64ulp를 더해 C를 대사한다. 생리 오차 허용치는 아니다.
같은 LAI=SLA×leaf에서 기존 RHS의 수치/유보·배분과 대사하며 기존 결과 bytes를 갱신하지 않는다.

출력은 명시 입력/모델·code/component/profile/정책·raw/정규 input SHA, 원 광 동화 결과,
LAI·기관/T24/Tsum 미분, 요청/유효/유보·실제 성장/유지 호흡·전체 과실C·50 C/N 미분/terminal과 수지다.
software_research_only/synthetic_explicit_lai_carbon_cohort_math_only/G0_G4=not_assessed를 고정한다.
추적 LAI의 전체 수관 권위·시간 적분·열/물·새 기관 질량·생과/등급/경제·추천을 만들지 않는다.

수용은 기존22 startup 사례의 같은 LAI 대사, app import 없는 독립 Decimal의 다른 명시 LAI와
기존 SLA 영역 밖/새 기하 영역 안 및 그 반대 사례·C/N/유보/단위/온도·고갈/잘못된 입력 거부다.
광 동화/그 helper 각1회·startup/50과실 각1회·기존 전체 carbon/startup/적분·DB/CLI/network/쓰기0,
같은 입력의 동일 결과·입력 불변/기존 result/profiles·WSL 보존을 확인한다.
후속 면적 기반 capacity/material energy와 짧은 구간/정확 사건/분할·재개, 출현/공급·관리 C와
실제 독립 국내/미래·작물 비교 및 G0–G4의 수용은 별도다.
