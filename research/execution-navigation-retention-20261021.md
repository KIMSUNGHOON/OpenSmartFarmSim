# 계산 접수 후 메뉴 이동의 작업 연결 유지 — 2026-10-21

사용자는 앱 내부의 다른 메뉴로 갔다가 돌아오면 접수 정보가 사라지는 경로를 확인했다.
전체 goal은 사용자 요청에 따른 paused 상태를 유지하며 이번 버그 수정만 수행한다.

## 원인과 수정 범위

App의 조건부 렌더링이 계산 workspace를 제거했다. 해당 컴포넌트의 메모리에만 있던
접수 파일·계산 작업 ID·농장 선택과 모델 선택이 함께 초기화됐다.
화면을 제거할 때 실행되는 정리는 HTTP 조회 중단이며 서버 작업 취소 요청은 아니다.

기존 RetainedWorkspace를 계산 메뉴에도 적용하고 메뉴의 활성 여부를 계산 화면에 전달한다.
다른 메뉴에서는 조회 timer/진행 중 GET을 정리하고 prefix와 저장3D를 해제한다.
돌아오면 기존 작업을 현재 서버 상태로 다시 조회한다. 새 POST 접수나 서버 취소는 발생시키지 않는다.
접수 응답이 메뉴 이동 뒤 도착해도 같은 작업을 유지한다. 계정 변경/연결 해제는 기존 작업·선택 파일을 지운다.
새로고침/외부 사이트 이동의 영속 복원과 토큰 저장은 이번 범위에 포함하지 않는다.

## 관측 및 검증

- [CI39565948331](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39565948331):
  타입·단위·빌드는 통과했지만 기존 Vite의 audit high에서 중단했다. 브라우저 재현 증거가 아니다.
- 최소 수정판인 Vite 8.3.3을 정확히 고정했다.
  [공식 권고](https://github.com/advisories/GHSA-587h-7wmj-h5pm)는 Vite 8.3.0–8.3.2의 영향을 명시한다.
  [명령 인자 권고](https://github.com/advisories/GHSA-r825-w8mm-5pxw)와
  [Windows escaping 권고](https://github.com/advisories/GHSA-698v-4r3x-3vcv)도 같은 수정판을 명시한다.
  npm registry의 8.3.3 metadata와 실제 tarball SHA-512를 대사했고 기존 잠금의 전이 패키지 판본은 바꾸지 않았다.
  npm ci/audit는 후속 실제 CI에서 확인한다.
- 로컬 npm 준비는 보호5root와 합산 RSS 1GiB를 넘겨 1.951389411초에 중단했다.
  단일243,896,320/합1,118,867,456bytes, FD4→4, 원2148항목/기존 소스·자산/보호5root와 소유 정리0을 확인했다.
  같은 실행은 반복하지 않고 브라우저/빌드를 hosted runner에서 수행한다.
- [수정 전 CI39566408040](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39566408040):
  audit를 통과한 뒤 메뉴 복귀 시 서버 체크포인트 `8 / 16`이 없는 실패를 실제 Chromium에서 재현했다.
  앞19검사 통과/해당1실패/후속5미실행이다.
- [CI39566874547](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39566874547)의
  source `de4612e`는 단위1,886·전체 Chromium263·타입/build/audit를 통과했다.
  이 CI 전체는 기존 빌드의 검사 자료 누락으로 실패했다(기존 단위1,705통과/1실패).
  누락된 원 public 재생 fixture를 같은 base에서 함께 추출하도록 보완했다.
- 이후 두 실행 화면의 계정 변경 시 파일 input도 비우고 그 회귀 조건을 추가했다.
  [최종 CI39568367571](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39568367571), source `6bc68a5`는
  현재 단위1,886·집중 Chromium25와 기존 고정 빌드 단위1,706·Chromium8,
  양쪽 타입/build/audit(취약점0)를 모두 통과했다. 최종 source에서 전체263 브라우저를 다시 실행하지 않았다.
  이전 전체 검증 뒤 제품 source 차이는 계정 변경의 두 파일 input 초기화이며 집중 검증에 포함됐다.
- [최종 증거](artifacts/execution-navigation-retention-20261021.json)는 두 모델의 접수/메뉴 복귀,
  숨김 조회 중지·재접수0·늦은 접수 응답·계정 변경 시 작업/파일 제거와
  저장3D 해제/같은 원 결과·UTC 재개를 구분해 기록한다. 브라우저 응답 fixture를 사용한 UI 소프트웨어 검증이다.

## 기존 사용자 화면 적용 조건

현재 미리보기의 고정 web base는 `2aa45fa7bc219a02e6a322ca095b0e726fad82da`다.
해당 판본에 App의 메뉴 유지 한 줄과 계산 workspace/두 실행 화면, 보안 수정 잠금과 회귀 검사만 적용한다.
현재 개발 브랜치의 다른 UI 변경을 함께 배포하지 않는다. 기존 backend·DB·키·불변 입력과 모델/동결2173파일을 보존한다.
최종 산출물의 기존209파일/현재4source와 빌드183파일의 지문을 대사했다.
App은 기존 판본의 메뉴 유지 한 줄만 바꿨으며 다른 UI 변경은 가져오지 않았다.
5174의 기존 NGINX root를 검증된 별도 빌드로 교체하고 같은 pidfd/시작시각의 master에 reload했다.
원 frontend183파일과 열려 있던 탭의 구 JS/CSS40개를 보존했다. 새 HTML과 entry/실행 JS·CSS6개의 실제 HTTP/SHA를 확인했다.
backend/DB 재시작 없이5root/동결2173파일·불변 원2148항목을 보존했다.
기존 안내 작업의 실제 인증 GET도200/완료 결과 존재를 확인했다(관측14.007초, 새 접수0).
초기 진단의 불필요한 쿼리는422로 거절됐고5초 관측 timeout 뒤 SDK와 같은 닫힌 URL/30초 제한으로 확인했다.
배포 뒤 상태 JSON은 두 포트200/원문 일치/no-store이며5173의 원 HTML과5174의 새 수용 HTML을 확인했다.
원 read-only 상태 검증기는 보존하고 현재 빌드용 별도 판본을 private handoff에 기록했다.
WSL 실제 브라우저/새 수치 계산/전체 backend CI는 이번에 실행하지 않았다.
전체 goal·새 CO₂·현장/예측/추천 관문을 수용하지 않는다.

설계 판단은 현재 Codex CLI `gpt-6.1-sol`/`xhigh` 세션에서 수행했다.
실제 turn_context는 `2026-10-21T07:52:20.440Z`, SHA-256
`ed1bc79199998be5ec5548a2abb92e1f62c0b18b254886ab61f19d626bb5fea4`다. CLI를 재귀 실행하지 않았다.
원 관측·실패·소스 지문·검토 출력은 private `20261021-execution-navigation`에 보존한다.
