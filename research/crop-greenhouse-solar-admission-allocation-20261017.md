# 일사 접수/임대 계측과 저장3D 개발 의존성 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-admission-allocation-20261017.json) ·
[선행 관측 수정](crop-greenhouse-solar-reclamation-and-observer-20261017.md) ·
[다음 웹 연결 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md).

이번 턴은 분리 계측과 실패 후보의 제외, 저장 결과 클라이언트의 개발 의존성 보완이다.
**제품 구현 코드는 변경하지 않았다.** 별도 checkout의 세 연결 수명 후보는 모두
실제 동시 실행 RSS 관문을 통과하지 못해 미채택이다. 새 일사3D·배포·전체 CI는 미수용이다.

## 실제 접수와 첫 작업 선택/임대

소유 SCRAM DB의 fresh configured API에서 검증된 TLS/Bearer POST202를 실행하고
API를 종료한 뒤 별도 fresh 작업자가 같은 작업을 발견·임대했다. 원64걸음 입력을
사용했지만 이 진단의 수치 적분은0걸음이며 동시 실행/최종 결과 수용은 아니다.
Pydantic/FastAPI/물리 모델/타입/권리/역할 감사/소유 범위/한도를 유지했다.

실제69294:0은26.719초·단일152,727,552/합1,035,333,632 bytes였다.
tracemalloc depth1·단계별 GC/allocator trim을 사용한 시험 전용 진단이다.
아래 RSS를 추적 없는 production RSS나 필요한 메모리의 하한으로 취급하지 않는다.

| 진단 단계 | RSS bytes | 해당 추적 구간의 live Python bytes |
| --- | --- | --- |
| API 조립 import 전 | 77,025,280 | 추적 전 |
| API 조립 뒤 | 127,107,072 | 15,721,432 |
| API 조립·GC/trim 뒤 | 124,551,168 | 추적 종료 |
| POST 뒤 | 132,018,176 | 4,268,982 |
| POST·GC/trim 뒤 | 130,482,176 | 추적 종료 |
| 작업자 import 뒤 | 70,590,464 | 추적 전 |
| 작업자/loop 생성 뒤 | 70,590,464 | 3,544 |
| 작업 발견 뒤 | 76,029,952 | 156,022 |
| 임대 뒤 | 76,349,440 | 248,274 |
| 임대·GC/trim 뒤 | 74,555,392 | 추적 종료 |

조립 단계의 큰 Python 보유 항목은 import·Pydantic fields/core schema 쪽이었다.
POST 구간에는 ASGI/HTTP 최초 사용 import가 포함된다. 이것만으로 프레임워크 설정이나
검증기를 변경할 근거로 삼지 않는다. API의 수식/CLI/SQL 변경 in GET 카운터는0이었고,
이 구간의 GET 자체는0이다. API POST의 필요한 접수 SQL을 읽기 계산0과 혼동하지 않는다.
작업자의 실제 SCRAM discovery/claim은 별도 PID에서 같은 job ID를 처리했다.

첫11054:1은26.297초/합1,030,930,432 bytes이며 진단의 첫 discovery 페이지에 정확히1개의
대상만 있을 것이라는 잘못된 단언이 실패했다. API 부분 결과는 남겼지만 전체 진단 수용에서
제외했다. 실제 cursor를 따라 대상 job을 선택하도록 고친69294를 수용했다.
제품 큐·페이지 순서·상태를 바꾸지 않았다.

## 사용하지 않는 작업자 import 비용

실제91231:0의 fresh process에서 DB 연결을 금지하고 Solar worker import 후
deterministic loop를 추가로 import했다. RSS67,047,424→즉시68,681,728→정리 후68,038,656
bytes였다. 정리 후 차이991,232 bytes다. unrelated worker 모듈을 불러오는 사실은
확인했지만 약1MB 관측만으로 새 lazy registry나 작업자 dispatch 구조를 채택하지 않는다.

## 마지막 로그 재대사와 연결 수명 후보

이전37370 실패의 종료된 전체 trace에는 첫 `_before/current` 진입과 최대 열린 DB
연결3개가 있었다. 실행 중 읽었던 초기 trace의 constructor 위치를 최종 위치로 간주하지
않는다. 첫 claim 이전에만 머물렀다는 해석은 수정한다. 양의 시간 적분/완료 checkpoint/
전진 prefix·동시 실행이 미수용이라는 이전 결론은 유지한다.

동일 원64걸음/chunk1·응답 뒤10초 조회·전체 configured API/독립 unpaused worker,
보호5root/동적 자식·512MiB/PID/합1GiB에서 별도 checkout만 변경했다.

| 후보 | 실제 도구/종료 | 시간 | 합 RSS 최대 | 관측 DB 연결 최대(API/worker) |
| --- | --- | --- | --- | --- |
| 후보 SQL 읽기 뒤 연결 회수 | 37602:1 | 38.076초 | 1,082,781,696 | 3/2 |
| 같은 신원의 source/candidate 읽기 scope 연결 | 60109:1 | 30.059초 | 1,080,963,072 | 3/2 |
| 같은 신원의 hold/context까지 읽기 scope 연결 | 30006:-15, 실행기1 | 31.011초 | 1,082,417,152 | 2/1 |

