# 등록 계산 감독 제어 — v1 개발 계약

2026-10-08 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh` 판단이며 재귀 CLI는0회다.
[선행 runtime](crop-cycle-calculation-registered-runtime-v1.md)과
[전체 실행 계약](crop-cycle-calculation-full-registered-run-v1.md)의 작은 감독 제어 자식이다.

사설0700 경로의 불변 spec은 요청 시작/마감·현재 Python·source SHA·고정 runtime config SHA·
입력 root/DB 참조·계산 묶음·표본 RSS 한도를 고정한다. 준비 검사도 같은 예산에 포함한다.
재개는 원 spec SHA와 원 deadline을 사용하며 자동 재시작하지 않는다. 두 저장 공간2GiB·
MemAvailable을 기록한다. 실제 PG가 child tree 밖에 있으면 data directory/postmaster PID와
boot/start identity를 명시해 해당 소유 tree도 RSS 합에 포함한다. 감독자는 PG 종료 권한을 받지 않는다.

감독자는 새 Python worker를 nice19로 실행하며 원 argv·PID/boot/start·로그·실제 종료를 fsync한다.
배타 flock은 child에도 상속한다. 원 종료 영수증이 없거나 이전 로그/결과·spec/source/config가
달라졌으면 새 dispatch를 거부한다. worker는 같은 DB/농장을 재구성하고 체크포인트를 RHS0 복원한다.
종료0과 결과가 있어도 원 source/config/spec·마감을 마지막으로 재검사한 뒤에만 기록 수용한다.
이 마지막 검사가 실패하면 실제 종료0/원 결과의 hash를 보존하면서 hold한다.
추가 계산은 기존 서버v3와 현재 입력/권한 검사로만 수행한다. 작은 시험의 chunk 수 제한은
원 마감을 변경하지 않는 명시적 확정 경계 중단이다. pause 요청은 다음 묶음 경계에서 멈춘다.

cancel/원 마감/표본 RSS/로그 한도 초과는 해당 소유 child group에 SIGINT를 보낸다.
10초 뒤 같은 소유 프로세스가 살아 있으면 SIGTERM, 추가10초 뒤 SIGKILL한다.
음수 종료·결과 부재·감독 중단은 완료 성공이 아니며 원 영수증과 확인된 과거만 남긴다.
실행 중인 PID는 실제 boot/start를 확인한다. 관측 유실로 새 실행이나 deadline 초기화를 하지 않는다.

수용은 실제 Python의 배타/취소/마감/RSS/변조·원 종료·정리 반례와 별도 작은 실제 SCRAM 계산의
같은 spec/deadline·전체 checkpoint/행/UTC 재개 대사다. 실제 SIGKILL 음수 종료도 보존한다.
새 계산의 genesis 생성은 RHS0이며 fault switch의 강제 종료 위치는 복원 직후·추가 RHS 전이다.
그 fault switch를 계산 중 crash 수용으로 넓히지 않는다.
제어용 가짜 Python은 프로세스 감독만 증명하며 DB·작물 수용에 세지 않는다.
순수 시험은 DB/작물 계산0, 실제 SCRAM 시험은 소유 PG 하나·원 명령600초 이내다.

전체166일·DB terminal 게시/API/3D·제품 CLI/worker lease·G1 수용은 별도다.
기존 runtime 파일과 제품 수식/저장 한도/HTTP30초를 변경하지 않는다.
실제 품종/국내 독립 자료/측정 농장 작물 Run0건·G0–G4 `not_assessed`·예측/추천 hold를 유지한다.
