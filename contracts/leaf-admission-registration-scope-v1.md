# Leaf 입력 확인·접수의 등록 읽기 범위 — 후보 v1

상태: **소프트웨어160검사·새 판본의 기존 결과/입력 HTTPS 수용, 사용자 적용/동시 retry/새 자동3D 전**.
[증거·남은 범위](../research/leaf-admission-registration-scope-20261023.md)를 확인한다.
[기존 보호 HTTP](api-crop-leaf-population-execution-v1.md),
[현재 조회 범위](leaf-population-query-registration-scope-v1.md)와
[다음 작업](../tasks/plan.md#현재-저장-job-ui-수용-뒤의-접수-단계--2026-10-23)을 따른다.

원 API의 첫 접수는30초를 초과했다. 별도 scratch DB의 같은 첫 POST 한 번을 관측했고,
등록 재구성64회/SQL33,022회를 확인했다. profiler가 있는 서버 작업은38.854초에 queued로 끝났다.
HTTP 요청은30초에 종료했고 재요청하지 않았다. 이 진단은 정상 시간 수용 시험이 아니다.

## 호출 경계

- HTTP의 인증·Scope·활성 graph·JSON/필드 검증 순서를 보존한다.
  검증된 body의 farm 참조는 아직 승인 입력이 아니다. 실제 등록의 현재 검사에 전달하는 참조다.
- 접수 callback이 실행되는 같은 작업 thread 안에서 admission의 기존 parent/farm graph가 가리키는
  FarmAuthoringService의 `registration_read_scope`를 연다. 본문에서 받은 tenant/서비스를 사용하지 않는다.
- 범위가 이미 있으면 중첩하지 않고 helper의 actor/ref·문맥 검증을 유지한다.
  다른 ref/손상된 범위를 별도 원 경로로 우회하지 않는다.
- 원 `admission.submit`의 권한·resolver·prepare·서명 입력·멱등성·commit_guard를 모두 실행한다.
  SQL 커밋 검증까지 같은 범위에 포함한다. 현재 원천/권한·원 행은 반복 대사하며 재구성만 재사용한다.
- owned `/leaf-preview-input`도 검증된 고정 config의 farm 참조로 같은 범위를 사용한다.
  원 prepare/current와 최종 인증·오류/응답 제한은 유지한다.
- 정상·거부·예외마다 소유 범위를 닫는다. 요청 사이 cache/TTL이나 새 전역 기본값을 추가하지 않는다.

접수 core의 CODE_SHA256과 서명 authority/model 소스는 바꾸지 않는다. 기존 intent/publication/result와
원 query가 재조회 가능한 별도 불변 source 판본을 유지한다. HTTP 코드 지문은 실제 변경에 따라 갱신된다.
기존 경로/스키마·Scope/오류 본문·30초/2MiB와 수치/단위·최초 시각은 바꾸지 않는다.

## 수용

1. 실제 SCRAM/인증서 검증 HTTPS 첫202·동일 retry202/같은 job·409가 원30초 안에 응답한다.
   매 요청의 재구성1회와 원64개 현재 등록/각76개 원천 조회를 구분해 대사한다.
2. commit_guard 직전 원천/초과 권한/인증 만료를 독립 변경해 새 job/events의 rollback을 확인한다.
   실제 원복 뒤 같은 원 작업을 정상 조회/재요청하고 scope/소유 연결 잔류0을 확인한다.
3. 기존 HTTP/권한·query의 정상/늦은 변경/취소와 owned 입력/기본 모드·실제 실행 회귀를 통과한다.
   새 source에서도 기존 저장 결과와 원 계산/parent 식별자·최초 시각을 읽을 수 있어야 한다.
4. 같은 원 입력의 실제 worker 계산 중 동일 POST도30초 내 같은 job을 반환하고 최종 attempt1/원 결과가 된다.
5. 현재 SDK의 입력 확인→한 접수→자동 완료3D·메뉴/reload·실제 철회/원복을 수동 복구 없이 확인한다.
   원 자료·DB/키/이전 URL과 WSL 상한·소유 정리를 보존한다.

각 항목의 실제 증거가 생긴 범위만 체크한다. 정상 단일 POST가 빠르다는 관측을 동시 retry/자동3D나
전체 runtime·G0–G4·실제 품종·생산/자원/경제·추천 수용으로 확장하지 않는다.
