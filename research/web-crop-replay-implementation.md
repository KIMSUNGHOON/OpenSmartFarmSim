# 저장 계산 기반 성장 3D — 구현·수용 기록

상태: **로컬 합성 연구 재생 소프트웨어 수용**, 2026-10-04.
[계약](../contracts/web-crop-replay-v1.md)과
[실행·응답·도형·코드 해시 증거](artifacts/web-crop-replay-reference-20261004.json)를 함께 읽는다.
6개 저장 시점·5분의 수식 시험이다. Axiany 한 작기의 재현이나 생과 생산량,
국내 예측·추천·공개 production 또는 G0–G4 수용으로 확대하지 않는다.

## 실제 개발 판단과 구현

기존 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의
`2026-10-04T13:25:16.916Z` turn context에서 `gpt-6.1-sol` / `xhigh`와
현재 workspace를 확인했다. 이 동일 세션에서 설계·검토·수정했다. 재귀 CLI는
실행하지 않았다. 개발 기록이며 독립 제품 runtime CLI 증거는 아니다.

| 경계 | 구현과 확인 |
| --- | --- |
| 조회 | 기존 인증 클라이언트의 GET 한 번, 정확한 결과 ID/농장 판본/등록 hash/작물 대사, 닫힌 단위·UTC·버전·완료/hold decoder. 현재 연결/입력 변경과 늦은 응답에서 이전 값 제거 |
| 수치·시간 | 하나의 저장 sample 인덱스로 기관량·LAI·누적 유량/수지·표·그래프·장면 연결. 자동 재생은 저장 시점 이동. 중간 생장 계산 없음 |
| 도형 | Three.js의 논리적 바닥 1m²와 고정 모식 잎 8패치. 실제 변환된 한 면 삼각형 면적 합계를 저장 LAI와 대사. 양면 렌더링 중복 없음 |
| 기관 비교 | 잎·줄기/뿌리·과실·버퍼의 `mg_CH2O/m2_floor`를 공통 최대 척도의 네 막대로 표현. 식물 키·잎수·착과수·숙기·생과 kg로 해석하지 않음 |
| 보류·장치 | 실패 진단의 음수/null과 마지막 확인 sample을 별도 표시. 정상 장면/그래프/표 없음. WebGL2 불가·실제 context loss/restoration 때 HTML 값 유지 |
| 자원·접근성 | 값/카메라/크기 변경 때만 렌더, pixel ratio ≤1.5, 자원/observer/이벤트 해제. 50행/사건 페이지, 키보드/range, 동작 줄이기·숨김 시 자동 재생 중지, 320px/200% 글자 확대 |

decoder, 도형과 React 화면/장면/그래프를 별도 모듈로 두고 기존 API/App과
개발 데모 진입점에 연결했다. 계획의 4개 핵심 파일보다 실제 파일이 늘어난 이유는
3D 자원 생명주기·그래프·조회와 실제 서버 브라우저 시험을 분리하기 위해서다.
프레임워크·lock·서비스·Compose·작업자는 추가하지 않았다.

기반 변경은 기존 작성 API CI의 browser 묶음에 `web_crop_replay_smoke.py`를
추가한 한 줄이다. 필요한 기능은 `web-crop-replay`의 실제 저장→HTTPS→장면 대사이며,
기존 묶음에는 작물 장면을 검사하는 시험이 없었다. 새 파이프라인/서비스는 없다.

## 통과한 검증과 실패 기록

모듈 부재의 RED를 확인한 뒤 decoder 36개·도형 13개를 통과했다. 도형 시험은
제품의 면적 함수와 별도로 좌표의 외적으로 면적을 계산하며 LAI 0/미소 값/큰 값,
실제 저장 6시점의 적엽 이후 감소와 영 기관량을 확인한다.

| 최종 검사 | 결과 |
| --- | --- |
| TypeScript | 통과, 0.49초 |
| 웹 단위 전체 | **209 passed / 13 files**, runner 2.77초; 작물 집중 49개 포함 |
| production build | 통과, runner 1.26초; 고정 데모 결과 ID/토큰이 JS 산출물에 없음 |
| 성장 Chromium 집중 | **10 passed**, runner 25.86초; 시점/단위·계정/늦은 응답·권리 거부·hold·실제 WebGL loss/restore·확대/대체·101시점 페이지 |
| 실제 SCRAM→표준 HTTPS→Chromium | **1 passed / 80.87초**, 임시 DB 준비/정리 포함 runner 82.46초 |
| 최종 화면 확인 | 1536×1024·390×844·hold: page error 0, 본문 가로 넘침 0, hold 장면/그래프 0 |

