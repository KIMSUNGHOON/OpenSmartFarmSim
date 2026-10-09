# 공동 작물·기후 결과 DB 계약 v1

`joint-crop-climate-result-v1`은 [새 서버 서명 이력](crop-climate-joint-server-custody-v1.md)과
[불변 페이지 저장](crop-climate-joint-storage-v1.md)의 **불변 참조 metadata**다.
provisioner가 `install_joint_crop_climate_result_schema(conn, schema)`로 새
`crop_climate_joint_research_results` 테이블을 원자 설치한다. 재설치는 실패하고 기존 행을 보존한다.
이전 작물 결과 테이블·모델 판본·권한을 변경하지 않는다.

## 원 bytes와 컬럼

UTF-8 `payload_raw`는 1–131,072bytes이며 원 SHA-256과 함께 저장한다. 최상위 키는
`schema_version/status/claim_scope/G0_G4/result_id/tenant_id/study_id/revision/farm/input/artifact/binding/policies/code`다.
`status=stored_unpublished_research`, `claim_scope=synthetic_joint_crop_climate_math_only`,
`G0_G4=not_assessed`를 고정한다. JSON 객체의 중복 키는 중첩 위치에서도 거부한다.

| 닫힌 객체 | 필수 키 / 대응 컬럼 |
| --- | --- |
| farm | scenario_id, scenario_revision, registration_job_id, registration_sha256, crop_id, batch_id, zone_id |
| input | program_id, source_sha256, context_sha256, time_binding_sha256, evidence_sha256, start_utc, end_utc |
| artifact | ref→artifact_ref, sha256→artifact_sha256, header_sha256→artifact_header_sha256, status→artifact_status; intent_sha256, farm_binding_sha256, head_sha256, proof_sha256; 아래 정수 7개 |

위 객체의 키·문자열 형식·원 JSON 값과 컬럼을 대사한다. `binding/policies/code`는 객체여야 한다.
이 세 객체의 상세 의미·canonical JSON·결과 ID의 내용 해시·HMAC·원 파일 및 현재 권리 검사는 후속 store가 맡는다.
DB의 SHA 대사만으로 서명·자료 진실성·모델 타당성이 입증되지는 않는다.

`result_id=joint-crop-climate-result-v1:<64 lowercase hex>`이며 artifact 참조는 실제 새 저장 판본인
`joint-crop-climate-storage-research-v1:<artifact_sha256>`다. 모든 SHA/서명 컬럼은 정확한 소문자 64자리다.
식별자는 기존 서버 식별자 범위 `[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}`를 따른다.

`start_utc/end_utc`는 마이크로초 6자리의 `YYYY-MM-DDTHH:MM:SS.ffffffZ` 문자열 그대로 보존한다.
유효한 달력·UTC와 `0 < end-start <= 600 seconds`를 검사하며 반올림하지 않는다.
이는 요청된 계산 구간이다. hold의 마지막 확정 시각은 이 종료 시각과 같다고 주장하지 않는다.

| 정수 | 범위 |
| --- | --- |
| steps / planned_steps | 0–4096 / 1–4096; steps≤planned_steps; completed이면 같음 |
| sample_count / event_count | 0–512 / 0–128 |
| commit_count | 1–4097 |
| storage_bytes / file_count | 1–536,870,912 / 1–65,536 |

원 JSON 숫자의 텍스트도 정수 컬럼과 같아야 한다. 소수·지수 표기·bool·문자열을 정수로 바꾸지 않는다.
이 상한은 [현재 짧은 공동 계산](crop-climate-joint-boundary-driver-v1.md)의 소프트웨어 범위다.
전체 작기나 다른 forcing으로 확장하려면 해당 계산/저장 계약과 DB 판본을 먼저 검토한다.

## 테넌트·불변성·권한

기본 키는 `(tenant_id,study_id,revision)`이다. `(tenant_id,result_id)`와 `(tenant_id,intent_sha256)`도 고유하다.
`(tenant_id,registration_job_id)`는 기존 jobs를 참조한다. 이 FK는 같은 테넌트의 작업 존재만 증명한다.
실제 농장 등록 작업·원 등록 hash·crop/batch/zone·작기 적용성은 현재 FarmAuthoringService와 후속 store가 확인한다.

행 UPDATE/DELETE는 trigger가 거부한다. `recorded_at`은 DB가 기록한다. PUBLIC 권한을 회수하며
runtime grant는 이 설치 함수에서 추가하지 않는다. 명시 opt-in 역할은 다음 자식 작업이다.
schema owner/provisioner의 DDL·TRUNCATE 권한은 이 행 trigger의 통제 범위가 아니다.

## 수용 범위

실제 SCRAM PostgreSQL에서 원 bytes/모든 컬럼, 이전 결과 공존, UTC 마이크로초/달력,
중복·닫힌 JSON/숫자 표기·상한·SHA·같은 테넌트 FK·고유 의도·수정 거부와 소유 정리를 검증한다.
fixture는 schema만 시험하는 합성 작업이며 실제 농장 등록·생산 Run·G0–G4 승인 증거가 아니다.
새 store/역할/API/3D/U3와 실제 품종·현장 검증은 후속이다.
