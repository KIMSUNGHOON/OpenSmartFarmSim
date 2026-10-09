# 검증 계산 결과의 같은 UTC 화면 — v1 개발 계약

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행은 [새 SDK](../research/web-crop-cycle-calculation-client-20261007.md)와
[현재 범위 선택](../research/web-crop-cycle-calculation-window-20261008.md)의 실제 로컬 수용이다.
`crop-cycle-calculation-view`의 core파일은 기존 `web/src/CycleCropReplay.tsx`,
`web/src/CropReplay.tsx`, 새 `web/e2e/calculation-cycle-crop-replay.spec.ts` **3개**다.
기존 SDK/window·fixture·장면/geometry·그래프·CSS·backend·잠금·CI는 보존한다.

## 화면의 변경 경계

기존 네 판본을 유지하고 검증 입력이 연결된 긴 계산 판본을 명시적으로 선택한다.
호스트는 새 ID prefix의 초기 선택을 올바른 판본으로 연결하고, 판본 전환 시 이전 화면을 해제한다.
범위 화면은 명시 source 종류에 해당하는 validator와 `open`/`openCalculation`을 사용한다.
94자 새 결과 ID를 잘라내지 않는다. 새 참조·두 input_validation과 manifest를 그대로 표시한다.
source 종류·계정·입력이 바뀌는 첫 render부터 이전 수치/장면을 숨기고 요청·재생 timer를 정리한다.
sample·C/N·LAI·관리 사건의 단위와 원량은 기존 장면/그래프/표에 그대로 전달한다.
현재7시점/2사건·원 UTC 선택·범위 끝 정지와 원 계정 재조회 흐름을 재사용한다.

## 수용 기준

1. 실제 소유 공개 fixture로 정상/25시간·확인 과거/빈/소수 초 hold·출력0 완료를 조회한다.
   원 result ID/reference/전체 validation·현재 offset/global index/UTC·sample/사건을 대사한다.
2. 같은 원 sample이 표·그래프·3D에 반영되고 원 50구획의 C/N·LAI 수치가 보존된다.
   다음/이전 범위·관리 사건·끝·자동 재생은 저장 시점만 선택한다. 진단/실패/중간 frame을 만들지 않는다.
3. 계정·판본·ID 변경, 취소, 권리/검증 거부·늦은 응답 때 이전 수치·장면을 비운다.
   단일 실제 요청/settlement와 renderer·차트·timer 정리를 확인한다.
4. 신규 Chromium 집중 시험과 기존 cycle/관련 판본 회귀, 웹 unit/typecheck/build를 확인한다.
   데스크톱·모바일·키보드·동작 줄이기·200% 글자·console/network를 실제 브라우저로 검사한다.
   현재 범위 배열 수와 실제 캡처·원량 대사 근거를 남긴다. 시험용 HTTP 응답과 실제 PG/TLS를 구분한다.
5. `12ui-design`의 기존 승인 이미지/LayerDoc·자산을 재사용하고 완료 후 해당 target으로 close한다.
   가짜 농업 수치/진행률을 요구하는 제안은 적용하지 않으며 낮은 일치율은 그대로 기록한다.
   실제 UI 관측은 격리된 기존 Playwright/Chromium을 사용한다. 현재 Chrome DevTools MCP는 없다.
6. 같은 최종 source의 명령/종료/hash·소유 서버/브라우저/임시 자원 정리 뒤 화면 자식을 체크한다.
   window/view 부모는 두 자식의 증거를 대사한 뒤에만 체크하며 native/browser 부모는 남겨둔다.

이 단계는 합성 공개 응답의 화면 연결이다. 다음 실제 등록 계산→보호 TLS→WebGL 자식이
동일한 원량/UTC·현재 권리·조회 RHS0와 정리를 검증한 뒤 웹 부모를 수용한다.
남은 화면/집중 브라우저1–2 + native3–5 = **4–7집중시간 잠정**이며 실제 실행 결과로 갱신한다.
CI·전체166일 등록 부하/복원·생과/자원/경제와 실제 자료 확보·최종 제품 날짜는 포함하지 않는다.

## 로컬 수용 — 2026-10-08

[수용 기록](../research/web-crop-cycle-calculation-view-20261008.md)의 새 Chromium15개/기존47개·
웹719개·타입/빌드, 원27시점/5사건·전체 참조/validation·같은 UTC 원량·113 source/정리로 화면 자식을 수용했다.
선행 helper와 합한 window/view 부모도 완료하며 native/browser·전체 웹 부모는 미수용이다.
정상/빈/과거의 원 승인 LayerDoc close는 종료0·새 구매0이다. 낮은 대응과 드라이버 경고를 보존했다.
단일 fetch/reader 정산 계측은 독립적인 실제 HTTP 서버 동시성 수용이 아니며 다음 native에서 확인한다.
남은 작은 native 연결은3–5집중시간 잠정이다. 전체166일/자료·경제·관문/최종 날짜는 포함하지 않는다.
