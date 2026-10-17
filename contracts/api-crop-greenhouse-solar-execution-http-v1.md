# 일사 접수·진행·취소·확정 구간 보호 HTTP v1

선행: [내부 실행](crop-greenhouse-solar-execution-core-v1.md), [현재 진행](crop-greenhouse-solar-execution-query-v1.md),
[확정 공개 응답](api-crop-greenhouse-solar-prefix-v1.md), [저장 결과 HTTP](api-crop-greenhouse-solar-route-v1.md).

POST `/v1/crop-greenhouse-solar-executions`는 닫힌64KiB Solar request를 현재 접수 서비스에 전달한다.
study/revision·farm/input SHA/증거·명시 권리 선언을 검사하고 기존 동일 원 요청은 같은 job을 반환한다.
접수202는 계산/관문/자료 권리 승인이 아니다. GET `/v1/jobs/{job_id}/crop-greenhouse-solar-execution`은 원 진행16KiB bytes를 반환한다.
POST 같은 경로의 `/cancel`은 현재 소유자 cancel scope로 source 권리 철회 뒤에도 취소할 수 있다.
취소 응답은 현재 job/요청/수락/관측 UTC·G0–G4 not_assessed·literal 승인 False다. 임대 worker의 ack가 별도다.

GET 같은 경로의 `/prefix`, `/prefix/samples`, `/prefix/events`는 검증된 현재 공개 read_prefix facade만 사용한다.
summary는 query 없음, page는 publication_sequence/head_sha256/proof_sha256 필수와 start/limit만 허용한다.
엄격한 UUID/hash/canonical decimal·중복/추가 query·GET/cancel body 거부·원64/8개·2MiB·원 selection/UTC/최초 시각을 적용한다.
원 입력/params/forcing/권리/검토·자격증명/서명 원문은 표시하지 않는다. 수치/복원/CLI/확정·조회 SQL 변경은0이다.

같은 jobs/admission/checkpoint/custody/result/current/prefix/farms/principal/resolver의 정확한 조립과 현재 코드를 요구한다.
접수/진행/취소 기본 경로는 설정 누락 시 인증 뒤503이며 prefix는 같은 실행 조립을 명시한 경우만 설치한다.
기존 진행 DTO·구 API·서명 자료/키/역할은 유지한다. 기본 OpenAPI에 실행3경로를 추가하고 prefix는 명시 조립에서만 문서화한다.
기준 commit52c66b5의 기존61 path/65 operation·389 schema를 보존한다. 기본 문서는64 path/68 operation·395 schema다.
전후 bearer/tenant·필요 AND scope·no-store·고정 오류와 transport/disconnect/cancellation 뒤 thread/identity 정리를 검사한다.
401/403/404/409(intent/selector)/413/415/422(잘못된 요청/현재 증거)/503(미구성/Pending/일시 불가)을 구분한다.

## 수용 기준

1. 실제 요청 parser·닫힌 DTO·권한/조립·오류/후계정·source/code drift·한도/전송 정리와 불필요 dispatch0을 검증한다.
2. 실제 SCRAM/검증 TLS 접수/동일 retry·미기동/확정/정상/수치 hold·원 응답/UTC·취소 요청/ack·권리 철회 뒤 cancel-only를 확인한다.
3. prefix 세 view의 원 값/단위/UTC/선택/최초 시각·직렬화 뒤 권리/페이지/owner witness/계정·heartbeat/취소·원 HEAD/DB 전진을 검증한다.
4. 기존 OpenAPI path/schema·소비자·원본2,148/두 UI/5root/동적 자식·512MiB/PID/합1GiB·FD/소유 PG/프로세스/passfile 정리를 유지한다.

다음은 전용 operator/runtime/독립 unpaused worker→typed 웹/같은 UTC3D→사용자 적용/재접속/재시작이다.
합성 software HTTP 경계이며 실제 자료/G0–G4·생산/경제/예측·추천·전체 완료 날짜는 별도다.
