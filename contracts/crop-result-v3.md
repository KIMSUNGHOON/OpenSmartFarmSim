# 시작 유보 모델의 농장 결합 연구 저장 — v3

상태: **schema/role/config와 custody 로컬 수용**, 2026-10-05 KST.
[실제 SCRAM·분할 184개 검증](../research/crop-startup-storage-schema-implementation.md)을 확인한다.
[custody의 실제 SCRAM·119개 검증](../research/crop-startup-result-storage-implementation.md)을 확인한다.
API/새 3D는 미수용이다.
선행: [새 immutable artifact/reader 수용](../research/crop-startup-artifact-implementation.md).
기존 [v1](crop-result-v1.md)/[v2](crop-result-v2.md)와 G0–G4를 보존한다.
이 개발 CLI `gpt-6.1-sol / xhigh`에서 설계 판단하며 재귀 CLI는 실행하지 않는다.

## 작물 기능에 필요한 변경과 두 구획

기존 v2는 원 기관 모델/manifest와 artifact에 고정되므로 시작 유보를 반영한 새 bytes를
그 표에 넣거나 같은 모델로 조회할 수 없다. 이 누락을 해소하는 변경만 추가한다.
새 `crop_startup_research_results` 표와 기본 false의 명시적
`crop_startup_result_storage` 로그인 flag를 둔다. 기존 기록·권한은 자동 갱신하지 않는다.

1. **수용된 schema/role:** `backend/app/crop_startup_result_store.py`의 실제 installer,
   `backend/app/runtime_roles.py`, `backend/app/operator_config.py`와 기존
   `backend/tests/login_database.py`, `backend/tests/test_runtime_roles.py`,
   `backend/tests/test_operator_config.py`에 한정한다. 표/불변 trigger·제약·명시 grant와
   기본 false/누락 필드 호환을 실제 SCRAM으로 검증한다. 아직 custody 수용은 아니다.
2. **수용된 custody:** 같은 새 store 모듈의 실제 `StartupCropResultStore`와
   `backend/tests/test_crop_startup_result_store.py`를 연결한다. 아래의 계산/권리/HMAC·
   원자성/재시작/읽기를 실제 SCRAM으로 검증한 뒤에만 저장 작업을 체크한다.

schema 단계의 수용: 실제 provisioned 표의 tenant 포함 등록 job 외래키·bytes hash/크기·
판본/범위/ID 제약, owner UPDATE/DELETE 거부 trigger, authority SELECT/INSERT만 허용,
다른 세 role의 직접 SELECT/INSERT와 authority UPDATE/DELETE/TRUNCATE 거부를 확인한다.
False/누락은 새 grant를 만들지 않고 기존 grant 목록·operator 정책을 유지한다.
True의 새 허용과 잘못된 타입/과다 grant 거부·DB/password 정리와 기존 role/config 회귀를 기록한다.
사용자 산출물은 schema/권한 검증 기록이며 아직 계산 목록/API가 아니다.

## 입력·계산·현재 권리

`StartupCropResultStore(farms, growth_profile, cohort_profile, transport_profile,
notice_raw, *, program_rights, integrity_key)`는 기존 실제 FarmAuthoringService와 같은
명시 authority/SCRAM JobStore·고정 세 profile/notice·현재 program 권리 공급자·비밀
32 bytes 이상 HMAC 키를 받는다. 기존 변경 없는 farm/right 결합 검사를 재사용한다.

`put(tenant, request_raw)`의 닫힌 study_id/revision/farm/program/rights 입력·식별자/
권리 선언은 v2 계약을 따른다. canonical 프로그램 ≤1 MiB/요청 ≤2 MiB이며 원 결과/
계수/서명/tenant를 본문에 넣을 수 없다. 새 artifact factory가 서버에서 직접 계산한다.
모든 source input block은 synthetic이어야 하며 동일 ID의 다른 block을 거부한다.
50 N/C·명시 S/W1/RGR/forcing/관리 사건과 새 program/manifest·16누적/4수지를 보존한다.

현재 farm/crop/batch/zone·재배 면적·원천/등록 hash·작물 occupancy/농장 달력과 program
UTC 범위, 선언 available_at ≤ decision_at·권리 정책을 계산 전후/commit/반환에 재검사한다.
profile 적용성은 계속 `unvalidated_for_registered_crop`다. 기존 principal READ/WRITE
scopes와 `research_display`/`research_calculation` 목적 권리를 요구한다.
공급자 교체·늦은 권리/scope 철회는 저장/반환을 보류하고 부분 row를 남기지 않는다.
commit 직후에도 반환 전 현재 권리를 다시 검사한다. commit 전에 철회되면 거래를
롤백한다. commit 뒤 철회되면 완전한 불변 기록을 삭제하지 않고 반환을 보류하며,
권리가 회복되기 전까지 현재 검사를 통과하지 못한 결과를 표시하지 않는다.

