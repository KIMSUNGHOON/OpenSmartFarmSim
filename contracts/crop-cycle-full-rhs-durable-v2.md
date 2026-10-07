# 전체 RHS의 지속 저장 실행 — v2 후보

2026-10-07 KST. [원 runner](crop-cycle-full-rhs-v1.md)의 수식·입력 생성·solver·출력·
writer/reader·한도와6시간 예산을 보존하는 별도 실험 감독자다.
[유실된 실험](../research/crop-cycle-full-rhs-missing-state-20261007.md)의 재개나 예산 재설정이 아니다.
기존 source와 영수증을 수정하지 않고 새 directory·판본·시작/마감·spec SHA를 발급한다.

## 지속 보존과 실행

실제 실행은 소유자의 홈 아래 지속 저장 경로/0700 directory를 사용한다. 시험의 임시 directory는
소프트웨어 검증용이다. 새 supervision manifest는 감독자/원 runner·의존성·reference/notice의
SHA와 Python·interval 수·합성 범위·관문을 고정한다. 준비 요청을 먼저 보존하고 원 입력/초기 artifact/spec을
RHS0회로 준비한 뒤 원 spec SHA·input root·deadline을 supervision에 고정한다.
호출자는 이 supervision의 원 SHA를 명시해야 한다. 각 실행은 별도 실제 Python child에서
원 CLI를 호출한다. Codex CLI를 재귀 호출하지 않는다. 원 계산 프로세스는 동시에1개다.

감독자는 배타적 flock을 자식에게도 상속한다. 현재 lock 파일의 존재를 실행 중의 증거로 쓰지 않는다.
각 시도의 실제 PID/시작 tick/boot ID와 argv, stdout/stderr, 원 결과 bytes·SHA 및
자식의 실제 종료 코드를 지속 저장한다. 로그는 매 줄 fsync하고 manifest/결과 영수증은
새 파일의 fsync와 directory fsync 뒤 변경 불가로 보존한다. 경로/원 로그는 비공개다.
감독자가 유실되면 기록 없는 종료 코드를 추정하지 않으며 실제 프로세스/lock과 원 HEAD를 재확인한다.

6시간 예산은 원 준비 시작부터다. 모든 실행/재개는 준비 단계에서 고정한 동일 spec SHA·input root·deadline을 요구한다.
부분 준비나 source/spec/결과 변조는 자동 삭제·새 준비 없이 거부한다.
자식이 비정상 종료하거나 원 결과가 없으면 해당 시도는 실패이며 전체 작기 성공이 아니다.
원 writer의 실제 HEAD/checkpoint는 재개의 유일한 계산 상태다. 로그·감독자 영수증은 이를 대신하지 않는다.
원 `incomplete`/hold와 확인된 과거를 그대로 보존한다. terminal 재조회는 새 RHS0회다.

## 다음 한 단계의 수용 기준

1. 작은 실제 계산의 첫 checkpoint 중단 → 별도 Python 재개 → 모든 원행/UTC/상태·수지/해시 대사.
2. 실제 계산 child의 SIGKILL 후 실제 음수 종료 코드·원 결과 부재를 보존하고, 동일 원 HEAD/spec/
   deadline의 새 child에서 복원한다. 연속 제어 결과의 전체 출력/사건과 일치해야 한다.
3. 동시 실행 거부, 감독자/원 source·spec 변조 거부, 기존 시도 영수증 보존과 terminal RHS0회.
   FD/자식 종료·lock 해제를 확인한다. 작은 실행을 전체166일로 세지 않는다.
4. 위 증거 뒤 새 자작166일/1,816,704걸음·47,809출력/5사건의 독립6시간 실험을 nice15로 시작한다.
   원 artifact512MiB/65,536파일/16,384commit·active RSS256MiB·원8초/300초를 유지한다.
   실제 종료·전체 원 reader 수지/행 검사 전에는 full-rhs/복원·부하 부모를 체크하지 않는다.

이 단계는 순수 수치 실험이다. 실제 farm/custody trace·DB/API/같은 ID/UTC3D는 별도 수용이며
참조 artifact를 농장 계산 이력으로 바꾸지 않는다. 실제 품종·독립 검증 자료·G0–G4와
생과/자원/경제·예측/추천 게시의 조건은 기존 명세를 따른다.
