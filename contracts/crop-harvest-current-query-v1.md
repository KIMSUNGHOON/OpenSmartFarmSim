# 질량·배정의 서버 등록과 현재 조회 — v1

2026-10-08 구현 전 계약. [기존 불변 artifact](crop-harvest-replay-v1.md) 뒤
`crop-harvest-current-query`를 세 자식으로 나눈다. 현재 native CLI `gpt-6.1-sol / xhigh`에서
판단하며 CLI를 재귀 실행하지 않는다. [기술 스택](../docs/TECH_STACK.md)의 POSIX 파일→DB 게시를 따른다.

## 작업 분해와 등록 경계

1. `crop-harvest-registry-schema`: 이 계약·`backend/app/crop_harvest_registry_schema.py`·
   `backend/tests/test_crop_harvest_registry_schema.py`의3 core파일. 별도 PostgreSQL 스키마/owner와
   publisher/reader 로그인을 명시적으로 설치·감사하고 불변 metadata 표를 만든다.
2. `crop-harvest-registration`: 기존 검증 query의 원 결과와 명시 질량/배정 원문에서 서버가 artifact를 생성한다.
   별도 integrity key와 domain으로 metadata를 서명하고 현재 부모/농장/권리를 확인한 뒤 DB에 등록한다.
   착수 시 publication/store와 집중/native 시험을3~5파일로 나눈다.
3. `crop-harvest-registered-query`: 서명 metadata의 서버 소유 key/hash로 artifact를 열어 현재 권리 아래
   summary/page를 제공한다. 혼합/변조/철회/다른 계정·페이지 뒤 변경을 거부하고 fresh Python 실제 DB 복원을 검증한다.
   그 뒤 HTTP/SDK·같은 UTC 표/3D로 연결한다.

원 query는 공유 runtime role policy와 원 store/schema의 실제 코드 hash를 검사한다.
별도 namespace·owner·두 최소 권한 로그인으로 파생 metadata를 추가하고 기존 원 schema/role/code/서명 이력을 보존한다.
이 별도 스키마의 현재 역할·권한·객체를 독립 감사하며 기존 parent query의 권한도 계속 검사한다.
파일만의 서명 catalog는 DB 등록을 대체하지 않는다. 새 프레임워크/관리형 저장소는 추가하지 않는다.

고객 요청은 원 result ID·명시 원문/판본을 지정할 수 있다. artifact 위치/key/hash와 등록 시각·서명은 서버가 정한다.
등록 조회에는 파생 result ID와 농장 참조를 사용하고 고객의 임의 경로/hash/승인 bool을 등록 권한으로 받지 않는다.
첫 경로는 `synthetic`/`assumed` 연구 산술이며 실제 품종·자료 채택/관문/Run 게시가 아니다.

## 별도 스키마와 역할

`HarvestRegistryPolicy(schema, owner, publisher, reader, database)`는 서로 다른 유효 소문자 SQL 이름만 허용한다.
owner는 NOLOGIN·비특권이며 publisher/reader는 LOGIN·비특권·연결 한도8이다.
installer는 지정 DB에서 새 역할/스키마만 원자적으로 만든다. 이미 있는 객체는 migration 없이 덮어쓰지 않는다.
자격증명은 운영자가 별도 비밀 파일로 주입하며 schema 함수가 비밀을 받거나 출력하지 않는다.

publisher는 schema USAGE와 해당 표 SELECT/INSERT만, reader는 USAGE/SELECT만 받는다.
양쪽 모두 CREATE/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER·owner membership을 받지 않는다.
PUBLIC에 schema/table/routine 권한을 주지 않는다. audit는 실제 DB·owner/로그인 특권·membership·객체·ACL·권한을 검사한다.
열별 추가 권한과 runtime의 권한 재위임을 거부하고 불변 trigger의 활성 상태·대상·함수 본문도 검사한다.
정상 생성 및 거부 뒤 기존 부모 schema/role 감사와 원 result의 재조회가 계속 성공해야 한다.

