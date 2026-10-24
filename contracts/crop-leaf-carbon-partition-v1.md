# 명시 잎 sink의 탄소 예산 배분 — 연구 v1

상태: **합성 순수 산술 자식 수용** — [54신규/187관련·fresh72조건 수용](../research/leaf-carbon-partition-20261024.md). [원문·의존성 판단](../research/leaf-carbon-sink-primary-sources-20261024.md)의 첫 순수 산술 자식이다.
기존 합계 leaf C와 독립 a/A 모델을 바꾸거나 새 잎/품종을 예측하지 않는다.
기관 C 원장/출현·공급 feedback·전체 작기와 farm/G0–G4는 후속이다.

`calculate_partition(*, inputs, growth_profile)`는 현재 고정 `ReferenceParameters`를 받는다.
닫힌 inputs는 input_id/origin=`synthetic`/policy/requested_leaf_growth/leaves다.
policy는 `explicit-relative-leaf-sinks-and-empty-deferral-v1`을 명시해야 한다.
requested_leaf_growth는 이미 상위 RHS가 요청/차감한 구조적 leaf CH2O 예산 G (`mg_CH2O/m2_floor/s`)다.
leaves는1–512개 원 순서의 고유 leaf_id와 명시 sink_weight(`1`)다.
상대 weight는 합성 조건부 입력이며 면적·질량·생리 계수나 절대 수요 상한이 아니다.
기본 균등 배분·면적/SLA 역산·다른 질량 단위의 자동 환산을 하지 않는다.
G와 weight는 bool 제외 유한 비음수 정상 binary64/0이다. 입력/출력은 각128KiB 이내다.

W=Σw가 양수면 각 구조적 유입은 `g_i=G*w_i/W`, 실제 합계 예산 F=G, 미사용 D=0이다.
W=0이면 모든 g_i/F=0, D=G다. 중간 나눗셈의 유실을 줄이기 위해 원 float의 정확 Fraction 비로 계산하고 각 g_i를 한 번 반올림한다.
이 정책은 상대 우선순위만 나타내며 g_i≤w_i 같은 차원 없는 수요 상한을 만들지 않는다.
공통 pool/상대 sink라는 원문 개념을 참고한 프로젝트의 조건부 정책이며 원 FSPM의 beta 함수·reserve 처리 전체를 재현하지 않는다.

기존 고정 growth profile의 cLeafG=c를 사용한다. 요청/실제/회피 생장호흡은 cG/cF/cD다.
상위가 G+cG를 이미 buffer에서 차감했다는 기준에서 다음 세 조정을 **함께 한 번** 적용해야 한다.

- buffer derivative: `+(D+cD)`
- aggregate leaf derivative: `-D`
- whole-plant growth respiration: `-cD`

이 함수는 조정량만 반환하며 상위 상태를 수정하지 않는다. 상위 결합 전에 단독 조정 하나를 적용하지 않는다.
유지호흡/제거·나이/면적/물·현열/과실 수를 다시 계산하지 않는다.
배분 합계·예산 G=F+D·호흡과 위 세 조정의 합계0·원 비용 차감과 실제 유입/호흡의 수지를 검사한다.
반올림 예산은64(n+8) ulp의 계산 수지이며 생물학적 허용 오차가 아니다.
비유한/집계 overflow·양수 배분/호흡의0·subnormal 유실과 잘못된 단위/형식·권리 밖 scope/profile·코드 변경은 hold다.

원 입력·정규 입력/코드·profile·정책 SHA와 원 순서의 배분/각 수지·서로 분리된 요청/실제/미사용·호흡/조정량을 보존한다.
scope=`software_research_only`, claim=`synthetic_leaf_carbon_partition_math_only`, G0_G4=`not_assessed`다.
원 입력/프로필을 바꾸지 않으며 DB/CLI/network/쓰기·성장/시간 전진0이다.

수용은 독립 Fraction/Decimal·고정 원6프로그램의 실제 요청/비용과 조정된 전체 C 수지,
0예산/모든0 sink/일부0/같은 비율/극단 비율/512·상한/잘못된 입력·입력 불변/동일 재실행,
기존 RHS를 다시 호출하지 않는 계산·독립 fresh/원 자료·4root/WSL이다.
공동 RHS 조정의 원자 결속→개별 C 상태/같은 stage 적분·고갈/제거→새 잎 초기 C·용량/현열의 출처 순으로 후속 수용한다.
실제 source/품종별 sink·공급 제한/면적 feedback과 독립 농장 검증은 별도로 남는다.
