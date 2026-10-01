# 수집 기록에서 농장 원천 참조 선택 v1

상태: 내부 제공자 계약, 2026-10-01. [지역 사용자 흐름](../docs/PROJECT_SPEC.md)에서
저장 조사·수집을 [농장 입력](farm-inputs-v1.md)에 연결하는 첫 선행 단계다.
기존 [원천 작업 이력](api-owned-source-history-v1.md)의 공개 응답은 유지한다.

## 읽기 계약

`SourceFarmSelectionService(research, collection).get(tenant, research_job_id,
collection_job_id)`는 실제 같은 authority JobStore·등록부의 소유 조사와 수집을
선택한다. 두 ID는 canonical UUID 객체다. 없는/다른 소유자의 작업 또는 다른 단계의
ID는 `None`, 미완료·서로 다른 부모·현재 근거 불일치는 고정 메시지의
`SourceFarmSelectionHold`, 읽기 범위 철회는 `PermissionError`다.

선택한 조사는 `historical-thermal-replay` 목표의 완료된 소유 조사여야 한다.
실제 보관 입력·입력 해시와 현재 등록 좌표/UTC 기간/목표/서명 문맥을 대사하고,
수집의 완료 영수증·원문 해시·조사 시도/결정/입력/출력 해시와 부모를 확인한다.
현재 고정 manifest와 수집된 원래 날씨·열 매개변수 바이트에서 계산한 스냅샷이
**이미 저장**되어 있어야 한다. 저장된 세 바이트·해시, 동일 스냅샷의 서명 문맥과
결정 시각/모드/실제 또는 가상 시각 종류를 다시 검사한다.

응답 `SourceFarmSelection`은 닫힌 불변 `owned-source-farm-selection-v1`이다.
조사/수집의 정확한 부모·시도·결정·입력/출력 해시, 등록 좌표/기간/목표,
원천 provider/registry/bundle 해시, 스냅샷 ID와 원본 세 해시, 서명 문맥 ID·해시·
결정 시각/모드/종류를 반환한다. 원본·키·서명·CLI 캡처와 농업/경제 숫자는 없다.
원천·서명 문맥을 반환 직전에 다시 읽고, 포인터·권한도 최종 확인한다.

필수 범위는 `metadata`, `artifact`, `collection_read`, `thermal_snapshot_read`,
`decision_context_read`다. 조회는 작업·스냅샷·시장 보류·경제 가정을 등록하지 않는다.
스냅샷이 없으면 기존 명시적 수집 검토 접수 경로가 먼저 필요하다.

`claim_scope=software_fixture_only`, `assessment_status=hold`,
`g0_status=g1_status=not_accepted`, `requires_registration_recheck=true`를 항상
반환한다. 선택은 등록 입력의 참조 후보이며, 실제 농장 등록에서 모든 참조를
다시 검증해야 한다. 완료 수집이나 읽기 성공으로 G0/G1·현장·작물/마진 예측을
승인하지 않는다. 합성 CLI/서명의 시험은 이 소프트웨어 계약만 검증한다.

## 후속 연결

인증 HTTP 조립·OpenAPI와 같은 문맥의 기존 시장 보류/경제 후보 선택을 별도 단계로
연결한다. 그 뒤 웹에서 저장 기록을 선택해 기존 농장 작성·검토·Run·경제·평가·3D로
잇는다. 필수 수치는 출처가 있는 명시적 사용자 가정으로 남으며 자동 계수·요금·
작물 생산량은 제공하지 않는다. 실제 제품 CLI·독립 해제·전체 G1은 별도 수용이다.