표는 `harvest_registered_results`이며 tenant/result ID가 기본 키다.
원 result ID·farm scenario/revision·등록 hash·artifact key/hash/row count/row chain·두 parameter hash,
canonical payload bytes/SHA·서명·publisher·서버 최초 시각을 저장한다. tenant/parent별 index를 둔다.
SQL은 닫힌 JSON·열/본문 일치·유형·범위·해시·result prefix·claim/status/승인false를 검사하고 UPDATE/DELETE를 거부한다.
SQL 형식 검사는 HMAC 진본·출처/원량·권리·관문 검사를 대신하지 않는다.

metadata v1의 최상위 key는 `schema_version,status,claim_scope,rights_or_gate_approval,tenant_id,result_id,`
`parent_result_id,farm,source,artifact,parameters,code`다. source는 원6필드, farm은 원4필드이며
artifact는 `key,sha256,row_count,row_chain_sha256,writer_code_sha256`, parameters는
`mass_sha256,allocation_sha256`를 갖는다. code는 publication/schema/artifact code hash다.
최초 기록 시각은 DB의 `recorded_at`으로 보존하며 재시도에 임의로 갱신하지 않는다.

## 첫 한 단계의 수용

정책 이름/DB/역할 격리·default deny·실제 TCP SCRAM의 publisher/reader 권한·SQL 닫힌 형식/열 대사·
hash/불변성·rollback을 확인한다. 기존 실제 원 result를 가진 DB에 별도 schema를 설치한 뒤
기존 권한 감사/원 행·조회·입력/파일을 보존하고 새 schema/role/passfile·PG/임시 경로 정리를 확인한다.
모든 시험 행은 SQL 형식 fixture라고 기록하며 실제 파생 등록·생장 계산·판매/마진·G0–G4로 보고하지 않는다.
이 증거가 존재한 뒤 schema 자식만 체크한다. 등록·현재 query와 전체 부모는 미완료다.

실제 품종/계수·국내 독립 자료0건, 생산/미래 마진/추천·원격 Backend/push·구형 native 종료 보류는 유지한다.
작은 스키마 개발은 독립 자료 확보/기후·자원 완성을 기다리지 않는다. 완료 날짜는 실제 검증 후 갱신한다.

## 스키마 수용과 다음 등록 한 단계

`crop-harvest-registry-schema`는2026-10-08 21:14 KST에 [실제 검증](../research/crop-harvest-registry-schema-implementation-20261008.md)으로 수용했다.
순수16개/실제 SCRAM1개·집중17개·원 종료0·SQL11종/권한·trigger10종 거부·416 source/정리를 확인했다.
시험 당시 계약/코드/시험의 hash와 snapshot은 영수증에 보존했다. 실제 artifact 서명/등록·현재 query는 미완료다.

다음 등록은 `backend/app/crop_harvest_registry.py`, `backend/tests/test_crop_harvest_registry.py`,
`contracts/crop-harvest-registration-v1.md`의3 core파일로 시작한다.
registry 제공자에서 metadata 구성/검사·서명·최초 INSERT/재시도를 함께 수행한다.
`publication_code_sha256`는 이 제공자의 실제 code hash를 뜻한다.

수용은 다음과 같다.

1. 정확한 현재 원 query와 서버 구성만 받고 원 result/farm·명시 합성 질량/배정 원문에서 서버가 저장 key·artifact·등록 ID를 정한다.
2. 원 계산/표시 권리와 쓰기 scope를 파일 생성 전·DB 게시 직전에 검사한다. 서로 다른 result/farm/원문/판본·임의 경로/hash·권한 철회를 거부한다.
3. 불변 파일을 먼저 완료한 뒤 별도 domain/key의 metadata 서명과 최소 권한 publisher 거래로 등록한다.
   SQL 형식 fixture를 진짜 서명으로 받아들이지 않으며 첫 DB 시각을 유지하는 동일 재시도·충돌 거부를 확인한다.
4. 파일 완료 후 DB 실패·게시 직전 철회·transaction rollback에서 새 등록을 조회 가능하게 만들지 않는다.
   미등록 파일은 private에 남을 수 있고 원 DB/파일/서명 이력은 보존한다.
5. 작은 실제 SCRAM 부모에서 원6행 artifact·서명/DB 대응·현재 권리와 scope 거부·RHS0/새 proof0·자원/비밀 정리를 확인한다.
   전체166일 새 등록 부하·fresh DB 현재 query·HTTP/SDK/3D·실제 계수/자료/관문 수용은 후속이다.
