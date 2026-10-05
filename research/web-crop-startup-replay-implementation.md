# 저장된 시작 모델의 같은 UTC 성장 연구 3D 수용

2026-10-05 KST. **합성 연구 결과의 로컬 소프트웨어 경로**를 수용한다.
도형 commit `44bf506`, 화면/실제 경로 commit `363ba6d`.
[계약](../contracts/web-crop-startup-replay-v1.md),
[수치·파일·화면·시험 증거](artifacts/web-crop-startup-replay-reference-20261005.json)를 확인한다.

## 사용자가 확인할 산출물

- 실제 저장 경로의 [데스크톱](artifacts/startup-crop-desktop.png),
  [모바일](artifacts/startup-crop-mobile.png),
  [확인된 과거가 있는 보류](artifacts/startup-crop-past-hold.png),
  [빈 보류](artifacts/startup-crop-empty-hold.png).
- `08 성장 연구 3D` → **v3 · 명시 진입·빈 과실 유보 연구**에서 현재 권한으로
  저장 ID와 등록 농장 판본을 조회한다. 기존 v1/v2와 메모리 토큰 방식을 유지한다.
  위 화면은 임시 시험 DB의 기록이다. DB는 정리됐고 운영 저장 목록이 아니다.
  로컬 기록 데모의 기존 v2 예제를 이 새 v3 기록으로 바꾸지 않았다.

새 decoder가 전체 sample/event를 검증한 뒤, 같은 저장 ID/farm/manifest/UTC의
50 C/N·기관·LAI·16누적·4진단을 표·그래프·3D에 연결한다. 최대512/128은 최대16회
순차 조회이며 사건 표시 페이지는 이미 검증한 배열에서 선택한다. 부분 결과는 표시하지 않는다.
계정/농장/판본 변경·현재 거부·취소/늦은 응답에는 이전 값과 장면을 지운다.
보류의 확인된 과거만 재생하고 소수 초 마지막 확인 상태는 별도 진단으로 보존한다.

재생은 저장 인덱스만 선택한다. 미래 상태·생장식·탄소 총량·누적량을 브라우저에서
계산하지 않는다. 잎 한 면 면적은 LAI와 대사한다. 도형의 높이·색·좌표는 실제 키,
열매 크기·개수·숙기·생과 kg가 아니다. 명시 진입/빈 sink 유보·전환 수렴 미평가와
작은 구획 합성 시험의 약8.52% 오차를 계속 표시한다.

## 극소 양수와 표시 척도

실제 저장 합성 empty-entry의 60초 값은 C 최소5.291029192486798e-214,
N 최소6.782557198434201e-222였다. 선형 높이는 Float32에서 각각37/38개가 0이 됐다.
v3에는 전체 저장 시점의 각 C/N 양수 최솟값 m/최댓값 M에서
L=floor(log10(m))-1, U=ceil(log10(M))를 고정하고 높이=(log10(v)-L)/(U-L)를 적용한다.
영은 숨기고 전부 영이면 양수 축이 없다. 임의 seed/작물 최소량을 만들지 않는다.
장면에 로그 비교와 L/U를 표시하고 표/그래프는 원 단위/값을 유지한다.
기존 v2 선형 표시와 unsafe GPU의 HTML 대체는 보존했다.

원 수치/단위·구획·visibility/중심 y는 정확히 대사했다. Node와 Chromium의 log10에서
2.220446049250313e-16의 표시 높이 차이가 관측돼, **표시 높이만** 4×Number.EPSILON의
절대 허용치를 적용했다. 영 높이는 정확히0이며 원값 검사는 완화하지 않았다.
별도 Python 영수증 대사의 최대 높이 차이는1.1102230246251565e-16이다.
농업 오차 허용치나 생장 계산 계수로 사용하지 않는다.

## 통과한 검증

| 검증 | 실제 결과 |
| --- | --- |
| 도형 집중 | 새7개와 기존17개, **24 passed**, 영/극소·극대·고정 축·50 mesh 원값/정리 |
| 웹 전체 단위 | **383 passed / 0 failed / 0 skipped**, 17개 파일; 새 도형7개 포함 |
| 집중 Chromium | **31 passed / 0 failed / 0 skipped**, 새12개·기존19개, 단일 worker·1.7분 |
| 실제 저장 → HTTPS/Bearer → WebGL | **1 passed / 195.57초**, PostgreSQL16.15/SCRAM·표준 API/새 client |
| 실제 완료 시점 | 빈 초기3·전량 제거/재유입3·양의 tail6, 고유12개; 모두 짧은 합성 계산 |
| 실제 화면 대사 | 과거/복귀/재연결 포함15번·C/N **1,500개 mesh**·원 단위/표/두 그래프·16누적/4진단 |
| 잎 면적 | 실제 한 면 삼각형 면적 최대 절대 오차8.881784197001252e-16 |
| 권리/계정 | 응답200,200,200,200,200,200,422,403,200; 성공 전체 본문7개·최대9.485초·no-store |
| 저장/정리 | 결과 행5→5, GET 재적분 금지, 브라우저 오류0, 서버/thread·DB/역할/schema/password 정리0잔여 |
| 장애/접근성 | 최대512/128의 전체성·취소/혼합 거부·권리 거부·계정 변경·소수 초/빈 보류·WebGL loss/restoration/HTML 대체·키보드·320/390/768/1536px·200% 글자 확대·reduced motion |
| 빌드 | typecheck/Vite build 성공, 0.579초; 기존 SVG chunk520.20kB의500kB 경고 유지 |

