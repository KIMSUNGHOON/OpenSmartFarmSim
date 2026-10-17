# 같은 신원 원천·후보 읽기 연결 구현 — 2026-10-17

[기계 증거](artifacts/crop-solar-shared-market-reader-implementation-20261017.json) · [좁은 계약](../contracts/crop-solar-shared-market-reader-v1.md).

## 완료한 범위와 남은 범위

읽기 연결 컴포넌트를 `fce9009`로 채택했다. 별도 checkout `d67b476`에서 검증한 것과
동일한4개 core 파일을 반영하고 현재 checkout의 핵심3검사를 다시 통과했다.
**S1b 실제 SDK 전체 수용·S2b 실제 저장 WebGL·S3 실행 중·S4 사용자 적용은 미완료**다.
S2a 기록 화면/전체 웹243브라우저·1,864단위·타입/build/audit의 이전 수용은 유지한다.
새 Solar 화면을 localhost에 배포하거나 기존 API/작업자를 재시작하지 않았다.

## 실제 변경

- `market_source_store.py`: scope가 소유하는 연결을 내부 소비자에게 제공한다. 원래 ContextVar
  슬롯을 보관해, 슬롯 필드가 바뀌어도 원 토큰을 정리한다.
- `market_candidate_store.py`: exact trusted facade/store·동일 DSN/schema·같은 runtime policy 객체/
  kind/provider/tenant만 공유한다. 실제 SCRAM/password·authenticated/effective user/database,
  Read Only/Read Committed·transaction 상태·전체 role/grant 감사와 pre/post pointer를 확인한다.
  부적합 구성은 기존 별도 연결이며 공유 후 변경은 새 연결로 덮지 않고 거부한다.
- 빌린 연결은 원천만 닫고 commit한다. 원 행/권리/숫자 검증과 산술을 캐시하거나 생략하지 않는다.
  None을 제공하는 기존 scope는 API facade import 전에 기존 연결 경로를 따른다.

AST 대사에서 기존 후보18/원천29개 다른 메서드와 module-level 선언을 보존했다.
`economics.py`와 `market_scenario.py`의 bytes는 원본과 같다. 코드 검토는 correctness/
readability/architecture/security/performance를 확인했다. 사용자 고정 모델에 따라 현재 native
Codex CLI gpt-6.1-sol/xhigh에서 판단했고 재귀 CLI는 실행하지 않았다.

## 수용한 검증

| 실제 실행 | 결과 |
| --- | --- |
| 57070:1 → 65268:0 | 기존 코드에서 공유 경로가 후보 연결1개를 더 여는 RED → 후보의 같은 시험 GREEN. 숫자/기존 검사 순서는 같았다. |
| 10914:0 | 공유/기존 경로30개. 권리 철회·committed 후보 숫자/원천 입력 변조·read-only·중첩/예외·동시 context·role grant drift·정리. |
| 74500:1 / 64733:0 | 새29개 중 초기28개 통과. 마지막 실제 SQL 역할 변경의 준비가 거부돼 전체 통과로 세지 않았다. 준비를 고쳐 실제 current_user가 바뀐 뒤 RolePolicyHold로 거부하는1개를 통과했다. |
| 49979:0 | 원천14개와 기존 None-scope 경로 반복4개 =18통과. |
| 9359:0 | 경제 시나리오 접수19개: 원자성/멱등·current 권리/참조 변조·rollback·저장/replay. |
| 62600:0 | 현재 checkout의 동일 Decimal/검사 순서·source ContextVar 교체 거부·실제 SQL 역할 변경 거부3개를 반복 통과. |

**고유92개**이며 GREEN·재검증·현재 checkout의 중복 통과를 더해 고유 수를 늘리지 않는다.
같은 입력의 typed request/scenario/pin·Decimal ledger/result ID·원 검증 순서는 같았다.
비교 대상인 validate+ledger 두 scope의 연결은 기존 원천2+후보2에서 원천2+후보0으로 줄었다.
각 scope의 논리 후보 reader와 원천 reader가 같은 실제 connection이며 source만 닫는 것을 확인했다.
이는 온실의 생산량/구매 에너지/비용 예측·운영 용량이나 전체 backend CI 수용이 아니다.

