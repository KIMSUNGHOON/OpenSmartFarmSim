# 저장 기관/50구획 페이지 조회 API의 로컬 수용

2026-10-05 KST. 범위는 **합성 연구 계산의 저장 수치 조회**이며 실제 품종 생산 예측이나
G0–G4 수용이 아니다. [검증 영수증과 코드 해시](artifacts/api-crop-coupled-replay-reference-20261005.json),
[API 계약](../contracts/api-crop-coupled-replay-v1.md)을 함께 읽는다.

## 실제 판단 환경과 구현

현재 Codex CLI session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의
2026-10-04T20:56:04.192Z turn metadata에서 **gpt-6.1-sol / xhigh**를 확인했다.
이 세션에서 설계·검토했고 CLI를 재귀 실행하지 않았다. 이 개발 기록은 제품 런타임의
독립 CLI 검토·자료 승인 증거를 대신하지 않는다.

새 GET `/v1/crop-coupled-research-results/{result_id}` 한 개를 추가했다.
정확한 v2 ID와 네 farm query를 요구하며 중복/알 수 없는 query·비정규 정수·GET 본문을
거부한다. 본문은 첫 비어 있지 않은 chunk에서 거부하여 전체를 버퍼링하지 않는다.
한 응답은 최대 64 sample/8 event·직렬화 전체 2 MiB다. 원 결과의 순서·수치·단위·
불변 해시를 유지하며 offset=total은 빈 페이지, offset>total은 hold다.

닫힌 타입으로 기관 5상태·50개 N/50개 C·LAI·과실 탄소 합·누적 유량 12개·
탄소/개수 잔차와 예산, 코드/프로필/입력/결과/solver 판본을 제공한다.
tenant·forcing/RGR/S/W1 원문·권리 선언·프로필 원문·비밀 key/HMAC는 공개하지 않는다.
GET은 thread pool에서 저장 결과를 검증·투영하며 적분을 다시 실행하지 않는다.

현재 farm/source/program 권리와 HMAC custody를 읽기 때 검사하고, 응답 bytes를 만든
뒤 현재 source/program 권리를 다시 검사한다. 응답 전 principal scope/tenant도 대사한다.
권리 철회·DB 변조·혼합은 공개 수치를 반환하지 않는다. 오류는 기존 닫힌 envelope이며
예외 원문을 숨긴다. `no-store` 정책을 유지한다.

`crop_coupled_result_storage`의 생략은 false다. 활성화에는 exact bool true와
같은 실제 farm service/JobStore에 묶인 exact store factory가 함께 필요하다.
잘못된 flag/factory 조합은 DB 연결 전에 거부한다. 기존 v1 경로와 역할은 유지한다.

hold 결과의 확인된 과거 sample/event만 반환한다. 소수 초 UTC를 실제 datetime으로
비교하며 last-confirmed 진단을 정상 output으로 추가하지 않는다. mg_CH2O/m2_floor와
fruits_equivalent/m2_floor를 생과 kg·실제 과실 개수·수확·판매량으로 환산하지 않는다.

## 실패 기록과 최종 검증

1. 새 모듈이 없는 RED를 backend cwd에서 확인했다(exit 2). 첫 순수 시험은 단위 표기를
   계약의 `1`로 수정한 뒤 25 passed/34.32초였다.
2. 첫 집중 실행은 **204 passed/2 failed**, 604.93초였다. 반환 전 source 철회의
   `FarmAuthoringHold`가 503으로 분류된 부분을 422로 고쳤고, 고정 OpenAPI의 기대
   operation 목록에 실제 새 경로를 추가했다. 수정 selector 2개는 119.66초에 통과했다.
3. 최종 제품 코드의 집중 실행은 **206 passed/1 failed**, 634.92초였다.
   유일한 실패는 권한 시험 fixture에 v2 ID와 네 필수 farm query가 없어 422가 된 것이었다.
   해당 fixture 입력만 수정하고 **OpenAPI 전체 61 passed/48.58초**를 확인했다.
   제품 코드는 이 두 실행 사이에 변경하지 않았다.

최종 207개 node 목록과 실행 결과를 대사해 **207개 고유 검증의 분할 수용**으로 기록한다.
단일 실행 207개 GREEN이라고 기록하지 않는다. 초기 실패 영수증도 보존했다.
최종 현재 코드/시험/OpenAPI 8개 해시·Python AST 7개, 고정 OpenAPI 재생성 check,
수정 문서의 로컬 파일 링크 870개와 `git diff --check`도 통과했다.

