# 검증 계산 결과의 같은 UTC 화면 — 로컬 수용

2026-10-08 KST. [3 core파일 계약](../contracts/web-crop-cycle-calculation-view-v1.md)의
`crop-cycle-calculation-view`와 선행 helper를 합한 `crop-cycle-calculation-window-view`까지 수용했다.
전체 웹 부모와 새 실제 PG/TLS/WebGL 자식은 미수용이다.
[고정 영수증](artifacts/web-crop-cycle-calculation-view-reference-20261008.json)에 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·실제 명령/종료/source/로그 SHA를 둔다.
화면 core커밋은 `d94f5dc`이며 원 SDK/window/장면·그래프/CSS/backend/잠금 **113 source**를 보존했다.

## 사용자에게 보이는 변경

기존 네 판본 옆에 입력 검사를 연결한 긴 계산 판본을 명시적으로 선택한다.
94자 결과 ID와 전체 농장/검증 참조·manifest를 유지한다. 새 ID로 초기 선택하면 해당 판본을 자동 선택한다.
기존 화면·장면·그래프를 그대로 사용하고 원/새 조회를 명시 source로 구분한다.
판본·계정 변경의 첫 render부터 이전 수치를 숨기고 기존 요청·재생 timer를 정리한다.

소유 합성 공개 fixture의 **원27시점/5관리 사건**을 실제 Chromium에서 대사했다.
같은 원 ID/전역 index/UTC·LAI·기관량·50구획 C/N·16누적/4진단/4수지 값이 표·그래프·3D에 대응한다.
현재7시점/2사건만 보존하며 시점은7/7/7/6, 사건은2/2/1로 탐색한다.
자동 재생은 현재 범위의 저장 시점만 선택한다. 과거/빈/소수 초 hold와 출력0 완료는 새로운 frame을 만들지 않는다.
HTTP403/422/503·검증 거부·늦은 응답/취소·ID/판본/계정 변경 때 이전 장면과 수치를 제거한다.

[데스크톱](artifacts/calculation-cycle-desktop.png), [모바일](artifacts/calculation-cycle-mobile.png),
[빈 보류](artifacts/calculation-cycle-empty-hold.png), [확인 과거 보류](artifacts/calculation-cycle-past-hold.png)는
실제 App의 **시험용 HTTP 응답**을 재생한 캡처다. 새 실제 농장 DB/TLS 경로의 캡처가 아니다.
최종 시험의 PNG는 직접 시각 검토한 선행 캡처와 byte 단위로 같다.

## 검증과 실패 보존

| 실행 | 결과 |
| --- | --- |
| 올바른 구현 전 RED | 새 판본 option 부재·1실패·종료1 |
| 최종 새 Chromium 집중 | **15통과 / 49.5초** |
| 기존 네 판본 Chromium 회귀 | **47통과 / 3.1분** |
| 웹 전체 단위 | **719통과 / 21파일 / 13.86초** |
| 최종 typecheck / build | 종료0 / 종료0 |

고유 브라우저 시험은62개다. 반복 실행을 더하지 않으며719개에는 선행 SDK/helper 시험이 포함된다.
원 회귀47개의 두 제품 파일 SHA는 최종과 같다. 그 뒤 새 시험의 사용하지 않는 타입/Window 선언만 수정했고,
최종 새15개·타입·단위·빌드의3 core SHA가 모두 같다. 제품 파일은 이 수정으로 바뀌지 않았다.
최초 잘못된 RED locator, lazy lookup helper의 열기/닫기 경합, 누적 객체 key 순서 비교,
JSON의0/JS의-0 척도 비교, 타입 검사 실패와 수정 전 로그도 영수증에 보존했다. 시간 제한은 늘리지 않았다.

실제 fetch/response reader의 완료·취소·오류 정산을 계측해 최대1개/종료0개를 확인했다.
이전 Playwright request 이벤트 계측은 취소에서 최대2개를 관측했다. 이 원 관측을 남기며,
새 reader 계측을 독립적인 실제 HTTP 서버 동시성 증거로 바꾸지 않는다. 다음 native 단계에서 확인한다.
애플리케이션 오류는0개이며 SwiftShader의 `ReadPixels` 성능 경고는 실제 기록 그대로 남겼다.
기능 시험에서는 정확한 드라이버 경고만 허용한다. 실기기/production 성능 수용은 보류다.

nice19·한 browser worker와 순차 Vitest를 유지했다. 소유 임시 tree·preview2경로를 제거하고
Vite5189/5190 종료와 실행 handle 소비를 확인했다. 기존 회귀가 덮어쓴 과거 PNG3개는
새 관측을 사설 보존한 뒤 원 HEAD/hash로 복원했다. 과거 수용 이미지를 새 증거로 교체하지 않았다.
표본 주 프로세스 RSS는 로그에만 기록하며 WSL 전체/renderer 합산 peak로 표시하지 않는다.
빌드의 기존500kB 초과 chunk 경고도 보존했다. 이번 새 PG/TLS/RHS 실행은0회다.

## 디자인 검토

`12ui-design`의 기존 승인 LayerDoc3개를 원 settled conversion에서 무료로 복원했고 원 SHA가 같다.
현재 URL/실제 컴포넌트를 같은 target으로 close했다. 세 kit는 종료0·plan settled이며 새 구매는0건이다.
DOM 대응은 정상28.8%/빈14.9%/과거19.7%로 낮다. 실제 입력/단위를 그래프나 가짜38% 진행률,
다른 작물·관측치로 치환하는 제안은 채택하지 않았다. 기존 네 cutout·font/CSS를 유지했다.
첫 close의 monorepo `--repo` 경로 오류도 남겼고 소유 `web/` 경로로 수정했다.
모바일390·키보드·동작 줄이기·200% **글자 확대**를 검사했다. 브라우저 zoom/실기기 시험으로 세지 않는다.
Chrome DevTools MCP는 없어 기존 격리 Playwright/Chromium을 사용했다. Pixel fidelity는 미수용이다.

## CI와 다음 단계

[종료 CI 기록](artifacts/crop-cycle-calculation-view-ci-terminal-20261008.json)의 구형 `353bffb`는
C0/웹/작성 PG 성공·앱/Backend 실패다. Backend는5분할 성공·분할5의21실패/724통과·집계 실패다.
실패는 구형 loader에 새 기본 false policy 필드를 넘긴 설정 fixture에서 발생했다.
관련 생성기/fixture는 이미 `a7bd5b6`에서 [고유125개 분할·실제 SCRAM/TLS](application-operator-policy-compatibility-20261007.md)로
로컬 검증했다. 현재 세 source SHA도 그 수용 영수증과 같아 추가 변경/반복 시험은 하지 않았다.
수정 판본의 hosted 수용은 별도이며 원 CI 취소/rerun·한도/설정 변경은0회다.

다음은 새 경로의 실제 등록 계산→보호 loader/TLS→같은 UTC WebGL·권리/복구/정리 검증이다.
화면1–2집중시간 추정은 위 실적으로 대체한다. **남은 작은 native 연결3–5집중시간 잠정**이며
CI·전체166일 등록 누적 비용/저장·복원·생과/물/양분/구매 에너지·Decimal 경제·외부 자료는 제외한다.
전체166일 RHS 완료를 전체 등록/API/3D 수용으로 바꾸지 않는다.
실제 품종 입력·국내 독립 검증 자료·측정 농장 작물 Run은0건이며 G0–G4는 `not_assessed`다.
생산 예측·미래 마진·작물 추천·공개 운영과 최종 완료일은 필요한 외부 증거 확보 전 보류한다.
