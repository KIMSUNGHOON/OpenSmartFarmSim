# 원천 문맥에 맞는 저장 경제 후보 선택 v1

상태: 내부 읽기 제공자 계약, 2026-10-01. [원천 참조](source-farm-selection-v1.md)를
선택한 뒤 [농장 작성](farm-inputs-v1.md)의 경제 핀·기존 시장 보류·평가 달력을
저장 기록에서 찾는다. 원천 조회나 후보 선택은 새 숫자·보류·승인을 발급하지 않는다.

## 저장 목록과 현재 선택

`FarmEconomicCandidateService(source, economic)`는 실제 `SourceFarmSelectionService`와
`EconomicScenarioService`의 동일 authority JobStore·원천 등록부·서명 문맥 저장소를
요구한다. 시장 후보·원천·보류 저장소는 기존 경제 서비스의 실제 조립이다.

- `list(tenant, research_job_id, collection_job_id, limit=20,
  before_recorded_at=None, before_candidate_id=None)`는 현재 원천 선택을 검증하고,
  같은 계정·스냅샷·서명 문맥/해시·결정 시각/종류의 시장 보류에 연결된 경제 후보를
  `(recorded_at, candidate_id)` 역순으로 조회한다. 기본 20, 최대 50이며 두 커서는
  함께 제공한다. 경제 달력은 Asia/Seoul의 원천 첫날부터 마지막 포함일까지 덮어야
  한다. 기상 두 시간과 월별 경제 달력을 같은 길이로 강제하지 않는다.
- 목록은 저장 핀·시장 보류 참조·평가 달력·기록 시각만 포함한다.
  `verification=requires_current_selection`이며 현재 개별 숫자/권리의 승인 목록이
  아니다. 각 행에 전체 원장 재계산/권리 재조사를 반복하지 않는다. 연결된 저장
  시나리오/보류의 결정 시각·문맥을 SQL에서 필터하고 현재 원천을 반환 직전 다시
  확인한다. 없다면 빈 목록이며 새 경제 가정이나 보류를 만들지 않는다.
- `get(tenant, research_job_id, collection_job_id, candidate_id)`는 정확한 저장 후보를
  현재 `MarketScenarioService.validate_pinned`로 재검사한다. 불변 원문·입력 해시와
  baseline/공동 충격·현재 개별 이용/표시 권리, 시장 보류의 서명/현재 범위를 확인하고
  선택한 원천의 문맥과 경제 결정 시각/달력을 대사한다. 두 현재 검증 결과가 일치해야
  하며 원천·Scope·조립 포인터도 반환 직전에 다시 확인한다.

첫 농장 작성은 기존 계약대로 `historical-thermal-replay`, `ex_post_replay`만 지원한다.
없는/다른 소유자의 원천 또는 후보는 `None`; 미완료·혼합·다른 문맥·기간 밖·변조·
현재 근거 불일치는 고정 메시지의 `FarmEconomicCandidateHold`; Scope 철회는
`PermissionError`다. 원천 ID는 UUID 객체, 후보 ID는 소문자 SHA-256이다.

응답은 닫힌 불변 `FarmEconomicCandidatePage` 또는 `FarmEconomicSelection`이다.
현재 선택에는 원천 참조, 정확한 경제 `scenario_id/revision/sha256/candidate_id`,
기존 `unavailable(hold_report_id)`, 경제 평가 시작/끝 날짜가 있다.
`verification=requires_registration_recheck`이며 원천의 합성/보류/G0·G1 미수용 표시를
유지한다. 원본·권리 원문·서명·자격증명·원장/금액·수확량·계수는 반환하지 않는다.
사용자가 직접 작성한 시설/제어/재배 의도와 권리 선언을 포함한 실제 농장 등록은
기존 등록 제공자에서 모든 참조·숫자·달력을 다시 검증해야 한다.

읽기 Scope는 원천의 다섯 범위와 `market_source_read`, `market_candidate_read`,
`market_hold_context_read`다. 새 DB 역할·테이블·쓰기 권한·외부 source를 추가하지 않는다.
목록 성공으로 현재 후보나 작물 순위를 승인하지 않는다. 실제 제품 CLI·독립 해제·
전체 G1과 G0/G2/G3a/G3b/G4 수용은 후속이다.
