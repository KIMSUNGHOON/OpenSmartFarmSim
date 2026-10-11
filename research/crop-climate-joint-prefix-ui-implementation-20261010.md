# 계산 중 확정 부분 결과 화면 — P5 기능 로컬 수용

2026-10-10 KST. 화면 `36d9b80`, 브라우저 검사 `fa2e72b`를 수용했다.
[기계 증거](artifacts/crop-climate-joint-prefix-ui-reference-20261010.json)는401,250bytes,
SHA-256 `0edfcc31cdae283134b09783f54150c6246bbf0d1ec229cea0ed2b7475048873`다.
기존 소유 기록 응답을 사용한 실제 Chromium/WebGL의 **화면 기능** 범위다.
실제 running 백엔드와의 브라우저 연결·5174 활성화는 P6에 남아 있다.

## 변경과 화면

P5a는 새 부분 결과 component와 기존 Execution/CSS의3파일이다.
P5b는 새 브라우저 spec과 기존 E8의 prefix 미지원404 fixture,2파일이다.
한 조회 주기에서 진행→prefix summary→최근8사건→최근64시점을 순차 조회하고,
모든 필요한 페이지가 같은 selector 검사를 통과한 뒤 함께 교체한다.
확인 시각·판본 최초 수용·계산된 시각·마지막 저장 시각은 구분한다.

같은 원 UTC를 표·그래프·기존 수치3D에 전달한다. 새 저장 시점은 최신값을 선택하고,
저장 시점이 같으면 선택을 유지한다. sample이 없으면3D를 만들지 않는다.
일시503은 마지막 전체 snapshot임을 표시하고,409는 이전 snapshot을 지운 뒤 재조회한다.
권리·인증·응답 거부, 취소·숨김·농장/계정 변경은 원값과 장면을 지운다.
미지원404는 부분 결과만 비활성으로 두며 기존 진행 조회·취소를 유지한다.
완료/수치 보류 뒤에는 기존의 같은 저장 결과 화면으로 전환한다.

