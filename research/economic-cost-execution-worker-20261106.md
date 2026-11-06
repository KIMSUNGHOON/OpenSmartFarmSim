# 항목별 비용 worker·불변 원자 게시 — 2026-11-06

[실행 worker](../backend/app/economic_cost_worker.py)와 [계약](../contracts/economic-cost-execution-worker-v1.md)을 수용했다.
[기계 증거](artifacts/economic-cost-execution-worker-20261106.json)는 부모 접수 manifest와 실제 검사·게시·보존·독립 검토 지문을 결속한다.
**서버 실행 라이브러리 수용이며 새 결과의 현재 무계산 조회·HTTP/runtime/자동 소비·SDK/UI는 후속이다.**

## 구현과 집중 검증

EconomicCostWorker는 기존 EconomicBatchWorker의 lease/CAS/SQL 원자 게시 엔진을 공유한다.
고정 selector·작은 참조/직렬화/ID hook 세 개의 identity를 불변 NamedTuple로 캡처하고 전후 대사한다.
정확 economic-cost-line-calculation-input-v1만 선택해 trace 한 번과 원 v10 한 번을 계산했다.
전체 base_result·Cost.id별 line/groups/months를 별도 economic-cost-line-calculation-result-v1에 보존하며
성공 CostCalculationOutcome은 trace_id를 반환한다. 원 v10/default version·outcome/reason·SQL과 전체 envelope2MiB 한도를 유지한다.

- 신규25/기존400=**고유425검사**를 최종 source에서 통과했다. 먼저 기록한 RED/core는 더하지 않았다.
  서로 겹치지 않는 묶음은 새 worker25·기존 접수/경제299·원 worker24·query29·HTTP20·runtime12·consumer16다.
- 실제 소유 SCRAM의 전체 원문·입력/source UUID·코드/환경/result SHA·최초 게시/재시도와 동시 단일 게시를 검증했다.
  별도 Decimal300 대사와 원 v10 canonical bytes SHA는 실제 publication proof에 남겼다.
- 다른 family/원 v10 선택0, 현재/늦은 권한·근거·코드/환경/selector, 취소·lease 만료/재임대,
  크기 hold·저장 실패·SQL/publication drift rollback과 기존 worker/query/gateway 관련 회귀를 수용했다.
  축소 한도 fault 주입을 실제2MiB 경계 크기 생성 시험으로 표시하지 않는다.

## 실제 자원·보존과 한계

판단·구현/시험·문서는 CLI0.166.0의 실제 gpt-6.1-sol/xhigh native child metadata로 대사했다.
부모 orchestration은 실제 ultra이며 정확 xhigh 판단 세션으로 표시하지 않는다.
독립 native child가 correctness/readability/architecture/security/performance를 검토했고 필수 미해결 지적은0이다.
재귀/외부 Codex CLI·새 DB/schema/역할/패키지/API/runtime/자동 소비/SDK/UI 추가는 없다.

기존 환경과 별도16MiB buffer 소유 PG의 host SCRAM을 썼고 원 사용자 DSN/비밀번호는 읽지 않았다.
서로 겹치지 않는 회귀4묶음의 실제 감독 시간/메모리는 regression-worker-v1 397.03001420618966초/PID 146608128B·합 245514240B；regression-query-http-v2 237.74112883000635초/PID 180174848B·합 338571264B；regression-runtime-consumer-v1 132.82483219495043초/PID 171634688B·합 389070848B；regression-core-v1 181.34754345193505초/PID 146313216B·합 299708416B다.
각600초/PID512MiB/보호·소유 합1GiB 한도 안에서 source 보존·FD4→4·소유 잔여0과 fixture PG 정지를 확인했다.

원 query/HTTP-v1은49 pytest와 fixture controller가 통과했지만 도구 연결/감독이 사라져 완전한 원 terminal이 없으므로 수용 합계에서 제외했다.
복구 기록은 원 runner/PG 종료·임시 디렉터리 제거·소유 잔여0·같은25 source를 확인했다. 원 terminal/RSS·전체 source 감독 증거를 재구성하지 않았다.
원 작업이 끝난 뒤 재실행한 query/HTTP-v2만 위 합계에 포함했으며 두49를 중복 합산하지 않았다.

새 manifest는 부모 접수 manifest와 새 계약만 SHA로 연결하고 기존22 통합 snapshot에 새3개를 더한25개를 기록한다.
부모가 상속한 source750 중 공유 worker 경로 하나만 수용 Git commit 8f7606c3f99696d139961226829f21571348833e의 원 SHA로 검증한다.
같은 경로를 고정한 과거6 manifest도 그 원 Git bytes로 대사하며 다른749 source는 현재 bytes로 검증한다.
이 예외는 이번 새 보존 증거에만 명시했고 과거 manifest/receipt/script/숫자/산출물은 바꾸지 않았다.
원 숫자 모델·입력/산출물과 저장3D source687/출력4/private745/external46을 보존했다.
만료5184의238파일·5181의233파일/원 소유·만료 정책과 과거 실제 HTTP 지문을 보존했다.
이번 preview HTTP는0이며 과거238 HTTP 검증과 구분한다. 미리보기 재시작·수명 연장은 없다.

과거 raw 전체 재실행·전체 backend/frontend suite·새 UI/browser·사용자 DB 배포는 실행하지 않았다.
대상 SCRAM 회귀는 새 현재 조회/HTTP/runtime/자동 소비의 수용이 아니다.
자체 합성 QA이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.

## 다음 한 단계

`economic-cost-line-stored-result-query`: 전체 trace/base_result·line/groups/months의 엄격 decoder와 현재 원 참조/권한/지원 코드, 원 canonical bytes/첫 게시 시각·다른 family/변조/늦은 변경·새 프로세스 읽기, 금액 호출·SQL 쓰기0을 수용한다.
기존201줄 batch query/29검사와 새 중첩 trace decoder·현재 참조 결속을 근거로1–2집중시간 초안(재작업/CI 대기 별도)이다. 새 HTTP/runtime/자동 소비와 원 자원 창·독립 구매/청구 기간 결속→strict SDK/같은 선택3D 비용 UI는 후속이다.
상위 stored-execution과 실제 품종/한 작기·생산/구매·경제/거시/수급·자율 비교 및 최종 제품은 미완료다.
후속 연결 공수와 외부 자료/현장/권리/R2/배포의 전체 완료일은 미정이다.
