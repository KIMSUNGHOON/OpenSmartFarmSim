# 소유 연구 프로세스의 pidfd 배포본 호환 — v1

2026-10-09. native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0.
선행은 Backend37892105708 분할3의 원10실패·1,073통과이며 정확한 uv Python3.12.13에서
기존10개 실패를 다시 확인했다. core3는 이 계약·`research/owned-research-process-scope.py`·
`backend/tests/test_owned_research_process_scope.py`다.

## 근거와 경계

[Python pidfd open](https://docs.python.org/3.12/library/os.html#os.pidfd_open)과
[pidfd signal](https://docs.python.org/3.12/library/signal.html#signal.pidfd_send_signal)은 Linux 전용 기능이다.
현재 Python3.12.3에는 두 함수가 있고 uv3.12.13에는 없다. 이는 이번 두 배포본의 관측이다.
설치된 glibc header와 [GNU glibc2.39 header](https://raw.githubusercontent.com/bminor/glibc/glibc-2.39/sysdeps/unix/sysv/linux/sys/pidfd.h)의
두 wrapper 선언, 실제 libc 심벌과 자기 pidfd/signal0 시험을 확인했다.
[Linux open](https://man7.org/linux/man-pages/man2/pidfd_open.2.html)/
[signal](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html)의 fd/errno/NULL info 의미를 따른다.
해당 man-page의 wrapper 부재 문구는 현재 header/심벌과 다르므로 libc 가용성은 실제 심벌로 확인한다.
외부 구현 코드는 복사하지 않는다. ctypes는 기존 Python 표준 라이브러리다.

두 Python 함수가 callable이면 기존 경로를 우선한다. 둘 중 하나가 없으면 지연 로드한
`CDLL(None, use_errno=True)`의 두 libc 심벌을 사용한다. C 인수/반환형을 명시하고
open flags0·send NULL info/flags0, 음수 반환의 errno→OSError 하위 형식과 fd close를 유지한다.
심벌/라이브러리 부재는 구성 실패이고 커널 거부·ENOSYS·권한 오류는 호출 실패다.
실패 뒤 다른 신호 방식이나 숫자 PID로 재시도하지 않는다. 임의 syscall 번호도 도입하지 않는다.

PID/start_ticks/boot_id, 보호 tree/재부모화 추적, 신호 직전 identity 재검사, TERM/KILL만의
정리와 finally fd close는 보존한다. 함수 호출 두 곳 외의 소유/보호 알고리즘은 바꾸지 않는다.
현재 실행 중인 전체 수확/미리보기는 기존 고정 source와 helper를 계속 사용한다.

## 수용

1. 정확한 uv3.12.13의 원 RED10개를 보존하고, 같은 배포본과 기존3.12.3에서 전체 해당 시험을 통과한다.
2. 실제 일반/스레드 child·고아/보호 descendant/parent 종료, stale identity·열린 fd 뒤 identity 변경,
   신호 거부/실패·모든 fd close와 보호 tree 생존을 확인한다. 강제 libc 실제 pidfd/signal0·CLOEXEC도 확인한다.
3. Python 우선·심벌 하나/둘 부재, libc 심벌/로드 부재·errno/NULL/flags·import 무부작용과
   숫자 PID fallback0을 시험한다. 원 종료/소유 자식 정리·512MiB/1GiB·원 source/전체 writer/미리보기를 대사한다.

로컬 호환 수용은 같은 수정판의 hosted 분할3/전체 CI를 대신하지 않는다.
전체 수확/실시간 U3·품종·자료/관문 수용과 별도로 기록한다.
