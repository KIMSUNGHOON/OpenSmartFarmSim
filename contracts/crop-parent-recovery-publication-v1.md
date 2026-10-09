# 중단된 연구 부모의 사전 게시 선언 복구 v1

선행: 원 producer의 사전 선언/입력/무작위 key 보존, 확인된 원 중단,
같은 artifact/입력의 감독 재개와 프로세스 정리 수정.
핵심4파일은 이 계약, `research/crop-parent-recovery-publication.py`,
`backend/tests/test_crop_parent_recovery_publication.py`,
`backend/tests/crop_parent_recovery_publication_smoke.py`다.

## 순서와 수용

1. 원 실행·게시 선언·config의 hash가 실제 중단 기록의 보존 목록과 일치해야 한다.
   원 선언/실행/key의 파일 시각은 첫 계산 요청보다 앞서야 한다. 원 source guard와
   version/input/plan/reference/farm/config/key를 검사하며 원 PG/마지막 worker는 종료되어야 한다.
   마지막 요청의 결과/receipt 유실만 중단으로 다루고 이전 receipt/hash/원량은 검증한다.
2. 새 감독은 같은 config/input/source/DB data directory/budget/RSS 한도를 사용한다.
   새 마감은 원 감독/준비 마감보다 늦을 수 없다. 원 중단 HEAD/걸음/commit에서 복원한
   첫 로그와 checkpoint가 일치하고 복원 RHS/delta QC0이어야 한다.
   실제 완료 receipt/원 plan 전체 수량·걸음, 종료0/SCRAM/FD 보존 뒤에만 파생 선언을 만든다.
3. 원 게시 선언에서 바꿀 수 있는 값은 supervision directory/SHA 두 개뿐이다.
   원 execution에서는 publication file/SHA 두 개만 바꾼다. 원 파일/key/plan을 덮어쓰지 않는다.
   새 복구 manifest는 원 중단·선언·감독·완료 receipt·파생 파일 hash와 helper source를 묶는다.
   기존 publisher/coordinator의 정상 validation을 파생 파일에도 그대로 적용한다.
4. 파생 manifest 조회 때 원 계보/새 완료/현재 source를 재검사한다. 실제 게시 전 전체 원 행과
   121상태를 기존 비교기로 대사한다. 같은 무작위 DB key로 정상 publisher를 실행하고
   인증 backup/현재 query/원 DB 정리/fresh 복원을 이어간다. 조회/파생의 RHS·게시·증명 발행은0이다.
5. 먼저 작은120걸음 관리 사건 작기에서 실제 중첩 pytest -15/worker 종료·PG 정지/동일 data 재시작,
   같은 checkpoint 복원→완료→원값 대사→정상 게시/원 key→backup/fresh 현재 query를 검증한다.
   원 실패는 남기고 복구 자식의 종료/정리/source/원 마감을 따로 기록한다.
   새 선언 뒤 계획/key/config/농장/입력/원 자료·source/권리/마감 변경을 거부해야 한다.

현재 전체 복구 계산과 이 작은 검증은 병행한다. 작은 수용 전 전체 파생/게시는 보류한다.
전체 부모는 그 뒤 전체 원값/현재 조회·원 종료/자원 감사로 따로 수용한다.
이 복구는 local owned 합성 연구의 사전 선언 계보에 한정하며 제품 재시도/실제 품종/관문 승인이 아니다.
기존 고정 producer source, 기존 guard/publisher, 이전 실패 manifest는 수정하지 않는다.
