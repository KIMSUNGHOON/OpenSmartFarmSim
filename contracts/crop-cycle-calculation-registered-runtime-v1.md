# 같은 등록 농장의 별도 Python 재구성 — v1 개발 계약

2026-10-08 KST. [전체 지속 실행](crop-cycle-calculation-full-registered-run-v1.md)의 첫 구현 자식이다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하고 재귀 CLI는 실행하지 않는다.

`research/crop-cycle-registered-runtime.py`는 소유 합성 시험의 동일 DB/농장/입력·서버v3를
사설0700 설정과 명시 config SHA로 다시 구성하는 연구 harness다.
새 소유 runtime 설정은 첫 계산 전에 발급하고 기존 intent/HEAD는 이 설정으로 자동 채택하지 않는다.
DB 비밀·서명 key·원 proof는0400 파일에만 두고 repository/공개 receipt/argv에 복사하지 않는다.
고정 참조 파일의 SHA·닫힌 schema/판본·현재 소유/mode를 검사한 뒤 서비스를 구성한다.
입력·수식·권리·DB 역할·HMAC·저장 한도·API/제품 CLI를 바꾸지 않는다.

권한/입력 허용은 소유 시험의 현재 사설 파일로 매번 확인한다. 실제 계정 서비스나
현장 원천 권리를 대체하는 제품 구현이 아니다. 닫힌 context는 마지막 하나만 보관하고 다음 열기 전 정리를 확인한다.
테스트용 기존 deterministic context verifier·고정 reference profiles를 사용하며 독립 G1을 주장하지 않는다.

수용 기준:

1. 잘못된 config SHA/판본/schema·공개 mode·고정 파일 변조를 DB 연결 전에 거부하는 RED/GREEN.
2. 실제 SCRAM 등록 계산을 일부 진행한 뒤 fresh Python에서 같은 현재 DB/농장·전체 checkpoint를 RHS0 복원한다.
   새 프로세스의 실제 PID/시작 identity·원 argv/로그·종료와 소스/FD/context 정리를 기록한다.
3. 별도 child의 실제 추가 계산은 같은 예산의 연속 제어 결과와 전체 checkpoint/행/UTC가 같아야 한다.
4. 복원 후 계산 전 정지한 소유 child에 SIGKILL을 보내 실제-9·원 HEAD 보존을 기록한다.
   새 Python이 같은 checkpoint를 다시 복원해 이어 계산한다. 계산 도중 crash 수용으로 넓히지 않는다.
5. 현재 read scope/입력 허용 철회를 새 child에서도 거부하고 불완료 DB 게시·원 결과·DB 행을 보존한다.
   시험은 nice19·소유 PG/계산 하나·원 명령600초 이내이며 host SCRAM·DB/비밀/PG/임시 경로를 정리한다.

이 자식은 지속 spec/deadline·동시/취소/RSS 감독의 전체 구현이나 전체166일 수용이 아니다.
그 부모의 남은 기준을 통과하기 전9시간 실험은 시작하지 않는다.
실제 품종/국내 독립 자료/측정 작물 Run0건·G0–G4 `not_assessed`·예측/추천 hold를 유지한다.
