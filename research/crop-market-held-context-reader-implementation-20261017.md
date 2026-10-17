# 현재 보류·판단 맥락 reader와 실제 SDK 연결 — 2026-10-17

[기계 증거](artifacts/crop-market-held-context-reader-implementation-20261017.json) · [계약](../contracts/crop-market-held-context-reader-v1.md).

## 수용 범위

`6004735`의 두 core 파일을 채택했다. 별도 checkout `c2e88ce`와 bytes가 같으며
**집중 고유141검사(새49/기존92), 현재 checkout 반복4개와 실제 SDK 정상·hold를 통과**했다.
S1b는 이 소유 합성 자료/실제 애플리케이션 HTTPS의 로컬 소프트웨어 연결 범위로 수용한다.
**S2b 실제 저장 WebGL·S3 독립 unpaused/계산 중3D·S4 사용자 적용과 새 Solar 배포는 미완료**다.
S1a/S2a·이전 전체 웹 회귀의 수용을 유지한다. 새 DOM/WebGL은 이번에 실행하지 않았다.

## 실제 변경

`backend/app/market_candidate_store.py`의 활성 읽기에서 정확한 facade/source/hold/context,
동일 DSN/schema·같은 runtime policy 객체/kind/provider일 때 source-owned connection을 빌린다.
실제 SCRAM/password·authenticated/effective user/database·Read Only/Read Committed,
현재 전체 role/grant·principal과 결속을 전후 확인한다. 두 ContextVar의 슬롯을 보존해 교체/
예외/중첩/동시 context를 거부 또는 정리하며 source만 close/commit한다.
초기 부적합 구성과 범위 밖 읽기는 기존 경로다. 활성 공유의 결속 변경을 새 연결로 덮지 않는다.

기존 private transaction reader로 보류 서명/원문/맥락 hash·현재 scope resolver를 다시 읽는다.
검증 결과를 캐시하거나 경제 참조 산술을 생략하지 않는다. 기존 후보의 다른17개 메서드 AST,
`economics.py`/`market_scenario.py`/`market_hold_store.py`/`thermal_run_store.py` bytes를 보존했다.
correctness/readability/architecture/security/performance를 현재 native Codex gpt-6.1-sol/xhigh에서
검토했고 실제 context hash를 기록했다. 재귀 CLI와 다른 모델/하위 에이전트는 사용하지 않았다.

## 단계별 검증

| 실행 | 결과 |
| --- | --- |
| 37657:1 → 76426:0 | RED의 source2+hold3+context6 → GREEN source2만. request/scenario/pin·Decimal 결과/ID·핵심 보류/맥락 검증 순서 동일. |
| 54377:0 | 결속/기존 경로26개. 동등 값의 다른 policy/provider, exact type·DSN/schema/tuple/키/검증자/ContextVar 변경과 fallback. |
| 41509:0 | 현재 권리·committed 원문/서명/유효 서명이나 다른 결속·SQL 실제 role/grant/session·후검사·read-only/중첩/예외/동시 소유22개. |
| 69370:0 | 원천14+경제 접수19+같은 resolver 함수의 반환 자료 변경 거부1 =34개. |
| 81239:0 | 기존 후보/공유 reader59개. 원 권리·원 행/숫자·grant drift와 소유 정리 기대값을 유지. |
| 41542:0 | 현재 checkout의 Decimal/원 검증 순서·reference slot 교체·유효 서명/맥락 변경·실제 effective SQL role4개 반복. |

고유 수는49+92=141이다. 초기 GREEN·집중3재검사·현재 checkout4개 반복을 더해 고유 수를 늘리지 않는다.
초기 결속 배치 `98710:1`은 실패 후 소유 pytest만 boot/PID/start/pidfd 확인 뒤 SIGINT로 중단했다.
그 배치와 중단 중 pytest teardown 오류를 통과로 세지 않았다. 인증 증거를 열린 연결에서 보관하도록
시험 관찰부를 고치고, 유효하게 다시 서명한 맥락 변조의 정확한 의미 오류를 확인한 `21191:0`의3개를 통과했다.
모든 최종 검증은 위 별도 전체 묶음에서 통과했다. 제품 기대값/권한이나 원 검증을 약화하지 않았다.

## 실제 현재 GET

`92994:0`은 source6004735의 별도 fresh producer/current API·실제 SCRAM/검증 TLS를 사용했다.
summary와 samples offset0/limit1은200/no-store·원 reference/최초 시각/값/단위/UTC와 같았다.

| 이 고정 시험의 두 GET | 이전 reader | 이번 reader |
| --- | --- | --- |
| 물리 connection opens |306|186|
| psycopg open/close hook의 동시 최대 |2|1|
| 경제 참조 calculate 진입 |summary10/samples10|summary10/samples10|

