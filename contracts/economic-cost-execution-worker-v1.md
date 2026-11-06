# 조건부 항목별 비용 worker v1

상태: [425개 집중 검사·실제 SCRAM 수용](../research/economic-cost-execution-worker-20261106.md). [불변 참조 접수](economic-cost-calculation-admission-v1.md)의 다음 실행 단계다.

`EconomicCostWorker`는 기존 실제 EconomicBatchAuthority/JobStore를 사용한다.
기존 EconomicBatchWorker의 lease·취소·내용 주소 저장·원자 게시 트랜잭션을 공유한다.
고정된 concrete worker만 프로그램을 정하며 요청이 worker/금액 공식/코드/결과 종류를 고르지 않는다.
새 worker는 정확 `economic-cost-line-calculation-input-v1`만 claim한다. 원 v10/다른 family·다른 tenant와 유효한 다른 lease는 소비하지 않는다.

입력의 원 base_input/source UUID·근거와 고정 trace/코드·성분을 현재 참조에 대사한 뒤
CostLineLedger를 한 번 호출한다. 커널이 원 v10을 한 번 계산하며 원 전체 base_result·Cost.id별 결과를 보존한다.
artifact는 별도 `economic-cost-line-calculation-result-v1`이고 원 input 전체/SHA·tenant/job/attempt,
실행 코드/환경 SHA·전체 trace와 원 canonical result SHA를 포함한다.
새 CostCalculationOutcome의 성공 ID는 trace_id이며 기존 BatchCalculationOutcome/ledger ID와 구분한다.

고정 input version/type·참조 서비스·계산기·artifact/outcome·사유 prefix·코드 파일 목록과
작은 참조·직렬화·ID 함수의 identity를 생성 시 불변으로 캡처하고 현재 선택자/함수와 전후 대사한다.
실행과 실패 응답은 이 캡처를 사용하므로 늦은 선택자 교체가 작업 family/실패 사유를 바꾸지 않는다.
원 scope/authority/root·입력/근거/코드/환경, 현재 lease/취소와 게시 후 metadata를 확인한다.
전체 envelope2MiB를 넘으면 게시하지 않으며 자르거나 근사하지 않는다.
실패·늦은 철회/변경·게시 트랜잭션 오류는 성공/event/publication을 롤백한다.
만료/취소·재임대와 동시/재호출은 원 lease/최초 게시를 보존한다. 미게시 CAS bytes는 성공 결과가 아니다.

원 v10의 constructor·input/artifact version·outcome/reason·숫자 계산/결과 형식은 유지한다.
공유 orchestration 파일의 이전 수용 bytes는 수용 commit `8f7606c3f99696d139961226829f21571348833e`의
`backend/app/economic_batch_worker.py` Git snapshot으로 검증하며 기존 manifest/receipt를 고치지 않는다.
새 보존 증거에서 부모 source750과 그 상속 이력의 이 파일만 명시적으로 Git snapshot으로 검증한다.
숫자 모델/입력·원 산출물은 그대로 보존한다. 새 DB schema/역할·패키지·HTTP/자동 소비·UI를 추가하지 않는다.

수용: 실제 소유 SCRAM의 한 번 계산/전체 원문·독립 Decimal300 대사, 최초 게시/동시·재시도,
다른 family/현재·늦은 권한/근거·코드/환경·선택자, 취소/만료/재임대/2MiB/rollback과
기존 worker/query/API/runtime/자동 소비의 관련 회귀 및 원 자료/화면·WSL 보존이다.
새 결과의 현재 무계산 조회→보호 HTTP/runtime/자동 소비→자원 창/비용 기간·SDK/UI 연결은 후속이다.
자체 합성 가정/G0–G4 미평가/R2 미승인이며 실제 수확·구매·미래 이익/최적 작물 승인이 아니다.
