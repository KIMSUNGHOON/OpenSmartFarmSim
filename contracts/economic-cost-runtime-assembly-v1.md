# 조건부 항목별 비용의 명시 runtime 조립 v1

상태: 수용. [실제 SCRAM/보호 HTTPS의 신규1·기존12검사와 원 증거](../research/economic-cost-runtime-assembly-20261106.md)로 [보호 비용 HTTP](economic-cost-protected-http-v1.md)의 기존 runtime 연결을 생산 코드 변경0으로 증명했다.

기존 ApiRuntime의 economic_batch_source_factory와 economic_batch_source_storage 정책을 그대로 사용한다.
서버는 실제 EconomicBatchSourceStore·JobStore/hold/context와 current_principal로 EconomicBatchAuthority를 조립하고
기존 create_app에 주입한다. 이미 설치되는 비용 접수/현재 결과 두 경로를 사용하며 새 runtime 필드·factory·flag·역할·schema를 추가하지 않는다.
기존 기본/7종 source와 선택8종 source의 경계 및 오류를 유지한다.

첫 ApiRuntime과 인증서 검증 TLS 리스너에서 참조-only 비용 POST/재시도를 수행한다.
원 queued job ID·입력 bytes/SHA·최초 생성 시각과 비용 input version을 보존하며, 이 HTTP 접수에서는 금액을 계산하지 않는다.
명시 실행 전 attempt_count0/미게시와 결과404를 확인한다.
첫 소유 리스너를 종료한 뒤 별도 소유 fixture의 operator authority로 수용된 EconomicCostWorker를 명시 호출한다.
한 번 trace/원 v10 계산의 전체 결과·trace_id와 원 입력/게시를 대사한다. runtime에 worker나 queue loop를 설치하지 않는다.

같은 시험 OS 프로세스에서 동일 소유 DB·artifact root/키/설정으로 ApiRuntime을 새로 조립하고 두 번째 TLS 리스너를 시작한다.
jobs/authority/source/holds/context는 첫 조립과 다른 객체이고 동일 current_principal 계약을 사용한다.
read-only/no-execute token의 결과 조회는 원 저장 bytes·최초 publication ID/시각·no-store/보호 header를 그대로 반환한다.
그 조회 동안 금액/line/group/month/reconciliation·worker·runtime digest 호출과 SQL 쓰기는0이다.
현재 signed scope/근거를 무효화하면 economic_cost_hold422로 원문을 숨기고, 복구하면 같은 원문/최초 게시를 다시 반환한다.
미인증 조회401·read token의 접수403과 요청 밖 current_principal 비어 있음을 확인한다.

두 TLS 리스너의 thread 종료·fixture 인증서/키 제거와 소유 PG 정지·FD/보호 source 보존을 실제 감독 기록으로 확인한다.
원 immutable input/생성 시각·publication은 재조립/재조회 뒤에도 바꾸지 않는다.
원 시험 결과와 별도 receipt는 두 runtime/리스너와 같은 프로세스 재조립을 명시한다.
소유 PG를 유지한 runtime/listener 재조립 범위이며 cold OS 프로세스/DB 재기동 증거는 후속이다.

수용은 신규1개 실제 비용 runtime 증명과 기존12개 batch runtime 검사 및 같은 고정 source/원 증거 대사다.
부모 HTTP308/조회114/worker425는 보존 증거로 유지하며 이번 실행 합계에 다시 더하지 않는다.
생산 코드·수치 모델·입력/원 산출물·과거 manifest/receipt와 배포 기반은 그대로 보존한다.

자동 비용 소비는 현재 exact worker/discovery 등록에서 지원하지 않는 별도 다음 단계다.
원 자원 창/독립 비용·구매/청구 기간 결속·SDK/UI와 실제 사용자 배포도 후속이다.
자체 합성 QA이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 제품 목표 미완료를 유지한다.
