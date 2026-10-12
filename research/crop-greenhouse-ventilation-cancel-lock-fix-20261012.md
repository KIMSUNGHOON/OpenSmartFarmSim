# 환기 실행의 취소 잠금 수정 — 2026-10-12

## 수용 경계

[실제503 발생 지점](crop-greenhouse-ventilation-cancel-lock-diagnosis-20261012.md)에 대응한 **환기 모델의 작은 수정과 집중125검사를 로컬 수용**했다. 수정본의 장벽 없는 실제 WebGL 취소/정상/보류와 사용자 적용은 다음 단계다. 기존 실제 정상/보류3D 기록은 당시 코드 판본의 증거로 보존한다.

동일 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 조사·설계·검토했고 재귀 CLI 실행은0이다. [구조화 기록](artifacts/crop-greenhouse-ventilation-cancel-lock-fix-20261012.json)에 실제 호출 문맥·4개 production 파일의 동일 SHA·원 도구 종료와 제외한 실행을 보존했다. 수식·계수·요금·관문을 변경하지 않았다.

## 수정

- `_before`/checkpoint/종료 처리에서 비용이 큰 현재 증거·권리 검증을 작업 행의 갱신 잠금 밖으로 옮겼다. 확정 직전에 같은 임대·취소·입력과 최신 checkpoint를 다시 검사한다.
- 환기 접수 서비스의 취소 메서드를 실제 typed API에 연결했다. tenant·취소 권한·정확한 입력 판본을 확인하고 기존 cancel flag·사건·queued/active/terminal 전이를 보존한다. 과학 입력 권리가 철회된 소유자도 취소할 수 있다.
- 짧은 확정과 취소에 `FOR NO KEY UPDATE`를 사용한다. [PostgreSQL16](https://www.postgresql.org/docs/16/explicit-locking.html#LOCKING-ROWS)의 KEY SHARE 호환성을 실제 FK/독립 SCRAM 연결에서 검사했다. timeout은5초 그대로다.
- 종료 결과를 잠정 작성한 뒤 현재 권리를 다시 검사하는 순서와 rollback을 유지한다. 미확정 checkpoint/결과가 취소·입력 변경·임대 만료·늦은 철회 후 commit되지 않게 한다.
- 공용 `JobStore`와 기존 모델 파일을 원 바이트로 보존했다. 공용 코드의 전체 해시를 입력 custody가 사용하므로 초기 공용 수정안의6검사 성공은 최종 수용에서 제외하고 환기 범위로 다시 구현·검증했다.

## 실제 검증

| 단계 | 원 도구 / 실제 종료 | 결과 |
| --- | --- | --- |
| 최소 실패 재현 |18739 /1|확정 검증 중 취소의 QueryCanceled·jobs tuple 잠금을 재현. 예상 실패로 보존|
| 최종 동시성/권한 검사 |77355 /0|10 passed: 취소6지점·변경 입력/임대 만료 rollback·queued/active 권리 철회 뒤 취소/범위 거부|
| 정상·보류/API 회귀 |22900 /0|110 passed: 정상/보류 원 수치·UTC·저장, typed API 단위 계약과 실제 SCRAM/검증 TLS 접수·진행·취소·동일 완료/보류 저장 GET·권리 철회 뒤 소유자 취소|
| 늦은 권한/복구 회귀 |26754 /0|5 passed: scope/rights/resolver 늦은 철회 rollback·만료 뒤 새 시도 재개·중복 checkpoint의 원 사건/최초 UTC 유지|
| 최종 사용자 현황 브라우저 |48587 /0|두 HTTP의 같은 최신 기록/실제 DOM·15초 재조회·390px·인증/쓰기0·pageerror0|
| 최종 원본/결과 보존 |14669 /0|원 DB·파일·키/권리·토큰·원본·보호root4 보존|

최종 집중 검사는 고유125개다. 동시성 회귀의 시험 장벽과 API의 수동 worker 단계는 **실제 자동 WebGL 수용 증거로 사용하지 않는다**. 전체 테스트·CI와 수정본의 장벽 없는 실제 WebGL는 이번 단계에서 실행하지 않았다.

원77355/22900/26754의 guard는438/557/375초다. 최대 단일/합 RSS197,197,824/974,118,912bytes,0.25초 표본으로512MiB/PID·1GiB 합 기준을 유지했다. 각 수용 guard의 소유 프로세스/PG/temp/passfile 잔여0·FD4→4다. 초기 선택자 오류·수집 전용·공용 수정안·시험 수정/범위 축소를 위한 두 중단은 제외했고, 중단된 시험의 무효 fixture passfile4개씩을 원 PG 종료 뒤 제거했다.

## 사용자 확인과 다음 순서

**http://localhost:5173/** 상단 또는 **http://localhost:5174/#crop-execution**에서11:35 KST의125검사·다음 작업·남은2–5집중시간을 확인한다. [5173 실제 화면](artifacts/crop-greenhouse-ventilation-cancel-lock-fix-status-5173-desktop-20261012.png), [5174 모바일](artifacts/crop-greenhouse-ventilation-cancel-lock-fix-status-5174-mobile-20261012.png).

두 기존 서버를 계속 열어 둔 채 최종 검사들을 실행했다. 현재 접속 안내는 [web README](../web/README.md)의 `run-v17`/`serve-v16`다. modern112작업/370사건/37attempt·464파일, legacy89작업/47,809표본/47,813수확행, 키·권리·토큰·원본2,148항목·현재 UI172asset을 보존했다.706개 기존 source/test 중 명시된4개 production/2개 test와 앞 단계의25장부 label만 달라졌고699개는 원 바이트다.

다음은 **수정본 실제 취소 WebGL → 같은 판본 정상/보류 WebGL → 기존·새 모델 명시 서버/worker 조립과 사용자 적용**이다. 자원 검증 창에서도 두 주소의 공개 진행 표시를 유지한다. 첫 두 검증/복구0.5–1.5시간, 혼합 조립/화면 적용·보존1.5–3.5시간으로 남은2–5집중시간을 잠정 배정한다. 오류/조립 근거가 나오면 갱신한다.

이 추정은 짧은 합성 모델의 연결 범위다. 새 모델 미배포·실제 농장 Run0·G0–G4 미평가이며 독립 현장 자료, 전체 작기/실제 생산·자원·경제/추천과 최종 제품 UI 완료일은 미정이다.
