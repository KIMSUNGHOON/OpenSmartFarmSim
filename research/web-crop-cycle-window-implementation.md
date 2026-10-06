# 긴 연구 결과의 현재 범위와 직렬 조회 수용

상태: **범위 helper 로컬 수용, 화면/3D 수용 전**, 2026-10-06 KST.
`083baf0586315dad1f6f65f71dfab72efe60b859`의
[불변 영수증](artifacts/web-crop-cycle-window-reference-20261006.json)을 고정했다.
[선행 client](web-crop-cycle-pages-implementation.md)와
[범위/3D 계약](../contracts/web-crop-cycle-replay-v1.md)의 첫2 core파일을 구현했다.

`cycleCropWindow.ts`는 같은 저장 ID·농장·전체 참조와 원 UTC/index의 선택을 유지한다.
현재 sample64개 또는 event8개 이하 한 페이지, 요약, 선택만 제공하며 이전 원 배열을 쌓지 않는다.
offset/실제 count/next·현재 UTC 범위·부분 표시와 전체 계산 completed/hold를 구분한다.
이전 조회는 실제 읽었던 정수 offset 목록을 사용해 다시 요청한다.
완료 출력0과 실제 빈 hold에는 frame을 생성하지 않는다. hold 진단은 요약에 따로 남긴다.

조회/범위 이동은 이전 sample·선택·요약 숫자를 먼저 지운다.
이전 요청의 AbortSignal을 취소한 뒤 전체 응답이 종료될 때까지 기다리고 새 요청을 시작한다.
선택/계정 변경·취소·권리/참조 오류와 늦은 응답은 이전 값을 복원하지 않는다.
대기 중 대체된 선택은 HTTP를 시작하지 않고, dispose 이후 상태 알림도 없다.
재진입 callback이 pending owner를 덮어쓰지 않도록 promise를 알림 전에 소유한다.
도형 척도·renderer/재생 timer는 다음 화면/실제 브라우저 단계에서 수용한다.

| 통과한 검증 | 실제 결과 |
| --- | --- |
| 새 범위 집중 | 19개 통과 |
| 웹 전체 | 19파일·522개/6.76초 통과 |
| 타입 검사/빌드 | 종료0·Vite875ms, 기존 chunk 경고 유지 |
| 보존 | 선행 client5개·backend49개 source hash 동일 |

원27시점/5사건의 공개 DTO와 byte-short next/이전·선택 UTC·마지막 부분 범위,
모든 오류의 숫자 삭제·완료 빈 출력·실제 빈 hold를 대사했다.
형식용40회 next/previous에서 현재 원 배열만 유지했다. crop 계산이나 브라우저 부하 측정은 아니다.
실제 API factory를 사용한 취소/계정 변경 시험은 요청 시작 promise와 전체 종료를 기다려
동시 HTTP1개·늦은 게시0을 확인했다. 최초 네 실패는 한 microtask 뒤 요청이 시작됐다고
가정한 시험 setup이며 명시적 시작 증거로 수정했다. 경로를 느슨하게 만들지 않았다.
현재 실제 `gpt-6.1-sol / xhigh` CLI 자체 검토/line hash를 기록했고 재귀 실행0회다.

다음은 화면/CSS·App·Scene/Chart 범위 문구의5 core파일과 별도 실제 PG/TLS/WebGL4 core파일이다.
남은 작업량은 **화면1–2 + 실제 경로/검증2–3 =3–5집중시간**, 하루4시간 기준
**2026-10-06–08 KST 잠정**이다. 실제 원 mesh/표/UTC·권리·정리/자원 실적 뒤 날짜를 갱신한다.
새 화면/브라우저·3D를 이번 helper 검증으로 수용하지 않는다.
현재 hosted runtime SHA는 웹 audit 실패/백엔드 진행 중이며 후속 잠금/클라이언트 판본은 별도다.
실제 품종/작기 입력·독립 국내 자료·crop Run0건과 G0–G4·생과/자원/경제 보류는 유지한다.
