# 취소503의 잠금 대기 발생 지점 — 2026-10-12

## 확인한 범위

[이전 실패](crop-greenhouse-ventilation-live-hold-cancel-20261012.md)에 이어 취소 action만 예외 위치를 기록했다. 진행 조회는 원 awaitable을 그대로 사용했다. 원65789 actual1에서 실제 취소503을 재현하고 `QueryCanceled`, SQLSTATE `57014`, `JobStore.cancel → _locked_job`의 `SELECT FOR UPDATE`를 수집했다. request role의 `statement_timeout`은5,000ms다. 오류 메시지·locals·개인 입력은 기록하지 않았다.

DB 행 잠금 대기 중 제한에 걸리는 발생 지점을 확인했다. 실제 blocking PID/worker phase의 pg_stat_activity 표본은 없으므로 특정 단계의 잠금 보유 시간을 측정했다고 주장하지 않는다. 작업자 `_before`/checkpoint/종료 transaction이 현재 권리·증거를 검증하는 동안 같은 행을 잠그는 코드가 있다. 수용 실패는 유지하며 취소 성공으로 표시하지 않는다.

## 다음 수정과 수용 기준

1. 실제 SCRAM DB의 독립 연결에서 증거 검증 중 취소가 commit되는 회귀 검사를 만든다. 시험 장벽은 이 동시성 검사에만 사용하며 실제 브라우저 수용 증거로 사용하지 않는다.
2. 비싼 검증 동안의 작업 행 잠금 범위를 줄인다. 종료 직전 현재 임대·취소·입력/체크포인트를 다시 검사하고 늦은 권리 철회 시 모든 결과 쓰기 rollback을 유지한다. timeout 상향은 수정으로 삼지 않는다.
3. 계측/정지 장벽 없는 실제 API/자동 작업자/WebGL에서 원값/UTC→취소 수락→worker canceled·장면 제거·결과 미게시를 확인한다. 기존 정상/보류·조회 부작용0·WSL/원본/두 UI 보존을 유지한다.

[PostgreSQL16 잠금 문서](https://www.postgresql.org/docs/16/explicit-locking.html#LOCKING-ROWS)는 NO KEY UPDATE와 KEY SHARE의 공존 및 UPDATE와의 충돌을 정의한다. 실제 FK를 포함한 동시성 검사가 수정의 전제다.

## 사용자 화면과 보존

두 화면을 같은 저장 결과·접속 토큰으로 복구했다. legacy `run-v17`, modern `serve-v16`이며 원14108 actual0으로 기존112작업/370사건/37attempt와464파일, legacy89작업/47,809표본/47,813수확행, 키·권리·원본2,148항목·보호root4를 보존했다. 접속 안내는 [web README](../web/README.md)에 있다.

원11121 actual0의 실제 브라우저가5173상단/5174에서 같은 최신 기록·5단계·15초 자동 재조회·390px·인증/쓰기0·pageerror0을 확인했다. 개발 기록은 작업 단계 검증 뒤 게시되며 계산 진행률은 아니다.

남은2–5집중시간은 잠금 수정/재검증1.5–3.5 + 사용자 적용0.5–1.5의 잠정 작업량이다. 새 모델 미배포·실제 농장 Run0·G0–G4 미평가·전체 작기/생산·경제/추천/최종 UI 완료일 미정을 유지한다. [구조화 기록](artifacts/crop-greenhouse-ventilation-cancel-lock-diagnosis-20261012.json).
