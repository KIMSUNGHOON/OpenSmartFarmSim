# 긴 작물 연구 결과의 같은 UTC 성장 3D — v1 후보

상태: **설계 후보·미구현**, 2026-10-06 KST. 선행은
[cycle API](api-crop-cycle-pages-v1.md)와 [새 client](web-crop-cycle-pages-v1.md)의 실제 수용이다.
현재 Codex CLI `gpt-6.1-sol / xhigh`의 turn_context
`2026-10-06T00:06:54.191Z`, 원 line SHA
`64f429fe2ffbde6de414f57f07bc72bbfb9f44131de1f5313de3b117e96e877c`에서
기존 startup 화면·도형·그래프와 새 공개 DTO를 대조했다. 재귀 CLI 실행은0회다.
이 계약 작성은 새 화면·실제 작기·품종/G0–G4 수용이 아니다.

## 표시 범위와 원값

summary의 전체 저장 sample/event 수와 **현재 읽은 범위**를 따로 표시한다.
최대131,072 sample을 모두 보관·렌더링한 뒤 첫 화면을 만들지 않는다. 한 sample page
최대64개와 한 event page 최대8개, summary/선택 sample만 화면에 보관한다.
페이지의 offset/실제 record 수/next_offset으로 범위를 표시하고 원 UTC·양·단위를 보존한다.
이전 조회 offset의 정수 목록은 보관할 수 있지만 이전 sample 배열·차트·mesh는 누적하지 않는다.
다음 범위는 반환된 next_offset, 이전 범위는 실제 조회했던 offset으로 다시 읽는다.
byte budget으로 짧아진 페이지를 요청 limit까지 채워 만들지 않는다.

한 시점의 표·기관량/16누적·4진단·50 C/N·LAI·그래프 선택선·3D는
`result_id + farm + 전체 reference + sample.at`를 함께 사용한다. 재생은 현재 범위의
원 sample 인덱스만 이동한다. 다음 범위의 성공 응답을 검증하기 전에는 이어서 재생하지 않는다.
자동 범위 수집·보간·생장식 재계산·미래 상태·생과 kg 환산을 하지 않는다.
완료 결과의 선택 출력0개도 정상적인 빈 출력으로 표시한다. 작기 시작/끝의 frame을 만들지 않는다.
hold는 확인 과거만 탐색하며 last_confirmed/소수 초 UTC는 별도 진단으로 남긴다.
현재 범위가 부분이라는 사실과 전체 계산의 completed/hold 상태를 혼동하지 않는다.

## 비교 척도와 실패

기존 startup의 C/N 로그 비교식과 LAI 한 면 면적 표현을 재사용한다. 비교 척도의
최솟값/최댓값은 **현재 sample 범위**에서만 계산하고, 같은 범위의 모든 frame에서 고정한다.
장면·구획 분포 그래프에는 현재 offset/끝 index·UTC 범위와 로그 C/N 축을 표시한다.
범위를 바꾸면 축도 바뀔 수 있음을 알린다. 전체 작기의 극값을 계산했다고 표시하지 않는다.
시간 그래프도 현재 원 sample만 그리며 빈 출력은 그래프/3D 없이 표시한다.
기존 v2/v3의 전체 저장 범위 척도·문구·계산 의미는 보존한다.

조회·범위/계정/ID 변경·취소·권리 실패에는 이전 sample/장면/재생 timer를 지운다.
오래된 응답은 epoch/선택 참조로 거부하며 새 범위를 이전 값으로 복원하지 않는다.
한 화면에서 원 HTTP 요청은 한 번에 하나다. 이전 요청의 취소·settlement를 확인한 뒤
다음 요청을 시작하며 표/사건 조회도 같은 직렬 처리를 따른다. summary와 각 페이지의
동일 참조를 확인하고 응답 후 취소/선택을 다시 검사한다. 서버 권리 거부 시 표시를 보류한다.
이미 읽은 화면에 현재 권리가 계속 유효하다는 보장은 하지 않으며 재조회 때 다시 검사한다.

연구/미게시/합성/품종 미검증/관문 미평가와 명시적 착과·빈 sink 유보·전환 오차의
제약은 계속 표시한다. 도형은 수치 모식도이고 실제 키·열매 크기/개수·숙기·수확량이 아니다.
WebGL 실패/loss는 같은 원값의 표·그래프로 대체하며 복구 때 현재 sample만 다시 그린다.

## 작은 구현 순서와 수용

1. **`web-crop-cycle-window` — 상태/범위 helper와 집중 시험(2 core파일).**
   summary/reference·offset/next·hold/출력0·부분 표시/이전 실제 offset·선택 UTC를 검증한다.
   byte-short·혼합 참조·잘못된 순서·범위 변경/취소·직렬 요청/늦은 응답을 실제 기록 DTO로 시험한다.
   형식용 큰 total fixture는 생장 계산으로 보고하지 않는다. 같은 model/profile/원값은 불변이다.
2. **`web-crop-cycle-view` — 새 화면/CSS·App 연결·기존 Scene/Chart의 범위 문구(5 core파일).**
   첫 조회와 현재 범위 선택·이전/다음·사건 범위, 같은 UTC·C/N/LAI·표/누적/진단,
   현재 범위 척도·빈 완료/과거·빈 hold·권리 오류를 연결한다. 기존 디자인/자산을 사용한다.
   `12ui-design`의 기존 화면 확장·원 시안 비교 절차와 브라우저 검증을 적용한다.
   functional 검증과 pixel fidelity는 별도로 보고한다. 이 구현만으로 replay 부모를 체크하지 않는다.
3. **`web-crop-cycle-browser` — 공개 fixture·집중 browser spec·실제 smoke·native test(4 core파일).**
   실제 SCRAM 저장→표준 TLS→WebGL의 원27시점/5사건, 페이지 경계와 같은 ID/UTC/원량·
   C/N mesh/LAI 면적을 대사한다. GET RHS0회·현재 철회/계정 변경·hold/빈 출력·늦은 응답,
   모바일/200% 확대·키보드·동작 줄이기·WebGL loss/restore를 검사한다.
   별도 형식 fixture의 많은 범위 이동에서 retained 원 배열64/8 이하·선택 C/N mesh100개와
   단일 canvas, 이전 renderer/차트/observer/listener/timer/요청 정리를 확인한다.
   CPU4배 throttle의 입력 반응 시간과 JS heap/시험 child peak RSS·렌더링 객체 수를 실측한다.
   관측 조건/값을 기록하며 emulator를 실제 저사양 기기나 WSL 전체 메모리로 보고하지 않는다.
   원 fixture 반복을 실제 전체 작기 계산으로 표시하지 않는다. 실제 DB/role/비밀/server 정리까지
   확인한 뒤 세 자식과 replay 부모의 체크를 갱신한다.

사용자가 확인할 산출물은 현재 읽은 범위/UTC가 표시된 실제 화면, 원값·mesh 대사 기록과
자원/정리 증거다. focused unit/typecheck/build·집중 Chromium·실제 native 경로가 필요하다.
새 framework/상주 service/계수·농장 자료 확보는 이 합성 연구 화면 개발의 선행이 아니다.
실제 품종/작기 입력·독립 국내 검증 자료0건과 생과/자원/경제·예측/추천의 외부 의존성은 유지한다.
client2–3시간과 별도 화면/실제 경로4–6시간의 잠정 추정은 실제 수용 실적으로 갱신한다.
