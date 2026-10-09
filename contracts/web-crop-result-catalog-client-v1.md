# 저장 작물 연구 결과 목록 웹 SDK v1

상위 U1의 SDK 자식이다. 선행은 [보호 API](api-crop-result-catalog-v1.md)의 로컬 수용이다.
핵심5파일: 이 계약, `web/src/cropResultCatalog.ts`, `web/src/cropResultCatalog.test.ts`,
`web/src/api.ts`, `web/e2e/crop-result-catalog-recorded-responses.json`.
원 HTTPS body를 기록하는 기존 수동 native harness와 검증 보고서/영수증은 지원 파일이다.

## 계약과 다음 한 단계의 수용 기준

- 기존 `createApi` request의 동일 origin/Bearer·no-store·redirect 거부·AbortSignal을 사용한다.
  한 호출은 GET1회이며 자동 페이지 이동/재시도·prefetch·계산/게시를 하지 않는다.
  30초·64KiB를 유지한다. 이미 취소된 호출은 전송하지 않고 늦은 응답도 취소로 거부한다.
- 닫힌 `{kind,farm,limit?,before?}`를 검사한다. 두 kind, farm4필드, limit1–20/기본10,
  UTC6자리 소수·kind별 원 ID cursor를 받는다. 호출 시 요청을 복사해 응답 전의 외부 변경과 분리한다.
- 응답의 version/scope/kind/farm·두 판본의 항목 전체·개수/상태/claim scope·불리언을 검사한다.
  알 수 없는 필드, 다른 판본/농장/등록/작물, 비정수 개수, 잘못된 ID/UTC/period를 거부한다.
  생장/수확 DTO는 서버의 각 개수 상한을 유지한다.
- 정규 UTC 저장 시각 문자열 전체와 ID를 비교해 DESC/중복·요청 cursor 경계를 검사한다.
  JS Date의 밀리초로 cursor를 줄이지 않는다. period의 소수 초도 정확히 비교한다.
  next_cursor는 null 또는 가득 찬 페이지의 마지막 항목과 같아야 한다.
  빈 페이지는 성공이며 전체 결과 개수를 추정하지 않는다.
- 응답을 복사해 반환한다. 원 요청/transport 객체·반환 객체의 변경이 다음 검사의 기준을 바꾸지 않는다.
  목록은 `stored_research_metadata_only`, `selection_validation_required=true`,
  `rights_or_gate_approval=false`이며 선택한 결과의 기존 query/API 재검사를 대신하지 않는다.
- 별도 소유 DB/실제 TLS·Bearer의 완료 body를 원 bytes로 기록하고 SHA/길이를 SDK fixture와 대사한다.
  원 body의 임의 편집/재구성을 실제 HTTP로 표시하지 않는다. 거부/빈/미세 UTC 경계 변형은 소프트웨어 fixture다.
  원 생산/입력/서명·계산 중인 full producer와 사용자 preview는 보존하고 소유 PG/HTTPS/FD를 정리한다.
- 집중 시험·기존 소비자를 포함한 전체 웹·typecheck/build와 원 종료/소유 자원 증거를 확인한다.
  SDK만 수용하며 U1/화면·실시간 진행·일반 운영 용량·제품 CLI·실제 작물/관문은 완료하지 않는다.

다음은 기존 작성 농장 목록에서 같은 crop의 결과 선택을 기존 생장3D/수확 조회로 전달하는 화면이다.
12ui-design과 기존 화면의 접근성/취소·늦은 응답 계약을 적용하고 실제 DB/API/브라우저로 별도 수용한다.
