# Solar 조회의 같은 신원 원천·후보 읽기 연결 — 후보 v1

상태: [읽기 컴포넌트 수용](../research/crop-solar-shared-market-reader-implementation-20261017.md), fce9009. 고유92검사/현재 checkout3반복을 통과했다. 후속 [현재 보류/맥락 reader6004735와 실제 SDK](../research/crop-market-held-context-reader-implementation-20261017.md)를 함께 검증해 기준5/로컬 S1b를 수용했다. 이 원천/후보 reader만으로 SDK 수용을 주장하지 않는다. 새 DOM/WebGL·배포/운영 용량은 별도다. [실제 GET 계측](../research/crop-greenhouse-solar-sdk-read-allocation-20261017.md)이
근거다. 기존 [후보 읽기 범위](crop-cycle-candidate-read-scope-v1.md)와
[원천 읽기 범위](crop-cycle-market-read-scope-v1.md)의 현재 권한/원 자료 검증을 유지한다.

## 구현 경계와 조건

core는 `backend/app/market_source_store.py`, `backend/app/market_candidate_store.py`와
대응 실제 SCRAM 읽기 범위 시험이다. 기존 별도 checkout의 공유 연결 후보는 참고 입력이며 승인 코드가 아니다.

- 원천 scope가 소유 연결을 내부 소비자에 빌려줄 수 있다. 후보는 빌린 연결을 닫거나 commit하지 않는다.
- exact trusted store/wrapper, 동일 DSN/schema·정확한 runtime policy/kind/provider/tenant와
  source ContextVar의 같은 connection을 확인한다. 실제 authenticated/effective user/database,
  SCRAM/password, Read Committed/Read Only와 전체 role/grant audit를 전후 확인한다.
- 동일 신원 적합성이 없으면 기존 두 연결 방식을 유지한다. 공유 후 pointer/identity/권한/transaction
  변경은 거부한다. 잘못된 공유 연결을 새 연결로 덮어 감추지 않는다.
- 범위 전·각 읽기·정상 종료의 현재 권한, source/candidate 원 행/해시 재조회와 산술을 보존한다.
  값이나 검증 결과를 캐시하지 않는다. ContextVar는 정상/오류/중첩·동시 context에서 소유권을 유지한다.
- 이전 v1의 원천1+후보1 관측은 불변 기록으로 보존한다. 이 후보의 적합 경로는 총1개 물리 연결,
  불적합 경로는 기존 원천1+후보1이어야 한다. 더 적은 연결을 권리/산술 검사 감소로 달성하지 않는다.

## 다음 한 단계의 수용 기준

1. 현재 조립의 실제 동일 신원 적합성을 비밀값을 공개하지 않고 확인한다. 기존 source/후보 검사
   순서·호출 수·동일 typed request/scenario/pin/Decimal ledger/result ID·원 행을 대사한다.
2. 소유 SCRAM에서 적합 공유/부적합 fallback, provider/tenant/scope/authenticated 철회,
   실제 role/grant/session identity/DSN/schema drift와 중첩/동시 context를 검증한다.
3. committed 후보 숫자/원천 job/권리 변조를 다시 읽어 거부한다. read-only write 차단,
   Read Committed, 정상/오류 후 source 소유 close·빈 ContextVar·FD/PG/role/passfile 정리를 확인한다.
4. 기존 원천/후보·경제 접수/원자성 회귀를 통과한 뒤에만 제품 후보를 채택한다. 기존 시험의
   물리 연결 수 관측은 새 경로에 맞춰 소유 연결을 추적하며 권리/변조/산술 기대값을 삭제하지 않는다.
5. 실제 SDK normal/hold·원 값/UTC/페이지/현재 및 직렬화 후 권리·잘못된 계정/판본·취소/전송 종료를
   통과하고 5root/두 UI/원본·512MiB/PID/합1GiB를 유지해야 S1b를 평가한다.
   GET 작물/CLI13진입점/SQL0과 경제 참조 검증을 구분해 계측한다. 기록 응답은 live 수용이 아니다.

이 후보는 S2a 화면 수용을 바꾸지 않는다. S1b/S2b/S3/S4, G0–G4/실제 생산·자원·경제·추천과
최종 UI는 해당 증거 전까지 미완료다. 전체 완료 날짜는 이 연결 수정/검증과 외부 자료 상태 뒤 판단한다.

## 현재 연결 매개변수의 호출 내 읽기 — 2026-10-19

[최종46검사](../research/market-current-connection-parameters-20261019.md)로 `_shared_reader` 호출 안에서 한 현재 매개변수 dict를 읽어 모든 기존 구성 필드를 비교하는 부분을 로컬 수용했다. 다음 호출은 다시 읽으며 별도 SCRAM/SQL identity·읽기 전용/isolation·원 역할/원천 검증은 유지한다. 공개 인터페이스와 scope/소유권은 바뀌지 않는다.

원 SQL12,919/감사343/원천3,040/순서/수치/UTC와 늦은 변경 거부·정리를 확인했다. 조회3,963→2,163 및 최종 제품의 로컬 평균 약2.53% 감소는 독립64/계산 중3D/새 배포 수용이 아니다. 후속 fresh SQL 투영은 아직 시험 후보이며 이 수용에 포함하지 않는다.
