# 소유 생산 batch 계산 접수 v1

상태: [서버 접수 라이브러리/실제 DB 수용](../research/economic-batch-calculation-admission-20261031.md).
[구현](../backend/app/economic_batch_calculation.py)은 [입력 저장](economic-batch-source-store-v1.md)과
[schema4/원장v10](economic-production-batches-v1.md)의 다음 단계다.

서버는 실제 JobStore·EconomicBatchSourceStore·MarketHoldStore·ThermalRunStore를
같은 schema·authority 로그인 정책/DSN·동일 principal provider에 결속한다.
명시 batch source 프로필과 JobStore의 실제 grant audit가 필요하다.
다른 구현/테스트 facade·누락된 결속과 호출 중 pointer/정책/로그인 변경은 거부한다.

접수 요청은 scenario ID/revision/SHA와 idempotency key만 받는다.
서버가 등록된 schema4와 최초 원 작업 UUID·SHA를 현재 조회한다.
원 커널의 계산 전 입력 검증을 재사용해 숫자/생산 batch·기간·decision_at와
실제 서명 hold/결정 문맥을 검사한다. 근거 지문에는 원 시나리오와 pin,
검증된 batch/입력·hold/결정 문맥을 포함한다.
누락·다른 tenant/기간/원문·과거 근거·현재 권한 부재는 접수하지 않는다.

고정 input_version `economic-batch-calculation-input-v1`과 원장v10,
실제 source 작업 UUID·시나리오 SHA·근거 SHA를 불변 simulation 작업 입력에 저장한다.
같은 요청 재시도는 최초 작업/시각을 돌려준다. 같은 key의 다른 입력은 conflict다.
commit 직전 현재 권한·객체 결속·동일 근거를 재확인하며 실패하면 작업/사건을 rollback한다.
필요 scope는 metadata/economic_batch_source_read/decision_context_read/
market_hold_context_read이고 접수에는 simulation_execute도 필요하다.
참조 준비 검증은 읽기 scope만 확인한다. 접수는 그 전후와 commit 직전에 실행 scope도 검사한다.
따라서 후속 읽기용 결과 검증에 실행 scope를 강제하지 않는다.

접수는 금액 계산/생장 계산·source 수정·결과 게시/관문 승격을 하지 않는다.
등록/접수 성공은 경제 산술 성공이나 실제 농장 비용·추천의 승인이 아니다.
실제 금액 계산·불변 결과/조회는 후속 worker가 다시 현재 근거와 입력을 검사한 뒤 수행한다.
기존 schema3/경제 입력v1–v3·worker·API·UI는 유지한다.
새 HTTP/자동 소비와 UI는 worker/결과 수용 뒤 명시적으로 조립한다.

수용: 실제 SCRAM/등록 입력·서명 hold와 fresh server authority, 같은/동시 재시도,
충돌/rollback·현재/늦은 권한과 pointer 변경·누락/변조/기간/다른 tenant,
최초 bytes/시각·조회 및 접수의 ledger 계산/source 쓰기0·원 schema3/자료/GUI 보존.
사례는 자체 합성 QA이며 G0–G4 미평가·R2 미승인을 유지한다.
