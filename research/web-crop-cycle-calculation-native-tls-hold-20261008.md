# 새 실제 DB·TLS·WebGL — 계산 완료 뒤 TLS 준비 오류 수정

2026-10-08 KST. [시작 기록](web-crop-cycle-calculation-native-started-20261008.md)의 실제 시험은
**1실패 / 1,526.43초**로 종료했다. 새 native/웹 부모는 미수용이다.
[별도 고정 영수증](artifacts/web-crop-cycle-calculation-native-tls-hold-reference-20261008.json)에
실제 종료/source/로그·계산·정리와 후속 원인 검증/수정 판본을 기록한다.
native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI0회다.

## 완료된 계산과 미수용 범위

실제 소유 등록 농장의25시간은 **11,400걸음·27시점/5사건·92 bounded 호출**로 계산을 완료했다.
advance 루프1,303.497794초, DB 게시·결과 증명·현재 조회를 포함한 준비1,334.085330초다.
원 수식/계수/격자와273일 UTC 이동·원 수치 기준을 유지했다. 과거 hold·빈 hold·출력0 완료도 준비했다.
이후 Vite의 신뢰 CA를 사용하는 HTTPS 준비 검사가 실패해 실제 브라우저 protocol은0단계다.
계산 완료를 새 3D 통합 성공으로 표시하지 않는다. fixture 정리 뒤 원 artifact/DB는 보존하지 않았고,
불변 progress·준비 참조/증명 SHA·실패 로그를 남겼다.

원118 source와 시험3 core SHA는 실행 전후 같다. 실제 schema/role/passfile0, PG PID/data와
소유 임시 tree·자식 프로세스 정리를 확인했다. 표본 primary RSS159,698,944bytes,
자식 포함 RSS 합 최대1,029,120,000bytes는 공유 메모리가 중복될 수 있는 표본이며 WSL 전체 peak가 아니다.

## 확인한 원인과 작은 수정

새 수동 시험은 `tls_files`를 함수 인자로 받아 계산 전에 발급했다.
기존 fixture의 인증서 유효기간은10분이고 실제 계산 준비는25분 이상 걸렸다.
기존 구형 native 시험은 계산 후 `request.getfixturevalue('tls_files')`를 호출한다.
실패한 원 인증서 bytes는 fixture 정리로 남아 있지 않으며, 진단은 이 발급 순서/기간 대조와 아래 실제 재현에 근거한다.

| 별도 실제 Vite HTTPS 검사 | 결과 |
| --- | --- |
| 소유 만료 인증서 + 신뢰 CA | `SSLCertVerificationError`, code10 / `certificate has expired` |
| 같은 원 fixture의 새 인증서 + 신뢰 CA | HTTP200 / 431bytes / 0.35초 |

두 Vite PID와 임시 파일을 정리했다. 이 검사는 DB/작물 계산/브라우저를 실행하지 않았다.
[수동 시험](../backend/tests/web_crop_cycle_calculation_replay_smoke.py)의 발급 시점을 계산 후로 옮겼다.
최종 브라우저 보고서도 Python 후속 검사 전에 보존하도록 수정했다.
수정 커밋은 `ac1067e`이며 기존 TLS fixture·인증서 유효기간·CA 검증·20초 준비 한도와 제품30초/2MiB는 그대로다.
수정 후 Python 구문·pytest1개 수집을 통과했다. 새 native 전체 실행은 시작했으며 성공 종료 증거는 아직 없다.

## 다음 단계

같은 수정 실행의 실제 terminal/HTTPS/WebGL/권리·변조 거부/정리를 확인한 뒤 native·웹 부모를 평가한다.
[누적 비용 계약](../contracts/crop-cycle-calculation-prefix-cost-v1.md)은 작은 기준선/곡선과 전체 입력 등록을 구분했다.
다른 PG/계산 실험은 현재 native 종료 후 실행한다. 전체166일 등록 복원/3D → 생과/자원 →
Decimal 경제 순서를 유지한다. 실제 품종 입력·국내 독립 자료·측정 작물 Run0건과 G0–G4 `not_assessed`,
예측·추천 보류는 그대로다. 최종 제품 완료 날짜를 이 작은 시험 시간으로 추정하지 않는다.
