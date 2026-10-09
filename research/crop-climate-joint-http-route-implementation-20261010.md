# 공동 작물·기후 결과의 보호 HTTP 수용 — 2026-10-10

[계약](../contracts/api-crop-climate-joint-route-v1.md)과
[불변 실행 기록](artifacts/crop-climate-joint-http-route-reference-20261010.json)을 대조해
`crop-climate-joint-http-route`와 선행 query를 포함한 `crop-climate-joint-current-http`를 **로컬 합성 소프트웨어 범위**로 수용한다.
core commit은 `1ebbabe`다. 실행 기록은31,698bytes/SHA256
`9de0e0b8c61b4be427e9633334ac5f2cb0936eb69464b0c1a2c6cf669642bf42`다.
운영 기반 고정 `d19f7c0`을 유지한다. 실제 품종/농장 작물 Run·국내 독립 검증 자료는0건이며 G0–G4는 `not_assessed`다.

## 변경과 판단 근거

현재 native Codex CLI의 실제 turn context는 `2026-10-09T21:54:37.503Z`,
`gpt-6.1-sol / xhigh`다. 원 LF SHA는 `ff628880e98aeeda4b6be5bb1a16653db1ee9b55564eb9a7a3f25cc3957ea10c`이며
원 확인 도구 `6905e1`/비공개 보존 `478216`을 기록했다. 재귀 CLI/새 제품 runtime CLI 실행은0회다.

core7은 다음과 같다. 파일별 SHA는 실행 기록에 고정했다.

- 새 route, 기존 `api.py`, 새 route tests, HTTP 계약.
- 생성 OpenAPI snapshot과 기존 전체 경로/필수 scope 검사: 실제 경로가 추가되어 필요한2파일이다.
- 기존 joint projection의 `Reference`→`JointReference` 이름 변경: 기존 수확 `Reference`가 이름 충돌로 바뀌는 것을 막는2줄 변경이다.
  원 응답 필드·수식·저장 code·수치 identity를 바꾸지 않는다.

새 보호 GET `/v1/crop-climate-joint-research-results/{result_id}`는 원 current query를 threadpool에서 한 번 호출한다.
같은 jobs/farm/principal의 정확한 타입/결속만 설치하고 query/store가 모두 없으면 인증 후503이다.
직렬화된 원 bytes를 전달하며 API에서 새 계산·등록·SQL·authority/key를 만들지 않는다.
summary/samples/events, 페이지64/8·offset512/128, 엄격 query/본문·ID·canonical 정수,
현재 계정 전후 검사·no-store/2MiB와 일반401/403/404/422/503 오류를 연결했다.
조회가 실패한 경우에도 현재 계정을 마지막으로 검사한다.

public import는 설치 시 수행한다. 새 DTO가 원 수치 계약의 상수를 참조하므로 schema 생성 때 해당 모듈은 import되지만
새 query를 만들거나 DB/소켓을 연결하지 않는다. 서로 다른3개 fresh import 순서에서도 이를 확인했다.

## 실제 검증

최종 source1,768/core7이 같은10그룹에서 새72개(일반65/실제 SCRAM7), 공개 투영39개,
관련 API·운영자 설정·OpenAPI 회귀260개, **고유371개**를 통과했다.
기존 투영의 실제 DB2개와 운영자 설정의 실제 SCRAM1개는 이번 회귀에서 제외했고,
새 native7개가 이번 원 store/query/API 조합을 검증한다.

| 최종 그룹 | 원 exec session → 실제 terminal 도구 | pytest 통과 | guard 초 |
| --- | --- | ---: | ---: |
| pure-v4 | 33423 → eeeb8e | 65 | 9.286 |
| completed-v5 | 45451 → 67b5d4 | 1 | 75.906 |
| hold-v1 | 86554 → e10bd7 | 2 | 149.965 |
| refusals-v1 | 39874 → dacaa6 | 1 | 45.807 |
| rights-v1 | 74899 → 4679b8 | 1 | 75.654 |
| account-v1 | 3138 → 3e5e44 | 1 | 54.907 |
| cancel-v1 | 22029 → 1f255d | 2 | 107.439 |
| send-v1 | 10194 → d792db | 1 | 55.787 |
| projection-v1 | 65040 → 6488da | 39 | 4.401 |
| regression-v1 | 10427 → 9faa80 | 260 | 121.615 |

모든 원 종료 코드는0이다. `hold`/`cancel`이 함수명에도 포함돼 해당 그룹은 각각 정상/보류와 취소/전송 실패 둘 다 선택했다.
따라서 정상1개와 전송 실패1개는 다른 그룹과 중복이다. 실행373회 중 중복2회를 제외한371개만 센다.
향후 private selector는 정확한 한 경우만 선택하도록 보완했고, 이 수정으로 이미 통과한 검사를 다시 실행하지 않았다.

실제 소유32초/16걸음 producer·SCRAM DB의 completed/hold를 등록하고,
인증된 제품 `create_app`을 검증된 loopback TLS로 조회했다. 원108상태/장부/마이크로초 UTC가 담긴
summary/samples/events의 **전체 응답 bytes/SHA**가 직접 current query의 원 응답과 같다.

