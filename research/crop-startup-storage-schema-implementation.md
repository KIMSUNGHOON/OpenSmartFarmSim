# 시작 유보 계산 저장 v3 — 표·권한·설정

날짜: 2026-10-05 KST. **저장의 schema/role/config 구획만 로컬 수용**했다.
구현 commit: `ec7c634`.
[저장 계약](../contracts/crop-result-v3.md),
[실제 시험 목록·코드/로그 hash·SCRAM/정리 증거](artifacts/crop-startup-storage-schema-reference-20261005.json)를 확인한다.

## 실제 CLI와 구현

현재 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn_context
`2026-10-05T02:01:46.820Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
같은 세션에서 설계/구현/검토했고 CLI를 재귀 실행하지 않았다.
실제 context line·출력 코드/시험 hash를 증거에 기록했다. 제품 runtime CLI의 수용은 별도다.

새 `crop_startup_research_results` 표는 `crop-result-v3`의 tenant/study/revision 및
result ID 유일성, tenant 포함 등록 job 외래키, packet hash/20 MiB·판본/범위/ID 제약,
UPDATE/DELETE 거부 trigger를 가진다. owner도 실제 행 수정/삭제 시 trigger에 걸린다.
`crop_startup_result_storage`는 기본 false다. 명시적으로 선택한 authority만
SELECT/INSERT하고 다른 세 역할은 직접 접근할 수 없다. 기존 선택 방식/현재 전체 권한
감사를 사용하며 표·역할·자료를 자동 갱신하지 않는다.
operator의 누락/false/true와 잘못된 타입을 검증했다. True 설정의 모의 API 조립 시험은
새 계산 API의 수용이 아니며 새 custody factory/endpoint는 아직 없다.

6개 구현/시험 파일에 한정했다. 기존 모델/artifact/profile·v1/v2 저장의 **25개 pin**을
대사해 보존을 확인했다. 새 dependency·계수·큐·상주 서비스는 추가하지 않았다.

## 통과한 검증과 교정

- 첫 RED: 새 필드/installer 부재와 설정 거부로 **8실패/4통과**.
  구현 뒤 기본·설정/식별자 12개가 통과했다.
- 새 최종 시험 **20개/4.65초·건너뜀0**. 기존 역할·operator·실제 로그인/API 조립과
  v2 farm custody/재시작까지 **184개 고유 시험의 분할 수용**이다.
  첫 큰 집중 실행의 183통과/1실패(235.41초) 뒤 새 20개와 해당 한 개를 실제 발급
  조건으로 재확인했다. 이 기록을 184개 단일 실행 또는 전체 백엔드 통과로 표현하지 않는다.
- 실제 SCRAM SELECT/INSERT·행 bytes/최초 DB 시각, 다른 세 역할의 SELECT/INSERT
  거부·authority UPDATE/DELETE/TRUNCATE 거부·owner UPDATE/DELETE trigger를 확인했다.
- 비활성 상태에서도 provisioned 표에 네 runtime 역할의 SELECT가 모두 거부된다.
  FK/교차 tenant, 빈/과대·hash/서명·판본/범위/ID·유일성의 **17개 잘못된 행**을 거부했다.
- worker/PUBLIC SELECT·authority UPDATE/column UPDATE·authority SELECT 철회의
  다섯 실제 권한 변화가 현재 전체 감사에서 거부된다.
- 시험 전제를 교정했다: 빈 bytes의 integrity/JSON 거부 순서를 단정하지 않고, 기존
  역할의 재설치를 호출하지 않는다. 빈 fixture 매개변수는 기존 fixture의 비밀번호 발급을
  생략하므로 명시 False로 실제 SCRAM을 확인했다. 제품 권한/timeout/계산식을 완화하지 않았다.
- 정리 집계는 의도적으로 작성한 불허 비밀번호 fixture와 실제 발급 파일을 구분하고
  private 시험 root 전체를 제거한다. 최종 **역할/schema/발급 비밀번호 파일0개**,
  PostgreSQL 종료/status exit3·cluster/관리자 비밀번호 파일 제거를 확인했다.

## 자원과 수용 한계

기존 설치 PostgreSQL **16.15**·잠긴 Python **3.12.3**/psycopg **3.3.6**/pytest **9.1.1**을
재사용했다. 단일 private loopback/SCRAM DB, 32연결/16 MB shared buffers/1 MB work memory와
순차 `nice -n 10` 시험이었다. 최종 새 20개 과정의 wall 5.136초/child 최대 RSS **152.57 MiB**다.
20 MiB 초과 제약 시험을 포함하며 제품 처리량이나 24시간 계산 메모리 수용으로 확대하지 않는다.
정확성·단순 경계·입력 보안·기존 연결·bounded 비용을 검토했고 현재 소유 서버/DB는 0개다.

시험 DB 행은 **schema 제약을 시험하는 직접 작성 행**이다. 실제 생장 계산/농장 등록과
program 권리·HMAC를 묶어 보존한 결과가 아니며 데이터/Run/G0–G4 승인도 아니다.
새 파일 모델의 DB custody·조회 API·성장 3D·전체 작기·생과 kg·자원/경제는 아직 미수용이다.
선행 원격 `d105daa`의 Backend 0/1 파트는 실행, 나머지는 대기 중이며 C0/Application/Web은
통과했다. 그 SHA에는 이번 schema 수정이 없으므로 로컬 commit을 유지하고 같은 실행의
terminal 확인 뒤 일괄 push한다.

## 다음 한 단계와 일정

다음은 같은 [v3 계약](../contracts/crop-result-v3.md)의 **custody 구획**이다.
새 store와 시험 두 파일에서 원 요청/등록 farm·crop/달력·현재 원천/program 권리를
계산 전후·저장/반환 시 대사하고, 서버 builder가 계산한 bytes에 새 HMAC domain을 적용한다.
동일/동시 재시도·충돌/rollback·권리 철회·변조/혼합 거부와 fresh store/별도 Python의
동일 bytes·재적분 없는 읽기를 실제 SCRAM으로 확인한 뒤 저장 부모 작업을 체크한다.

schema는 **10월5일 KST 로컬 완료**로 갱신한다. custody의 잠정 작업량은
계산/권리·packet 0.5–1시간, 원자성/철회·재시작/회귀 0.5–1시간, 정리/보고 0.5시간으로
**1.5–2.5 집중시간·10월5–6일 KST**(하루4시간)다. CI 대기는 별도다.
그 뒤 페이지 API → 같은 저장 ID/UTC 성장 3D를 각각 계약/수용한다.
국내 독립 자료 0건/actual forcing·Run0개와 cultivar/초기/자동 S/W1/RGR·pre-onset/
전체 작기/수확·자원/경제의 외부 의존성은 유지한다. 실제 예측/추천 날짜는 독립 자료/
검증 작기 확보 전에 정하지 않는다. 운영 기반은 `d19f7c0`으로 고정하며 자료 확보와 개발을 병행한다.
