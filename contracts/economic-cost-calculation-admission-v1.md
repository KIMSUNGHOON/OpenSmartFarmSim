# 조건부 항목별 비용 계산 접수 v1

상태: [23신규/276기존=299·실제 SCRAM 수용](../research/economic-cost-calculation-admission-20261106.md). [비용 커널](economic-cost-line-trace-v1.md)의 저장 실행을 위한 첫 참조 접수다.

`EconomicCostCalculationService`는 기존 실제 `EconomicBatchAuthority`만 받는다.
요청은 기존 `EconomicBatchCalculationRequest`의 scenario ID/revision/SHA·idempotency key뿐이다.
tenant·저장소·모델/코드 지문·source UUID·근거 SHA를 사용자가 지정할 수 없다.
원 source8/schema4의 준비 경계를 재사용하며 접수에서 금액을 계산하지 않는다.

새 `economic-cost-line-calculation-input-v1`은 원 `EconomicBatchCalculationInput` 전체를
`base_input`으로 보존하고 `trace_version`, `code_sha256`, `component_sha256`를 서버가 결속한다.
기존 v10 작업과 다른 idempotency namespace를 쓰며 같은 키/입력의 재시도는 최초 작업·원 bytes/시각을 반환한다.
같은 키/다른 입력은 충돌이다. 새 DB schema·로그인·의존성을 추가하지 않는다.

현재/commit 전 실제 authority의 읽기4scope와 `simulation_execute`, 같은 원 source/hold/context,
지원 trace/숫자 코드/성분 지문을 확인한다. 권한·참조·authority 교체나 코드 변경이면 접수/게시 없이 보류한다.
JobStore의 기존 원자 삽입/이벤트/commit_guard를 사용해 실패 시 새 job/event를 롤백한다.
읽기 전용 참조 준비는 실행 권한을 요구하지 않고, 제출은 실행 권한도 요구한다.

수용: 실제 소유 SCRAM에서 순차/동시 재시도·최초 원문/시각·한글/충돌·잘못된 참조/tenant,
현재/늦은 scope·근거/authority·코드 변경/롤백, 접수 금액 계산·다른 작업 소비0,
기존 source/v10/API·저장 자료/버전/화면/WSL 자원 보존을 확인한다.
후속 worker/불변 결과·무계산 조회·HTTP/runtime/자동 소비·SDK/비용 UI는 이 접수 수용에 포함하지 않는다.
자체 합성 가정이며 실제 농장 자료/요금·수확·이익 예측·추천이나 G0–G4/R2 승인이 아니다.
