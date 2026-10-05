# Cycle 연구 결과의 불변 저장 참조 — v1

상태: **schema만 로컬 소프트웨어 수용**, 2026-10-05 KST. 작업 `crop-cycle-storage-schema`.
[실제 SCRAM·수용/제한](../research/crop-cycle-storage-schema-implementation.md),
[CLI·코드/초안·시험/정리 영수증](../research/artifacts/crop-cycle-storage-schema-reference-20261005.json)을 확인한다.
[제품 범위/관문](../docs/PROJECT_SPEC.md), [저장/worker 경계](../docs/ARCHITECTURE.md),
[POSIX 객체/DB metadata stack](../docs/TECH_STACK.md),
[수용된 계산 결과 파일](crop-cycle-artifact-v1.md)을 따른다.
현재 Codex CLI `gpt-6.1-sol / xhigh`로 설계/검토하며 같은 세션 안에서 CLI를 재귀 실행하지 않는다.

## 이번 산출물과 다음 단계

3파일은 `backend/app/crop_cycle_result_schema.py`,
`backend/tests/test_crop_cycle_result_schema.py`, 이 계약이다.
provisioner가 명시적으로 새 `crop_cycle_research_results` 표/불변 trigger를 설치한다.
기존 startup v3와 실제 적분/artifact/reader/API의 hash/의미를 보존한다.
새 dependency·서비스·queue나 자동 schema/role 갱신은 선행이 아니다.

이번 표는 최대512MiB POSIX 결과를 기존20MiB startup row에 넣지 않고 **불변 metadata/내용 주소
참조**를 둔다. 파일 실재/완전성·원 계산/등록·현재 farm/source/program 권리·HMAC/서버 코드의
검사는 후속 custody의 책임이다. schema에 직접 만든 행은 농장 결과/승인 Run/자료 채택이 아니다.
기본 runtime 네 role의 새 접근은 모두 거부하며, 다음 명시 role/config 단계가 별도 권한을 검증한다.
이후 custody → API/client → 같은 UTC 성장 연구3D → 작기 부하 → 생과/자원/경제 순서다.

## 표와 metadata

- `tenant_id/study_id/revision`이 primary key이고 `tenant_id/result_id`가 유일하다.
  식별자·scenario/revision·registered_by는1..200자, result ID는 `crop-cycle-result-v1:<sha256>`이다.
- tenant 포함 `registration_job_id`가 기존 jobs 외래키이며 registration SHA/scenario 참조를 보존한다.
  FK는 같은 tenant의 job 존재만 증명한다. job 종류/실제 farm/현재 권리는 custody가 대사한다.
- 원 input root, artifact root/header SHA를 각각 보존한다.
  `artifact_ref`는 정확히 `crop-cycle-artifact-v1:<artifact_sha256>`다. 디렉터리/사용자 경로가 아니다.
  실제 해석은 후속 서버의 private POSIX 저장 범위에서 한다.
- terminal 상태는 completed/hold다. steps0..40,000,000·planned_steps1..40,000,000이며
  steps≤planned이고 completed는 두 값이 같다. sample/event 각0..131,072,
  commit1..16,384·저장 bytes1..512MiB·파일1..65,536을 보존한다.
  이 상한은 기존 input/artifact의 유한 연구 계약이며 전체 부하 수용이 아니다.
- `payload_raw`는1..128KiB UTF-8 JSON object, 모든 깊이에서 중복 key를 거부한다.
  bytes SHA는 DB에서 계산한 값과 같고 `integrity_signature`는64자리 소문자 hex다.
  서명의 실제 검증은 custody 단계다. DB가 만든 최초 recorded_at을 보존한다.

metadata의 닫힌 top-level은 schema_version/status/claim_scope/result_id/tenant_id/study_id/revision,
farm/input_root_sha256/artifact/binding/policies/code다. 판본은 `crop-cycle-result-v1`,
status는 `stored_unpublished_research`, claim_scope는 `synthetic_crop_math_only`다.
farm은 닫힌 scenario_id/scenario_revision/registration_job_id/registration_sha256,
artifact는 닫힌 ref/sha256/header_sha256/status/steps/planned_steps/sample_count/event_count/
commit_count/storage_bytes/file_count다. 이 값들의 JSON type/원 문자열을 모든 대응 column과 대사한다.
숫자 bool/float/문자열/소수·지수 표기를 정수 counter로 묵인하지 않는다. 누락/null도 거부한다.
binding/policies/code는 object이며 내부의 권리·원 요청/등록·코드 pin을 custody가 닫힌 schema로
검증한다. 이 단계는 비어 있는 시험 object로 승인/권리를 만들지 않는다.

