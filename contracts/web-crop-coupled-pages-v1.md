# 50구획 연구 결과의 웹 페이지 조립 — v1

상태: **로컬 페이지 조립 수용; 새 장면/브라우저 미수용**.
[135개 집중·기록된 공개 TLS bytes 대사 1개](../research/web-crop-coupled-pages-implementation.md)를 통과했다.
부모는 [같은 시점 연구 3D](web-crop-coupled-replay-v1.md),
선행은 [페이지 API](api-crop-coupled-replay-v1.md)다.
현재 CLI gpt-6.1-sol / xhigh(2026-10-04T22:05:49.804Z)에서 판단했고 재귀 호출은 없다.

첫 작은 구현은 새 decoder/페이지 모듈·집중 시험 각 한 파일과 기존 `api.ts`의
선택 메서드/외부 AbortSignal 연결이다. 이 단계는 화면·도형·브라우저 수용이 아니다.

- API의 닫힌 필드·정확한 50개 N/C·단위·판본/해시·연구 범위를 검증한다.
- UTC 검증 뒤 마이크로초 BigInt로 순서를 비교한다. Date.parse의 밀리초 절삭으로
  정수 초 sample과 .000001Z hold를 같은 시각으로 처리하지 않는다.
- 최대 8개 sample 페이지를 순차 읽는다. ID/농장/저장 UTC·전체 manifest/hold와
  총수를 고정하고 offset/limit/next_offset·순서·시작/끝을 검사한다.
- 첫 event 페이지는 한 번만 보존한다. 이후 sample 요청은 event_offset=total로
  빈 사건 페이지를 요청한다. 사건 탐색은 sample_offset=total로 빈 sample 페이지를
  읽고 같은 결과의 별도 event 페이지로 제공한다.
- 조립 전에는 완성 결과를 반환하지 않는다. 확인한 페이지/시점 수만 진행 상태로
  전달한다. 다른 등록/계정의 화면 교체와 이전 결과 제거는 후속 React 단계에서 검증한다.
- 기존 request의 2 MiB·30초/요청·no-store·동일 origin Bearer 정책을 사용한다.
  외부 취소는 fetch/body 수신에 전달하며 선행 취소·늦은 응답·페이지 사이 취소·오류는
  다음 요청이나 완성 결과를 만들지 않는다. 타이머/Abort listener를 정리한다.
- 조립 결과의 수치·단위는 복사/보존한다. 수지·생장식·미래 상태를 계산하지 않는다.

수용은 혼합/누락/중복/순서·50배열/단위/실제 달력·fractional hold·빈 과거,
512 sample/128 event의 페이지 경계·모든 응답 거부 코드·2 MiB/UTF-8/취소/30초와
기존 request/작물 v1 회귀다. 실제 이전 TLS 응답을 decoder에 대사한 사실은
재사용된 공개 합성 bytes의 수용이며 새 브라우저/실제 서버 실행으로 세지 않는다.
