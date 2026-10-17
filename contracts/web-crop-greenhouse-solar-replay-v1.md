# 일사 저장 결과 웹 연결 v1

상태: S1a 구현 후보·원 HTTPS6응답과 로컬 회귀424검사 통과. 전체 TypeScript 컴파일은
종료0을 관측했으나 로컬 합 RSS 관문을 통과하지 못해 S1a 전체 수용은 보류한다.
S1b/S2/S3/S4는 미수용이다. 계산/공개 응답의 선행은
[결과 조회](crop-greenhouse-solar-current-query-v1.md)와
[보호 HTTP](api-crop-greenhouse-solar-route-v1.md)다.
[제품 명세](../docs/PROJECT_SPEC.md#7-순서와-의존성)의 저장→3D 경로를 작은 자식으로 나눈다.

## S1a — 저장 응답 해석기와 요청 클라이언트

구현 core: `web/src/greenhouseSolarReplay.ts`, 대응 `.test.ts`, `web/src/api.ts`의 공통 factory
연결과 원 응답 fixture. 기존 공통 요청/검사 유틸리티를 사용한다.

- 일사 모델의 별도 result ID·farm 선택자와 summary/samples/events 요청을 사용한다.
  환기/공동 기후 ID·버전·단위를 혼합하지 않는다.
- 실제 정상/hold의 공개 응답을 같은 source/model/parameter 판본으로 수집하고 원 bytes의
  해시·원 UTC·수치·단위·페이지 수를 기록한다. 합성 공개 응답만 테스트 fixture로 보존한다.
  기존 projection template는 구조 시험용이며 실제 HTTPS 원문을 대신하지 않는다.
- 닫힌 응답 해석에서108상태,41연속/6사건 장부,15수지와 PAR/NIR·환기 진단,
  관리 전후 상태·단위·UTC를 보존한다. 원 값을 변환/추정하거나 광/수확/비용을 계산하지 않는다.
- JSON keyset·버전/해시·finite 수치·50구획·수지 예산·원 microsecond UTC/격자·
  summary/page 동일 판본을 검사한다. samples64/events8의 페이지 경계, 총량/전진/종료,
  2MiB 응답 상한·취소/시간 초과·거부 응답을 기존 요청 계약에 연결한다.
- 수용 증거는 원 정상/hold 응답의 해석·원 값/UTC 대사, 혼합/변조/경계 거부,
  페이지/취소/오류 단위 검사, TypeScript 검사와 기존 환기/공동 기후 회귀다.
  기록 원문 해석과 실제 SDK→현재 HTTPS 호출은 각각 검증 범위를 표시한다.

## S1b/S2 — 현재 HTTPS 연결과 저장3D

S1a 뒤 실제 SDK→인증된 현재 API의 정상/hold·원 선택자/페이지·권리 철회·취소/전송
정리와 조회 계산/SQL 변경0을 확인한다. 이 증거 없이 live client 전체 수용으로 표시하지 않는다.
그다음 원 snapshot의 같은 UTC를 표/그래프/장면에 연결한다. 원 LAI/기관 탄소·구획값의
연구 표현이며 검증되지 않은 실제 형태·생과 수확·사업성 예측으로 표시하지 않는다.
빈 상태/거부 시 장면 제거·재접속·실제 WebGL과 기존 두 화면/원본/자원을 별도로 확인한다.

저장 결과용 S1a/S1b/S2는 독립 unpaused worker의 동시 실행 성공을 개발 착수 조건으로
두지 않는다. 해당 현재 결과 API와 원 응답이 선행이다. 이것으로 실행 중 결과 수용이나
사용자 활성화를 완료하지 않는다.

## S3/S4 — 실행 중3D와 사용자 활성화

계산 중3D는 [실행 runtime](crop-greenhouse-solar-execution-runtime-v1.md)의 실제 독립
unpaused 정상/hold/취소·전진 prefix/원 UTC·현재 권리·조회 계산0·동시 자원 수용이 선행이다.
저장/실행 중 장면을 각각 검증한 뒤 같은 배포 판본의 사용자 접수·재접속/재시작을 수용한다.
현재 필수5root/동적 자식·512MiB/PID·합1GiB와 제품 관문을 유지한다.

## 일정과 외부 의존성

S1a→실제 HTTPS→저장 WebGL과 실행 runtime→prefix WebGL을 준비된 순서로 진행한다.
S1a의 실제 작업량·원 응답 확보/집중 검사 뒤 다음 시간을 갱신한다. 현재 전체 날짜와
남은 집중 시간은 미정이다. 지역/품종/시설·독립 농장·시장 자료의 확보/권리/검증은
이 소프트웨어 연결과 병행하며 해당 제품 게시 조건은 제품 명세를 따른다.
