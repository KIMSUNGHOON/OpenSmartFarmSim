# 검증 계산 결과의 실제 PG/TLS/WebGL — v1 개발 계약

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행 [새 SDK/범위/화면 수용](../research/web-crop-cycle-calculation-view-20261008.md) 뒤
`crop-cycle-calculation-native-browser`를 실제 소유 등록 합성 계산으로 검증한다.
원 수식/프로필·계산/저장/조회·보호 loader·제품 화면/geometry/그래프/CSS·잠금/CI는 보존한다.

## 변경 경계와 순서

core는 새 `backend/tests/web_crop_cycle_calculation_replay_smoke.py`와
기존 `web/e2e/real-cycle-crop-replay-smoke.mjs` **2파일**이다.
기존 브라우저 하네스의 기본 원 cycle 경로를 보존하고 명시 새 판본/경로를 선택한다.
새 하네스의 소유 기록 응답으로 연결을 먼저 검사한 뒤 실제 소유 SCRAM/보호 설정/TLS에서 실행한다.
수치 기준은 선행 불변 합성 계산의 원 sample/event이며 새 농장 등록/입력 hash와 그 관계를 기록한다.
시간 이동이 등록 농장 범위에 필요하면 명시적 UTC 이동만 허용하고 원 수치 비교에서 그 이동을 대사한다.
입력/결과 증명 발급과 실제 계산/DB 게시는 조회 전에 수행한다.

## 수용 기준

1. 실제 등록 농장25시간·11,400걸음/27시점/5사건과 확인 과거/빈 hold·출력0 완료를 준비한다.
   원 수치/단위·전역 index/UTC·farm/result/reference/manifest·두 validation 객체를 대사한다.
2. 실제 보호 설정 loader와 같은 jobs/farm/store/query의 HTTPS를 기존 App의 새 판본으로 읽는다.
   본문 전체30초/2MiB·no-store·현재7시점/2사건·브라우저 fetch/reader와 서버 요청 동시성1개를 검증한다.
   서버 요청 계측은 실제 ASGI 처리의 시작부터 최종 body/정리까지이며 socket 개수와 구분한다.
3. 읽기 parser/context/QC/RHS/advance/put/새 증명 발급을 금지하고 원 파일/DB 행을 보존한다.
   현재 권리 철회·계정 거부·유효 HMAC 변조에 이전 수치/장면을 제거하고 정상 재조회로 복구한다.
4. 실제 WebGL loss/restore·키보드/모바일/동작 줄이기·원 저장 시점 재생을 검사한다.
   observer/listener/timer/RAF/chart/GPU 객체 정리와 소유 PG/비밀/서버/브라우저/PID/data 정리를 기록한다.
   소프트웨어 GL 드라이버 경고와 주/자식 프로세스 메모리의 측정 범위를 그대로 남긴다.
5. 원 기본 브라우저 연결도 소유 기록 응답으로 회귀 확인한다. 실제 명령·종료/source/로그/hash·캡처와
   권리/서명 검사 증거 뒤에만 native와 새 웹 부모를 체크한다. 시험용 HTTP와 실제 TLS를 구분한다.

실험은 nice19·계산 child1개/PG1개/브라우저1개로 순차 수행한다. 원 과거 native의 약34분 실측을
근거로 첫 실제 실행의 관측 예산을60분으로 두며 HTTP/제품 한도를 늘리지 않는다.
관측 유실/timeout만으로 같은 계산을 재시작하지 않고 실제 handle/PID/terminal을 확인한다.
작은 native 연결3–5집중시간 잠정은 실제 실행 결과로 갱신한다.
전체166일 등록 부하/복원·생과/자원/Decimal 경제·외부 자료 확보/관문·최종 완료일은 별도다.
