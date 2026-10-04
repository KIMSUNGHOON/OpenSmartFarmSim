# 기관/50과실 구획의 농장 결합 저장 — 2026-10-05 KST

상태: **로컬 합성 연구의 실제 SCRAM 불변 저장 수용**.
[저장 계약](../contracts/crop-result-v2.md),
[실제 입력/검증·저장 hash·정리 증거](artifacts/crop-coupled-result-storage-reference-20261005.json)를 확인한다.
새 API/성장 3D·전체 실제 작기·실제 G0–G4는 후속이다.

## CLI와 필요한 변경

기존 실제 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의
`2026-10-04T19:45:00.834Z` context에서 **gpt-6.1-sol / xhigh**를 확인했다.
이 세션에서 schema/권리·시간/거래/파일 custody를 판단했고 재귀 CLI를 실행하지 않았다.
이는 개발 기록이며 제품 runtime의 별도 CLI/G1 실행 증거는 아니다.

기존 v1은 단일 프로필/결과 ID/schema에 고정돼 새 artifact를 넣을 수 없다.
따라서 `crop_coupled_research_results` 한 표와 명시적인 기본 false
`crop_coupled_result_storage` flag를 추가했다. 새 권한은 authority SELECT/INSERT다.
v1 저장·profile/notice·계산식·기존 기본 grant 목록은 유지했다. 새 큐/Compose/서버는 추가하지 않았다.

`CoupledCropResultStore`는 frozen v1의 farm/right 검사만 재사용한다.
그 코드 hash도 packet에 보존하며 source 변화 시 hold다. v2의 profile 3개·artifact/
manifest와 domain HMAC·schema/ID/SQL 경계는 별도로 검증한다.
요청 2 MiB/프로그램 1 MiB·artifact 16 MiB·packet 20 MiB를 유지한다.
같은 farm/crop/batch/zone·등록/source binding과 per_m2_floor/적용성,
원 프로그램/권리 정책·profile/model/policy/code/solver·입력/결과 hash를 묶는다.

public builder가 서버에서 합성 프로그램을 계산하며 호출자가 결과/계수/승인을
넣을 수 없다. 약 59초 계산을 수행하는 put은 HTTP handler 밖의 메서드다.
같은 완료 intent의 재시도/조회는 재적분하지 않는다. 다른 요청은 conflict이고 정정은 새 revision이다.
current farm/source/program 권리와 객체/로그인 연결을 계산 전후·commit/반환 전에 검사한다.

## 실제 시험과 수정 사항

모듈 부재 RED는 **exit 2**였다. 첫 집중 실행은 기존 시험 전용 runner의
600초 제한에 걸려 11개 통과 뒤 중단됐다. 전체 수용으로 세지 않았다.
subprocess 종료와 임시 DB/password 디렉터리 0개를 확인하고, 동일 전체 검증을
1,200초 runner 예산으로 완료했다. 제품의 시간 제한/수용 기준은 변경하지 않았다.

최종은 **564 passed / 850.85초**, skipped **0**이다.
새 저장 8개·기존 저장 8개·farm/role/login 18개·수식/artifact 530개다.
한 개 `nice -n 10` pytest 과정과 loopback SCRAM PostgreSQL 16.15 임시 클러스터를
사용했다. shared_buffers 32 MB/max_connections 24, 실제 시험은
20:11:01~20:25:14 UTC다. runner/로그 SHA와 완료·정리를 증거에 기록했다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/python -m pytest -q \
  tests/test_crop_coupled_result_store.py tests/test_crop_result_store.py \
  tests/test_farm_authoring_storage.py \
  tests/test_runtime_roles.py::test_general_roles_cannot_access_authoritative_tables \
  tests/test_runtime_roles.py::test_installer_removes_public_column_and_global_default_grants \
  tests/test_runtime_login.py::test_direct_authenticated_identity_and_idle_connection \
  tests/test_crop_coupled_artifact.py tests/test_crop_plant_cohort_integration.py \
  tests/test_crop_plant_cohort_rates.py tests/test_crop_fruit_cohorts.py \
  tests/test_crop_fruit_allocation.py tests/test_crop_fruit_transport.py \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

실제 명령은 private runner가 기존 로컬 바이너리/비밀 파일로 임시 SCRAM 서버를
준비한 환경에서 실행했다. 외부 서버/자격증명이나 추가 설치가 필요하지 않았다.
fork 결과는 큰 packet 때문에 queue를 먼저 읽은 뒤 child 종료를 확인하도록
시험을 구성했다. 수용을 위해 생산 코드를 바꾸거나 테스트를 생략하지 않았다.

