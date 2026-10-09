# 검증 계산 결과의 명시적 runtime factory — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행 [순수 공개 투영](api-crop-cycle-calculation-projection-v1.md)은 로컬 수용했다.
이 계약은 `crop-cycle-calculation-operator-runtime`의 첫 자식이며 실제 로컬 수용은 아래에 기록한다.

## 현행 경계와 범위

현재 `ApiRuntimeDependencies`는 구형 cycle store/query factory만 받는다.
새 store는 새 정책 flag를, 그 farm binding은 기존 cycle 저장 flag도 요구한다.
원 `operator_config.py`는 서명 dependency이므로 별도 loader를 뒤 자식에서 추가한다.
core3파일: `backend/app/api_runtime.py`,
`backend/tests/test_crop_cycle_calculation_runtime.py`, 이 계약.
새 서비스·표·설정 판본·HTTP route를 이 자식에서 추가하지 않는다.

## 인터페이스

optional/기본 None/`repr=False`인 두 callable 필드를 명시적으로 추가한다.

- `crop_cycle_calculation_result_store_factory(*, farm_authoring_service)`
- `crop_cycle_calculation_current_query_factory(*, result_store)`

새 flag가 false이면 두 factory는 모두 None이어야 한다. true이면 둘 다 필요하며
기존 cycle 저장 flag와 기존 store factory도 명시적으로 선택해야 한다.
누락·비 callable·flag 혼합은 factory 실행/JobStore 생성·DB 연결 전에 고정 오류로 거부한다.
기존 cycle query의 선택 규칙은 유지한다. flag나 권리·키를 자동 생성하지 않는다.

runtime이 만든 같은 jobs/farm authoring service에서 exact 새
`CalculationCycleCropResultStore`만 받아 jobs/farms/server binding과
`current_principal`을 대사하고 `_binding()`을 호출한다.
같은 store를 받는 exact `CalculationCurrentCycleQuery`만 받아 `_binding()`을 호출한다.
기존 네 종류의 독립 키와 입력/결과 authority·현재 source 검사는 각 객체의 기존 경계를 따른다.
runtime은 `calculation_cycle_crop_results`와 `calculation_cycle_crop_query`로 선택된 객체를 보존한다.
새 계산/파일 쓰기·입력 파싱·권한 승인·결과 게시를 조립 부수 효과로 실행하지 않는다.

## 수용 기준

1. 새 flag만 활성화한 실제 반례부터 시작한다. 누락/혼합/비 callable·기본 None과
   숨긴 repr·기존 설정/기존 factory 회귀를 확인한다. 전후 호출·FD·원 source를 대사한다.
2. 소유 SCRAM DB와 실제 농장 authoring service·보호된 입력/서버 root·TLS 인증서로
   새 store/query의 정상 명시 조립을 확인한다. 같은 jobs/farms/current principal과 선택된 객체가 같아야 한다.
   다른 jobs/farm·구형/잘못된 store/query와 binding 검사 실패를 고정 오류로 거부한다.
3. 조립 중 원 parser/context/QC/RHS·server advance/게시를 금지하고 새 작물 row/Run0개를 대사한다.
   소유 schema/role/passfile/PG PID·임시 tree를 정리하고 실제 명령·종료·source SHA를 기록한다.
4. 원 loader/서명 이력은 보존한다. 기존 API 집중 회귀와 세 import 시작 순서를 확인한다.
   이 자식의 조립을 새 HTTP/OpenAPI/TLS 응답·브라우저/전체166일 성능 수용으로 표시하지 않는다.

다음은 별도 operator loader/config → 인증 route/실제 HTTPS30초/2MiB → client/같은 UTC3D다.
전체 등록 prefix/복원 검증과 실제 품종 입력·국내 독립 자료 확보는 별도 경로다.
G0–G4 `not_assessed`, 실제 작물 입력/검증 자료/Run0건을 유지한다.

## 로컬 수용 — 2026-10-07

[실제 보고서](../research/crop-cycle-calculation-runtime-factory-20261007.md)와
[고정 영수증](../research/artifacts/crop-cycle-calculation-runtime-factory-reference-20261007.json):
새19개 단일/기존136개 단일·고유155개 분할, 실제 SCRAM 동일 jobs/farm/principal 제공자·네 독립 키·재구성과
9개 혼합/변경 거부·parser/context/QC/RHS/advance/게시0·작물 행0·원 입력/FD·세 별도 import·73 source/정리를 확인했다.
초기 시험 디렉터리 누락의 실제 실패/진단을 보존했다. 원 loader/source와 signed 이력은 유지했다.
runtime factory 자식만 수용하며 별도 loader·새 HTTP/OpenAPI/TLS 응답·전체 작기/3D·관문은 후속이다.
