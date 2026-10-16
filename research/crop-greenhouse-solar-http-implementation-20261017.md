# 일사 결과 보호 HTTP 로컬 수용 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-http-implementation-20261017.json) · [HTTP 계약](../contracts/api-crop-greenhouse-solar-route-v1.md).

## 구현과 검증

`GET /v1/crop-greenhouse-solar-research-results/{result_id}`를 추가했다. 정확한 SolarResultStore/SolarCurrentQuery와 같은 jobs/farm/principal provider를 명시적으로 전달한다. 미구성은 인증 후503이며 부분·혼합 조립은 설치를 거부한다. 별도 ID·operation·닫힌 query·본문 거부·samples64/events8·2MiB·no-store·판본/코드 헤더를 적용한다. 같은 current query를 threadpool에서 한 번 호출하고 오류 경로에서도 응답 직전 계정·scope를 재검사한다. 원 예외/내부 자료를 오류 응답에 포함하지 않는다.

**새 전용67/공통·기존138=고유205검사**를 통과했다. 최초 회귀 배치에서 통과한 사례와 수정 뒤 재검사한 사례를 중복 없이 합산했다.

| 검사 | 원 tool session | 결과 |
| --- | --- | --- |
| 새 ASGI·기존 환기 경로 | 71919 | 각각62개 통과. 같은 배치의 공통 검사1개 실패는 아래에 기록 |
| 새 독립 import 순서 | focused-imports-v1의 private terminal | 3개 통과·FD4→4·DB/소켓 접속0·query/계산 context 미로딩 |
| 실제 SCRAM/검증된 HTTPS 보류 | 73589 | 1개 통과·원 summary/samples/events bytes/UTC |
| 실제 SCRAM/검증된 HTTPS 정상·철회/전송 | 34968 | 1개 통과·12철회 차단·취소/전송 실패 정리 |
| 공통 OpenAPI 수정 후 전체 회귀 | 28318 | 75개 통과·계약/참조/스키마/65operation의 필수 scope |
| 독립 실제 OpenAPI 명령 | 2481 | 1개 통과·`python -B -m app.api_openapi --check` 실제 종료0/출력 없음 |

처음 공통 권한 검사에 새 일사 ID·필수 농장 query 예제가 빠져 잘못된 요청422를 검사했다. 최초 배치는198통과/1실패였고 전체 배치를 성공으로 처리하지 않았다. 시험 예제를 보완한 뒤 공통75개를 전부 재검사했다. 해당 실패를 통과 수에 더하지 않았고 재실행 사례도 한 번만 계수했다. API의 요청·권한 검증을 완화하지 않았다.

같은 소유 DB의 등록·계산 프로세스 A가 종료된 다음, 별도 B가 production 객체와 실제 인증 앱을 구성했다. 검증된 loopback TLS에서 current query의 원 공개 bytes와 완전히 일치했다. 원108상태·장부·관리 전후 진단·단위/마이크로초 UTC의 전달을 확인했으며, 그 수치 의미의 선행 검증은 [공개 투영 수용](crop-greenhouse-solar-public-query-implementation-20261017.md)을 유지한다. 수식/계수·서명 원문/저장·현재 query·기존 공개 타입은 바꾸지 않았다.

조회 단계의13수치/복원/CLI 카운터와 SQL 변경 시도는 모두0이며 기존 행 수와 새 결과1행을 보존했다. 준비/등록과 시험 DB 정리는 이 읽기 단계 밖이다. 자료 권리·검토·농장 원천·인증의 철회를 각3view 직렬화 도중 주입해12응답을 차단했다. 원천 철회는 실제 DB UPDATE가 아닌 현재 source callback fault injection이다. 조기 disconnect·잘못된 요청·없는/다른 계정 결과도 검사했다. 취소/전송 실패 후 잠금·현재 principal/FD를 정리하고 같은 custody를 다시 열어 동일 원 응답을 읽었다.