## 사용자가 확인하는 저장 결과

| 저장 사례 | sample/event | 실제 packet bytes |
| --- | --- | ---: |
| 낮→밤/기관·같은 N/C 관리 | 6 / 3 | 147,711 |
| 일정 야간/terminal 흐름 | 5 / 0 | 78,412 |

두 packet의 ID/hash·UTC 저장 시각·farm/source binding·manifest는 증거에서
확인한다. 원 packet/프로그램/권리 선언은 private
`/tmp/ossf-crop-coupled-stored-case-{0,1}-20261005.json`에 있으며 공개 기록에는
자격증명/키·raw 프로그램/권리 선언을 넣지 않았다.
초과 관리 제거의 numeric hold도 확인된 과거 3개 시점/진단만 저장했다.
모든 정상/hold 조회는 현재 권리 검사를 통과해야 한다.

fresh FarmAuthoringService/store와 별도 실제 Python의 같은 bytes·최초 DB 시각,
SCRAM require_auth/사용 비밀번호를 확인했다. 이는 service 객체/프로세스 재구성
시험이며 새 HTTP 서비스 재시작/브라우저의 검증은 다음 API 단계다.
동일/동시 재사용·새 revision/conflict·try-lock pending/해제, getter/재시도의
비재계산, 원자 INSERT/rollback을 확인했다.

12개 입력 거부/5개 bytes 거부, 모든 READ scope/다른 tenant/farm·program/source 권리
철회, 계산 후/INSERT 뒤/반환 전 변경을 거부했다. 다른 3 role의 SELECT/INSERT,
authority UPDATE/DELETE/TRUNCATE·owner UPDATE/DELETE trigger, 실제 tenant 등록 FK를
확인했다. owner가 trigger를 잠시 끄고 실제 payload/hash를 고친 경우에도 HMAC로 조회를 거부했다.

수동 검토에서 닫힌 요청/packet·v1 재사용의 source pin·세 profile·HMAC와
farm/program 연결·SQL/거래 잠금·late 권리 검사·예산/오류 경계를 확인했다.
변경된 Python 5파일의 AST/공백·지역 링크와 증거 hash도 확인한다.
실제 개인정보/농장/3자 restricted 원본이나 production 비밀은 사용하지 않았다.

## 다음 조회/3D와 남은 의존성

다음 [페이지 조회 계약](../contracts/api-crop-coupled-replay-v1.md)은 같은 ID/farm/hash에서
64개 sample/8개 event·2 MiB 전체 본문을 읽는다. 원 512시점은 누락/중복 없이
보존하며 계산 HTTP 분리/비재적분과 실제 HTTPS/SCRAM 30초 본문·현재 권리/정리를 수용한다.
그 뒤 같은 저장 ID/UTC를 표·그래프/50구획 연구 3D에 연결한다.

당시에는 새 저장의 HTTP/브라우저·hosted 전체 CI를 수용하지 않았다.
선행 `784335d`의 [CI 5개/2,969개·별도 UID 4개](artifacts/crop-fruit-cohort-plant-ci-20261005.json)는
이전 순간 구획/기관 모델 판본의 실제 수용이다.
전체 작기 capacity/startup·실제 품종/forcing QC·생과·자원/경제 연결은 남아 있다.
국내 동의/독립 미래 자료 0개, actual forcing/Run 0개, G0–G4 열린 관문도 없다.
현재 fake source/rights/CLI와 시험 키를 실제 자료 승인이나 독립 custody로 보고하지 않는다.

## 후속 실제 hosted 수용 (2026-10-05 KST)

`d15cf92`의 [CI 5개](artifacts/crop-coupled-storage-ci-20261005.json)가 모두 성공했다.
Backend 3,070개·별도 UID smoke 4개, 여섯 분할의 같은 전체 목록
`1c55d10dd915d579cfa4c652c3187b84fc429040e28f3fab9d1ba36edeac22d3`,
여섯 DB/password 정리와 별도 집계 job까지 실제 로그/API로 대사했다.
Application의 실제 이미지/runtime 49개·세 Compose 정리는
[별도 증거](artifacts/crop-coupled-operator-policy-ci-20261005.json)에 있다.
이 범위는 짧은 시간 적분/artifact·v2 저장·기본 false policy 회귀 복구다.
이후 [새 API 로컬 수용](api-crop-coupled-replay-implementation.md)과 웹 페이지/수치 도형은
새 head의 hosted/브라우저 검증이 필요하다. 기존 실행은 완료까지 보존했고 재시작하지 않았다.
실제 품종/전체 작기·G0–G4 보류는 그대로다.
