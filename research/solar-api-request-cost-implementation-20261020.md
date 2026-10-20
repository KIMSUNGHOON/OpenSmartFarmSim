# API 요청별 비용 진단기 — 2026-10-20 KST

**후속 실제 관측 완료:** [24요청/서버 구간·CI39369990827의 failure27/64](solar-api-request-cost-observation-20261020.md)를 대사했다. 아래는 실행 전 로컬 수용과 접수 당시 기록이며 원 정상64/새 배포는 미수용이다.

[로컬 기계 증거](artifacts/solar-api-request-cost-local-implementation-20261020.json) · [계약](../contracts/solar-api-request-cost-diagnostics-v1.md) · [진단기](crop-solar-api-response-trace.py) · [검사](../backend/tests/test_solar_api_response_trace.py).

## 구현과 확인 범위

기존 선택 `worker-api` header에 client 요청의 monotonic 시작/끝·wall·client thread CPU와 고정 route 분류를 추가했다. 서버에서는 기존 보호 `checked`/prefix `read` 동기 본체의 outermost 구간만 wall·해당 thread CPU·실제 SQL/current/storage load/source 선택 횟수를 기록한다. SQL wall/CPU는 중첩 실행의 바깥 구간만 합친다. 이 서버 구간 밖의 인증/ASGI 전송·직렬화 비용은 포함하지 않는다.

frame/thread 식별자는 내부 수명 결속에만 사용하고 내보내지 않는다. raw path/query/ID·SQL/인자·body/locals·인증값/예외 메시지는 기록하지 않는다. 최근 응답/작업32개·예외16개·전체 동시 작업16개, Unicode 위치가 큰 경우에도 전체64KiB 상한과 drop 수·owner-only atomic 파일을 유지한다. 종료되지 않은 요청은 active로 보존하며 status/완료를 만들지 않는다.

## 최종 같은 source의 검사

**고유11검사**를 CPython3.12.3과 잠금3.12.13에서 확인했다. 두 판본을22개로 더하지 않으며 이전9검사와 실패/준비 실행도 합산하지 않는다.

- 기존 실제 status/허용 오류 코드·스레드 예외 위치·32개 기록 상한3건 보존.
- client 시간·route 분류와 path/body 비노출, 서버 thread/중첩 root·알 수 없는 SQL 제외.
- 예외 뒤 thread 재사용, 실제 겹치는 두 thread의 서로 다른 카운터, 중첩 SQL의 호출 수/바깥 시간.
- 최대 Unicode 위치와 혼합 기록의64KiB·drop/임시 파일 정리, active16 상한·frame/thread ID 미노출.
- 실제 중단된 프로세스의 incomplete client/server 기록과 거짓 응답/완료 없음.

경과 시간과 thread CPU는 [Python 공식 time 문서](https://docs.python.org/3.12/library/time.html)의 서로 다른 clock이다. 예비 검사에서263209ns CPU/263186ns wall을 관측해 정확한 `CPU<=wall` assertion이 부적절함을 확인했다. 각 clock의 원 차이와 구현/해상도를 보존하고 CPU를 wall에 맞춰 줄이지 않는다. 단위가 ns라는 것만으로 clock 간 정확한 대소를 가정하지 않는다.

첫 준비 actor 검증기는 API 전용 provider prefix를 worker에도 적용해 SHA 대조에 실패했다. 실제 실행기가 사용하는 bare worker prefix로 검증기만 수정했고, 원 기대 SHA/실제 actor 본문은 바꾸지 않았다. 이후 헤더만 제거하면 원 API `ab5a93ae…`·worker `14fe24de…`의 본문/단언이 byte 단위로 일치했다. worker header와 계측 worker SHA도 이전과 같다. 새 API header SHA는 로컬 기계 증거에 결속했다.

## 보존과 다음 실제 실행

최종 두 검사와 actor 대조의 최대 관측 합 RSS는950,177,792bytes/1GiB, 단일145,444,864bytes/512MiB다. 각 FD4→4·원5root/2,148항목·두 frozen UI/source/자산과 소유 PG/비좀비/임시/passfile 잔여0을 확인했다. 제품 app261/SHA d477b74b…는 유지했다.

로컬 진단기만 수용한 상태다. 다음은 이 새 header로 원 actor/input64/chunk1/조회·retry360/RSS를 유지한 선택 동시 관측1회이며, 그 실행의 실제 반환·원 source/actor/header·run/artifact·종료/정리를 확인하기 전51 부모를 완료 처리하지 않는다. client 대기와 서버 body CPU/SQL을 혼동하거나 계측 실행을 원 정상64/계산 중WebGL/WSL 적용으로 수용하지 않는다.

현재 native Codex CLI `gpt-6.1-sol`/`xhigh`의 문맥·원행/source/출력 SHA를 기록했다. 재귀 CLI/하위 agent·새 framework/자료 채택0이다. 전체 backend/browser CI·새 DOM/WebGL·실제 농장/경제 검증은 미실행이며, 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active다.

## 실제 관측 접수

[새 CI39369990827](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39369990827), 고정 source `7fda9ba96b68297832d5d313091d041689f4fd39`/attempt1·job118455456705를 한 번 접수했다. [접수/현재 단계 기록](artifacts/solar-api-request-cost-dispatch-20261020.json)의2026-10-20T04:35:04Z 관측에서 실제 API·worker 단계가 in_progress였다. 종료·실제 timing/counter·원 수치/UTC·artifact/자원/정리 대사 전이며51 부모와 원 정상 수용은 미완료다.
