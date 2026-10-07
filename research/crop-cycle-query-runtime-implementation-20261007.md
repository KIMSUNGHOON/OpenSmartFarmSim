# 현재 저장 작기 조회의 실제 API/runtime 연결

2026-10-07 KST. [연결 계약](../contracts/crop-cycle-query-runtime-v1.md)의 작은 합성 농장
소프트웨어 범위를 로컬 수용했다. [증거 영수증](artifacts/crop-cycle-query-runtime-reference-20261007.json)은
최종7개 source SHA, 실제 시험 로그/정리 SHA, 원 계산 manifest/checkpoint, 응답 시간·크기와
현재 Codex CLI `gpt-6.1-sol / xhigh` 문맥을 기록한다. 재귀 CLI는 실행하지 않았다.

## 구현과 현재 권리

`ApiRuntimeDependencies.crop_cycle_current_query_factory`를 명시적으로 선택하면
같은 runtime의 원 store/jobs/farm을 사용하는 정확한 `CurrentCycleQuery`만 허용한다.
잘못된 구성은 연결 전에 거부하고, 잘못된 factory 반환도 실제 조립에서 거부한다.
기존 기본 reader와 공개 JSON schema는 유지한다.

새 reader의 `open` 안에서 기존 공개 투영과 전체 JSON bytes를 만든 뒤 현재 DB/농장 등록·
Scope/계정·원천/입력 권리·원 서버 서명/trace와 실제 입력/result bytes를 다시 검사한다.
투영 중 권리를 철회해도 결과를 반환하지 않는다. 원 math 판본은 보존하며 새 조회 판본/code는
`X-OSSF-Crop-Query-Version`, `X-OSSF-Crop-Query-Code-SHA256` 헤더에 기록한다.
private proof/경로/키/DB HMAC는 공개하지 않는다.

## 통과한 검증

- 실제 PostgreSQL16.15/SCRAM과 HTTPS: **1개/243.58초**, 종료0.
  원120걸음의 **3시점/3관리 사건**을 모든 페이지·UTC·원량과 대사했다.
  완료·출력 없는 hold·끝 페이지·두 runtime 재시작, 401/403/404, 현재 권리/원천 철회·
  투영 후 철회·원 intent 변조422 및 실제 잘못된 DB 역할 권한503을 확인했다.
- 전체 HTTPS **22응답**, 최대 **6.306509초/21,514bytes**.
  모든 본문을 읽었고 기존 **30초/2MiB**와 `no-store`를 유지했다.
  조회 parser/context 준비/terminal QC/RHS0회, 서버2개 종료·custody FD0을 확인했다.
  실제 연구 결과3행/실제 작물 Run0행이며 이후 스키마/역할/pgpass0, PG process/data directory 부재를 확인했다.
- 새 runtime 구성5개와 기존 runtime6개/route41개: **52개/7.65초**.
  기존 API/runtime/OpenAPI/투영: **137개 통과·9개 건너뜀/185.78초**.
  건너뛴9개는 해당 분할에 PG DSN이 없었던 기존 선택적 DB 시험이며 실행한 것으로 보고하지 않는다.
- [선행 authority](crop-cycle-query-authority-implementation-20261007.md)의8개를 포함한
  수집 목록은 고유207개이며 **분할 통과198개·건너뜀9개**다. 단일 전체 backend 실행은 아니다.
  후속 권한 회귀2개/166.21초는 이8개에 포함하므로 합산하지 않는다.

## 실제 실패와 코드 판본

새 구성5개 실패/0.86초로 시작했다. route의 최상위 import에서 순환 참조3개를 재현했고,
installer 안으로 import를 옮긴 뒤52개를 통과했다.
첫 실제 TLS에서는 잘못된 worker 권한을 이미 거부했지만422를 반환해 **1개 실패/230.07초**였다.
기존 계약의503을 보존하도록 `RolePolicyHold`를 전파했고, 최종 권한 회귀2개와 실제 TLS를 통과했다.
역할 제한/권한 검사와 원 계산식은 완화하지 않았다. 실패 실행도 PG/역할/비밀 정리를 확인했다.

선행8개/631.33초의 코드는 `04072f0`으로 보존한다. 이후 query module 변경은
`RolePolicyHold` import와 예외 전파 두 곳이며, 선행 영수증을 다시 쓰지 않았다.
52개/137개 분할도 이 변경 전 결과이고, API/factory source는 그 이후 그대로다.
최종 transport 변경은 영향받는 권한2개와 실제 SCRAM/TLS로 검증했다.
198개 전체가 최종 query code에서 한 번에 실행됐다고 주장하지 않는다.
원 수학52개·선행12 primitive source와 기존 store/farm/custody source를 보존했다.

## 현재 수용과 다음 단계

`crop-cycle-query-authority`, `crop-cycle-query-runtime`과 두 자식으로 구성한
`crop-cycle-current-query`의 **작은 저장 조회 소프트웨어 범위**를 수용한다.
새 경로의 전체166일·중단 복원·부하·3D 연결과 전체 backend/hosted CI는 이번 수용에 포함하지 않는다.
이번 단계에서 새 브라우저/WebGL 시험은 실행하지 않았다. 앞서 수용한25시간의
[실제 PG/TLS/WebGL 경로](web-crop-cycle-native-implementation.md)와 구분한다.

다음은 [유실된 원166일](crop-cycle-full-rhs-missing-state-20261007.md)을 완료로 바꾸거나
예산을 재설정하는 대신, **별도 판본의 지속 저장 실험 설계·실행**이다.
원 입력/코드/제한·독립 실행 예산과 checkpoint/terminal 보존을 먼저 고정하고,
실제 연속 RHS 전체 종료 → 저장 조회/중단 복원 → 같은 ID/UTC3D를 검증한다.
그 뒤 생과 생산량 → 자원 사용 → Decimal 경제 계산을 연결한다.
전체 완료 날짜는 실제 전체 처리/조회 실측과 자료 확보 상태 뒤 산정한다.

운영 기반은 `d19f7c0`으로 고정한다. 실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건이며,
G0–G4는 `not_assessed`다. 생산 예측·미래 마진·최적 작물 추천 게시는 계속 보류한다.
