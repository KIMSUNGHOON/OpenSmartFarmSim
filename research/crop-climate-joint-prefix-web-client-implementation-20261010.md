# 계산 중 확정 결과의 웹 reader — P4 로컬 수용

2026-10-10 KST. 공용 검사 `c750007`, 새 SDK `f40a8ff`, 시험 경로 정리 `0a28e6b`를 로컬 수용했다.
[현재 증거 v2](artifacts/crop-climate-joint-prefix-web-client-reference-v2-20261010.json)는3,441bytes,
SHA-256 `1cdc86842faed375e12bfc6d9e85306a54b1b7d54a53e359244bdb7c9b372f2e`다.
v2가 참조하는 [원 실행 증거](artifacts/crop-climate-joint-prefix-web-client-reference-20261010.json)는302,832bytes,
SHA-256 `b0ab5fe3301fc665da5e1663c35c3b8c8d1855ea68bb67911e09a03103e0feb3`다.
계산 중인 소유 합성 자료를 실제 HTTPS로 읽는 웹 전달 범위다. 사용자 화면 배포는 후속이다.

## 변경

P4a는 기존 terminal reader의 격자·manifest·sample/event 검사와 실행 checkpoint/lookup 검사를
두 파일에서 공용 함수로 추출했다. 기존 응답 계약과 수치 코드는 유지했다.
P4b는 새 prefix reader, 기존 API 연결, unit, 실제 SDK 시험의4파일이다.
새 reader는 none/accepted/closed와 원 selector/checkpoint를 구분하며 완료 결과 ID나 root를 만들지 않는다.
페이지의 `start`·64/8행·2MiB·30초, 원 수치/UTC·단위/격자·현재 작업/농장·같은 reference를 검사한다.
늦은 입력 변경/Abort와 기존 HTTP 오류를 처리하고 기존 sample/event 검사를 재사용한다.
서명·현재 권리·관문 승인은 서버가 담당한다.

실제 SDK 시험의 TypeScript entry는 저장소 test의 literal에서 추출해 설치된 Vite로 별도 SSR bundle을 만든다.
Node는 제품 `createApi`를 사용하고 시험용 사설 CA를 명시적으로 신뢰한다. 신뢰하지 않는 CA는 거부된다.
입력 토큰·원 wire·개인별 시험 출력은 저장소 밖 보호 디렉터리에만 둔다.
브라우저 동작을 이 Node 시험으로 수용하지 않았다.

최종 검토에서 Node bundle을 요구하는 시험이 기본 backend CI의 `test_*.py` 발견에 들어가는 것을 확인했다.
기존 명시 smoke 관례에 맞춰 [시험 파일](../backend/tests/crop_climate_joint_prefix_sdk_smoke.py) 이름만 변경했다.
내용 SHA는 원 실행과 동일하고 변경 후 명시 collection3개를 확인했다. 계산 시험3개는 경로 변경 뒤 반복하지 않았다.
워크플로/의존성을 변경하지 않았으며 v2는 이 경로 변경과 원 증거의 해시를 연결한다.

## 통과한 검증

최종 같은6파일 SHA에서 **고유306개, skipped0**와 타입/제한된 비압축 빌드를 확인했다.

| 범위 | 확인 |
| --- | --- |
| 기존 terminal/실행226개 | 공용 검사 추출 뒤 기존 결과·진행·취소 계약 |
| 새 prefix77개 | 원 sample/event·UTC/격자/단위·폐쇄 DTO·빈 결과·범위/페이지·오류·같은 판본·늦은 변경·Abort/timeout/UTF8 제한 |
| 실제 SDK3개 | 실제 SCRAM/검증 HTTPS·별도 자동 작업자·정상/hold·권리 철회 후 소유자 취소·원 저장 결과 |

정상/hold 각각 pause 없는 chunk8 작업자는 첫 시도에서 종료했다.
각 running accepted summary2회와 원 sample1행/2행을 읽고 종료 후 원 저장 summary bytes로 전환했다.
원 wire와 SDK 결과의 모든 값/UTC 문자열을 대사하고 총1,514개 수치의 IEEE754 binary64 bit를 대사했다.
이 검사는 음의0도 구분하며 SDK에서 다시 계산한 작물 값은 없다.
권리 철회422 뒤 실제 작업자가 취소를 확인했고 결과/게시가 없다. 조회21종 계산/쓰기 계수는0이다.
실제 HTTP43응답의 최대는9.563초다. 정상/hold 각각503 여섯 번을 재조회했다.

실제 unpaused events 요청은503이어서 **성공한 event-prefix HTTPS 페이지는 관측하지 않았다**.
원 event 수치의 새 envelope 검사는 unit으로 통과했다. 해당 실제 UI/사건 경로는 P5/P6에서 확인한다.
이 제한을 원 event의 실제 전달 성공으로 세지 않았다.

최초 unit fixture에 application/json 헤더가 없어7개가 실패하고 일부 거부 검사가 본문을 검사하지 않았다.
헤더 수정 뒤에는 lowercase authorization assertion 한 개가 실패했다.
두 원 로그/source pin/종료 증거를 보존하고 fixture/assertion을 수정했다. 수용 수는 최종303+3만 센다.

다섯 최종 실행 guard와 별도 경로 collection guard에서 원본2,148항목·두 frozen 사용자 서버/source/assets·FD4→4·소유 프로세스/PG/passfile 정리를 확인했다.
WSL 단일/보호 사용자 서버 포함 합산 RSS 최대423,849,984 /967,147,520bytes로512MiB/1GiB 안이다.
전체 웹/backend/remote CI와 P5 화면/e2e·P6 실제 브라우저/사용자 기동은 실행하지 않았다.

## 현재 사용자 화면과 다음 단계

5173은 완료166일 저장 생장/수확 재생이다.5174는 접수한 작업의 상태/checkpoint 자동 조회와 종료 후 저장3D다.
정상 응답 후10초를 기다리는 polling이며 계산 중 확정 숫자의 성장3D는 아직 연결되지 않았다.
별도 개발/시험 DB의 계산은 사용자 화면에 자동으로 나타나지 않는다. 이번 변경도 두 서버에 배포하지 않았다.

다음은 [P5 부분 결과 화면](../tasks/plan.md#joint-prefix-view-20261010)이다.
진행→summary→같은 selector의 필요한 page를 순차로 읽고 같은 UTC의 표/그래프/3D를 함께 교체한다.
빈 출력·현재 권리/취소·숨김/계정/늦은 응답·terminal 전환과 실제 기록 응답 Chromium을 확인한다.
P6 실제 브라우저 뒤 frozen 후보를5174에 기동한다.
남은 P5–P6는3–6집중시간 잠정이며2026-10-11 KST의 작은 합성 사용자 화면은 조건부다.
누적 조회 비용/503·실제 브라우저·서비스 수명 관측 뒤 다시 산정한다. 전체 제품 완료일은 아니다.

native CLI는 실제 `gpt-6.1-sol`/`xhigh`, turn context `2026-10-10T11:37:56.681Z`,
LF 포함 SHA `3cb5491a2456c77a91d4e1d4f007d59e82e7010cc36e063bf0b14330d229869d`다.
재귀 CLI0·runtime CLI0·native→마지막 시험1,576.244초(약26분), 문서/commit 별도다.
실제 crop Run/독립 국내 농장 자료0건·G0–G4 미평가·생산/미래 마진/추천 hold와 기반/push 고정을 유지한다.
