# 일사 결과 조회의 명시 runtime — v1

2026-10-17. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단한다. 재귀 CLI를 실행하지 않는다.
[보호 HTTP](api-crop-greenhouse-solar-route-v1.md)를 기존 서버에 조립하는 계약이다.

`app.crop_greenhouse_solar_operator_config.load_solar_api_runtime(path)`는
읽기 판본 `operator-greenhouse-solar-api-config-v1`을 받는다. 새 [실행/prefix 명시 판본](crop-greenhouse-solar-execution-runtime-v1.md)은 별도 필드 집합을 사용하며 아래 읽기 판본을 확장하지 않는다. 최상위 필드·보호 파일·중복 JSON/비유한 값/크기/경로/모드 검사는
[기존 operator](operator-config-v1.md)를 사용한다. `crop_greenhouse_solar_result_storage`는 필수 exact bool이다.
선택 joint/ventilation/calculation-cycle flag도 exact bool이며 활성화 시 기존 `crop_cycle_result_storage=True`가 필요하다.
기존 cycle factory는 농장 authority 선행 조립이며 계산이나 등록을 실행하지 않는다. 실행/prefix 최상위 flag는 이 판본에서 받지 않는다.
trusted factory 전후와 조립 뒤 읽은 모든 파일의 bytes/메타데이터/모드를 다시 검사한다.
기존 loader는 solar 생략/False를 유지하고 True/새 판본을 거부한다.
`api_service()`는 `OSSF_API_CONFIG`와 기존 HTTPS 전경 진입점을 사용한다. 고정 오류는 `operator_config_rejected`다.

`ApiRuntimeDependencies` 끝의 기본 None인 두 factory는 다음과 같다.

- `crop_greenhouse_solar_result_store_factory(farm_authoring_service=...)`
- `crop_greenhouse_solar_current_query_factory(result_store=...)`

flag/두 factory 존재·cycle 선행 조건은 I/O 전에 일치해야 한다. exact SolarResultStore/SolarCurrentQuery,
같은 jobs/farms/current_principal과 query.store를 요구한다. 기존 binding/code·현재 역할 감사를 유지하고
입력/서버 이력/DB integrity key는 서로 달라야 한다. 조립 객체를 `solar_crop_results`/`solar_crop_query`로 노출하고
같은 객체를 보호 HTTP에 전달한다. False는 두 객체 None/인증 후503이다. 혼합 조립은 `API runtime assembly rejected`다.
기존 역할/키/resolver/root를 trusted factory가 제공한다. 자동 key 생성·grant·마이그레이션·계산·결과 등록·worker 시작은 추가하지 않는다.

## 수용 기준

1. 닫힌 설정·파일 변경·False/누락 호환·두 factory/cycle 선행·기본 None·잘못된 factory/type/pointer/key/code/역할을 검사한다.
2. 실제 같은 SCRAM DB·검증된 TLS에서 normal/hold 원3view bytes·단위/UTC와 현재/늦은 권리·계정 차단, 조회13수치/CLI 및 SQL 변경0을 확인한다.
3. 기존 API·모델·원 결과/키/배포 역할·두 UI·원본·5root/동적 자식·WSL512MiB/PID/합1GiB와 소유 PG/FD/파일 정리를 유지한다.

합성32초 연구 계산 조립이다. 자동 worker/확정 prefix·같은 UTC3D·사용자 활성화·전체 작기/동시 사용자 성능·실제 자료/G0–G4·예측/추천 승인은 별도다.
