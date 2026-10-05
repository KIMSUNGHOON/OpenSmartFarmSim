# 긴 작물 계산 결과의 불변 DB 참조 표

2026-10-05 KST. [installer](../backend/app/crop_cycle_result_schema.py),
[시험](../backend/tests/test_crop_cycle_result_schema.py),
[계약](../contracts/crop-cycle-storage-v1.md),
[실제 CLI·소스/초안·시험/정리 영수증](artifacts/crop-cycle-storage-schema-reference-20261005.json).
**cycle 저장의 schema 구획만 로컬 수용**했다. 원격/명시 role/config·custody/API/긴 결과3D는 후속이다.

## 확인할 수 있는 산출물

새 `crop_cycle_research_results`가 private POSIX 결과의 원 input/artifact root·header/참조,
tenant/study/revision/result ID·farm 등록 job/scenario·metadata bytes/hash·처리/기록/저장 수를 보존한다.
512MiB 파일을 기존20MiB startup row에 넣지 않는다. 경로 대신 내용 주소인
`crop-cycle-artifact-v1:<sha256>`만 기록한다. 기존 계산/입력/저장/API42개 hash를 보존했다.

metadata는128KiB 이하의 닫힌 top-level/farm/artifact 구조와 object형 binding/policies/code다.
원 JSON의 field type/문자열을 대응 column과 대사하며, counter는 bool/float/문자열/null·지수 표기를
정수로 묵인하지 않는다. 누락/null을 CHECK의 unknown으로 통과시키지 않고 중복 key를 모든 깊이에서
거부한다. signed 내용 주소/현재 권리·실제 파일/등록/model/manifest 검사는 다음 custody가 맡는다.
이 schema의 직접 작성 행은 실제 crop Run·농장 파일/자료 권리 승인 결과가 아니다.

fresh provisioner의 table/function/trigger는 transaction/savepoint로 함께 설치한다.
owner UPDATE/DELETE도 거부하고 재설치가 기존 행/함수를 조용히 갱신하지 않는다.
기본 네 runtime role에는 새 권한0이며 PUBLIC table/routine 접근도 거부한다.
owner DDL/TRUNCATE·superuser 통제와 배포 자격증명/UID 독립성을 수용했다고 표시하지 않는다.

## 통과한 검증과 자원

- **74개 고유 집중 검증의 분할 수용:** 첫72개/24.17초, 추가2개/1.10초·skip0.
  단일74개 실행이나 전체 백엔드 통과로 표시하지 않는다. 초기 미구현 RED의8실패와
  설치 후 식별자8개/0.21초도 보존하며 중복 계산하지 않는다.
- 실제 SCRAM/owner provision·행 원 bytes/hash·최초 DB 시각과 같은 tenant의 job 참조를 확인했다.
  실제 네 runtime 로그인에서 SELECT/INSERT/UPDATE/DELETE/TRUNCATE를 모두 거부하고,
  기존 전체 role 감사가 새 표/routine에도 적용됐다. PUBLIC SELECT/EXECUTE 변화는 감사가 거부했다.
- 동일 metadata로 맞춘 잘못된28종 column/range/hash·2종 parent FK/교차 tenant·
  다시 hash한17종 metadata identity/shape/counter type,9종 malformed/UTF-8/oversize JSON을 거부했다.
  terminal completed는 모든 planned step을 요구하고 hold의 빈 확인 과거0count를 보존했다.
- owner UPDATE/DELETE trigger·중복/새 revision, 재설치 실패 뒤 원 bytes 유지,
  parent 없는 fresh 설치의 부분 객체0개/rollback과 기존 startup v3 행/기본 policy 보존을 확인했다.
- 마지막2개는 정상 JSON을 **정확히131,072bytes**로 만들어 저장/원 bytes를 읽고,
  동일한 닫힌 구조의131,073bytes를 CheckViolation으로 거부했다. 빈 raw bytes도 행0개다.
  malformed JSON 거부를 정상 JSON의 byte 상한 검증으로 대신하지 않았다.
- schema 시험에서 RHS/advance를 금지했다. fixture의 숫자/hash·빈 binding은 표 제약용이며
  계산량/production 규모·권리 검증·재현 정확도/G0–G4를 증명하지 않는다.

```bash
# 기존 테스트용 SCRAM DSN/비공개 passfile을 준비한 환경
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_result_schema.py
```

