# 원 저장 결과의 HTTP SDK — 2026-10-30

[원본 연결](crop-supply-morphology-source-graph-20261030.md)과
[저장 수치 검증](crop-supply-morphology-stored-quantities-20261030.md)에 이어
[HTTP 계약](../contracts/supply-morphology-http-replay-v1.md)과
[SDK](../web/src/supplyMorphologyReplay.ts)를 수용했다.
**자체 공개 합성 fixture의 연구 재생 SDK** 범위다. 새3D·제품 농장/worker·운영 수용은 남아 있다.

고정한 공개 경로와 독립 root/index를 사용하며, 기존 스트림 reader의 credentials omit,
no-store·redirect error·2MiB/파일과 graph의64MiB/512프레임/32768좌표 제한을 재사용한다.
호출마다 권리·원 byte/hash·기관/시계/장부를 다시 검사한다.
`summary()`와 `frame(index)`는 매번 방어 복사하며, 세대별 요청 취소로 이전 응답의 반환을 거부한다.
자료 캐시·새 생장 계산은 추가하지 않았다.

## 실제 검증

- 새 집중9검사: 원101파일·38프레임/6208좌표, 단위/원 UTC/phase·현재 선언 권리,
  잘못된 선택, 선택/다른 프레임/summary의 복사 격리, HTTP 상태/빈 응답/잘못된 byte·용량 초과/스트림 오류,
  사전/대기 중 취소와 abort를 무시하는 늦은 응답을 거부했다.
- 전체 TypeScript 타입·별도 ES2022 번들 통과. 번들97,247bytes,
  SHA256 `703d93ab6a740c633e48c3eeb56ae1af8f65d1a8b95d66d2b7134cfb9a012c67`.
- 독립 실제 HTTP 서버: 정상 두 번202원본 GET, 실패/취소를 포함한 총306자료 GET.
  38개 반환 프레임을 원 저장 투영과 모두 대조했다. 최초101파일14,197,795bytes의 HTTP+decode는 약3.610초였다.
  실제 요청의 cache 정책·인증/cookie 없음,2MiB 초과·302 추적 거부·마지막 프레임404·응답 도중 abort/latest도 확인했다.
  검증 서버와 소유 프로세스는 종료했다. 실제 브라우저 수용은 아니다.
- 첫 HTTP 검사도 통과했지만 취소 후 테스트 서버의 keepalive read에 ConnectionReset 로그가 있었다.
  새 v2 검사기는 예상 client reset과 뜻밖의 오류를 분리 계수했으며, v2는 뜻밖의 오류0이었다.
  첫 기록과 v2를 모두 보존했다. 애플리케이션 구현은 바꾸지 않았다.

기존393source/1output, CAS124개/입력 metadata32개·원 false/true 권리와 동결 GUI4,865파일 등
기존 보존 사슬을 확인했다. 모든 단계에서 원4,500항목·실행 중5175와 WSL 상한/정리를 보존했다.
타입 검사는 native compiler의 `GOMEMLIMIT=160MiB,GOGC=15,GOMAXPROCS=1`로 수행했으며
관측 PID 최고 RSS528,699,392bytes는512MiB 이내다. 상한을 올리지 않았다.
전체 웹 빌드/전체 suite·새 UI·API/DB/worker는 실행하지 않았다.

정확한 native `gpt-6.1-sol/xhigh`의 현재 세션/작업공간 메타데이터와 실제 출력 지문은
[기계 증거](artifacts/crop-supply-morphology-http-sdk-20261030.json)에 있다. 재귀 CLI0·생장 RHS0이다.
이전 wire51/graph93/수치64검사는 불변 부모의 수용 증거이며 이번9검사에 재실행한 것으로 합산하지 않는다.
독립 국내 품종/농장 자료0·G0–G4 `not_assessed`/R2 `not_approved`, 원 terminal hold와 전체 goal 미완료를 유지한다.

## 다음은 같은 상태3D

원38프레임에는 길이0인 절간4행과 부착 미지정 초기 잎3개/114행이 있다.
기존 renderer는 양수 길이/명시 부착을 요구하므로 그대로 강제로 연결할 수 없다.
새 렌더링은0을 늘리거나 부착 ID를 만들지 않고 원 존재/치수/부착 상태를 보존해야 한다.

작업 분해는 기관→mesh/독립 면적·길이 검증0.5–1.5h, 저장 선택/재생·표/그래프 화면1–2.5h,
실제 브라우저/재조회·모바일·자원·기존 화면 회귀0.5–1.5h, 사용자 preview 적용0.5–1h다.
합계2.5–6.5집중시간의 잠정 추정이다.23:15 KST 연속 착수 가정이면 연구 화면 검증 목표는
**2026-10-31 01:45–05:45 KST**이며, 다음 mesh 검증의 실제 결과와 자원 상태로 갱신한다.
실제 품종 한 작기·생산량/자원·경제/거시/수급·자율 비교/제품 전체 완료일과 독립 자료 확보일은 미정이다.
