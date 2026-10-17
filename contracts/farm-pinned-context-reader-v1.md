# 농장 등록의 같은 범위 현재 참조 읽기 v1

근거: [실제 등록 비용](../research/crop-solar-worker-progress-diagnostics-20261017.md).
CI39033602306의 등록674반환 중 `_prepare`269.181초, 경제 검증159.035초,
별도 hold33.791초·context2022반환49.780초를 관찰했다. 시간은 중첩·관찰 비용 포함이다.

## 작은 변경

기존 candidate `read_scope` 안에서 현재 decision context·hold를 읽고 같은 경제 pin 검증을 수행한다.
현재 참조는 매번 실제 행/서명/권한을 읽는다. 기존 같은 신원 source-owned reader의
SCRAM·Read Committed/Read Only·역할/결속 전후 검사와 부적합 fallback을 재사용한다.
농장 입력 컴파일·연구/snapshot 검증·Decimal 본문·수치·원 시각·권리는 유지한다.
새 연결 pool·값/검증 결과 cache·물리 계수·CLI 호출은 추가하지 않는다.

## 다음 한 단계 수용

1. 실제 SCRAM에서 기존 개별 context/hold+경제 검증과 새 조합의 원 context/hold·typed pin을 대사한다.
   적합한 구성의 실제 연결을 줄이고 모두 source 소유 close를 확인한다. 절약 시간은 측정 전 추정하지 않는다.
2. 부적합 구성은 기존 별도 연결을 보존한다. 공유 시작 후 변경은 실패하며 새 연결 fallback으로 감추지 않는다.
3. 현재 scope 철회·다른 거래의 원문/서명 변경을 다시 읽어 거부하고, 정상/예외 후 scope 토큰과 연결을 정리한다.
4. 농장 등록의 기존 불변 bytes/해시·입력/경제 계산 호출·늦은 권리/저장 변경 회귀를 확인한다.
5. source/fixture/5root/두 UI/512MiB/PID·합1GiB와 FD/소유/PG/임시/passfile 정리를 보존한다.

컴포넌트 GREEN은 원64걸음 정상 완료·WSL 동시 용량·S3/S4·배포/G0–G4 수용이 아니다.
원 정상의 trace-OFF 독립 실행은 별도 원 기준을 통과해야 한다.
