# 기관/과실 구획의 농장 결합 연구 저장 — v2

상태: **다음 구현의 계약; 실제 DB 저장은 미수용**.
선행은 [coupled artifact](crop-coupled-artifact-v1.md)의 로컬 수용이다.
이 개발 CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는 실행하지 않는다.
[v1](crop-result-v1.md)과 G0–G4 관문을 유지한다.

## 작물 핵심 경로에 필요한 추가 범위

현재 `crop_research_results`는 `crop-result-v1`과 단일 프로필/적분 manifest에
고정된다. 새 50구획 artifact를 넣거나 조회할 수 없다. 이 누락만을 근거로
`crop_coupled_research_results` 표 하나와 명시적인 기본 false 로그인 flag
`crop_coupled_result_storage`를 추가한다. 기존 정책/테이블/자료는 자동 갱신하지 않는다.
authority의 SELECT/INSERT만 허용하고 다른 role의 직접 접근과 UPDATE/DELETE/
TRUNCATE를 거부한다. 새 큐/Compose/항상 켜진 서비스는 이 단계에 추가하지 않는다.

예정 핵심 변경은 `backend/app/crop_coupled_result_store.py`,
`backend/tests/test_crop_coupled_result_store.py`, `backend/app/runtime_roles.py`,
실제 test provisioning의 `backend/tests/login_database.py`와
`backend/tests/test_runtime_roles.py`다. 계약/실제 검증 보고서는 구현과 함께 보존한다.

## 저장의 입력과 계산

`CoupledCropResultStore(farms, growth_profile, cohort_profile, transport_profile,
notice_raw, *, program_rights, integrity_key)`는 실제 FarmAuthoringService와 같은
authority/SCRAM JobStore·고정 세 profile/notice·현재 프로그램 권리 제공자와
32 bytes 이상 비밀 HMAC 키를 받는다. profile 적용성은
`unvalidated_for_registered_crop`다. 기본 허용/권리 캐시/가짜 G0 승인은 없다.

`put(tenant, request_raw)`는 v1과 같은 닫힌 study_id/revision/farm/program/rights
입력이다. program은 artifact 계약의 다섯 필드와 명시적인 초기 50 N/C,
forcing·RGR/S/W1·관리 사건을 포함한다. 호출자가 결과/계수/서명/tenant를 본문에
넣을 수 없다. canonical 프로그램은 1 MiB 이하, 전체 요청은 **2 MiB** 이하다.
다른 모형의 program, reference_observation 입력, 단위·시점/예산·서로 다른 동일
input_id는 계산 전에 거부한다. 식별자/권리 선언은 v1의 규칙을 따른다.

등록 farm/crop가 실제 존재하고 전체 UTC 구간이 작물 occupancy와 농장 KST 기간에
들어가야 한다. 선언 available_at은 farm decision_at보다 늦을 수 없다.
현재 원천·등록 hash와 program 권리를 계산 전후·commit/반환 전에 다시 확인한다.
쓰기에는 `research_calculation`/`research_display`, 읽기에는 `research_display`가 필요하다.
principal scopes는 기존 farm READ와 `crop_result_read`, 쓰기에는 추가
`crop_result_write`다. 별도 DB flag는 v1 테이블의 권한을 자동 부여하지 않는다.

put은 public artifact builder로 서버에서 계산한다. 이 **약 59초의 동기 계산
메서드를 HTTP handler에 연결하지 않는다**. operator/후속 계산 작업은 요청 처리
밖에서 실행하며 완료된 저장 조회만 새 API에 연결한다. 실제 보류도 보존하고
미확인 출력/작기를 채우지 않는다. 이번 저장 수용은 새 async 접수/worker의 수용이 아니다.

## 불변 packet과 custody

닫힌 `crop-result-v2` packet에 tenant·정확한 원 요청, registration job/hash·
farm/source binding hash, crop/batch/zone/floor area/per_m2_floor·적용성,
권리 정책 판본/저장 코드 hash와 **artifact 객체·그 canonical bytes hash**를 묶는다.
`stored_unpublished_research`/`synthetic_crop_math_only`를 유지한다. artifact 원
canonical bytes는 packet에서 같은 규칙으로 재생되며 두 raw 입력 hash를 혼용하지 않는다.
Run/게시/검증 서명·실제 품종/생과 환산은 넣지 않는다.

