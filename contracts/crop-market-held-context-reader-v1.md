# 후보 범위의 현재 보류 보고서·판단 맥락 읽기 v1

상태: [현재 GET 계측과 RED 재현](../research/crop-solar-native-HTTP-allocation-20261017.md). 제품 미구현·미채택.
[이전 reader 개선](crop-solar-shared-market-reader-v1.md)의 고유92검사 수용을 유지한다.

## 작은 구현 경계

`backend/app/market_candidate_store.py`와 대응 실제 SCRAM 시험을 우선 경계로 한다.
기존 `MarketHoldStore._market_hold_report/_decision_context`와
`ThermalRunStore._decision_context_in_transaction`을 통해 현재 서명/원 행을 그대로 검증한다.
새 자료/결과 캐시·권한 프로필·공개 API·산술/모델/요금 변경은 이 작업의 근거가 아니다.

- 활성 후보 읽기 scope가 소유하거나 적합하게 빌린 연결만, 정확한 facade/source/hold/context store와
  동일 DSN/schema·같은 runtime policy 객체/kind·같은 provider/tenant일 때 사용한다.
- 실제 SCRAM/password·authenticated/effective user/database와 Read Only/Read Committed,
  열린 transaction·원 scoped connection·현재 역할/권리를 전후 확인한다.
- scope 진입 시 적합하지 않은 설정/기존 프로토콜/범위 밖 읽기는 기존 경로를 유지한다.
  공유 시작 뒤 store/policy/provider/ContextVar/connection/context verifier 등의 결속 변경은
  거부하고 새 연결로 덮지 않는다. 구현 시 결속의 실제 필드와 검증 범위를 기록한다.
- 보류 원문/signature/hash·DecisionContext 원문/signature/hash와 현재 scope resolver를 매번 검사한다.
  현재 tenant/scope/authenticated·판단 시각/용도 검사와 Decimal 참조 산술을 생략하지 않는다.
- 빌리는 쪽은 close/commit하지 않는다. 소유 scope는 예외/취소/중첩/동시 context에서 토큰·연결을 정리한다.

## 다음 한 단계의 수용 기준

1. 실제 SCRAM의 RED를 GREEN으로 전환한다. 같은 request/scenario/pin·전체 Decimal 결과/ID와
   기존 보류/맥락 검증 순서를 보존하며 두 적합 scope의 source2+hold3+context6을 source2로 만든다.
   부적합 fallback은 기존 값/권리/연결 소유를 유지한다.
2. 각 관련 scope/tenant/authenticated 철회와 실제 role/grant/session/DSN/schema/policy/provider/
   store/ContextVar 변경을 거부한다. 공유 시작 후 부적합 경로로 도망가지 않는다.
3. 같은 scope 중 다른 실제 transaction에서 commit한 보류 원문/signature/맥락 원문/hash/
   권한·판단 scope 변조를 다시 읽어 거부한다. 정상 원 bytes/판본/UTC와 current 의미를 보존한다.
4. Read Only write 차단·Read Committed·중첩/별도 동시 context·정상/예외 뒤 소유 close/빈 토큰,
   실제 FD/역할/schema/PG/passfile 정리와 기존 원천/후보·시장/경제 접수 회귀를 통과한다.
5. 기존 산술/원 검증 본문과 변경 파일을 대사한다. 고정 두 실제 GET의 값/UTC·물리 연결/동시 수·
   실제 경제 호출 수를 다시 계측한다. 절약량/전체 최대/운영 용량을 구현 전 추정으로 승인하지 않는다.
6. 필요한 회귀와 새 계측 뒤 실제 SDK 정상/hold의 모든 현재·늦은 권리/페이지/계정/판본/
   취소/전송/원 값·UTC·소유 정리·원본/5root/두 UI·512MiB/PID/합1GiB를 통과해야 S1b를 평가한다.

이 컴포넌트의 GREEN만으로 S1b/S2b/S3/S4나 G0–G4/실제 생산·자원·경제·추천을 완료하지 않는다.
