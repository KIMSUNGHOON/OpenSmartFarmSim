# 환기 결과 조회의 명시 runtime — v1

2026-10-12. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단한다. 재귀 CLI를 실행하지 않는다.
[보호 HTTP](api-crop-greenhouse-ventilation-route-v1.md)의 서버 조립 계약이다.

## 설정과 조립

`app.crop_greenhouse_ventilation_operator_config.load_ventilation_api_runtime(path)`는
`operator-greenhouse-ventilation-api-config-v1`만 받는다. 최상위 필드·보호 파일 규칙은
[기존 operator](operator-config-v1.md)를 재사용하며 새 `crop_greenhouse_ventilation_result_storage`는 필수 exact boolean이다.
기존 joint/calculation-cycle flag도 선택적으로 받을 수 있지만 활성 flag는 기존 `crop_cycle_result_storage=True`를 요구한다.
새 결과의 기존 농장 결속이 이 cycle authority를 사용하므로 기존 cycle store factory도 필요하다.
이 선행 조립은 cycle 계산/등록을 실행하지 않는다. 실행/prefix 최상위 flag는 이 조회 판본에서 받지 않는다.

중복 JSON 키·비유한 값·초과 크기·잘못된 타입/경로/판본·예상 밖 필드는 거부한다.
설정·DSN·TLS·키 파일은 기존 보호 reader로 읽고 trusted factory 전후/조립 뒤 bytes와 메타데이터를 재검사한다.
기존 legacy/calculation/joint/execution/prefix loader는 새 flag 생략/False만 유지하고 True/새 판본은 거부한다.
`OSSF_API_CONFIG`/`api_service()`는 기존 HTTPS 전경 진입점을 재사용한다. 오류는 `operator_config_rejected`다.

`ApiRuntimeDependencies` 끝에 기본 None인 두 factory를 추가한다:

- `crop_greenhouse_ventilation_result_store_factory(farm_authoring_service=...)`
- `crop_greenhouse_ventilation_current_query_factory(result_store=...)`

flag와 두 factory의 존재·cycle 선행 조건은 I/O 전에 일치해야 한다.
exact `VentilationResultStore`/`VentilationCurrentQuery`, 동일 jobs/farms/current_principal와 동일 query.store를 요구한다.
native binding/code/현재 권리 검사를 유지하며 입력/서버 이력/DB 결과 integrity key는 서로 달라야 한다.
조립한 객체를 `ventilation_crop_results`/`ventilation_crop_query`로 노출하고 같은 인스턴스를 기존 HTTP에 전달한다.
False는 두 객체 None/인증된 경로503을 유지한다. 신원/설정 혼합은 `API runtime assembly rejected`다.

trusted factory가 기존 provisioned 역할·원 입력/권리·resolver·custody root·서로 다른 키를 제공한다.
자동 key/role grant/마이그레이션·디렉터리 생성·자료 채택을 추가하지 않는다.
조립은 모델 계산·새 결과 등록·worker 시작·사용자 배포·G0–G4 승인을 뜻하지 않는다.

## 수용

1. 닫힌 새 설정/파일 변경·기본 None·flag/factory 불일치·I/O 전 거부와 기존5판본의 동작을 확인한다.
2. 실제 SCRAM/검증 TLS에서 새 정상/보류의 요약·생장·사건 bytes/원 UTC가 저장 current query와 일치한다.
3. foreign 객체/키 재사용/변조된 code pin/실제 grant 철회를 거부하고 복원 뒤 같은 현재 결속을 재조립한다.
4. 실제 DB의 직렬화 중 자료권/계정 변경을 차단하고 조회9수치 호출·새 등록·기존 cycle 실행은0이다.
5. 기존 joint runtime의 같은 TLS 응답·새 경로503, 원 입력/파일/DB 행·FD·소유 PG/passfile·두 UI/WSL을 보존한다.

합성32초 조회 조립이다. 자동 작업/진행·같은 UTC3D/실제 사용자 적용·전체 작기/생산·경제·독립 농장 검증은 후속이다.
