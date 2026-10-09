# 작물·기후 공동 결과의 보호 HTTP — v1

2026-10-10. 현재 native Codex CLI `gpt-6.1-sol / xhigh` 안에서 판단한다. 재귀 CLI는 실행하지 않는다.

`GET /v1/crop-climate-joint-research-results/{result_id}`는
[현재 query](crop-climate-joint-current-query-v1.md)가 같은 권리 세션에서 검증·직렬화한
[원 공개 bytes](api-crop-climate-joint-replay-v1.md)를 반환한다. 계산이나 새 등록을 수행하지 않는다.
ID는 `joint-crop-climate-result-v1:`와 소문자 hex64다.

필수 query는 `scenario_id,scenario_revision,registration_sha256,crop_id`다.
기본 `view=summary`에는 offset/limit을 명시할 수 없다. `samples`는 offset0..512/limit1..64,
`events`는 offset0..128/limit1..8이며 기본 offset0/limit64 또는8이다.
unknown/중복 query, canonical 아닌 정수, 누락/잘못된 농장 필드·ID·view·범위, GET 본문은422다.
본문을 읽기 전 연결 종료도422이며 query를 호출하지 않는다.

`install_joint_crop_climate_routes`는 정확한 새 query/store와 동일 jobs/farms/principal provider를 요구한다.
둘 다 None이면 경로는 존재하되 인증 후503이다. 하나만 지정하거나 잘못된 타입/포인터/권한 결속이면 설치를 거부한다.
별도 authority/key/service를 추가하지 않는다. `create_app`의 두 명시 인자로만 전달한다.
기존 operator의 새 True 지원과 기본 runtime 자동 조립은 후속이다.

기존 Bearer/READ_SCOPES를 전후 검사한다. threadpool에서 query.read를 한 번 호출하고
그 query의 원 서명/페이지·현재 권리·직렬화 전후 검사를 통과한 bytes만 전송한다.
조회가 실패한 경우에도 응답 직전 tenant/credential/scope를 재검사한다. 연결 종료/취소 뒤 worker가 남으면 현재 query의
finally/현재 principal 검사로 정리한다. 전송 전에 확정된 bytes 이후 발생한 철회를 소급 취소하는 스트림은 아니다.
성공은 JSON/no-store/2MiB 이하이며 query version/code와 projection code를 헤더로 제공한다.
인증401, 계정/scope403, 없는 결과404, 요청/현재 증거 hold422, 미구성/예상 밖 장애503이다.
오류에는 원 예외·경로·키·내부 자료를 노출하지 않는다.

OpenAPI는 닫힌 `JointReplay`/108상태·장부·관리 사건/원 UTC·completed/hold와 오류/인증/scopes를 선언한다.
DTO가 원 수치 계약의 상수를 참조하므로 schema 생성 때 해당 모듈은 import되지만 계산·DB 접속은 하지 않는다.
route의 public import는 설치 시 수행해 기존 api/operator import 순환을 피한다.
기존 경로는 유지한다. 실제 API 스키마가 달라지므로 생성 snapshot `contracts/openapi-v1.json`과
그 전체 경로/필수 scope inventory를 확인하는 `backend/tests/test_api_openapi.py`를 변경 경계에 추가한다.
새 projection의 `Reference` 클래스는 `JointReference`로만 이름을 바꾼다. 기존 수확 `Reference`의
OpenAPI 이름/참조를 보존하기 위한 추가1파일이며 wire·수식·저장 code는 변하지 않는다(core7).

## 수용 기준

1. 닫힌 요청/권한/없는 결과/잘못된 조립/오류·늦은 계정 변경과 조기 disconnect·취소/전송 실패를 검사한다.
2. 실제 SCRAM DB와 검증된 loopback TLS의 원 summary/samples/events bytes·UTC·108상태/장부와 completed/hold를 대사한다.
3. 직렬화 중 현재 자료 권리/검토/농장 원천 철회를 주입해 stale 응답을 차단한다. 조회 수치 호출/새 행은0이다.
4. OpenAPI/기존 경로/import·원 artifact/기동 UI/FD/소유 PG·passfile와 WSL 자원 한도를 보존한다.

작은 합성32초의 보호 조회다. 전체 작기 성능, runtime True, 웹/3D/U3, 실제 생산·미래 마진·추천과 G0–G4 승인은 포함하지 않는다.
