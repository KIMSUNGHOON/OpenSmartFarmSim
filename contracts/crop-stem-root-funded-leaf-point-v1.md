# 개별 stem/root 재고를 보존하는 새 잎 조달점 — research v1

상태: [신규69/관련128·별도6문맥/독립812항목 수용](../research/crop-stem-root-funded-leaf-point-20261027.md). [원 잎 점](crop-leaf-funded-birth-point-v1.md)의 명시 추가 구조 형성/기준온도 상대 현열 가정을 [기관별106+3n+m 상태](crop-stem-root-stock-continuation-v1.md)에 이식한다. [초기 source 연결](crop-stem-root-initial-binding-v1.md)과 [새 절간 점](crop-stem-root-funded-internode-point-v1.md)을 참조하며 원 모듈/계수는 수정하지 않는다. 자동 출현 판정·변경 목록 CP/시간 전진·공급 제한 A/실제 품종 승인은 후속이다.

`apply_leaf_births(context, raw_checkpoint, expected_sha256, crop_directory, stem_directory, access, *, crop_root_sha256, stem_root_sha256, stem_start_index, binding_declaration, inputs)`는 검증된 현재 CP·원 초기 source를 사용한다. 닫힌 inputs는 schema_version=`stem-root-funded-leaf-point-input-v1`, input_id/origin=synthetic/policy=`explicit-new-leaf-carbon-from-buffer-v1`, context_sha256/checkpoint_sha256/initial_binding_sha256, at_elapsed_seconds_exact/model_floor_area, events/rights/reviewer다. 원 Context/CP raw SHA·현재 상태/원 장부와 현재 초기 source 전체 canonical hash를 검사하고 실제 CP의 reduced exact step×index/원 floor를 요구한다. 전/후 source/권리·코드/profile를 재검증하며 CP 진본/농장 권한 발급은 별도다.

각 event는 event_id/parent_internode_id/incoming_temperature/leaf다. parent는 실제 pre-point 목록의 internode ID이며 root/없는 ID를 허용하지 않는다. leaf는 원 c_i/a/A 계약의 완전한 leaf_id/curve/thermal_age/base_temperature/initial_area/initial_carbon/sink_weight/carbon_removal다. 0나이·양의 명시 C/F(0)·nonnegative sink/removal·중복 없는 leaf/event ID, 최종 잎≤512를 요구한다. 원 logistic 하한0의 F(0)>0을 사용하고 초기 요청 A는 원1e-12상대 오차로 검사한 영수증/정규 면적을 보존한다. 현재 기존 잎의 A/나이/D0를 다시 정규화하지 않는다. 면적→C/SLA/기본 seed/실제 질량 추정은 없다.

원 pinned cLeafG로 새 질량의 정확 binary64 합 S에 대해 structural=round(S), Rg=round(cLeafG·S), debit=round((1+cLeafG)·S), buffer_after=round(buffer_before−debit)>0이다. cStemG로 대체하거나 연속 조달을 환급/재차감하지 않는다. 숨은 조직의 이미 지불한 재고 공개에는 별도 이동 모델이 필요하다.

각 ΔK_i=round(k_leaf·canonical_F_i(0)/floor), E_i=round(ΔK_i·(T_in_i−T_ref))이며 명시 incoming T를 요구한다. 합계를 정확히 한번 반올림해 U_after=round(U103_before+ΣE_i)로 반영한다. buffer0/U103 외 원 첫106scalar를 보존하고 old age+새0/old A+새canonical A/old leaf C+새 C/원 모든 stem/root C를 순서대로 조립한다. after RHS가 같은 상태의 수관온도/열용량을 계산한다. 화학 에너지를 임의 열로 변환하거나 완전한 물/열 첫 법칙을 주장하지 않는다.

검증된 현재 데이터용 내부 `_jump(program,state,profiles,events,anchors)`를 제공한다. public wrapper가 source/CP/time/권리 검증을 소유하며 후속 가변 목록 조립은 자신의 typed 현재 CP를 검증한 뒤 산술을 재사용한다. old token/Context를 가장하지 않는다. 기존 anchors는 그대로이고 새 canonical 초기 면적의 gap0을 덧붙인다. buffer/new-stock/whole-C/U/K point 장부와 새 leaf별 C 장부를 원64ULP 예산으로 검사한다. 현재 CP RHS1회+after RHS1회이며 과거 전진/기존 재초기화0이다. 초기화는 선언된 새 leaf에 대해서만 수행한다.

반환은 원 manifest/초기 연결/before CP/입력·권리·현재 source/code/profile hash, after program/sample/rates/layout/anchors, 새 잎 초기 영수증/부모·point 흐름/장부/계산 SHA다. CP=None/시간 전진0, 원 prefix/연속 장부와 분리하고 stateless 재평가만 동일하다. 단일 채택/중복 이력·변경 목록 재개와 자동 threshold/분수 결속은 후속이다. 새 입력 rights/reviewer와 기존 source 권리를 보존하며 어떤 redistribute=False도 승격하지 않는다. 입력/출력2MiB·하위 caps/원512잎 요청 hold를 유지하고 실패 시 부분 결과 없음. DB/CLI/network/write0·G0–G4=not_assessed·time_kind=synthetic_model_clock_not_observation이다.

수용: 실제 owned 초기 source6조건/현재 초기·후기 CP/단일·batch·온도, 원 old point와 실제 준비한 old Context의 상태/흐름 동등성, 독립 Decimal C/ΔK/U/부모·비대상 상태·원 stem/root/leaf D0 보존, 두 종류 core의 교차 조립, 부족/형식/초기 A·시각/권리/profile/code/late source/caps·원 자료/GUI/WSL·fresh 동일 결과/호출 계측이다.
