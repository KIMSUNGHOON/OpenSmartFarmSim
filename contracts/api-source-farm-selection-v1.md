# 원천에서 농장 입력 참조 조회 API v1

상태: 내부 소프트웨어 후보, 2026-10-01. [참조 제공자 계약](source-farm-selection-v1.md)을
기존 인증 API에 조립한다. 조사/수집을 자동 선택하거나 새 자료를 발급하지 않는다.

`GET /v1/source-history/{research_job_id}/collections/{collection_job_id}/farm-input-references`
는 같은 계정이 선택한 정확한 완료 조사·수집에서 이미 저장된 원천 스냅샷과 서명
문맥의 참조를 반환한다. 두 경로 값은 UUID다. 닫힌 `SourceFarmSelection` 응답과
오류/필수 범위는 [OpenAPI](openapi-v1.json)에 고정한다.

Bearer 인증과 `metadata`, `artifact`, `collection_read`, `thermal_snapshot_read`,
`decision_context_read`가 필요하다. 인증 없음은 401, 범위 없음/철회는 403,
없는/다른 소유자의 작업 또는 잘못된 단계는 404, 잘못된 입력·현재 근거 불일치·
미완료/혼합 부모·저장 스냅샷 없음은 422 보류다. 실제 소유 조사/수집 조립이 없거나
백엔드 장애이면 503이다. 오류는 기존 닫힌 `ErrorEnvelope`와 고정 메시지이며
원본/자격증명·내부 예외를 노출하지 않는다. 표준 HTTPS 응답은 `no-store`다.

`create_app`은 기존 실제 `OwnedResearchService`와 `CollectionService`가 함께
제공되면 같은 JobStore·등록부의 제공자를 조립한다. 표준 `ApiRuntime`도 이 기존
조립을 사용한다. 새 factory·DB 역할·테이블·별도 저장소나 쓰기 범위를 추가하지 않는다.
기존 30초 클라이언트 제한 아래 실제 TLS/Bearer/SCRAM 응답 전체를 확인한다.

참조 선택은 `software_fixture_only`, `hold`, `not_accepted`를 유지하며 실제
농장 등록 때 재검사가 필요하다. 시장 보류/경제 후보 선택과 농장 웹 연결,
실제 제품 CLI·독립 해제·전체 G1/G4 수용은 후속이다.
