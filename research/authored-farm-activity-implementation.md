# 작성 농장 검토·계산 작업 이력 후보

2026-09-30. [작성 농장 HTTP 계약](../contracts/api-farm-authoring-v1.md)의
`GET /v1/farm-authored-inputs/activity`는 같은 테넌트의 불변 등록 판본과
등록 해시를 먼저 확인한다. 기존 PostgreSQL 작업표에서 작성 검토와 작성
열 계산 입력 버전만 골라 원문 해시·입력 필드·농장 식별자/해시·계산 작업의
검토 작업 링크를 검사한다. 응답은 공개 `JobStatus`와 시간 커서만 포함한다.
작업 원문, CLI 프롬프트, 비밀, 임대 토큰, 제한된 출처 자료는 반환하지 않는다.

`04 작성 농장 실행`에서 판본을 열고 **작업 이력 보기**를 누르면 과거
검토/계산 작업을 페이지별로 볼 수 있다. 항목 선택은 현재 단건 농장 GET의
등록 해시와 실제 작업 상태 GET을 다시 확인한다. 계산 작업을 선택하면 그
작업의 검토 작업도 복원해 완료 Run의 3D 버튼을 사용할 수 있다. API의
Run 읽기는 기존 해제·권리·게시 근거 검사를 그대로 수행한다.

이력은 **과거 작업 메타데이터**다. 원천 권리 철회 후에도 소유 계정에
작업 기록이 보일 수 있으나, 다시 사용하거나 3D Run을 읽을 수 있다는
허가가 아니다. 검토 `succeeded`는 독립 서명 해제를 뜻하지 않고,
계산 `succeeded`도 이 목록만으로 G1 승인 증거가 되지 않는다.

검증은 PostgreSQL 16.15/SCRAM에 실제 등록 판본과 검사 가능한 검토
입력을 만든 뒤, 시험에서 직접 기록한 검토·계산 작업의 연결을 읽는
범위다. 운영 CLI·독립 해제·실제 계산 작업자의 신규 게시까지 이 시험이
수행하지는 않는다. Chromium 시험은 합성 API 응답으로 새로고침/재연결
후 이력 선택→저장 Run 재생 경로를 확인한다. 큰 테넌트의 작업표에서
JSON 조건 조회 지연과 인덱스 적합성은 아직 측정하지 않아 G4 hold다.

확인한 결과:

```text
backend/ OSSF_TEST_PG_DSN=<private disposable SCRAM DSN>
  uv run --locked --group dev python -m pytest -q --tb=short
  tests/test_api_farm_authoring.py tests/test_api_openapi.py
  53 passed in 286.44s

backend/ uv run --locked --group dev python -m app.api_openapi --check
  passed

web/ npm run typecheck && npm run test && npm run build
  typecheck passed; 75 passed / 8 files; build passed

web/ OSSF_TEST_WEB_PORT=5174 npx playwright test
  e2e/authored-workflow.spec.ts --grep 'saved authored jobs reopen'
  1 passed in 3.6s (390px 가로 넘침 없음 포함)
```

이 결과는 이력 조회와 합성 브라우저 복구의 소프트웨어 계약 증거다.
실제 제품 Codex CLI 실행·독립 서명 해제·현장/시장 자료 검증 또는 G1/G4
수용으로 해석하지 않는다.
