# 자작 전체 작기 실제 RHS 실험 — v1 후보

상태: **[runner17개·실제5시간 저장/별도 프로세스 재개 전략 로컬 수용](../research/crop-cycle-full-rhs-small-strategy-implementation.md), 실제166일 수용 전 후보**,2026-10-06 KST.
선행 [비용 profile](../research/crop-cycle-burden-profile-implementation.md)을 로컬 수용했다.
[부하 부모](crop-cycle-burden-v1.md), [원 불변 writer](crop-cycle-artifact-v1.md)를 따른다.
제품 관문·실제 농장/자료의 착수/게시 조건은 [명세](../docs/PROJECT_SPEC.md)에 있다.
현재 실제 Codex CLI `gpt-6.1-sol / xhigh`로 설계하며 재귀 CLI0회다.

## 이번 작은 구현과 범위

core3파일은 이 계약, `research/crop-cycle-full-rhs-reference.py`,
`backend/tests/test_crop_cycle_full_rhs_reference.py`다. 기존 계산/입력/저장49파일을 수정하지 않는다.
승인된 profile의 자작 uniform 입력 generator를 재사용하고 기존 writer를 한 실행 중 유지한다.
이는 원 writer의 지원 방식이며 수식·원 격자·출력·저장/검증 정책을 바꾸는 최적화가 아니다.
chunk마다 원 결과의 canonical blob/commit·atomic HEAD를 남긴다. 재개 시 같은 input/code/profile과
현재 HEAD의 전체 prefix를 검증하며, 완료/hold의 최종 reader에서도 전체 수지·원량을 검증한다.

실제166일 성공·등록 농장 전체 저장·30초 공개 API/3D는 별도 실제 증거가 생겨야 수용한다.
본 runner의 자작 입력은 실제 Axiany forcing/초기/관리의 채택이 아니다.
새 FarmSnapshot/Run/G0 승인이나 예측·추천을 만들지 않는다. 기존 운영 기반은 유지한다.

## 입력과 예산

- 소유 합성 program의 첫 forcing 구간을 **입력** template로 사용하고 각 UTC를 명시한다.
  profile과 같은 `own-uniform-cycle-shape-cost-v1` ID, 모든300초 anchor/출력과 범위 내 원 관리 사건을 쓴다.
  이미 계산한 출력 행을 복사하는 것은0회다. solver는 원8초 RK4·roundoff 정책을 유지한다.
- 실제 reader plan을 받아 expected plan/root로 고정한다. 자작166일은47,808interval·47,809출력·
  5사건·47,811경계·1,816,704걸음·1,864,515transition 계획이다.
- 실험 manifest는 source/profile/notice/입력 root·plan, 준비 시작 UTC와 고정 deadline을 담은
  불변 canonical JSON이다. 생성에 사용한 실제 root SHA를 실행/재개 인자로 요구한다.
- global wall은 준비 시작부터6시간이며 재개로 deadline을 새로 만들지 않는다.
  테스트용 짧은 정수 budget도 명시적으로 기록한다. 원 artifact chunk10000steps/128transition,
  16,384commit·512MiB·65,536파일을 유지한다. chunk 전 active process RSS 한도는256MiB다.
  과거 allocation을 포함하는 process peak RSS도 관측하되 현재 사용량의 중단 판정으로 쓰지 않는다.
  작은 시험은 명시적 작은 chunk budget을 manifest에 기록할 수 있으며 원 solver/격자는 유지한다.
- 만료·관찰 메모리 한도·원 writer의 실제 저장 한도 거부·명시적 chunk 중단은 runner의 `incomplete`와 사유다.
  artifact는 확인된 HEAD/checkpoint와 원 상태를 유지한다. 최종 root 게시 전에는 완료 상태의
  checkpoint가 있어도 runner는 미완료다. 이를 모델 numeric hold로 바꾸지 않는다.
  deadline이 지난 재개도 같은 보류와 확인된 원 상태를 반환한다. 새 초기 조건으로 다시 시작하지 않는다.
  저장 한도 거부 뒤에는 닫힌 writer의 메모리를 사용하지 않고 현재 HEAD의 전체 검증으로
  실제 commit 상태를 복원한다. 별도의 큰 reserve로 원 저장 한도를 줄이지 않는다.

6시간은 관측된5시간 순수21.843599초와 실제 형태 plan에서 정한 **실험 budget**이다.
전체166일 완료의 상한/날짜가 아니다. 최종 읽기/정리는 별도 관찰 시간을 기록한다.
wall 만료를 확인한 뒤 새로운 RHS chunk는 실행하지 않는다. 진행 중 chunk는 원 atomic HEAD까지
마친 뒤 보류하므로 한 chunk/검증 시간이 추가될 수 있다. 프로세스 전체의 강제 중지 상한은 아니다.

## 실행·정리·기록

새 실험 directory만 만들며 불변 manifest/inputs와 original artifact를 보관한다.
재개는 artifact의 현재 HEAD hash를 읽고 실제 `open_writer`의 전체 검증을 통과한다.
다른 root/code/profile/notice·입력/결과 변조는 재계산 전 거부한다.
writer가 terminal이면 RHS를 호출하지 않고 최종 불변 reader를 연다.

runner의 관측 파일은 입력/실행 authority나 원 checkpoint를 대신하지 않는다.
actual committed steps·sequence·sample/event count·prefix/hash·최종 상태/hold·예산/사유,
실제 RHS 호출 수·wall/CPU·process peak와 FD·최대 페이지 byte·전체 원행 SHA를 기록한다.
모든 시점의 탄소/개수·요청/호흡 잔차는 원 reader 검사로 확인한다.
부분 상태에서 없는 미래 출력·생과kg·자원 구매·마진을 생성하지 않는다.
중단 시 저장 결과를 남기고 handle/FD를 닫는다. 기존 결과 directory를 자동 삭제하지 않는다.

## 수용 순서

1. 실제 작은 프로그램을 retained writer와 중단/재개로 계산한다. 원 제어 흐름과 모든 원행·
   상태/seed/clock·global counters/수지를 대사하며 terminal 읽기/retry RHS0회를 강제한다.
2. deadline 전후·원 관리 pending 경계·수치 hold·invalid budget/root/code·물리 변조·FD 정리를 검증한다.
   축소된 테스트를166일 성공으로 표시하지 않는다.
3. 원300초 모든 출력의5시간 실측으로 실행 전략·byte/file 성장과 함수 해시를 확인한다.
   기존 매 chunk 재개 측정과 원량을 대사한다. 추가 중복 full-RHS 시험은 남은 위험에 필요할 때만 한다.
4. 위 증거/검토/문서 확인 뒤 고정된 자작166일을 nice10·한 계산 프로세스로 실제 실행한다.
   모든47,809선택 출력/5사건과 원 manifest/root·최종 수지·예정/실제 걸음·시간/byte/file/FD를 기록한다.
   조기 모델/resource hold·미완료는 실제 reason/확인된 과거와 함께 보존하며 full-rhs를 체크하지 않는다.
5. 실제 중단 process 복원 및 완전 저장의 farm/current rights·DB/API/같은 UTC3D는
   `crop-cycle-burden-replay-restore`의 별도 수용이다. 반복 input/farm 검증 비용을 먼저 해결한다.

사용자 산출물은 실행 계약/작은 검증 기록·실제166일 진행/종료 receipt다.
첫 runner/집중 검증 뒤 실험을 시작하며 전체 날짜는 실제 종료 상태와 후속 조회 비용 수정 뒤 산정한다.
국내 독립 검증/실제 품종 자료 확보는 개발과 병행한다. G0–G4는 유지한다.
