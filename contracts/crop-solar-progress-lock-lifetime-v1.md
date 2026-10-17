# 일사 진행 조회의 짧은 custody 잠금 v1

근거: [실제 종료 진단](../research/crop-solar-worker-termination-diagnostics-20261017.md).
CI39036105645/sourceba87cb8에서 confirm→custody open Pending 재시도 뒤 실제
attempt1/queued/solar_execution_busy를 반환했다. 원 확정4/64다. API는 수집된14응답에서
202/200/503·accepted prefix/page를 반환했고 예상 밖 상태는 관찰하지 않았다.
이것으로 이전 API 단언 실패의 원인을 단정하지 않는다.

## 한 단계 변경

진행 조회 `_checkpoint`의 잠금은 일관된 원 snapshot을 읽는 구간으로 제한한다.
후속 `_terminal`·현재 권리/농장 참조·DB 대사·직렬화 동안에는 조회가 쓰기 잠금을 점유하지 않는다.
응답 종료 시 다시 짧은 잠금으로 원 progress를 대사한다.
정상 signed descendant 전진이나 마지막 대사 잠금 충돌은 Pending으로 응답을 폐기한다.
동일 판본의 변조·불일치·철회·비정상 fork/rollback은 기존 hold/권한 거부를 유지한다.
입력·수식·원64걸음/chunk1·조회 주기·임대/취소·5초 재시도·360/600초·RSS 상한을 바꾸지 않는다.

## 수용 기준

1. 실제 SCRAM 진행 조회의 후속 검증 중 별도 open file description으로 custody 잠금을 획득할 수 있다.
   원 응답/시각/최초 기록·조회 계산/SQL 변경0·모든 FD/소유 정리를 유지한다.
2. 응답 종료 대사의 실제 잠금 충돌은 Pending이며 원 변조는 hold다.
   미리 실제 모델로 만든 signed descendant HEAD를 검증 중 게시했을 때도 Pending으로 부분 응답을 폐기한다.
   이 결정적 소프트웨어 경합 시험을 독립 unpaused 계산 증거로 표시하지 않는다.
3. 기존 none/current/unconfirmed/real-lock·heartbeat/재시도·terminal 정상/hold·권리/late drift 회귀를 통과한다.
4. 원 source/prototype·5root/기존 두 화면/원본·512MiB/PID/합1GiB·FD/PG/임시/passfile을 보존한다.
5. 그 뒤 별도 trace-OFF 원 정상64걸음/attempt1·두 전진 prefix·원 값/UTC·후검사/정리를 수용한다.

컴포넌트 GREEN은 정상/S3/S4·계산 중 WebGL·로컬 동시 용량·사용자 적용·실제 자료/G0–G4 완료가 아니다.
