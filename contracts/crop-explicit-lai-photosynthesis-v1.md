# 명시 LAI의 순간 광 동화 — 연구 v1

상태: [254검사·fresh96사례 수용](../research/crop-explicit-lai-photosynthesis-20261024.md). [연속 결합 조사](../research/continuous-leaf-carbon-primary-sources-20261024.md),
[기존 광합성 영역](crop-photosynthesis-domain-v1.md)·[탄소 유량](crop-growth-research-v1.md)을 따른다.
새 연구 부품은 기하 입력의 효과만 분리한다. 원 Vanthoor 전체 모델·품종·동적 hybrid 검증을 뜻하지 않는다.

`crop_explicit_lai_photosynthesis.calculate_photosynthesis(*, inputs, profile)`는 닫힌
`{input_id,origin=synthetic,values}`를 받는다. ID는1–200 ASCII 식별자다. values의 정확한 필드는
buffer(mg_CH2O/m2_floor), leaf_area_index(m2_leaf/m2_floor), canopy_temperature(degC),
par_above_canopy(umol_photons/m2_floor/s), co2(ppm)이며 모두 닫힌 `{value,unit}`다.
bool/문자열/누락·여분/비유한·음수를 거부하고 CO2는 양수, Tc는 고정 profile의10–34°C 범위를 따른다.
원52개 parameter profile 바이트만 허용한다. SLA를 새로 고르거나 leaf mass를 LAI/SLA로 만들지 않는다.

기존 `crop_growth_rates._photosynthesis`의 원식을 그대로 사용하고 해당 파일/프로필 SHA를 남긴다.
다른 기존 함수·모델/프로필을 수정하지 않는다. helper의 Γ/PAR/전자 전달·buffer 억제와 단위가 동일하다.
PAR0이면 Γ를 평가하지 않고 P0이다. PAR>0/LAI0은 Tc가 기존 pivot인 경우만 유한 극한을 허용한다.
양의 LAI에서는0≤Γ≤Ci의 기존 영역을 유지한다. 작은 LAI 하한·낮은 CO2의 LAI 상한을 없애거나
Γ/온도/입력을 clip하지 않는다. 비유한·음의 P/전자 전달은 hold다.

출력은 연구 model/code/component/profile·raw 입력/정규 입력 SHA, 정규 입력 복사본,
명시 LAI·순 광 동화 mg_CH2O/m2_floor/s와 기존 Γ(ppm)/electron transport(umol_electrons/m2_floor/s) 진단이다.
buffer는 억제 함수의 현재 저장량 입력일 뿐 이 함수가 어떤 재고도 전진시키지 않는다.
allocation·호흡/기관 C 미분·분배/수확/열용량/온실 적분·비용/추천은 출력하지 않는다.
scope=software_research_only/claim_scope=synthetic_explicit_lai_photosynthesis_math_only/G0_G4=not_assessed를 고정한다.
입력/출력은 각각128KiB 이하이며 새 artifact/DB/API·worker/3D 게시를 만들지 않는다.

수용은 app import 없는100자리 Decimal 참조의 명시 LAI·Tc/CO2/PAR/buffer 행렬,
기존4유량 사례의 LAI=SLA×leaf 지점 P/진단 일치, 낮/밤·0LAI·양쪽/낮은CO2 상한,
실제 입력의 독립 변경·원 입력/프로필/구형 결과 보존과 잘못된 단위/영역/타입/변조 거부다.
fresh에서 같은 참조·생장/기관 advance/적분/DB/CLI/network/쓰기0·WSL/원 자료를 확인한다.

연속 hybrid의 다음 선행은 명시 면적/floor/모집단과 현재 C의 독립 근거·분배/출현/제거 질량 원장,
광 동화를 같은50구획/기관/buffer RHS에 한 번 넣는 C 수지, 면적 기반 capacity/열 수지와 시간 전진이다.
추적 목록 LAI는 전체 실제 수관의 증거가 아니며 본 함수의 수치 성공으로 그 권위가 생기지 않는다.