| 집중 범위 | 최종 수용 node |
| --- | ---: |
| 새 coupled API | 29 |
| 기존 v1 작물 API | 18 |
| operator configuration | 59 |
| 표준 API runtime | 40 |
| OpenAPI/권한 계약 | 61 |
| 합계 | 207 |

backend cwd에서 실제 실행한 집중 범위:

```bash
.venv/bin/python -m pytest -q tests/test_api_crop_coupled_replay.py tests/test_api_crop_replay.py tests/test_operator_config.py tests/test_api_runtime.py tests/test_api_openapi.py
.venv/bin/python -m pytest -q tests/test_api_openapi.py
```

## 실제 저장 → HTTPS 검증과 정리

실제 SCRAM PostgreSQL과 표준 ApiRuntime/Bearer/TLS 서버를 사용했다.
최대 출력 시험은 **512 sample/128 관리 event**의 짧은 합성 프로그램이다.
511초/한 constant forcing segment의 용량 시험이며 24시간이나 전체 작기 검증은 아니다.
모든 8개 sample 페이지를 실제 HTTP로 읽어 원본 512개와 대사했다.
128 event 전체 페이지는 순수 투영에서 대사했고 실제 HTTPS에는 기본 8개 event 페이지를 포함했다.

**HTTPS 전체 응답 19개**, status 200×13/401×1/403×1/404×1/422×3,
최대 **11.508339초·649,718 bytes**로 기존 30초와 새 2 MiB 경계를 통과했다.
두 실제 HTTPS server/runtime를 종료·재생성한 뒤 같은 ID/최초 DB UTC·hash·수치를 확인했다.
조회 중 적분/계산 호출은 실패 sentinel로 막았다. 현재 권한·source/program 철회,
응답 생성 뒤 철회, 틀린 factory/farm/tenant, 부분 본문 거부, 공개 bytes 상한과
실제 owner의 bytes/hash 변조(HMAC 유지) 거부도 시험했다.

시험 동안 승인된 열 Run은 0개였고 기존 결과 행 수는 변하지 않았다.
두 서버와 thread를 종료하고 임시 DB cluster·password 파일을 제거했다.
영수증의 결과 ID는 제거된 시험 DB의 기록이며 현재 데모에서 조회 가능한 ID가 아니다.
원천/권리/CLI 제공자는 합성 fixture다. 실제 데이터 채택으로 세지 않는다.

WSL2에서는 한 pytest 실행 runner/한 private PG를 순차 실행했다(nice 10,
shared_buffers 32 MiB, max_connections 24). 최종 OpenAPI 실행 중 별도의 짧은
collect-only Python으로 목록만 대사한 사실을 구분해 기록했다.
새 Docker·패키지를 설치하지 않았고 브라우저/생산 동시 부하 시험은 하지 않았다.
현재 새 API 코드의 hosted CI는 별도 미수용이다. 기존 d15cf92 Backend 실행을
문서 push 때문에 취소하지 않는다.

## 다음 한 단계와 일정

다음은 [같은 저장 ID·UTC의 50구획 연구 3D 계약](../contracts/web-crop-coupled-replay-v1.md)이다.
페이지 decoder/전체성·취소, 수치 도형/공통 scale, 화면/접근성,
실제 저장→TLS→브라우저 대사의 네 묶음으로 실행한다.
잎 triangle 면적과 50개 C/N의 단위 있는 비교 도형을 원 수치에 연결하며
형태·키·색·숙기·과실 크기나 임의 애니메이션을 생산량으로 제시하지 않는다.

기존 v1 웹 209개·Chromium 10개·실제 저장/브라우저 1개의 구현을 재사용하되
새 50배열/페이지 처리가 필요하므로 **집중 개발·검증 2–4시간**을 잠정 추정한다.
로컬 연구 장면 목표는 2026-10-05~06 KST이며 브라우저 및 저장 대사를 통과해야 확정한다.
현재 API는 20:56 UTC부터 구현·진단·집중 검증을 관측했고 마지막 OpenAPI 검증까지 완료했다.
전체 작기·초기/자동 착과·생과 변환·자원/경제는 이 추정에 포함하지 않는다.

국내 동의/독립 실측 자료와 채택 forcing/실제 Run은 여전히 0건이다.
UTC/면적·수관/초기조건·관리/QC, whole-cycle 용량·품종 변환과 G0–G4 hold는 유지한다.
따라서 실제 미래 생산·수익·최적 작물 추천이나 production 완료 날짜는 아직 확정할 수 없다.
