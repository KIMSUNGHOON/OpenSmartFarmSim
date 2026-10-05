# Cycle 서명 결과의 불변 DB 게시 — v1 후보

상태: **구현 후보·집중 검증 중**, 2026-10-05 UTC. 작업 `crop-cycle-db-custody`.
[실행 범위와 남은 수용](../research/crop-cycle-db-custody-implementation.md)을 확인한다.
선행 [서버 계산/서명 저장의 로컬 수용](../research/crop-cycle-server-custody-implementation.md),
[불변 DB 표/명시 authority 권한](crop-cycle-storage-v1.md)을 연결한다.
판단은 현재 Codex CLI `gpt-6.1-sol / xhigh`에서 수행했다.
12:12:17.766Z turn_context의 원 line SHA는
`9309fcc957e31594235bb0febf064b4091b49455cd05d052942706cf71b12236`이며 재귀 CLI0회다.
원 계산/저장49개 파일을 보존한다. 이번 작업은 module/순수 test/SCRAM test/계약의4 core파일과 집중 검증 보고서/영수증이다.

## 내부 인터페이스

`CycleCropResultStore(server, *, integrity_key)`는 정확한 `CycleServerCustody` 객체와
운영자가 제공한32..4096bytes의 별도 DB HMAC key를 고정한다.
server/binding/jobs/authority identity·정확한 bool flag/현재 전체 grant 감사·private root·resolver·
rights policy와 module hash가 달라지면 hold다. 생성자가 표/권한을 설치하거나 입력·실행을 만들지 않는다.

- `put(tenant, request_raw)`는 이미 terminal인 서버 결과만 게시한다. yielded/미생성 결과는 hold다.
  실제 계산은 선행 `server.advance`에서 끝낸다. 요청에서 파일 경로·외부 artifact·progress를 받지 않는다.
- `get(tenant, result_id, farm_ref)`는 현재 권리가 허용한 내부 불변 record를 반환한다.
  유효한 현재 principal의 미존재 ID만 `None`이다. farm_ref는 원 binding 요청의 닫힌4개
  scenario_id/scenario_revision/registration_sha256/crop_id다.
- `page(tenant, result_id, farm_ref, kind, start=0, limit=None)`는 같은 DB 참조의 원 sample/event 페이지를 읽는다.
  선택 HEAD·progress가 저장 시점과 다르면 hold다. metadata와 실제 페이지의 ID/hash/UTC를 바꾸지 않는다.
- `summary(tenant, result_id, farm_ref)`는 원 terminal summary의 manifest·hold 사유·확인 과거를
  최대2MiB로 읽는다. 전후 현재 권리/선택 progress를 검사한다. 다음 typed API와3D가 보류를 설명할 근거다.

record는 기존 내부 관례의 result_id/payload_raw/payload_sha256/recorded_at이다.
원 binding/등록·정책을 포함하는 내부 packet은 공개 API 응답이 아니다.
원 서버의 hold/conflict/pending/PermissionError를 사용해 context manager가 오류 종류를 지우지 않게 한다.
HTTP·새 worker/queue·Run·schema migration은 이번 인터페이스에 포함하지 않는다.

## 닫힌 metadata와 HMAC

최대128KiB canonical UTF-8 JSON이며 중복 key/nonfinite/null·잘못된 타입을 거부한다.
top-level13개와 farm4개/artifact11개는 [수용된 표](crop-cycle-storage-v1.md)의 형식을 그대로 사용한다.
metadata에는 큰 원 입력/결과 배열이나 파일 경로를 넣지 않는다.

| 필드 | 생성·대사 규칙 |
| --- | --- |
| schema_version/status/claim_scope | crop-cycle-result-v1 / stored_unpublished_research / synthetic_crop_math_only |
| tenant_id/study_id/revision | 실제 principal와 canonical 원 요청의 값 |
| farm | 현재 binding.request.farm의 scenario/revision/SHA와 binding.registration의 job ID |
| input_root_sha256 | 현재 binding.input.root_sha256와 원 progress의 동일 SHA |
| artifact | 원 terminal progress의 root/header/status/steps/planned/counts/commit/bytes/files를 그대로 대사; ref는 crop-cycle-artifact-v1:<root SHA> |
| binding | 정확한 서버 intent의 CycleFarmBinding bytes를 해석한 닫힌 object; canonical 재생성 값도 같아야 함 |
| policies | 정확히 input_rights_version/resolver_version/notice_sha256/server_progress |
| code | 정확히 storage_code_sha256/server_custody_code_sha256/schema_code_sha256/server_dependency_sha256 |
| result_id | result_id를 제외한 전체 canonical packet SHA 앞에 crop-cycle-result-v1:을 붙임 |

binding의 닫힌8개 필드는 version/scope/tenant_id/request/registration/input/rights_policy_version/
binding_code_sha256이다. 원 요청은 현재 binding._request로, 등록/입력/프로필/정책은 새 reader를 사용하는
현재 binding 검사와 정확히 대사한다. server_progress는 원 서버의 닫힌18개 progress를 그대로 보존한다.
input_rights_version은 binding.rights_policy_version, resolver_version은 서명 intent의 고정 판본,
notice SHA는 고정 bytes SHA다. server_dependency_sha256는 원 서버의 닫힌 dependency map과 같다.
code hash는 실제 module 파일/현재 import pin과 대사하며 단순한 사용자 선언으로 인정하지 않는다.

