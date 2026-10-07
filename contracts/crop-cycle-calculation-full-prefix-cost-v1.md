# 등록된 전체166일 입력의 부분 계산 비용 — v1

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[달력 등록 수용](../research/crop-cycle-full166-calendar-registration-20261008.md) 다음 단계인
`crop-cycle-calculation-full-prefix-cost`를 다룬다. [기존 계측 계약](crop-cycle-calculation-prefix-cost-v1.md)을 따른다.

## 입력과 구현 범위

새 전체 root `05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`와 기존 입력 증명을 재사용한다.
2026-10-01~2027-03-16 UTC·47,808 forcing구간·47,809 output/anchor·5사건,
8초 RK4·300초 출력·1,816,704걸음 계획과 source/입력 판본을 보존한다.
실제 SCRAM 농장·경제 가정은 기존 수용된 생성/등록 fixture로 새 소유 시험 namespace에서 등록한다.

기존 `research/crop-cycle-calculation-prefix-cost.py`에 농장 등록 읽기·시장 후보 검증·경제 검증/산술·
원천 읽기 경계의 비용 항목만 추가한다. 함수의 반환값과 예외·권리/현재 입력 검사를 유지하며
wrapper는 정상/예외 뒤 원 함수로 복원한다. 원천 읽기 시간은 SQL 실행만의 시간이 아니다.
새 수동 시험은 `backend/tests/crop_cycle_full_prefix_cost_smoke.py`다. 제품 수식/계수·권한·schema·UI는 변경하지 않는다.

## 검증 순서

1. 계측 wrapper의 실제 함수 교체/예외 복원과 기존 경량 회귀를 확인한다.
2. 실제 새 전체 입력의125걸음/128전이 한도에서 원 첫123걸음을 계산하고, 원166일 완료 artifact의 저장 검증 증명/typed reader로
   확정 시점/사건을 읽어+273일 시각과 모든 원 수치·input ID를 대사한다.
   원 결과의 parser/전체 QC 재실행이나 RHS는 조회 중 금지하며 원 proof/HEAD·파일을 보존한다.
3. 기존 실제 서버·불변 입력/현재 농장·권리 아래 최대32회의10,000step/128transition bounded advance를 수행한다.
   step/counts/bytes/files와 호출별 포함/독점 시간을 보존한다. 계측 구간은900초,
   전체 소유 명령은1,200초 예산으로 두어 원 행 대사/철회/정리 시간을 남긴다.
   예산이나 호출 한도로 끝나면 실제 yielded/확정 prefix 그대로 기록한다.
4. 새 서비스에서121상태·seed/clock/cursor/누적의 같은 checkpoint를 재조회한다.
   원 완료 artifact의 해당 prefix와 모든 sample/event를 대사하고 조회 RHS0을 확인한다.
   미완료 DB 게시·현재 권리/계정 철회는 거부해야 한다. 입력/기존 결과/행을 변경하지 않는다.
5. nice19·소유 PG/계산 각1개, source 동결·실제 종료 코드·FD/cache·schema/role/passfile·PG PID/data 정리를 기록한다.

이 관측으로 작은 `full-prefix-cost` 자식의 실제 초기/증가 표본만 수용할 수 있다.
전체 등록 계산/누적 비용 부모·전체 terminal/DB/API/3D·복원 부하는 후속 증거를 요구한다.
관측한 병목이 필요한 개선을 입증하면 별도 작은 계약/검증으로 진행하고 그 뒤 전체 실행 예산을 고정한다.
경제 거래량은 명시 가정이며 실제 품종/독립 농장 자료·생과/자원/경제 연결과 G0–G4는 기존 보류를 유지한다.
