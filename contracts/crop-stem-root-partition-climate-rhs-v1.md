# 같은 시점의 줄기·뿌리 배분 공동 RHS — 연구 v1

상태: [신규96/관련159·255검사와 독립 fresh72조건 수용](../research/stem-root-partition-climate-rhs-20261027.md)의 합성 순간 RHS 자식. [배분 산술](crop-stem-root-carbon-partition-v1.md)을 [현재 개별 잎 재고 RHS](crop-leaf-carbon-stock-rhs-v1.md)의 같은 시점에 결속한다. 시간 전진·기관별 stem/root 재고·길이 feedback·farm/Run 승인은 없다.

`evaluate_rhs(*, scenario, leaf_stocks, stem_root_stage, growth_profile, cohort_profile, transport_profile, exchange_profile)`.
scenario와 leaf_stocks는 기존 source가 소유하는 닫힌 계약 그대로다. stem_root_stage는 닫힌 input_id/origin/policy/model_floor_area/compartments이며 G를 받지 않는다. 같은 input_id·synthetic origin·배분 정책·명시 양의 floor를 요구한다. floor는 원 scenario.geometry 및 leaf_stocks와 같아야 한다. compartments는 원 순서의 고유 ID·명시 kind(internode/root_system)·상대 sink_weight이며 정확히 하나의 root_system을 요구한다. 기본 기관이나 배분율을 만들지 않는다.

명시 기관 목록은 합성 배분처다. 기존 잎/기후 source에는 절간·뿌리의 현재 재고나 저장 geometry 계보가 없으므로 이 함수만으로 실제 저장 절간 ID·형태와 결속했다고 하지 않는다. 해당 결속은 초기 기관 재고/발달 프로그램의 후속 계약이다.

원 개별 잎/기후 source를 **한 번** 평가한다. 원 code·4profile·raw 입력/계산 hash와 정상 연구 scope를 대사한다. 그 결과의 `source_stage.source_joint.crop.allocation.stem_root`를 G로 읽는다. 이는 유지호흡/제거 전의 구조 유입이며 `derivatives.plant.stem_root`가 아니다. 원 leaf-adjusted allocation의 stem_root와도 같아야 한다. 같은 G·floor·프로필·원 선언 기관으로 배분 산술을 **한 번** 계산한다.

배분 원 입력/정규 입력·정책/프로필/code·계산 hash·기관 ID/순서·단위를 대사한 뒤 buffer·stem_root 미분과 전체 성장호흡의 세 조정을 함께 한 번 적용한다. 조정이0이면 원 값을 그대로 유지한다. 조정 후에도 현재 buffer 또는 aggregate stem_root가0이면 해당 미분이 음수가 될 수 없다. 원 source의 유입으로 가능했던0재고 flow-through가 보류 뒤 불가능해지면 DEPLETED_STATE_HOLD이며 제거량/재고/미분을 임의로0 처리하지 않는다. 잎별 유입/유지호흡/제거·합계·원 P/과실/기후/나머지 미분은 그대로다. source 자체가 hold인 경우 그 상태를 이 함수에서 임의로 복구하지 않는다.

원 authoritative 잎 합계·과실 C·변경된 buffer/stem_root·변경된 성장호흡과 원 유지호흡/제거/terminal outflow/P로 전체 C 수지를 다시 계산한다. 변경된 stem_root 미분 + 원 stem/root 유지호흡/제거 − 개별 배분 합계도 대사한다. 기존 장부를 보존하며 새 carbohydrate/stem_root_compartment 장부와 원 예산+배분/계산 roundoff를 기록한다. 이는 수치 반올림 예산이지 생물학적 오차 기준이 아니다. 비유한/음의 호흡·단위/식별자·source/profile/code/hash/수지 불일치와 입력/출력 각512KiB 초과는 hold다. 기존 원512잎 RHS byte-cap hold를 상향/축소하지 않는다.

원 source 결과와 배분 결과를 보존하고 새 판본·입력/정규 입력·정책/code/profile/계산 hash·원 선언 기관 순서를 반환한다. 원 source/partition·입력/프로필은 수정하지 않는다. source/배분/하위 각 함수의 호출 수, 독립 Decimal 전체 C/기관 수지와 0/혼합 sink·최소/상한·변조/hold·fresh/자료·GUI/WSL 보존을 수용 기준으로 한다.

scope=`software_research_only`, claim=`synthetic_stem_root_partition_joint_rhs_only`, G0_G4=`not_assessed`, time coordinate=`derivatives_per_second_no_time_advance`다. DB·CLI/network/쓰기·solver/새 초기값·재개/출현 비용·기관별 현재 stem_root C·길이/수확/자원 구매·경제/추천을 계산하지 않는다. 해당 개발과 실제 품종/농장 자료 확보를 병행하고 실제 주장/게시 관문을 구분한다.