현재 GET별 JobStore33/ThermalRunStore40/MarketHoldStore10/MarketSourceStore10이다.
기존 중첩120연결을 제거했고 원 경제 참조 검증·산술20회는 유지했다. 작물/CLI13진입점·SQL 변경은0이다.
모든 산술0을 뜻하지 않는다. 동시 수는 client connection hook 기준이며 PG 프로세스의 잔존/
RSS 표본과 구분한다. tracemalloc/stack 관찰을 포함한102.511초/합997,539,840bytes이며
다른 입력·부하나 배포 운영 용량의 상한을 증명하지 않는다.

## 실제 SDK 정상·hold

| 실제 native 실행 | 결과 | guard 시간 | 합 RSS 최대 bytes |
| --- | --- | --- | --- |
| 66669:0 정상 | 실제 SDK 전체 통과 |163.064초|1,065,000,960|
| 43191:0 hold | 실제 SDK 전체 통과 |148.484초|1,068,044,288|

각15개의 SDK 명령 응답을 검사했다. 원 SDK3소스/기존 bundle hash·native fetch·독립 producer·
current API의 실제 SCRAM과 검증 TLS를 사용했다. 원 summary/limit1 전체 sample/event 페이지,
값/단위/microsecond UTC·공통 참조·현재 권리 철회/복원과 직렬화 후 철회·잘못된 계정/tenant/
revision·만료·실제 in-flight cancel/drain·서버 중단의 오류/전송 정리를 통과했다.
잘못된 CA의 TLS 연결도 거부했다. 페이지/응답/권리 검사를 mock으로 대체하지 않았다.
각 Node2개 exit0, reader FD3→3, 원 counts/행 동일·current principal 복원·작물/CLI13 hook/SQL 변경0이다.

[직전 분리 계측](crop-solar-native-HTTP-allocation-20261017.md)의 근거에 따라 시험 Node에만
`--liftoff-only`와 기존64MiB old-space/1MiB semi-space를 사용했다. 소유 시험 PG1MiB·경량 shell
대기 실행기와 test-owned transport Popen 분리도 유지했다. 실제 args/DB 설정·같은 물리 source/
후보 reader·hold context 공유 preflight를 확인했다. 제품의 Node/PG 설정을 바꾼 것이 아니며,
이 사설 검증 실행기를 제품 runtime으로 채택하지 않았다. 사설 소스/hash는 보존했고 전체 CI의
SDK 실행 자동화나 브라우저/운영 용량 수용을 이 증거로 대신하지 않는다. 이전7회 RSS hold는
불변 실패 이력으로 유지하며 이번 성공으로 지우지 않는다.

## 다음 구현·의존성

1. **S2b**: S1b/S2a를 선행으로 같은 현재 HTTPS→저장 WebGL을 실제 값/원 UTC와 대사한다.
   현재 거부 시 장면 제거·재접속·기존 두 UI/원본/5root·자원과 실제 도구 종료를 확인한다.
2. **S3**: 별도 명시 runtime/독립 unpaused worker의 정상/hold/취소·전진 prefix·현재 권리·
   원 UTC/소유/동시 자원 수용 뒤 계산 중3D를 수용한다. 이번 읽기 성공은 이 관문을 해제하지 않는다.
3. **S4**: 저장/실행 중 장면을 수용한 같은 판본을 사용자 접수·재접속/재시작으로 확인한다.

새 source6004735의 Backend 전체 CI [39018578815](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39018578815)는
기존 workflow를 별도 ref에서 실행 중이다. 이전9af2f97의39015742702를 중단하지 않았다.
전체 CI 성공으로 세지 않는다. 프론트 소스는 바꾸지 않았다. 외부 지역/시설/품종·독립 농장과
미래 생산/정산/비용·시장 자료의 권리/검증은 병행해야 하는 외부 의존성이다.

원2,148항목·두 기존 화면/자산·원5root/동적 자식, guard FD4→4와 소유 비좀비/PG/
임시 PG/passfile0을 모든 종료에서 확인했다.512MiB/PID/합1GiB/nominal0.25초를 유지했다.
실제 농장 Run0/G0–G4 미평가/승인False·전체 goal active다. 다음 실제 WebGL/독립 동시 실행과
자료 확보가 남아 전체 완료 날짜/남은 집중시간은 미정이다.

진행 feed를 2026-10-17T08:56:56.037972Z로 게시했다. parser28개(`70338:0`),
최종 게시 원문의 publisher 검증과 실제 양쪽 HTTP200/no-store·동일 bytes/기존 HTML·환기2,173파일
보존(`61442:0`)을 통과했다. 새 DOM/WebGL은 재실행하지 않았다.
