# 검증 계산 API의 별도 운영 설정 로더 — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행은 [명시적 runtime factory](crop-cycle-calculation-runtime-factory-v1.md)의 실제 로컬 수용이다.
core3파일: `backend/app/calculation_operator_config.py`,
`backend/tests/test_calculation_operator_config.py`, 이 계약. 이 문서는 구현 수용이 아니다.

## 설정과 실행 인터페이스

`load_calculation_api_runtime(config_path)`는 새 `operator-calculation-api-config-v1`만 읽는다.
최상위 필드는 원 loader의 `FIELDS`와 같고 policy는 원 필수/선택 필드에
필수 `crop_cycle_calculation_result_storage` bool 하나를 추가한다.
false는 명시적 비활성, true는 명시적 활성이다. 누락·비 bool·추가 필드·다른 판본은 거부한다.
true에는 기존 `crop_cycle_result_storage=true`도 필요하며 이 정책 오류는 dependency plugin import 전에 거부한다.
store/query의 flag/factory 결속은 선행 runtime이 해당 factory 실행과 JobStore 생성 전에 검사한다.

원 `operator_config.py`와 그 상수/전역을 변경하지 않는다. 원 보호 파일/경로·중복 JSON 키·비유한 상수
검사 helper를 재사용하고 private JSON을 구형 판본으로 다시 쓰거나 임시 설정을 만들지 않는다.
동일한 0700/0600·owner·nofollow/ACL/hardlink·읽기 전후 metadata와 크기/키 길이 규칙을 유지한다.
DSN/TLS/열·시장 key·선택 authored key·ContentAccess와 trusted `module:attribute` dependency factory를
명시적으로 구성하고 exact `ApiRuntimeDependencies`/`ApiRuntime`만 조립한다.
실패는 기존 `OperatorConfigHold('operator_config_rejected')`로 고정하며 비밀값/경로를 노출하지 않는다.

`api_service()`는 기존 `OSSF_API_CONFIG`의 사설 파일 경로로 위 로더를 호출해 service를 반환한다.
기존 `python -m app.api_serve --factory app.calculation_operator_config:api_service`로 선택한다.
기존 default entrypoint/Compose·서비스·한도는 바꾸지 않는다. 새 route는 다음 transport 자식에서 연결한다.

## 수용 기준

1. 새 판본/명시 false·true의 보호 파일을 원 helper로 읽고 전달한 flag/기존 설정과
   dependency factory의 exact config/결과 타입·숨긴 repr를 확인한다. 원 loader의 새 필드 거부는 유지한다.
2. 판본/필드/JSON·flag/prerequisite·factory 경로/결과·secret 파일 mode/symlink·누락/교체·ACL과
   env entrypoint 오류를 고정 오류로 거부한다. schema/정책 오류에서 plugin import가 없어야 한다.
3. 소유 SCRAM·현재 농장 서비스/보호 root·실제 TLS 자료와 trusted factory로 활성 판본의 실제 조립을 확인한다.
   새 store/query·same jobs/farm/current principal·재구성과 원 private files/FD·새 작물 row/Run0개를 대사한다.
   parser/context/QC/RHS/advance/게시를 금지하고 DB/schema/role/passfile/PG PID·임시 tree를 정리한다.
4. 기존 설정/기동·새 runtime 집중 회귀와 별도 Python import 시작 순서, 원 loader/source/서명 이력을 보존한다.
   실제 명령·종료·source SHA/native CLI를 기록한다. 새 HTTPS 응답·G0–G4 수용은 별도다.

원 loader45줄의 조립 재사용·닫힌 새 정책/거부·실제 SCRAM 검증을 근거로1–2집중시간 잠정이다.
이어 route/실제 TLS1–2시간, 남은 작은 API 연결2–4집중시간 잠정이며 각 실제 수용 뒤 갱신한다.
CI 대기·전체166일 등록 prefix/복원·3D·실제 품종/국내 독립 자료 확보와 최종 제품 완료일은 포함하지 않는다.

## 로컬 구현 수용 — 2026-10-07

새 로더 전체57개/15.45초와 기존 설정·API/runtime 회귀155개/44.99초,
**고유212개 분할 검증**으로 이 자식과 명시 operator-runtime 부모를 로컬 수용한다.
단일 전체 backend 수용이나 새 HTTP 응답 수용은 아니다.
새 판본의 명시 false/true·정책/형식·보호 파일/ACL·실제 읽기 중 변경/FD·고정 오류·env와
별도 Python 세 import 순서를 확인했다. 원 loader와 선행75 source SHA는 같다.
실제 SCRAM/TLS 파일로 동일 jobs/farm/principal의 새 store/query와 네 독립 키·재구성·env service를 조립했다.
parser/context/QC/RHS/advance/게시를 금지했으며 jobs88/events88·작물 결과0행·원 파일 SHA/mode/inode·FD12는 같다.
host 인증4규칙은 SCRAM이고 소유 schema/role/passfile0·PG PID/data/임시 tree 정리를 확인했다.
첫 실제 조립 시험의 잘못된 시험 속성명 `authority`를 `input_authority`로 고쳤고
실패 로그와 정리·제품 source 불변을 보존했다. 원 설정 거부 RED도 별도 보존한다.
자세한 명령/source/로그 SHA와 보류는 [수용 기록](../research/crop-cycle-calculation-operator-loader-20261007.md)에 둔다.
다음은 [인증 route/OpenAPI → 실제 runtime/TLS](api-crop-cycle-calculation-transport-v1.md)다.