[데스크톱 캡처](artifacts/crop-climate-joint-prefix-ui-desktop-20261010.png)와
[모바일 캡처](artifacts/crop-climate-joint-prefix-ui-mobile-20261010.png)는 실제 시험 화면이다.
LAI·50과실 C/N·온도의 수치 모식도이며 실제 품종 외형이나 생산 예측은 아니다.
기존 조회 폼의 HTML pattern도 Chromium에서 유효하도록 `/`와 `-`를 이스케이프했다.
[HTML 표준의 pattern 규칙](https://html.spec.whatwg.org/multipage/input.html#attr-input-pattern)을 확인했고,
최초 브라우저의 Invalid regular expression 경고와 수정 후 검사를 기록했다.

## 통과한 검증

| 범위 | 수용 증거 |
| --- | --- |
| 새 Chromium20개 | 원 UTC·LAI·50개 C/N·WebGL draw·차트/표 시각, 순차 GET·판본 원자 교체·선택 유지, 빈/사건만 있는 결과, 거부/503/409·독립 취소·숨김/계정/늦은 응답·완료/hold·390px 키보드/넘침 |
| 기존 Chromium15개 | prefix 미지원 서버에서 기존 접수·진행/취소·재접속·완료/hold 저장3D 계약 |
| 웹303개 | 기존 terminal113/실행113·prefix77의 집중 회귀 |
| 타입·빌드 | 최종 TypeScript와 스레드/메모리를 제한한 비압축 Vite build |

고유338개·skip0이다. 전체 웹/backend suite와 remote CI는 실행하지 않았다.
새 브라우저 검사는 console/pageerror와 요청/응답을 기록한다.
캡처 때 발생한 정확한 WebGL ReadPixels 성능 경고와, 해당 시험이 의도한 상태/실제 prefix URL이
일치하는 HTTP 오류만 별도로 분류했다. 새20개의 나머지 오류/경고는0이다.
기존15개에 이 새 console 계측을 소급 적용했다고 주장하지 않는다.

표준 Playwright CLI의 부모/작업자 Node와 Chromium을 함께 띄우면 두 사용자 서버를 포함해1GiB를 넘었다.
원 시험 본문·hooks·실제 Playwright expect/page/Chromium을 단일 Node adapter에서 실행했다.
adapter·runner·bundle/자원 제어 source와 해시를 기계 증거에 담았다.
**표준 CLI runner 통과로 세지 않았다.** 영구 spec은 기존 `@playwright/test`를 사용한다.

39개 최종 guard는 동일한 제품3파일 SHA를 확인했다.
시험의 시계·카운터·hold 농장/lookup·캡처 위치 수정은 별도 판본/diff로 기록하고 영향받은 경로를 재검증했다.
변하지 않은 시험 본문을 파일 SHA 정리를 위해 모두 반복하지 않았다.
처음의 fixture 페이지 수 초과, 시계의 실제 시간 진행, 요청 카운터,
completed/hold 농장 해시 혼용·잘못된 lookup, 최종 타입의 시험 식별자 오류도 원 실패로 보존했다.
거부된 fixture를 제품 검사 완화로 통과시키지 않았다.

## WSL과 디자인 대조

최종 guard의 단일/두 사용자 서버 포함 합산 RSS 최대는427,528,192 /951,529,472bytes다.
512MiB/1GiB·0.25초 감시, 원본2,148항목·두 frozen source/assets·FD4→4·소유 프로세스/PG/passfile 정리를 확인했다.
초기 RSS 초과·Node heap OOM·SSR 외부 모듈/브라우저 경로 실패와 PID 진단기 오류의 복구를 별도 보존했다.
기계 기록의 실패 종료21개와 진단기 오류 복구는 수용 검사 수에 포함하지 않았다.
설치된 고정 Playwright1.63.0에 맞는 headless Chromium만 사용자 cache에 받았으며 OS/제품 의존성은 변경하지 않았다.

`12ui-design`과 실제 브라우저 검증 스킬을 적용했다. DevTools MCP가 없어 기존 Playwright/Chromium을 사용했다.
12ui는 변경하지 않은 기존 승인 LayerDoc으로 active/empty/blocked3상태를 대조했고 모두 실제 종료0·구매0이다.
기본 다중 프로세스의 RSS 초과 뒤, 설치된 도구를 수정하지 않고 소유 실행의 launch 옵션/Node 메모리를 제한했다.
원 tool과 이 제한 wrapper도 기록했다. 수치3D는 실제 제품 브라우저에서 별도로 확인했다.

대조 kit의 DOM coverage는25.0%/23.1%/23.1%로60% 기준보다 낮고 원 raster 자산도 kit에 없다.
`12ui-design`의 안전한 selector 대응·원 자산 사용 지침 때문에 해당 추가/삭제·raster 배치는 적용하지 않았다.
기존 실제 그래프/3D와 데이터·조작을 유지했으며 **최종 디자인 일치/U5는 보류**다.
기존 글꼴·반응형 수치 화면을 재사용한 이번 기능 수용과 최종 제품 UI 수용을 구분한다.

## 현재 사용자 화면·다음 단계

이번 변경은 두 사용자 서버에 배포하지 않았다.
5173은 완료166일 저장 재생,5174는 상태/checkpoint 자동 조회와 종료 후 저장3D다.
다른 개발/시험 DB의 계산이 사용자 UI에 자동 노출되지는 않는다.

다음은 P6a: 실제 SCRAM/HTTPS·별도 자동 worker의 running 중 원값/UTC/온도/WebGL·원 사건을 확인한다.
특히 P4에서 관측하지 못한 실제 SDK event-prefix200을 확인하고 완료/hold·취소·재접속과 원 결과를 대사한다.
관측을 만들기 위해 사용자 계산을 pause하거나 늦추지 않는다.
P6b는 그 frozen 후보를5174에 연결하고 현재 키·기존 결과·5173을 보존한다.

native `gpt-6.1-sol`/`xhigh` context12:13:42.345Z부터 이 수용 증거까지3,285.142초(약55분)이며 문서/commit은 별도다.
재귀 CLI는0이다. 남은 P6a–P6b는1.5–3집중시간 잠정, 연속 작업 시2026-10-11 KST의 작은 합성 화면을 조건부 범위로 둔다.
실제 event 전달·writer 동시성·WSL/서비스 수명 관측에 따라 갱신한다.
실제 작물 Run0·독립 국내 농장 자료0·G0–G4 미평가, 생산량/자원 구매·미래 마진·추천은 보류다.
