# 새 검증 계산의 실제 DB·TLS·WebGL — 실행 시작 기록

2026-10-08 KST. [2 core파일 계약](../contracts/web-crop-cycle-calculation-native-v1.md)에 따라
새 수동 통합 시험과 기존 브라우저 하네스의 명시 판본 선택을 구현했다.
[고정 시작 영수증](artifacts/web-crop-cycle-calculation-native-started-reference-20261008.json)은
**종료·수용 증거가 아니다.** native와 웹 부모 체크는 미완료로 유지한다.
native Codex CLI `gpt-6.1-sol / xhigh`의 실제 문맥을 확인했으며 재귀 CLI 실행은0회다.

## 구현과 통과한 준비 검사

[수동 시험](../backend/tests/web_crop_cycle_calculation_replay_smoke.py)은 실제 소유 등록 농장에서
계산·서명·DB 게시 후 보호 설정 loader·HTTPS·기존 App으로 원량/UTC를 대사한다.
[브라우저 하네스](../web/e2e/real-cycle-crop-replay-smoke.mjs)는 기본 구형 경로와 명시 새 경로를 지원한다.
새 경로의 유효 HMAC 변조 거부·실제 WebGL loss/restore·동작 줄이기/키보드·정리 검사를 추가했다.
기존 모델/계수·SDK/window/UI/backend/잠금·CI의118 source SHA를 보존했다.

| 준비 검사 | 실제 결과 | 증거 범위 |
| --- | --- | --- |
| 새 기록 응답 브라우저 | 종료0 / 16.79초 | 원값·권리/변조 거부·WebGL 복구·정리 |
| 기존 기본 경로 브라우저 | 종료0 / 15.59초 | 기본 연결·원값·권리·정리 호환 |
| 수동 pytest 수집 | 종료0 / 1개 수집 | import·fixture 수집만 |
| Python/Node 문법 검사 | 종료0 | 구문만 |

두 브라우저 검사는 소유 기록 응답이며 실제 DB/TLS 검증을 대신하지 않는다.
기존 경로의 과거/출력0 사례는 형식 호환용 구성이다. 새 품종/수확 근거로 사용하지 않는다.
원 누적 값의 비교는 key 순서만 정규화하며 수치·단위 검사와 엄격한 메타데이터 검사를 유지한다.

## 실제 실행에서 발견한 두 준비 오류

첫 실행은175byte 소켓 경로로 PG 기동에 실패했다. crop 계산0걸음이며 소유 임시 tree와 프로세스가 정리됐다.
Linux AF_UNIX 길이 거부를 확인해 짧은 소유 `/tmp` 경로로 수정했다. 제품/HTTP 한도는 유지했다.
두 번째 실행은 실제 SCRAM·과거 hold까지 도달했으나 새 시험이 내부 증명의 전체 summary를
닫힌 공개 projection에 넘겨 실패했다. 실제 CurrentQuery의 terminal을 사용하도록 시험을 수정했다.
두 실행의 실패 로그/명령/source/종료·PG/비밀번호/임시 정리는 시작 영수증에 보존했다.

## 01:26 KST의 실제 진행 관측

수정한 동일 실행의 세 사례는 계산·서명·DB 게시·현재 조회 준비 검사를 통과했다.
확인 과거 hold·빈 hold는 각각0걸음/hold, 출력 없는 완료는120걸음/completed다.
이어25시간 프로그램의 **1,620 / 11,400걸음**,4시점/2사건을 불변 progress에서 확인했다.
같은 PID/start ticks의 생존을 직접 확인했다. 이 관측 시점의 새 HTTPS/브라우저 단계는 아직 시작 전이다.
원27시점/5사건의 수치와273일 UTC 이동을 전체 브라우저에서 대사하는 종료 증거는 남아 있다.
nice19·PG/계산/브라우저 각1개·60분 관측 예산을 유지한다. 예산을 완료 약속으로 해석하지 않는다.

## 기존 CI의 실제 완료 범위

`f2dc10f`의 C0/웹/작성 PG/앱은 성공했다. Backend는1분할 성공·2분할 실행·3분할 대기 관측이다.
[앱 hosted 영수증](artifacts/application-operator-policy-hosted-reference-20261008.json)은
기존 세 Compose 경로의42개 실제 사건·재시작·권한 거부·정리를 대사했다.
이 증거로 기존 설정 호환 작업만 완료한다. 새 수동 통합 코드의 hosted 또는 전체 Backend 성공은 아니다.
추가 push·CI 취소/rerun·설정/한도 변경은 수행하지 않았다.

다음은 **같은 실행의 terminal/HTTP/WebGL/정리 확인 → 등록 전체 작기 누적 비용·복원 →
생과 수확 → 자원 사용 → Decimal 경제 연결**이다. native3–5집중시간 잠정은 실제 종료 뒤 갱신한다.
실제 채택 품종 입력·국내 독립 검증 자료·측정 농장 작물 Run0건과 G0–G4 `not_assessed`를 유지한다.
전체 생산 예측·추천/공개 운영 완료 날짜는 외부 자료·검증 확보 전 산정하지 않는다.
