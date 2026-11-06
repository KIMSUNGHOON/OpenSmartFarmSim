# 조건부 항목별 비용 저장 결과 조회 v1

상태: [신규37/기존77=114개 집중 검사·실제 SCRAM 수용](../research/economic-cost-stored-result-query-20261106.md). [불변 비용 worker](economic-cost-execution-worker-v1.md)가 게시한 원 결과의 현재 조회 단계다.

`EconomicCostResultQuery(authority).read(tenant, canonical_job_uuid)`는 실제 EconomicBatchAuthority만 사용한다.
정확 `economic-cost-line-calculation-input-v1`의 완료 작업과 `economic-cost-line-calculation-result-v1`만 읽는다.
미완료/없는 작업과 다른 family는 `None`이며 다른 tenant·현재 권리 철회·잘못된 저장 결과는 반환하지 않는다.
반환 `StoredCostResult`는 원 envelope bytes, 최초 publication ID/시각과 typed CostTraceResult를 담는다.
`decode_stored_cost_result(raw)`는 잘못된 trace를 `CostResultHold`로 거부한다.

기존 EconomicBatchResultQuery의 단일 SQL/metadata·read-only 거래·현재 참조 준비·원본 재조회 경계를 공유한다.
고정 입력 version/type·envelope·참조 서비스·artifact·반환/hold type과 참조·decoder·코드 fence·결속 함수 identity를
생성 시 불변으로 캡처하고 현재 선택자/함수와 전후 대사한다. 요청은 프로그램이나 저장소를 고르지 않는다.
metadata/artifact와 원 source/hold/context 읽기 scope가 필요하며 simulation_execute는 요구하지 않는다.
현재 authority/provider/root/content binding, 원 input SHA/전체 입력, publication/manifest와 최초 이력을 재검사한다.

decoder는 전체2MiB 경계·canonical JSON·엄격한 typed trace와 원 nested base_result를 검증한다.
기존 batch decoder로 원 inventory tuple key·null·Decimal 문자열을 복원하고 같은 canonical bytes를 다시 확인한다.
유한 값·허용 scope/G0–G4/R2/currency·고정 trace/code/component와 trace_id를 제외한 원 payload SHA를 대사한다.
추가/누락 필드·비문자열 금액·중복/누락 category나 월·잘못된 판본/지문/identity는 보류한다.

원 batch 조회의 scenario/입력 provenance·생산 batch/원 ledger identity 결속을 nested base_result에 재사용한다.
별도로 현재 scenario와 정확한 기간·순서/분류/Cost 원문·setoff·지급 상태/선언·월 범위 및
원 ledger에서 복사한 group/month 성분을 구조/원 값의 동등성으로 대사한다.
CostLineLedger·원 v10/EconomicLedger·worker를 실행하지 않으며 비용 line/group/month/reconciliation 함수를 호출하지 않는다.
금액/수량을 재계산하거나 합산하지 않고 해시·형식 변환·원 값 비교만 수행한다. SQL 쓰기는0이다.

outer envelope의 과거 worker/environment SHA는 원 이력으로 보존하며 오늘 orchestration 지문과 비교하지 않는다.
원 input/artifact SHA·원 result SHA, 현재 지원 숫자 코드와 원 source/권한은 별도로 확인한다.
반환 전에 metadata와 원 artifact bytes를 다시 읽고 현재 참조/권한/프로그램을 검사한다.
동시/늦은 원본·권한·코드·publication/root/provider/선택자 교체에는 원 버퍼를 반환하지 않는다.
재조회는 원 bytes/최초 publication을 바꾸지 않으며 반환 객체는 재호출 사이에 공유하지 않는다.

기존 batch query의 constructor·_Envelope·codec·version·StoredBatchResult·기본 동작과 오류 protocol을 보존한다.
공유 query의 원 bytes만 수용 commit `4edef92da8ebb7849ccde96a9d8f97e9c385b856`의
`backend/app/economic_batch_query.py` Git snapshot으로 검증하는 새 예외를 보존 증거에 명시한다.
과거5 manifest의 같은 query pin도 이 snapshot으로 대사한다. 기존 worker 경로의 Git `8f7606c3f99696d139961226829f21571348833e` 예외는 유지한다.
다른 숫자 모델/입력·원 산출물과 과거 manifest/receipt/script는 바꾸지 않는다.

수용: 실제 소유 SCRAM의 신규 reader·독립 새 프로세스에서 전체 typed 원문/최초 이력·null/inventory·변조/재해시 Cost 결속,
현재/늦은 권한·원 source/hold/context·지원 코드·metadata/raw/root/provider/selector 변경과 금액 호출/SQL 쓰기0,
기존 batch query/HTTP/runtime/자동 소비 회귀 및 원 자료/만료 화면·WSL 보존이다.
새 비용 HTTP/runtime/자동 소비·SDK/UI와 원 자원 창/독립 구매·청구 기간 결속은 후속이다.
자체 합성 QA이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 제품 목표 미완료를 유지한다.