DB는 JSON의 whitespace/key 정렬을 canonical로 바꾸지 않고 원 bytes/hash를 보존한다.
canonical 전체 packet/ID·artifact root/manifest/code/HMAC/current rights 대사는 custody가 맡는다.
원 입력/결과 상태/고지 전체를 metadata에 복사하거나 공개 응답으로 노출하지 않는다.

## 설치·불변성·권한

`install_cycle_crop_result_schema(conn,schema)`는 기존 NAME 정책의 안전한 식별자만 받는다.
명시 fresh transaction/savepoint에서 table/function/trigger와 PUBLIC 권한 거부를 설치한다.
IF NOT EXISTS/CREATE OR REPLACE·기존 행의 수정/삭제를 사용하지 않는다.
이미 설치돼 있거나 parent가 없으면 실패하고 새 부분 객체를 남기지 않는다.
후속 schema 변경은 새 계약의 명시 migration이 필요하다.

owner UPDATE/DELETE도 trigger가 거부한다. owner/provisioner의 DDL·TRUNCATE·superuser 권한을
방어했다고 표시하지 않는다. runtime의 SELECT/INSERT/UPDATE/DELETE/TRUNCATE와
routine EXECUTE는 이번 단계에서 모두0이다. 로그인 자체와 전체 기존 role 감사는 계속 통과해야 한다.
새 선택 flag/authority SELECT/INSERT는 `crop-cycle-storage-roles`에서 명시적으로 수용한다.

## 수용 기준과 일정

1. 실제 SCRAM 로그인 DB에서 owner provision/행 bytes·hash/시각/참조를 보존한다.
2. wrong root/참조·tenant FK·closed/schema/type/누락/null·정수 counter/예산·raw/hash/서명·
   중복/metadata 혼합과 invalid UTF-8/JSON/duplicate keys를 거부한다.
3. 실제 네 runtime 로그인에서 새 SELECT/INSERT와 변경을 거부하고 전체 권한 감사/기존 v3 경로를 보존한다.
   owner UPDATE/DELETE trigger, fresh 재설치·부분 설치 rollback/기존 bytes 보존을 확인한다.
4. 집중 시험/원40개 hash·현재 CLI metadata/공식 SQL 근거·로그·DB/role/schema/password 정리와
   링크를 확인한 뒤 checkbox를 갱신한다. 진행 중 CI를 후속 push로 취소하지 않는다.

SQL 근거는 PostgreSQL16의 [JSON/형식·중복 key 검사](https://www.postgresql.org/docs/16/functions-json.html),
[NULL/외래키/유일성 제약](https://www.postgresql.org/docs/16/ddl-constraints.html),
Psycopg의 [transaction/savepoint](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)다.
JSON 누락 추출과 CHECK의 null 허용을 고려해 metadata 조건에 `IS TRUE`를 사용한다.
로컬16.15와 hosted18.6의 수용은 각각 실제 실행 증거로 구분한다.

계약0.5–1시간+installer/불변 제약1시간+SCRAM/잘못된 행·회귀/정리1–2시간의
**2.5–4집중시간**, 하루4시간/CI 대기 제외 **10월5–6일 KST 잠정**이다.
이 추정은10월5일 로컬 수용으로 대체한다. 고유74개의 분할 검증(72개/24.17초와
정상 JSON128KiB/한 byte 초과·빈 bytes2개/1.10초), 실제 SCRAM/기본 네 role·불변/제약·
rollback/기존 v3 보존·DB/role/schema/password 정리를 확인했다. 원 계산/저장42개 hash를 보존했다.
schema fixture 행은 실제 농장 계산이나 파일 실재/HMAC/current rights 증거가 아니다.
다음5파일 명시 role/config의 수용 기준·1.5–2.5시간 잠정치는 위 구현 보고서를 따른다.
실제 채택/국내 독립 자료/actual crop Run0개이며 G0–G4·예측/추천 게시 조건과 날짜 보류를 유지한다.
