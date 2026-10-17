# SDK 성공 HTTP의 할당과 남은 중첩 읽기 — 2026-10-17

[기계 증거](artifacts/crop-solar-native-HTTP-allocation-20261017.json) · [다음 작은 계약](../contracts/crop-market-held-context-reader-v1.md).

## 현재 수용 범위

기존 읽기 개선 `fce9009`의 고유92검사/현재 checkout3반복과 S1a/S2a의 수용은 유지한다.
이번에는 **제품 코드를 바꾸지 않았다**. 실제 SDK 전체는 다시 RSS hold로 정상 누적7회,
실제 hold SDK는 미실행이다. S1b/S2b/S3/S4·새 Solar 사용자 배포·최종 디자인은 미완료다.
원5root/동적 자식·두 서비스/원본·512MiB/PID/합1GiB/nominal0.25초는 유지했다.

## 성공 응답의 분리 진단

현재 SDK 원 bundle/3개 원 소스의 hash를 대사했다. 별도 소유 TLS 서버가 저장 합성 JSON을
다시 직렬화해 제공하고 Node native fetch·body reader·원 해석기의 정상/hold summary를 비교했다.
원 production API/SCRAM/current 권리나 원 HTTPS bytes를 재현한 시험이 아니다.
응답 값은 같고 Node에서 native transport/응답 값을 mock하지 않았지만 관찰 wrapper의 비용은 포함한다.

