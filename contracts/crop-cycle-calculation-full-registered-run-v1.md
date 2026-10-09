# 등록 전체 작기의 지속 실행·수용 — v1 개발 계약

2026-10-08 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`의 설계 판단이며 재귀 CLI는0회다.
선행은 [전체 원 격자·참조 용량](../research/crop-cycle-calculation-full-capacity-observed-20261008.md)이다.
다음 구현은 이 계약의 작은 감독자/등록 런타임 검증이다. **장시간 실행은 아직 시작하지 않는다.**

## 고정 대상과 실행 예산

전체 소유 합성 달력 root `05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`,
2026-10-01→2027-03-16, 원8초RK4/300초 출력·현재 서버v3·요청4,096전이/10,000걸음을 유지한다.
계획456묶음/1,816,704걸음/47,809출력/5사건은 정수·참조 용량 근거이며 실제 완료값은 새 실행에서 검증한다.
실효128경계·page2MiB/128행·delta8MiB/16page·artifact512MiB 등 제품 한도는 바꾸지 않는다.

준비 시작부터 **32,400초(9시간)**의 고정 실험 예산을 사용한다. 시작·deadline·spec SHA를
준비 요청에 먼저 보존하고 중단/재개에서도 같은 deadline을 사용한다. 완료 시간의 추정·약속이 아니다.
근거는 선행 실제 전체 순수 계산20,518.836초, 원 격자 전체 대사와456묶음·예약 포함481,987,541bytes의 용량이다.
남은11,881.164초는 등록/현재 입력·권리/전체 bytes/HMAC·서명·terminal QC/게시·정리를 위한 실험 여유다.
그 비용이 여유 안에 든다고 검증한 것은 아니다. 두 초기 advance의 선형 외삽으로 처리량/완료 날짜를 내지 않는다.
현재 prefix는 과거 metadata와 page bytes·proof 체인을 반복 읽는다.456묶음에서도 누적 순회가 남으므로
호출별 원 비용/저장량/현재 bytes/HMAC·진행 시각을 보존하고 만료 시 확인된 과거와 hold를 남긴다.

nice19·소유 무거운 계산/PG pipeline은 하나다. 주 계산 프로세스 표본 RSS512MiB,
동시에 살아 있는 소유 pipeline의 표본 RSS 합1GiB를 상한으로 감시한다. shared page를 중복 셀 수 있는
보수적 감시값이며 WSL 전체/PSS나 production 성능 수용이 아니다.
선행 등록 trial의 primary219,074,560bytes/descendant 합299,700,224bytes와 용량 trial140,320,768bytes를 근거로 한다.
시작 직전 MemAvailable·지속/임시 저장 여유를 기록하고 두 공간에 각각2GiB 미만이면 시작하지 않는다.
모든 닫힌 context를 누적 보관하는 시험 resolver를 장시간 harness에 그대로 쓰지 않는다.
입력 재검사·현재 권리/bytes/HMAC를 줄이는 캐시로 메모리 문제를 해결하지 않는다.

## 감독과 현재 상태

소유0700 지속 경로에 준비·spec·source/입력/등록/DB 참조·원 명령·PID/start tick/boot ID·
로그 SHA·실제 종료 코드·선택 HEAD·시도 영수증을 fsync 후 불변 보존한다. 비밀은 사설 파일만 사용한다.
감독자는 실제 Python child를 실행하며 Codex CLI를 실행하지 않는다. source freeze는 최종 감사 뒤 해제한다.
배타 lock의 실제 획득·현재 PID 시작 identity를 확인한다. lock 파일만 보고 실행 중으로 판단하지 않는다.
관측 만료는 종료가 아니다. 같은 handle/PID/원 receipt를 확인하고 관측 만료로 재시작하지 않는다.

진행은 실제 custody HEAD/progress에서만 기록한다. 정수 용량 cursor를 crop checkpoint로 넣지 않는다.
명시 중단은 확정 묶음 사이에서 요청하고, deadline/RSS 초과는 소유 child에 SIGINT 후 실제 종료를 기록한다.
유예10초 뒤에도 동일 소유 프로세스가 살아 있으면 SIGTERM, 추가10초 뒤 SIGKILL을 사용한다.
강제 종료·로그 유실·결과 부재는 성공이 아니다. 같은 spec/source/deadline·현재 DB/농장/입력 권리와
원 HEAD/HMAC의 별도 Python 복원 검증이 있어야 명시 재개한다. 자동 재시작·예산 초기화는 하지 않는다.
시험용 PG도 PID/start와 directory를 추적하고 부속 process·role/schema/passfile을 끝에 정리한다.

기존 HTTP30초·작업 lease/cancel 정책은 바꾸지 않는다. 긴 advance는 HTTP handler 안에서 실행하지 않는다.
새 harness가 제품 작업자/lease 경로를 사용한다면 heartbeat·취소·게시 fencing을 기존 계약으로 검증해야 한다.
소유 등록 harness를 제품 CLI 작업자의 실행 또는 독립 G1으로 재분류하지 않는다.

## 다음 구현의 수용 기준

1. 작은 실제 SCRAM 등록 계산에서 지속 spec/로그/원 명령 종료·source/입력/DB 참조를 대사한다.
2. 확정 HEAD 뒤 중단 → **fresh Python**에서 같은 DB/농장·서버 설정·전체 checkpoint의 RHS0 복원 →
   실제 추가 계산을 검증한다. fork만으로 이 조건을 충족하지 않는다.
3. 소유 child SIGKILL의 실제 음수 종료·불완전 상태를 기록하고 같은 spec/deadline 재개가
   연속 작은 제어 결과의 상태/출력/사건과 같아야 한다. 동시 실행·source/spec/bytes 변조를 거부한다.
4. 현재 권리 철회·취소/만료·메모리/벽시계 한도·불완료 게시 거부와 FD/context/cache·
   실제 host SCRAM·DB/비밀/PG/임시 경로 정리를 검증한다. 작은 시험은 원 명령600초 이내다.
5. 위 증거와 고정 manifest를 감사한 뒤에만 별도 새 전체166일 등록 실행을 시작한다.
   성공은 실제 terminal·전체 원량/행/UTC·수지·현재 권리·종료/정리와 DB 게시 증거로 판단한다.
   전체 원 참조와 +273일 이동을 대사하며 실제 새 저장량과 용량 상계를 구분한다.

그 다음은 저장된 전체 결과의 현재 API/같은 UTC3D, 생과 수확 제거/환산 → 물·양분/구매 에너지 →
작물 결과와 Decimal 손익 연결이다. 최신 native 화면 원 명령 종료 유실과 hosted Backend HBA hold는 별도다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
