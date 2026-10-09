# 작성 농장 등록 판본 목록의 소프트웨어 검증

2026-09-30. [HTTP 계약](../contracts/api-farm-authoring-v1.md)에 테넌트별
`GET /v1/farm-authored-inputs/catalog`를 추가했다. 기존 불변 작업 입력의
버전·테넌트·식별자 키·원문 해시와 농장/수치/권리 해시를 검사해 등록 요약만
최신순으로 내보낸다. `(created_at, job_id)` 커서는 20개씩 읽는 화면과
1–50개를 허용하는 API에서 다음 페이지를 가리킨다. 다른 테넌트의 판본과
농장/권리 원문은 응답에 없다.

화면의 **저장된 판본 → 목록 보기**는 서버 목록을 읽고, 항목 선택 시 기존
단건 GET을 다시 호출해 정확한 등록 해시와 현재 자료·권리 연결을 확인한다.
목록은 과거 등록 메타데이터이므로 원천 권리가 철회돼도 과거 항목이 보일
수 있다. 이 경우 항목 선택은 보류되고 계산이나 3D 결과로 이어지지 않는다.
목록은 브라우저 저장소에 보존하지 않으며 연결 계정이 바뀌면 지운다.

검증 범위:

- 로컬 PostgreSQL 16.15/SCRAM의 인증 HTTP 시험은 두 판본의 최신순
  페이지 이동, 필수 읽기 권한, 다른 테넌트의 빈 목록, 잘못된 커서 거부와
  철회 뒤 단건 GET의 보류를 확인했다.
- 웹 타입 검사, 단위 시험 **74개**, 빌드가 통과했다. 목록 DTO의 닫힌
  필드·커서·제한과 예상치 못한 원문 필드 거부를 확인했다.
- Chromium 합성 응답 시험은 목록 선택 때 단건 GET의 422 보류와
  정상 해시 재확인, 390px 가로 넘침 없음으로 통과했다.

실행 결과:

```text
backend/ OSSF_TEST_PG_DSN=<private disposable SCRAM DSN>
  uv run --locked --group dev python -m pytest -q --tb=short
  tests/test_api_farm_authoring.py tests/test_api_openapi.py
  51 passed in 244.21s

web/ npm run typecheck                     passed
web/ npm run test                          74 passed / 8 files
web/ npm run build                         passed
web/ OSSF_TEST_WEB_PORT=5174 npx playwright test
  e2e/authored-workflow.spec.ts --grep 'saved farm catalog'
  1 passed in 2.1s
backend/ uv run --locked --group dev python -m app.api_openapi --check
  passed
```

로컬 DB는 PostgreSQL 16.15이고 비밀번호를 기록·출력하지 않았다. 위 HTTP
시험은 실제 저장소와 인증 문맥을 사용하지만 브라우저 시험 응답은 합성이다.

이 경로는 저장된 **농장 입력 판본** 목록이다. 후속
[검토·계산 작업 이력 후보](authored-farm-activity-implementation.md)가 추가됐으나
완료 Run 전체 목록은 아직 없다. 선행 조사·수집·경제 자료는 사용자가
식별자를 알아야 하고, 실제 제품 CLI·독립 해제·전체 G1/G4는 수용하지
않았다. 목록 표시나 합성 브라우저 시험은 농업 적합성·미래 마진·작물
순위의 근거가 아니다. 큰 테넌트의 작업표에서 목록 질의의 지연과 인덱스
적합성은 측정하지 않았으므로 G4 성능 증거도 아니다.
