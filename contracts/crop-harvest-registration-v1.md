# 서버 수확 산술 등록 — v1

2026-10-08 구현 전 계약. 선행 [스키마/현재 조회 분해](crop-harvest-current-query-v1.md)와
[불변 artifact](crop-harvest-replay-v1.md)를 사용한다. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서
판단하며 재귀 CLI를 실행하지 않는다. 이 자식은 registry 제공자·집중/native 시험·이 계약3파일이다.

## 인터페이스와 신뢰 경계

`HarvestRegistry(query, policy, directory, *, dsn, integrity_key)`는 정확한 현재 crop query와
명시적 `HarvestRegistryPolicy`·기존 private 절대 디렉터리·해당 publisher/reader의 SCRAM DSN을 받는다.
DSN은 비밀번호 대신 private passfile을 사용한다. DB/로그인 주체·실제 역할/객체/권한을 연결 안에서 감사한다.
새 key는 bytes32~4096이며 원 store/custody/입력/증명 signer key와 달라야 한다.
오류에는 DSN·비밀·원문을 넣지 않는다. metadata HMAC은 별도 `ossf-crop-harvest-registration-v1` domain을 쓴다.

`put(tenant, parent_result_id, farm_ref, parameter_raw, allocation_raw)`만 서버 등록을 수행한다.
고객의 임의 key/path/hash·서명·승인 bool을 인자로 받지 않는다. reader 로그인은 put을 거부한다.
원 query/농장과 쓰기 scope·현재 `research_calculation`/`research_display` 권리를 확인한다.
두 원문은 기존 parser의 canonical bytes·합성/assumed·단위·원 source/모집단·수지 규칙과 범위 검사를 통과해야 한다.
실제 품종/외부 자료 채택 경로는 별도다.

## 저장 key·metadata·게시

서버는 schema/status/claim/승인false·tenant·parent·farm·source6필드·두 원문 SHA·code3필드의
canonical 묶음 SHA를 key로 정한다. result ID는 `crop-harvest-registered-result-v1:<key>`다.
이는 입력 식별자이며 전체 payload의 hash는 별도 `payload_sha256`이다.
`publication_code_sha256`는 registry 제공자, schema/artifact hash는 실제 선행 파일이다.
원 parent/농장·code·입력이 바뀌면 새 key/ID다. metadata는 선행 닫힌 v1 schema를 따른다.

private root는0700·같은 소유자·ACL/symlink 금지·inode 고정이며 단일 `.registry-lock`으로 게시를 직렬화한다.
key 하위 artifact의 기존512MiB/65,536파일/64행·2MiB page 제한을 유지한다.
root 전체는1GiB/131,072파일/128개 등록 디렉터리이며 생성 전 한 artifact 최대량을 예약 검사한다.
원 입력·서명 이력과 같은 파일을 덮어쓰지 않는다.

첫 게시 순서는 현재 권리→기존 DB 확인→서버 artifact 계산/불변 HEAD→원문/원 source·전체 저장 행 순서
검사→metadata/HMAC→DB INSERT→현재 권리/원 부모 재검사→commit이다.
미등록 orphan이 있으면 같은 입력에서 writer를 다시 수행해 기대 hash를 구하며 임의 HEAD를 권위로 채택하지 않는다.
SQL fixture의 자리표시자 서명은 거부한다. 파일 게시와 DB 등록 사이 실패는 DB 미게시/private orphan을 허용한다.
DB 거래 실패·게시 직전 권리 철회는 INSERT를 롤백한다.

등록된 같은 입력의 재시도는 서명·열/본문·code·원문·artifact root와 현재 권리를 검사하고
동일 record/최초 `recorded_at`을 반환한다. 원 질량/배정 행을 다시 생성하지 않는다.
일치하지 않는 기존 record는 conflict/hold이며 다른 내용으로 교체하지 않는다.
내부 `_find`/`_row`는 등록 거래와 후속 현재 query의 제공자다. 사용자 결과 조회·목록·HTTP/SDK는 후속이다.

## 수용 기준

1. 순수 검사로 닫힌 metadata/유형/해시·서버 key/ID·HMAC·code 변경·부적합 설정을 거부한다.
2. 작은 실제 SCRAM 농장/부모에서 원6행 artifact와 DB metadata·두 원문·서명·행 순서/합계를 대사한다.
3. 최초 INSERT 뒤 계산 권리만 철회하고 표시 권리는 유지한 사례에서 거래 rollback/DB0·private orphan을 확인한다.
   복원 후 실제 게시/동일 재시도와 첫 시각 보존·재시도 행 재생성0을 확인한다.
4. 다른 계정·쓰기 scope/계산 권리 누락·혼합 부모/농장/원문·reader 게시·잘못된 서명/metadata를 거부한다.
5. 기존 부모 query/역할·입력/custody SHA/mode/inode·DB 행 수를 보존하고 조회 RHS0/새 proof0·
   bounded page/root·WSL 소유 프로세스/메모리·FD·schema/role/passfile/PG/temp 정리를 확인한다.

해당 증거 뒤 `crop-harvest-registration`만 체크한다. 전체 작기 새 등록 부하와
현재 query/fresh Python 실제 DB 복원→HTTP/SDK→같은 UTC 표/3D는 후속이다.
실제 품종 계수·국내 독립 자료·실측 농장 작물 Run0건과 G0–G4 `not_assessed`, 생산/미래 마진/추천·
원격 Backend/push·구형 native25시간 원 종료 보류를 유지한다. 최종 production 완료일은 자료 확보 상태에 따라 갱신한다.

## 개발 수용과 다음 현재 query

`crop-harvest-registration`은2026-10-08 21:35 KST에 [집중/native 검증](../research/crop-harvest-registration-implementation-20261008.md)으로 수용했다.
순수37개/실제 SCRAM1개·집중38개·원 종료0·6행/서명 DB1건·계산 권리 철회 rollback/동일 재시도·
독립 HMAC/Decimal·421 source/정리를 확인했다. 시험 당시3파일의 hash/snapshot은 영수증에 보존했다.
실제 품종/농장 생산 검증과 현재 query·전체 재생 부모/관문 수용은 별도다.

다음은 `backend/app/crop_harvest_current_query.py`, `backend/tests/test_crop_harvest_current_query.py`,
`contracts/crop-harvest-registered-query-v1.md`의3 core파일이다. registry의 reader 로그인과 같은 부모 crop query를 사용한다.
현재 읽기 scope/표시 권리→서명 metadata/서버 key/hash→현재 원 부모/농장/source→파일/요약/제한 page 순으로 검사하고
반환 전 같은 등록/원 권리·파일을 재검사한다. 승인false·원 UTC/단위/가정/미배정/hold를 보존한다.
계산 권리가 없더라도 표시 권리가 있는 기존 결과 읽기는 유지하며 등록 쓰기와 구분한다.
혼합/변조/철회/다른 계정·미등록 파일 거부, fresh Python 실제 같은 DB 권한 재구성·행 재생성/RHS0·
페이지/bytes·WSL 자원/비밀 정리가 수용 기준이다. 이후 HTTP/SDK·같은 UTC 표/3D로 연결한다.
