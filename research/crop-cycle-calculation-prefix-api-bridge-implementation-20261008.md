# prefix 증명의 공개 API·SDK·기록 3D 연결 수정

2026-10-08 KST. [수정 계약](../contracts/crop-cycle-calculation-prefix-api-bridge-v1.md)을
**고유928개·타입/빌드·실제 종료0·정리로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-prefix-api-bridge-reference-20261008.json)의 SHA는
`6ba3120a3f3a4616d361d9f9756f2bf2a162f14dedc121a2bf047706fffad0d5`다.
판단은 기존 native Codex CLI `gpt-6.1-sol / xhigh`에서 수행했고 재귀 CLI는0회다.

## 관측 결함과 수정

서버의 고정 dependency map에는 새 `prefix` 모듈이 있지만 공개 Pydantic 모델과
웹 SDK의 닫힌 key 목록에는 없었다. 실제 수치 artifact의 공개 투영은
1실패/62미선택·종료1, SDK의 새 필수 map 시험은1실패/178미선택·종료1로 재현했다.
앞선 내부 저장/조회 수용으로 공개 경로의 호환성을 추정하지 않았다.

API에 필수 `prefix: Digest`를 추가하고 실제 선언으로 OpenAPI를 재발행했다.
SDK는 정확한8개 필수 dependency key와 소문자64자리 SHA를 검사한다.
누락·변조·추가 key를 거부하며 일반 map 허용이나 provenance 삭제로 통과시키지 않는다.
backend 반례는 재해시한 payload도 거부하는지 확인한다.

생장 수식·입력·계산 문맥·artifact·prefix·서버 custody·저장 소스는 보존했다.
이전에 존재한 backend 제품 소스 중 변경한 파일은 공개 API 모듈 하나다.

## 새 실제 투영 기록과 원량 대사

현재 실제 수치 artifact/공개 투영으로6개 소유 합성 프로그램의34개 JSON을 새로 수집했다.
원 기록에 해시를 덧붙여 만든 fixture가 아니다. 새 수집 명령은114.149초·종료0이며
공개 투영 중 parser/context/QC/RHS 호출을 금지했고 수집 전체의 FD4→4·원 source/정리를 확인했다.

| 기록 | bytes | SHA256 |
| --- | ---: | --- |
| 보존한 기존 JSON | 640,855 | `a2d3e197b352bc51ab1dd66f520f38912032bb9a9e705733eb89919e47f4a80b` |
| [새 JSON](../web/e2e/calculation-cycle-crop-prefix-recorded-responses.json) | 643,439 | `6fb7f94c060b54b8dcc97e78d8eda3c543075f2670ab21447c7d7423cb46b006` |

새34개 응답의 prefix SHA는 현재 실제 모듈의
`34bec7b1745d47558e571bdea00183616eb4d92c737c80feae0656105850d059`다.
각 page의 전체 행·UTC·사건·hold와 요약 수량/기간은 기존과 같다.
현재 코드와 input evidence provenance의 해시는 새 투영 판본으로 구분한다.
긴 사례는 원25시간·11,400걸음·27시점/5사건을 유지했다.
짧은 정상, 과거 hold, 빈 hold, 소수 시각 hold, 출력0 사례도 대사했다.

## 실제 검증과 정리

| 순차 명령 범위 | 통과 | 실제 명령 wall | 종료 |
| --- | ---: | ---: | ---: |
| API 투영·route·OpenAPI | 193 | 191.993초 | 0 |
| 웹 전체 단위 시험 | 720 | 6.609초 | 0 |
| 타입 검사·Vite 빌드 | 해당 없음 | 2.048초 | 0 |
| 해당 Chromium 재생 | 15 | 51.174초 | 0 |

합계928개다. 먼저 실행한 최소 GREEN backend4개/SDK1개는 이 합계에 다시 더하지 않는다.
Chromium은 기록 JSON을 사용하는 실제 App·WebGL의 장면/표·이전·취소·보류를 검사했다.
application error0·동시 읽기 최대1을 확인했다. 소프트웨어 GPU 드라이버의 ReadPixels 경고2건은
실제 장비 성능이나 production 성능 수용을 뜻하지 않는다.

nice19·소유 무거운 작업 하나씩 실행했다. 별도 최종 감사에서270개 고정 source,
실제 로그/종료 기록, 원/새 fixture hash, 원 PID 시작 identity의 종료,
임시 tree·passfile·PG 잔재 없음과 브라우저 포트 종료를 대사했다.
이 감사 뒤 source freeze를 해제했다. 새 PG·컨테이너는 시작하지 않았다.

## 수용 경계와 후속

이번 증거는 **소유 합성 공개 투영 JSON·API·SDK·기록 응답 3D의 소프트웨어 연결**이다.
fixture의 농장/증명 metadata는 시험 scaffolding이며 실제 서명 발급·DB 게시·TLS wire가 아니다.
전체 Backend, 새 native PG/TLS/WebGL, 전체166일 등록 terminal/DB/API/같은 UTC3D는 실행하지 않았다.
최신 native의 원 명령 종료 기록 누락 hold도 유지하며 관측 만료 때문에 재시작하지 않았다.

다음은 출력/사건 각각128개와 기존 bytes 한도를 지키는 명시 판본의 계산 묶음 정책이다.
원8초 RK4/300초 출력, 현재 bytes/HMAC·권리/입력·HEAD 경계와 수치 hold를 보존한 뒤
실제 저장/재개 비용을 측정해 전체 작기 실행 예산을 정한다. 전체 작기 날짜를 외삽하지 않는다.

생과 수확·물/양분·구매 에너지·작물 결과와 Decimal 손익 연결은 남아 있다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run은0건이다.
실제 제품 CLI/독립 G1은 수용 전이며 G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
원격 최신 `2a3e615`는 다른4 workflow 성공·Backend 실패로 종료했다.
[엄격한 HBA 검사 조사](ci-host-scram-primary-evidence-20261008.md)는 실패 환경의 실제 HBA 행을
확보하지 못했으므로 원인을 확정하지 않았으며 현재 로컬 수정의 hosted 수용은 별도다.
