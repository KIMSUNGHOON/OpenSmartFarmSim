# 불변 작물 연구 결과 저장 — 2026-10-04

상태: **로컬 합성 연구 저장 소프트웨어 수용, 172개 집중 시험 통과**.
[저장 계약](../contracts/crop-result-v1.md)을 먼저 작성하고 모듈 부재의 RED를 확인한 뒤
[저장 모듈](../backend/app/crop_result_store.py)과
[집중 시험](../backend/tests/test_crop_result_store.py)을 구현했다.
이 범위의 저장 체크박스만 실제 수용 증거에 따라 갱신한다.

## 이번 범위와 판단 근거

기존 CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn context
`2026-10-04T11:32:53.180Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
그 세션에서 설계/판단하며 다른 Codex CLI를 재귀 실행하지 않았다.
기존 farm 등록/현재 원천 권리와 `JobStore`의 직접 SCRAM/role 감사를 재사용한다.

합성 환경·초기조건·제거 사건을 기존 적분기로 실제 계산하고, 정확한 요청과
고정 profile/고지 bytes, model/solver/code·정규화 입력/결과 해시, scope와 수치 hold를
한 packet에 묶는다. HMAC는 변조 검사용이며 독립 심사/관문 승인 서명이 아니다.
계산 결과를 호출자가 제출하지 않는다. 같은 요청·조회에는 적분을 재실행하지 않는다.
현재 farm 원천/계정과 해당 프로그램의 권리를 반환/commit 전에 다시 확인한다.

`crop_research_results` 1표와 기본 false인 `crop_result_storage` 옵션이 추가된다.
새 결과를 불변 저장하면서 기존 승인 Run과 분리하기 위해 필요한 최소 권한 연결이다.
authority는 SELECT/INSERT, 나머지 role은 이 표의 직접 접근 없음이다.
수정/삭제는 trigger로 거부하고 기존 roles를 자동 갱신하지 않는다.
새 Compose·프로세스·큐·서버·라이브러리는 추가하지 않았다.

현재 판본은 합성 수식 프로그램만 허용한다. 실제 참조/관측 자료의 원본·권리·QC
연결은 입력 audit 뒤 후속 판본이다. `program_rights`는 명시적으로 제공해야 하고
기본 허용/권리 캐시는 없다. 시험 제공자는 **직접 작성한 합성 제공자**이며 실제
농장 동의/외부 자료 사용권/G0 수용을 증명하지 않는다. 일반 계수의 해당 등록 작물
적용성은 계속 `unvalidated_for_registered_crop`다.

## 검증과 자원

현재 환경에서 실행 중인 PostgreSQL은 없었고, 기존 사용자 경로의 PostgreSQL 16.15
바이너리를 확인했다. 운영 구성 변경/패키지 설치 없이 임시 loopback SCRAM 서버
하나를 사용한다. shared_buffers=32MB, max_connections=24, 병렬 worker=0,
전체 실행 nice=10으로 두고 기존 다른 프로세스는 건드리지 않았다.
개인 password 파일은 0600이고 시험 teardown에서 서버/비밀 파일을 제거한다.
로컬 버전은 Python 3.12.3/PostgreSQL 16.15이며 hosted의 고정 3.12.13/18.6과 구분한다.

최초 실제 DB 시험은 **19 passed / 2 failed / 544.67초**였다. 동시 재시도 하나는
동일 행의 INSERT가 커밋 전 권리 재검사와 경합해 기존 SQL 5초 제한으로 실패했다.
동일 사례를 좁혀 예외의 종류/SQLSTATE/파일·행만 진단했고 **57014 QueryCanceled**를
INSERT 위치에서 확인했다(33.51초). 공개 오류에는 DB/비밀 상세를 추가하지 않았다.
같은 의도의 비대기 거래 잠금이 사용 중이면 `CropResultPending`으로 동일 요청
재시도를 요구하도록 보완했다. SQL/접속 제한과 유일성 제약은 유지했다.
잠금의 즉시 boolean/거래 종료 해제는
[PostgreSQL 16 원 문서](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS)를
확인했다. 참고 HTML은 로컬에 보존하며 전문을 저장소로 재배포하지 않는다.

supervisor 쓰기는 읽기 전용 거래가 먼저 거부해 기대한 표 권한 오류에 도달하지
않았다. 시험에서 읽기 전용 설정을 해제한 뒤에도 실제 표 권한이 INSERT를 거부하는지
확인하도록 보완했다. 제품 연결의 기본 읽기 전용 설정은 그대로다.
15개 입력 거부 사례는 같은 불변 시험 farm에서 각각 새 요청 사본으로 검사한다.
초기 시험에서 관측한 반복 farm 준비 비용을 줄이며 사례/거부 기준을 삭제하지 않았다.

최종 명령은 기존 로컬 바이너리로 임시 서버를 준비하는 시험 전용 실행기에서
다음을 실행했다. 실행기는 저장소 밖에 있고 DSN/비밀을 출력하지 않는다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/python -m pytest -q \
  tests/test_crop_result_store.py tests/test_farm_authoring_storage.py \
  tests/test_runtime_roles.py::test_general_roles_cannot_access_authoritative_tables \
  tests/test_runtime_roles.py::test_installer_removes_public_column_and_global_default_grants \
  tests/test_runtime_login.py::test_direct_authenticated_identity_and_idle_connection \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

**172 passed / 434.49초, skipped 0**이다. 저장 8개, 기존 농장/role/login 18개,
유량/영역/적분 146개다. 실제 SCRAM/별도 Python 프로세스의 동일 bytes·최초 DB 시각,
동시 접수와 pending 후 재시도·잠금 해제, 조회/재시도 비재계산, 새 판본/conflict,
수치 hold 저장을 확인했다. 입력 거부 15사례와 bytes 경계 5사례를 각각 검사했고,
현재 scope/프로그램 계산·표시권/농장 원천 철회 및 계산 뒤/INSERT 뒤/반환 전 변경을
거부하며 rollback했다. 실제 role 권한·owner 변경 거부·등록 외래키 실패와, owner가
저장 bytes와 hash를 실제 바꾼 경우의 조회 거부도 확인했다.

실행은 12:09:17~12:16:33 UTC였고 전체 실행기 시간은 436.25초다.
최종 로그 SHA-256은
`fda0115ff69b4889cab3378e3b204f2fa45ffb15bf8e324e8ca2ee5a691c69ad`이다.
임시 서버/비밀 파일 제거를 실행기가 확인했고 이후 `pgrep -a postgres`도 비어 있었다.

[실제 저장 packet/검증 metadata](artifacts/crop-result-storage-reference-20261004.json)에서
정확한 저장 bytes·입력·계수/고지·시계열 6시점과 CLI/코드/로그/원 문서 hash를 확인한다.
result ID는 `crop-result-v1:7fea3f9dd90656b22824483eb947da7761ab19665375e8641f740b1148df9514`,
저장 packet SHA-256은 `ffbfa09d9d1bc101dcb52f7f9dfe98fa0543f8fd5f4b889592f04f1f7c3b0662`다.
공개한 자료는 모두 합성 시험 기록이며 무결성 키·DB 비밀은 포함하지 않는다.

로컬 Docker/HTTPS/브라우저·전체 백엔드는 이번 저장 수용의 증거가 아니다.
latest hosted 전체 회귀는 새 커밋에서 별도로 확인한다.

최종 검토에서 변경 문서/계약의 상대 링크 680개와 저장 packet/입력·profile/고지·
코드 hash 연결을 확인했다. `git diff --check`는 통과했고 작업 목록에서는
`crop-result-storage`만 수용으로 바뀌었다. 기존 미수용 관문/작업은 유지했다.

## 다음 사용자 산출물과 외부 의존성

다음은 `api-crop-replay`다. 현재 인증/권리 아래 정확한 farm/result ID의 연구 상태·
UTC 시계열/단위·hold를 조회하고, 이후 `web-crop-replay`가 같은 수치로 표/그래프/
성장 3D를 연결한다. 저장 성공을 승인 Run·생과 kg·미래 생산/추천으로 표시하지 않는다.
실제 Axiany 한 작기 forcing/초기기관/관리 QC와 국내 독립 농장 접근은 계속 별도다.
국내 실제 동의/독립 작기 자료는 **0건**이며 G0–G4의 미수용 관문은 유지한다.

## 후속 운영자 파일 회귀 수정 (2026-10-04)

`b4a8d18`의 [앱 CI 37203066261](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37203066261)은
API 기동 시 `operator_config.py:96`의 닫힌 policy 필드 검사로 실패했다.
새 dataclass의 `asdict()`가 기본 false인 `crop_result_storage`도 내보내지만 기존
운영자 검사에는 그 선택 필드가 없었다. 기존 직접 로컬 시험은 운영자 파일을
거치지 않아 이 결합 회귀를 검증하지 못했다. 기존 정상 파일 시험으로 같은
실패를 재현했다(1 failed/0.77초).

운영자 계약에 해당 선택 boolean 한 개만 추가했다. 이전 11필드 파일의
생략은 기본 false, 명시한 true/false는 그대로 전달하고 정수/문자열/null과 다른
필드는 거부한다. 기존 필수 필드·비밀 파일·명시적 schema/권한 검사는 유지한다.
같은 기존 세션 `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는 실행하지 않았다.
운영자 비DB 경계 집중 46개/0.80초가 통과했다. 실제 SCRAM/HTTPS 6개 및 새
hosted 앱 재수용은 후속 검증이며 이 기록만으로 전체 CI를 통과라 하지 않는다.
