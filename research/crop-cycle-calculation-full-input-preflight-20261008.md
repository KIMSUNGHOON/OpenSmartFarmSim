# 원166일 입력의 새 계산 문맥 사전 검사

2026-10-08 KST. [작은 등록 비용 측정](crop-cycle-calculation-prefix-cost-observed-20261008.md) 뒤
`crop-cycle-calculation-full-registration`의 첫 입력 검사를 실제 실행했다.
[고정 영수증](artifacts/crop-cycle-calculation-full-input-preflight-reference-20261008.json)에
원 root/기간·입력 검사 증명·실제 명령 종료와 source/로그 SHA를 보존한다.
native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI0회다.

기존 [순수 전체 실행](crop-cycle-full-rhs-durable-completed-20261007.md)의 불변 입력을 그대로 사용했다.
원 root는 `ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98`,
실제 기간은 **2026-01-01T00:00:00Z~2026-06-16T00:00:00Z**다.
750파일/113,920,841bytes·47,808구간·47,809출력/anchor·5사건을 확인했다.

새 입력 증명을 발급하고 verified calculation context를 실제 열었다.
계획1,816,704걸음·47,811경계·seed121개를 대사했으며 이번 **실제 계산 걸음/RHS/농장 DB 호출은0**이다.
증명 발급30.284409초, context 열기0.369296초, 원 명령 전체32.050963초/종료0이다.
context와 reader는 닫혔고 두 cache는 비었으며 FD4→4다.
원750파일의 SHA/mode/device/inode와 이번123 source pin을 전후 보존했다.
실제 primary PID 종료와 고정120초 예산 내 완료를 확인했다.
표본 primary RSS 최대98,041,856bytes는 WSL 전체 메모리나 실제 농장 실행 부하가 아니다.

## 등록 전에 해결할 달력 대응

현재 작은 등록 fixture의 농장 평가 기간은2026-10-01~2026-11-30이다.
원166일 입력의1~6월 기간과 맞지 않는다. 이번에는 실제 farm binding을 시도하거나 기간 검사를 우회하지 않았다.
다음은 원 입력과 농장 점유/평가·경제 수확/판매/수금 기간을 실제 등록 경로에서 결속하는 단계다.
시각 변환을 선택하려면 별도 명시 판본·새 root와 원량/간격 대사를 먼저 고정해야 한다.
이 관측에서는 입력 UTC를 변경하지 않았다.

입력 증명의 `rights_or_gate_approval`은 false다. 검사 성공은 G0 채택이나 농장 등록 승인이 아니다.
새 context SHA는 원 순수 계산 이력을 등록 서버 이력으로 바꾸지 않는다.
전체166일 등록 계산/누적 비용·DB/복원/API/같은 UTC3D는 미수용이다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건과 G0–G4 `not_assessed`를 유지한다.
