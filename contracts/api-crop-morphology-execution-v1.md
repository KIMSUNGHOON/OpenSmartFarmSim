# 형태 계산 보호 HTTP — v1

상태: [27제어/89 OpenAPI·권한/실제 HTTPS2 수용](../research/api-crop-morphology-execution-20261022.md).
선행은 [E1–E3](crop-morphology-execution-v1.md)다. 표준 create_app의 선택적 service/query이며 기본은 disabled/503이다.
서로 다른 jobs/provider/service/farm/query 조합은 거부한다. 인증 tenant는 서버가 결정한다.

| 방법/경로 | 결과 | 필수 Scope |
| --- | --- | --- |
| POST `/v1/crop-morphology-executions` | 202/queued JobStatus; 계산은 worker | simulation_create + 기존 crop WRITE_SCOPES |
| GET `/v1/jobs/{job_id}/crop-morphology-execution` | 현재 status/결과 식별자 | metadata/artifact + 기존 crop READ_SCOPES |
| GET 위 경로 + `/manifest` | 같은 완료 서명/원 manifest | 같은 읽기 Scope |
| GET 위 경로 + `/frames/{index}` | 같은 완료의 원 DTO/UTC/길이 | 같은 읽기 Scope |
| GET 위 경로 + `/replay` | 현재 원 DTO 묶음 | 같은 읽기 Scope |
| POST 위 경로 + `/cancel` | 실제 cancel_accepted/cancel_requested/JobStatus | metadata/cancel |

접수는 닫힌 farm/input/rights 요청64KiB, 중복 키·NaN/부정 UTF-8·추가 query/field를 거부한다.
원본/키/tenant와 임의 경로는 받지 않는다. 조회/취소는 빈 body/query와 UUID, frame은0이상 정수 path만 허용한다.
모든 응답 no-store, 닫힌 typed envelope/JobStatus·2MiB 상한이며 권한/tenant·서비스 결속을 실행 전후 확인한다.
401 인증/만료, 403 Scope, 409 같은 study/revision 충돌, 413 크기, 415 JSON media,
422 입력/현재 자료 보류, 503 Pending/비활성/내부 오류다. 내부 오류·비밀/자료 경로는 반환하지 않는다.
권리 철회 뒤 취소는 허용하되 tenant/stage/version·원 job input을 확인하며 다른 모델 작업은 거부한다.

값은 연구용 합성 수치이며 실제 farm Run·G0–G4로 승격하지 않는다. 자동 consumer/운영 조립과 사용자 UI는 별도 단계다.