최종 웹 검사 구간은 `2026-10-04T14:16:19.949750Z~14:16:50.330564Z`다.
명령·로그 hash는 JSON 증거에 있다. 전체 Chromium suite는 이 로컬 실행에서
다시 돌리지 않았다. 변경한 성장 경로와 전체 웹 단위 검사를 실행했으며
전체 브라우저/백엔드 hosted 회귀는 별도 CI 결과를 확인한다.

실제 저장 시험은 `13:55:09.547587Z~13:56:32.008227Z`에 수행했다.
시험 결과 ID는 `crop-result-v1:9b2b6f9e0746b2fc86548fdada7be2eab4be0e05b796d1e5b591daf8f31367a1`이다.
6시점 모두 표·그래프·실제 렌더 도형의 같은 값/UTC를 확인했고, 최대 면적 오차는
**4.163336342344337e-17 m²**로 계약의 `max(1e-8, LAI × 1e-6)` 이내였다.
GET 중 적분을 금지해 재계산 없음과 저장 행 2개 불변을 확인했다.
정상/수치 hold/현재 권리 철회/계정 변경/재연결의 HTTP 상태는
`200,200,200,422,403,200`이며 모든 응답은 no-store다.
전체 본문을 읽은 정상 200 응답 4개의 최대는 **5.9015초**, 기존 제한은 30초다.
큰 작기/동시 사용자 처리량이나 실기기 GPU 성능을 확인한 것은 아니다.

첫 실제 서버 시험은 **1 failed / 80.68초**였다. React lazy 화면이 올라오기 전에
조회 details를 클릭하는 시험 동기화 오류를 확인했고, 화면 준비 대기를 추가했다.
첫 실패 로그와 수정 후 로그의 hash를 모두 보존했다. 합격 조건·서버 제한이나
계산 결과를 바꿔 통과시키지 않았다. 이후의 변경은 화면 자산·모바일 간격·hold
헤더이며 최종 빌드/단위/집중 브라우저와 시각 확인을 다시 통과했다.

WSL2에서는 nice 10·브라우저 한 worker와 PostgreSQL 16.15 임시 한 cluster
(shared_buffers 32MB, max_connections 24, parallel workers 0)를 사용했다.
실제 TLS 서버 join·브라우저 종료·frontend 종료·DB/비밀번호 파일 제거를 확인했다.
시험 ID의 DB는 정리되어 현재 사용자의 저장 내역으로 제공하지 않는다.
DevTools MCP가 제공되지 않아 격리된 Playwright Chromium을 사용했다.
기존 ECharts SVG bundle의 500kB 경고는 남아 있으며 이번 작업에서 lock을 변경하지 않았다.

## 디자인과 실제 화면 비교

12ui draft 4개를 실제로 확인하고 B를 선택했다. 같은 원 디자인에서 desktop,
mobile, hold를 branch하여 4 HTML 상태와 클릭 가능한 prototype의 완료를 확인했다.
branch run은 `crt-11dff27ce77b3b3b9bea91ed937b610147996811`이다.
이미 완료된 변환에서 변경하지 않은 LayerDoc를 무료로 파생하여 desktop/mobile/hold
모두 target 기반 improve를 끝냈다. 종료 kit에서 추가 구매는 0이다.

처음 improve는 repository root의 `src` 부재로 실패했다. durable 기록을 수정하지
않고 실제 frontend root에서 같은 원 target으로 다시 실행했다.
최종 DOM 대응률은 desktop **30.43%**, mobile **33.33%**, hold **34.78%**로 모두
낮았다. 자동 selector/content 치환을 적용하지 않고 계획을 검토했다.
따라서 원 디자인과의 픽셀 일치를 수용했다고 보고하지 않는다.

