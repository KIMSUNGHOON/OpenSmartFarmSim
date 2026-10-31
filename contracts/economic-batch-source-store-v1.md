# 소유 생산 batch/schema4 입력 저장 v1

[EconomicBatchSourceStore](../backend/app/economic_batch_source_store.py)는
[미수확 기간 비용 커널](economic-production-batches-v1.md)의 사용자 가정 입력을
실제 불변 작업 입력에 결속하는 PostgreSQL 저장소다. 새 제품 HTTP/worker/UI는 아직 조립하지 않았다.

## 명시적 활성화와 기존 경계

`RuntimeLoginPolicy.economic_batch_source_storage`는 기본 false이며 명시 JSON boolean만 받는다.
true에는 기존 `market_calculation`/`market_source_storage`가 필요하다.
운영 설정에서도 생략/false는 기존 경계이고 잘못된 값은 dependency factory 전에 거부한다.
새 테이블 설치·권한 설정은 trusted provisioner가 선택한 새 프로필에서만 수행한다.
이번 변경은 기존 운영 설정/DB/서비스를 자동 전환하지 않는다.

`economic_batch_source_records`와 별도 immutable trigger/function을 설치한다.
정책 판본은 활성화 때 `runtime-economic-batch-source-login-policy-v9`다.
authority에 해당 테이블 SELECT/INSERT만 허용하며 UPDATE/DELETE/DDL·grant option은 허용하지 않는다.
request/worker/supervisor 프로필은 새 테이블을 읽을 수 없다. 원 권한 감사 전체를 재사용한다.

기존 `market_source_records`, source-v1의7종·schema3 등록/목록과 기본 정책은 유지한다.
기존 등록·검증 엔진의 model/version/table 선택 지점과 DDL 생성을 공유하며 두 번째 등록 엔진을 만들지 않는다.
새 source 판본은 `economic-batch-user-source-v1`이고 실제 테이블/버전이 원 source와 분리된다.

## 자료 종류와 입력

새 저장소는8종을 받는다. `economic_scenario`만 schema4로 지정하고 `production_batch`를 추가한다.
`economic_input`, `joint_shock`, `input_rights`, `settlement_applicability`,
`settlement_evidence`, `prior_batch_cost`는 기존 typed 모델이다.
scope 검사는 별도 `economic_batch_source_read`/`economic_batch_source_write`를 사용한다.
원 market_source scope만으로 새 자료를 읽거나 등록하지 않는다.

모든 원문은 실제 같은 tenant의 collection/simulation 작업에 저장된 canonical JSON bytes여야 한다.
자료는 기존 JobStore 입력 한도인 **64KiB**를 따른다. 독립 계산 커널의2MiB 상한을
이 등록 경로의 한도라고 표시하지 않는다. ID/revision은 기존200자 한도를 유지한다.
tenant·kind/model·ID/revision·canonical bytes/SHA·실제 작업 입력/지문·서버 DB actor를 검증한다.
연구/잘못된 stage, 미지 필드·비정규/변조 원문, 다른 tenant·판본/권한은 거부한다.
schema4의 시장 문맥은 첫 조건부 경로의 unavailable만 허용한다.

이것은 typed 사용자 가정의 등록이다. 개별 record가 등록됐다고 관련 입력의 완전성,
미래 적용성·batch/비용 기간 일치나 실제 농장/구매량이 승인된 것은 아니다.
계산 전 커널이 원 숫자/소유 batch·기간/decision_at와 현재 서명 문맥을 다시 검증한다.

## 등록·조회·수정

`adopt_job(tenant, kind, job_id)`는 source 원문과 최초 작업 참조·actor·recorded_at을 저장한다.
같은 tenant/kind/ID/revision의 동일 bytes 재시도·동시 요청은 같은 기록을 반환한다.
같은 bytes의 다른 작업으로 재시도해도 최초 참조/시각을 교체하지 않는다.
다른 bytes는 conflict이며 부분 실패/늦은 쓰기 권한 철회는 트랜잭션을 rollback한다.
정정은 새 revision으로 등록한다. DB도 source UPDATE/DELETE와 raw SHA 불일치를 차단한다.

`get_production_batch`, `get_economic_scenario`, `get_economic_scenario_pin`과 기존 종류별 getter는
새 테이블의 현재 tenant/권한·원문/작업 지문을 검증해 독립 typed dict를 반환한다.
scenario pin의 immutable_job_input_ref는 실제 최초 작업 UUID이고 두 SHA는 실제 원 입력 지문이다.
한글 식별자도 같은 UTF-8 canonical bytes/SHA를 사용한다.
초기 권한 부재/없는 참조는 null이고, 진행 중 읽기 권한/tenant 변경은 반환을 차단한다.
조회는 경제/작물 계산이나 source 수정·실행을 하지 않는다.

`get_user_source`/`list_user_sources`는 원과 같은 metadata 형식이며 목록은 최대50개/커서다.
새 저장소 조회는 기존 테이블의 자료를 새 판본으로 자동 해석하거나 원 목록에 섞지 않는다.
caller-owned transaction의 내부 등록은 호출 서버가 전체 거래를 rollback/commit해야 한다.

## 검증과 주장

실제 PG16.15/SCRAM·원7종 회귀·현재/늦은 scope/충돌/동시 재시도/rollback·SQL 불변/권한,
운영 설정/원 역할 감사·별도 fresh reader와 실제 서명 hold의 계산 연결을 검증한다.
[실제 수용 결과](../research/economic-batch-source-store-20261031.md).
모든 사례는 자체 합성 조건부 QA다. 실제 농장/자료·계수·요금 채택과 G0–G4/R2 평가는 없다.
제품 factory의 source/hold 권한 결속·접수/worker·결과 저장/SDK/3D는 후속 수용이다.
