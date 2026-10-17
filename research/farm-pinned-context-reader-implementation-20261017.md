# 농장 등록의 현재 참조 읽기 — 2026-10-17

[계약](../contracts/farm-pinned-context-reader-v1.md) · [기계 증거](artifacts/farm-pinned-context-reader-implementation-20261017.json) ·
[측정 근거](crop-solar-worker-progress-diagnostics-20261017.md).

## 변경과 실제 관측

source8423263의 새 `MarketScenarioService.validate_pinned_context`는 현재 context/hold를 먼저 읽고,
기존 전체 경제 pin 검증을 같은 candidate read_scope에서 수행한다. scope 소유 연결을 재사용한다.
현재 행·서명·scope/role/identity·Read Committed/Read Only와 부적합 fallback은 기존 reader가 검사한다.
FarmAuthoring은 받은 참조를 기존 연구/시간/농장/후보 조건과 계속 대사하고 같은 입력을 컴파일한다.
반환 참조가 별도 승인이나 농장 적합성을 뜻하지 않는다. HTTP/DB 형식·Decimal 산술 본문은 바꾸지 않았다.

실제 SCRAM 조합 조회에서 **contexts2+holds1+source1 → source1**을 확인했다.
원 context/hold·typed request/scenario/pin과 선택한 현재 검증 호출 순서가 동일하며 모든 연결을 소유 종료했다.
순서 대사 대상은 `MarketHoldStore._verified`와 `ThermalRunStore._decision_context_in_transaction`이다.
농장 고유 연구/시간/경제 join 조건은 보존했으며, 새 흐름에서는 경제 pin 검증이 그 join 조건보다 먼저 끝난다.
제품 전체 처리 시간이나 WSL 동시 worker 용량의 개선 수치로 해석하지 않는다.

## 통과한 검증과 실패 이력

- 16186:1은 fixture import 누락의 setup error여서 행동 RED가 아니다. 보완한57403:1은 새 메서드가 없어 실패했다.
- 52786:0의 첫 비교1개를 통과했다. 78944:0은 비교·현재4scope 철회/복원·부적합 provider fallback·
  다른 거래의 hold/context signature 변경을 포함한 **8개**를 통과했다.
- 42818:0은 활성 provider/key/transaction 변경의 새 연결 fallback 거부3개와 기존 농장 등록3개를 통과했다.
  기존 검사는 동일 판본/원 numeric bytes·hash/재현·잘못된 참조/권리·늦은 권한/저장 바이트 변경·게시 없음이다.
  따라서 **고유14개**다. 초기 green의1개 재실행을 추가 수로 세지 않는다.
- 최종 두 배치는 각각62.801/62.299초, 합 RSS1,050,988,544/1,056,989,184bytes였다.
  512MiB/PID·합1GiB, 새5root·원2,148항목·frozen 소스/자산·기존 두 화면,
  감독FD4→4·소유 비좀비/PG/임시/passfile0을 유지했다.

## 다음과 남은 의존성

[trace-OFF 원 정상 CI39034668788](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39034668788)는
source8423263에서 진행 중이다. 원 prototype·64걸음·chunk1·조회 주기·360/600초·RSS 상한을 유지한다.
정상 완료/원 수치·UTC·두 전진 prefix·후검사/정리를 모두 통과하기 전 정상 기능으로 수용하지 않는다.

현재 컴포넌트만 로컬 소프트웨어 수용이다. 전체 backend·독립 정상/hold/취소·계산 중3D·WSL 용량·
S3/S4·새 Solar 사용자 적용은 후속이다. 실제 품종/독립 농장 자료·자료 권리·G0–G4는 별도이며
actual farm Runs0·전체 goal active·전체 완료일 미정을 유지한다. 판단은 기록한 native6.1/xhigh이며 재귀 CLI/새 agent는 없다.

최신 상태 기록은72387:0에서5173/5174의HTTP200·no-store·원 HTML/source/5root·정리를 확인해 게시했다. 브라우저/디자인 재검사는 하지 않았다.
