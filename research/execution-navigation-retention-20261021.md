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
- 수정 후 전체 웹 회귀, 두 모델의 접수/메뉴 복귀·숨김 조회 중지·늦은 접수 응답·계정 변경,
  저장3D 해제/같은 원 결과 재개와 배포용 기존 빌드의 검증은 진행 중이다. 완료 전 수용하지 않는다.

## 기존 사용자 화면 적용 조건

현재 미리보기의 고정 web base는 `2aa45fa7bc219a02e6a322ca095b0e726fad82da`다.
해당 판본에 App의 메뉴 유지 한 줄과 계산 workspace/두 실행 화면, 보안 수정 잠금과 회귀 검사만 적용한다.
현재 개발 브랜치의 다른 UI 변경을 함께 배포하지 않는다. 기존 backend·DB·키·불변 입력과 모델/동결2173파일을 보존한다.
검증된 별도 frontend 빌드와 provenance를 확보한 뒤5174의 기존 NGINX root만 교체해 적용한다.
기존 빌드는 보존하고 동일 소유 master에 reload한다. 전체 goal·새 CO₂·현장/예측/추천 관문을 수용하지 않는다.

설계 판단은 현재 Codex CLI `gpt-6.1-sol`/`xhigh` 세션에서 수행했다.
실제 turn_context는 `2026-10-21T07:52:20.440Z`, SHA-256
`ed1bc79199998be5ec5548a2abb92e1f62c0b18b254886ab61f19d626bb5fea4`다. CLI를 재귀 실행하지 않았다.
원 관측·실패·소스 지문·검토 출력은 private `20261021-execution-navigation`에 보존한다.
