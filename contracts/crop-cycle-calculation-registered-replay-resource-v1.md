# 같은 등록 계산·3D 경로의 자원 수용

2026-10-08 KST. [기능 경로](crop-cycle-calculation-registered-replay-harness-v1.md)의 후속이다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는 실행하지 않는다.

기존 관측의 descendant RSS 합1,583,595,520bytes는 전체1GiB 예산 초과이며
PostgreSQL이 descendant에서 벗어난 구간은 포함하지 않았다. 이를 자원 수용으로 표시하지 않는다.
같은 작은120걸음/3시점/3사건과 원 계산·게시·권리 검증을 유지한다.

새 원 명령은 준비부터600초, primary512MiB·소유 pipeline RSS 합1GiB를 감시한다.
현재 primary의 descendant와 소유 임시 directory의 PID/start/boot로 확인한 PostgreSQL tree,
감시 controller를 중복 PID 없이 포함한다. 표본 간격0.1초·동시 최대 snapshot과 프로세스별 최대를
보존한다. shared page 중복이 가능한 RSS 합이며 PSS/WSL 전체·미관측 순간 최대가 아니다.
한도 초과는 원 primary에 SIGINT,10초 뒤 SIGTERM,추가10초 뒤 SIGKILL을 순서대로 적용한다.
실제 종료·남은 소유 process/PG·schema/role/passfile·temp·source를 확인한 뒤 다음 변경을 한다.

변경 전 기준선을 먼저 측정한다. 화면 캡처 범위와 production build 서빙은 각각 독립 변경으로
검증하며 실제 병목/예산에 도움이 없는 변경은 남기지 않는다. production build를 사용할 때는
기존 잠금 도구·현재 App과 TLS/CA proxy를 유지하고 build bytes를 원 명령에 고정한다.
Vite preview만으로 예산이 충족되지 않으면 기존 배포 명세의 Nginx1.30.5·현재 TLS/CA proxy
설정을 소유 native 검증에 사용한다. 소스 서명·바이너리/의존성 hash·실제 준비 종료를 보존하고
시스템 설치/서비스 등록은 하지 않는다. native 검증을 기존 container/G4 수용으로 바꾸지 않는다.

수용에는 같은 DB·보호 HTTPS·원 UTC/50개 C/N/LAI/사건·실제 WebGL·GET RHS0·권리 철회/복원·
계정 거부·실제 원 종료0·원600초/512MiB/1GiB·source/비밀/DB/PG/브라우저 정리가 모두 필요하다.
예산 거부 실행이나 대표 화면을 전체166일 완료/G1·G0–G4 수용으로 재분류하지 않는다.
수용 뒤 원9시간 전체 등록 작기→전체 원량 streaming 비교→게시/API/대표3D를 진행한다.
