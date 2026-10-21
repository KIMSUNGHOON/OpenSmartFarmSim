# CO₂ 결과 조회의 명시 runtime v1

Status: functional runtime accepted; shared WSL capacity and user activation pending.
[기능 수용](../research/crop-greenhouse-co2-runtime-20261021.md)은 source8c1ba5d/CI39518527650의
177검사·새 CO₂/기존 Solar 실제 SCRAM/검증 TLS 정상·보류4와 원 응답/권한·설정/정리를 대사했다.
[사전 증거](../research/artifacts/crop-greenhouse-co2-runtime-preflight-20261021.json)의 원 한도를 유지했다.
선행은 [보호 HTTP 기능 수용](api-crop-greenhouse-co2-route-v1.md)이다.
[기존 Solar runtime](crop-greenhouse-solar-runtime-v1.md)의 보호 설정/동일 객체 조립을 대조한다.
기본 operator 자동 활성화·worker/prefix/3D·공통 WSL 용량/사용자 적용은 별도 조건이다.

## 닫힌 설정과 명시 동의

별도 `load_co2_api_runtime(path)`와 `operator-greenhouse-co2-api-config-v1` 읽기 판본을 사용한다.
기존 operator_config 파일/보호 파일 helpers와 기존 loader의 CO₂ True 조기 거부를 유지한다.
최상위는 원 읽기 설정 필드만 받고 policy의 crop_greenhouse_co2_result_storage를 필수 exact bool로 받는다.
중복 JSON/비유한 값/unknown 필드·경로/모드/소유/ACL·크기와 trusted factory reference를 먼저 검사한다.
읽은 config/DSN/키/cert의 bytes·메타데이터를 factory 전후/전체 조립 뒤 재검사한다.
새 loader에서 같은 bytes로 다시 쓴 파일도 inode/시각 메타데이터로 거부하며 기존 helper는 유지한다.

기존 ApiRuntimeConfig의 암묵적 CO₂ True 거부를 보존하기 위해 서버의 별도 kw-only
crop_greenhouse_co2_read(defaultFalse) 동의와 policy flag를 정확히 맞춘다.
이 동의는 새 loader가 판본에 따라 생성하며 JSON 최상위의 새 임의 flag로 받지 않는다.
누락/default 상태의 기존 직접 생성자는 policy True를 계속 거부해야 한다.
두 flag의 비bool/불일치, True일 때 cycle/farm 선행·두 factory 누락/혼합을 I/O 전에 거부한다.
farm 선행은 thermal/source storage와 owned fixture/context 구성이다. 현재 실제 farm 객체 결속은 조립 때 다시 확인한다.

## 객체와 권한

ApiRuntimeDependencies 끝에 기본None인 두 factory만 추가한다.

- crop_greenhouse_co2_result_store_factory(farm_authoring_service=...)
- crop_greenhouse_co2_current_query_factory(result_store=...)

exact Co2ResultStore/Co2CurrentQuery·같은 jobs/farms/current_principal/query.store,
현재 binding/code/역할 감사와 입력·서버 이력·DB integrity key의 구분을 확인한다.
조립 결과 co2_crop_results/co2_crop_query의 같은 객체를 create_app에 전달한다.
False는 객체None/인증 뒤503이며 두 factory도 없어야 한다. True는 기존 authority의 명시 권한을 검증한다.
키/권한/마이그레이션/계산/등록/worker를 자동 생성하거나 시작하지 않는다.
기존 HTTPS 전경 service 진입점을 사용하고 잘못된 설정은 operator_config_rejected,
잘못된 조립은 API runtime assembly rejected로 닫는다.

## 수용 기준

False/default·직접 생성자의 암묵적 True 거부, 새 명시 True·factory 선행/혼합·파일 변경·잘못된
타입/포인터/키/코드/역할을 검사한다. 기존 모든 loader 판본/기존 True 맥락·공통 runtime 회귀를 보존한다.
실제 같은 SCRAM DB와 검증된 TLS에서 정상/보류 원3view bytes/UTC·현재/늦은 권리·계정 차단,
계산/context/restore/UTC생성/CLI17계측·SQL쓰기0, 원 행/시각과 FD/소유 PG/schema/role/passfile 정리를 대사한다.
원 결과/키·두 UI/자료·필수5root와600초·512MiB/PID/합1GiB 조건을 유지한다.
hosted 수용은 공통 WSL 동시 용량이나 사용자 적용을 해제하지 않는다.

합성32초 조회 조립이며 전체 작기·자원/경제·실제 CLI 종단 간·실제 자료/품종 예측·추천과 G0–G4는 후속이다.
