# 불변 작물 연구 결과 v1

상태: **로컬 합성 연구 저장 소프트웨어 수용**, 2026-10-04.
[실제 SCRAM·집중 172개 증거](../research/crop-result-storage-implementation.md)를 확인했다.
기존 CLI `gpt-6.1-sol / xhigh` 세션에서 설계하며 재귀 CLI는 실행하지 않는다.
선행은 [생장 적분](crop-growth-integration-v1.md)과 현재 농장 등록/권리 제공자다.
[제품 관문](../docs/PROJECT_SPEC.md#6-검증과-수용-관문)은 그대로 적용한다.

## 저장 경계

`CropResultStore(farms, profile, notice_raw, *, program_rights, integrity_key)`는
실제 `FarmAuthoringService`와 같은 authority/SCRAM `JobStore`, 고정 참조 프로필/
GreenLight 고지, 명시적 현재 프로그램 권리 제공자와 비밀 무결성 키를 요구한다.
호출자가 계산 결과·계수·서명·테넌트를 요청 본문에 넣을 수 없다.
현재 프로그램 권리 제공자는 `(tenant, rights, program_sha256, intended_use)`에
정확히 `True`를 반환해야 한다. `policy_version`도 고정한다. 기본 허용/권리 캐시는 없다.
농장 원천·계정 권리와 별도로 저장에는 해당 프로그램의 `research_calculation`과
`research_display` 모두, 조회에는 `research_display`를 반환/commit 전에 확인한다.

첫 저장 판본은 **명시적인 합성 수식 프로그램**을 받는다. 모든 초기조건/forcing/
연속·사건 제거 블록의 origin은 `synthetic`이어야 한다. 실제 관측·외부 참조 입력은
원본/단위/QC/권리 감사를 연결하는 후속 판본까지 거부한다. 일반 참조 계수를
등록 농장의 품종 프로필로 승인하지 않는다.

`put(tenant, request_raw)`의 canonical UTF-8 JSON은 다음 닫힌 형태다.

```json
{
  "study_id": "crop-study-1",
  "revision": "r1",
  "farm": {
    "scenario_id": "farm-1",
    "scenario_revision": "r1",
    "registration_sha256": "<64 lowercase hex>",
    "crop_id": "crop-1"
  },
  "program": {
    "initial_state": {}, "segments": [], "events": [],
    "output_times": [], "solver": {}
  },
  "rights": {
    "declaration_id": "self-authored-crop-1", "revision": "r1",
    "program_sha256": "<SHA-256 of canonical program before numeric normalization>",
    "ownership_asserted": true, "access": true, "store": true,
    "transform": true, "use": true, "display": true, "redistribute": false,
    "available_at": "2026-09-28T00:00:00Z"
  }
}
```

빈 program은 형태 예시이며 실행 입력이 아니다. 실제 요청에는 적분 계약의
완전한 초기조건·UTC 구간·단위·출처 ID·solver가 필요하다.
연구/판본/농장/작물/선언/각 입력 ID는 200자 이내의 기존 ASCII 식별자 규칙을 쓴다.
중복 JSON 키·비유한 값·추가 키·비canonical bytes를 거부한다.
전체 요청 상한은 16 MiB, 저장 packet 상한은 64 MiB이며 적분의
20,000건/1,000,000단계 상한도 유지한다. 이는 연구 연산의 자원 경계다.

지정 불변 농장 등록의 현재 원천·권리와 등록 hash를 다시 읽는다. 작물 ID는 그
등록에 실제로 존재하고 계산 UTC 구간 전체가 작물 occupancy와 농장 KST 평가 기간에
들어가야 한다. 선언 available_at은 농장 decision_at보다 늦을 수 없다.
crop/batch/zone, 농장/원천 binding hash, floor area와 `per_m2_floor`를 저장하며
식재 면적으로 암묵적으로 환산하지 않는다. 선언/계수/시각 기록은 G0 승인이 아니다.

## 불변 packet과 재시도

서버는 정확한 요청·profile bytes·notice bytes를 보존하고 기존 적분기를 호출한다.
packet은 `stored_unpublished_research`, `synthetic_crop_math_only`, 적분 결과의
`software_research_only`를 유지하고 profile의 등록 작물 적용성을
`unvalidated_for_registered_crop`로 기록한다. 수치 hold도 진단/마지막 확인 상태를
저장할 수 있으며 완료 시계열로 바꾸지 않는다. 무효 요청은 저장하지 않는다.

`crop-result-v1:<sha256>`는 result_id를 제외한 packet의 canonical bytes hash다.
정규화 전 요청과 적분 manifest의 정규화 입력 hash, profile/model/solver/code/결과 hash를
구분한다. packet bytes SHA-256과 영역 구분 HMAC-SHA256도 저장한다. HMAC 키는
명시적인 32 bytes 이상 비밀이며 packet·로그·공개 manifest에 내보내지 않는다.
변조 검사이며 독립 심사나 G1/G4 승인 서명이 아니다.

`(tenant, study_id, revision)` 유일성 제약으로 동시 재시도를 처리한다. 같은 정확한 요청은
같은 저장 packet/최초 DB 시각을 반환하고 다른 요청은 conflict다. 재시도/조회에서
긴 적분을 재실행하지 않는다. 정정은 새 revision이다. DB 시각은 저장 metadata이며
관측·공표·이용 가능 시각을 대신하지 않는다.

동시 INSERT의 기존 SQL 5초 제한을 유지하기 위해 같은 의도의 거래 잠금을
`pg_try_advisory_xact_lock`으로 확인한다. 다른 거래가 쓰는 중이면 즉시
`CropResultPending`을 반환하고 동일 요청 재시도를 요구한다. 의도 hash의 앞 64비트를
키로 쓰며 충돌은 보수적인 pending만 만들 수 있다. 유일성 제약과 정확한 packet
대사가 최종 재사용을 결정한다. 잠금은 거래 종료 시 풀린다
([PostgreSQL 16 함수](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS),
[거래 잠금 규칙](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS)).

## PostgreSQL과 현재 조회

`install_crop_result_schema(conn, schema)`는 전용 owner로 실행한다. 추가 범위는
`crop_research_results` 1표, hash/범위/고정 scope 검사, 유일성 제약, 등록 jobs의
tenant 포함 외래키, UPDATE/DELETE 거부 trigger다.
`RuntimeLoginPolicy(crop_result_storage=True)`는 기본 false다. 새 profile에서
authority에 SELECT/INSERT만 주며 나머지 3개 role의 직접 접근은 거부한다.
기존 role을 자동 갱신하거나 새 Compose/worker/큐를 만들지 않는다.

`get(tenant, result_id, farm_ref)`는 같은 요청의 farm 참조를 필수로 받는다. 미저장 ID는
None, 불일치/변조/권리 상실은 hold/denied다. 현재 principal에는 기존 농장 READ scopes와
`crop_result_read`, 저장에는 추가 `crop_result_write`가 필요하다. 새 접속의
SCRAM/role 감사, 현재 농장/원천·program 권리, policy/의존 object의 연결을 재검사한다.
현재 고정 profile/notice/code와 다르면 hold이며 이전 bytes를 바꾸지 않는다.
후속 API/3D는 이 packet의 같은 ID·UTC를 읽고 기존 Run/publication에 삽입하지 않는다.

## 이 단계의 수용 기준

1. 완료/수치 hold의 정확한 입력·profile/notice·manifest/출력을 실제 SCRAM으로
   불변 저장하고 fresh service와 별도 Python 프로세스에서도 같은 packet을 읽는다.
2. 동일/동시 재시도, 새 revision, 다른 요청의 conflict와 등록 job 외래키를 확인한다.
3. 잘못된 시각/단위/비합성 입력/선언 hash/작물/기간/등록 혼합을 저장 전에 거부한다.
4. byte/hash/서명/열의 변조, 다른 tenant/farm, 현재 scope·농장 원천·program 권리
   철회, 계산 중/commit 직전/조회 중 변경을 거부하며 실패 거래를 rollback한다.
5. 다른 role의 SELECT/INSERT, authority의 UPDATE/DELETE/TRUNCATE와 owner의
   UPDATE/DELETE가 실제 DB에서 실패한다. 기존 role/login 회귀도 확인한다.
6. 실제 CLI/시험/packet hash와 남은 입력 audit/API/3D/외부 의존성을 보고한다.

HTTP 연결·실제 작기 재현·독립 현장 검증·승인 Run·성장 3D·공개 production은
이 저장 수용에 포함하지 않으며 후속 증거가 필요하다.
