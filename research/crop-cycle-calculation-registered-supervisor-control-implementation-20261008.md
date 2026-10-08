# 등록 계산의 지속 감독 제어 수용

2026-10-08 KST. [작은 감독 제어 계약](../contracts/crop-cycle-calculation-registered-supervisor-control-v1.md)을
**고유16개·원 명령 종료0·별도 최종 감사/정리로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-registered-supervisor-control-reference-20261008.json)의 SHA는
`2477ca848d1e5ec1b08a23451237eb4cd3afc6e4f834d575899b554e67285204`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는0회다.

## 구현과 범위

연구 harness는 원 요청 시작/마감·고정 runtime config·입력/DB 참조·Python/source SHA·묶음/RSS 한도를
사설 불변 spec에 기록한다. 준비 검사도 원 시간 예산에 포함하며 같은 boot에서는 monotonic 시간도 검사한다.
두 공간의 저장 여유2GiB·MemAvailable을 기록한다. nice19 자식과 상속 flock·현재 boot/start를 사용하고
이전 원 종료/로그/결과가 없거나 바뀌었으면 새 dispatch를 거부한다. 명시 재개가 원 마감을 바꾸지 않는다.
최종 spec/config/source/마감 검사 실패는 종료0과 결과가 있어도 hold하며 원 종료와 결과 hash를 보존한다.

worker는 기존 등록 runtime을 재구성하고 새 genesis 또는 기존 checkpoint를 RHS0으로 읽는다.
추가 계산은 기존 서버v3의 현재 입력/농장/권리·전체 bytes/HMAC 검사와 원 수식/격자로만 수행한다.
pause는 확정 묶음 경계에서 확인한다. cancel/벽시계/RSS/로그 초과는 소유 group에 INT→10초→TERM→10초→KILL을
보내며 실제 신호·원 종료를 기록한다. 시험용 PG가 child tree 밖에 있어도 data directory/PID/boot/start로
소유를 확인해 해당 tree를 RSS 합에 포함한다. PG 정리는 외부 소유 시험 fixture가 맡는다.
이는 제품 CLI/worker lease·일반 계정/원천 서비스의 구현이 아니다.

## 실제 SCRAM 계산과 제어

15개는 실제 Python 자식으로 감독을 시험한 DB/작물 계산0의 제어용 사례다.
나머지1개는 실제 PostgreSQL 16.15/SCRAM·같은 농장/입력의 등록 계산이다.

| 실제 계산 | 첫 fresh Python | 두 번째 fresh Python | SIGKILL 뒤 fresh Python |
| --- | ---: | ---: | ---: |
| 걸음 / 전체 계획 | 40 / 120 | 60 / 120 | 80 / 120 |
| 확정 묶음 | 2 | 3 | 4 |
| 확정 출력 / 사건 | 1 / 0 | 1 / 0 | 2 / 0 |
| 실제 새 RHS 호출 | 201 | 100 | 101 |
| 복원 RHS | 0 | 0 | 0 |

첫 worker가 실제 두 묶음을 처리했다. 다음 worker의 복원 checkpoint 전체는 직전 확정값과 같았다.
복원 직후·추가 계산 전 SIGSTOP한 세 번째 worker를 SIGKILL해 실제-9·선택 이력 보존을 기록했고,
다음 worker가 같은 spec/deadline으로 이어 계산했다. 같은 예산의 연속 제어 artifact와 전체 checkpoint·행·UTC가 정확히 같다.
계산 도중 crash나 관리 사건 사례의 수용으로 넓히지 않는다.

다섯 번째 native worker는 현재 경계의 실제 pause 요청 뒤 추가 RHS0/종료0·같은 checkpoint였다.
여섯 번째는 복원 직후 정지 상태에서 실제 cancel을 받아 INT/TERM/KILL 순서와 최종-9를 기록했다.
그 worker의 FD11에서 실제 동일 lock inode와 FLOCK을 별도 읽기 관측으로 확인했다.
현재 입력 허용·계정 read scope 철회를 각각 별도 worker에서 거부했다.
총8개의 원 종료는 `[0,0,-9,0,0,-9,1,1]`이고 원 명령/worker/로그/결과/제어/spec39파일을 사설 보존했다.
모든 계산 결과는 yielded·artifact SHA null이다. 미완료 DB 게시를 거부했고 DB 수는 `[89,89,0,0,0]`으로 같았다.

## 검증·수정·정리

최종16개는162.88초·원 명령/정리163.495초, primary 표본 RSS129,093,632bytes·
동시 descendant RSS 합228,352,000bytes다. shared page 중복 가능 표본이며 WSL 전체/PSS·production 성능 수용이 아니다.
FD13→13·현재 입력/선택 이력 보존·선행284개를 포함한289 source 보존을 확인했다.
별도 최종 감사는 child/primary/controller/PG 실제 종료, 임시/비밀 경로 제거·schema/role/passfile0·네 host SCRAM을 대사했다.
그 감사 뒤 source freeze를 해제했다. 전체 Backend/API/웹 시험은 이번에 반복하지 않았다.

최초 모듈 부재 RED 뒤 초기 제어12개를 통과했다. 로그 한도 초과 때 bounded reader가 원 종료 영수증 저장까지
막는 실패를 추가 RED로 확인하고 metadata/소유 검사를 유지하는 streaming hash로 수정했다.
첫 native v1은14개를 통과했다. 원 설정 변경/마감 경과 직후 결과를 기록 수용하는 두 반례를 다시 RED로 확인하고
최종 검사를 추가했다. 실제 native pause/cancel도 보완한 v2가 위16개를 통과했다.
v1은 완전히 종료·정리/감사한 뒤 수정했고 source snapshot·로그를 보존했다.
과거12개/14개·실패 시험을 최종 고유16개에 더하지 않으며 관측 만료 재시작은0회다.

## 다음 단계와 hold

선행 [별도 Python runtime](crop-cycle-calculation-registered-runtime-implementation-20261008.md)과 이 제어 증거로
작은 등록 감독자 부모를 로컬 수용한다. 전체 실행은 아직 시작하지 않았다.
다음은 고정166일 입력을 사용하는 새 사설 준비/spec·동일 등록 농장/DB·별도 DB 게시 key를 묶고,
[원9시간 예산](../contracts/crop-cycle-calculation-full-registered-run-v1.md) 안에서 실제 terminal 계산/DB 게시와
원 전체 값/행/수지·명시+273일 달력 이동·현재 권리·원 종료/정리를 검증하는 단계다.
9시간은 실험 상한이며 완료 시간/처리량/완료 날짜의 예측이 아니다. 전체 API/동일 UTC3D는 그 다음이다.

생과 수확·물/양분·구매 에너지·작물 Decimal 손익, 실제 제품 CLI/독립 G1과 G0–G4는 후속이다.
실제 품종 입력/국내 독립 자료/측정 농장 작물 Run0건·예측/미래 마진/추천 hold,
최신 native 화면 원 명령 종료 누락과 hosted Backend HBA hold를 유지한다.
