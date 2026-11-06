# 항목별 비용의 현재 무계산 결과 조회 — 2026-11-06

[서버 조회](../backend/app/economic_cost_query.py)와 [계약](../contracts/economic-cost-stored-result-query-v1.md)을 수용했다.
[기계 증거](artifacts/economic-cost-stored-result-query-20261106.json)는 [부모 worker](economic-cost-execution-worker-20261106.md)와 새 계약·실제 조회/보존/독립 검토 지문을 연결한다.
**서버 조회 라이브러리 수용이며 새 비용 HTTP/runtime/자동 소비·SDK/UI는 후속이다.**

## 구현과 실제 검증

CostResultHold/decode_stored_cost_result/EconomicCostResultQuery/StoredCostResult를 추가했다.
원 metadata·읽기 전용 SQL과 source read_scope를 재사용하고 typed 비용 decoder/현재 참조 binding을 적용한다.
정확 cost input/result family의 전체 trace/base_result·Cost.id별 line/groups/months, 원 재고/unknown null을 보존한다.
같은 canonical raw bytes와 첫 publication UUID/시각을 반환하며 읽기에 실행 권한은 필요하지 않다.
현재 권한·원 source/입력·지원 trace/model code와 불변 게시/파일을 전후 대사한다.
outer worker 코드/환경 SHA는 당시 실행의 provenance로 보존하고 현재 worker를 다시 실행하거나 당시 fingerprint를 현재 runtime으로 덮어쓰지 않는다.
금액 계산·worker 호출이나 SQL 쓰기 없이 파싱/결속만 수행한다. 원 batch Envelope/globals/model codec/default 의미를 유지한다.

- 신규37+기존77=**현재 고유114검사**를 최종 source에서 통과했다.
  기존77은 원 query29·보호 HTTP20·runtime12·consumer16이다. 별도 프로세스는 해당 실제 검사에 포함하며 중복 pytest로 더하지 않았다.
- 실제 소유 SCRAM의 같은 원문·최초 publication/재시도·반환 복사, 현재/늦은 권한·원 근거·코드,
  잘못된 family/metadata/hash/원 파일 변경·null/재고/엄격 decoder를 수용했다.
- 같은 프로세스와 독립 새 프로세스의 실제 원 raw/hash·최초 게시를 대사했고 금액 진입/SQL 쓰기0을 기록했다.
  새로운 결과를 계산해 조회 원문 대신 쓰지 않았다.
- 이전 worker425검사의 실제 terminal/proof와 수용 이력은 보존했다. 이번 현재 검사 합계에 그425를 다시 더하지 않았다.
  변경하지 않은 worker/금액 모델은 원 source/output SHA와 수용 Git snapshot으로 보존했다.

독립 검토 R1은 늦은 instance decoder lambda와 live hold/stored type 교체의 의미 있는 회귀 누락이었다.
전용 검사를 추가해 교체 함수를 호출하지 않고 원 binding 거부를 확인했다.
R2는 호출자 Decimal.capitals=0일 때 유효한 nested2E-9의 원 문자열을 잘못 hold하는 실제 decoder 결함이었다.
순수 RED의 실제 `1 failed, 36 deselected in 0.84s`와 결함 당시 코드를 보존하고,
새 decoder만 localcontext(trace._CONTEXT)로 격리해 canonical 표현과 호출자 문맥 복원을 확인했다.
원 숫자 공식·old batch codec/default·worker는 이 수정에서 바꾸지 않았다. 최초 module RED와 수정 전35 core는 보존하되 현재 합계에 더하지 않았다.

## 자원·보존·남은 범위

CLI0.166.0의 실제 gpt-6.1-sol/xhigh native child metadata로 판단·구현/시험·문서와 독립 검토를 대사했다.
부모 orchestration은 실제 ultra이며 정확 xhigh 판단 세션으로 표시하지 않는다.
독립 검토의 correctness/readability/architecture/security/performance 필수 미해결 지적은0이다.
재귀/외부 Codex CLI·새 DB/schema/역할·패키지/API/runtime/자동 소비/SDK/UI 추가는 없다.

별도16MiB buffer 소유 PG의 host SCRAM을 썼고 원 사용자 DSN/비밀번호는 읽지 않았다.
실제 회귀3묶음의 감독 시간/메모리는 final-core-v1 240.33073339401744초/PID 107712512B·합 292171776B；regression-query-http-v1 226.39072221098468초/PID 179982336B·합 336932864B；regression-runtime-consumer-v1 128.15962286107242초/PID 212897792B·합 392392704B다.
각600초/PID512MiB/보호·소유 합1GiB 한도와 source 보존·FD4→4·소유 잔여0·fixture PG 정지를 확인했다.
새 manifest는 부모 worker manifest와 새 계약을 SHA로 연결하고 기존25 통합 snapshot에 실제 추가 경로를 더한29개를 기록한다.
상속 source750의 기존 worker 예외와 과거6 worker pin은 원8f7606c3f99696d139961226829f21571348833e 그대로다.
공유 economic_batch_query.py만 이번에 추가로4edef92da8ebb7849ccde96a9d8f97e9c385b856의 원11,139B/SHA로 검증한다. 과거5 query pin도 같은 Git bytes로 대사하며 다른748 source는 현재 bytes로 확인한다.
과거 manifest/receipt/script·금액/입력/원 산출물은 바꾸지 않는다. 이전 worker425·제외된 원 query/HTTP-v1 이력도 덮어쓰지 않았다.

저장3D source687/출력4/private745/external46과 만료5184의238파일·5181의233파일/원 소유·만료 정책을 보존했다.
이번 preview HTTP는0이며 과거 실제238 HTTP 지문을 유지했다. 미리보기 재시작/수명 연장은 없다.
과거 raw 전체 재실행·전체 backend/frontend suite·새 UI/browser·사용자 DB 배포·새 비용 HTTP/runtime/자동 소비는 실행하지 않았다.
자체 합성 소프트웨어 계약이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.

## 다음 한 단계

`economic-cost-line-protected-http`: 기존 source/authority와 비용 접수·현재 조회를 별도 보호 경로/닫힌 DTO에 결속하고, 인증 tenant/현재 scopes·원 bytes/첫 publication header·no-store·크기/잘못된 query/late 변경/정상·hold 오류와 기존 batch 경로를 실제 SCRAM/HTTPS로 검증한다.
기존170줄 batch routes·55줄 wire/20 집중 HTTP 검사와 수용된 비용 접수·조회에 근거한1–2집중시간 초안(재작업/CI 대기 별도)이다. 명시 runtime 조립/자동 소비는 그다음 별도 수용이며 원 자원 창·독립 구매/청구 기간 결속→strict SDK/같은 선택3D 비용 UI는 후속이다.
상위 stored-execution과 실제 품종/한 작기·생산/구매·경제/거시/수급·자율 비교/최종 제품은 미완료다.
후속 연결 공수와 외부 현장/권리/검증/R2/배포의 전체 완료일은 미정이다.
