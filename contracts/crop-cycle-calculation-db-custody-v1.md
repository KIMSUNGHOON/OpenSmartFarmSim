# 검증 계산 판본의 DB 저장 — v1 개발 계약

2026-10-07 KST. `crop-cycle-calculation-db-custody`의 구현 계약이며 아직 미수용이다.
선행은 [새 서버 실행](crop-cycle-calculation-server-custody-v1.md)과
[기존 DB 경계](crop-cycle-db-custody-v1.md)다. 현재 native Codex CLI
`gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI 실행은0회다.
10:10:03.951Z turn_context line SHA는
`7603d8b2181dd96a4fb8f98141c1ab94fe296a84155a293f50f43c61ae300487`이다.

## 현행 경계와 두 구현 자식

기존 `crop_cycle_research_results`는 `crop-cycle-result-v1` ID와 payload,
`crop-cycle-artifact-v1` ref만 받는다. 기존 store도 exact 원 서버와8필드 binding을 받는다.
새 서버는 별도 판본·9필드 binding·공식 계산 context를 사용한다.
기존 표의 기본키는 tenant/study/revision이므로 같은 의도의 두 판본을 혼합하면 기존 조회도 모호해진다.
기존 행/constraint/서명/code pin을 변경하지 않고 **새 결과 표와 명시적 권한 opt-in**을 사용한다.
원166일 실행의55 source는 실제 종료와 증거 보존 전까지 고정한다.

1. `crop-cycle-calculation-result-schema`: 새 schema module, runtime role module,
   실제 SCRAM schema/role test, 이 계약의4 core파일.
   새 표·제약·기존 행 공존과 default deny/명시 authority 최소 권한을 검증한다.
2. `crop-cycle-calculation-result-publication`: 위 수용 후 새 store module,
   순수 metadata test, 실제 SCRAM publication test, 이 계약의4 core파일.
   현재 등록/권리·서명 참조·원자 게시/재시도·새 서비스 재조회와 원값을 검증한다.

두 자식을 실제 수용한 뒤 DB 부모를 체크한다. 농장 결속 부모·전체 작기 저장/복원·API/같은 UTC3D와
G0–G4의 수용은 각각 해당 증거를 요구한다. 새 queue/service/일반 운영 확장은 필요하지 않다.

## 첫 자식: 새 표와 역할

- module: `backend/app/crop_cycle_calculation_result_schema.py`
- installer: `install_calculation_cycle_crop_result_schema(conn, schema)`; trusted provisioner가
  owner identity로 새 객체만 한 transaction에 설치한다. 잘못된 identifier는 SQL 전 거부한다.
  기존 객체가 있으면 실패하며 재설치/ALTER/기존 데이터 갱신을 수행하지 않는다.
- table: `crop_cycle_verified_research_results`
- payload/result ID 판본: `crop-cycle-verified-result-v1`
- artifact ref: `crop-cycle-verified-artifact-v1:<sha256>`
- 기존25개 column, 닫힌13 top/farm4/artifact11 metadata 형태와 원 수량/한도를 유지한다.
  bytea/hash·JSON unique keys·판본/column equality·상태/걸음/개수/크기·tenant/job FK·불변 trigger를 검사한다.
  이 SQL 형식 검사는 서버 실행·권리·HMAC 확인의 대체 증거가 아니다.
- `RuntimeLoginPolicy.crop_cycle_calculation_result_storage`는 정확한 bool이며 기본값False다.
  True이면 기존 전체 role audit와 fresh installer의 authority SELECT/INSERT 허용 목록에 새 표만 추가한다.
  request/worker/supervisor 및 PUBLIC의 새 표/column/sequence/routine 권한은0이다.
  authority에도 UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER/GRANT OPTION을 허용하지 않는다.
  새 flag를 켜도 기존 표의 허용 목록은 기존 flag를 따른다.
- installer는 runtime grants를 부여하지 않는다. 새 표를 먼저 provision하고 명시 policy로
  역할을 설치한다. 이미 설치한 운영 역할의 migration은 별도 검토·실행 증거가 필요하다.
  이번 실제 시험의 fresh roles를 배포된 운영 역할 migration으로 보고하지 않는다.

### 첫 자식 수용 기준

1. 실제 SCRAM의 owner·authority round trip, 새 policy의 whole role audit와 fresh role installer 성공.
2. default policy에서 네 역할의 새 표 접근 거부; True에서 authority SELECT/INSERT만 허용.
   True인데 표가 없거나 권한이 부족하면 audit hold. bool 외 값과 추가 table/column/routine grant도 거부.
3. SQL 제약을 실제 잘못된 insert로 검증한다. 구형 ID/ref·판본 혼합, 중복/추가/누락/null JSON,
   payload hash/column·수량/상태 불일치, foreign tenant/job·중복 의도/ID를 거부한다.
4. 같은 tenant/study/revision의 원 표 행과 새 표 행을 실제 저장하고 원 bytes/hash/time을 보존한다.
   owner UPDATE/DELETE도 불변 trigger로 거부한다. 새 revision의 정정만 별도 행으로 허용한다.
5. 부모 jobs 없는 설치의 transaction rollback, 재설치 실패와 원 객체 보존을 확인한다.
6. RHS/적분0, 임시 schema/role/passfile/PG PID/data 정리0와 실행 로그/소스 SHA/비용을 기록한다.

## 두 번째 자식: 서명 결과 게시와 현재 조회

`CalculationCycleCropResultStore(exact CalculationServerCustody, *, integrity_key)`는
원 server key와 다른32..4096bytes의 고정 DB HMAC key를 받는다. 새 flag와 현재 authority를 검사한다.
기존 put/get/page/summary 내부 관례를 유지하고 공식 context 자체를 현재 binding 검사에 전달한다.
조회 전용 타입·원 서버/DB packet을 새 결과로 받지 않는다.

- terminal인 원 signed progress만 put한다. 미생성/yielded는 hold다. 게시/조회 RHS는0이다.
- canonical 최대128KiB packet, 닫힌9필드 binding과 input validation provenance,
  새 code/dependency map·result ID·모든 대응 column·원 HEAD/proof/artifact를 대사한다.
- DB HMAC domain은 `b'ossf-crop-cycle-verified-result-v1\0'`다.
  HMAC은 권리 승인이나 실제 농장 정확도의 증거가 아니다.
- root/journal lock 아래 기존 nonblocking transaction advisory lock을 사용한다.
  INSERT ON CONFLICT DO NOTHING 뒤 SELECT·byte-identical retry/최초 recorded_at을 확인한다.
  다른 결과는 conflict다. commit 직전 철회는 rollback, commit 직후 철회는 반환 hold와 audit row 보존이다.
- get/page/summary는 현재 tenant/farm/source/input rights를 전후 검사하고 저장된 원 progress/UTC/량을 읽는다.
  DB bytes/hash/HMAC/column·code/key/policy·원 파일 변조·혼합을 거부한다.
- 실제 작은 연속/중단 재개 결과의 저장·새 서비스 조회·원량/manifest/hold 보존,
  실제 잠금·rollback·철회·기존 행 공존·FD/DB/role/passfile/PG 정리로 수용한다.
  별도 프로세스 시험은 실제 child 실행 방식과 복원한 상태 범위를 보고한다.

## 일정·자료와 전체 경로

첫 자식은 SQL/role 이식·검토0.5–1.5집중시간, 실제 DB 검증/기록0.5–1시간의
**1–2.5집중시간**으로 잠정 분해했다. 10월7–8일 KST 범위이며 실제 실행 결과로 갱신한다.
두 번째 자식은 실제 code port/현재 binding 비용을 대사한 뒤 별도로 추정한다.
CI 대기·전체166일·전체 등록 실행의 누적 prefix/서명 비용·외부 자료 확보는 이 추정에 포함하지 않는다.
원166일 고정 마감은10월7일20:07 KST이며 완료 약속이 아니다.

채택된 실제 품종 입력·국내 독립 자료는 각각0건이다. G0–G4는 미평가이며 생산 예측·미래 마진·추천은 보류다.
전체 작기/복원·같은 UTC3D 뒤 수확 제거/생과 환산 → 물/양분·구매 에너지 → Decimal 경제 연결 순서를 유지한다.

## SQL 근거

원 primary key·unique/FK·NOT NULL/CHECK의 행 경계는
[PostgreSQL18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html),
최소 권한 행렬은 [GRANT](https://www.postgresql.org/docs/18/sql-grant.html),
불변 행 거부는 [CREATE TRIGGER](https://www.postgresql.org/docs/18/sql-createtrigger.html)를 확인했다.
이 문서들은2026-10-07 조회했다. 현재 로컬 SCRAM 검증용 PostgreSQL16.15와 hosted/제품 이미지는
시험별 실제 판본으로 기록하며 문서 조회를 실행 증거로 세지 않는다.
