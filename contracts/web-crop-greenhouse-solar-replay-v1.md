# 일사 저장 결과 웹 연결 v1

상태: [S1a 수용](../research/crop-greenhouse-solar-web-client-implementation-20261017.md).
원 HTTPS6응답·로컬 회귀424검사와 hosted 전체 타입/단위/build/audit를 확인했다.
로컬 전체 TypeScript의 합 RSS 관문은 미통과이며 호스팅 증거를 WSL 용량 수용으로 바꾸지 않는다.
[S2a 기록 화면/회귀 수용](../research/crop-greenhouse-solar-saved-web-implementation-20261017.md)을 추가했다. S1b/S2부모/S2b/S3/S4는 미수용이다. 계산/공개 응답의 선행은
[결과 조회](crop-greenhouse-solar-current-query-v1.md)와
[보호 HTTP](api-crop-greenhouse-solar-route-v1.md)다.
[제품 명세](../docs/PROJECT_SPEC.md#7-순서와-의존성)의 저장→3D 경로를 작은 자식으로 나눈다.

**현재 S1b 후속:** [실제 GET 계측](../research/crop-greenhouse-solar-sdk-read-allocation-20261017.md) 뒤 [같은 신원 읽기 연결 후보](crop-solar-shared-market-reader-v1.md)의 적합성/보안 회귀를 [고유92검사로 수용](../research/crop-solar-shared-market-reader-implementation-20261017.md)했다. 실제 SDK 전체 동시 수용은 남았다. SDK 누적7회는 RSS hold이며 경제 참조 재검증을 작물/CLI0과 구분한다. [추가 실제 GET/RED](../research/crop-solar-native-HTTP-allocation-20261017.md) 뒤 다음은 [현재 보류/판단 맥락 reader](crop-market-held-context-reader-v1.md)이며 미구현이다.

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

S1b는 실제 SDK→인증된 현재 API의 정상/hold·원 선택자/페이지·권리 철회/복원·
잘못된 계정/판본·취소/전송 정리와 조회 계산/SQL 변경0을 확인한다. 원 bytes의 값/단위/UTC·
공통 참조와 대사하고 실제 도구 종료·FD/소유 정리·원본/5root/두 UI/자원을 기록한다.
기록 응답이나 mocked fetch로 live client 전체 수용을 대체하지 않는다.
그다음 원 snapshot의 같은 UTC를 표/그래프/장면에 연결한다. 원 LAI/기관 탄소·구획값의
연구 표현이며 검증되지 않은 실제 형태·생과 수확·사업성 예측으로 표시하지 않는다.
빈 상태/거부 시 장면 제거·재접속·실제 WebGL과 기존 두 화면/원본/자원을 별도로 확인한다.

**2026-10-17 의존성 보완:** 실제 SDK/API 동시 시험 세 번이 합 RSS hold여서 S1b는 미수용이다.
[관측 기록](../research/crop-greenhouse-solar-sdk-resource-and-browser-entry-20261017.md)에 따라
S2의 개발과 실제 연결 수용을 나눈다. **개발을 분리한 S2a**는 수용된 S1a 타입/해석기와
원 정상/hold 응답을 선행으로 하는 저장 화면·회귀다. 별도 Solar 소비자/선택 연결/브라우저 시험의
3–5 core파일을 고정하고 기존 geometry/scene/chart/assets를 재사용한다. 같은 원 UTC의
수치·단위·50구획·PAR/NIR·관리 전후·보류/빈 상태, 선택·계정·취소/권리 거부 시 제거와
기록 원문 기반 WebGL을 확인한다. 이는 live API·사용자 배포 수용이 아니다.
**S2b 실제 HTTPS→저장 WebGL**에는 S1b가 계속 선행하며 실제 현재 권리/원 선택자·페이지·
원 UTC·거부 시 제거/재접속·두 UI/원본/자원을 확인해야 한다. S2 부모는 S2a/S1b/S2b 전부
수용 전 미완료다. 제품 화면에 fixture fallback을 추가하거나 자료/관문 승인을 바꾸지 않는다.

저장 결과용 S1a/S1b/S2는 독립 unpaused worker의 동시 실행 성공을 개발 착수 조건으로
두지 않는다. 해당 현재 결과 API와 원 응답이 선행이다. 이것으로 실행 중 결과 수용이나
사용자 활성화를 완료하지 않는다.

## S2a 구현 경계 — 2026-10-17

핵심 파일은 `web/src/GreenhouseSolarReplay.tsx`, `web/src/CropReplay.tsx`,
`web/e2e/greenhouse-solar-replay.spec.ts`다. 기존 scene/geometry/chart/CSS/잎 자산을 재사용한다.
Solar 전용 해석기/요청으로 읽고 다른 모델 타입으로 캐스팅하지 않는다. 화면은 원108상태,
41연속/6사건 장부·15수지, 같은 UTC의 PAR/NIR/환기와 관리 전후 진단을 보존한다.
표·그래프·실제 WebGL·50구획·선택 시각의 원 값, 실패 이전 출력/빈 상태·페이지·지연 응답/
선택/계정/취소/현재 거부 시 제거를 기록 응답으로 검증한다. 기존 세 판본 회귀도 함께 확인한다.
CI의 집중 선택과 합성 화면 PNG 보존은 이 화면 검증의 보조 경계이며 전체 CI/G1/G4가 아니다.
최초 적용 전 타입/기존 단위·기록 Chromium/원본·두 화면/자원과 원 디자인 대조를 기록한다.
새 fixture fallback·생장/열·수확/금액 계산은 추가하지 않는다. 실제 HTTPS 결합은 S1b/S2b에 남는다.

## S3/S4 — 실행 중3D와 사용자 활성화

계산 중3D는 [실행 runtime](crop-greenhouse-solar-execution-runtime-v1.md)의 실제 독립
unpaused 정상/hold/취소·전진 prefix/원 UTC·현재 권리·조회 계산0·동시 자원 수용이 선행이다.
저장/실행 중 장면을 각각 검증한 뒤 같은 배포 판본의 사용자 접수·재접속/재시작을 수용한다.
현재 필수5root/동적 자식·512MiB/PID·합1GiB와 제품 관문을 유지한다.

## 일정과 외부 의존성

S1a→실제 HTTPS→저장 WebGL과 실행 runtime→prefix WebGL을 준비된 순서로 진행한다.
S1a 원문 확보 guard204.794초/최종 회귀2.907초이며 개발·분석/CI·실패 시도 시간과 구분한다.
S1b의 실제 시험 구성/응답 비용을 확인한 뒤 다음 시간을 갱신한다. 현재 전체 날짜와
남은 집중 시간은 미정이다. 지역/품종/시설·독립 농장·시장 자료의 확보/권리/검증은
이 소프트웨어 연결과 병행하며 해당 제품 게시 조건은 제품 명세를 따른다.
