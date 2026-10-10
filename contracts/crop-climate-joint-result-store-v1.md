# 공동 작물·기후 결과 등록과 현재 조회 v1

`JointCropClimateResultStore`는 [새 DB 계약](crop-climate-joint-result-schema-v1.md),
[명시 authority 권한](crop-climate-joint-result-roles-v1.md),
[서명된 서버 이력](crop-climate-joint-server-custody-v1.md)을 사용한다.
정확한 새 결과 flag=True·authority·전체 grant 감사와 현재 농장/자료 권리가 필요하다.
기존 operator 판본의 누락/False 호환은 이 서비스를 활성화하지 않는다.

## 불변 결속

metadata는 128KiB 이하의 닫힌 canonical UTF-8 JSON이다.
tenant/study/revision·같은 농장의 scenario/crop/batch/zone·원 등록 job/SHA,
source/context/UTC/evidence·farm binding·intent/HEAD/proof/header/root,
원 terminal progress와 코드/정책 판본을 결속한다.
UTC는 원 6자리 마이크로초 문자열을 보존한다. 원 입력 범위는 0초 초과/600초 이하이다.
현재 서버 custody의 전체 서명 체인과 원 페이지/checkpoint를 재검사한다.

ID는 `joint-crop-climate-result-v1:` 뒤 result_id를 제외한 canonical metadata의 SHA256이다.
DB HMAC은 별도 `ossf-joint-crop-climate-result-v1\0` domain과 custody와 다른 32–4096byte key를 사용한다.
등록 잠금도 별도 domain의 tenant/study/revision 해시를 사용한다.
모든 SQL 참조 컬럼·payload SHA/HMAC·현재 authority를 대사한다.
과거 판본의 서명 결과를 새 판본으로 자동 재서명하거나 이관하지 않는다.

## 등록과 실패

`put(tenant, request_raw)`는 이미 존재하는 completed/hold 원 root만 등록한다.
원 producer를 호출하거나 ready/yielded를 완료로 바꾸지 않는다.
실제 DB transaction의 try-advisory lock·INSERT·현재 권리 재검사를 사용한다.
잠금 중이면 Pending, 같은 판본의 다른 bytes/고유 intent 충돌이면 Conflict다.
같은 bytes 재시도는 최초 recorded_at을 보존한다. 실패 전후를 검사해 commit 전 철회는 rollback한다.
commit 뒤 철회는 이미 기록된 private 감사 행을 삭제하지 않으며 응답/후속 조회를 보류한다.
custody callback 안의 DB Pending은 파일 custody의 일반 Hold로 바뀌지 않도록 callback 밖으로 전달한다.

## 현재 조회

`get`, `page`, `summary`는 현재 같은 tenant/farm·자료 review/rights·계정·코드/정책을 확인한다.
선택된 원 progress와 원 artifact를 읽기 전후 대사한다. 다른 source/context/UTC/농장/HEAD/proof 혼합은 보류한다.
없는 ID는 권한 검사 후 None이다. 접근 불가/변조의 세부 원 입력은 오류에 노출하지 않는다.
`page`는 원 `{value,time}` 행을 반환하며 samples64/events8·응답2MiB 상한을 따른다.
`summary`는 원 terminal checkpoint/hold/last_confirmed/counts/times와 원 manifest/time binding을 반환한다.
조회 시 Context 생성·복원·RHS·적분·관리 사건·새 UTC binding/행 생성은 실행하지 않는다.
선택되지 않은 파일을 추가해 저장량이 바뀌어도 등록 metadata를 수정하지 않는다. 기존 progress와 달라지면 보류한다.

## 수용 범위

실제 SCRAM 등록/재시도·별도 exec 원 bytes/최초 시각/페이지/UTC·조회 계산0,
기본 권한 거부·busy·충돌·rollback·현재/늦은 철회·변조/혼합·원 hold/기존 결과 공존·소유 정리를 검증한다.
실제 농장 fixture에 결속한 합성 32초 소프트웨어 결과이며 status는 stored_unpublished_research,
claim_scope는 synthetic_joint_crop_climate_math_only, G0_G4는 not_assessed다.
실제 품종/한 작기/생산·자원 구매·마진/추천 관문을 통과한 결과가 아니다.
HTTP/API·같은 UTC 3D·사용자 계산 접수/실시간 U3는 후속이다.

