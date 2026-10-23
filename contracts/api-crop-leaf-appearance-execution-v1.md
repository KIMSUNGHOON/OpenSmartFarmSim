# 자동 출현 계산의 보호 HTTP — v1

상태: 신규 HTTP47/OpenAPI·Scope101/기존 HTTP45와 실제 SCRAM·검증 TLS3, 고유196검사로 기능 수용했다.
사용자 runtime/같은 job3D·계산 중 재접수/동시 U1은 후속이다. 선행은 [appearance E1–E3/자동 consumer](crop-leaf-appearance-execution-v1.md)다.
기존 인증/Scope·create_app의 선택적 service/query를 확장한다. 기본 비활성503이며 부분 조립은 거부한다.
같은 jobs/provider/admission/query·farm/완료 parent graph를 요구한다. tenant는 서버가 결정한다.
앱에 농장 서비스가 제공되면 appearance parent farm binding이 같은 FarmAuthoringService를 가리켜야 한다.

| 방법/경로 | 결과 | 필수 Scope |
| --- | --- | --- |
| POST `/v1/crop-leaf-appearance-executions` | 202/JobStatus; 기존 consumer 계산 | simulation_create + 기존 crop WRITE_SCOPES |
| GET `/v1/jobs/{job_id}/crop-leaf-appearance-execution` | 현재 status/결과 식별자 | metadata/artifact + 기존 crop READ_SCOPES |
| GET 위 경로 + `/manifest` | 같은 완료 서명/원 manifest | 같은 읽기 Scope |
| GET 위 경로 + `/frames/{index}` | 같은 완료의 원 DTO/UTC·기관/면적 | 같은 읽기 Scope |
| GET 위 경로 + `/replay` | 현재 원12frame 묶음 | 같은 읽기 Scope |
| POST 위 경로 + `/cancel` | 실제 cancel_accepted/cancel_requested/JobStatus | metadata/cancel |

## 입력·출력과 재시도

닫힌 요청은 study_id/revision·farm/input/rights와 parent job_id/result_sha256/numerical_root_sha256이다.
Input source는 leaf-appearance-input-source-v1, rights는 leaf-appearance-input-rights-v1이다.
원 program/source/evidence bytes·키/tenant·임의 경로는 받지 않는다. trusted resolver에서 원 입력을 찾는다.
JSON64KiB와 중복 키/NaN/잘못된 UTF-8·추가 query/field를 거부한다.
같은 tenant/study/revision·같은 요청은 원 job/입력을 반환하고 다른 내용은409 충돌이다.
현재 권한/권리 철회에는 이전 접수 성공으로 대체하지 않는다. 원 입력과 커밋 검증을 유지한다.
계산 중 동일 재요청도 같은 작업 의도이며 별도 작업을 만들지 않는다. 실제 응답 지연은 별도 검증한다.

조회/취소는 빈 body/query·canonical UUID, frame은0이상 정수 path만 허용한다.
응답은 기존 JobStatus 또는 닫힌 leaf-appearance-execution-read-v1 envelope다.
원 result/root/calculated_at·parent job/result/root/시각·farm/입력/binding SHA와
profile_applicability=unvalidated_for_registered_crop, normalization=per_tracked_shoot를 유지한다.
manifest/frame/replay는 요청 view만 제공하고 원 sample_count/정책·준비 참조·UTC/기관/면적을 바꾸지 않는다.
응답은 no-store·2MiB 이내이며 Scope/tenant·서비스 결속을 실행 전후 확인한다.

401 인증/만료,403 Scope,409 다른 의도,413 크기,415 media,422 입력/현재 자료 보류,
503 Pending/비활성/내부 오류는 기존 ErrorEnvelope/고정 공개 이유로 응답한다.
비밀·원 자료/키 경로·내부 오류 본문은 반환하지 않는다.
권리 철회 뒤 취소는 같은 tenant/stage/appearance 판본·원 job input을 확인해 허용하고 다른 모델은 거부한다.

## 수용 기준

1. 기존 OpenAPI80경로/84연산/492스키마·Scope 지문을 먼저 고정하고 기존 객체 불변·새6경로/typed 계약을 대사한다.
2. 비활성/부분/다른 graph를 거부하고 실제 인증 tenant·현재 Scope·양쪽 자료 권리/검토를 유지한다.
3. 실제 SCRAM/검증 TLS에서 접수·동일 재시도/409·원 완료12frame/47면적/UTC·취소를 확인한다.
4. 늦은 인증 만료·원본/부모 결속 변경과 전송 실패에서 결과를 잘못 반환하지 않는다.
5. 조회의 생장/CLI·지속 SQL/파일쓰기0·원 결과/행·3root/WSL 상한·소유 정리를 확인한다.
6. 내부 단독 조회11.37–11.85초와 별개로 실제 요청부터 응답까지 기존30초 예산을 실측한다.
   현재성 검사 생략이나 임의 timeout 증가로 통과를 대신하지 않는다. 계산 중 재접수/동시 U1·공통 용량/G4는 별도다.

이후 owned runtime/자동 consumer 조립→strict SDK/같은 job3D·메뉴/reload·실제 브라우저를 검증한다.
합성 연구 범위를 유지하며 실제 품종/농장·생산/마진·추천과 G0–G4를 구분한다.
