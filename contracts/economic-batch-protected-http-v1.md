# 소유 생산 batch의 보호 HTTP v1

상태: [149집중·실제 SCRAM/보호 TLS 수용](../research/economic-batch-protected-http-20261031.md). source 저장/계산 접수·worker·현재 조회를 제품 경로에 연결하는 첫 단계다.
create_app에 실제 EconomicBatchAuthority를 명시 주입한 경우에만 새 경로를 설치한다.
그 authority는 같은 JobStore/hold/context·principal provider를 사용해야 한다.
기존7종/schema3/default 경로·운영 설정/DB는 유지한다. runtime/자동 소비·SDK/UI는 후속이다.

| 경로 | 동작과 권한 |
|---|---|
| POST /v1/economic-batch-sources | 200.8종 typed 사용자 가정 등록. metadata/economic_batch_source_read/economic_batch_source_write |
| GET /v1/economic-batch-sources | kind·limit≤50·원 cursor 쌍의 목록. metadata/economic_batch_source_read |
| GET /v1/economic-batch-sources/record | kind·record_id·revision의 원 등록 조회. 같은 읽기 scope |
| POST /v1/economic-batch-calculations | 202. 원 schema4 참조/지문의 불변 계산 의도 접수. 원 READ_SCOPES+simulation_execute |
| GET /v1/jobs/{job_id}/economic-batch-result | 원 JSON bytes·최초 publication header. READ_SCOPES+artifact, 실행 scope 불요 |

인증 tenant는 서버 provider로 결정하며 body/query/header의 tenant를 채택하지 않는다.
source 요청은 kind/input/idempotency_key이고 input의 tenant_id는 거부한다.
원 kind/model/version·canonical job bytes/최초 기록·재시도/충돌/rollback 검사를 공유한다.
같은 authority의 source/hold/context 결속을 저장 거래 안에서도 검사하고 늦은 교체 시 작업과 입력을 함께 되돌린다.
새 family/scope/모델을 class 설정으로 선택하고 기존 기본값은 그대로 둔다.

source 전체 요청은64KiB, 계산 요청은4KiB까지다. embedded source canonical bytes도 기존64KiB 한도를 따른다.
JSON content type/중복 key/비유한 JSON·추가/누락/다른 schema·잘못된 cursor를 고정 오류로 거부한다.
등록/접수는 금액 계산·worker 실행·관문 승격을 하지 않는다.
저장 결과는 원2MiB 한도·현재 권한/입력/근거를 재검증한 뒤 같은 bytes를 반환한다.
원 Decimal 문자열/null/재고 배열을 닫힌 실제 wire schema로 문서화한다.

경로와 OpenAPI는 인증/필요 scope·body/결과 한도와 고정 오류를 명시한다.
현재/늦은 권한/객체 변경·자료 손실/hold는 반환을 차단한다.
unknown/미완료 결과는404, 인증401/scope403, 충돌409, 큰 요청413,
content type415, 입력/근거422, 서버 결속/일시 불가503을 사용한다.
결과 header는 최초 publication ID/시각이고 no-store·기존 서비스의 보안 header를 유지한다.

수용: 실제 owned SCRAM의8종 등록/목록/조회·job 결속/재시도/충돌/rollback,
HTTP 접수→명시 worker→현재 GET 원 bytes/읽기 권한·계산/SQL쓰기0,
실제 보호 TLS·tenant/만료/late·요청/응답 schema·기존7종/default/API 회귀와 자료/GUI/WSL 보존이다.
이는 자체 합성 소프트웨어 수용이며 G0–G4/R2·작물/구매/마진/추천 승인은 아니다.
