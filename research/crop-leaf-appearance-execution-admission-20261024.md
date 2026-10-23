# 자동 출현 작업의 접수·멱등성과 commit 검증 — 2026-10-24

상태: [실행 계약 E1](../contracts/crop-leaf-appearance-execution-v1.md)의 **합성 소프트웨어 수용**.
[서버 계산/현재 조회](crop-leaf-appearance-signed-artifact-20261024.md) 다음의 접수 단계다.
새 worker/원자 완료 게시·현재 query·자동 loop/API/같은 job3D는 후속이다.
[사용자 저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 유지하며 이 모듈은 사용자 runtime에 미배포다.

## 구현

LeafAppearanceExecutionService는 정확한 appearance authority와 판본 고정 trusted resolver를 받는다.
현재 farm/완료 parent·원 program/source/evidence와 검토/권리를 대사하고,
원 binding을 별도 private store에 보관한 뒤 기존 simulation jobs에 참조만 접수한다.
2,519bytes input은 원 request/binding SHA/resolver 판본·authority/code·새 domain의 intent HMAC이다.
program/source/evidence bytes나 키를 job input에 넣지 않는다. binding은29,174bytes였다.

동일 study/revision의 같은 요청은 같은 queued job을 반환하고 변경된 원 요청은 충돌이다.
JobStore의 기존 commit_guard가 커밋 직전 원 bytes/현재 binding·검토/권한/판본을 재검사한다.
실패하면 job/event 삽입을 롤백한다. 남은 private binding 객체는 게시 결과가 아니다.
current_input은 simulation_create 없이 현재 read scope로 읽을 수 있으며 write=True는 계산 권리도 요구한다.
접수에서 생장/producer·CLI를 실행하지 않고 새 큐/표/역할·수치 모델을 추가하지 않았다.

## 통과한 검사와 계측 수정

- **신규 순수13:** 원 요청/parent·binding/판본·admission code와 signed authority code,
  issuer/key ID/resolver·HMAC·다른 키/계열·닫힌 필드/정규 bytes·64KiB 한도를 검사했다.
- **실제 SCRAM 정상1:** 같은 요청 두 번은 queued job1/submitted event1이며 attempt/publication 추가0이었다.
  같은 원 binding/3개 bytes·parent와 create scope 없는 현재 read를 대사했다.
  변경 요청은 충돌, 검토 철회 후 재접수는 이전 job 반환 없이 보류했다.
  새 job/event를 제외한25표 모든 원 행 SHA·parent18파일을 보존했다.
- **실제 SCRAM 변경 거부1:** foreign tenant·양쪽 현재 권리/검토와 세 입력 bytes 변경을 거부했다.
  INSERT 뒤 commit_guard에 create scope/leaf 검토/parent 검토/leaf 권리/parent 권리/원 program을 바꾼
  **6경우**가 모두 rollback되어25표 원 행 SHA/건수는 같았다.
  부모18파일을 보존했고 private binding1파일은 미게시 상태로 남았다.

모든 current_input 호출은 작업/객체 쓰기7진입과 지속 SQL을 차단·계측해0회를 확인했다.
접수 자체의 정상 job/event 쓰기는 허용하며 이 읽기 구간과 구분한다.
두 native 시험 모두 생장/producer/CLI 진입0·소유 schema/role0·passfile/짧은 임시 PG 디렉터리 정리를 확인했다.
사용자 DB가 아닌 소유 scratch PostgreSQL을 사용했다.

모듈 부재 RED 뒤 기본12검사가 통과했고 signed authority code 변조 반례를 더했다.
첫 native는 제가 추가한 계측의 복원 순서 때문에1실패/1통과/2teardown 오류로 미수용이었다.
클래스 차단 메서드를 인스턴스에 복원해 다음 submit/event를 막은 문제였다.
기존 인스턴스 override만 클래스보다 먼저 교체하도록 수정해 같은 생산 코드의 최종 native2를 통과했다.
실패 때도 DB/역할·임시 프로세스 정리와 원3root/파일 보존을 확인했다. 실패 시도를 통과 수에 합산하지 않는다.

기존 접수/새 farm/signed/input 회귀를 포함한 **순수185(신규13 포함)+실제 DB2=187개**가 최종 고유 수용 묶음이다.
별도 fresh admission·전체 backend/새 hosted CI·HTTP/브라우저는 이번에 실행하지 않았다.
이전 수치/서명·원 입력·DB 스키마/역할·웹/서비스는 변경하지 않았다.

source는 `e318f1ae37c5124f8436333b43f3d621775b7712`다.
현재 native gpt-6.1-sol/xhigh의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
최종 코드/시험 지문·초기 실패와 원 증거는 [기계 기록](artifacts/crop-leaf-appearance-execution-admission-20261024.json)에 보존했다.
source/review/farm은 자체 소프트웨어 fixture이며 실제 제품 CLI나 농장/품종 검증으로 세지 않는다.

## 자원과 다음 수용

최종 native2는239.27초(guard240.372초)/912표본·PID102,731,776/합산491,339,776bytes였다.
.25초 설정·512MiB/PID·1GiB/600초/4MiB 로그 안에서 보호3root·원2,504항목/현재 소스·잔여0·FD4→4를 보존했다.
단일 submit/같은 retry/current read의25.394/25.138/12.695초는 내부 관측이며 HTTP30초/U1 수용은 아니다.

다음 E2는 해당 tenant/input_version만 claim해 실제 signed producer1회를 잠금 밖에서 수행하고,
현재 입력·lease/cancel을 전후 확인해 같은 거래에서 opaque 참조/publication/outcome/events·terminal을 게시하는 worker다.
원 result/root/parent/최초 시각·12시점/47면적과 완료 재실행의 계산0, 다른 queued 모델 보존,
취소/만료/늦은 권리·검토 변경 때 참조 게시0·행/파일/3root/WSL/소유 정리가 수용 기준이다.
원 parent의 samples에서 계획 출력 수를 읽고 새 signed.PROGRAM_MAX를 사용한다. 생장 진행률을 임의 생성하지 않는다.
이후 E3 현재 조회→기존 자동 loop/보호 API→같은 job3D다.

E2의 구현/참조20–40분 + 실제 DB 정상·취소/임대·늦은 변경35–70분 + 검토/기록10–20분 =
**65–130집중분**을 낮은 신뢰로 추정한다. 이번 E1 예상은 실제 수용 기록으로 대체한다.
실제 품종/국내 독립 작기0, 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고·G0–G4와 전체 완료 날짜 미정을 유지하며 goal active다.