DB 서명은 `HMAC-SHA256(key, b'ossf-crop-cycle-result-v1\0' + payload_raw)`다.
원 server intent/HEAD 서명과 domain/key를 구분하고 compare_digest를 사용한다.
DB bytes/hash/signature·전체 canonical schema·result ID·모든 대응 column·registered_by authority를 대사한다.
valid HMAC로 다시 서명한 잘못된 payload도 schema/current binding/원 결과 대사에서 거부해야 한다.
recorded_at은 최초 DB 값이며 동일 retry로 갱신하지 않는다.

## 게시·철회·재시작

1. 현재 authority/WRITE_SCOPES와 선택 flag/grants를 검사한다.
2. 생성 없는 server._open의 원 reader/journal과 root/intent/writer lock을 유지한다.
   현재 계산/표시 권리를 `binding.current(..., write=True)`로 확인한다.
   원 journal의 실제 선택 proof/chain·header/context/terminal artifact와 progress를 검증한다.
3. 닫힌 packet을 구성하고 유한 예산을 검사한다. terminal completed와 numerical hold를 구분한다.
   numerical hold는 확인된 과거·실패 사유를 보존하며 성공 작기나 미래 상태를 만들지 않는다.
4. 기존 tenant/study/revision 방식의 nonblocking transaction advisory lock을 얻는다.
   `INSERT ... ON CONFLICT DO NOTHING` 뒤 같은 transaction의 별도 SELECT로 실제 행을 다시 읽는다.
   payload가 정확히 같으면 immutable retry이며 다른 의도/결과는 conflict다.
5. commit 직전 현재 farm/source/input·write scopes/권리를 다시 대사한다. 실패하면 rollback한다.
6. commit 뒤 현재 문맥을 다시 대사한 뒤 record를 반환한다. 직후 철회면 반환을 hold한다.
   이미 commit한 private 불변 audit row는 보존되지만 현재 조회·표시가 허용되었다고 보고하지 않는다.
   외부 정책 변경과 DB commit이 단일 원자 transaction이라고 주장하지 않는다.

get/page는 DB HMAC/닫힌 참조 검사 후 같은 private 서버 journal을 새로 연다.
현재 display 권리·원 binding/선택 progress를 반환 전후 대사한다. page는 stored progress를 원 journal.page에
전달해 조회마다 두 번 전체 service를 열지 않는다. RHS/advance/원 적분은 모두0회다.
code/key/정책·source/input·header/proof/root 변경과 혼합 참조는 hold다.
root와 DB advisory lock이 busy이면 빠른 pending이며 부분 게시/부분 결과를 반환하지 않는다.

DB lock은 transaction 종료 시 해제된다. advisory lock은 사용하는 코드의 협력 규칙이고
유일성/불변 trigger·HMAC/current checks와 함께 사용한다.
[PostgreSQL16 lock 문서](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS)를 근거로 한다.
Read Committed에서 DO NOTHING의 충돌 행이 INSERT snapshot에 보이지 않을 수 있으므로
한 INSERT RETURNING 결과만으로 존재/동일성을 판단하지 않는다.
[격리 문서](https://www.postgresql.org/docs/16/transaction-iso.html#XACT-READ-COMMITTED)와
[INSERT 문서](https://www.postgresql.org/docs/16/sql-insert.html#SQL-ON-CONFLICT)를 확인했다.
이는 본 계약의 설계 판단이며 실제 동시 게시 수용은 다음 SCRAM 시험으로 확인한다.

## 다음 한 단계의 수용 기준

1. 실제 SCRAM authority와 같은 등록 farm/root·terminal 서버 파일로 게시한다.
   DB 원 bytes/hash/signature/시각·원 페이지·같은 새 service/별도 Python 조회가 일치하고 조회 RHS0회다.
2. completed와 numerical hold 모두 저장하되 yielded/미생성/unsigned/외부 fabricated 결과를 게시하지 않는다.
   hold의 확인 과거와 실패 사유를 원 결과와 정확히 대사한다.
3. 동일 retry가 최초 ID/bytes/recorded_at/행 수를 보존한다. 다른 선언/농장/tenant/root·
   code/policy·부분 참조와 valid HMAC의 닫힌 schema 반례를 거부한다.
4. 원 payload·서명·DB column과 header/selected proof·입력 파일 변조를 각각 거부한다.
   오류 전후 crop row와 actual Run 수를 기록한다.
5. INSERT 뒤 commit 전의 실제 farm/source/input 철회는 rollback한다.
   commit 직후 철회는 private row1/조회·반환 hold이며 이전 row를 수정하지 않는다.
   실제 별도 connection의 advisory lock pending과 process 재시작 후 동일 읽기를 확인한다.
6. 현재 권한/flag/grants 변경과 다른 key/root/resolver를 거부하고 기존 v3/frozen49개 hash를 보존한다.
   실제 페이지 크기/시간과 metadata·FD/lock/temp/DB/roles/password·WSL 순차 자식 RSS 정리를 기록한다.
   HTTP/TLS30초와166일 실제 부하 수용은 이 시험으로 대체하지 않는다.

통과 전 parent crop-cycle-result-storage와 이번 checkbox는 열어 둔다.
준비/닫힌 참조1시간+실제 SCRAM 게시/철회/재시작·정리1–2시간의
**2–3집중시간/10월5–7일 KST 잠정**이다. 하루4시간 기준이며 CI/외부 자료 대기는 제외한다.
뒤 API/client → 같은 ID/UTC 성장3D → 작기 부하 → 생과/자원/Decimal 경제 순서를 유지한다.
실제 cultivar/forcing/초기/관리 채택·국내 독립 측정0건과 G0–G4·예측/추천 게시 보류를 유지한다.
