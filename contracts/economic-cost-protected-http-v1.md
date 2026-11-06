# 조건부 항목별 비용 보호 HTTP v1

상태: [신규30/기존278=308개 집중 검사·실제 SCRAM/보호 HTTPS 수용](../research/economic-cost-protected-http-20261106.md). [불변 비용 접수](economic-cost-calculation-admission-v1.md)와
[현재 무계산 조회](economic-cost-stored-result-query-v1.md)를 기존 인증 API에 연결한다.

기존 `create_app(..., economic_batch_authority=authority)`에 실제 EconomicBatchAuthority를 제공할 때만
`POST /v1/economic-cost-calculations`와 `GET /v1/jobs/{job_id}/economic-cost-result`를 추가한다.
기존 source8 등록/조회 경로를 재사용하며 비용 source 경로·DB/schema/역할·새 설정 flag는 만들지 않는다.
authority를 제공하지 않은 기본 경로/OpenAPI와 원 batch/source 동작은 유지한다.

POST는 기존 닫힌 EconomicBatchCalculationRequest의 scenario ID/revision/SHA·ASCII idempotency key만 받는다.
application/json·UTF-8·4096 bytes 경계, 중복 JSON key/비유한 상수/추가 필드와 모든 query parameter를 거부한다.
기존 read scopes와 simulation_execute를 요구하고 EconomicCostCalculationService의 불변 접수를 사용한다.
성공은 `202 JobStatus`이며 계산 완료·trace 생성이나 작물/경제 승인이 아니다.
동일 요청의 최초 입력/생성 시각·작업 ID와 기존 비용 idempotency namespace를 보존하며 다른 입력은409다.
tenant·자료/프로그램 지문·source UUID·금액/공식을 요청에서 지정하지 못한다.

GET은 canonical job UUID만 받으며 다른/중복 query parameter를 거부한다.
기존 read/artifact scopes를 요구하고 simulation_execute 없이 EconomicCostResultQuery를 사용한다.
현재 표시 가능한 정확 cost family의 저장 원문 전체를 그대로 반환한다.
응답은 `CostArtifactRead`의 닫힌 schema이며 trace/base_result·Cost/그룹/월별·inventory/null과 Decimal 문자열을 보존한다.
artifact/trace version·ID/code/component digest·scope/G0–G4/R2/currency를 제한하고 전체 envelope 한도는2097152 bytes다.
성공 응답은 `Cache-Control: no-store`, 원 `X-OSSF-Publication-ID`와 `X-OSSF-Published-At`을 포함한다.
과거 outer worker/environment 지문·최초 publication/원 bytes를 오늘 실행 지문이나 새 직렬화로 바꾸지 않는다.

HTTP 경계는 현재 인증 tenant/scopes, 원 authority/source/holds/context/jobs/provider·artifact root/content와
서비스/reader 객체 및 지원 trace 프로그램을 실행 전후 확인한다.
비용 HTTP 접수의 작은 고정 wrapper는 원 서비스의 _prepare를 감싸 같은 확인을 기존 commit_guard 안에서도 수행한다.
commit 전의 늦은 tenant/권한·객체/root/프로그램 변경은 intent/event 거래를 rollback하며202를 반환하지 않는다.
commit 이후 응답 직전의 변경도 성공 본문/저장 원문을 숨긴다. 이미 commit한 불변 intent를 삭제하거나
그 이후의 실패가 과거 commit을 rollback했다고 표시하지 않으며 동일 키 재시도로 원 intent를 확인한다.
소유 worker 실행/queue 등록·runtime 조립/자동 소비는 이 HTTP 단계에서 추가하지 않는다.

원 계산/result HTTP의 공통 handler만 공유하고 source handler와 원 batch 프로그램/오류는 유지한다.
Cost wire는 기존 lossless 변환 helper로 새 type을 만들며 원 BatchArtifactRead/숫자 모델/schema를 바꾸지 않는다.
접수와 결과 HTTP에서 비용/원장 금액 계산·재생은0이며 GET의 SQL 쓰기도0이다.

오류는 기존 ErrorEnvelope를 사용한다. 인증401·scope/tenant403·없는/미완료/다른 family404·입력 충돌409,
본문 초과413·media415·JSON/closed schema/query/path422·현재 경제 근거/코드 보류422와 서버 결속/가용성503을 구분한다.
비용 근거 보류는 `economic_cost_hold`, 서버 결속/가용성 실패는 `economic_cost_unavailable`이며
외부 예외/원문·비밀값을 오류 본문에 넣지 않는다.

수용: 실제 소유 SCRAM·인증 HTTPS의 source8→불변 비용 접수/최초 재시도→명시 worker→현재 원문 HTTP,
새 프로세스/현재 인증·권한·근거·코드와 늦은 commit/응답 결속 변경, 닫힌 transport/OpenAPI/Decimal schema,
접수 금액 계산0·GET 금액/SQL쓰기0과 원 batch/default/source 경로·숫자/기존 증거 보존이다.
runtime/자동 소비·원 자원 창/독립 비용·구매/청구 기간 결속·SDK/UI는 후속이다.
자체 합성 QA이며 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 제품 목표 미완료를 유지한다.