## E3 호출자 거래에 결속한 등록 — 2026-10-10

[거래 hook 검증](../research/crop-climate-joint-result-transaction-implementation-20261010.md)을 수용했다.
`_put_in_transaction(conn, tenant, request_raw)`는 서버 내부 context manager다.
호출자는 기존 jobs.connect의 authority 연결에서 외부 transaction을 먼저 시작하고,
context 안에서 반환 record를 사용하는 작업 완료/게시 기록을 같은 conn에 작성한다.
context 종료의 현재 권리 검사가 끝난 뒤 외부 transaction을 commit한다.
실제 worker 결속은 [E4 수용](../research/crop-climate-joint-execution-worker-implementation-20261010.md)으로 검증했다.
hook 종료 뒤 같은 외부 거래에서 현재 실행 권리/입력·임대를 확인하고 마지막 fence로 terminal 상태를 갱신한다.

연결은 열린 정확한 psycopg Connection, autocommit=False, INTRANS여야 한다.
SCRAM session/current authority·DB·명시 endpoint와 현재 runtime grants를 다시 검사한다.
idle/aborted/closed·admin/다른 runtime role·다른 tenant를 허용하지 않는다.
내부 savepoint를 사용하므로 hook은 외부 transaction을 commit하거나 닫지 않는다.
context 안의 호출자 오류와 최종 권리 거부는 결과와 그 savepoint 안의 호출자 기록을 함께 되돌린다.
호출자가 오류를 잡아 외부 거래를 계속해도 부분 결과는 남지 않는다. 호출자 예외 객체는 보존한다.
context 뒤 외부 거래가 실패해도 결과는 외부 rollback에 포함된다.

기존 put과 새 hook은 같은 `_insert`를 사용한다. 원 packet 생성/검증, try-advisory lock,
HMAC/참조 컬럼 대사·충돌·INSERT 뒤 현재 권리 검사는 공유한다.
기존 put의 commit 뒤 재검사도 유지한다. 새 hook은 yield 뒤 호출자 기록까지 작성한 시점에
권리를 재검사한다. 권리 저장소와 DB 전체의 전역 원자 snapshot을 뜻하지 않는다.
completed/hold의 원 terminal 값과 같은 입력 재시도의 최초 bytes/recorded_at을 보존하며 계산은 하지 않는다.

### 코드 판본 경계

SQL/wire schema와 result ID prefix는 joint-crop-climate-result-v1을 유지한다.
새 storage_code_sha256은 원 code 객체와 result ID 해시에 포함되므로 별도 저장 코드 판본이다.
이전 결과 bytes/HMAC/recorded_at을 갱신하거나 새 코드로 재서명하지 않는다.
현재 reader와 두 writer는 이전 code pin을 보류하며 기존 intent를 자동 채택하지 않는다.
이전 reader 전체 source는 git23b9da42f2bce869bab1106bdb53a848650b3f54에 보존돼 있다.
그 storage source의 SHA256은87e7e10e8d3476e437f5fec55f0cbc1ab03026a62a62019332ad5f0eab30538c이며,
실제 SCRAM 행에서 원 reader의 동일 bytes/시각 재조회를 검증했다. 새 코드와 구형 결과를 암묵적으로 혼합하지 않는다.

신규10/기존9개 집중 검사는 완료/hold·동일 최초 값·외부 commit/rollback·savepoint 복구,
늦은 권리/권한/resolver 변경과 원 판본 보존을 다룬다. 입력·모델·기존 UI/원본은 보존한다.
worker/API/UI 자동 연동·전체 작기·실제 자료와 관문은 이번 수용 범위에 포함하지 않는다.
