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
