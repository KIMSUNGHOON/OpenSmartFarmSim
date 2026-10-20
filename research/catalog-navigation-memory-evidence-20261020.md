# 목록→저장 3D의 브라우저 연결과 탐색 결함 — 2026-10-20

[기계 증거](artifacts/catalog-navigation-memory-evidence-20261020.json) ·
[앞선 API/빌드·TLS 경계](crop-result-catalog-native-connection-20261020.md).

## 수용과 보류

**고정 사이드바의 탐색 결함 수정과 실제 데스크톱/모바일 탐색 2경로를 수용했다.**
실제 목록→생장 3D의 두 시점 대조 구간도 관측했다. 그러나 전체 브라우저 실행은
메모리 한도로 중단됐으므로 수확/재접속/계정 복구·U1과 사용자 배포는 미수용이다.
기존 두 사용자 화면과 원 저장 값은 그대로 유지했다. 실제 농장 검증은 아니다.

## 원인과 제품 수정

원래 1024×768/DPR0.5에서 sidebar는 높이1098.390625px였다. 8번 성장 메뉴의
y788.84375–870.03125px는 viewport 밖이며 페이지 scrollY가0→445가 되어도
고정 위치가 같고 `elementFromPoint`가 null이었다. 원 pointer 진단은 화면을 전환하지
못했다. 다음 RED 실행도 같은 결함을 기록했으나 정리 중 RSS로 종료돼 정상 RED 종료로
합산하지 않는다. 키보드 진단의 실패를 제품 키보드 결함으로 확정하지 않았다.

`web/src/App.css`에서 데스크톱 sidebar를 viewport 높이에 맞추고 내부 세로 스크롤을
허용했다. 모바일은 기존 가로 메뉴를 위해 높이 제한/overflow를 해제했다.
`web/e2e/navigation-viewport.spec.ts`에 두 크기의 성장 메뉴→입력 복귀 회귀를 추가했다.
이 Playwright 파일의 실행은 별도이며, 아래 검증은 실제 Chromium/CDP의 같은 사용자 동작이다.

현재 source/lock/진행 feed를 고정한 개발 빌드는 종료0·1.888965초,
단일506,810,368/합1,028,153,344bytes로 통과했다. unminified 개발 빌드이며
새 minified production build의 수용은 아니다.

수정 뒤 native 검증은1024×768과390×844에서 성장 메뉴의 실제 pointer 선택과
입력 화면 복귀·메뉴의 세로 viewport 포함·문서 가로 넘침 없음을 확인했다.
데스크톱 메뉴는 내부 scrollTop366 뒤 y422.84375–504.03125px였다.
두 스크린샷을 직접 확인했다. guard15.709386초·단일284,442,624/
합986,660,864bytes·FD4→4·종료0이다. 전체 웹/백엔드 회귀는 실행하지 않았다.

## 실행기와 실제 저장 결과

`@playwright/test`와 루트 `playwright-core` import의 GC 뒤 Node RSS는 각각
115,621,888/119,017,472bytes였다. import 교체는 채택하지 않았다.
Chrome의 명령행 API는 automation 옵션이 없어 거부됐고, `/proc`의 명령행은
하나로 합쳐진 process title이었다. 소유 ancestry와 원 실행 옵션을 확보한 뒤
같은 잠긴 HeadlessChrome153.0.8010.12·파이프·사용자 옵션·viewport/DPR을 사용했다.

최소 CDP 제어기는 새 의존성 없이 시험 프로세스의 Node 메모리를 약53–62MiB로 줄였다.
공식 [Chrome DevTools Network 프로토콜](https://chromedevtools.github.io/devtools-protocol/tot/Network/)과
잠긴 Playwright의 파이프 구현을 참고했다. 실제 API는 원 CA/호스트/시각 검증과 GET-only
nginx를 거쳤다. API 응답/모델 값이나 페이지 동작을 대체하는 mock은 사용하지 않았다.

클라이언트가 완료된 이전 요청을 다음 선택에서 abort하면 `getResponseBody`가 원문을
놓칠 수 있었다. 헤더 뒤 `streamResourceContent`의 원 바이트를 관측하고, 이미 완료된
응답은 `getResponseBody`로 읽었다. 완성 JSON/길이·2MiB 한도와 HTTP 상태를 검사했다.
전체 바이트가 확보된200의 `ERR_ABORTED`만 별도 기록했다. 실패 응답을200으로 바꾸지 않았다.

v7/v8은 원166일 저장 판본의 farm→crop→생장 결과 목록→summary/sample을 실제로 읽었다.
각 실행의 `growth_first`와 `growth_second` phase는 같은 ID/UTC, 두 배열의 원 C/N100값과
단위·표, LAI 허용 오차·WebGL2/양수 draw-call 단언 뒤에 기록됐다.
v7의 원 GET6응답/전부200·body SHA와 동결 driver SHA를 보존했다.
이는 실패 실행 안에서의 부분 관측이며 최종 browser-accepted 기록은 없다.
저장 PNG는 스크롤된 구획 표를 보여 주므로 전체3D 형상의 시각 일치 증거로 쓰지 않는다.

v7은24.464637초·합1,093,750,784bytes로 중단됐다. v8에서는 대기 Python과
시험 nginx master를 제거했지만24.395435초·합1,093,455,872bytes로 다시 중단됐다.
보호 서비스와 PostgreSQL 하위 프로세스의 할당도 포함되므로 두 합계로 성능 개선율을
계산하지 않는다. 원1GiB/512MiB·600초/.25초와 건강한5root/원본2148개·두 frozen UI를
유지했다. 각 controller가 시험 소유 잔여0을 확인했다.

## 다음 작업과 남은 의존성

`product-ui-result-catalog-native`의 전체 수용은 계속 열려 있다. 다음은 두 성장 시점 뒤
수확 선택을 시작하는 구간에서 API/PG와 브라우저의 동시 할당을 실제로 분리하는 것이다.
건강한 서비스를 정지하거나 같은 실패 조건을 반복해 통과를 고르지 않는다.
원 수확3행·모바일·reload/401 제거/복구와 이후 재시작·권리 철회·늦은 응답/3상태 디자인을
모두 확인한 뒤에만 U1을 판단한다. 지원하는 기존 reader 판본과 최신 backend의 구판 CODE
지원은 별개이며 원 manifest/서명·코드 검사는 유지한다.

새 Solar normal64·독립 hold/HTTP취소/계산 중 WebGL/WSL 적용, U2–U5와 실제
자료·독립 농장/경제·시장 검증은 남아 있다. 전체 완료 날짜는 미정이며 goal active다.
native CLI gpt-6.1-sol/xhigh의 실제 문맥 SHA를 기록했고 재귀 CLI/하위 agent는0이다.