계산은 HTTP handler 밖에서 수행한다. 이미 완료된 동일 원 요청의 재시도는 재계산 없이
읽고 다른 요청은 conflict, 잠긴 동일 intent는 pending이다. 새 정정은 새 revision이다.
이번 단계는 새 async 큐/작업자·계산 접수 API나 항상 켜진 서비스를 추가하지 않는다.

## 불변 저장과 reader

닫힌 `crop-result-v3` packet에 `stored_unpublished_research`/`synthetic_crop_math_only`,
tenant·정확한 원 요청·registration job/hash·farm/source binding·crop/batch/zone/floor
area/per_m2_floor·적용성·권리 정책/저장 코드/변경 없는 farm 검증 코드 hash를 묶는다.
새 artifact 객체와 그 canonical bytes hash를 보존한다. 입력 프로그램 hash와 artifact
파일 hash는 별개다. 실제 Run·gate 승인·생과 kg·추천을 추가하지 않는다.

전체 packet ≤20 MiB, `crop-result-v3:<sha256>`는 ID를 뺀 canonical packet hash다.
새 HMAC-SHA256 domain은 `ossf-crop-startup-research-custody-v3` 뒤 NUL이며 다른 저장
판본과 혼용하지 않는다. 키/credentials는 packet·공개 증거·로그에 넣지 않는다.
HMAC은 서버 custody 검사이며 독립 검토나 G0/G1/G4 승인이 아니다.
표는 tenant/study/revision 및 tenant/result ID 유일성·해시/제약·불변 trigger를 가진다.

`get(tenant, result_id, farm_ref)`는 현재 READ 권리와 같은 등록 참조를 검사하고
HMAC·행/packet/현재 코드/권리·artifact reader를 대사한다. 적분을 다시 실행하지 않는다.
미저장은 None, 혼합/변조/권리 철회는 hold/denied다. 조회에 저장 과거 외의 새 시점을 만들지 않는다.

## custody 수용과 후속 경로

- 실제 SCRAM에서 빈 초기/전량 제거 후 재유입·양의 tail 프로그램과 numeric hold를
  저장하고 fresh store/별도 Python 프로세스에서 같은 첫 시각/packet/artifact bytes를 읽는다.
- 동일/동시 재시도·conflict/새 revision·try-lock·원자 저장/rollback과 계산 중/commit 직전/
  읽기 중의 scope/원천/program 권리 철회·교체를 검증한다.
- 다른 tenant/farm/crop·기간/available_at·비합성/ID 충돌과 raw/행/HMAC/manifest/모델/
  원 요청·binding 변조를 거부하고 새 artifact의 입력/정책/코드·수지/hold를 그대로 보존한다.
- v1/v2의 기존 bytes/결과·기본 flag/grant를 보존하고 집중 farm/role/config 회귀와
  실제 DB/password 정리를 기록한다. 신뢰 hash/HMAC의 재작성은 데이터 승인으로 취급하지 않는다.

사용자 산출물은 farm/result ID·immutable packet/hash·UTC별 상태/누적/hold의 저장 검증이다.
그 뒤 별도 계약으로 **페이지 조회 API(현재 권리/TLS/30초 전체 본문) → 같은 저장 ID/UTC
표·그래프·50구획 성장 3D(원 수치/mesh·hold/취소/권리·WebGL 대체/실제 브라우저)**를 수용한다.
현재 기존 API/3D가 새 시작 모델을 보여 주는 것으로 표시하지 않는다.

## 작업량과 외부 의존성

기존 v2의 schema/권리 구현 약 40분과 실제 집중 시험 850.85초를 근거로 두 구획에
잠정 **2–4 집중시간**을 둔다: schema/role/config 0.5–1시간, custody 1–1.5시간,
독립 재시작/철회·회귀/정리/보고 0.5–1.5시간. 하루4시간 기준 목표는
**10월5–6일 KST**이며 실제 실패·CI/자료 상태로 수정한다. hosted 대기 시간은 별도다.
schema는 10월5일 KST에 새20개/기존 포함184개 고유 분할·실제 SCRAM/정리로 수용했다.
custody도 10월5일 KST에 새18개/집중119개·실제 SCRAM/6프로그램/별도 Python·commit 전후
철회/정리로 로컬 수용했다. schema만으로 부모를 체크하지 않고 두 구획의 증거를 대사했다.
다음 [페이지 API](api-crop-startup-replay-v1.md)는 잠정 **2–3 집중시간/10월5–6일 KST**다.
국내 독립 자료 0건·actual forcing/Run 0개, cultivar/초기/자동 S/W1/RGR·pre-onset·
전체 작기/생과 환산의 외부 의존성과 G0–G4 holds는 유지한다. 자료 확보는 개발과 병행한다.
예측/추천 완료 날짜를 이 소프트웨어 저장 추정으로 대신하지 않는다.
