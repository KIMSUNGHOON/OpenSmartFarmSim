# 소유 연구 시험의 프로세스 정리 범위 v1

2026-10-09 저장 결과 재생 시험에서 관측용 RSS 목록을 종료 권한으로 사용해
별도 전체 계산과 미리보기의 자식을 종료했다. 이 수정은 그 사고의 직접 원인을 다룬다.
핵심3파일은 이 계약, `research/owned-research-process-scope.py`,
`backend/tests/test_owned_research_process_scope.py`다. 제품 작업자나 수식은 변경하지 않는다.

## 다음 한 단계의 수용

- RSS 관측은 시험 실행기와 명시된 보호 프로세스들의 전체 자식을 포함할 수 있다.
  종료 권한은 실행기 자신의 자식으로 확인한 프로세스에만 부여한다.
  보호 root뿐 아니라 확인한 전체 자식의 identity를 정리 대상에서 제외한다.
- identity는 boot ID/PID/start ticks다. 보호 identity를 다시 읽은 PID로 대체하지 않는다.
  이미 확인한 보호 자식은 부모 종료/재귀속 뒤에도 제외한다. 관측되지 않은 고아는 종료하지 않는다.
- 모든 thread의 children을 읽고 부모 identity를 재확인한다. 관측한 RSS dict는 종료 대상의 입력이 아니다.
  보호와 소유 범위의 충돌, 실행기 자체, 불확실한 identity는 신호 전송을 거부한다.
- Linux pidfd를 열고 identity를 다시 검사한 뒤 그 fd에만 TERM/KILL을 보낸다.
  PID/프로세스 그룹에 대한 포괄 신호나 pidfd 미지원 시의 느슨한 대체는 없다.
- 격리된 실제 Python 부모/자식/손자의 시험에서 소유 자식만 종료되고 보호 자식은 유지되어야 한다.
  thread가 만든 자식, 보호 부모 종료 뒤 자식, PID identity 변경, pidfd 종료/실패를 확인한다.
  자원 상한 중단과 정상 자식 종료 뒤 정리 두 경로에서 실제 잔여 소유 프로세스0을 확인한다.
- 기존 실패 실행기/로그는 보존하고 새 판본 실행기에 이 helper를 연결한다.
  새 실행기는 낮은 RSS 상한으로 조기 중단하는 합성 자식 시험을 먼저 통과해야 한다.
  실제 보호 계산/미리보기의 PID 시작 identity와 입력/source/배포 파일을 전후 대사한다.

helper 시험 통과만으로 UI·전체 계산·새 실행기 수용을 완료하지 않는다. 원 전체 실행의
실패와 체크포인트 복구는 각각 기록하며 게시/백업/복원/원 종료 감사는 별도 관문이다.

## 확인한 실행 API

[Python os.pidfd_open](https://docs.python.org/3.12/library/os.html#os.pidfd_open),
[Python signal.pidfd_send_signal](https://docs.python.org/3.12/library/signal.html#signal.pidfd_send_signal),
[Linux thread 디렉터리](https://man7.org/linux/man-pages/man5/proc_pid_task.5.html),
[Linux thread children](https://man7.org/linux/man-pages/man5/proc_tid_children.5.html).
`children` 관측은 동시 종료와 경합할 수 있으므로 현재 확인한 identity만 권한으로 사용한다.
