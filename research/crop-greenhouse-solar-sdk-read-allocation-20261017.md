# 실제 SDK 보류와 저장 조회의 DB 연결 비용 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-sdk-read-allocation-20261017.json) · [다음 작은 계약](../contracts/crop-solar-shared-market-reader-v1.md).

## 현재 판단

지난 단계의 [S2a 저장 화면 수용](crop-greenhouse-solar-saved-web-implementation-20261017.md)과
전체 웹243브라우저/1,864단위·타입/build/audit 통과를 유지한다. 이번에는 제품 코드를 변경하지 않았다.
**실제 SDK/HTTPS S1b·저장 WebGL S2b·실행 중/사용자 적용 S3/S4는 미수용**이다.
전체 goal은 active이고 새 Solar 화면은 localhost에 미배포다.

## 새 자원 시도와 제외한 실행기

기존 SDK 첫 시험의 보존된 cluster 설정은 shared_buffers4MiB다. native 시험 도구는1/4/8/16MiB를
허용하며 이전 SDK 코드/해석기의 소스 pin과 원 bundle을 유지한 채1MiB 시험 설정을 선택했다.
개인/실제 농장 자료나 보호된 기존 PostgreSQL 설정은 변경하지 않았다.

| 실제 실행 | 결과 | 시간 | 합 RSS 최대 bytes |
| --- | --- | --- | --- |
| 48375:1 · 소유 시험 PG1MiB | RSS hold |85.346초|1,075,363,840 |
| 36051:1 · 대기 Python 부모를 shell로 exec | RSS hold |92.874초|1,075,367,936 |
| 15554:0 · 실제 HTTPS GET 분리 계측 | 진단 수용, SDK 아님 |107.956초|1,045,921,792 |

첫 설정만으로는 충분하지 않았다. 두 번째 시도는 실제 API/SDK/모든 기대값을 유지하며 대기 실행기만
바꿨다. 대기 Python19,771,392bytes와 shell1,781,760bytes를 각각 관측했지만 전체 통과로 이어지지 않았다.
이후에는 같은 SDK 동시 시험을 반복하지 않고 GET을 분리 계측했다. 이전3회와 합해 SDK 정상5회가
자원 보류이며 hold SDK는 아직 실행하지 않았다. 단계별 메모리·요청 진행이 다르므로 두 hold의
비슷한 최대값을 설정/부모 변경의 무효나 절약량으로 해석하지 않는다.

시험용 Node 전송 실행이 제품의 CLI 카운터로 잘못 잡힐 수 있는 후보 코드도 확인했다.
시험 전용 launch만 원 Popen 별칭을 사용하고 제품 Popen 계측은 유지하도록 수정했으나, 이 후보의
SDK 전체 수용은 실패했다. 공개 시험/제품에 채택하지 않았고 별도 사설 소스·오류를 보존했다.
SDK/Node heap·검증/TLS/권리/물리 모델·512MiB/PID/합1GiB/필수5root를 바꾸지 않았다.

## 실제 HTTPS 조회에서 얻은 새 근거

소유 SCRAM DB의 별도 producer와 fresh API를 사용했다. 인증된 TLS GET summary와
samples offset0/limit1은200/no-store였고 원 reference/최초 시각·summary 전체/첫 sample 값·단위·UTC가
일치했다. 원13개 작물/CLI 진입점과 SQL 변경 카운터는0이며 원 행·권리는 유지했다.
**이 진단에는 TypeScript SDK가 없으며 권리 철회/취소의 전체 SDK 검증을 수용하지 않는다.**

연결 이벤트는 총326개({'summary': 163, 'samples': 163})이며 동시에 유지된 소유 backend 최대는3이었다. 이 수는
DB connect hook에서 얻었고 각 SQL statement 수와 같지 않다. 연결 시점의 stack/RSS를 기록했으며
원자 RSS나 생산 용량의 하한으로 해석하지 않는다. 다음 경로를 실제 stack에서 확인했다.

