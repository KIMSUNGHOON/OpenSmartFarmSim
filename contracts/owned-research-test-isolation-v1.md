# 같은 pytest 실행기의 선행 자식과 소유 프로세스 시험 — v1

2026-10-09, native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
Backend37918274666/921d0e7 분할1의 strict sent-set2실패를 다룬다.
core3은 이 계약, `backend/tests/test_owned_research_process_scope.py`,
`research/owned-research-shared-controller.py`다. 제품 helper/계산·미리보기 source는 변경하지 않는다.

1. 실제 spawn-context semaphore의 resource tracker가 있는 같은 Python에서 기존 pytest 검사를 실행한다.
   원 tracker boot/PID/start·argv와 SIGTERM 무시 상태를 확인하고, 원 두 실패의 extra identity가
   이 알려진 선행 자식과 같은지 대조한다. 과거 hosted PID의 종류는 원 로그만으로 단정하지 않는다.
2. 시험 fixture는 시험 가족을 만들기 전에 같은 실행기의 기존 자식 identity를 한 번 기록한다.
   그 원 identity를 명시 protected에 추가하는 scope factory를 제공한다. 이후 만든 시험 가족을
   baseline에 추가하지 않는다. 명시 보호 가족은 기존과 같이 별도로 검사한다.
3. 기존 strict sent-set/실제 pidfd·thread/고아·identity/오류/FD 검사를 유지한다.
   선행 일반/thread 가족을 별도로 만든 회귀에서도 그 가족을 보존하고 새 소유 가족만 종료해야 한다.
   제품 ownership 범위를 줄이거나 sent-set의 허용 범위를 넓히지 않는다.
4. 선행 tracker가 없는 일반 검사와 있는 같은-controller 검사, 기존 두 Python 배포본을 각각 확인한다.
   원 도구 종료·tracker identity 생존/정상 소유 정리·잔여 비좀비0·FD/입력/source·현재 미리보기,
   0.25초512MiB/1GiB 관측과 로그를 기록한다. 단순 수집이나 원0의 재현을 성공으로 표시하지 않는다.
5. 로컬 수용과 새 exact-commit hosted 회귀를 구분한다. 이 수정으로 U1/U3·작물 예측/관문을 체크하지 않는다.