- 최초 `65255:1`은 진단 서버가 `view=summary` query를 빠뜨린 기대값 오류다. 제품 결함이나 성공으로 세지 않는다.
- 이를 고친 `10765:0`은 정상/hold 각6개 summary를 통과했다. JS heap 약10MB와 달리 Node RSS가 약84MB까지 올랐다.
- `94020:0`의 단일 `--no-wasm-tier-up` 비교는 RSS/별도 V8 할당을 줄이지 못해 기각했다.
- 실제 내장 Undici6.24.1에서48,643bytes WebAssembly compile 호출을 관측했다.
  [고정 Node22.22.3의 flags](https://raw.githubusercontent.com/nodejs/node/v22.22.3/deps/v8/src/flags/flag-definitions.h)에서
  `liftoff_only`가 eager/dynamic tiering 모두를 끄는 것을 확인했다. `wasm_tier_up`만 끄는 것은
  [dynamic 경로 전체를 끄는 것과 같지 않다](https://raw.githubusercontent.com/nodejs/node/v22.22.3/deps/v8/src/wasm/module-compiler.cc).
- `40031:0`은 같은 정상/hold 각6개에서 baseline Node RSS84,332,544/84,160,512bytes,
  `--liftoff-only`70,787,072/70,422,528bytes를 관측했다. 별도 V8 malloc 최고는
  14,301,384/14,399,680에서566,168/557,416bytes로 줄었다. JS heap은 약10MB였다.

이 결과는 이 고정 환경의 제한된 비교이며 일반적인 RSS 상한/성능/누수 원인이나 다른 프로세스의
절약을 증명하지 않는다. [Node의 memoryUsage 정의](https://nodejs.org/download/release/v22.22.3/docs/api/process.html#processmemoryusage)에
따라 RSS와 JS heap/external/ArrayBuffer를 구분했다. 제품/브라우저의 설정은 바꾸지 않았다.

## 실제 SDK 재시도는 미수용

새 원인 근거를 얻은 뒤 시험 Node에만 그 단일 옵션을 적용했다. 원 native fetch/검증 TLS,
독립 producer·SCRAM·현재 API/권리·모든 기존 요청/수치/UTC/페이지·취소/전송 기대값을 유지했다.
`18647:1`은105.057초·합1,083,203,584bytes에서 RSS hold였다. Node72,560,640bytes를
최대 합 표본에서 관측했으나 전체 수용으로 이어지지 않았다. 이 옵션/사설 실행기는 미채택이다.
관측 중 지나간 한도 내 표본은 최종 성공이 아니며, 중단 후 AssertionError는 별도 기능 결함으로 해석하지 않는다.
실제 SDK를 새 구현/할당 근거 없이 다시 실행하지 않는다.

## 현재 코드의 실제 GET 근거

`66294:0`은 별도 fresh API/소유 SCRAM/검증 TLS에서 summary와 samples offset0/limit1을
200/no-store·원 reference/최초 시각/값·단위·UTC로 대사했다. SDK는 없다.

| 관측 | 이전163개/GET | 현재153개/GET |
| --- | --- | --- |
| 두 GET 물리 연결 |326|306|
| 동시에 열린 소유 backend 최대 |3|2|
| 현재 GET별 caller | 이전 분류 미계측 | JobStore33, ThermalRunStore80, MarketHoldStore30, MarketSourceStore10 |

숫자는 이 고정 두 GET의 관측이며 전체 제품 처리량/메모리의 상한이 아니다.
동시2인120개 연결의 stack은 후보의 scoped lookup→시장 보류 보고서40개·그 내부 판단 맥락40개·
직접 판단 맥락40개였다. 현재 source/candidate/holds/context는 동일 DSN/schema·동일 policy 객체/
kind·같은 principal provider다. 기존 private transaction reader가 존재하는 것도 코드에서 확인했다.

경제 참조 `EconomicLedger.calculate`는 summary10/samples10회 실제 호출됐다. 원 작물/CLI13진입점과
SQL 변경은0이다. 경제 참조의 재검증/산술을 생략하거나 “모든 계산0”으로 표현하지 않는다.
tracemalloc·stack 관찰 비용을 포함한105.128초/합1,034,514,432bytes이며 이후 모든 추적 연결은0개였다.

## 다음 구현의 실행 가능한 기준

별도 checkout에 고정한 RED 시험 `37657:1`에서 원 request/scenario/pin·Decimal 결과/ID·
보류/맥락 검증 순서는 같았다. 두 scope는 source2+hold3+context6 연결을 열어 목표 source2만을
만족하지 못했다. 의도한 연결 수 assertion 실패이며 수용/green이 아니다. 시험 commit/hash는 기계 증거에 남겼다.

[다음 계약](../contracts/crop-market-held-context-reader-v1.md)은 같은 신원의 현재 보류/맥락 검증만
기존 후보 읽기 연결을 빌리도록 제한한다. 서명/원 행/현재 권리/경제 산술/Read Committed와
정확한 실제 identity·변경 거부·부적합 fallback·소유권/정리를 모두 유지해야 한다.
RED→구현→현재·committed 변조/역할·권리/동시·기존 회귀→GET 재계측→실제 SDK 정상/hold 순서다.
그 뒤에만 S2b 실제 저장 WebGL→S3 실행 중3D→S4 사용자 적용을 평가한다.

Backend 전체 CI [39015742702](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39015742702)는
9af2f97 소스에서 아직 실행 중이다. 완료/성공으로 세지 않으며 관찰 시간 때문에 재시작하지 않는다.
모든 로컬 종료에서 원2,148항목·두 기존 화면/자산·필수5root, FD4→4·소유 비좀비/PG/임시 PG/passfile0을 확인했다.
실제 native Codex gpt-6.1-sol/xhigh의 현재 context hash를 기록했고 재귀 CLI는0이다.

실제 농장 Run0/G0–G4 미평가/승인False·전체 goal active다. 지역/품종/시설·독립 농장과 미래
생산/판매/비용·시장 자료의 권리/검증은 외부 의존성으로 남았다. 위 작업 분해와 아직 통과하지 못한
동시 실행/CI·자료 확보 상태 때문에 전체 완료 날짜와 남은 집중시간은 미정이다.

진행 feed를 2026-10-17T08:15:19.188508Z로 게시했다. parser28개(`27744:0`),
실제 두 UI의200/no-store·새 원문 동일/기존 HTML·환기2,173파일 보존(`26923:0`)을 통과했다.
새 DOM/WebGL이나 새 Solar 배포 수용은 추가하지 않았다.
