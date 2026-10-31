# material 저장 창과 조건부 자원 비용의 결속 v1

상태: **구현 전 입력·검증 계약**. [8counter 조사](../research/supply-material-energy-primary-sources-20261031.md)와
[기존 경제 계약](../docs/ECONOMICS.md)의 범위다. 현재 조회/3D와 기존 경제 schema3를 변경하지 않는다.
새 계산기·추정 요금·농장 권한·예측/추천을 만들지 않는다.

## 계산값과 구매량의 경계

원 [quantity window](supply-material-quantity-window-v1.md)의8개 연속 counter는 원 부호와
`J/m2_floor` 또는 `kg_water/m2_floor`를 보존한다. 전기·연료·급수의 양수 구매 계량량으로
직접 입력하거나 절대값/양수 절단·단순 합·요금 곱으로 바꾸지 않는다.
내부 현열/잠열은 reduced-energy 수지에서 상쇄된다. 열용량 유입/유출 에너지는 기준온도 상대값이다.
외부 forcing에도 설비·구매 경계가 아직 식별되지 않았다.

물리적 열량의 단위 변환과 설비의 구매 전력 변환은 별개다. 구매량을 모델에서 만들려면
동일 시간·floor basis의 제어/설비 경계·전달열/냉각·운전점/COP·보조전력/손실·계량 대사가 필요하다.
급수는 배지·급액/배액·재순환/저장 수지와 구매 계량을 먼저 구분해야 한다.
이번 입력 계약은 이러한 매개변수나 변환 경로를 추가하지 않는다.

## 다음 구현의 입력과 출력

첫 범위는 **불변 연구 저장 창과 명시 사용자 가정의 비용을 함께 검토하는 조건부 결과**다.
두 입력의 관계는 `independent_user_assumption`이며 모델 counter에서 구매량을 도출했다는 뜻이 아니다.
현재 material 연구 root에는 소유 FarmScenario/작업 결속이 없으므로 제품 농장 작업에 임의 결합하지 않는다.
제품 통합에는 실제 소유 source/결과 등록·현재 권한과 같은 농장/평가기간의 결속 수용이 별도로 필요하다.

| 입력 | 필요한 내용 | 검증/누락 처리 |
|---|---|---|
| `material_selection` | 원 root SHA·quantity projection code/result SHA, first/last index·원 frame/state/source cursor·phase·정확 시작/끝·floor basis | trusted reader의 현재 source/권리/code fence로 얻는다. 원 결과나 원 선택을 재구성하지 않는다. 변경/불일치 때 결속 폐기 |
| `economic_selection` | 기존 scenario ID/revision/canonical SHA·tenant·decision_at·평가 시작/끝·market context | 기존 서비스의 소유 불변 job 입력/pin 검증을 재사용한다. 호출자가 repository나 tenant를 선택하지 않는다 |
| `resource_cost_refs` | 기존 `Cost.id`와 원 `EconomicNumber` 입력 ID/revision·origin/evidence/assumption_scope/source_ref/available_at, 전기·연료·물의 명시 품목/범위 | trusted 소유 입력과 값/단위/기간 일치, decision_at 이전 이용 가능성과 scope를 확인한다. 이름만으로 새 비용이나 단가를 생성하지 않는다 |
| 비용의 시간·범위 | 원 incurred_at, paid_at/payment 또는 명시 미지급, 실제 가정한 구매/청구 기간과 비용 포함 항목 | source 시각과 경제 발생/지급일을 분리한다. 한 달의 비용을 수초의 선택 구간 비용으로 표시하지 않는다. 범위 미확인은 금액0이 아니라 hold |

출력은 원 material 참조/정확 창, 원 economic 선택/Cost 참조, 독립 사용자 가정이라는 관계,
검증된 범위·등급과 hold를 보존한다. 기존 Decimal 원장이 산출한 비용 항목의 금액만 사용한다.
새로운 매출·수확·과실 생과중·전체 사업비·마진·작물 순위 또는 관문 승격을 만들지 않는다.
결과를 저장할 때 두 입력 판본/선택과 계산 코드가 바뀌면 새 판본으로 남긴다.

