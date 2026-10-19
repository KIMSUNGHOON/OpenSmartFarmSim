# 등록 조회의 연결 수명 본체 — 2026-10-19 KST

상태: **연결 관리 본체·최종 source의51개 기능 검사와 실제 paired 비용1검사를 로컬 수용**.
본체 수용 당시 관련 worker/query/HTTP 회귀·독립 원64·새 Solar 배포는 미수용이었다. 후속58 로컬 통합 수용은 아래 링크를 따른다.
[계약](../contracts/farm-registration-connection-lifetime-v1.md) ·
[구현](../backend/app/runtime_connection_scope.py) ·
[새 검사28](../backend/tests/test_registration_connection_lifetime.py) ·
[기계 증거](artifacts/registration-connection-lifetime-core-20261019.json) ·
[최종 비용 검사](artifacts/registration-connection-lifetime-core-20261019-product-cost-test.py.txt).

기준 commit은 `145c46efe7012801e843140dae761c58c60e97c1`이다. 앞선
[보호 지문 후보](market-current-reference-agreement-cost-evaluation-20261019.md)는 미채택 상태를 유지한다.
그 후보의 getter 생략이나 검사를 줄이는 방식을 사용하지 않았다.
현재 native Codex CLI `gpt-6.1-sol/xhigh`의 실제 문맥 시각/해시를 기록했다.
재귀 CLI·하위 에이전트는 사용하지 않았다.

후속 [같은 application source의 관련58 회귀·검토](registration-connection-lifetime-integration-20261019.md)로
로컬 통합을 수용했다. 현재 다음은 변경 source의 원 계측 OFF64 독립 정상이다.
아래 관련 회귀 미수용 문구는 본체52 수용 당시의 범위다.

## 구현 범위

같은 `RegistrationRead` 안의 명시적인 여섯 읽기 위치에서 물리 연결 하나를 재사용한다.
job/source/thermal의 정확한 기본 저장소·같은 policy 객체/authority·DSN/schema/principal 제공자만 지원한다.
초기 비적격 구성은 기존 경로이고, 진입 뒤 binding/code/실행 문맥 변경은 현재 등록을 거부한다.

- `read_connection(store)`는 실제 기본 Psycopg 연결을 반환한다. 원 store `.connect()`와
  현재 identity/역할 감사를 매번 실행한다. 실제 factory 요청 동안만 private ContextVar로
  유휴 연결을 빌리고, 일반 `.connect()`는 계속 새 연결을 만든다.
- 각 원 트랜잭션의 commit/rollback과 작업 행 잠금 해제 위치를 유지한다.
  시장 읽기의 `READ COMMITTED READ ONLY`도 유지한다. 바쁜 연결 안의 별도 읽기는 새 연결을 사용한다.
- 클라이언트 설정과 loader/dumper 등록 결속, 서버의 기본 트랜잭션 설정·timeout·role·search path·
  timezone/표현 설정 등을 검사한다. 원 identity 트랜잭션과 data 트랜잭션 안에 점검을 넣었다.
  추가로 긴 트랜잭션을 만들지 않았다.
- owner/등록·Task/thread·ContextVar token과 코드 상태를 확인한다. 취소·실패·변경은 등록을
  poison하고, 연결/문맥/권한 참조를 종료 시 해제한다. rollback 실패도 원 취소를 덮지 않는다.

JobStore/MarketSourceStore/ThermalRunStore의 `.connect()` 메서드 AST는 기준과 같다.
제품에서 Psycopg 전역 메서드를 교체하거나 범용 pool·교차 요청 캐시를 추가하지 않았다.
역할 SQL·수식·모델/매개변수·actor/원 입력/chunk1/조회·retry360/RSS·lock 파일은 변경하지 않았다.
추가 패키지나 lock 변경도 없다. 이 검사는 검토한 구성과 설정/등록 결속의 범위이며,
임의 Python 프로세스 메모리 변조 전체의 증명이 아니다.

## 같은 최종 source의 실제 비용

실제 SCRAM DB·같은 기존 합성 입력의 두 custody를 준비하고 step2는 원→후보,
step3은 후보→원 순서로 비교했다. 대조군은 **같은 최종 코드에서 연결 scope만 비활성화한 시험 경로**다.
기준 commit의 별도 실행이나 독립 API/worker 전체 처리량으로 확대하지 않는다.

