# 2026-10-09 연구 시험의 프로세스 정리 오류와 수정

## 실제 중단과 복구 범위

저장 결과 선택→기존 3D 연결의 시험 실행기 원33788은 타입 검사 뒤 첫 브라우저 시험에서
동시 RSS1,078,620,160bytes로1GiB를 초과해 종료1이었다. 그 뒤 실행기 정리 코드가
RSS 관측 목록의 보호 프로세스 자식을 소유 대상으로 잘못 추가해 TERM을 보냈다.
이는 에이전트가 작성한 실행기의 오류다. 원 실행기와 실패 로그는 보존했다.

전체166일 원95086은 pytest -15/실행기1로 중단됐고 미리보기 원82604도 종료1이었다.
원 전체는 **완료/수용되지 않았다**. 마지막 확정은303commit/1,209,263걸음이었다.
09:12 시작 이후 진행 중이라는 이전 관측은 그 당시 기록이며 현재 실행 상태를 뜻하지 않는다.

원 입력/config/인증 자료와 PostgreSQL data를 보존하고 재시작 전 오프라인 사본1,103파일을 남겼다.
원 고정 producer의 읽기 전용 복원은 종료0/RHS0·delta QC0/FD4→4로 같은 체크포인트를 확인했다.
별도 복구 감독 원95915는 같은 artifact/수식/입력/격자로 재개했다. 원9시간 상한
**2026-10-09 18:12:12 KST**를 연장하지 않았다. 13:35 무렵 실제 같은 복구 프로세스의
확정 HEAD는313commit/1,249,173걸음(전체1,816,704걸음)이었다. 계산 종료/게시/수용은 아니다.
고정 producer의3개 원 파일과 분리된 source checkout은 변경하지 않았다.

미리보기는 원83196의 새 run-v5로 복구했다. 기존 토큰/저장 ID와 만료 조건을 유지한다.
`http://localhost:5173/`은200이며, 실제 인증 HTTPS 생장 summary도200/원 run-v4 응답과
전체 JSON이 같다. 여전히 별도 DB의 작은 합성3시점이며 전체 계산의 실시간 연동은 없다.
실제 품종/농장 작물 Run·국내 독립 자료0건과 기존 관문 보류는 유지한다.

## 직접 원인 수정의 로컬 수용

[3파일 계약](../contracts/owned-research-process-scope-v1.md)에 따라 RSS 관측과 신호 권한을 분리했다.
실행기 자식으로 확인된 identity만 소유로 기록하고 보호 root/전체 자식은 제외한다.
보호 root에서 소유 탐색을 중단하므로 보호 쪽 children 관측이 일부 빠져도 그 가지를 소유하지 않는다.
기록한 보호 자식은 부모 종료/재귀속 후에도 보호하며 PID/start ticks/boot ID를 유지한다.

신호는 [Python pidfd](https://docs.python.org/3.12/library/os.html#os.pidfd_open)를 열고
identity를 재확인한 뒤 [pidfd_send_signal](https://docs.python.org/3.12/library/signal.html#signal.pidfd_send_signal)로만 보낸다.
모든 thread의 children을 읽으며 경합 시 확인하지 못한 프로세스를 종료 권한에 추가하지 않는다.
[Linux children의 관측 한계](https://man7.org/linux/man-pages/man5/proc_tid_children.5.html)도 유지한다.

- 집중10개: 원 c66e47 종료0, pytest0.45초/전체0.716초. 실제 격리 Python 자식/손자,
  thread의 자식·보호 부모 종료·소유 부모 종료 뒤 정리, 불완전 보호 탐색,
  관측 dict 변경, pidfd 전후 identity 변경/신호 거부/FD 닫기와 느슨한 fallback 거부를 확인했다.
- 집중 실행 동시 RSS 합548,319,232bytes/단일128,204,800bytes, 표본12개.
  복구 계산/PG·미리보기/PG의 원4 identity 유지, 새 소유 비좀비0이다.
- 새 불변 실행기 run-v3에 helper를 연결해 작은 합성 자식/손자의 실제 RSS 상한 중단을 실행했다.
  원50b664 종료0/0.219초, 자식 -15는 의도된 중단이다. 측정 소유 RSS24,981,504bytes가
  명시8,388,608bytes를 초과했고 종료 후 소유 비좀비/직접 자식0이었다.
  동시 RSS 합497,586,176bytes/단일128,204,800bytes·원4 identity/1,545 source/배포 dist를 보존했다.
- 선행 run-v2는 준비 신호를 이용한 정리 진단이었다. 그 결과를 RSS 상한 시험으로 사용하지 않는다.
- 실제 native CLI `gpt-6.1-sol`/`xhigh` turn context와 출력/원 명령/로그 hash를 보존했다.
  현재 CLI에서 재귀 CLI 실행0이다. [기계 판독 기록](artifacts/resource-ownership-fix-reference-20261009.json)을 따른다.

## 남은 의존성과 다음 순서

1. 복구 계산 원 종료와 원 전체 행/121상태 대사. 원 실패를 정상 종료로 바꾸지 않는다.
2. 원 계산 전 선언한 게시 plan/key의 계보를 보존하는 **명시 복구 게시 계약/검증**.
   원 선언의 감독 PG identity가 종료됐으므로 원 publisher 경로를 그대로 재호출할 수 없다.
   새 계산 뒤 임의 선언, 원 manifest 변경, source guard 완화나 빈 artifact 위장은 허용하지 않는다.
   현재 복구 단계에는 게시가 없으며 이 의존성은 미완료다.
3. 정상 게시/인증 backup→원 DB 정리→fresh 현재 query 복원과 원 종료/자원 감사.
   그 뒤 전체 수확 writer/registry→실제 API/대표3D→기후/자원/Decimal 경제다.
4. U1 전달 자식은 타입 검사0만 확인했고 브라우저/현재 전체 웹/빌드는 미검증이다.
   새 프로세스 helper 수용을 UI 수용으로 대신하지 않는다. 브라우저 재실행은 실제 동시 자원
   여유가 입증된 뒤 진행한다. U1 선택 화면·U3 진행 상태·계산 중3D는 미완료다.

종전 전체 종료 예상은 이번 중단 전의 조건부 관측으로 남긴다. 복구 후 계산 종료 시각과
복구 게시 검증의 실제 작업량이 없으므로 전체 부모/통합 UI의 새 완료 날짜는 확정하지 않는다.
