# 전체 작기 실험의 지속 저장·실제 프로세스 복원

2026-10-07 KST. [v2 감독자 계약](../contracts/crop-cycle-full-rhs-durable-v2.md)의 작은 실제
실행 범위를 로컬 수용했다. [고정 증거](artifacts/crop-cycle-full-rhs-durable-reference-20261007.json)에
3 core source와 로그 SHA, Codex CLI `gpt-6.1-sol / xhigh` 문맥·실제 종료/원행 해시를 보존한다.
재귀 Codex CLI는 실행하지 않았다. 원166일의 유실된 종료 상태는 계속 확인 불가다.

## 구현

[감독자](crop-cycle-full-rhs-durable.py)는 원 runner를 별도 Python child로 실행하고 실제
종료 코드·PID/시작 tick/boot ID·argv·로그와 원 결과 SHA를 지속 저장한다.
flock을 child에도 상속해 동시에 계산하는 원 worker를1개로 제한한다.
원 spec과 실제 HEAD/checkpoint를 재개하며 로그나 감독자 영수증으로 계산 상태를 만들지 않는다.

준비 요청을 먼저 fsync하고 원 입력/초기 artifact/spec을 RHS0회로 만든다.
원 spec SHA·input root·6시간 deadline을 감독자의 변경 불가 manifest에 고정하고
호출자가 원 manifest SHA를 명시하게 했다. 재개할 때 새 budget을 만들지 않는다.
manifest/영수증은 file·directory fsync/0400, 로그는 매 줄 fsync 후 종료 시0400이다.
실제 장시간 실험은 임시 경로 대신 홈 아래 비공개0700 경로를 사용한다.

## 실제 검증과 수정

- 최종 집중 **5개/22.67초**, 실제 종료0. 이전2개/2.69초는 합산하지 않는다.
- 실제 계산 child를123걸음 checkpoint 뒤 **SIGKILL**했다. 감독자가 실제 **-9** 종료 코드와
  원 결과 부재를 기록했다. 새 child는 저장된 checkpoint 전체와 동일하게 재개했다.
- 재개 결과 **760걸음·21시점/2사건**, 원 모든 시점/사건 SHA와 최종121상태 성분이
  같은 입력의 연속 제어 계산과 일치했다. 재개 RHS3,202회/6.595366초,
  연속 제어 RHS3,822회/7.868277초다. 조회 RHS는0회다.
- 별도 작은 중단/재개는123→152걸음·5시점/2사건이며 checkpoint 전체가 같았다.
  terminal의 추가 별도 child 조회는 RHS0·읽기 RHS0이다.
- 모든 대상 child PID 부재·lock 재획득과 worker FD5→5를 확인했다.
  감독자의 lock FD를 상속하므로 기존 별도 worker의 FD4와 절대 개수는 다르다.
- 최초 미구현1오류/0.09초 후, **원 spec의 시작/마감을 함께 바꾼 재개**가 받아들여지는
  실제1실패/2.30초를 재현했다. 원 spec SHA를 준비 시 감독자 manifest에 고정해 수정했다.
  **과거 결과 변조를 무시한 재개**도 실제1실패/2.37초로 재현해, 이전 영수증의 원 결과 SHA를
  재대사하도록 수정했다. 새 코드에서 두 거부와 동시 실행 거부를 확인했다.

## 보존 범위와 다음 실제 실행

원 수학52개·원 runner/profile·기존 store/farm/custody와 선행 조회 source를 보존했다.
기존53개 중 이미 수용한 CI 시험 격리 수정1개만 원 baseline과 다르다.
전체 backend·브라우저, 실제 재부팅·감독자 자체의 SIGKILL은 이번 단계에서 시험하지 않았다.
배타 lock 파일의 존재나 PID 기록만으로 실행 중·정상 종료를 주장하지 않는다.

선행 `86290c3`의 [hosted CI5개](artifacts/crop-cycle-full-rhs-test-isolation-ci-20261007.json)는
백엔드6분할/집계까지 모두 성공으로 종료했다. 이 SHA에는 로컬 조회3커밋과 새 감독자가 없다.
해당 CI 종료를 확인한 뒤 새 변경을 정상 push해 별도로 검증한다. 실행 취소/재시작이나 CI 설정 변경은 없다.

다음은 새 directory·판본·원 spec SHA·독립6시간 deadline을 가진 자작166일 실험이다.
원8초 RK4·300초 출력·1,816,704걸음·47,809출력/5사건·원 저장/RSS 한도를 보존한다.
nice15의 단일 계산 child에서 첫 checkpoint 뒤 실제 종료/같은 spec 재개를 기록하고,
전체 RHS 종료 및 원 reader의 모든 행/수지 검증을 관찰한다. 실행 시작과 전체 완료는 구분한다.
고정6시간은 실험 예산이며 전체 처리/제품 완료 날짜의 상한이 아니다.

`crop-cycle-full-rhs-durable`의 작은 감독자만 수용한다. `crop-cycle-burden-full-rhs`,
전체 복원/부하와 실제 farm/DB/API/같은 ID·UTC3D는 별도 증거를 기다린다.
참조 artifact를 원 농장 실행 이력으로 바꾸지 않는다. 실제 품종·독립 국내 농장 자료·실제 작물 Run0,
G0–G4 `not_assessed`와 생산 예측·미래 마진·추천 게시 보류는 유지한다.
