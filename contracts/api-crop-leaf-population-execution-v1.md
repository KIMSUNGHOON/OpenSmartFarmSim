# 새 잎 계산의 보호 HTTP — v1

상태: 구현/검증 전. 선행은 [leaf E1–E3/자동 consumer](crop-leaf-population-execution-v1.md)다.
기존 인증/Scope·create_app의 선택적 service/query를 확장한다. 기본 비활성503이며 부분 조립은 거부한다.
같은 jobs/provider/admission/query·farm/parent graph를 요구한다. tenant는 서버가 결정한다.
leaf farm binding의 parent farm binding이 같은 FarmAuthoringService를 가리키는지 실제 객체로 확인한다.

| 방법/경로 | 결과 | 필수 Scope |
| --- | --- | --- |
| POST `/v1/crop-leaf-population-executions` | 202/queued JobStatus; 기존 consumer 계산 | simulation_create + 기존 crop WRITE_SCOPES |
| GET `/v1/jobs/{job_id}/crop-leaf-population-execution` | 현재 status/결과 식별자 | metadata/artifact + 기존 crop READ_SCOPES |
| GET 위 경로 + `/manifest` | 같은 완료 서명/원 manifest | 같은 읽기 Scope |
| GET 위 경로 + `/frames/{index}` | 같은 완료의 원 DTO/UTC·기관/면적 | 같은 읽기 Scope |
| GET 위 경로 + `/replay` | 현재 원12frame 묶음 | 같은 읽기 Scope |
| POST 위 경로 + `/cancel` | 실제 cancel_accepted/cancel_requested/JobStatus | metadata/cancel |

## 입력·출력과 재시도

닫힌 요청은 study_id/revision·farm/input/rights와 **parent job_id/result_sha256/numerical_root_sha256**이다.
Input source는 leaf-population-input-source-v1, rights는 leaf-population-input-rights-v1이다.
원 program/source/evidence bytes·키/tenant·임의 파일 경로는 받지 않는다. 원 입력은 trusted resolver에서 찾는다.
JSON64KiB와 중복 키/NaN/잘못된 UTF-8·추가 query/field를 거부한다.
같은 tenant/study/revision과 같은 원 요청은 최초 job/입력을 반환한다. 다른 내용은409 충돌이다.
현재 권한/권리가 철회되면 이전 접수의 성공으로 대체하지 않는다. 접수의 커밋 검증과 원 입력 보존을 유지한다.

조회/취소는 빈 body/query·canonical UUID, frame은0이상 정수 path만 허용한다.
응답은 기존 JobStatus 또는 닫힌 leaf-population-execution-read-v1 envelope다.
result 요약은 원 result/root/calculated_at·parent job/result/root/계산 시각·farm/입력/binding SHA와
profile_applicability=unvalidated_for_registered_crop, normalization=per_tracked_shoot를 유지한다.
manifest/frame/replay는 요청한 view만 제공하며 원 DTO·UTC/기관 ID/면적을 바꾸지 않는다.
응답 no-store·2MiB 상한이며 Scope/tenant·서비스 결속을 실행 전후 확인한다.

401 인증/만료,403 Scope,409 다른 의도,413 크기,415 media,422 입력/현재 자료 보류,
503 Pending/비활성/내부 오류는 기존 ErrorEnvelope/고정 공개 이유로 응답한다.
비밀·원 자료/키 경로·내부 오류 본문은 반환하지 않는다.
권리 철회 뒤 취소는 같은 tenant/stage/leaf 판본·원 job input을 확인해 허용하고 다른 모델은 거부한다.

## 수용 기준

1. 현재 기본 OpenAPI/Scope 지문을 먼저 기록하고 기존 경로/스키마 불변·새6경로/typed 계약·권한을 대사한다.
2. 미구성/부분/다른 graph를 거부하며 실제 인증 tenant/현재 Scope와 양쪽 자료의 권리/검토를 유지한다.
3. 실제 SCRAM/TLS에서 접수·동일 재시도/409·진행/원 완료 조회·원12frame/52면적/UTC·취소를 확인한다.
4. 늦은 인증 만료/권한·원본/부모 결속 변경과 실제 취소/전송 실패에서 결과를 잘못 반환하지 않는다.
5. 조회의 관련 생장/CLI·지속 SQL/파일쓰기0·원 결과/행·두 미리보기/WSL 상한·소유 정리를 확인한다.
6. 내부 조회26–29초가 관측되어 기존 클라이언트30초와 가깝다. 실제 요청부터 응답까지 실측해 예산 안에
   처리됨을 확인한다. 현재성 검사 생략이나 임의 timeout 증가로 통과를 대신하지 않는다.

이후 명시 runtime/자동 consumer 조립→strict SDK/같은 job의3D·메뉴/reload 복원·실제 브라우저를 검증한다.
이 계약 작성은 HTTP 기능 수용이 아니다. 합성 연구 범위를 유지하며 실제 품종/농장·생산/마진·추천·G0–G4와 구분한다.
