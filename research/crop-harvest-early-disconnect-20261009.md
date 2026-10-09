# 전체 수확 조회의 조기 연결 종료 보완 — 2026-10-09

native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[core4 계약](../contracts/crop-harvest-early-disconnect-v1.md)의 구현 `d92ad73`과
[불변 수용 기록](artifacts/crop-harvest-early-disconnect-reference-20261009.json)을 대조했다.
선행 [전체 API/대표3D](crop-harvest-full-view-20261009.md)의 본문 수신 전 취소500을 보완했다.

## 원인과 수정

설치된 Starlette의 `Request.stream()`은 실제 `http.disconnect`를 받으면 `ClientDisconnect`를 발생시킨다.
기존 수확 route의 body 검사는 예외 처리 밖에 있어500이 발생했다.
본문을 받는 좁은 범위에서 이 예외만 기존422 `invalid_request`로 처리하며 결과 query를 열지 않는다.
작업 cancellation은 전파한다. 모델/계수·결과/manifest/decoder·권한·OpenAPI·정상 응답은 유지했다.

[ASGI disconnect 계약](https://asgi.readthedocs.io/en/latest/specs/www.html#disconnect-receive-event)과
[Starlette 공식 구현](https://github.com/Kludex/starlette/blob/main/starlette/requests.py)을
설치된 lock 판본의 `Request.stream`/Uvicorn `receive`와 대조했다.
닫힌 TLS client가422를 받았다는 주장이 아니다. 실제 서버 ASGI 종료와 별도 정상 client wire를 확인했다.

## 통과한 검증

- 원9983 종료1: 즉시/빈 미완료 조각 뒤 disconnect의2개 RED, cancellation1개 통과.
- 원26424 종료0: 같은 원 전체 저장 DB·정상 보호 runtime에서 실제 TLS GET의 Content-Length1/body0,
  서버 receive 진입 뒤 client close로 `http.disconnect`/`ClientDisconnect`/ASGI500을 재현했다. 수용 성공이 아니다.
- 원85391 종료0: 새3개와 기존 route/공개 투영의 집중149개/19.77초 통과.
- 원89030 종료0: 같은 원 DB/runtime/TLS의 조기 종료422/64bytes·query0/서버 예외0과
  정상 summary/첫64행/현재 Scope403·다른 계정404·표시권422/복원으로 실제7응답을 확인했다.
  원 summary·첫64행 wire SHA/bytes는 선행 수용과 같고 최대 정상10.798초/486,219bytes다.
  전체37.418초·native FD3→3·DB counts 불변·조회 RHS/생성/게시/proof0·공유 권리 파일 변경0이다.
- 별도 root 도구 `8effa8` 종료0: 현재 source1,652항목/원본2,148항목·원 종료/원 wire/권한·FD4→4,
  소유 PG/HTTPS/controller 정리와 기존 사용자 미리보기/source/dist·frontend200을 확인했다.
  검증용 정지 DB와 네 임시 디렉터리83,936,616bytes를 제거했고 원 backup/keys/artifact는 유지했다.

지정0.25초 관측의 모든 실행은 단일512MiB/명시 소유+보호 트리 합1GiB 안이다.
집중 검사 peak215,236,608/520,167,424bytes, 최종 native141,307,904/486,625,280bytes다.
전체 WSL/일반 브라우저/배포 용량 수용은 아니다. 변경 없는 WebGL·웹 빌드/넓은 회귀는 반복하지 않았다.
이전 전체 대표3D 증거는 유지하며 이번 새 증거는 조기 body 종료와 정상 현재 조회의 좁은 범위다.

## 다음 사용자 확인 단계

`http://localhost:5173/`은 완료 합성166일/47,809시점의 기존 생장 조회를 유지한다.
이번 수정과 전체 수확은 아직 그 고정 미리보기 서버에 배포하지 않았다. 실시간 U3도 미구현이다.
다음은 수정된 고정 source의 전체 수확 동시 기동·원 summary/page/현재 권한 확인·접속 안내와
기존 소유 서비스의 안전한 전환이다. 실제 TLS37.418초/앞선 대표 WebGL225.535초를 근거로
0.5–1.5집중시간을 잠정 잡으며 추가 실패가 있으면 갱신한다.
그 뒤 상위 mass-load/replay 수용을 평가하고 기후/물·양분/구매 에너지→사용자 실행/Decimal 경제로 진행한다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold다.