OpenAPI는60기존 경로·319기존 스키마를 모두 그대로 유지하고61경로/389스키마가 됐다. 새 operation은 닫힌 SolarReplay와 공통 인증/오류를 사용한다. 기본 operator/runtime의 새 True 지원이나 사용자 서비스 활성화는 이번 구현에 포함되지 않는다.

## 자원·보존

기존5root와 동적 자식, 원본2,148항목·두 서비스의 frozen source/자산·원 API/worker/키/배포 역할을 유지했다. 모든 감독 terminal에서 FD4→4·남은 소유 프로세스/PG/임시 PG/passfile0을 확인했다. 실제 시험 DB schema/roles도0으로 정리했다. 순차 native 프로세스는 실제 assertions를 유지한 같은 시험 함수를 사용한다. OpenAPI 명령은 가벼운 부모에서 기존 시험 함수를 실행하며 실제 자식에 `-B`만 추가한다. 재귀 Codex CLI는 실행하지 않았다.

512MiB/PID·합1GiB·명목0.25초·numeric thread1/nice19를 준수했다. 전체 관측 합 최대1,067,503,616bytes·단일 PID 최대224,645,120bytes다. 합 상한까지 여유가 작으므로 후속 런타임 검증도 같은 감독과 순차 실행을 유지해야 한다. 소유 시험 PG만 shared_buffers1MiB/JIT off를 사용했다. 정상/보류 HTTPS6응답은6.25–6.60초였으며 작은 합성32초 fixture의 관측이다. 전체 작기·동시 사용자·운영 용량 수용을 뜻하지 않는다.

## 사용자 산출물과 남은 의존성

새 HTTP 계약·코드·고유205검사·기계 증거와 두 UI의 개발 진행 기록을 확인할 수 있다. 원 session20782 실제 종료0으로5173/5174의 최신 기록 HTTP200/no-store·원 bytes 일치와 두 기존 HTML·환기 frozen2,173파일을 확인했다. 기록 시각2026-10-17 03:37:21KST·SHA b3ba81b7d9683c095133deb2c91438ad2d7061c28a892be43e656256e74837a5다. 현재 DOM/WebGL이나 새 일사3D 검증은 아니다. 기존 환기 사용자 적용을 유지한다.

합성 연구 계산 범위이며 실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False다. 전체 CI·최종 UI·실제 생산/구매 자원/경제/추천·전체 완료일은 미정이다. 독립 국내 품종/작기·농장 관측·시설/광학·시장 자료의 확보·권리/QC 검토는 소프트웨어 개발과 병행한다. 이 HTTP 단계가 실제 예측·추천 게시 조건을 바꾸지 않는다. 전체 goal은 active다.

다음 한 단계는 **전용 operator/runtime 명시 조립**이다. 수용 기준은 다음과 같다.

1. 새 flag의 누락/False는 기존 조립을 유지하고 True일 때만 정확한 solar binding/custody/store/query factory를 같은 jobs/farm/principal·권한·키에 결속한다. 부분·혼합 조립/권한 drift/잘못된 factory를 거부한다.
2. 실제 같은 SCRAM DB·검증된 TLS에서 정상/hold의 원3view·현재 계정/농장/자료 권리·늦은 철회와 조회 계산/SQL 변경0을 확인한다.
3. 기존 서버/모델/원 결과/키/역할·두 사용자 주소·5root·WSL 한도와 소유 정리를 보존한다. 이번 단계에서 사용자 활성화나 새3D를 완료로 표시하지 않는다.

이후 독립 worker/확정 prefix→typed 웹/같은 UTC3D→사용자 정상/hold/취소·재접속/재시작 순으로 진행한다. native 검증의 실제 감독 시간은 보류105.78초/정상193.09초, 공통 회귀 재검사는151.14초였다. 이는 다음 구현 전체의 완료 시간 추정이 아니며, 외부 검증 자료가 없는 전체 제품의 완료 날짜를 확정할 근거는 아직 없다.
