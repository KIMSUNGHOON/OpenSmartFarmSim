# 항목별 비용 보호 HTTP — 2026-11-06

[비용 HTTP](../backend/app/api_economic_cost.py)와 [닫힌 wire](../backend/app/economic_cost_wire.py), [계약](../contracts/economic-cost-protected-http-v1.md)을 수용했다.
[기계 증거](artifacts/economic-cost-protected-http-20261106.json)는 [부모 현재 조회](economic-cost-stored-result-query-20261106.md)와 실제 transport/보존/독립 검토 지문을 연결한다.
**보호 HTTP 수용이며 새 비용 명시 runtime/자동 소비·SDK/UI와 사용자 배포는 후속이다.**

## 구현과 실제 검증

기존 실제 economic_batch_authority를 제공할 때만 POST /v1/economic-cost-calculations와
GET /v1/jobs/{job_id}/economic-cost-result를 설치한다. 기존 source8과 같은 실제 저장소/권한을 사용한다.
POST는 원 닫힌 scenario 참조 요청과 불변 비용 접수를 재사용하며202는 queued intent다.
별도 명시 worker 실행 뒤 GET은 현재 조회의 전체 trace/base_result·Cost/그룹/월별·재고/null/Decimal 문자열과 원 bytes를 그대로 반환한다.
읽기에는 실행 scope가 필요하지 않으며 no-store·원 첫 publication UUID/시각을 유지한다.
CostArtifactRead는 실제 원문과 같은 닫힌 schema이고 기존 BatchArtifactRead/default schema·원 숫자 모델을 보존한다.
본문4096B/응답2097152B·JSON/media/query/path와 현재/늦은 tenant/scopes·source/hold/context/provider/root·서비스/코드 결속을 검사한다.
commit 전 변경은 원 intent/event 거래를 rollback하고, commit 뒤 응답 경계 변경은 본문을 숨긴다.
뒤늦은 응답 거부를 이미 기록된 원 intent의 rollback으로 표시하지 않는다.

- 신규30+기존278=**현재 고유308검사**를 최종 source에서 통과했다.
  원 batch HTTP20·경제 runtime12·consumer16와
  기본 OpenAPI101·인증33·원 source 등록21/조회35·기본 runtime40를 포함한다.
  실제 수집된 module별 개수/고유 node ID와 통과 수·실제 pytest argv를 대사했고 반복 RED/core는 더하지 않았다.
- 실제 소유 SCRAM의 source8→불변 접수/최초 재시도→명시 trace/원 v10 각1회→원 결과 HTTP를 검증했다.
  접수 금액 계산0·GET 금액/SQL쓰기0과 현재 근거 hold/복원·오류/비밀 제거·현재/늦은 권한/결속·원 batch/default 경로를 수용했다.
  응답 크기 회귀는64B 축소 fault로 확인했으며 실제2MiB load는 실행하지 않았다.
- 실제 인증서 검증 HTTPS에서 원 bytes/첫 publication/no-store와 현재 근거의422/복원, 다른 tenant·query/만료 인증을 확인했다.
  이 증거의 worker는 명시 실행이며 자동 소비 완료로 보고하지 않는다.
- 부모 조회114/worker425의 실제 proof/terminal과 수용 이력은 보존했다. 이번 현재 합계에 그 수를 다시 더하지 않았다.

검토 R1의 실제 `1 failed, 29 deselected in 6.96s`에서 live callback을 no-op으로 바꾸자503 뒤에도
원 job/event가27/27→28/28로 늘어나는 precommit 결함을 확인했다. 결함 당시 원 코드를 보존하고
새 비용 wrapper가 원 callback을 별도로 캡처해 identity를 확인한 뒤 그 함수만 호출하도록 수정했다.
전용 precommit 검사는 원 거래 rollback을, postcommit 검사는 이미 기록된 intent를 삭제하지 않고 응답만 숨긴 뒤
같은 키의 최초 intent를 되찾는 의미를 대사했다. 초기 transport/JSON-context 시험 수정은4KiB/엄격 schema를 유지했으며,
초기 부분 실패·RED를 현재 합계에 더하지 않았다.

