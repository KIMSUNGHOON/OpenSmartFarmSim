# 등록 농장의 큰 계산 묶음·재개 비용 — v1 관측 계약

2026-10-08 KST. 작업 `crop-cycle-calculation-registered-chunk-cost`.
선행은 [제한된 계산 묶음 수용](../research/crop-cycle-calculation-bounded-chunks-implementation-20261008.md)이다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는 실행하지 않는다.

## 범위와 원값

첫 대상은 고정 root `05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`의
전체166일 **소유 합성 입력**을 실제 SCRAM PostgreSQL의 등록 농장/경제 달력에 연결한 경로다.
원/새 각750개 입력과 원29,141개 artifact의 bytes/hash/mode/identity를 보존한다.
신규 core는 이 계약과 `backend/tests/crop_cycle_registered_chunk_cost_smoke.py`다.
제품·기존 비용 계측기·SQL/API/SDK·CI/권한/적분/bytes 한도는 변경하지 않는다.

`max_steps=10000, max_transitions=4096`의 첫 두 묶음을 실제 계산/서명/HEAD에 저장한다.
첫 checkpoint 전체는 선행 실제4,096 저장 증거와 같아야 한다.
두 묶음의 합은 원128전이64commit의 checkpoint와6 provenance 필드를 구분해 대사하고,
원 sample/event는 명시한 +273일 달력 이동 뒤 전체 값/UTC·순서가 같아야 한다.
현재 서명 proof와 현재 bytes/HMAC·농장/경제/입력 권리 검사는 그대로 실행한다.

## 별도 프로세스와 비용 정의

첫 묶음은 부모, 둘째 묶음은 `multiprocessing`의 별도 **fork** 프로세스에서 수행한다.
fork 직전 DB 연결은 각 `with connect()` 범위를 벗어나 닫고, 자식은 새 서버 객체·입력 문맥·DB 연결을 연다.
자식이 실제 SCRAM/used_password를 확인하고 기존 HEAD/전체 checkpoint를 RHS0으로 복원한 뒤 이어 계산한다.
자식 보고서는 실제 PID/시작 identity·종료·새 progress/checkpoint와 호출/비용을 기록한다.
이는 fresh exec·제품 CLI worker/설정 loader·독립 권한 해제 검증이 아니다.
그 범위는 앞선 fresh Python 파일 복원과 이후 실제 런타임 수용 증거로 따로 관리한다.

기존 `crop-cycle-calculation-prefix-cost.py`의 `observation()`/Costs를 재사용한다.
이 계측기의 기존128전이 관측 loop/판본·수치는 바꾸지 않는다.
각 실제 advance의 RHS·새 delta QC·현재 blob bytes·HMAC/proof·농장/시장/Decimal 참조 검증 비용과
별도 read-only checkpoint 진단 비용을 구분한다. wrapper 중첩 시간은 더해서 총 시간으로 쓰지 않는다.
농장 경제 참조의 검증 호출을 작물 수확량과 손익의 신규 연결로 표시하지 않는다.

## 수용 기준

1. 실제 PostgreSQL의 명시 runtime 권한으로 등록한 농장·경제 기간과 원 입력을 확인하고
   실제 SCRAM/used_password·모든 host rule의 `scram-sha-256`/error 없음 및 기본 권한을 유지한다.
2. 실제 두 advance가 각각4,096전이이고 합8,192전이·2commit·yielded이어야 한다.
   두 프로세스의 원량·경계/hold·체크포인트/행·예산·출력/사건128행 및 기존 bytes 한도를 확인한다.
3. 별도 fork 자식이 현재 DB/권리·bytes를 재검사하고 첫 checkpoint 전체를 RHS0으로 복원한다.
   자식의 실제 계산·종료0와 부모의 재조회/확정 행 대사·FD/cache 정리를 확인한다.
4. 실제 각 advance의 delta QC는 writer/publisher 각각 한 번이다.
   측정한 server의 read-only 복원/재조회는 RHS0·과거 delta 물리 QC0이며 현재 전체 bytes/HMAC 검사는 양수다.
   관측 밖 원량 대사를 위해 따로 수행하는 artifact 전체 delta QC는 이 조회 비용과 구분한다.
5. 부모 재조회 중 현재 입력 권리·계정 scope 철회를 거부한다.
   소유 시험용 복사 packet의 현재 root/block bytes 변조도 재계산 전에 거부하고 선택 HEAD/DB 행은 보존한다.
   yielded prefix를 DB 완료 결과로 게시할 수 없어야 한다.
6. 원/새 입력·원 결과·선행 증거/source를 보존하고 DB 행·schema/role·비밀/passfile·PG·자식/감독자·임시 경로를 정리한다.
   실제 PID 시작 identity·로그 SHA·원 명령 종료와 별도 최종 감사를 불변 receipt/보고서로 남긴 뒤 이 자식만 체크한다.

nice19·소유 계산 하나씩 실행한다. 부모가 자식 계산을 기다리는 동안 새 계산/브라우저/컨테이너를 시작하지 않는다.
PG는 이 단일 시험에 필요한 로컬16.15 한 cluster만 쓴다.
원 명령 예산600초, 자식 관측240초는 선행 실제32회339.187초 및 저장4,096전이63.181초에 근거한다.
만료 때 소유 작업을 정리하고 실제 종료를 기록하며 관측 만료로 같은 실험을 재시작하지 않는다.

전체 작기 실행 예산은 이 두 묶음과 전체 경계/저장 용량·남는 이력 순회 비용을 대조한 뒤 별도 고정한다.
이 초기 두 묶음만으로 전체 완료 날짜를 외삽하지 않는다.
전체166일 terminal/DB/API/같은 UTC3D·생과/자원/Decimal 경제·실제 제품 CLI/독립 G1은 후속이다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
