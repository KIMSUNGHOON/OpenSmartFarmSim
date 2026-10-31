# 명시 생산 batch의 기간 비용 — v1

[BatchEconomicScenario/ProductionBatchLedger](../backend/app/economic_production_batches.py)는
기존 [schema3/원장 v9](../backend/app/economics.py)를 보존하는 **schema4/원장 v10 계산 커널**이다.
조건부 사용자 가정만 받으며 제품 API/worker/DB/3D 연결은 아직 없다.
[구매량 경계](supply-material-resource-economics-binding-v1.md)는 그대로 유지한다.

## 입력과 소유권

`BatchEconomicScenario`는 기존 모든 경제 입력과 필수 `production_batches` tuple을 가진다.
각 항목은 `batch_id`, `revision`이다. 동일 batch ID는 한 번만 선언하며 최대512개다.
빈 목록은 명시한 현재 생산 batch가 없다는 뜻이다. 기존 schema3를 자동 변환하지 않는다.
현재 scenario/소유 batch records/결과는 각각2MiB로 제한한다.

trusted repository는 기존 경제 메서드에 `get_production_batch(batch_id, revision)`을 제공해야 한다.
반환은 다음 불변 소유 record의 원 dict다. 호출자는 repository를 요청 payload로 전달하지 않는다.

| 필드 | 의미·검증 |
|---|---|
| `batch_id`, `revision`, `tenant_id` | 원 참조/인증 tenant와 같아야 함 |
| `production_start_at` | UTC 시각. 이 배치에 귀속한 첫 생산 활동의 가정 시작이며 정식일·발아/생물학적 예측이 아님 |
| `origin=user`, `evidence_level=assumed` | 기존 첫 조건부 원장과 같은 등급. measured/quoted/modeled로 승격하지 않음 |
| `source_ref`, `assumption_scope` | 비어 있지 않은 원 사용자 근거·적용 범위 |
| `available_at` | UTC, decision_at 이전 또는 같음 |
| `scope_start`, `scope_end` | 평가기간 전체를 포함하는 달력 날짜 |
| `rights=conditional_g1_use`, `immutable=true` | 이 내부 조건부 사용을 위한 소유 record. JSON 불리언 true만 허용하며 숫자1은 거부 |

권리 필드는 G0/농장 자료·공개 표시/재배포 승인이 아니다.
실제 자료/생산 source 결속은 별도 현재 권리·불변 저장/제품 계약을 거쳐야 한다.

기존 canonical scenario/job pin·tenant 인증·원 숫자/기간/단위·시장 hold와 정산 검증을 재사용한다.
수확 또는 production Cost의 batch는 위 소유 선언 안에 있어야 하고 시작 시각보다 빠를 수 없다.
기초 판매 가능 재고 batch와 현재 생산 batch의 중복은 거부해 과거 생산비 재부과를 막는다.
원장이 원래 거부하는 기간 밖 비용·중복 사건·원장 목적/수량·재고/현금 불일치도 계속 거부한다.

## 계산과 결과

기존 Decimal128 exact-domain 비용·재고·현금 산술을 상속한다.
새로 허용하는 것은 **기간 전체에 수확이 없는 선언 batch의 production 비용**이다.
수확/판매/수확0 사건을 만들거나 production을 period로 바꾸지 않는다.
변동 직접비는 V, 고정 직접비는 F에 원래대로 한 번 들어간다.
아직 수확/선별하지 않은 작물을 판매 가능 kg나 판매 재고 가치로 만들지 않는다.

`ProductionBatchResult.ledger`는 기존 결과에 새 formula_version과 result_id를 부여한다.
같은 기간에 나중 수확이 있는 경우 원 schema3의 수치·현금·재고 결과를 보존한다.
명시 소유 batch 기록과 batch별 다음 요약을 함께 반환한다. 모든 금액 단위는 KRW다.

- `variable_incurred`, `fixed_incurred`: 해당 production Cost만의 부분합이다.
  공통 period 비용이나 sale 비용을 배분/재가산하지 않는다. 원 비용 그룹이 미확인이면 null이다.
- `cash_paid_in_period`: 원 지급 중 이 평가기간 안의 해당 production 비용 지급 합이다.
- `remaining_payable_at_period_end`: 발생 직접비에서 위 기간 지급을 뺀 값이다.
  기존 정산 상계는 sale 비용 전용이며 production 요약에 섞지 않는다.
- `harvest_event_declared`: 입력에 그 batch의 수확 사건이 있는지다. 실제 수확·생존·생산량 검증이 아니다.

지급일/금액이 미확인이면 현금·잔여 미지급액 요약도 null과 원 hold를 유지한다.
기간 후 지급일/금액이 명시된 가정은 현재 지급0·기말 미지급과 미래 지급 schedule로 구분한다.
알려진 미지급을 확정하려고 허위0원 지급 사건이나 날짜를 생성하지 않는다.
새로운 ‘지급일 미정이나 미지급이 확정된 거래’ 상태를 이번 입력에 추가하지는 않았다.

기존 날짜는 UTC 저장/Asia-Seoul 결산이며 미래 지급을 현재 월의 현금에 넣지 않는다.
수확·판매·매출/재고/마진의 필수 입력이 누락되면 기존 hold를 유지한다.
현재 생산 직접비/기간 현금 계산은 작물 모델이 산출한 구매량·농장 청구액이나 미래 수익 예측이 아니다.

## 지문·변경 차단·범위

새 모듈과 원 economic_contracts/economics/market/provenance 코드 지문을 전후 확인한다.
원 scenario/경제 입력과 시장 조건을 다시 검증하고 소유 batch 기록이 같음을 확인한 뒤 반환한다.
원 scenario SHA·batch 기록 SHA·계산/구성 코드·formula_version을 result ID에 결속한다.
같은 입력의 재생은 같은 bytes이며 원 판본·참조 변경은 새 result ID를 낸다.
`result_bytes`는 Decimal을 문자열, 판매 재고 tuple key를 명시 행으로 표현하며 원 typed 결과를 바꾸지 않는다.
공개 HTTP 응답 계약·서명 저장의 대체물은 아니다.

현재 연구 결과는 `assessment_status=hold`, G0–G4 미평가/R2 미승인을 유지한다.
재배 batch 선언은 실제 작물 모델/생장 상태를 등록한 증거가 아니다.
기존 한 batch당 수확1사건·기초 미지급/미수금의 첫 조건부 범위 등 v9 제한도 유지한다.
연속/다회 수확과 생과중·자원 구매·실제 농장/모델/제품 작업 결속은 후속이다.

[새37/기존169 검사·독립4사례·보존 증거](../research/economic-production-batches-20261031.md).