첫 후보는 연결/감사 횟수가 증가했고 메모리 관문도 통과하지 못했다. 둘째/셋째는
exact trusted store/connection·같은 DSN/schema/policy/provider/tenant·실제 SCRAM
authenticated/effective user/database·READ COMMITTED/READ ONLY·full role audit를
전후 검사하는 격리 후보였다. 후보/원 문맥/서명/현재 권리 재검증과 별도 source scope의
소유권/정리를 유지하도록 설계했지만 **보안·현재 권리·동시성 회귀 전체는 실행하지 않았다.**
이 부분 trace만으로 새 공유 세션 프로토콜을 수용하지 않는다.

셋째에서 첫 API GET 시작과 작업자의 첫 advance/current 호출을 관측했으나 GET 완료·
양의 시간 적분/완료 checkpoint·전진 prefix/최종 결과는 수용하지 못했다.
모든 후보는 미채택이며 main의 API/작업자/시장 저장소 코드를 보존했다.
별도 세 checkout의 각2,347파일과 실제 actor script/원 종료/자원 로그를 보존했다.

[PostgreSQL16의 READ COMMITTED 설명](https://www.postgresql.org/docs/16/transaction-iso.html#XACT-READ-COMMITTED)은
각 SELECT의 snapshot이 달라질 수 있음을 명시한다. 이를 전체 범위의 원자 스냅샷으로
주장하지 않았다. [Psycopg 연결 context 설명](https://www.psycopg.org/psycopg3/docs/basic/usage.html#with-connection)은
context 종료 시 연결 종료를 설명한다. 설치된 Psycopg3.3.6의 실제 연결/종료를 추적했으며
현재 웹 문서3.3.7.dev1을 설치 판본의 직접 증거로 사용하지 않는다.

## 보존과 CI

모든 실행에서 원본2,148항목·두 frozen 서비스 source/assets·보호5root,
FD4→4·소유 비좀비/PG/passfile0을 확인했다. 셋째의 terminal snapshot에는 임시 PG
디렉터리1개가 남아 있었고 controller의 `short_temp.cleanup()` 뒤 별도 감사에서 부재와
모든 관측 PG 종료·보호5root 생존을 확인했다. 원 terminal의 잔여1 기록은 수정하지 않았다.

현재 원격 CI를 직접 조회했다. 최신 해당 branch의 Backend37995386543/
Authored37995386531/Compose37995386493은10월9일 `f06fb67`의 completed/failure다.
[Backend 원 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386543)의
6분할은 disposable PostgreSQL 시작에서 실패하고 backend test 단계는 skipped였다.
이는 현재 로컬 판본의 시험 결과가 아니다. 새 CI 실행/수용을 주장하지 않는다.

## 구현 순서 보완과 다음 한 단계

수용된 결과 API는 저장 재생 클라이언트의 충분한 개발 선행이다. 저장용 웹 개발을
독립 unpaused worker의 동시 실행 성공 뒤로 묶었던 계획을 분리한다.

1. **S1a 저장 결과 해석기/요청 클라이언트:** 원 정상/hold 공개 응답 확보·원 값/단위/UTC,
   닫힌 타입/페이지/혼합 거부·취소/오류·TypeScript/기존 회귀. 현재 미구현이다.
2. **S1b/S2 실제 현재 HTTPS와 저장3D:** 실제 권리/조회·SDK와 같은 UTC의 표/그래프/
   WebGL·거부 시 제거·재접속을 수용한다. 아직 미구현/미검증이다.
3. **S3/S4 실행 중3D·사용자 적용:** 원 unpaused 정상/hold/취소·전진 prefix·동시 자원
   관문 뒤 같은 배포 판본의 재접속/재시작을 수용한다. 기존 부모는 미완료다.

이번 메모리 후보를 더 반복하거나 한도/보호 root/권리/모델/타입을 완화해 완료하지 않는다.
다음은 [웹 연결 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md)의 S1a다.
저장·실행 중3D를 각각 검증하는 선례는 [환기 계획](../tasks/plan.md)의 완료 결과/부분 결과
분해에 있다. 원5root와 한도는 모든 후속 로컬 시험에 유지한다.

native CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context와 조사/판단 출력 해시를 기록했다.
재귀 CLI0, 실제 농장 Run0·G0–G4 `not_assessed`·승인False다.
지역/품종/시설·독립 농장/미래 작기·시장 판본 자료는 외부 의존성이다.
전체 goal active·새 Solar3D/사용자 배포/전체 CI 미수용·완료일/남은 집중 시간 미정을 유지한다.

두 UI의 진행 기록을2026-10-17 13:22:14KST로 갱신했다. 실제50893:0에서 양쪽
HTTP200/no-store·동일 feed bytes·원 HTML/환기 frozen2,173파일 보존을 확인했다.
UI 코드/DOM/WebGL은 변경·재실행하지 않았다. 다음 S1a는 아직 구현 전이다.
