# 생산 batch 계산의 기존 자동 소비 v1

상태: [367집중·실제 SCRAM/별도 작업자/보호 TLS 수용](../research/economic-batch-automatic-consumer-20261031.md). 기존 deterministic discovery/foreground loop에
economic-batch-calculation-input-v1·정확한 EconomicBatchWorker/BatchCalculationOutcome만 추가한다.
기존 worker 계약/판본과 source7/schema3 경로는 유지한다.

loop는 batch worker의 _access로 원 객체/저장 root/현재 권한을 검사한다.
선택한 tenant와 simulation stage·현재 due/만료 lease·불변 입력의 정확 판본만 발견한다.
다른 종류/판본/tenant·완료 작업은 계산하지 않는다. 취소/hold/lease/reclaim·원자 게시와 현재 근거는 기존 worker가 담당한다.
unclosed 같은 미확정 결과를 성공 이벤트로 바꾸지 않고 기존 LoopHold/CLI 고정 오류로 종료한다.

worker는 HTTP 요청과 별도의 operator 조립/서비스 principal을 사용하며 현재 scope와 실제 SCRAM authority를 유지한다.
기존 python -m app.deterministic_work --factory 경로를 사용한다. Codex CLI를 재귀 실행하지 않는다.
새 큐/서비스 체계·DB/역할/숫자 계산·모델/관문은 만들거나 변경하지 않는다.

수용: 실제 HTTPS 접수→별도 작업 프로세스의 발견/1계산/원자 완료→fresh HTTPS 원 bytes/현재 권한,
페이지/다른 queued 작업/완료 뒤 재선택0·취소/현재 scope/늦은 객체·실제 만료 lease의 재임대와 기존 consumer/worker/API 회귀다.
입력은 자체 소유 합성 fixture이고 실제 농장/예측·추천/사용자 배포·비용 SDK/UI 수용은 별도다.
