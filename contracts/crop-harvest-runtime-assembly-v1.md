# 등록 수확의 명시 API runtime 조립 — v1

2026-10-08. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [인증 route](api-crop-harvest-route-v1.md) 뒤 runtime/factory 부모의 첫 조립 자식이다.
5 core파일은 이 계약·`backend/app/api_runtime.py`·`backend/app/api.py`·
`backend/tests/test_crop_harvest_runtime.py`·기존 `backend/tests/test_api_crop_harvest_route.py`의 연결 적응이다.
`contracts/openapi-v1.json`은 같은 코드에서 생성하는 산출물이다.

## 구성과 경계

`ApiRuntimeDependencies.crop_harvest_current_query_factory`는 기본None이며 repr에 비공개다.
non-None callable의 명시 선택이 활성화 조건이다. 기존 calculation storage flag와 두 calculation factory가
모두 필요하며 누락/비정상 조합은 DB/다른 factory 호출 전에 거부한다.
수확 registry는 별도 schema/reader 역할을 사용하므로 기존 runtime SQL grants를 늘리지 않는다.

factory는 `factory(calculation_current_query=...)`로 호출한다. 반환값은 정확한
`HarvestCurrentQuery`, 그 store는 정확한 reader `HarvestRegistry`, 그 원 query는 전달한 동일 객체여야 한다.
원 calculation query/store는 기존 runtime의 jobs/farm/current_principal에 결속돼 있다.
수확 schema는 원 schema와 달라야 하며 DB 이름과 실제 인증 연결의 host/port/dbname은 원 jobs와 같아야 한다.
registry._binding과 실제 SCRAM reader 연결/정확 ACL 감사를 통과한 뒤 App에 전달한다.
private passfile의 소유/모드/무ACL/inode·root identity·독립 integrity key 검사와 버전 핀은 기존 registry/query 계약을 재사용한다.
publisher·다른 DB/원 query·변경된 binding/credentials·추가 grants는 일반 조립 오류로 거부한다.

`create_app(..., crop_harvest_current_query=None)`은 기존 installer에 실제 jobs/farm/principal/계정 검사를 전달한다.
미구성 route는 인증 뒤503이다. 표준 OpenAPI에 새 경로를 넣고 기존 경로/스키마를 보존한다.
runtime은 `harvest_crop_query`, `harvest_crop_results`로 구성된 reader를 보존하며 민감 값은 repr에 노출하지 않는다.
조립은 작물 입력 해석·RHS·질량/배정 행 생성·증명 발행·결과 게시를 실행하지 않는다.

## 수용

1. 미구성/잘못된 factory·원 calculation 선행 누락을 연결 전에 거부하고 기존 기본 동작을 보존한다.
2. 실제 SCRAM에서 같은 DB/jobs/farm/query/reader·독립 key·정확 grants·재조립과 혼합/변경 거부를 확인한다.
   원 DB 이력/불변 입력·FD·private credential·registry schema/role·임시 PG/프로세스 정리를 대사한다.
3. 기본 App의 인증503과 명시 query 전달·원 ASGI bytes/철회·OpenAPI/cache/저장 계약을 검증한다.
4. 새 Python import의 연결 부작용0·계산 모듈 lazy loading과 원 명령/종료·고정 source·WSL 자원을 기록한다.

같은 프로세스의 재조립과 새 Python import는 보호된 운영 설정의 별도 프로세스 복원이 아니다.
후속 `crop-harvest-protected-factory`에서 실제 private config/dependencies factory·새 Python 같은 DB 복원을 검증한다.
그 뒤 실제 SCRAM/HTTPS30초·2MiB/원6행·철회·정리로 API 부모를 평가하고 SDK→같은 UTC 표/3D를 연결한다.
이번 자식은 위 부모·전체 작기 질량 부하·실제 품종·G0–G4·생산/미래 마진/추천을 수용하지 않는다.

## 로컬 개발 수용 — 2026-10-08 23:01 KST

[수용 기록](../research/crop-harvest-runtime-assembly-implementation-20261008.md)과
[불변 영수증](../research/artifacts/crop-harvest-runtime-assembly-implementation-reference-20261008.json)은
새17개(실제SCRAM1)/관련121개·집중138개·원 종료0·440 source/정리,
같은 reader/DB/query/farm·10거부·row0/FD12→12·원 이력/입력·OpenAPI49/156 보존·새50/201을 기록한다.
보호된 별도 프로세스 복원·실제 HTTPS·SDK/3D·부모/관문 수용은 아니다.
