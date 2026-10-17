# 일사 실행·확정 구간 명시 runtime — v1 (구현·검증 중)

[설정·API 조립 부분 수용109검사](../research/crop-greenhouse-solar-execution-assembly-implementation-20261017.md). 독립 unpaused worker와 단계 전체는 미수용이다.
[독립 동시 실행은 자원 hold](../research/crop-greenhouse-solar-unpaused-resource-hold-20261017.md)이며 누락된 수용 증거를 대체하지 않는다.


선행: [결과 runtime](crop-greenhouse-solar-runtime-v1.md), [실행/prefix HTTP](api-crop-greenhouse-solar-execution-http-v1.md),
[내부 worker](crop-greenhouse-solar-execution-core-v1.md).

ApiRuntimeConfig의 kw-only `crop_greenhouse_solar_execution`/`crop_greenhouse_solar_prefix`는 exact bool·기본False다.
execution은 기존 solar 결과 저장/factory·farm 선행을, prefix는 execution을 요구한다. 기존 역할/키/판본을 재사용한다.
같은 result.server의 farm/jobs/resolver로 SolarExecutionService→CheckpointStore→ExecutionQuery→PrefixQuery를 조립하고
네 객체를 runtime에 노출하며 같은 객체를 보호 HTTP에 전달한다. execution=False에서는 실행 객체 셋을, prefix=False에서는 prefix query를 만들지 않는다.
API 프로세스에서 수치 worker를 시작하지 않는다. 실제 소비는 별도 deterministic worker process가 담당한다.

기존 Solar 읽기 설정 `operator-greenhouse-solar-api-config-v1`은 변경 없이 실행/prefix 최상위 필드를 거부한다.
새 `operator-greenhouse-solar-execution-api-config-v1`은 execution 필드를,
`operator-greenhouse-solar-prefix-api-config-v1`은 execution/prefix 두 필드를 필수로 받는다.
중복/추가/누락·coercion·정책 내부 flag·불완전 의존성·보호 파일 변경은 trusted factory 전에/후에 거부한다.
기존 다른9 operator 판본에는 새 root 필드를 추가하지 않는다. 오류·파일/경로/소유권·키 정책은 기존 계약을 따른다.

## 수용 기준

1. 새 기본False/닫힌 판본/의존성·기존 loader/파일 재검사·오조립/키/현재 역할을 검증한다.
2. 실제 SCRAM/검증 TLS API와 **독립 unpaused numerical worker**에서 정상/hold/취소·계산 중 확정 구간/UTC/최초 시각·원 저장 응답을 대사한다. 메타데이터 actor나 중단 장벽을 이 증거로 대신하지 않는다.
3. 현재/늦은 자료 권리·계정·취소 요청/ack·재시도와 제품 읽기 계산/SQL 변경0을 확인한다.
4. 원5root/동적 자식·필수 소비자/원본/키/역할/두 UI를 포함해512MiB/PID·합1GiB·FD/소유 PG/임시/자격 파일 정리를 유지한다. 초기 합배치 assertion/RSS 실패는 보존한다.

명시 조립만으로 이 단계 전체를 완료하지 않는다. 같은 UTC의 typed 웹/3D·사용자 적용/재접속/재시작과 실제 자료/G0–G4·생산/경제/추천은 후속이다.