| 상태 | 응답 | bytes | 완료된 HTTPS 초 |
| --- | --- | ---: | ---: |
| completed | summary | 18,904 | 4.839 |
| completed | samples | 35,046 | 4.841 |
| completed | events | 73,566 | 4.849 |
| hold | summary | 18,995 | 4.870 |
| hold | samples | 24,764 | 4.874 |
| hold | events | 49,736 | 4.844 |

이는 작은 합성 조회 비용이다. 전체 작기·동시 사용자 용량으로 외삽하지 않는다.
completed와 hold의 TLS 각1개, 나머지 native5개는 실제 SCRAM/보호 ASGI 검증이다.
조기 disconnect는 ASGI422/조회0을 확인했으며, 이미 끊어진 소켓에 오류 응답이 도착했다는 주장은 하지 않는다.

자료 이용 권리/검토/농장 원천의 직렬화 중 철회9경우는422로, 인증 만료3경우는401로 원 bytes를 차단했다.
실제 취소·전송 실패 후 worker가 닫혔고, 같은 custody를 다시 열어 동일 bytes를 조회했다.
읽는 동안8종 수치 진입점 호출0·등록 행1/농장 관련 counts 불변·FD 보존을 확인했다.
기존52개 경로/211개 스키마는 값까지 동일하고 새 계약은53경로/256스키마다.

## 실패 기록과 수정

1. `completed-v1/v2/v3`는 원 bytes/TLS가 맞았으나 FD12→11/목록에서 FD10이 사라져 실패했다.
   원 목록은 기존 `/dev/null` 핸들 하나만 닫히고 추가/교체0임을 보였다. GC 선행으로는 해결되지 않았다.
   설치된 pytest의 기본 `_FileHandler`와 Uvicorn `logging.dictConfig`의 handler 정리를 확인했다.
   최종 시험은 해당 pytest 핸들의 소유/닫힘을 직접 확인한 뒤, TLS 설정 이후 전체 FD inventory10→10을 검사한다.
   앱이나 frozen HTTPS 구현은 바꾸지 않았다. `completed-v4`의 성공은 최종 계정 오류 수정 전이라 최종 수에 넣지 않는다.
2. `pure-v3`는 조회 오류와 늦은 계정 변경이 함께 발생하면 마지막 인증 검사를 건너뛰는5실패를 실제 재현했다.
   route의 오류 처리 뒤에도 현재 계정을 검사하도록 수정했고 `pure-v4`65개 및 native 만료3경우가 통과했다.
3. 첫 OpenAPI 생성은 기존 수확의 schema 이름 충돌을 발견했다. 새 클래스명만 바꾸어 기존211개 schema를 보존했다.

19개 감시 시도의 원 로그 SHA·실패/종료·범위는 실행 기록에 남겼다. 실패를 최종 성공으로 덮어쓰지 않는다.

## 보존·자원·외부 상태

nice19/.25초 관측에서 최종10그룹의 단일 PID 최대241,807,360bytes,
소유+명시 보호 트리 합 최대594,550,784bytes로512MiB/1GiB 안이다.
감시 시간 합은700.767초다. controller FD4→4, 소유 PG/process·schema/role/passfile/temp 정리,
원본2,148항목·고정 UI source/assets·기존3프로세스와5173 HTTP200을 모두 보존했다.

기존 f06fb67 hosted Web37995386488은 success다. 다른4개는 Docker Hub429·token endpoint timeout/504로
애플리케이션 검사 전에 실패했으며 새로운 backend 테스트 실패를 입증하지 않는다.
원 로그/원인 보존 후 재실행·취소·이미지/워크플로 변경 없이 hosted 수용과 후속 push를 보류한다.
이번 수정판의 hosted CI 수용은 없다.

## 다음 단계와 일정

다음은 `crop-climate-joint-runtime-assembly`다. 기존 operator의 누락/False 호환을 유지하면서
새 닫힌 판본/명시 True와 같은 jobs/farm의 정확한 input authority/custody/store/query factory를 조립한다.
잘못된 flag·factory·키/권한/모델 결속을 기동 때 거부하고, 실제 공유 DB/TLS의 원 bytes/현재 권리·계산0/정리를 확인한다.
착수 때 기존 runtime/config의 실제 검사와 대조해 변경 파일을 고정한다. 별도 queue/service는 필요하지 않다.

HTTP의 종전2–3시간 추정은 native21:54Z부터22:26Z까지 약32분의 개발/실패 추적·검증 관측과
위700.767초 최종 감시로 갱신한다. 기록/검토·commit 시간은 별도다.
다음 runtime은 기존347줄 조립·새 두 factory/닫힌 loader·이번 작은 TLS4.9초 근거로 **2–4집중시간 잠정**이다.
2026-10-10 연속 작업/새 계약 오류 없음 조건이며 CI/registry 복구 대기·웹/전체 작기·외부 자료 확보는 포함하지 않는다.
그 뒤 typed 웹 client→동일 UTC 표/3D→사용자 실행/U3를 수용한다.
전체 공동 작기/forcing·새 브라우저·최종 UI·실제 품종/독립 계측·관문과 생산/미래 마진/추천 완료일은 미확정이다.
