# 저장 원천 작업 이력 연결 검증

2026-09-30 내부 합성 소프트웨어 시험. [계약](../contracts/api-owned-source-history-v1.md)에 따라 PostgreSQL의 조사 입력·해시를 확인해 테넌트별 목록과 수집·검토 부모 연결을 조회한다. 선택 시 현재 등록 범위·원본·서명 문맥을 다시 확인하고, 현재 불가하면 이력만 보여 준다.

검증 명령과 범위:

| 명령 | 결과·범위 |
| --- | --- |
| `PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q tests/test_owned_source_history.py` (`backend/`) | 실제 로컬 PostgreSQL 16.15/SCRAM, 3건 통과. 테넌트 분리·목록 커서·권한 철회·저장 수집/검토 연결·이전 검토 재시도 2건과 페이지 커서·잘못된 부모 해시 거부·미조립 API를 포함한다. CLI는 직접 작성한 가짜 실행기다. |
| `PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q tests/test_api_openapi.py tests/test_owned_source_history.py tests/test_owned_research.py tests/test_api_owned_collection.py` (`backend/`) | 조사·수집 API 및 저장 OpenAPI 스냅샷·권한/응답 참조 회귀 77건 통과. |
| `PYTHONPATH=. .venv/bin/python -m app.api_openapi --check` (`backend/`) | 저장 OpenAPI 스냅샷과 추가 경로 일치. |
| `npm run typecheck`; `npm run test`; `npm run build` (`web/`) | TypeScript 통과, 웹 단위 78건, 정적 빌드 통과. Vite는 기존 그래프·3D 청크 크기 경고를 출력했다. |
| `OSSF_TEST_WEB_PORT=5187 npm run test:browser` (`web/`) | Chromium 28건 통과. 390px에서 토큰 재연결·새로고침 뒤 조사/수집/검토 복구, 이전 검토 시도 선택, 보류 조회, 권한 철회 표시를 포함한다. |

이 시험은 실제 원천 G0 채택, 제품 Codex CLI `gpt-6-sol` `xhigh` 실행, 독립 G1 해제, 작물 추천, 공개 운영/G4를 증명하지 않는다. 목록과 페이지는 저장된 과거 시도를 사용자가 다시 찾게 하지만, 다른 탭에서 접수 응답이 유실된 작업의 자동 재발견은 후속이다.
