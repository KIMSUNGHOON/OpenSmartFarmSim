# 자동 출현 실제 worker와 원자 완료 게시 — 2026-10-24

상태: [실행 계약 E2](../contracts/crop-leaf-appearance-execution-v1.md)의 **합성 소프트웨어 수용**.
[E1 접수](crop-leaf-appearance-execution-admission-20261024.md) 다음의 명시 run_once worker다.
E3 현재 조회·기존 자동 consumer 등록·보호 API/runtime/같은 job3D는 후속이다.
[사용자 저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 유지하며 새 worker는 사용자 runtime에 미배포다.

## 구현과 결과

LeafAppearanceExecutionWorker는 해당 tenant/input_version의 simulation만 claim한다.
현재 원 입력/parent·binding과 live lease/cancel을 확인한 뒤 실제 signed appearance producer를
job 잠금 밖에서 실행한다. 계획 출력 수는 현재 binding에 결속된 원 parent manifest의 samples에서 읽는다.
새 appearance manifest는 sample_count를 제공하므로 이 두 구조를 혼동하지 않는다.
원 parent bytes의 상한은 새 signed.PROGRAM_MAX를 사용한다.

원 signed 결과/binding과 현재 입력·양쪽 권리/검토·lease/cancel을 게시 전후 확인하고,
같은 DB 거래에서 publication·결과/성공 events·attempt outcome·terminal을 저장한다.
generic artifact는 원 job/input/result에 결속된 새 판본의 **371bytes opaque 참조**다.
private 파일 작성과 DB 게시는 구분하며 실패 때 private signed/참조가 남아도 완료 참조를 게시하지 않는다.
새 큐/표·역할·수치 모델이나 CLI invocation은 추가하지 않았다.
계산 중 프레임/checkpoint 재개와 자동 loop는 이번 명시 worker의 수용 범위가 아니다.

## 검증

- **신규 참조9:** 원 job/input/result 형식·scope/판본·닫힌 필드·정규 bytes/4KiB 한도와
  artifact SHA·attempt를 검사했다. 새 모듈 부재의 예상 RED9오류를 보존했고 이후9개가 통과했다.
- **실제 SCRAM 정상1:** 실제 수치 producer1회로 원 outer root
  `77c3ffcab5f02b0dab132530a3f4c278db07dd18a258633bb4b148c18f5e423a`와
  **원12frame/47면적·UTC/기관 ID**의 전체 bytes를 대사했다.
  원 parent job/result/최초 시각·계획12출력·worker code/publication/완료 참조를 확인했다.
  같은 접수와 완료 재실행의 추가 계산은0이며 다른 queued 모델을 보존했다.
  새 두 작업과 연관 행을 제외한 **25표 원 행 SHA**, 부모18파일을 보존했고 signed47파일을 확인했다.
  실제 해당 attempt의 CLI invocation은0이다. CLI 조사 결과나 승인 Run을 위조하지 않는다.
- **현재 권리 보류1:** 접수 후 계산 권리 철회 때 hold/참조·게시0과
  **53개 생장/producer/CLI 진입0**을 확인했다.
- **늦은 변경7:** 실제 private signed 계산 뒤 cancel/lease_expired,
  publication INSERT 뒤 잎 권리/부모 권리/잎 검토/부모 검토/원 program 변경을 적용했다.
  cancel은 canceled, 다섯 변경은 hold, 만료는 unclosed였으며
  **publication·성공 사건·조회 가능한 완료 참조는 모두0**이었다.
  각 경우 해당 작업을 제외한25표 원 행 SHA와 부모18파일을 보존했다.
  unclosed는 완료나 자동 재개 수용으로 표시하지 않는다.

관련 접수·farm/signed/input 및 기존 참조를 포함한 최종 **순수203(신규9 포함)+실제 SCRAM9=212개**가
고유 수용 묶음이다. 최초 예상 RED 외의 실패나 생산 코드 수정은 없었다.
native는 사용자 DB와 분리한 scratch PostgreSQL에서 순차 실행했다.
모든 native의 schema/role0·passfile/짧은 임시 디렉터리 제거와 소유 자원 정리를 확인했다.
전체 backend/새 hosted CI·E3 독립 fresh·HTTP/브라우저는 이번에 실행하지 않았다.

source는 `9f1a5a202c074d8b346dc5b0059cef1060caf03b`다.
현재 native gpt-6.1-sol/xhigh의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
최종4소스 지문·원 로그/종료 증거는 [기계 기록](artifacts/crop-leaf-appearance-execution-worker-20261024.json)에 보존했다.
원 수치/입력·서명·DB 스키마/역할·사용자 웹/키/서비스는 변경하지 않았다.

## 자원과 다음 단계

정상 native231.667초, 실제 worker 단일 관측126.995초였다.
8개 검증 단계의 최대 PID111,472,640/보호+소유 합505,982,976bytes였다.
.25초 설정·512MiB/PID·1GiB 합산/600초/4MiB 로그 안에서 보호3root·원2,504항목/현재 소스를 보존했고,
모든 단계에서 소유 잔여0·FD4→4를 확인했다. 병렬 DB 검사는 실행하지 않았다.
이는 HTTP30초/U1이나 Windows Chrome을 포함한 공통 호스트 용량/처리량 수용이 아니다.

다음 **E3**는 같은 job/input/publication/outcome/events·원 signed 결과를 대사하는
status/manifest/frame/replay 조회다. 원 result/root/calculated_at·parent/UTC/12frame/47면적을 유지하고,
현재/늦은 권리·검토/원본/게시 변경을 거부하며 조회·독립 fresh의 계산/CLI/쓰기0과 fresh의 생장/producer/worker import0을 요구한다.
새 manifest의 sample_count와 signed._frame_scope를 사용해 선택 frame과 마지막 시점의 원 기간을 확인한다.
그 뒤 기존 자동 consumer의 정확 판본/worker/outcome 등록→보호 API/runtime→같은 job3D·메뉴/reload 복원이다.

E2의 이전65–130분 예상은 위 실적으로 대체한다.
E3 구현/새 manifest·기간 경계30–60분 + 실제 DB/독립 조회·변경40–80분 + 기록10–20분 =
**80–160집중분**의 낮은 신뢰 작업량이다. 기존 조회 경계를 재사용하지만 새 구조·현재성/전송 비용은 별도 확인한다.
후속 consumer/API/UI나 외부 자료 확보 시간은 포함하지 않으며 전체 제품 날짜는 미정이다.
실제 품종/국내 독립 작기0, 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고·실제 runtime CLI G1/G0–G4와 전체 goal 미완료를 유지한다.
