# 소유 생산 batch의 명시 서버 조립 v1

상태: [161집중·실제 SCRAM/보호 TLS 수용](../research/economic-batch-runtime-assembly-20261031.md). 기존 ApiRuntime에 선택한8종/schema4 source를 연결한다.
정확한 CLI/자료·관문 조건은 AGENTS.md와 PROJECT_SPEC을 따른다.

ApiRuntimeDependencies의 keyword-only economic_batch_source_factory는 기본 None이다.
None 또는 callable만 허용하며 config.policy.economic_batch_source_storage와 제공 여부가 같아야 한다.
불일치는 factory/DB/HTTP 기동 전에 거부한다.

새 기능을 선택하면 기존 market_source_factory는 정확한 MarketSourceStore를 계속 제공한다.
새 factory(principal_provider=current_principal)는 정확한 EconomicBatchSourceStore를 제공한다.
서버는 기존 JobStore/hold/context와 EconomicBatchAuthority를 조립하고 기존 create_app에 명시 주입한다.
동일 DSN/schema/정책/authority role/provider를 검사하며 실제 source/current 결속을 유지한다.
값이 같은 다른 객체로의 늦은 교체도 검증 경계를 통과하지 못한다.

새 authority는 runtime의 economic_batch_authority로 제공하고 미선택 시 None이다.
기존7종/schema3 경로/설정·OpenAPI 기본값과8종의 표/버전·읽기/쓰기 scope는 섞지 않는다.
startup 오류는 기존 고정 API runtime assembly rejected를 사용하고 비밀/원문을 노출하지 않는다.

수용: 실제 소유 SCRAM·두 source family의 등록/조회, 실제 보호 TLS 계산 접수→명시 worker→
새 runtime 객체의 원 bytes/최초 publication 조회·현재 권한/근거, 늦은 교체 거부와 기존 runtime/API 회귀다.
자동 소비·SDK/비용 UI/사용자 DB·키 이전/배포는 이 단계에 포함하지 않는다.
자체 합성 시험은 G0–G4/R2 또는 실제 생산/마진/추천 승인을 뜻하지 않는다.