| 실제 계산 구간 | scope OFF 초 | 최종 후보 초 | 시간 감소 |
| --- | ---: | ---: | ---: |
| step2, OFF→후보 | 6.740946074 | 5.405257600 | 19.81% |
| step3, 후보→OFF | 6.657643506 | 5.239237467 | 21.30% |

각 구간에서 다음을 실제 대사했다.

| 항목 | 대조군 | 최종 후보 |
| --- | ---: | ---: |
| 감사한 물리 backend | 144 | 1 |
| 역할 감사 / 역할 SQL | 183 / 2,745 | 183 / 2,745 |
| 원천 조회 / 순서 hash | 1,824 / 동일 | 1,824 / 동일 |
| 트랜잭션 종료 / 순서 hash | 432 / 동일 | 432 / 동일 |
| 작업 행 잠금 트랜잭션의 종료/IDLE 확인 | 24 | 24 |
| 세션 점검 SQL | 0 | 288 |
| 전체 SQL | 7,113 | 7,401 |

steps/status/counts/checkpoint/last_confirmed/times·provenance/artifact hash를 비교해 원 수치·UTC를
확인했다. 모든 감사 연결이 끝에 닫혔다. SQL 결과를 대체하지 않았다.
source trace hash는 `7b1fb256…1ea401`, transaction end trace hash는 `fcdb5ab1…acf742`로 같다.
두 구간 관측이므로 일반 성능·원64 완료 시간이나 WSL 동시 용량을 예측하는 수치로 사용하지 않는다.

초기 시험 전용 factory/context 교체 후보의 약26%/23% 감소와 초기 제품 후보의
약12.3%/10.8% 감소는 이전 source의 관측으로 분리했다.
공개한 [초기 helper](artifacts/registration-connection-lifetime-core-20261019-feasibility-helper.py.txt)와
[그 검사](artifacts/registration-connection-lifetime-core-20261019-feasibility-test.py.txt)는 제품 구현이 아니다.

## 검증과 실제 수정

| 최종 실행 | 결과 | guard 초 | 합산 최대 RSS bytes |
| --- | --- | ---: | ---: |
| 48149:0 | 기존 등록13 + 새 연결/수명28 = 41통과 | 501.628848346 | 1,005,674,496 |
| 43472:0 | 같은 최종 source의 실제 paired1통과 | 68.583361803 | 1,005,604,864 |
| 63029:1 | 일반 SCRAM/idle4·잘못된 로그인5·가짜 인증1 = child10통과, 종료 후 아래 정리 | 5.522229902 | 948,662,272 |
| 73102:0 | 일반 로그인 시험의 알려진 invalid fixture2개 정리 확인 | 0.333129177 | 816,021,504 |

최종52개 검사이며 이전 source의 성공/실패는 더하지 않았다. core41과 paired1의 guard 합계는
570.212초(약9.5분)다. 최초 개발/이전 실패/CI 대기 전체를 뜻하는 시간이 아니다.
모든 최종 실행의 제품6파일/새 검사 SHA가 같다.

새28은 물리 재사용/새 범위/일반 직접 연결·종료·잔류 참조 거부,
클라이언트/서버 설정10변경, 준비된 SQL 뒤 실제 SELECT 철회/NOLOGIN/역할 소속 변경,
별도 연결의 실제 `NOWAIT` 잠금 배제/commit 뒤 해제, body/commit/rollback 실패,
취소/child Task/동일 thread 복제 Context, 초기 비적격 경로·binding3/코드2변경을 포함한다.
기존13의 현재 원천/권한·연구/스냅샷·잘못된 args/중첩·thread·늦은 철회/코드/Decimal도 통과했다.

일반 로그인10의 시험 본문은 모두 성공했다. 감독기는 테스트가 만든 `invalid.pgpass` 두 개의
잔여 때문에1로 끝났다. 원 terminal을 수정하지 않고, 정확한 소유 경로/일반 파일/0600과
알려진 빈 값 또는 `incorrect` fixture bytes만 확인한 뒤73102에서 제거·잔여0을 검증했다.
실제 인증 파일은 삭제하지 않았다. 이를 처음부터 정리까지 정상0으로 끝난 실행으로 보고하지 않는다.