512/128 브라우저 사례는 **명시적인 cardinality shape 시험**이다. 이 실제 저장/브라우저
시험이512개의 작물 출력이나 전체 작기를 계산했다는 뜻이 아니다. 실제512출력/128사건의
API 본문 검증과24시간 적분/artifact는 각 선행 영수증의 별도 증거다.
시험 fixture의 완료3사례는 앞선 실제 SCRAM packet의 공개 합성 projection이고 보류2사례는
별도 순수 수학 projection이다. 이번 실제 경로는 새로5개를 저장하고 HTTPS로 조회했다.
fixture를 현재 운영 행이나 원 TLS wire bytes로 표시하지 않는다.

초기 RED는 새 판본/도형 함수 부재였다. 이후 lazy 화면 준비를 기다리는 시험 도우미,
명시적인 option value49(구획50), runtime decoder를 거친 quantity 타입 경계,
Playwright의 명시적 반복 사례와 위 표시 높이 차이를 수정했다. 모든 최종 검증은 통과했다.
기존 수학/profile/artifact/custody/API34개 hash와 client decoder/HTTP·잠금을 보존했다.
새 Framework·계수·큐·상주 서비스는 없다.

```bash
cd web
npm test -- --maxWorkers=1
npm run test:browser -- startup-crop-replay.spec.ts coupled-crop-replay.spec.ts crop-replay.spec.ts
npm run build
```

실제 DB 시험은 `backend/tests/web_crop_startup_replay_smoke.py`이며 기존 authored browser
CI 목록에 한 줄을 추가했다. 이는 새 작물 경계의 검증이며 운영 기반 확대가 아니다.
원격92cade3 실행은 새 API/client/3D를 포함하지 않는다. 그 실행을 취소하지 않고 완료를 기다린다.
로컬 Docker·production 배포·새 판본 hosted 수용은 이번 검증에서 실행하지 않았다.

## UI 검토와 WSL 자원

현재 CLI 세션01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc의
2026-10-05T04:25:00.397Z turn_context에서 **gpt-6.1-sol / xhigh**를 확인했고,
그 세션에서 구현/판단/검토했다. 재귀 CLI는 없다. 실제 context와 출력 hash를 증거에 기록했다.
12ui-design·browser-testing 절차를 적용했다. Chrome MCP가 없어 기존 격리 Playwright를 사용했다.

기존 승인 완료/과거/빈 보류 LayerDoc을 그대로 사용해12ui target closeout을 수행했다.
monorepo 루트의 src 부재와 durable repo 변경 거부를 기록한 뒤 올바른 web 경로의 무료 kit로
복구했다. 완료20.5%·빈 보류21.9%·과거25.7%는60%보다 낮아 **pixel fidelity는 미수용**이다.
생성된 정적 도형/그래프와 토큰 입력에 도형을 배치하는 잘못된 매핑을 적용하지 않았다.
부족한 hold raster·unsupported 숫자/범례를 과학적 결과로 그리지 않았으며 기존 테마/자체 글꼴/
네 실제 디자인 자산을 재사용했다. 새 구매/글꼴/자산은0개다. 실제 데스크톱·모바일·보류 화면을
직접 확인했다. 전체 시각적 충실도 보류를 기능·수치 수용으로 대체하지 않는다.

DB는 단일 loopback SCRAM·max_connections32/shared_buffers16MB/work_mem1MB의
임시 클러스터였다. nice 프로세스와 단일 브라우저 worker를 순차 실행했고, 실제 시험 child
최대RSS는622.39MiB(WSL 전체 메모리가 아님)였다. 시험 DB·HTTPS/frontend와 추가 UI preview
서버를 모두 종료했고 임시 preview HTML·자격 파일/역할을 제거했다. 공개 화면은 자작 합성
수치의 변경 없는 PNG이며 실제 개인 농장 자료가 없다.

## 다음 한 단계와 남은 외부 의존성

화면과 실제 연결은 **10월5일 KST 로컬 완료**다. 기존1.5–3시간 잠정치를 이 실제 수용으로
대체한다. 다음은 `crop-cycle-execution-contract`: 현재 적분의 상태/누적량/forcing·event·output
cursor와 전역 걸음 경계, 불변 checkpoint/hash/권리, 실패·재시작·출력 분리를 먼저 계약한다.
추가 chunk 경계가 RK4 계산 격자를 바꿔 결과를 바꾸지 않는지 확인하고, 이후 작은 순수
연속 실행 모듈 → 저장/페이지 → 실제 작기 부하의 순서로 분해한다. 단순 한도 증대는 수용이 아니다.

이 다음 계약/분해는 코드 독해·독립 대사/보류 목록·수용 검토의 **2–4 집중시간** 잠정이다.
하루4시간/CI 대기 제외 기준10월5–6일 KST가 목표이며 실제 전체 작기/생과 모델 날짜는
그 분해와 실제 입력 확보 뒤 추정한다. 국내 독립 자료0건·adopted actual forcing/crop Run0개다.
자동 착과·pre-onset/실제 초기 품종 계수, G0–G4·생과/자원·경제/예측·작물 순위는 보류한다.
자료 확보를 모델 개발의 선행으로 잠그지 않는다. 실제 예측·추천의 완료 날짜는 아직 산정하지 않는다.
