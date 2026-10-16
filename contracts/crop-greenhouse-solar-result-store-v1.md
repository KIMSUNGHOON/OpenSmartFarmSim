# 현재 일사·환기 공동 계산 결과 등록과 현재 조회 v1

`SolarResultStore`는 [새 DB 계약](crop-greenhouse-solar-result-schema-v1.md),
[명시 authority 권한](crop-greenhouse-solar-result-roles-v1.md),
[서명된 서버 이력](crop-greenhouse-solar-server-custody-v1.md)을 사용한다.
정확한 새 결과 flag=True·authority·전체 grant 감사와 현재 농장/자료 권리가 필요하다.
기존 operator 판본의 누락/False 호환은 이 서비스를 활성화하지 않는다.

## 불변 결속

metadata는 128KiB 이하의 닫힌 canonical UTF-8 JSON이다.
tenant/study/revision·같은 농장의 scenario/crop/batch/zone·원 등록 job/SHA,
source/context/UTC/evidence/provenance·farm binding·intent/HEAD/proof/header/root,
원 terminal progress와 코드/정책 판본을 결속한다.
UTC는 원 6자리 마이크로초 문자열을 보존한다. 원 입력 범위는 0초 초과/600초 이하이다.
현재 서버 custody의 전체 서명 체인과 원 페이지/checkpoint를 재검사한다.

ID는 `joint-solar-result-v1:` 뒤 result_id를 제외한 canonical metadata의 SHA256이다.
DB HMAC은 별도 `ossf-joint-solar-result-v1\0` domain과 custody와 다른 32–4096byte key를 사용한다.
등록 잠금도 별도 domain의 tenant/study/revision 해시를 사용한다.
모든 SQL 참조 컬럼·payload SHA/HMAC·현재 authority를 대사한다.
원 progress는 별도 `progress_raw`/SHA로 최대128KiB를 그대로 저장한다. metadata의
`progress_sha256`와 내장 `policies.server_progress`의 canonical bytes가 그 원문과 같아야 한다.
HMAC/content ID에 이 SHA를 결속하고 출처 SHA·서명 custody 코드 SHA도 컬럼과 대사한다.
metadata·binding·progress의 `rights_or_gate_approval`은 모두 정확히 False다.
출처 available_at과 선언 권리 available_at은 원 농장의 decision_at 이전이어야 한다.
과거 판본의 서명 결과를 새 판본으로 자동 재서명하거나 이관하지 않는다.

## 등록과 실패

`put(tenant, request_raw)`는 이미 존재하는 completed/hold 원 root만 등록한다.
원 producer를 호출하거나 ready/yielded를 완료로 바꾸지 않는다.
실제 DB transaction의 try-advisory lock·INSERT·현재 권리 재검사를 사용한다.
잠금 중이면 Pending, 같은 판본의 다른 bytes/고유 intent 충돌이면 Conflict다.
같은 bytes 재시도는 잠금 안에서 기존 행을 대사하여 INSERT를 다시 시도하지 않고 최초 recorded_at을 보존한다. 실패 전후를 검사해 commit 전 철회는 rollback한다.
commit 뒤 철회는 이미 기록된 private 감사 행을 삭제하지 않으며 응답/후속 조회를 보류한다.
custody callback 안의 DB Pending은 파일 custody의 일반 Hold로 바뀌지 않도록 callback 밖으로 전달한다.

## 현재 조회

`get`, `page`, `summary`는 현재 같은 tenant/farm·자료 review/rights·계정·코드/정책을 확인한다.
선택된 원 progress와 원 artifact를 읽기 전후 대사한다. 다른 source/context/UTC/농장/HEAD/proof 혼합은 보류한다.
없는 ID는 권한 검사 후 None이다. 접근 불가/변조의 세부 원 입력은 오류에 노출하지 않는다.
`page`는 원 `{value,time}` 행을 반환하며 samples64/events8·응답2MiB 상한을 따른다.
`summary`는 원 terminal checkpoint/hold/last_confirmed/counts/times와 원 manifest/time binding을 반환한다.
조회 시 Context 생성·복원·RHS·PAR/NIR·환기·적분·관리 사건·새 UTC binding/행 생성은 실행하지 않는다.
선택되지 않은 파일을 추가해 저장량이 바뀌어도 등록 metadata를 수정하지 않는다. 기존 progress와 달라지면 보류한다.

## 수용 범위

실제 SCRAM 등록/재시도·별도 exec 원 bytes/최초 시각/페이지/UTC·조회 계산0,
기본 권한 거부·busy·충돌·rollback·현재/늦은 철회·변조/혼합·원 hold/기존 결과 공존·소유 정리를 검증한다.
실제 DB의 합성 농장 등록에 결속한 합성 32초 소프트웨어 결과이며 status는 stored_unpublished_research,
claim_scope는 synthetic_joint_solar_math_only, G0_G4는 not_assessed다.
실제 품종/한 작기/생산·자원 구매·마진/추천 관문을 통과한 결과가 아니다.
HTTP/API·같은 UTC 3D·사용자 계산 접수/실시간 U3는 후속이다.

## 호출자 transaction과 판본 경계

`_put_in_transaction(conn, tenant, request_raw)`는 서버 내부 context manager다.
정확한 열린 authority Connection·autocommit=False·INTRANS·실제 SCRAM/명시 endpoint/현재 grants를 검증한다.
내부 savepoint에서 같은 `_insert`를 사용하고, 호출자 기록 후의 권리를 다시 확인한 뒤 외부 거래가 commit한다.
idle/aborted/closed·admin/다른 runtime/다른 tenant를 거부한다. 호출자 오류/늦은 권리·권한·resolver 철회는 결과와 호출자 기록을 함께 rollback한다.
오류를 잡은 부모 거래는 계속 쓸 수 있고, context 뒤 외부 rollback도 결과를 되돌린다. 호출자 예외 객체와 최초 bytes/recorded_at을 보존한다.

기존22장부 joint/25장부 ventilation store/table/ID/HMAC/authority를 새41장부 solar 결과와 혼합하지 않는다.
코드 SHA는 원 metadata/ID/서명에 포함되며 다른 판본의 원 행을 자동 채택·갱신·재서명하지 않는다.
기존 source는 git 이력과 기동 frozen source로 보존한다. 현재 코드와 다른 hash의 원 결과는 해당 원 reader가 필요하다.
기존4표의 SQL 형식 fixture 행과 새 signed 결과의 공존·행 보존, 구 producer 정확한 타입/ID·별도 HMAC/lock domain 거부를 검증한다. 과거 signed 결과의 이관/재서명이나 그 원 reader 재검증을 뜻하지 않는다.
HTTP/worker/사용자 실행의 수용은 각각 후속이며 이 hook만으로 전체 제품 원자성을 주장하지 않는다.