실제 로컬 PostgreSQL **16.15**, Python **3.12.13**/psycopg **3.3.6**/pytest **9.1.1**을 재사용했다.
각 실행은 순차 private loopback/SCRAM cluster1개,32연결/16MB shared buffers/1MB work memory였다.
첫 전체 과정24.542초/순차 자식 최대RSS84.73MiB, 추가 byte 과정1.427초/74.91MiB다.
이 값은 WSL 전체 메모리나 DB/pytest 프로세스군 합계·production 처리량이 아니다.
두 실행 모두 role/schema/발급 비밀번호 파일0개, PostgreSQL 종료/status exit3와
private cluster/admin 비밀번호 파일 제거·남은 소유 서버0개를 확인했다.

## 설계 근거와 검토

현재 CLI turn_context **2026-10-05T08:51:25.279Z**, **gpt-6.1-sol / xhigh**에서
설계/구현/검토했고 actual line SHA·코드/시험/로그 hash를 보존한다. 재귀 CLI0회다.
이 개발 세션과 DB 시험은 제품 runtime Codex 호출 증거가 아니다.

PostgreSQL16의 [JSON/중복 key·추출/형식](https://www.postgresql.org/docs/16/functions-json.html),
[NULL/외래키/유일성](https://www.postgresql.org/docs/16/ddl-constraints.html),
Psycopg의 [transaction/savepoint](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)를
같은 세션에서 확인했다. JSONB 정규화 전 원 JSON counter 문자열을 column과 비교한다.
닫힌 object 검사는 CASE로 형식을 확인한 뒤 key 연산을 수행하고 모든 조건에 IS TRUE를 둔다.
공식 문서 검토는 잠긴 패키지/로컬 DB를 새 버전으로 변경한 증거가 아니다.

검토는 column↔raw metadata type/pin·내용 주소/예산·tenant parent/유일성·NULL/closed/중복,
fresh transaction/immutable trigger·PUBLIC/기본 runtime grants와 전체 기존 audit·예외/정리를 확인했다.
SQL은 schema/등록 job 존재·저장 참조의 형식만 검사한다. 실제 farm/input/file·canonical packet ID/
manifest/code/서명/권리 정책의 의미는 후속 서버 검증을 통과해야 한다.
첫72개 시험/계약 hash는 Git`de3db52`에서 검증하고 최종74개/수용 계약 hash와 구분한다.

후속 SHA`fe41e22`의 authored-browser 재시도는 **7passed/1,207.46초·정리 성공**과 workflow 성공이다.
첫25분 deadline 취소는 [별도 보류 증거](artifacts/crop-cycle-stream-ci-hold-20261005.json)로 보존했다.
동일 SHA Backend 전체/집계는 아직 대사가 필요하며 이번 schema는 그 SHA에 없다.
진행 중 CI를 후속 push로 취소하지 않고 local commit을 보존한다.

## 다음 한 단계와 외부 의존성

다음 **`crop-cycle-storage-roles`**는5파일(runtime_roles/operator_config, 두 시험과 login_database)이다.
기본 false의 `crop_cycle_result_storage` flag·optional operator parsing·선택 설치/grant를 연결한다.
실제 SCRAM에서 true의 authority SELECT/INSERT만 허용, 다른 role/변경·과다 grant·잘못된 타입 거부,
누락/false의 기존 config/grant/저장 호환·기존 v3 bytes/hash·전체 audit와 DB/password 정리를 확인한다.
불변 표만으로 연구 결과 저장/게시 부모를 체크하지 않는다. 그다음 current rights/HMAC custody가
실제 원 input/artifact와 farm 연결을 보존하며 API/client/같은 UTC3D로 이어 간다.

계획 작업량은 flag/grant와 fixture0.5–1시간+operator config/type 호환0.5시간+
실제 SCRAM/권한 변화·회귀/정리0.5–1시간의 **1.5–2.5집중시간**,
하루4시간/CI 대기 제외 **10월5–6일 KST 잠정**이다. 관측 근거는 현재74개·이전 v3 role/config 수용이다.
이전 schema2.5–4시간/10월5–6일 예상은 **10월5일 로컬 완료** 실적으로 대체한다.
전체 작기3D/생과·자원·경제의 다음 일정은 각 실제 연결/입력 근거 뒤 갱신한다.

실제 forcing/초기/관리·품종 채택0개·국내 독립 자료0건·actual crop Run0개다.
166일 실제 RHS 부하·자동 착과/pre-onset/RGR·생과/구매 자원/경제와 G0–G4는 미수용이다.
농장 자료 확보를 모델 개발과 병행하며 예측·추천/production 완료 날짜는 자료 확보 전 산정하지 않는다.
