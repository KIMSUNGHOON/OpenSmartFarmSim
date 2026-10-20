# CO₂·일사 공동 결과의 공개 응답 v1

Status: implementation pending. 선행은 [서명 결과 저장소](crop-greenhouse-co2-result-store-v1.md)와
현재 CO₂ continuation/checkpoint/journal v2·UTC·불변 artifact다.
[기존 Solar 투영](api-crop-greenhouse-solar-replay-v1.md)의 닫힌 타입/개인정보/페이지 원칙을 대조한다.

[사전 검증](../research/artifacts/api-crop-greenhouse-co2-replay-preflight-20261021.json)은 순수37검사와
별도 프로세스의 템플릿 응답 SHA/조회 계산·CLI·SQL0을 확인했다. 실제 SCRAM 연결은 WSL 합산 RSS
상한으로 미수용이다. 격리된 hosted39검사/실제 등록 원문의 fresh2를 준비했으며 전체 backend CI와 별도다.
새 시험 DB의 work_mem64kB/jitoff 실제 적용도 확인한다. 원5서비스/자료와 자원 상한은 유지한다.

`project_co2_result(record, terminal, *, source_program, view='summary', page=None, limit=None)`은
`joint-co2-solar-replay-v1` 응답을 만든다. 원 저장소가 검증한 완료/보류를 표현하는 순수 투영이며
함수 자체는 HMAC·계정·자료 권리나 G0–G4를 승인하지 않는다. 실제 HTTP와 권리 검사는 후속 current reader가 담당한다.

## 원 값과 농도 기준

summary/samples/events는 원109상태·8파생량·44연속 장부·6사건 합계·17수지/허용오차,
forcing_step_index·순서·단위·microsecond UTC·마지막 확정값과 실패 경계를 보존한다.
공기 CO₂ 질량/밀도는 양수이며 수확·호흡/환기/에너지의 순 흐름을 일괄 비음수로 제한하지 않는다.
50개 과실 구획 배열과 유한 float의 원 값을 보존하고 bool/int를 float로 묵시 변환하지 않는다.

ppm의 wet/dry 기준은 snapshot에 저장되지 않는다. 기존 artifact reader는 이미 같은 root의
`_context['program']`을 검증해 읽으므로 이 원 program을 추가 인자로 전달한다.
program SHA는 manifest.program_sha256와 같아야 하고 forcing 행의 닫힌 index/basis를 확인한다.
`source_program`은 서버 내부 인자이며 사용자 요청으로 받지 않는다.
원 forcing_step_index에 해당하는 basis만 sample/사건의 별도 metadata로 제공한다.
같은 실패 시각에 새 forcing이 아직 확정되지 않은 경우가 있으므로 마지막 시각으로 forcing을 새로 선택하지 않는다.
원 `{value,time}`의 두 값은 바꾸지 않으며 basis metadata를 더한다. 원 압력/경계 forcing/매개변수는 공개하지 않는다.

## v2 사건 기록의 경계

원 journal의 사건은 step/elapsed/forcing_step_index와 management다. management의 before/after에는
원109상태·8파생량·입력/계산 SHA가 남아 있고 원 event/boundary/parameters는 공개 대상에서 제외한다.
제거량·co2_basis_carbohydrate·사건 수지/예산·bulk_air_invariants와 코드/출처 지문을 보존한다.
사건 수지와 예산은 각각10항목이다.
co2_basis_carbohydrate는 제거된 탄수화물의 CO₂ 질량 기준 환산량이며 공기 배출량으로 이름을 바꾸지 않는다.

v2는 transient after_rhs를 저장하지 않는다. 따라서 원 Solar 판본의 solar_before/solar_after 또는
관리 후 CO₂ 교환 진단을 사건 응답에 만들어 넣지 않는다. sample에 저장된 일사/환기/CO₂ 교환 진단은 그대로 제공한다.
부족한 진단을 얻기 위한 Context/복원/RHS/관리/적분/새 UTC binding/CLI 실행은 허용하지 않는다.

## 응답과 실패

summary는 원 manifest/model/code/profile/QC/수지·마지막 확정 상태/시각·checkpoint SHA와 hold를 제공한다.
samples64/events8·원 offset/total/next_offset·원 artifact/HEAD/proof/context/UTC 결속과 UTF-8 2MiB 상한을 유지한다.
hold는 실패 단계/시각과 닫힌 reason code만 공개하며 자유 형식 내부 오류문은 공개하지 않는다.
원 tenant·등록 job·권리/검토자·원 농장 기록·forcing/프로필/매개변수/인증 정보는 공개하지 않는다.
잘못된 타입/단위/판본·manifest/program/UTC/progress/페이지 혼합은 일반 ProjectionHold다.
기존 Solar나 다른 family의 ID/코드/모델을 새 CO₂ 결과로 받아들이지 않는다.

## 수용 기준

원 실제 CO₂ producer/file의 정상·보류/forcing 변경·관리 전후 행/모든 숫자·단위·시각·basis를 대사한다.
fixture template는 기존 실제 SCRAM 소프트웨어 결과에서 캡처한 합성 원문이며 현재 농장 승인/서명 증거가 아니다.
추가/누락 필드·잘못된 float/단위/50배열·model/코드/UTC/basis/program 혼합·페이지/2MiB·개인정보 경계를 검증한다.
별도 exec의 같은 응답 SHA와 조회 수치/context/restore/CLI0, 실제 SCRAM 정상·보류 결과와의 연결,
원 자료/기존 서비스·FD·WSL/시험 소유 PG/schema/role/passfile 정리를 확인한 뒤에만 수용한다.
그 뒤 같은 세션의 current query→보호 HTTP/runtime→worker/prefix→같은 UTC3D로 진행한다.
실제 품종/작기·생산/수익 예측·추천·G0–G4는 [제품 명세](../docs/PROJECT_SPEC.md)를 따른다.
