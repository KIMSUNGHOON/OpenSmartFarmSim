# 일사 공동 계산 결과 DB 계약 v1

`joint-solar-result-v1`은 [서명 이력](crop-greenhouse-solar-server-custody-v1.md)과
[불변 저장](crop-greenhouse-solar-storage-v1.md)의 참조 metadata와 원 진행 bytes를
보존한다. provisioner가 `install_joint_solar_result_schema(conn, schema)`로
`crop_greenhouse_solar_research_results`를 원자 설치한다. 재설치는 실패하며 기존
결과 표·모델·권한을 변경하지 않는다. runtime opt-in 권한과 등록/조회는 후속이다.

## 두 원문과 식별자

`payload_raw`와 `progress_raw`는 각각 UTF-8 JSON1–131,072bytes다. 각각의
`payload_sha256/progress_sha256`는 원 bytea SHA256과 같아야 한다. 공백을 포함한
원 bytes를 보존한다. 중첩/유니코드 별칭을 포함한 중복 JSON 키를 거부한다.

metadata top keys는 `schema_version,status,claim_scope,G0_G4,result_id,tenant_id,
study_id,revision,farm,input,artifact,binding,policies,code,rights_or_gate_approval,
progress_sha256`다. `status=stored_unpublished_research`,
`claim_scope=synthetic_joint_solar_math_only`, `G0_G4=not_assessed`,
`rights_or_gate_approval=false`를 고정하고 원 progress hash를 묶는다.

| 닫힌 객체 | 필수 키 / 대응 컬럼 |
| --- | --- |
| farm | scenario_id, scenario_revision, registration_job_id, registration_sha256, crop_id, batch_id, zone_id |
| input | program_id, source_sha256, context_sha256, time_binding_sha256, evidence_sha256, provenance_sha256, start_utc, end_utc |
| artifact | ref→artifact_ref, sha256→artifact_sha256, header_sha256→artifact_header_sha256, status→artifact_status; intent_sha256, farm_binding_sha256, head_sha256, proof_sha256; 아래 정수7개 |

`binding/policies/code`는 객체여야 한다. `code.server_custody_code_sha256`는
새 `custody_code_sha256` 컬럼과 같아야 한다. 모든 SHA/서명은 소문자64hex다.
ID는 기존 ASCII200자 규칙을 따른다. `result_id=joint-solar-result-v1:<SHA256>`,
artifact ref는 실제 판본 `joint-solar-ventilation-storage-research-v1:<SHA256>`다.
새 result/storage/custody 판본·context/custody code SHA가 모델 계열을 결속한다.
상세 model/profile identity는 binding에 포함하며 후속 store가 검증한다.

## 원 progress와 컬럼 대사

progress의 닫힌26keys는 `version,scope,G0_G4,rights_or_gate_approval,
intent_sha256,binding_sha256,source_sha256,context_sha256,time_binding_sha256,
provenance_sha256,custody_code_sha256,head_sha256,proof_sha256,header_sha256,
artifact_sha256,status,commit_count,steps,planned_steps,counts,checkpoint,
last_confirmed,hold,times,storage_bytes,file_count`다.
version은 `joint-solar-server-custody-v1`, scope/관문/권리 승인 여부는 metadata와
같다. 모든 핵심 hash/status와 정수는 대응 컬럼과 같아야 한다.
`counts`는 정확히 `samples,events`를 가지며 sample_count/event_count에 대응한다.
times는 객체, checkpoint/last_confirmed/hold는 객체 또는 null이다.

상태/장부/수지의 상세 단위·UTC 배열·checkpoint 의미, canonical JSON,
result ID 내용 해시·HMAC·원 artifact 및 현재 농장/자료 권리는 후속 store가
검증한다. DB의 일치/hash 검사는 인증·과학적 타당성·관문 승인이 아니다.

| 정수 | 범위 |
| --- | --- |
| steps / planned_steps | 0–4096 /1–4096; steps≤planned_steps, completed면 같음 |
| sample_count / event_count | 0–512 /0–128 |
| commit_count | 1–4097 |
| storage_bytes / file_count | 1–536,870,912 /1–65,536 |

양쪽 원문 정수의 텍스트도 컬럼과 같아야 한다. 소수/지수/bool/문자열을
정수로 변환하지 않는다. start_utc/end_utc는 원 마이크로초6자리 UTC 문자열,
유효 달력과 `0 < end-start <= 600seconds`를 요구한다. 요청 구간 종료와
hold의 마지막 확정 시각을 같다고 주장하지 않는다. 전체 작기 확장은 별도다.

## 불변성·권한·수용

PK는 `(tenant_id,study_id,revision)`, 고유 키는 `(tenant_id,result_id)`와
`(tenant_id,intent_sha256)`다. `(tenant_id,registration_job_id)` FK는 기존 jobs의
같은 tenant 작업 존재만 증명한다. 실제 등록 작업/hash/crop 적용성은 store 책임이다.
UPDATE/DELETE trigger가 행 변경을 거부하고 recorded_at은 DB가 기록한다.
PUBLIC 권한은 회수하며 runtime grant를 추가하지 않는다. owner/provisioner의
DDL/TRUNCATE는 이 행 trigger의 범위 밖이다.

실제 SCRAM에서 두 원문/모든 컬럼/정확한 크기 상한, 이전 표3개 공존/행 보존,
metadata/progress 해시·핵심 pin/닫힌 JSON/타입/숫자 표기/중복 키·UTC/고유 키/FK,
수정/재설치 거부와 설치 rollback, runtime4역할20작업 접근 거부를 확인한다.
[캡처한 합성 progress](../fixtures/synthetic-solar-custody-progress-v1.json)는 실제
기존 producer 출력의 DB 원문 보존을 시험하며 서명된 실제 농장 등록/G0–G4나
농작물 생산을 증명하지 않는다. schema 작업은 계산·복원·CLI를 실행하지 않는다.
