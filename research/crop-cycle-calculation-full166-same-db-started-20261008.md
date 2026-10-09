# 전체166일 등록 실행 시작 — 2026-10-08

[작은 실행 구성 수용](crop-cycle-calculation-full166-same-db-preparation-implementation-20261008.md)을
커밋 `2e03d27`로 보존한 뒤 별도 실제 전체 실행을 시작했다.
[원 시작/실제 살아 있는 계산 worker 관측](artifacts/crop-cycle-calculation-full166-same-db-start-reference-20261008.json)을 남겼다.

- 원 준비 시작: **2026-10-08 11:41:29 KST**.
- 준비·계산·전체 대사·게시·API/대표3D·정리를 포함한 원 마감: **같은 날20:41:29 KST**.
  9시간은 고정 실험 상한이다. 완료 시각의 추정이나 보장이 아니다.
- 목표: 원8초 RK4/300초 출력의 **1,816,704걸음·47,809시점·5사건·121상태**.
- 실제 fresh Python 계산 worker의 PID/start/boot·nice19·원 계획/입력 root와 실제 진행 기록을 확인했다.
- primary512MiB/pipeline1GiB·소유 PG/controller 포함 동시 RSS·두 공간2GiB·원 마감을 유지한다.
- source398개를 고정했다. 계산 동안 두 번째 무거운 pipeline을 시작하거나 고정 source를 수정하지 않는다.
- 관측 만료는 재시작 사유가 아니다. 같은 원 handle/PID/로그를 확인한다.

이 기록은 **시작 관측**이다. 실제 terminal·원 전체 행/상태/수지 대사·현재 권리·원 종료·
DB/비밀/PG/브라우저/임시 정리 전에는 전체 DB/API/3D 수용으로 표시하지 않는다.
전체 새 계산 결과의 artifact는 소유 사설 지속 경로에 남기며 원 참조를 덮어쓰지 않는다.
다음은 이 원 실행의 관측·검증이다. 생과/자원/경제·실제 CLI/독립 G1은 후속이다.
실제 품종 입력/국내 독립 검증 자료/실측 농장 작물 Run0, G0–G4 `not_assessed`, 예측·추천 hold는 유지한다.
