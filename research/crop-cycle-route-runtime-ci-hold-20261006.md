# Route/runtime 판본의 종료된 CI

상태: **`d61bcb3` hosted 미수용, 두 로컬 수정 검증·수정 판본 CI는 별도**, 2026-10-06 KST.
이 판본은 인증 route/runtime·원천 읽기 연결까지이며 후속 client/범위/3D와 두 수정은 포함하지 않는다.
종료 상태·job/step·로그 hash는 [불변 receipt](artifacts/crop-cycle-route-runtime-ci-hold-20261006.json)에 있다.

| 경로 | 종료 결과 | 수용 범위 |
| --- | --- | --- |
| Backend | 실패 | 분할0/1/3/4/5 성공, 분할2 실패. 최종 집계는 모든 분할 성공 조건에서 거부 |
| Web | 실패 | 타입·단위·빌드 성공, 높은 등급 audit 실패. Chromium 설치/브라우저는 건너뜀 |
| C0 Compose | 성공 | 해당 SHA의 기존 조립 검사 |
| Application images | 성공 | 해당 SHA의 기존 이미지 검사 |
| Authored path | 성공 | 해당 SHA의 첫 시도7job |

[Backend run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37405273500)의
마지막 분할4는 **503 passed/3692.23초**, 최종 집계는 04:37:03 UTC에 종료됐다.
다운로드한 결합 로그에는 분할3/4/5와 집계만 포함돼 전체 backend 통과 수로 합산하지 않는다.
분할2의 실제 실패·703통과/1실패/1137.44초와 재현은
[권한 기대값 수정](market-candidate-read-authority-assertion-20261006.md)에 보존했다.
`f9c4bc9`는 제품의 정확한 `MarketCandidateDenied`와 메시지를 검사하도록 시험만 수정했다.
실제 PostgreSQL5개/정리 통과는 로컬 증거다.

[Web run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37405273365)의
`source-map-js1.2.1` 감사 실패는 [단일 잠금 수정](source-map-js-audit-fix-20261006.md)으로
재현·수정했다. `e9c2431`의1.2.2 잠금과 웹503개·타입/빌드·audit0은 로컬 증거다.
기존 CI를 취소하거나 timeout/분할 정책을 바꾸지 않았다.

운영 기반은 `d19f7c0`으로 고정한다. 새 실제 PG/TLS/WebGL 재검증과 수정 판본 hosted CI는
각각 종료·원값/자원 정리 증거 뒤 수용한다. 실제166일·생과/자원/경제·품종/국내 독립 자료와
G0–G4는 별도이며 실제 작물 Run/국내 독립 자료는0건이다.
