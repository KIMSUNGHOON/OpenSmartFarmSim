# 원천별 저장 경제 후보 조회 API v1

상태: 내부 인증 읽기 계약, 2026-10-01. [제공자 계약](farm-economic-candidate-selection-v1.md)의
목록과 현재 선택을 표준 HTTPS API에 연결한다. 농장 작성 전에 기존 식별자·달력을
찾는 경로이며 새 숫자, 시장 보류, 입력 등록이나 관문 승인을 만들지 않는다.

## 두 조회

- `GET /v1/source-history/{research_job_id}/collections/{collection_job_id}/economic-candidates`
  (`listSourceEconomicCandidates`)는 `FarmEconomicCandidatePage`를 반환한다.
  `limit`은 기본 20, 범위 1–50이다. 다음 페이지는 응답의 정확한 UTC
  `before_recorded_at`과 소문자 SHA-256 `before_candidate_id`를 함께 사용한다.
  한쪽 커서, 시간대 없는/UTC가 아닌 시각, 범위 밖 limit은 422다.
- 같은 경로의 `/{candidate_id}` (`getSourceEconomicCandidate`)는 현재 입력/권리와
  선택 원천을 다시 검증한 `FarmEconomicSelection`을 반환한다. 목록의
  `requires_current_selection`은 단건 성공을 보장하지 않는다. 선택도
  `requires_registration_recheck`이며 실제 농장 접수는 모든 근거를 재검사한다.

두 작업 ID는 UUID이며 후보 ID는 정확한 소문자 SHA-256이다. 서버 조립은 기존
`OwnedResearchService`·`CollectionService`·`EconomicScenarioService`의 같은
authority JobStore와 서명 문맥을 사용한다. 이 중 하나가 없으면 503이며 독립된
source, 새 저장소, owner DB 역할이나 새 runtime factory를 생성하지 않는다.

## 인증·오류·표시

필수 Bearer Scope는 `metadata`, `artifact`, `collection_read`,
`thermal_snapshot_read`, `decision_context_read`, `market_source_read`,
`market_candidate_read`, `market_hold_context_read`다. 모든 읽기 전에 검사하며
인증되지 않으면 401, 한 범위라도 없거나 늦게 철회되면 403이다. 다른 계정 또는
없는 원천/후보는 404다. 현재 권리·문맥·기간의 불일치는 422 보류이며 내부 오류는
503이다. 모든 실패는 기존 닫힌 `ErrorEnvelope`와 고정 공개 메시지만 반환한다.

응답과 오류는 기존 `Cache-Control: no-store`를 따른다. 원문·서명·권리 원문·
계수·금액·작물 수치·비밀을 노출하지 않는다. 정확한 `SourceFarmSelection`의
합성/보류/G0·G1 미수용 표시를 유지한다. 기존 합성 CLI/시험키로 계약을 확인할 수
있지만 실제 제품 CLI, 독립 해제 및 G1/G4 수용의 증거는 아니다.

수용은 닫힌 OpenAPI 및 인증 선행 검사, 실제 SCRAM 저장의 소유권/페이지/현재
권리 재검사, 표준 HTTPS/Bearer 조립과 30초 제한 안의 전체 응답, 쓰기 권한 없이
저장 행 수 불변을 포함한다. 증거가 존재한 뒤 구현 작업 체크를 갱신한다.
