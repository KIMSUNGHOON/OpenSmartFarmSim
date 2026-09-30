# 저장 원천 작업 이력 연결 검증

2026-09-30 내부 합성 소프트웨어 시험. [계약](../contracts/api-owned-source-history-v1.md)에 따라 PostgreSQL의 조사 입력·해시를 확인해 테넌트별 목록과 수집·검토 부모 연결을 조회한다. 선택 시 현재 등록 범위·원본·서명 문맥을 다시 확인하고, 현재 불가하면 이력만 보여 준다.

검증 명령과 범위:

| 명령 | 결과·범위 |
| --- | --- |
| `PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q tests/test_owned_source_history.py` (`backend/`) | 실제 로컬 PostgreSQL 16.15/SCRAM, 3건 통과. 테넌트 분리·목록 커서·권한 철회·저장 수집/검토 연결·잘못된 부모 해시 거부·미조립 API를 포함한다. CLI는 직접 작성한 가짜 실행기다. |
| `PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q tests/test_owned_source_history.py tests/test_owned_research.py tests/test_api_owned_collection.py` (`backend/`) | 주변 조사·수집 API 회귀 포함 26건 통과. |
| `PYTHONPATH=. .venv/bin/python -m app.api_openapi --check`; `PYTHONPATH=. OSSF_TEST_PG_DSN=... .venv/bin/pytest -q tests/test_api_openapi.py tests/test_owned_source_history.py` (`backend/`) | 추가 경로의 저장 OpenAPI 스냅샷 일치와 권한/응답 참조를 포함한 53건 통과. 첫 호스팅 스모크의 스냅샷 불일치를 확인해 [OpenAPI 계약](../contracts/openapi-v1.md)과 JSON을 갱신했다. |
| `npm run typecheck`; `npm run test -- --run src/api.test.ts` (`web/`) | TypeScript 통과; API DTO/경로 검증 25건 통과. |
| `OSSF_TEST_WEB_PORT=5187 npx --no-install playwright test e2e/shell.spec.ts --grep 'saved source jobs return after reload' --reporter=line` (`web/`) | Chromium 390px에서 토큰 재연결·새로고침 뒤 조사/수집/검토 이력 복구, 검토 보류 조회, 권한 철회 표시 1건 통과. |
| `npm run test`; `npm run build`; `OSSF_TEST_WEB_PORT=5187 npm run test:browser` (`web/`) | 웹 단위 77건, 정적 빌드, Chromium 28건 통과. Vite는 기존 그래프·3D 청크 크기 경고를 출력했다. |

이 시험은 실제 원천 G0 채택, 제품 Codex CLI `gpt-6-sol` `xhigh` 실행, 독립 G1 해제, 작물 추천, 공개 운영/G4를 증명하지 않는다. 현재 API는 선택한 조사에서 가장 최근 수집/검토 한 쌍만 보여 주며, 전체 작업 이력·다른 탭에서 접수 응답이 유실된 작업의 자동 재발견은 후속이다.