전체 packet 상한은 **20 MiB**다. `crop-result-v2:<sha256>`는 ID를 제외한
packet의 canonical bytes hash다. payload bytes hash와 별도 domain의 HMAC-SHA256을
저장한다. 키/credentials/raw restricted source는 packet·보고·로그에 넣지 않는다.
HMAC은 custody 검사이며 독립 심사나 G1/G4 승인이 아니다.

표는 tenant/study/revision 유일성과 tenant/result ID 유일성, tenant 포함 등록
job 외래키, bytes hash·크기·schema/scope/ID 검사와 UPDATE/DELETE 거부 trigger를 가진다.
같은 intent의 거래 잠금은 기존 try-lock 패턴으로 pending을 반환한다. 정확히 같은
원 요청만 같은 첫 DB 시각/packet을 재사용하고 다른 요청은 conflict다. 새 정정은
새 revision이다. 실패/늦은 권리 변경은 rollback한다. 재시도는 이미 완료된 결과를 재계산하지 않는다.

## 조회와 이후 3D

`get(tenant, result_id, farm_ref)`는 정확한 farm 참조와 현재 READ 권리를 요구한다.
미저장은 None이며 혼합·변조·권리 철회·현재 profile/code/연결 불일치는 hold/denied다.
HMAC와 행/packet·farm binding을 검증한 뒤 artifact reader로 현재 형식/수지를
대사한다. 적분을 다시 실행하지 않는다. 새 API는 이것을 최대 출력/사건 페이지로
제한하고 실제 HTTPS 전체 본문 30초를 별도 검증한다. API 수용 뒤 같은 저장
result ID·UTC sample·단위와 hold의 표/그래프/50구획 3D를 연결한다.

## 다음 한 단계의 수용 기준

1. 실제 SCRAM 연결에서 두 참조 사례와 numeric hold를 불변 저장하고 fresh store/
   별도 Python 프로세스·서비스 재시작에서도 동일 canonical artifact/packet/hash를 읽는다.
2. 현재 farm/crop/batch/zone·등록/source hash·권리 정책·model/profile/policy/code/
   solver·입력/결과 hash가 한 packet에 묶임을 확인한다. 실제 Run/G1 데이터는 생성하지 않는다.
3. 동일/동시 재시도·conflict/new revision·진행 중 try-lock·원자 저장/rollback을 확인한다.
4. 다른 tenant/farm/program·미존재 crop/기간/available_at·비합성 입력·원문/행/서명/
   모델 변조를 거부한다. 계산 중/commit 직전/조회 중 scope·원천/program 권리 철회도 거부한다.
5. v1과 기본 flag=False의 기존 grant 목록을 보존한다. 다른 3 role의 SELECT/INSERT,
   authority의 UPDATE/DELETE/TRUNCATE, owner의 UPDATE/DELETE 거부를 실제 DB에서 확인한다.
6. 집중 수용/기존 farm·role 회귀, 실제 파일/hash·DB와 password 파일의 정리를 보고한다.
   HTTPS/브라우저·전체 작기/실제 품종/G0–G4는 별도 미수용으로 남긴다.

## 작업량과 외부 자료

v1의 관측된 약 44분 계약/구현·SCRAM 검증과 새 artifact 검사를 근거로
권리 결합/새 표·role/거래/실제 재시작·변조/정리의 네 묶음에 **집중 개발·검증
2~4시간**을 잠정 배정한다. 하루 4시간 순차 작업이면 0.5~1작업일이며 로컬
수용 시도는 2026-10-05~06 KST다. 실제 실패 진단 후 갱신하고 hosted 전체 CI는 별도 기록한다.
국내 미사용 독립 자료 0건과 실제 reference 입력/품종·startup/cycle holds는 유지한다.
자료 확보는 개발과 병행하며 전체 생산 예측/추천·production 완료 날짜를 이 추정으로 대신하지 않는다.