숲색/아이보리·3열 구조·토큰/아이콘·모바일 쌓기, 추출된 잎 배지와 보류 문서/정지
이미지를 적용했다. 실제 clean plate는 포맷만 WebP로 변환해 용량을 줄였다.
고밀도 작물 이미지/정적 예시 그래프는 계산에 연결된 Three.js/ECharts로 대체했다.
생리 센서·하드웨어/식물 위치·미구현 상세 route·휴대폰 OS 아이콘·승인으로 오인될
shield는 자료/기능 근거가 없어 채택하지 않았다. 모바일 생성안의 3.12px 글자와
잘못 대응된 입력/메뉴 문구도 적용하지 않고 기존 self-hosted font/접근성을 유지했다.
이 자산은 생성/추출 디자인의 출처를 기록한 내부 연구 화면이며 실제 농장 사진이 아니다.
공개 자산/배포 권리의 전체 G4 점검은 아직 남아 있다.

| 상태 | 원 디자인 참고 | 실제 HTTPS 시험 | 최종 화면 |
| --- | --- | --- | --- |
| desktop | [원안](artifacts/crop-replay-design-reference-desktop.png) | [실제 저장 조회](artifacts/crop-replay-desktop.png) | [개발 데모](artifacts/crop-replay-final-desktop.png) |
| mobile | [원안](artifacts/crop-replay-design-reference-mobile.png) | [실제 저장 조회](artifacts/crop-replay-mobile.png) | [개발 데모](artifacts/crop-replay-final-mobile.png) |
| hold | [원안](artifacts/crop-replay-design-reference-hold.png) | [실제 저장 조회](artifacts/crop-replay-hold.png) | [개발 데모](artifacts/crop-replay-final-hold.png) |

최종 화면은 기록된 공개 합성 응답의 개발 전용 재생이다. 일반 build/운영 API가
fixture를 자동 제공하지 않는다. [직접 실행 안내](../web/README.md#지금-3d를-직접-보기)를 따른다.

## 남은 외부 의존성과 다음 한 단계

`web-crop-replay`만 체크한다. 실제 Axiany forcing/초기기관·밀도·관리 사건의
권리/QC, 해당 품종의 발달/생과 환산·수확/품질·자원/정산과 국내 독립 작기는
별도 미수용이다. 국내 동의/자료는 0건이며 G0–G4는 유지한다.
다음은 `crop-input-audit`의 3문서와 실제 archive 검토다. 단위·시간대/시각·면적,
결측·초기조건·관리 사건을 대사하고 입력으로 쓸 수 없는 채널은 이유와 함께 보류한다.
이를 개발 참조 과실 구획의 문헌식 검토와 독립 농장 확보 준비에 병행한다.

## 앞선 저장/API 판본의 hosted 수용

`d251df9bc5b0bffc7dc236705da6fd6015ad79c2`의 CI 5개가 모두 성공했다.
[전체 backend run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37205032293)은
6분할 373+406+351+763+488+290 = **2,671 passed**, 별도 UID **4 passed**,
모든 동일 전체 목록 hash와 DB/비밀번호 정리·마지막 집계를 확인했다.
이는 생장 유량/적분·저장/API를 포함한 앞선 판본의 회귀이며 새 웹 3D 변경의
hosted 수용을 대신하지 않는다. 새 commit의 CI는 push 뒤 따로 확인한다.

## 성장 화면과 포장 판본의 hosted 수용 — 2026-10-05 KST

`d76410f`의 [웹 CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37213151229)는
typecheck/build·단위 209개와 브라우저 61개(한 worker)를 통과했다.
[작성 경로 CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37213151129)의
7개 묶음과 DB/비밀번호 정리도 모두 통과했다. 새 작물 브라우저 시험은 69.88초로
실제 SCRAM/HTTPS 저장 결과의 6시점 잎 면적/기관 막대 대사와 현재 철회·계정 변경·
재연결을 확인했다. 200/200/200/422/403/200·no-store와 브라우저 오류 0이었다.
이는 해당 fixture 경로의 hosted 증거이며 새로운 품종/농장 검증이 아니다.
[새 CI 판본 증거](artifacts/web-crop-replay-ci-20261005.json)는 실제 log hash와
원 browser report를 보존한다. 앞선 구현 artifact의 경로/hash는 수정하지 않았다.

[포장 보완](crop-web-image-inputs-implementation.md)의 실제 이미지/전체 Compose와
C0도 성공했다. 새 전체 backend 집계는 아직 진행 중이며 앞선 2,671개 수용과
구분한다. 입력 파일 감사와 [과실 구획 명세](crop-fruit-cohorts-baseline.md)는 이후
완료했고 현재 다음 단계는 고립된 과실 순간 이동이다. 실제 Axiany/국내 자료의
보류·G0–G4는 유지한다.
