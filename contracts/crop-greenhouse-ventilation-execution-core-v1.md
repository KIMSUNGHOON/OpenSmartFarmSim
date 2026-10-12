# 환기 모델의 접수·자동 계산 핵심 — v1


**2026-10-12 취소 경계 보완:** [환기 범위 잠금 수정·125검사](../research/crop-greenhouse-ventilation-cancel-lock-fix-20261012.md)를 로컬 수용했다. 현재 증거 검증 후 짧은 행 확정 잠금에서 임대/취소/입력·최신 checkpoint를 재확인한다. 환기 typed 취소는 같은 서비스의 NO KEY UPDATE 전이를 사용하고 현재 취소 권한/입력 판본과 기존 사건/상태를 보존한다. 입력 사용 권리 철회 뒤 소유자 취소가 가능하다. 수정본 실제 WebGL·사용자 적용은 후속이다.
2026-10-12. native Codex CLI `gpt-6.1-sol / xhigh`에서 설계한다. 재귀 CLI0.
[명시 조회 runtime](crop-greenhouse-ventilation-runtime-v1.md) 이후의 실행 핵심이다.

## 입력과 실행

새 `joint-ventilation-execution-input-v1`은 현재 등록 농장·새 입력 증거·권리·resolver 판본을 고정한다.
별도 intent domain과 study/revision 멱등 키로 기존 simulation 작업표에 접수한다.
같은 요청은 같은 작업이며 같은 revision의 다른 입력은 충돌한다. 접수 중 권리 변경은 삽입 전체를 되돌린다.
접수와 checkpoint 확인은 생장/환기 계산·결과 등록을 호출하지 않는다.

`VentilationExecutionService`, `VentilationExecutionCheckpointStore`, `VentilationExecutionWorker`는
새 binding/custody/result store의 정확한 타입·동일 객체·코드/입력 판본을 검사한다.
기존 임대·취소·재시도와 현재 권리를 사용한다. lease 갱신 뒤 제한된 구간만 계산한다.
서명한 파일 HEAD를 기존 작업 사건에 확인하고, 중복 확인은 최초 사건/시각을 유지한다.
새 checkpoint/publication/result-link 판본·사건 이름을 사용해 구 모델과 구분한다.

서버가 이미 계산한 확정 HEAD는 다음 시도가 채택한다. 재개 전에 원 prefix를 다시 계산하지 않는다.
계산 취소·권리 철회·임대 상실은 결과 게시를 막는다. 비공개 파일 prefix 자체는 확정 사용자 결과가 아니다.
정상·수치 보류의 등록 결과와 result link·attempt outcome·작업 terminal을 같은 DB 거래로 저장한다.
정상만 기존 job publication을 추가한다. 수치 보류는 원 prefix/사유를 가진 보류 결과다.
마지막 현재 권리·입력·lease fence가 실패하면 부분 DB 결과와 terminal 게시를 모두 되돌린다.

기존 `DeterministicJobDiscovery`와 `DeterministicWorkerLoop`의 허용 목록에 새 판본/정확한 worker 타입만 추가한다.
명시 선택한 판본만 자동 소비한다. 기존 worker·경제/구 joint 판본의 선택은 유지한다.
새 queue/schema·역할 grant·패키지·사용자 서비스 재시작은 추가하지 않는다.

## 이번 수용 범위

1. 실제 SCRAM에서 접수 멱등/충돌·닫힌 입력·접수 중 권리 철회의 원자 rollback.
2. 실제 정상/보류의 원108상태·25장부/10수지·사건/UTC·완료 checkpoint/저장 결과 일치.
3. 취소·임대 만료/재시도·실제 SIGKILL 뒤 fresh worker의 prefix 채택과 남은 구간만 계산.
4. publication/최종 fence 실패와 늦은 scope/권리/resolver 변경에 부분 결과0.
5. 독립 Python 자동 소비자가 작업 ID 지시 없이 새 판본만 발견·계산하며 다른 판본은 queued 유지.
6. 조회/중복 checkpoint의9수치 호출0·원 사건/시각·기존 소비자·두 UI/원본·WSL 보존.

합성32초 소프트웨어 검증이다. 다음은 새 실행의 현재 진행 조회·접수/취소 HTTP·명시 runtime 조립이다.
그 뒤 typed web/같은 UTC3D·실제 사용자 적용을 진행한다. 이 핵심만으로 부모 실행/UI 작업을 완료하지 않는다.
실제 품종·전체 작기·구매 자원·경제·농장/전망 관문은 각 자료와 별도 수용 증거를 요구한다.
