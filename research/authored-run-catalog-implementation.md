# 작성 Run 저장 목록 API 검증

2026-09-30 내부 합성 소프트웨어 범위. [계약](../contracts/api-authored-thermal-run-v1.md)에 따라
`GET /v1/authored-runs/catalog`이 같은 테넌트의 불변 작성 Run 저장 행에서
Run ID·계산 작업 ID·기록 시각만 역순으로 읽는다. 각 항목의
`requires_current_read`는 목록이 현재 표시 승인이나 G1 해제를 뜻하지 않음을 나타낸다.
선택한 Run의 실제 표시 가능 여부는 기존 정확한 Run 조회가 현재 자료 권리,
서명 해제, 입력·영수증·게시·trace 해시를 다시 검사한다.

검증: `backend/`에서
`PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q
tests/test_farm_authored_run_store.py tests/test_api_authored_runtime.py
tests/test_api_openapi.py`를 실행해 **56 passed in 35.27s**를 확인했다.
실제 로컬 PostgreSQL 16.15/SCRAM과 HTTPS Bearer에서 소유/타인/권한 없는 목록,
불완전한 커서, 저장 행 조회, 오래된 해제에 대한 정확한 Run 조회 보류를 확인했다.
`PYTHONPATH=. .venv/bin/python -m app.api_openapi --write`와 `--check`로
저장 OpenAPI 스냅샷도 재생성·대조했다.
저장소 결합 검사 실패를 안전하게 보류하도록 보완한 뒤 같은 PostgreSQL에서
`tests/test_farm_authored_run_store.py` **3건**을 다시 통과했다.

저장 목록은 브라우저 화면에 아직 연결되지 않았다. 이 시험은 가짜 CLI와
합성 검토자/서명 근거를 사용하며, 실제 Codex CLI `gpt-6-sol`/`xhigh`,
독립 G1 해제, 농업 정확도나 G0/G2/G3/G4를 증명하지 않는다.