초기 실패도 기계 증거에 분리했다.

- 93653:1에서 기존 구현의 재사용 부재를 재현했고24678:0에서 최초 정상 경로를 확인했다.
- 82976:1은 권한 거부를 이미 처리한 등록에서 종료 시 같은 오류를 다시 던지는 문제였다.
  거부된 등록의 재사용 차단을 유지하고 정상 정리하도록 수정했다.
- 40628:1은 닫힌 frame의 재호출이 참조 해제 뒤 AttributeError를 만들었다. 명시 hold로 수정했다.
- 43489:1은 rollback 실패가 원 CancelledError를 덮었다. 실제 연결 종료와 원 취소 보존을 수정했다.
- 41326:1의 timezone 검사에서는 지정한 값의 실제 변경을 단언하지 않았다. 다른 값을 선택하고
  실제 변경을 확인하는 시험으로 수정한 뒤 최종41에서 통과했다.
- 88376:4는 잘못 지정한 parameter node ID로 시험0이었다. 93814:1은14개 본문 성공 뒤
  두 모듈의 같은 증거 파일 중복 생성 오류였다. [한 모듈 fixture shim](artifacts/registration-connection-lifetime-core-20261019-fixture-shim.py.txt)으로
  정리 writer를 한 번만 실행했다. 영구 시험을 중복 등록하지 않았다.

최종52/정리 실행 모두5root·원본2,148항목·기존 두 UI source/assets·512MiB/PID/합1GiB,
FD4→4·소유 프로세스/PG/임시0을 보존했다. 마지막 별도 정리 뒤 invalid passfile도0이다.
단일 PID 최대 RSS는141,316,096bytes다. core/paired의 실제 DB 역할/schema 잔여는0이다.
보호 서비스를 중단하지 않았다.

## 근거와 다음 단계

Psycopg3.3.6의 [잠금 판본](../backend/uv.lock)·설치된 context 코드 해시와 실제 실행을 확인했다.
[공식 transaction 설명](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)은
commit/rollback 경계를, [PostgreSQL16 잠금 설명](https://www.postgresql.org/docs/16/explicit-locking.html)은
트랜잭션 종료 시 행 잠금 해제를 설명한다.
[prepared statement 설명](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html)은 계획 재사용에 관한 근거다.
현재 웹 문서는3.3.7.dev1이며 설치 판본의 직접 증거를 대신하지 않는다.
이 후보에서는 준비된 SQL 뒤 실제 권한 변경 거부와 잠금 해제를 별도 실행으로 확인했다.

다음은 관련 원 worker/query/HTTP 회귀와 코드 검토다. 이52건을 해당 전체 회귀로 대신하지 않는다.
그 뒤 변경 source의 원 계측 OFF64 독립 정상→hold→실제 HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용이다.
원 actor/64/chunk1/조회·retry360/RSS·두 전진 prefix·원 수치/UTC·actor 종료0/전체 정리 기준을 유지한다.
새 CI는 아직 실행하지 않았고 최신 진단39211556239/원 정상39210494752는 이전 source의 종료된 실패다.

현재 사용자가 보는3D는 기존 합성 생장/수확과 환기다. 새 Solar는 배포하지 않았다.
실제 농장 Run0·자료 권리/독립 현장/미래/대응 비교 검증·G0–G4·실제 생산/경제 추천과
전체 완료일은 미완료/미정이다. 전체 goal은 active다.

## 게시·최종 범위 검토

43166:0에서 최종7개 source/시험·연구 helper4개의 해시/문법, 같은 source52검사와 정리 증거,
기존 `.connect()` 메서드3개 AST·원 actor/header·로컬 링크2,367개를 확인했다.
두 UI의 개발 기록은 HTTP200·동일 JSON bytes/no-store로 게시했고 원 HTML·환기2,173파일을 보존했다.
UI code/DOM/WebGL은 수정·재실행하지 않았다.
게시 guard1.622388644초·합 RSS913,375,232bytes·단일141,316,096bytes,
5root·FD4→4·소유 프로세스/PG/임시/passfile0이었다.
관련 전체 회귀·원64·새 Solar 배포·실제 자료/관문 수용으로 승격하지 않는다.
