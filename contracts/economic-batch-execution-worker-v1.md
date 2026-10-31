# 소유 생산 batch 계산 worker v1

상태: [실제 worker/결과 수용](../research/economic-batch-execution-worker-20261031.md).
[구현](../backend/app/economic_batch_worker.py)은 [등록 입력의 접수](economic-batch-calculation-admission-v1.md)를 따른다.
기존 JobStore·실제 EconomicBatchAuthority·schema4/원장v10을 재사용한다.
새 DB 표/역할·기존 worker/API/UI의 변경은 포함하지 않는다.

worker는 정확한 tenant/job UUID·simulation stage·지원 input_version을 현재 확인하고
그 작업만 실제 lease로 claim한다. 다른 종류/완료 작업과 유효한 다른 실행자의 lease를 소비하지 않는다.
metadata/artifact/simulation_execute와 원 참조 읽기 scope가 필요하다.
원 입력 bytes/SHA·최초 source UUID·근거 SHA를 다시 대사한 뒤 원 v10을 계산한다.
계산 전후 실제 객체/현재 권한·원 입력/근거와 코드/잠금 환경 지문을 확인한다.

결과 artifact는 고정 `economic-batch-calculation-result-v1` JSON이다.
tenant/job/attempt·원 input SHA/모든 접수 pin·코드/환경 SHA와
원 Decimal 결과 전체 및 그 canonical bytes SHA를 담는다.
2MiB envelope 한도를 넘으면 보류하며 금액을 자르거나 근사하지 않는다.
같은 결과의 수확/판매 사건을 생성하지 않고 G0–G4/R2 상태를 올리지 않는다.

내용 주소 파일을 durable 저장한 뒤 같은 DB 거래에서 live lease/cancel·원 입력과 근거를 대사하고
결과 publication/manifest·succeeded/outcome을 원자 게시한다.
마지막 기록 뒤에도 현재 권한·코드/환경·근거와 정확한 terminal row를 검사한다.
중간 실패는 DB 게시/성공을 rollback하고 소유 lease 범위에서 고정 hold/실패 사유로 닫는다.
파일만 남은 경우는 미게시 내용 주소 bytes이며 결과 성공으로 조회하지 않는다.
기존/공유 파일을 실패 정리 과정에서 삭제하지 않는다.

재호출/동시 실행은 성공 결과를 덮어쓰거나 금액을 다시 계산하지 않는다.
취소는 소유 live lease로 acknowledge하며 만료/소유권 상실 때 게시하지 않는다.
외부 호출 예외 메시지·입력/비밀값을 사유나 manifest에 넣지 않는다.

수용: 실제 SCRAM·등록/서명 입력에서 claim→v10→원 bytes/지문/publication/terminal,
독립 Decimal 대조·동시/재호출·취소/만료·현재/늦은 scope/pointer·입력/근거/코드/환경 변경,
DB 기록 fault rollback·기존 자료/worker/GUI·원 첫 만료/WSL 보존이다.
fresh 현재 조회의 계산/SQL쓰기0과 보호 HTTP/runtime/자동 소비·SDK/화면은 후속 수용이다.
