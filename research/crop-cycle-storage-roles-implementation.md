# Cycle 저장의 명시 로그인 권한/구성 — 구현과 검증

상태: **로컬 소프트웨어 수용**, 2026-10-05 KST. `crop-cycle-storage-roles`.
[schema 선행](crop-cycle-storage-schema-implementation.md),
[계약](../contracts/crop-cycle-storage-v1.md#별도-명시-로그인-프로필--로컬-수용),
[불변 수용 영수증](artifacts/crop-cycle-storage-roles-reference-20261005.json)을 따른다.
현재 실제 Codex CLI `gpt-6.1-sol / xhigh`의09:33:56.226Z turn_context와 원 line SHA를 기록했다.
CLI 재귀 실행0회이며 제품 runtime CLI 실행으로 표시하지 않는다.

## 구현 범위

5파일은 `backend/app/runtime_roles.py`, `backend/app/operator_config.py`,
`backend/tests/test_runtime_roles.py`, `backend/tests/test_operator_config.py`, `backend/tests/login_database.py`다.
새 keyword-only exact bool `crop_cycle_result_storage=False`와 선택 표 tuple을 연결했다.
누락/false의 기존 profile/table/config는 보존한다. true에서만 명시 설치된
`crop_cycle_research_results`의 authority SELECT/INSERT를 기존 provisioning/현재 전체 감사에 포함한다.
나머지 역할과 authority 변경·grant option·새 routine EXECUTE는 계속 거부한다.
새 dependency/서비스/queue·기존 role/schema 자동 갱신은 없다.

이 flag를 허용한 operator config 시험은 신뢰 factory 전달 경계다.
기존 operator의 실제 HTTPS/SCRAM 기동·기동 후 권한 변경 차단도 회귀 범위에 포함했다.
새 cycle 저장/API 서비스나 현재 파일/farm/HMAC를 이 설정으로 활성화하거나 승인하지 않는다.
직접 작성한 metadata와 시험 서명은 **schema/권한 fixture**이며 실재 계산 artifact/Run이 아니다.

## 실제 검증

WSL의 실제 Python3.12.3/Psycopg3.3.6/Pytest9.1.1, native PostgreSQL16.15를 사용했다.
hosted의3.12.13/18.6 수용은 별도다. loopback SCRAM cluster1개씩 순차 실행,
max_connections32/shared_buffers16MB/work_mem1MB/maintenance16MB, nice10으로 제한했다.

| 검증 | 실제 결과 |
| --- | --- |
| 첫 focused suite: roles/config/schema/login | 234통과·2실패·skip0·80.98초 |
| 실패 원인 | 새 시험이 기존 routine 이름을 두 곳에서 잘못 적음; UndefinedFunction |
| 수정 | 두 시험의 문자열만 실제 `reject_cycle_crop_result_change()`로 대사; 제품 코드 변경0 |
| 해당 두 시험 재실행 | 2통과·skip0·1.16초 |
| 최종 고유 수용 범위 | 236개, 새21개 포함; 분할 검증이며 단일236 GREEN/전체 backend가 아님 |
| 선택 true | 실제 authority SCRAM의 원 metadata INSERT/SELECT/hash/최초 DB 시각 |
| 거부 | 선택 true의 직접 SQL18회·누락/false40회; owner UPDATE/DELETE도 trigger 거부 |
| effective privileges | 네 역할×일곱 table 권한·각 routine EXECUTE 대사, 전체 기존 감사 통과 |
| drift7종 | worker SELECT, authority UPDATE/column UPDATE, PUBLIC SELECT, SELECT 누락, grant option, routine EXECUTE 거부 |
| config | 누락/false/true·잘못된6타입을 dependency import 전에 검사 |
| 기존 v3 | 새 표와 함께 저장/재접속 뒤 이전 payload_raw bytes 보존 |
| frozen source | 원 계산/저장/API/artifact42개+schema source/test2개=44개 SHA 그대로 |

처음에는 아직 없는 flag의 expected RED4개/130deselected·0.86초를 확인했다.
첫 focused 실패와 수정 로그를 보존했다. 두 routine 문자열을 치환한 파일이 현재 시험과 정확히
같고 제품/fixture/config 코드·다른 시험은 변경되지 않았음을 hash/bytes로 확인한다.
schema 기존74개를 이번 focused 회귀에서 모두 포함했다.
권한 시험의 advance/RHS 호출을 금지했으며 role 설치가 crop 계산을 만들지 않는다.

두 검증의 wall은81.4704초/1.4775초, 관측한 최대 순차 자식RSS는157.34375/75.171875MiB다.
WSL 전체나 동시에 실행된 process group의 합계 메모리 측정이 아니다.
각 실행 뒤 role/schema/runtime 비밀번호0개·DB stop/status3·private cluster/admin 파일 제거·소유 서버0개를 확인했다.
원 로그와 접속/비밀은 private `/tmp`에만 두고 공개 영수증에는 hash/정리 수치만 보존한다.

## 권한 근거와 검토

[PostgreSQL16 GRANT](https://www.postgresql.org/docs/16/sql-grant.html)는 table/column/routine 권한,
PUBLIC·membership을 합친 유효 권한과 grant option의 전파를 설명한다.
따라서 선택 SELECT/INSERT만 추가하며 기존 전체 matrix/column/identity 감사를 유지했다.
[권한 정보 함수](https://www.postgresql.org/docs/16/functions-info.html)로 실제 table/function 권한을 대사했다.
[ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/16/sql-alterdefaultprivileges.html)는
새 객체의 기본 권한과 기존 객체의 권한 변경을 구분한다. 현재 provisioner의 fresh 설치와
기존 전체 감사·명시 grant를 재사용했다. owner DDL/TRUNCATE/superuser나 배포 UID/키 소유권은 이번 수용 범위가 아니다.

## CI와 다음 한 단계

이전 `fe41e22`의 [최종 CI5개](artifacts/crop-cycle-stream-ci-20261005.json)는
백엔드3,709개·별도UID4개·여섯 동일 목록/DB 비밀번호 정리·최종 집계로 수용했다.
범위는 continuation/input reader/긴 RHS까지다. cycle artifact/schema/이번 roles는 해당 SHA 밖이다.
작성 browser의 첫25분 timeout 뒤 같은 SHA의 실패 job만 재실행해7개/정리·workflow 성공을 확인했다.
[처음 hold](artifacts/crop-cycle-stream-ci-hold-20261005.json)와
[재실행 증거](artifacts/crop-cycle-stream-authored-retry-ci-20261005.json)는 그대로 보존한다.
후속 batch push는 이 원격 실행이 모두 terminal인 것을 확인한 뒤 수행한다.

다음 `crop-cycle-result-storage`는 실제 파일/입력 root와 등록 farm의 현재 권리·HMAC를 연결한다.
기존 v3의 inline program/20MiB payload를 긴 파일에 그대로 적용할 수 없으므로
bounded root/manifest·period/forcing·현재 원천/프로그램 권리의 대사를 별도 계약으로 고정한다.
선행 artifact/schema/roles는 수용했으며 다음 module/test/계약의3–5파일로 진행한다.
수용 기준은 실제 SCRAM의 같은 farm/root metadata·파일 완전성/코드/header/고지·HMAC,
commit 전후 철회·교차 farm/tenant/root·혼합/부분 파일 거부·별도 Python 읽기/복구,
재적분 없는 현재 권리 조회와 DB/비밀/FD 정리다. GET/API/client/3D는 이후다.

기존1.5–2.5시간/10월5–6일 역할 단계 예상은10월5일 로컬 수용으로 대체한다.
다음 custody는 계약/기존 farm-provider 대사1–2시간+bounded 입력/결과 결합2–3시간+
실제 SCRAM/철회/재시작·정리2–3시간, **5–8집중시간**이다.
하루4시간·CI/외부 자료 대기 제외 **10월5–7일 KST 잠정**이며 실제 입력/참조 결합 감사에 따라 갱신한다.
actual input 채택/국내 독립 농장 자료/실제 crop Run0개·G0–G4 미승격이다.
166일 실제 RHS·성장3D/생과·자원·Decimal 경제 결합, 예측/추천 게시 날짜는 아직 보류한다.
