# 검증 계산 결과의 인증 조회 API — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행 [별도 운영 설정 로더](crop-cycle-calculation-operator-loader-v1.md)의 로컬 수용 뒤,
새 공개 투영과 현재 query를 실제 API/동일 UTC3D에 연결한다.
아래 수용 절은 route/OpenAPI 자식만의 로컬 소프트웨어 수용이며 실제 runtime/TLS는 후속이다.

## 요청·권한·응답

`GET /v1/crop-cycle-calculation-research-results/{result_id}`를 별도 경로로 둔다.
ID는 `crop-cycle-verified-result-v1:<64 lowercase hex>`이며 필수 farm query는
`scenario_id/scenario_revision/registration_sha256/crop_id`다.
`view=summary|samples|events`, canonical ASCII 정수 offset/limit와 상한64/8·빈 마지막 page는
[원 cycle API 계약](api-crop-cycle-pages-v1.md)의 의미를 따른다. summary에는 offset/limit가 없고
중복·알 수 없는 query, body, 구형 ID와 임의 계산 입력은422다.

기존 `READ_SCOPES`와 principal/tenant 검사 후 exact 새 store/query·same jobs/farm을 사용한다.
활성 경로는 `CalculationCurrentCycleQuery.open` 한 번에서 원 record/terminal/page를 얻고,
`project_calculation_cycle_result` 및 `_public_bytes`로 닫힌 새 응답을 만든다.
문맥이 닫힐 때 투영 후 현재 권리·DB/부모 서명·원 bytes를 재검사하며 그 완료 전 응답을 반환하지 않는다.
threadpool 뒤 현재 인증/tenant도 다시 검사한다. 구형 store 읽기나 원 parser/context/QC/RHS 재실행으로
우회하지 않는다. QC·결과 증명 발급은 요청 밖의 준비 단계다.

응답은 기존 수용된 `crop-cycle-calculation-replay-v1`과 원량/UTC/validation provenance를 보존한다.
`Cache-Control: no-store`와 새 query version/code SHA header를 확인한다.
전체 본문은 기존30초/2MiB 이하이며 페이지를 모으거나 HTTP 한도를 늘리지 않는다.
인증401/권한403/없음404/요청·작물 근거 보류422/기본 비활성·운영 오류503은 기존 의미를 따른다.
`RolePolicyHold`는503이며 민감한 파일 경로·원본 payload/서명·키·사유 원문은 응답에 없다.
수치 hold의 확인 과거와 빈 결과를 보존하며 생과 kg·미래 수확·관문 승격을 만들지 않는다.

## 작은 구현 순서와 수용 기준

1. **인증 route/OpenAPI 자식** — 새 `backend/app/api_crop_cycle_calculation_route.py`,
   `backend/app/api.py`, `backend/tests/test_api_crop_cycle_calculation_route.py`,
   `backend/tests/test_api_openapi.py`, `contracts/openapi-v1.json`의5 core파일.
   기본 비활성·엄격한 요청/인증/오류·exact store/query 결속·한 문맥·투영 뒤 철회·원량/UTC/hold를
   ASGI로 확인한다. 기존 route 선언/공개 형식은 그대로이고 기계 snapshot에는 새 경로와 schema만 추가한다.
   세 별도 Python import 순서에서 새 계산/store/query를 미리 불러오지 않고 FD가 같아야 한다.
   이 자식의 stubbed custody 시험은 실제 DB/TLS 수용과 구분한다.
2. **runtime/실제 TLS 자식** — `backend/app/api_runtime.py`,
   `backend/tests/test_crop_cycle_calculation_runtime.py`,
   새 `backend/tests/test_api_crop_cycle_calculation_tls.py`의3 core파일.
   설정 로더에서 조립한 exact 새 store/query를 `create_app`에 전달한다. 현 단계까지 api_runtime.py를
   보존한75 source 중 이 파일의 변경은 이 자식의 명시 범위이며 이전 SHA/증거는 보존한다.
   실제 소유 SCRAM·보호 설정/TLS·서버/클라이언트의 전체 본문으로 정상·관리 사건·확인 과거 hold·빈 hold,
   순차 samples/events·재기동·현재 철회·다른 tenant/권한·운영 grant 변경/변조·기본 비활성을 대사한다.
   parser/context/QC/RHS/advance/put을 금지한 읽기에서 각 응답30초/2MiB, 비밀 비노출과
   FD·thread/socket·schema/role/passfile·PG PID/data·임시 tree 정리를 기록한다.

두 자식 모두 실제 명령·종료·source/로그 SHA와 기존 route/runtime 회귀를 확인한 뒤 API 부모를 수용한다.
다음 client/표/그래프/3D는 새 ID/manifest·동일 UTC를 선택하며 실제 PG/TLS/WebGL로 검증한다.
전체166일 등록 prefix/복원 비용과 실제 품종/독립 자료·G0–G4는 별도 의존성이다.

## 일정 근거

선행 로더1–2집중시간 잠정은 실제 수용으로 대체했다. 기존 route/TLS 시험과 정확한 전체 OpenAPI 목록을
대조하면 새 route/OpenAPI5파일과 runtime/TLS3파일의 두 검증 단위가 남는다.
route/요청·ASGI·snapshot2–3집중시간 + 실제 설정 조립·SCRAM/TLS·회귀2–3집중시간의
**남은 작은 API 연결4–6집중시간 잠정**으로 갱신한다. 이전 route/TLS1–2시간은 이 분해로 대체한다.
실제 TLS 응답 실패가 있으면 원 한도 안의 원인 수정과 재검증을 추가한다.
CI 대기·전체166일/3D·생과/자원/경제·외부 자료 확보와 최종 제품 완료일은 포함하지 않는다.

## route/OpenAPI 자식 로컬 수용 — 2026-10-07

새 경로63개/8.77초와 경로/OpenAPI/runtime·설정 회귀221개/127.87초,
**고유284개 분할 검증**으로1번 자식만 수용한다. 그 회귀에는 새 OpenAPI operation의 권한 사례도 포함된다.
원 API의 AST는 새 import·기본 None인 두 읽기 인자·installer 호출을 제외하면 같다.
기존48 path/148 schema와 나머지 선언은 같고 새 path1개/schema8개만 추가됐다.
원 계산/저장/조회·loader/runtime·시험78 source SHA는 보존했다.
실제 자작 수치 artifact의 원량/UTC·정상/관리 사건·확인 과거 hold60걸음/1시점/1사건·빈 hold와
한 query 문맥·bytes 뒤 권리 철회/인증/tenant·고정 오류·strict query·세 별도 import/FD를 ASGI로 검증했다.
route 시험의 farm/DB custody는 격리한 exact 타입 stub이다. 기존 회귀의 실제 SCRAM 조립과
새 route의 실제 SCRAM/TLS를 혼동하지 않는다. 새 TLS 응답/브라우저 실행은0이다.
[수용 기록](../research/crop-cycle-calculation-route-openapi-20261007.md)에 명령/source/로그/정리를 둔다.
위 route2–3시간 잠정은 이 실적으로 대체한다. 다음2번 runtime/TLS3 core파일2–3집중시간 잠정이며
실제 HTTP30초/2MiB·철회/정리 수용 전에는 API/transport 부모를 체크하지 않는다.