새 거부 시험에는 DSN/schema/policy/provider/원천/facade/hold/ContextVar pointer 변경,
같은 값으로 바꾼 policy 객체, 잘못된 offered connection·tenant·closed/type,
Read Write/Repeatable Read/autocommit/row factory와 실제 SQL effective role 변경이 포함된다.
원래의 숫자/권리/오류 기대값을 삭제하지 않았다. 실패한 마지막 시험은 애플리케이션 수용이 아니라
실제 SET ROLE 준비 실패였다. [PostgreSQL16 GRANT의 SET 옵션](https://www.postgresql.org/docs/16/sql-grant.html)을
확인하고 소유 시험에서 그 옵션·실제 membership을 명시, transaction 경계를 재설정해 실제 role
변경을 만든 뒤 거부를 검증했다. 제품 권한을 완화한 것이 아니다.

## 실제 SDK 동시 실행은 아직 보류

`39328:1`은 원 SDK 소스 pin/실제 native fetch·소유 SCRAM/fresh producer/API/검증 TLS,
기존 모든 요청/권리/페이지/취소·전송 정리 기대값을 사용했다. 코드의 pre-SDK 실제 공유 연결
확인을 지나 정상 요청 구간까지 갔지만 **111.564초·합1,077,645,312bytes RSS hold**였다.
정상 SDK 누적6회 보류이며 hold SDK는 미실행이다. 실제 TypeScript SDK의 전체 원 수치/페이지/
current 권리·직렬화 뒤 변경·잘못된 계정/판본·취소/전송 정리 통과를 주장하지 않는다.
한도 중단 뒤의 후속 AssertionError는 별도 기능 결함의 증거로 쓰지 않는다.

동시 최대 표본의 Node는76,369,920bytes였다. 앞선 비수신 포트 진단의 약61MB는 성공 HTTP
처리의 메모리 상한을 증명하지 않는다. 이 숫자만으로 parser/heap/GC 원인이나 특정 설정의
절약량을 단정하지 않는다. 같은 실패를 근거 없이 반복하거나 새 runtime/heap flag를 조합하지 않는다.
다음은 성공 HTTP 중 실제 SDK/API의 남은 보유/일시 할당을 분리해 필요한 작은 수정만 선택한다.

소유 시험 PG1MiB/경량 실행기/Popen 카운터 분리는 제품에 채택하지 않았다. core 채택과 SDK
수용을 구분한다. 모든 종료에서 원2,148항목·필수5root/동적 자식·두 서비스/원 코드/자산,
FD4→4·소유 비좀비/PG/임시 PG/passfile0을 확인했다.512MiB/PID/합1GiB·nominal0.25초를
유지했으며 원자 RSS나 운영 용량의 하한을 주장하지 않는다. 경제 참조 재검증을 작물/CLI13진입점/
SQL0과 구분한다. 전체 backend/현재 변경의 원격 CI·새 DOM/WebGL은 아직 미실행이다.
기존 Backend 전체 CI를 변경 없이 수동 실행하기 위한 dispatch 트리거만 추가했다.

진행 기록 parser28개(`28939:0`)와 실제 두 포트 HTTP(`85132:0`)도 통과했다.
5173/5174는200·no-store·게시 원문 동일, 기존 HTML과 환기 frozen2,173파일을 보존했다.
이는 새 Solar 화면 배포나 새 브라우저/DOM/WebGL 검증이 아니다.

실제 지역/품종/시설·독립 농장/미래 생산/정산/비용·시장 자료의 권리/검증은 계속 외부 의존성이다.
실제 농장 Run0/G0–G4 미평가/승인False·전체 goal active·전체 완료일/남은 집중시간 미정을 유지한다.
