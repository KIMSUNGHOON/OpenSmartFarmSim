# prefix 검증 모듈의 공개 provenance 연결 — v1 수정 계약

2026-10-08 KST. 작업 `crop-cycle-calculation-prefix-api-bridge`.
선행은 [prefix/최종 권한 경계](../research/crop-cycle-calculation-prefix-attestation-implementation-20261008.md)다.
판단은 기존 native Codex CLI `gpt-6.1-sol / xhigh`에서 수행하며 재귀 CLI를 실행하지 않는다.

## 관측한 결함과 우선순위

서버의 고정 `DEPENDENCY_SHA256`에는 새 `prefix` 모듈의 SHA가 추가됐지만
공개 API의 `CalculationServerDependencies`와 SDK의 닫힌 key 목록은 이를 받지 않는다.
기존 실제 수치 artifact의 summary/page 투영 시험을 실행해
1실패/62미선택·실제 종료1/정리로 재현했다. 내부 저장/조회208개 수용과 공개 투영 수용은 구분한다.
이 누락은 저장 결과→3D 경로의 의존성이므로 큰 계산 구간의 제품 구현보다 먼저 수정한다.

## 변경 경계

1. `backend/app/api_crop_cycle_calculation_replay.py`: 닫힌 dependency 모델에 `prefix: Digest` 필수 필드 추가.
2. `contracts/openapi-v1.json`: 실제 선언에서 다시 발행해 그 필수 필드를 반영.
3. `web/src/calculationCycleCropReplay.ts`: 정확한8개 dependency key와 SHA 형식 검사.
4. `web/src/calculationCycleCropReplay.test.ts`: 새 map의 수용과 prefix 누락/잘못된 SHA/추가 key 거부.
5. `web/src/calculationCycleCropWindow.test.ts`, `web/e2e/calculation-cycle-crop-replay.spec.ts`: 새 기록 JSON 경로.
6. `web/e2e/calculation-cycle-crop-prefix-recorded-responses.json`: 현재 실제 투영에서 새로 수집한 소유 JSON.
7. 이 계약. 필요하면 기존 backend 투영 반례를 같은 시험 모듈에 추가한다.

현재 실제 서버가 고정한 prefix SHA를 그대로 공개한다. 해시 필드를 제거하거나
추가 key를 일반적으로 허용하는 방식으로 통과시키지 않는다. 기존 원 기록 JSON은 그대로 보존한다.
새 기록은6개 소유 프로그램의 실제 수치 artifact/공개 투영으로 생성하고
기존 fixture의 수치/UTC·hold·사건·페이지를 대사한다. 옛 JSON에 해시 하나를 덧붙인 기록으로 대체하지 않는다.
두 fixture는 합성 공개 투영 시험 자료이며 실제 TLS wire/현장 자료나 승인된 production Run이 아니다.

## 수용 기준과 실행

1. backend 기존 실제 투영 반례와 SDK 새 map 반례의 RED 종료/로그/정리를 보존한다.
2. 수정 뒤 실제 summary/sample/event의 모든 값/UTC·검증 metadata를 보존한다.
   재해시한 잘못된 dependency·누락·알 수 없는 key를 거부하며 투영/SDK에서 RHS를 실행하지 않는다.
3. 새 소유34개 JSON의 prefix SHA가 현재 서버와 같고 원 fixture의 배열·시각·관리 사건/hold와 같아야 한다.
   source/키/계보 hash는 현재 실제 투영 판본으로 구분한다. 원 fixture SHA는 바뀌지 않아야 한다.
4. 집중 API 투영/route·OpenAPI snapshot을 검증하고 SDK/범위 선택·웹 전체 단위 시험·타입/빌드를 확인한다.
   새 기록을 사용하는 실제 Chromium의15개 장면/표·이전/취소/보류 검증을 통과해야 한다.
   브라우저 응답은 기록 합성이며 실제 PG/TLS native 수용과 구분한다.
5. nice19·한 소유 무거운 작업만 순서대로 실행한다. 기존 실제 fixture 수집116.570초에 근거해
   새 수집의 명령 관측 예산은300초다. 실제 종료·PID 시작 identity·source/원 파일·FD/cache·임시 경로/child 정리를 기록한다.
   관측 만료만으로 재시작하지 않는다. 테스트 중 고정한 source는 실제 종료/정리 감사 전 수정하지 않는다.

산출물은 새 현재 JSON/필수 schema/SDK와 소프트웨어 검증 보고서·불변 receipt다.
전체166일 등록 terminal/DB/API/같은 UTC3D와 최신 native의 원 종료 기록 누락 hold는 별도다.
실제 품종/국내 독립 자료/측정 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