1. 등록 농장의 참조 검증 → MarketScenarioService.validate_pinned.
2. 원천 read_scope 연결과 후보 read_scope 연결을 동시에 유지.
3. 시장 hold/DecisionContext를 검증하면서 별도 세 번째 연결을 생성.

조회 완료 뒤 추적된 Python live는 summary1,019,596 / samples1,177,042bytes,
각 추적 peak는10,858,504 /11,119,455bytes였다. API RSS는116,862,976→144,736,256,
144,834,560→150,036,480bytes다. tracemalloc/stack 수집 오버헤드를 포함하므로 생산 RSS와 같지 않다.
최종 연결은0개였고 원 데이터·FD/소유 정리를 확인했다.

## “조회 계산0”의 범위 정정

실제 stack에는 등록 농장의 연결된 경제 입력을 검증하는 MarketScenarioService._prepare →
EconomicLedger.calculate도 있었다. 이번 계측은 그 호출 횟수를 세지 않았으므로 정확한 횟수는 미정이다.
이는 관측된 calculate stack과 정상 GET, 소스의 _calculate_verified 정상 반환 경로를 대조한 판단이다.
기존 물리13진입점/SQL0 기록은 유효하나 **모든 종류의 산술0을 증명하지 않는다.**
기존 [현재 조회 계약](../contracts/crop-greenhouse-solar-current-query-v1.md)의 나열된 작물·CLI 범위와
경제 참조 재검증을 구분한다. 과거 불변 JSON/로그를 덮어쓰지 않고 이 기록으로 범위를 보완한다.
새 재배/수익 전망이나 경제 결과를 게시한 것이 아니며 산술/검증을 생략하는 최적화는 제안하지 않는다.

## 다음 수용과 남은 의존성

새 근거에 따른 다음 작은 후보는 **정확히 같은 신원의 원천/후보 읽기 연결만 공유**하는 것이다.
이전 미채택 후보는 별도 원천으로만 참고한다. 현재 실제 동일 신원 적합성과 보안 회귀를 먼저
검증해야 하며, 전체 regression 없이 그 후보를 조합/채택하지 않는다. 원 필드/후보·권리·숫자·
산술·현재 조회·역할 감사를 유지하고, 부적합한 저장소는 기존 별도 연결로 처리한다.

S1b 수용은 새 후보의 adversarial 검증 뒤 실제 SDK normal/hold·현재 및 직렬화 후 철회·잘못된
계정/판본·취소/전송 종료·원 bytes/단위/UTC·실제 FD/소유/자원을 모두 통과해야 한다.
이어 실제 HTTPS→저장 WebGL S2b, 독립 unpaused/prefix S3, 고정 판본 사용자 적용·재시작 S4를 진행한다.
원13개 작물/CLI0과 SQL0을 계속 검증하고 경제 참조 계산은 별도 계측·보존한다.

모든 종료는 원본2,148항목·소스/기존 자산·5root/동적 자식·기존 두 UI,
FD4→4와 소유 비좀비/PG/임시 PG/passfile0을 확인했다. 후보/시험 설정은 미채택이며
백엔드/전체 CI와 새 DOM/WebGL을 이번에 실행하지 않았다. 실제 native CLI gpt-6.1-sol/xhigh,
재귀 CLI0을 기록했다. 실제 농장 Run0/G0–G4 미평가/승인False다.
지역/품종/시설·독립 농장·미래 생산/판매/비용·시장 자료/권리는 여전히 외부 의존성이다.
수정 범위와 자료 확보 일정이 확정되지 않아 전체 완료 날짜/남은 집중시간은 미정이다.

진행 feed를 2026-10-17T07:08:07.684470Z로 게시했다. 현재 공개 기록의 React/기존5173 parser28검사(37821:0)와 실제16937:0의 양쪽 HTTP200/no-store·같은 새 bytes·원 HTML/환기2,173파일 보존을 확인했다. 게시 뒤 로컬 브라우저를 재실행하거나 backend/worker를 재시작하지 않았다.
