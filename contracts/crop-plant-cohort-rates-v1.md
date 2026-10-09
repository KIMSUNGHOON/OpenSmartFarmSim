# 전체 기관과 명시적 과실 구획의 순간 결합 — v1

상태: **순간 결합의 로컬 소프트웨어 수용; 시간 적분 수용 전**.
상위 `crop-fruit-cohort-integration`의 첫 작은 단계다. 시간 적분/관리 사건은 뒤에 검증한다.

## 판본과 근거

`vanthoor-greenlight-explicit-entry-plant-rates-research-v1`은
[기존 carbon kernel](crop-growth-research-v1.md)의 광 동화·smooth buffer/기관 유입·
잎/줄기 fixed-RGR 호흡과 [명시적 과실 구획](crop-fruit-cohorts-v2.md)의
Gompertz 수요·개수/탄소 이동·배분·구획 유지 호흡을 결합한 **별도 연구 모델**이다.
원 Vanthoor 전체 자동 착과 모델이나 Axiany 보정 모델로 표시하지 않는다.

고정 기존 growth/cohort/transport profile만 허용하고 다음 대응을 대사한다.
`cFruitG=fruit_growth_respiration`, `cFruitM=fruit_maintenance`, `cRgr=cRgr`,
`q10m=Q10`, 온도 기준/간격과 하루 seconds는 같다.
원식/권리·각 profile hash와 실제 CLI 근거는 원천/구획 수용 기록을 따른다.
잎/줄기의 고정 RGR은 기존 출처의 연구 가정이며 실제 품종 측정으로 취급하지 않는다.

## 입력과 공개 함수

`calculate_plant_cohort_rates(*, state, cohort_state, forcing, removals, fruit_entry,
growth_profile, cohort_profile, transport_profile)`.

각 block은 닫힌 `input_id/origin/values`다. ID는 1–256문자, origin은 기존 연구 enum이다.

- `state`: buffer/leaf/stem_root의 CH2O 저장량, temperature_filtered_24h/temperature_sum.
  별도의 fruit 총량 입력을 받지 않는다.
- `cohort_state`: v2의 정확한 50개 N/C/RGR와 동일한 두 온도 상태. 두 block의
  온도 상태가 다르면 hold한다. 총 과실 CH2O는 `fsum(C_j)`에서 한 번 파생한다.
- `forcing`: 기존 수관 온도/PAR/CO₂ 단위·영역.
- `removals`: leaf/stem_root의 명시적 연속 CH2O 제거 유량만. 이 판본은 과실의
  임의 연속 제거를 받지 않으며 발달 마지막 유출을 구획 kernel에서 계산한다.
  후속 개별 구획 관리 사건은 동일 N/C 제거를 별도로 계약/적분해야 한다.
- `fruit_entry`: 명시적인 S/W1 두 quantity. F는 받지 않고 기존 기관 유입의
  계산 결과만 cohort kernel에 전달한다. 자동 S/W1/RGR·seed는 제공하지 않는다.

순수 함수는 기존 공개 계산 함수를 호출한다. 기존 단일 fruit 유지 호흡/미분은
구획 결과로 교체한다. 기존 buffer 미분에 F+성장 호흡을 다시 차감하지 않는다.
기존 kernel이 반환하는 단일 fruit 진단을 실제 결합 결과로 노출/합산하지 않는다.

## 미분과 보존

    dBuffer = photosynthesis-sum(organ_allocation)-growth_respiration
    dLeaf = F_leaf-maintenance_leaf-removal_leaf
    dStem = F_stem-maintenance_stem-removal_stem
    dC_j / dN_j = cohort kernel(F_from_organ_allocation,S,W1,RGR_j)
    fruit_total = sum(C_j)  # derived; not an independently integrated state
    maintenance_fruit = sum(cohort_maintenance_j)

성장 호흡은 기존 kernel의 기관별 계수를 한 번 사용한다. 과실 부분은 .27F로
cohort 결과와 대사하며 새 debit을 추가하지 않는다.

    dBuffer+dLeaf+dStem+sum(dC_j)+growth_respiration
      +maintenance_leaf+maintenance_stem+sum(maintenance_j)
      +removal_leaf+removal_stem+terminal_C-photosynthesis = 0
    sum(dN_j)+terminal_N-S = 0

탄소 budget은 기존 plant budget+cohort budget+32×ulp(전체 유량 최대 절대값과 1의 최대)다.
개수 budget은 cohort의 동일 예산이다. clipping/임의 잔차 재배분은 없다.
비유한 합계/파생 mass·호환 불일치/온도 불일치·source 영역/배분·수지 실패는 hold다.

결과는 기관과 50개 N/C 미분·LAI/유량·총 과실 CH2O/유지 호흡·terminal·수지,
모든 고정 profile/model/policy·정규화 입력 hash와 `software_research_only`를 반환한다.
입력 불변/같은 계산 재현이 필요하다. 생과 kg/수확/판매/예측·관문 승인은 반환하지 않는다.

## 이 단계의 수용과 다음 단계

독립 60자리 Decimal 기관 원식과 별도 구획 참조로 day/night·17/20/23°C·
0/명시 varying RGR·기관 제거의 수치/두 수지를 대사한다. 입력/온도/프로필/유한성·
빈 tail/entry hold·중복 성장 차감과 기존 fruit 호흡의 잘못된 채택을 시험한다.
이 수용 뒤 시간 입력/초기조건·bounded RK4·누적 호흡/terminal·N/C 사건/수렴/
불변 manifest의 별도 작은 계약을 검증한다. 저장 v1이나 기존 3D의 결과를 덮어쓰지 않는다.

빈 초기 tail/자동 착과·W1/RGR/생식기 이전 정책, 실제 품종/forcing QC·작기 처리 한도와
국내 독립 자료/G0–G4는 유지한다. 순간 결합을 전체 작기 또는 실제 생산으로 표시하지 않는다.
