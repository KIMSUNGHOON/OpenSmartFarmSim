# 수확 조회의 본문 수신 전 연결 종료 — v1

2026-10-09, native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [전체 실제 API/대표3D](../research/crop-harvest-full-view-20261009.md)의 조기 취소500을 보완한다.
core4는 이 계약, `backend/app/api_crop_harvest_route.py`,
`backend/tests/test_crop_harvest_disconnect.py`, `research/crop-harvest-disconnect.py`다.

기존 bodyless GET가 `request.stream()` 중 `ClientDisconnect`를 받으면
기존422 `invalid_request`를 반환하며 현재 query를 열지 않는다. 이 예외만 명시적으로 처리한다.
작업 취소를 성공/검증 오류로 바꾸지 않는다. 입력/manifest/decoder/모델·계수/권한·정상 응답은 유지한다.

[ASGI disconnect 계약](https://asgi.readthedocs.io/en/latest/specs/www.html#disconnect-receive-event)에 따라
닫힌 client가 오류 응답을 받았다고 주장하지 않는다. 실제 pinned Uvicorn의 ASGI 종료/서버 오류와 별도 정상 wire를 관측한다.
[Starlette 요청 구현](https://github.com/Kludex/starlette/blob/main/starlette/requests.py)과
설치된 lock 판본의 `Request.stream`/Uvicorn `receive`를 대조해 원인을 확인한다.

## 수용

1. ASGI의 즉시 disconnect/빈 미완료 조각 뒤 disconnect는422, query0이며 task cancellation은 전파한다.
2. 같은 원 전체 저장 결과를 정상 SCRAM/runtime/HTTPS로 복원한다. 인증된 GET의 Content-Length1에
   body0을 전송하고 서버 receive 진입을 확인한 뒤 실제 TLS client를 닫는다. 원 코드500→수정422,
   실제 `http.disconnect`/query0·서버 예외 없음과 정상 summary/첫64행 wire/원 저장값을 확인한다.
3. 현재 Scope403/다른 계정404/현재 표시권422·복원, 기존 늦은 정상 응답 정리 증거를 유지한다.
   조회 RHS/행 생성/게시/proof0, DB counts·원본/manifest·FD identity·검증 PG/소유 정리를 확인한다.
4. 실제 원 명령 종료,512MiB/1GiB 관측 상한과 기존 사용자5173/고정 source/dist 보존 뒤 체크한다.

이 수용은 전체 수확 사용자 미리보기 전환이나 실시간 U3, 실제 자료/작물 관문 수용이 아니다.
