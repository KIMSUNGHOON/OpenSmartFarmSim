# CO₂·일사 저장 결과의 보호 HTTP v1

Status: planned; implementation/tests pending.
선행은 [현재 권리 조회](crop-greenhouse-co2-current-query-v1.md)의 기능 수용이다.
[기존 Solar 보호 조회](api-crop-greenhouse-solar-route-v1.md)의 요청/전송/명시 조립 계약을 대조한다.
WSL 동시 용량과 기본 operator/runtime 활성화는 별도 미완료 조건이다.

## 요청과 조립

`GET /v1/crop-greenhouse-co2-research-results/{result_id}`는 현재 query가 검증·직렬화한 원 bytes만 반환한다.
ID는 `joint-co2-solar-result-v1:`와 소문자 hex64다. 필수 query는
scenario_id/scenario_revision/registration_sha256/crop_id이며 view는 summary/samples/events다.
summary는 offset/limit 명시를 거부하고 samples는 offset0..512/limit1..64, events는 offset0..128/limit1..8이다.
기본 offset0/limit64 또는8, 정확한 마지막 빈 페이지를 유지한다.
중복/unknown query·canonical 아닌 정수·GET 본문·잘못된 ID/농장/view/범위와 조기 disconnect는422다.
raw program/basis/forcing/계수는 요청으로 받지 않는다. 계산·등록/새 UTC 연결·CLI를 실행하지 않는다.

설치 함수는 exact Co2ResultStore/Co2CurrentQuery와 같은 jobs/farms/principal provider를 요구한다.
둘 다 None이면 인증된 요청에503을 반환하며 하나만 전달하거나 타입/포인터/권한 결속이 다르면 설치를 거부한다.
`create_app`의 명시 인자로만 연결한다. 기존 operator의 새 True 지원과 기본 runtime 자동 조립은 후속이다.
새 계정/키/서비스를 만들거나 flag만으로 활성화하지 않는다.

## 전송과 문서

Bearer/READ_SCOPES를 앞뒤로 확인하고 threadpool에서 current query를 한 번 호출한다.
실패한 조회도 응답 직전 현재 tenant/credential/scope를 다시 확인한다. 성공은 JSON/no-store·원2MiB 이하다.
X-OSSF-CO2-Query-Version/Query-Code-SHA256/Projection-Code-SHA256 헤더로 읽기 코드를 명시한다.
401인증·403계정/범위·404없는 결과·422요청/현재 증거 보류·503미구성/예상 밖 장애를 닫힌 오류로 반환한다.
내부 예외/경로/원 자료/키는 전송하지 않는다. 취소/전송 실패의 소유 reader/DB/FD 정리를 검증한다.
전송 전에 확정된 bytes 이후의 철회를 소급 취소하는 스트림이라고 주장하지 않는다.

OpenAPI는 Co2Replay·109상태/44장부/17수지·사건10수지/원 UTC와 오류/인증/scopes를 선언한다.
원 v2에 없는 사건 after_rhs/Solar 진단은 schema에도 추가하지 않는다.
기존 모든 경로/타입 이름/참조를 보존하며 생성 snapshot과 전체 경로/scope inventory를 대사한다.
모듈 import/스키마 생성이 계산·DB 접속을 수행하지 않도록 확인한다.

## 수용 기준

닫힌 요청·권한/없는 결과·잘못된 조립/미구성·오류/늦은 계정 변경, 조기 disconnect·취소/전송 실패를 검사한다.
실제 SCRAM와 검증된 loopback TLS에서 정상/보류의 원3응답 SHA·수치/단위/UTC를 대사한다.
투영/직렬화 중 자료 권리·검토·농장 원천 철회가 stale 응답을 차단해야 한다.
조회17물리 진입점/CLI/SQL쓰기·새 결과 row0, 원 결과/최초 시각·FD/소유 PG/schema/role/passfile 정리를 확인한다.
연결된 농장/경제 입력의 기존 결정론적 재검증은 보존하며 모든 산술0이라고 확대하지 않는다.
기존 OpenAPI/경로/import·기동 UI/원 자료와600초·512MiB/PID/합1GiB 조건을 유지한다.
hosted 결과로 기존5root를 포함한 WSL 동시 용량을 해제하지 않는다.

이후 명시 runtime→worker/prefix→같은 UTC3D이며 전체 작기·자원/경제·실제 자료/품종 예측·추천과
G0–G4는 [제품 명세](../docs/PROJECT_SPEC.md)의 별도 조건이다.