## 자원·보존과 한계

CLI0.166.0의 실제 gpt-6.1-sol/xhigh native child metadata로 판단·구현/시험·문서와 독립 검토를 대사했다.
부모 orchestration은 실제 ultra이며 정확 xhigh 판단 세션으로 표시하지 않는다.
독립 correctness/readability/architecture/security/performance 검토의 필수 미해결 지적은0이다.
재귀/외부 Codex CLI·새 DB/schema/역할/flag·패키지·runtime/자동 소비/SDK/UI 추가는 없다.

별도16MiB buffer 소유 PG의 host SCRAM을 썼고 원 사용자 DSN/비밀번호는 읽지 않았다.
실제 회귀5묶음의 감독 시간/메모리는 final-core-v2 238.40727647882886초/PID 228122624B·합 364138496B；regression-batch-gateway-v1 183.50136493099853초/PID 224079872B·합 408526848B；regression-default-contracts-v1 250.70708433212712초/PID 193257472B·합 383823872B；regression-source-runtime-v1 67.24744715890847초/PID 177201152B·합 437796864B；regression-source-read-v1 49.61260640388355초/PID 183250944B·합 293818368B다.
각600초/PID512MiB/보호·소유 합1GiB 한도와 source 보존·FD4→4·소유 잔여0·fixture PG 정지를 확인했다.
새 manifest는 부모 query manifest/새 계약 두 개를 SHA로 연결하고 기존29 통합 snapshot에 새3개를 더한32개를 기록한다.
이번 기존 통합 경로 변경은 backend/app/api.py, backend/app/api_economic_batch.py다. 이 경로의 이전 bytes는 각 수용 Git snapshot으로 보존하고 현재 회귀를 별도로 확인한다.
strict source750의 worker8f7606c3f99696d139961226829f21571348833e/query4edef92da8ebb7849ccde96a9d8f97e9c385b856 예외 두 개는 그대로다.
과거6 worker/5 query pin과 다른748 현재 source·원 숫자 모델/입력/산출물·manifest/receipt/script를 보존했다. 새 strict-source 예외는 없다.

저장3D source687/출력4/private745/external46과 만료5184의238파일·5181의233파일/원 소유·만료 정책을 보존했다.
이번 preview HTTP는0이며 과거 실제238 HTTP 지문을 유지했다. 새 검증 HTTPS는 별도 소유 임시 API다.
과거 raw 전체 재실행·전체 backend/frontend suite·새 UI/browser·사용자 DB 배포·새 비용 runtime/자동 소비는 실행하지 않았다.
자체 합성 소프트웨어 계약이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.

## 다음 한 단계

`economic-cost-line-runtime-assembly`: production 변경0의 기존 ApiRuntime/authority 조립을 재사용하는 집중 통합1사례에서 실제 HTTPS 비용 접수·명시 worker·새 runtime/service 재조립의 원 bytes/첫 publication·읽기 권한/현재 hold·복원·금액/SQL쓰기0·소유 정리를 검증한다.
기존655줄 ApiRuntime과186줄 runtime 검사모듈의 fixture/TLS·재조립 사례 및12개 회귀 증거를 재사용하고 production 변경0·새 통합1사례로 한정한0.5–1집중시간 초안(재작업/CI 대기 별도)이다. 기존12 runtime 회귀 증거는 보존하고 새 비용 runtime 수용으로 아직 표시하지 않는다.
`economic-cost-line-automatic-consumer`는 그다음 별도 수용이며 그 공수는 실제 runtime 수용 뒤 산정한다.
원 자원 창/독립 구매·청구 기간 결속→strict SDK/같은 선택3D 비용 UI와 실제 품종/한 작기·생산/구매·경제/거시/수급·자율 비교는 후속이다.
상위 stored-execution/전체 제품은 미완료이며 외부 현장/권리/검증/R2/배포의 전체 완료일은 미정이다.
