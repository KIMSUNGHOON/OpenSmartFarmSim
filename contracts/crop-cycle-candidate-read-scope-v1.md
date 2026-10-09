# 작기 계산을 위한 후보 입력 읽기 범위 — v1

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[전체 입력 부분 비용](../research/crop-cycle-full166-prefix-cost-observed-20261008.md)의
경제 검증/계산338회·독점280.720초와 실제 getter의 반복 감사 연결이 변경 근거다.
기존 [원천 읽기 범위](crop-cycle-market-read-scope-v1.md)의 후보 연결 후속이며 운영 기반은
[고정 범위](../research/crop-priority-and-runtime-freeze-20261004.md)를 따른다.

## 다음 한 단계

`MarketCandidateStore.read_scope`가 현재 `validate_pinned` 한 호출 동안 자체 후보 연결 하나도 소유한다.
`ContextVar`와 읽기 전용 Read Committed를 사용하고 같은 store의 중첩을 거부한다.
기존 source 범위는 그대로 연결한다. `_candidate`·`get_economic_input`의 읽기만 범위 연결을 사용한다.
범위 밖 읽기와 모든 쓰기는 기존 독립 연결 경로를 따른다.
pin/숫자 payload·manifest·해시·현재 tenant/scope·원천 job·rights·정산 검사는 매번 실제 행으로 수행한다.
행/결과를 캐시하지 않으며 산식·프로필·schema·제출/게시 계약은 이 단계의 변경 대상이 아니다.
정상 반환 전 현재 principal과 runtime effective grants를 다시 검사한다.
예외에는 ContextVar를 복원하고 rollback/close한다. 다른 tenant·닫힌 연결의 재사용은 거부한다.

## 수용 기준

1. 실제 SCRAM 시험에서 기존 read_scope의 후보 연결 반복을 먼저 재현한다.
   수정 뒤 같은 request/scenario/전체 pin/Decimal 결과·ID와 원 후보/숫자/원천 검사 횟수를 보존하고
   후보 연결은 검증 호출당1개가 되어야 한다. 원천 연결도 기존1개를 유지한다.
2. 같은 범위에서 commit된 후보 숫자/원천 job 변조와 권리 누락을 다시 읽어 거부한다.
   현재 scope/tenant/authenticated 철회·진입/정상 종료 grant drift를 거부한다.
3. 읽기 전용·Read Committed, write 거부, 중첩 거부, 정상/예외 뒤 연결 종료와 빈 ContextVar,
   범위 뒤 독립 읽기 및 같은 store의 별도 동시 context 연결을 실제 PG에서 확인한다.
4. 기존 후보·원천 범위·경제 접수의 원자성/권한 회귀를 집중 검증한다.
   원 validator와 산술 본문 보존, 실제 명령 종료·FD/DB/비밀/PG 정리를 확인한다.
5. 같은 등록 입력의 작은 계산을 개선 전 관측과 대사하고 호출별 비용을 기록한다.
   원 결과·checkpoint·현재 권리·RHS0 조회를 보존한다. 개선 측정 전에는 성능 수용을 선언하지 않는다.

이 자식은 전체166일 실행 예산·terminal/DB/API/3D나 누적 비용 부모를 완료하지 않는다.
실제 품종·독립 자료·제품 CLI·G0–G4와 생산/경제 연결의 후속 조건도 유지한다.
