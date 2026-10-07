# 검증 계산 결과의 새 DB 표·명시 역할 — 로컬 수용

2026-10-07 KST. [개발 계약](../contracts/crop-cycle-calculation-db-custody-v1.md)의
`crop-cycle-calculation-result-schema`만 수용한다. 서명 결과 게시·농장 결속 부모·전체 작기/API/3D는 후속이다.

## 구현과 경계

원 표는 구형 result/artifact ID만 받으며 tenant/study/revision의 유일성을 사용한다.
원 constraint/행/서명·조회 의미를 보존하기 위해 새 계산의 별도 표를 설치한다.
[새 schema module](../backend/app/crop_cycle_calculation_result_schema.py)은96줄이다.
원 schema와 import/판본/table/installer/trigger 이름의 명시 변환 뒤 AST가 같다.
`crop_cycle_verified_research_results`는 새 result/artifact ID와 원25 column·닫힌13/4/11필드,
128KiB metadata/원 한도·payload hash/column equality·tenant/job FK·불변 trigger를 검사한다.

[역할 module](../backend/app/runtime_roles.py)은 기본값False의 정확한 bool
`crop_cycle_calculation_result_storage`와 새 table 목록을 추가했다.
기존 함수 중 bool 검사와 `_tables` 두 함수만 바뀌었다. True일 때 fresh role installer와
whole effective grant audit가 authority SELECT/INSERT만 허용한다. 나머지 역할/PUBLIC·column/routine/
GRANT OPTION 등은 기존 감사로 거부한다. 일반 pipeline·service·새 framework는 추가하지 않았다.

이 flag는 **내부 policy의 opt-in**이다. 운영자 설정 파일/API runtime factory와 배포된 역할 migration은
아직 새 판본에 연결하지 않았다. 이 작업의 fresh 역할 설치를 운영 배포 수용으로 보고하지 않는다.

## 실제 검증

현재 [시험 파일](../backend/tests/test_crop_cycle_calculation_result_schema.py) 전체를 최종 실행해
**68개/22.68초·종료0**을 확인했다. policy/identifier15개와 실제 DB53개다.
실제 SCRAM PostgreSQL16.15(`server_version=160015`)에서 다음을 확인했다.

- trusted owner의 설치와 authority round trip, 전체 grant audit, default deny와 명시 opt-in의 네 역할 행렬.
- 같은 tenant/study/revision의 기존 표 행과 새 표 행 공존, 설치/삽입 전후 기존 bytes/hash/최초 시각 보존.
- 구형 ID/ref·판본 혼합, 닫힌 JSON·중복 key/null/nonfinite/UTF-8/크기,
  payload hash/column·상태/수량 불일치와 foreign tenant/job 거부.
- sample/event/commit/bytes/files 한계값 자체 허용과 초과 거부, 부분 걸음의 hold metadata 보존.
- 중복 의도/ID 거부·새 revision 정정, owner UPDATE/DELETE 불변 trigger,
  PUBLIC/table/column/routine/GRANT OPTION drift와 opt-in의 표/권한 누락 거부.
- jobs 없는 설치 rollback, 재설치 실패 뒤 원 객체/행 보존, 실행/RHS0과 schema/role/passfile/PG 정리.

이 행은 **직접 작성한 SQL 형식 시험 metadata**다. integrity_signature의 자리값을 포함하며
실제 농장에 등록한 signed 계산 결과·수확·예측 입력이 아니다. 실제 서명/HMAC/current farm 검사는 다음 자식이다.

처음 policy 시험의 autouse DB fixture는 PG 환경이 없어1건너뜀이었고 assertion을 실행하지 않았다.
fixture 의존성을 좁힌 뒤 누락된 flag의 실제1실패를 확인하고 구현했다.
첫 전체 실행은63통과/5실패였다. 초과값의 CHECK 거부를 pytest가 먼저 잡아 savepoint rollback 전에
종료하던 시험의 context manager 순서를 수정했다. 제품 SQL/role 소스는 이 수정에서 바뀌지 않았다.
후속 전체68개/22.84초도 통과했다.

초기 private 실행기는 복사한 서버 단계의 source 세 경로를 남겼고 실제 schema 시험 경로/해시는 기록했다.
그 기록을 덮어쓰지 않고 schema/role/test/contract 네 경로를 명시해 실행 전후 SHA를 대사했다.
실제 PG 판본도 기록한 **최종68개/22.68초**가 현재 수용 근거다. 앞4개/중간68개를 고유 수에 더하지 않는다.
별도 collection68개는 실행 수가 아닌 목록 대사다. 위 오류와 실제 로그/판본은
[불변 영수증](artifacts/crop-cycle-calculation-result-schema-reference-20261007.json)에 기록했다.

## 비용·정리와 원 실행 보존

최종 전체 호출 wall23.254453초, 주 pytest 프로세스의200ms 표본 최대 VmRSS98,811,904bytes다.
이 표본은 PG/모든 자식 합계나 확정 peak가 아니다. 정상 SQL metadata는1,063bytes다.
실제 성공3회와 실패1회의 각 PG PID/data·임시 test tree 제거, DB schema/role/passfile 잔존0을 확인했다.
전체 backend/새 브라우저/이 커밋의 hosted CI는 실행하지 않았다.

원166일 실행의55 source·750입력/113,920,841bytes·각 named blob SHA와 root/spec/감독자 SHA를 보존했다.
19:26 KST의 같은 controller/worker PID·시작 ticks·nice15를 확인했고
1,736,196/1,816,704걸음(95.568%)이며 terminal result/receipt는 없었다.
이는 실행 관측이며 전체 수용이 아니다. 원 마감20:07 KST와 예산을 변경하지 않았다.

native CLI는 `gpt-6.1-sol / xhigh`, 재귀 실행0이다. 이 작업의 CLI record/actual command/output·
실패/정정·current source/청소 증거를 위 영수증에 결속한다.

## 다음 수용과 외부 의존성

다음 `crop-cycle-calculation-result-publication`은 새 exact 서버·공식 context/current binding을
DB HMAC/닫힌 packet·원자 put/byte-identical retry·get/page/summary에 연결한다.
실제 작은 등록 계산/중단 재개·권리 철회/rollback·원 signed 이력 공존·조회 RHS0/원량과 정리가 필요하다.
DB 부모는 두 자식 뒤 체크하며, 전체 registered 작기의 누적 prefix/서명 검사 비용·저장/복원·같은 UTC3D는 별도다.
이번 schema의1–2.5집중시간 잠정 추정은10월7일 로컬 수용 실적으로 대체한다.
publication 날짜는 실제 port/현재 binding 비용 대사 뒤 갱신한다.

채택 실제 품종 입력·국내 독립 자료·새 실제 작물 Run은0이며 G0–G4는 미평가다.
생과 수확량 → 물/양분·구매 에너지 → Decimal 경제 연결이 남아 있고 생산 예측·미래 마진·추천은 보류다.

SQL 설계 근거는 [PostgreSQL18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html),
[GRANT](https://www.postgresql.org/docs/18/sql-grant.html),
[CREATE TRIGGER](https://www.postgresql.org/docs/18/sql-createtrigger.html)다.
문서 확인과 로컬16.15 실행·제품/hosted18.6의 수용 범위를 구분한다.
