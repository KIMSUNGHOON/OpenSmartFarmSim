# 시작 유보 모델 — 응답 해석과 전체 순차 페이지 결합

날짜: 2026-10-05 KST. **합성 저장 응답/페이지의 로컬 수용**이다.
구현 commit `3e61724`. [화면 계약](../contracts/web-crop-startup-replay-v1.md) 첫 구획과
[파일/시험·기록 응답 대사 증거](artifacts/web-crop-startup-pages-reference-20261005.json)를 확인한다.
새 장면/브라우저와 실제 품종 생산 예측을 수용한 것은 아니다.

## 실제 CLI와 구현

현재 CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 turn_context
`2026-10-05T04:03:18.857Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
그 세션에서 판단·구현·검토했으며 CLI를 재귀 실행하지 않았다.
actual context line hash와 출력 파일 hash를 증거에 보존했다. 제품 runtime CLI는 별도 미수용이다.

새 206행 client는 v3 ID/농장·schema/program/모델 판본·9개 code hash/두 정책/
두 artifact dependency·면적 문자열, 50 N/C·16누적/4진단과 연구 hold를 검사한다.
기존 기관/단위·event/page validator 네 개를 같은 v2 모듈에서 명시적으로 재사용한다.
v2에는 export 두 행만 추가했으며 판본/숫자/조회 동작은 그대로다.
v3의 ID나 모델 이름을 v2로 바꾸어 검사하지 않는다.

인증된 기존 HTTP 함수에 두 메서드를 추가했다. **최대512 sample/128 event를
최대16회 순차 요청으로 모두 수집**한다. 각 응답은 30초/2 MiB이며 sample/event 각각의
다음 offset을 진행하고 끝난 쪽은 빈 마지막 페이지를 받는다. 같은 저장 ID/farm/첫 DB UTC/
면적/manifest/status·총수와 시각 순서를 매 페이지 대사한다. 원값을 재계산/보간하지 않는다.
현재 거부/취소·식별자 변경·늦은 성공·누락/중복/혼합에는 부분 재생 결과를 반환하지 않는다.
소수 초 hold는 microsecond 비교를 유지하고 last_confirmed를 sample로 추가하지 않는다.
미세 구획 약8.52% 합성 오차·수렴/품종 미검증·관문 미평가 설명을 보존한다.

## 통과한 검증

- 최종 **웹 전체 단위376개, 새 단계77개, 건너뜀0개**가 통과했다. 16개 시험 파일의
  JSON report wall 구간은 약6.06초다. 그 전에 작물/도형/HTTP 집중229개도 통과했다.
- 초기 RED는 새 모듈 부재였다. decoder만 작성한 중간28개 통과/나머지3개 미선택,
  전체 첫31개 통과를 기록했다. 확대 후 타입 검사에서 시험 도우미의 page 반환 타입
  8개 오류가 나왔다. 변형용 fixture의 반환 경계를 명시한 뒤 최종 타입 검사가 통과했다.
- **`npm run build`의 typecheck와 Vite build가 모두 통과**했다.
  기존 SVG renderer chunk 520.20 kB에 관한 500 kB 경고는 남아 있으며 제한을 완화하지 않았다.
- 실제 앞선 SCRAM/HTTPS 시험 응답0의 **정확한 decoded JSON 원값**을 fixture로 고정했다.
  64 sample/8 event·686,491 file bytes와 SHA를 대사했다. 원 TLS wire bytes나
  현재 운영 기록으로 표시하지 않는다. 이 fixture는 시험에서만 읽고 제품 번들에 넣지 않는다.
- 512/128의 완전한 순차 결합은 명시적 shape fixture로 검증했다. sample/event 도중 현재
  403/422 거부, HTTP401/403/404/422/503, late/cancel·30초 timer/listener/stream 정리,
  초과 본문/UTF-8, UTC/페이지/모델/해시/면적/단위/진단 변조를 검증했다.
- 기존 v1 decoder·v2 해석/도형과 package/lock을 보존했다. backend math/profile/artifact/
  custody/API의34개 SHA는 앞선 API 증거와 동일하다. 새 계수·Framework·상주 서비스는 없다.

실제 저장→TLS→새 client→3D 브라우저 시험은 **이번 구획에서 실행하지 않았다**.
표준 TLS/SCRAM API의 실제19응답은 [선행 API 수용](api-crop-startup-replay-implementation.md)이고,
최종376개는 웹 단위 시험이다. 이를 새 브라우저/생산 경로의 종단 간 증거로 합치지 않는다.
시험과 빌드는 순차 nice 프로세스로 실행했고 새 DB/서버/브라우저/GPU 서비스는 기동하지 않았다.

## 다음 한 단계와 외부 의존성

다음은 새 시계열 객체의 **같은 저장 ID/farm/hash/UTC sample을 표·그래프·기존 50구획
수치 도형에 연결**하는 화면 구획이다. 빈 초기/전량 제거 후 재유입·완료/과거 hold/빈 hold,
LAI 잎 면적·공통 C/N 척도/원 수치·mesh·취소/권리 거부·WebGL 대체/정리를 시험한다.
집중 Chromium과 실제 SCRAM 저장→표준 HTTPS→브라우저의 원값 대사·정리 후에만
부모 `crop-startup-replay-link`를 체크한다. 임의 seed/숙기 색상·생과 kg를 추가하지 않는다.

응답/페이지는 **10월5일 KST 로컬 완료**다. 남은 화면/도형·브라우저1–2시간과 실제 경로/
정리·보고0.5–1시간의 **1.5–3 집중시간**, 하루4시간 기준 **10월5–6일 KST**를 추정한다.
기존 coupled 화면의 129단위/19Chromium/실제 경로1개가 근거이며 CI 대기는 별도다.
`d105daa`의 시작 수학 hosted CI는 수용됐고 저장까지의 `92cade3` backend는 확인 중이다.
이번 API/client 커밋은 아직 그 원격 실행에 포함되지 않았다. 같은 실행을 취소하지 않는다.
국내 독립 자료0건·actual forcing/crop Run0개·G0–G4 미수용과 전체 작기/생과·자원/경제의
외부 의존성을 유지한다. 실제 예측/추천 완료 날짜는 자료 확보 뒤 추정한다.
