# 명시 잎 탄소 배분의 같은 stage 공동 RHS — 연구 v1

상태: **합성 같은 stage 공동 RHS 수용** — [79신규/293관련·fresh42조건](../research/crop-leaf-partition-climate-rhs-20261025.md). [배분 산술](crop-leaf-carbon-partition-v1.md)과
[출현/공급 의존성 판단](../research/leaf-carbon-sink-primary-sources-20261024.md)의 다음 자식이다.
새 생리 법칙/계수·개별 C 재고·시간 전진·출현/면적 공급 제한을 추가하지 않는다.

`evaluate_rhs(*, scenario, leaf_stage, growth_profile, cohort_profile, transport_profile, exchange_profile)`.
scenario는 기존 [명시 LAI 공동 RHS](crop-explicit-lai-climate-rhs-v1.md)의 닫힌 합성 stage이며 원4profile을 받는다.
leaf_stage는 닫힌 input_id/origin/policy/leaf_ids/sinks다. input_id는 scenario.input_id와 같고 origin=`synthetic`,
policy는 `explicit-relative-leaf-sinks-and-empty-deferral-v1`이다.
leaf_ids는 호출자가 선언한 현재 stage의 원 ID 순서이며1–512개의 고유 ASCII ID다.
sinks는 같은 수/순서의 leaf_id·sink_weight(`1`)를 명시한다. 누락/추가/중복/순서 변경은 hold다.
현재 함수는 호출자의 선언을 같은 stage에 결속할 뿐 저장 문맥/농장 provenance를 검증하지 않는다.
추후 개별 재고/재개에서 현재 원 목록을 공급해야 하며 여기서 ID나 면적·질량을 추정하지 않는다.

원 공동 RHS를 한 번 평가한 뒤 그 원 leaf allocation G를 배분기에 정확히 한 번 전달한다.
G를 외부 입력으로 받거나 원 source 출력을 이미 조정된 결과로 바꾸어 다시 조정하지 않는다.
원 RHS의 계산 domain/hold는 유지한다. 특히 원 평가가0 buffer/기타 고갈에서 hold라면 이 단계는
조정 후 상태가 가능하다고 가정해 그 hold를 우회하지 않는다. 고갈/개별 재고는 후속 계약이다.

배분기의 미사용 D와 고정 c=cLeafG에 따라 원 미분/비용을 다음과 같이 **같이 한 번** 조정한다.

- buffer′ = 원 buffer′ + D+cD
- leaf′ = 원 leaf′ − D
- 전체 생장호흡 = 원 전체 생장호흡 − cD
- 실제 leaf allocation = G−D. requested allocation은 G를 보존한다.

같은 stage의 P·기존 과실 startup/50C·50fruit-number N·stem_root/온도 상태,
수관/공기 현열·증기/면적/총 용량 흐름은 원 결과 그대로다. N은 질소가 아니다.
면적이나 열용량에서 조직 C를 역산하지 않으며 잎 sink0을 자동으로 면적 확장0과 동치로 두지 않는다.
공통 pool 상대 priority라는 자체 조건부 정책이며 원 논문의 beta 수요·reserve 전체 모델을 구현하지 않는다.

원 결과는 `source_joint`에 원 calculation SHA/모든 값 그대로 보존한다.
`leaf_partition`도 원 배분 결과/hash를 재검사·보존한다. `adjusted_carbon`과 최상위 derivatives/balance는
새 판본으로 반환하며 원 중첩 객체의 숫자를 바꿔 옛 hash를 붙이지 않는다.
전체 C 수지를 조정된 미분/호흡과 원 P/유지호흡/제거/말단 유출에서 다시 합산하고,
leaf compartment도 실제 배분−원 유지호흡−원 제거와 대사한다.
예산은 원/배분기의 계산 예산과 합산 반올림64ulp로 명시하며 생물학적 정확도가 아니다.

원 입력/정규 stage·4profile·component/정책/새 코드 SHA와 원 source 계산 SHA를 묶는다.
닫힌 입력/출력 각각256KiB·1–512행 범위를 적용한다. 긴 ID/중첩 결과는 byte 상한에서 hold할 수 있다.
비유한/단위·수치/불변식·수지/코드/profile 변경은 hold며 부분 결과를 반환하지 않는다.
DB·CLI/network/쓰기·적분/재초기화0, scope=`software_research_only`,
claim=`synthetic_leaf_partition_joint_rhs_only`, G0_G4=`not_assessed`다.

수용: 원6조건×전부/일부0·다양한 상대 weight의 독립 Decimal 전체 C/leaf 수지와 조정량,
원 P/과실/기후·미수정 미분/값 보존, 각 component1회·source/배분 hash·ID/입력 불변,
512/상한·잘못된 입력/원 hold·새/원 code 변경과 단계 실패, 별도 fresh/원 자료·4root/WSL.
0요청 예산은 선행 배분 산술에서 검증했다. 현재 고정 profile/원 domain의 실제 leaf 요청은 양수이며0요청 사례를 조작하지 않는다.
후속은 권위 개별 C_i와 합계·유지호흡/고갈·같은 stage 적분/분할 재개→조달된 출현→저장/같은 상태3D다.
