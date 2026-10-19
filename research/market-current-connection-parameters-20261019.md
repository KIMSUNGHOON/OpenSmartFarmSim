# 공유 읽기의 현재 연결 매개변수 — 2026-10-19

[기계 증거](artifacts/market-current-connection-parameters-20261019.json) · [선행20검사/비용 관측](solar-checkpoint-registration-scope-20261019.md).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 turn_context 시각/해시를 기록했다. 재귀 CLI/하위 에이전트는 실행하지 않았다.

## 근거와 변경

원 실제 before→advance→confirm에서 get_parameters3,963회 중2,400회가 `_shared_reader`의 필드 비교에 있었다. 같은 검증 호출이4개 구성 필드마다 전체 사전을 만들었다. 현재 메서드 안에서 한 번 읽고 모든 원 필드를 비교하도록 바꿨다. 다음 호출은 반드시 다시 읽는다. 현재 SCRAM/SQL identity/읽기 전용·isolation·역할/원천 검사는 원 방식이고 보관 cache/새 API/의존성은 없다.

[Psycopg 공식 API](https://www.psycopg.org/psycopg3/docs/api/objects.html#psycopg.ConnectionInfo.get_parameters)는 비기본 연결 매개변수 dict 반환과 password 제외를 설명한다. 웹 문서는3.3.7.dev1, 실제 lock/설치 구현은3.3.6이다. 설치 source/lock SHA를 확인했다. 직접 raw HTML 요청은403이어서 raw문서를 채택/배포하지 않았고 API 문서와 설치 source를 대조했다. 농업/경제 데이터 채택이나 관문 승인이 아니다.

## 최종 source 검증

**새9 + 기존 공유29 + 늦은 변경5 + 실제 normal/hold2 + paired1 = 고유46**을 로컬 수용했다. backend app 전체 파일 집계 SHA를 각 stage 원 source pin과 대사했다. 이전20/58·원인 관측1/시험 후보1은 더하지 않았다.

- 새9: 각 호출의 새 사전·별도 SCRAM 확인·다음 호출의 변경 거부, host/hostaddr/port/dbname/user/require_auth 불일치, 누락/조회 예외·연결/slot 정리.
- 공유29: 원 Decimal 결과/검증 순서, 기존 부적격 별도 연결,15 binding drift·4세션 변경·3잘못된 연결/tenant·실제 SQL 역할 변경과 정리.
- 늦은 변경5: 검증 도중 DB grant/principal/원천/연결/검증 객체 변경의 전체 거부.
- normal/hold2: 실제16걸음·start1/restore2·원 checkpoint/모든 sample/event 값·UTC·출처·원자 결과/게시/조회 계산0.
- 모든 stage: 보호5root/원본2,148/두 frozen UI·512MiB/PID/합1GiB·FD4→4·역할/schema/소유 PG/임시/passfile 잔여0.

| stage | 검사 | guard초 | 합 RSS 최대bytes |
|---|---:|---:|---:|
| focused-current-connection-parameters-green-v1 | 9 | 67.718080 | 1,037,172,736 |
| focused-current-connection-parameter-product-cost-v1 | 1 | 72.147852 | 1,007,550,464 |
| focused-current-parameters-shared29-v1 | 29 | 221.778580 | 1,042,698,240 |
| focused-current-parameters-bundle5-v1 | 5 | 64.297242 | 1,014,108,160 |
| focused-current-parameters-worker2-v1 | 2 | 136.161485 | 1,033,244,672 |

## 실제 비용과 한계

| 항목 | baseline2a80a1d | 현재 제품 |
|---|---:|---:|
| ABBA의 두 wall초 | 9.634945, 9.792733 | 9.450429, 9.486225 |
| 매개변수 조회 | 3,963 | 2,163 |
| 역할 감사 / SQL / 원천 읽기 | 343 / 12,919 / 3,040 | 동일(원천 순서 SHA 동일) |

현재 제품 source의 평균 감소는 **2.527%**다. 앞선 사설 후보의4.764%와 구분한다. 실제 step2→5와 UTC04/06/08/10.123456Z·counts를 확인했다. 사설 후보와 제품 함수 AST가 동일함을 대사하고 최종 module source에서 별도 ABBA를 실행했다. 이 로컬 소프트웨어 관찰을 독립 처리량/원360초 수용으로 일반화하지 않는다.

시험 보조의 첫2실패는 AST 구조/표현 가정 오류였다. 실제 RED는 원 메서드의5회 조회를 재현했다. 최종 source46만 합산한다. 정확성·단순성·모듈 경계·현재성/오류 거부·실제 비용을 검토했다.

전체 backend/browser·새 fresh exec/SIGKILL/독립64는 이번 source에서 미실행이다. 새 Solar/계산 중3D/사용자 적용·실제 품종/농장 자료/독립 검증과 G0–G4는 미수용이다. 전체 완료일 미정·실제 농장 Run0·goal active를 유지한다.

## 다음 작은 단계

원 현재성 값은 유지하면서 shared-reader마다 실행하는 SQL identity1/읽기 전용SHOW1/isolationSHOW1을 **하나의 fresh SQL 투영**으로 비교하는 시험 후보다. 실제 current 값5개·호스트/SCRAM·역할 감사343/원천3,040·원 수치/UTC·트랜잭션/늦은 변경/정리를 보존해야 한다. 현재1,200 SHOW와600 shared identity의3질의/검사를 하나로 관측할 수 있는지 검증하고 paired 비용이 일관되지 않으면 미채택한다. 기존 역할 감사15→4/pipeline/ACL/v4 후보의 재적용과 변경 없는 native64 반복은 하지 않는다. 새 구현/정상 수용은 아직 없다. PostgreSQL16의 [current_setting](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADMIN-SET)은 SHOW에 대응하는 현재 설정 조회를 정의한다. 이 문서는 투영 후보의 API 근거이며 동등성/성능 수용은 실제 시험 전까지 보류한다.

원64/chunk1/조회/retry360/RSS 정상→독립hold→HTTP취소→계산 중WebGL→WSL 용량/사용자 적용의 남은 관문은 그대로다. 이번46의 실제 guard 합은 562.103초이며 전체 제품 완료 추정이 아니다.

최종 게시 `focused-current-parameters-final46-status-v1`은 실제 자식0/guard1.362549초였다. 전체 backend app261파일 집계·원 actor/로컬 링크2,381개·두 HTTP200/동일bytes/no-store·두 frozen HTML/환기2,173파일/5root/원본/FD/정리를 대사했다. UI 코드/DOM/WebGL 재검증은 수행하지 않았다.
