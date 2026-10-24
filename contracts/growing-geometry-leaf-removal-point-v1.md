# 독립 면적의 잎 제거 point — 연구 v1

상태: [71신규/356관련·독립288수량의 순간 소프트웨어 수용](../research/growing-geometry-leaf-removal-point-20261024.md).
[저장3D](../research/growing-geometry-3d-20261024.md) 뒤의 첫 제거 자식이다.
기존 [SLA 일치 제거](crop-leaf-carbon-removal-v1.md)를 호출하지 않는다.
[면적/용량 경계](crop-area-canopy-energy-v1.md)의 표현된 용량 회계를 유한 사건으로 제한한다.
실제 조직/수분/물성이나 열역학 엔탈피·농장 정확도의 검증이 아니다. 새 계수·관문 승인0이다.

`apply_removals(*, context, raw_checkpoint, expected_sha256, inputs)`는 원
[continuation](crop-growing-geometry-continuation-v1.md)의 context와 신뢰한 원 checkpoint bytes/SHA를 검증한다.
복원 검사의 현재 RHS 평가1회는 허용하며 과거 replay/초기 재정규화·시간 전진/적분은0이다.
새 출력은 기존 continuation checkpoint가 아니며 그대로 다음 구간에 넣을 수 없다.

inputs는 닫힌 schema_version=`growing-geometry-leaf-removal-point-input-v1`, input_id,
origin=`synthetic`, context_sha256, checkpoint_sha256, at_elapsed_seconds_exact,
mass_basis, events다. exact seconds는 기존 reduced 정수 문자열/`s` 형식이며
`step_index * Fraction.from_float(step_seconds)`와 같아야 한다. UTC를 새로 만들지 않는다.
raw input/결과는 각2MiB 이하, ID1–200 ASCII·원512잎 한도다.

mass_basis는 닫힌 `{origin=synthetic,evidence_level=assumed,evidence_id,model_floor_area,leaves}`다.
footprint의 `m2_floor`는 원 context와 같고, leaves는 모든 현재 잎의 정확한 순서의
`{leaf_id,carbohydrate:{value,unit=mg_CH2O}}`다. 질량은 각각 양수 정상 binary64의 명시 합성 가정이다.
면적이나 SLA에서 만들지 않는다. Fraction(binary64)의 질량 합/footprint를 한 번 반올림한 값이
원 C_leaf와 정확히 같아야 한다. 실제 개별 잎 탄소 분배를 추정/검증했다는 뜻이 아니다.

각 event는 닫힌 event_id, leaf_id, carbohydrate(`mg_CH2O`),
capacity(`J/m2_floor/K`), sensible_energy(`J/m2_floor`), outgoing_temperature(`degC`)다.
원 ID/고유 사건·잎을 지정하며 C는 해당 mass_basis와 같아야 한다. 사건 순서는 선언 순서를 보존한다.
capacity/energy/temperature를 누락하거나 면적에서 자동 채우지 않는다.
완전 제거/빈 수관, 연속 leaf C 제거율 또는 연속 capacity_outflow가0이 아닌 경우는 hold한다.
현재 모델은 각 연속 유출의 기관 귀속을 기록하지 않아 같은 잎의 중복 차감을 배제할 근거가 없다.
원 여섯 저장 프로그램의 nonzero capacity_outflow도 이 첫 point에서는 hold하며 원 입력을 수정하지 않는다.

검증할 회계는 고정 k와 동일 footprint에서 `ΔCcap=k*removed_area/floor`,
`Tout=Tc_before`의 명시 well-mixed 사건과 `Eout=ΔCcap*(Tout-Tref)`다.
이 식은 caller의 별도 용량/현열 선언을 검증하며 실제 잎 물질을 면적에서 추론하지 않는다.
용량/현열은64ulp 원 항 규모로 대사한다. signed energy를0으로 clamp하지 않는다.
원 Uref에서 명시 Eout을 빼며 재맞추지 않는다. 남은 용량으로 복원한 Tc의 차이는 기존2e-13K 이내다.
잘 섞이지 않은 제거·추가 순간 열/물/출현·k 변화는 미지원이다.

원 C_leaf에서 명시 제거 C/floor를 한 번 차감한다. 남은 명시 질량 합/floor와64ulp 안에서 대사하고
buffer/stem/50과실 C/N·필터/공기·증기·남은 잎 a/A·D0/원 초기 영수증·21개 과거 누적량은 변경하지 않는다.
현재 A를 curve로 다시 맞추지 않는다. 현재와 마지막 제거 상태·선언/원 checkpoint/context/코드/profile SHA,
원 정확 시각과 별도 사건 C/용량/현열 장부를 반환한다. 부분 성공/입력 변경·DB/CLI/network/쓰기는0이다.
동일 원 입력의 재실행은 동일 결과이며 영속 exactly-once/현재 farm 권한은 외부 계약이다.

수용은 새 zero-continuous-outflow 합성6조건의 초기/중간/완료 및 분수 dt,
한 잎/동시 두 잎 제거의 독립 Decimal/Fraction C·LAI·용량/현열/온도·잔차,
원 a/A/D0/과거 장부 불변·동일 재실행·다음 context로 오인 거부,
단위/시각/코드/profile/SHA/목록/중복/누락/과다·완전 제거·잘못된 탄소 분포/연속 유출 거부다.
기존 continuation/면적·열 회귀와 별도 fresh·4root/원 자료/WSL을 확인한다.
scope=`software_research_only`, claim_scope=`synthetic_independent_area_leaf_removal_point_only`, G0_G4=`not_assessed`다.
다음 구간·분할 재개/출현·공급·전체 작기·생산/자원/경제/추천과 제품 게시·R2는 별도다.
