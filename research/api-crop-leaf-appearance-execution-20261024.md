# 자동 출현 계산 보호 HTTP — 2026-10-24

상태: [보호 HTTP 계약](../contracts/api-crop-leaf-appearance-execution-v1.md)의 **합성 소프트웨어 기능 수용**.
[기존 자동 consumer](leaf-appearance-automatic-consumer-20261024.md) 다음의 접수·현재 조회·취소6경로다.
사용자 runtime/같은 job3D·계산 중 재접수/동시 U1은 후속이다.
[사용자 저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 유지하며 새 API는 사용자 runtime에 미배포다.

## 구현과 호환성

표준 create_app에 선택적 appearance service/query와 닫힌 typed 요청/응답을 추가했다.
기본 비활성503·부분/다른 graph 거부, 같은 jobs/provider/admission/query·farm/완료 parent graph를 유지한다.
테넌트는 현재 인증이 결정하며 원 program/source/evidence bytes·키·임의 경로는 요청에서 받지 않는다.
현재 Scope/tenant·서비스 결속을 전후 확인하고 기존 ErrorEnvelope·고정 공개 이유를 사용한다.
JSON64KiB/응답2MiB·no-store와 원 UTC/기관/면적·sample_count/정책·준비 참조를 유지한다.
계산은 기존 worker/consumer가 맡으며 HTTP에서 생장 계산이나 관문 승격을 하지 않는다.

변경 전 실제 schema-only export와 저장된 문서의 동일성을 먼저 확인했다.
OpenAPI는 **80경로/84연산/492스키마 → 86경로/90연산/496스키마**다.
기존80경로·492스키마와 Scope 객체가 모두 같고 새6경로·4스키마만 추가됐다.
이전 HTTP 모듈과 E2/E3/consumer의12개 소스 지문도 그대로였다.

## 통과한 검증

| 범위 | 고유 검사 | 확인한 내용 |
| --- | ---: | --- |
| 신규 HTTP/ASGI 제어 | 47 | 닫힌 요청/응답·상한·오류, 현재 인증·Scope·graph, 이전 입력/권리 판본 거부, 연결 종료/전송 실패 문맥 정리 |
| OpenAPI/Scope | 101 | 기존 계약·문서 일치, 새6경로/operation ID·권한/typed 계약과 기존 경로 권한 유지 |
| 기존 잎 HTTP 제어 | 45 | 기존 leaf-population 요청/조회·graph·권한/오류·문맥 유지 |
| 실제 SCRAM·검증 TLS | 3 | 접수/멱등·409/실제 worker/원 완료 조회, 철회 후 취소·늦은 만료, 원본/부모 검토 변경 |
| **합계** | **196** | 반복 실행·native 부분 선택의 제외1개는 중복 합산하지 않음 |

실제 TLS 정상 경로는 인증 없는401, 신규202, 같은 요청의 같은 job, 변경409와 worker 완료를 확인했다.
완료 원12frame/47면적의 전체 bytes·UTC/기관 ID, frame11·manifest·result/parent root·최초 시각을 대사했다.
현재 자료 권리 철회는422, 철회 후 취소는200/결과 미게시였다.
읽기 뒤 인증 만료는401, 늦은 resolver source/parent 검토 변경은 각각422였으며 검토 복원도 확인했다.

모든 실제 HTTP query.read 호출에 생장/CLI·8개 작업/객체 쓰기·지속 SQL·3개 파일 write-open 차단을 적용했다.
관련 호출/쓰기 시도는 모두0이었으며 정상/늦은 변경 조회의25표 원 행 SHA를 보존했다.
취소의 명시적 JobStore 쓰기는 이 query.read 구간과 구분한다.
19개 실제 요청 모두 기존30초 안이었고 최장 요청은 replay **11.946599초**였다. 접수는11.400초였다.
현재성 검사를 생략하거나 timeout을 늘리지 않았다. 계산 중 동시 요청/동일 재접수·공통 U1/G4 수용은 아니다.

최초 미등록의 예상 RED45오류와 이전 입력/권리 판본의 추가2반례를 보존했고 이후47개를 통과했다.
예상 RED 외의 실패나 생산 코드 수정은 없었다.
native는 사용자 DB와 분리한 scratch PostgreSQL에서 순차 실행했다.
schema/role0·passfile/짧은 임시 PG 디렉터리 제거, TLS thread/소유 process 정리와 FD4→4를 확인했다.
전체 backend/이번 hosted CI·브라우저·사용자 runtime 배포는 실행하지 않았다.

source는 `b7effd42b196e7956b7d57748b2ba942b160987e`다.
native gpt-6.1-sol/xhigh의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
최종6소스 지문·기준선/호환성·원 로그/종료·각 요청/조회 차단 증거는
[기계 기록](artifacts/api-crop-leaf-appearance-execution-20261024.json)에 보존했다.
기존 수치 모델/원 입력·서명·사용자 웹/DB/키/서비스는 변경하지 않았다.

## 자원과 다음 단계

정상 native246.984초였다.7개 검증 단계의 최대 PID176,832,512/보호+소유 합586,919,936bytes였다.
.25초 설정·512MiB/PID·1GiB 합산/600초/4MiB 로그 안에서 보호3root·원2,504항목/현재 소스·잔여0·FD4→4를 보존했다.
Windows Chrome을 포함한 공통 호스트 capacity나 동시 처리량 증거로 표시하지 않는다.

다음은 기존 owned preview의 appearance resolver/현재 검토·권리·서명 authority/service/query와 정확 consumer 조립이다.
기존 farm/parent의 과거 판단에 새 source를 소급 부착하지 않고16시 이후 decision의 별도 합성 farm/완료 parent를 사용한다.
실제 API 접수→자동 발견/계산→같은 저장 결과 조회·취소/현재 철회, 원 행/파일·DB/키/기존 화면·WSL 보존을 확인한다.
이후 사용자 적용→strict SDK/같은 job의 사실적 잎3D·UTC/표/그래프·메뉴/reload와 실제 브라우저를 검증한다.
계산 중 동시 요청/재접수의30초·U1은 실제 통과 전까지 별도 보류한다.

이전 API90–180분 예상은 위 실적으로 대체했다.
다음 runtime 조립25–50분 + 실제 자동 API/취소·현재성/보존25–50분 + 기록10–20분 =
**60–120집중분**의 낮은 신뢰 작업량이다. 후속 사용자 적용/SDK/UI와 자료 확보 시간은 포함하지 않는다.
실제 품종/국내 독립 작기0, 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고·실제 runtime CLI G1/G0–G4와 전체 제품 날짜 미정·goal 미완료를 유지한다.