## 기존 Decimal 원장에 그대로 남는 규칙

[EconomicNumber](../backend/app/economic_contracts.py)는 현재 십진 문자열,
`origin=user`, `evidence_level=assumed`만 받는다.
현재 비용 쌍은 `kg/KRW/kg`, `month/KRW/month`, `kWh_e/KRW/kWh_e`, `L/KRW/L`이다.
이 중 자원 연결의 첫 범위는 명시한 전기 `kWh_e` 또는 품목이 확인된 연료/물 `L`이다.
같은 `L`이라는 이유로 연료와 물을 합치지 않는다. `kWh_th`, `kWh_fuel`, `m3`나
`measured/quoted/modeled`를 다른 지원 단위·가정 등급으로 바꿔 통과시키지 않는다.
필요하면 별도 판본의 단위/근거 계약과 독립 회귀를 먼저 수용한다.

[EconomicLedger](../backend/app/economics.py)는 원 소유 scenario/input pin과 market hold를 검증하고
128자리 Decimal exact domain에서 비용을 계산한다. 발생 비용과 실제 지급을 구분하고
금액·통화/단위·날짜·미확인/미지급·미배분과 기존 중복 비용 검증을 유지한다.
동일 자원 비용을 원 scenario와 새 자원 요약에서 두 번 합산하지 않는다.
기본/수요/조정/세금·고정 항목이 없는 사용량×단가는 전체 청구서가 아니다.

`purpose=production` 비용은 평가기간 안의 harvest 목록에 그 batch가 있어야 한다.
같은 기간 후반에 명시한 수확보다 먼저 발생한 비용은 이 조건을 충족할 수 있다.
그러나 **평가기간 전체에 수확 사건이 없는 재배 중 batch**는 현재 원장이 받지 않는다.
이를 위해 수확0 사건을 만들거나 작물 직접비를 `period`로 바꾸지 않는다.
그 범위가 필요하면 명시 재배 batch/미수확 생산비 계약·재고/기간 비용/현금 대사를 별도 구현한다.
실제 공통 기간 비용만 원래의 `purpose=period` 의미로 받는다.

## 시각·표시·게시

원 저장 시각은 UTC 원점+정확 분수 초다. 경제 사건은 원 UTC datetime,
평가/청구 달력은 Asia/Seoul이다. 원 분수 초를 float나 microsecond 반올림으로 바꿔
발생/지급 사건을 생성하지 않는다. 날짜 경계가 필요한 후속 구현은 정확 시각으로 판정하고
원 분수를 계속 남긴다. source 창과 경제 적용 기간을 각각 표시한다.

누락된 실제 구매/설비/가격/농장/전체 필수 비용은 명시 hold다. 원8counter 표시와 독립 가정의
부분 비용 검토를 할 수 있어도 모델 구매량·농장 청구액·마진·추천 게시를 해제하지 않는다.
독립 자료 확보와 모델 개발은 병행한다. G0–G4/R2와 전체 작기/최종 제품의 기존 의존성을 유지한다.

## 다음 구현의 수용 기준

1. 실제 source-bound quantity 조회와 불변 소유 economic 입력 판본을 각각 검증한다.
   원 counter/단위·부호/시각·phase·해시를 그대로 보존하며, 새 구매량/가격 생성0을 확인한다.
2. 기존 원장의 숫자/소유권/기간/단위·등급·반올림/현금 검사를 재사용한다.
   독립 Decimal oracle, 늦은 권리/입력 변경·취소/중복, 누락/범위 불일치 hold를 통과한다.
3. 기간 일부의 합성 창·원 가정 비용·포함/누락 범위를 분리해 표시한다.
   숫자만 맞는 것을 전체 농장 비용·생산 마진이나 같은 창의 설비 구매량으로 표시하지 않는다.
4. 사용자 화면/3D 연결 전에는 새 backend 결과·strict SDK를 먼저 검증한다.
   실제 생산 배치/기간 결속이 없는 입력은 연구 결과만 내며 제품 FarmScenario에 게시하지 않는다.
