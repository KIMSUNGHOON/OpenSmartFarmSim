# 등록 수확 조회의 인증 route·OpenAPI — v1

2026-10-08. 현재 native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 응답 수용](../research/crop-harvest-public-projection-implementation-20261008.md) 뒤
이 계약·`backend/app/api_crop_harvest_route.py`·`backend/tests/test_api_crop_harvest_route.py`의3 core파일로 구현한다.

`install_harvest_routes(app, *, jobs, farms, query, principal_provider, authorized_tenant, error, access)`는
`GET /v1/crop-harvest-research-results/{result_id}`를 설치한다. query=None은 인증 후503이며 자동 구성하지 않는다.
구성된 query는 정확한 `HarvestCurrentQuery`/reader `HarvestRegistry`·현재 crop query/store이고
기존 jobs/farm/principal과 동일해야 한다. publisher·다른 타입/계정 조립·잘못된 binding은 설치 때 거부한다.

농장 query 필드는 `scenario_id,scenario_revision,registration_sha256,crop_id`다.
`view=summary` 기본값은 offset/limit을 받지 않는다. `view=records`는 offset0..262144·limit1..64,
생략 시 offset0/limit64다. ID는 등록 수확 prefix와64자리 소문자 hex다.
unknown/중복 query·canonical 아닌 정수·누락 농장·body·구형/잘못된 ID·범위는422이며 조회를 열지 않는다.

기존 READ_SCOPES와 Bearer principal 계약을 재사용한다. `_read_response`는 threadpool에서 query.open을
한 번 열어 현재 record/summary/page를 공개 투영/직렬화한다. context 종료의 권리/파일 검사를 통과한 뒤
현재 tenant/scope/credential을 재검사하고 bytes를 반환한다. 증명 발행·행 생성·등록·직접 SQL은 수행하지 않는다.
없는 현재 등록은404, 계정/scope 거부는403, 인증 부재/만료401, 현재 query/투영 hold422,
미구성/예상 밖 내부 장애503이다. 일반 오류 메시지만 노출하고 성공 응답은 no-store다.
기존 PrincipalMiddleware의 모든 응답 no-store·보안 헤더와 외부 HTTPS 인증 정책을 유지한다.

OpenAPI에는 `HarvestReplay`·닫힌 farm/ID/view/offset/limit·ServiceBearer/READ_SCOPES·위 오류를 명시한다.
설치 뒤 schema cache를 무효화한다. 기존 경로/스키마는 보존한다.
이번 자식은 기존 App에 아직 자동 설치하지 않는다. 후속 명시 operator/runtime/factory 조립에서 연결한다.

## 수용

1. 소유 Bearer ASGI 경로에서 선행 실제 DB 조회 기록의 summary/6행·분할·빈 끝과 공개 UTC/원량/단위를 대사한다.
2. 닫힌 요청/권한/없는 등록·혼합 조립·read/종료/투영 오류·투영 중 권리/credential/tenant 변경을 거부한다.
   원 bytes 공개 전에 종료 검사를 수행하고 한 context를 닫는다. RHS/행 재생성/등록/proof0을 검증한다.
3. OpenAPI의 요청/응답·Bearer/scopes·기존 경로/스키마/저장 계약 보존과 bounded bytes·FD/import/자원 정리를 확인한다.
4. 실제 모델/명령/종료·고정 source와 owned 오류 주입 범위를 기록하고 이 route 자식만 체크한다.

소유 ASGI·기록 응답/명시 오류 주입은 실제 DB authority·TLS/배포 수용이 아니다.
후속 명시 runtime/factory·실제 SCRAM/HTTPS30초·2MiB→SDK→같은 UTC 표/3D와 전체 작기 질량 부하는 별도다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4·생산/미래 마진/추천 보류를 유지한다.

## 로컬 개발 수용 — 2026-10-08 22:40 KST

[수용 기록](../research/crop-harvest-route-openapi-implementation-20261008.md)과
[불변 영수증](../research/artifacts/crop-harvest-route-openapi-implementation-reference-20261008.json)은
새72개/선행 공개 투영70개·집중142개·원 종료0·436 source/정리,
원6행/summary/분할 bytes·조회 후 철회·기존49 path/156 schema/저장 계약 보존을 기록한다.
소유 Bearer ASGI/기록 DB 응답이며 실제 DB/TLS·App/runtime·SDK/3D·제품 관문 수용은 아니다.
