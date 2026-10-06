# 긴 저장 계산의 현재 범위와 성장 연구 3D 화면

상태: **기록된 합성 응답의 화면 기능 로컬 수용·새 실제 DB/TLS/WebGL 경로 미수용**, 2026-10-06 KST.
화면5 core파일은 `6f0a083`, 공개 fixture/spec2 core파일과 화면은 `ac1ff7f`에 고정했다.
[불변 영수증](artifacts/web-crop-cycle-view-reference-20261006.json)에 코드·검사·출처 참조·화면 hash를 기록했다.
[현재 범위 계약](../contracts/web-crop-cycle-replay-v1.md),
[선행 client](web-crop-cycle-pages-implementation.md), [범위 helper](web-crop-cycle-window-implementation.md)를 따른다.

## 사용자가 확인할 수 있는 결과

기존 **08 성장 연구3D → 저장 결과 판본 → cycle v1**에서 긴 계산을 조회한다.
첫7개 시점만 읽고 다음 범위는 서버의 실제 `next_offset`, 이전 범위는 실제 방문했던 offset으로 다시 읽는다.
전체27시점/5사건과 현재 읽은 범위·UTC·부분 여부·계산 완료/보류를 구분한다.
사건은2개씩 별도로 조회하며 이때 기존 시점 장면을 지운다. 상한64/8과 서버30초/2MiB는 유지한다.

같은 저장 ID·농장·전체 참조·원 인덱스/UTC에서 기관량·LAI·50 C/N·16누적·4진단과
표·그래프·3D를 표시한다. 현재 시점 범위에서만 C/N 로그 비교 축을 계산하고 그 범위 안에서는 고정한다.
축이 범위마다 달라질 수 있음을 표시한다. 같은 LAI 한 면 면적과100 C/N mesh를 기존 도형으로 그린다.
자동 재생은 현재 범위의 원 시점만 선택하고 끝에서 멈춘다. 보간·생장식 재계산·임의 성장 애니메이션은 없다.

[실제 App 화면](artifacts/cycle-crop-desktop.png), [모바일](artifacts/cycle-crop-mobile.png),
[실제 빈 hold 응답 화면](artifacts/cycle-crop-empty-hold.png)을 확인할 수 있다.
[선택 범위 3D 확대 화면](artifacts/cycle-crop-selected-window-preview.png)은 같은 실제 컴포넌트를
임시 검토용 shell에서 캡처했다. 입력은 소유한 기록 합성 공개 응답이다.
[과거 hold 화면](artifacts/cycle-crop-past-hold-shape.png)은 **형식 시험용으로 만든 상태**이며 새로운 작물 계산이 아니다.
일반 데모 명령에 이 cycle fixture를 새로 넣거나 실제 저장 이력으로 등록하지 않았다.

## 통과한 검사와 보존

| 검사 | 최종 결과 |
| --- | --- |
| 현재 화면 Chromium | 16개/1.4분 통과, worker1·격리 profile |
| 기존 v1/v2/v3 Chromium | 3개/20.3초 통과 |
| 웹 단위 | 19파일·522개/6.08초 통과 |
| 타입/빌드 | 종료0, Vite645ms·기존500kB chunk 경고 유지 |
| 보존 | backend49개·선행 client/window7개 hash 동일 |

원25시간 계산에서 기록한27시점을 네 페이지7/7/7/6으로 선택하고2,700개의 C/N mesh 원량·단위·높이,
LAI 면적·원 표·분포/시간 그래프·누적/진단을 대사했다. 원5사건은2/2/1로 조회해 제거 전후 scalar와
50 C/N을 확인했다. 이 Chromium 시험은 기록된 공개 JSON을 반환한다. 새 실제 PG→TLS 연결 시험이 아니다.
기록의 실제 계산/HTTP 선행은 [별도 runtime 수용](api-crop-cycle-runtime-implementation.md)에 있다.

byte-short·이전 실제 offset·정상 빈 완료 형식/실제 빈 hold·소수 초 마지막 확인 진단의 분리,
403/404/422/503·혼합 참조·취소/늦은 전체 응답·ID/계정 변경·동작 줄이기·키보드·WebGL loss/restore를 확인했다.
형식용512시점을 복제한20범위에서 현재7개/사건0개·canvas1개/선택 C/N100개를 확인하고 화면을 해제했다.
실제 전체 작기 계산이나 renderer/observer/listener/timer의 전체 누수 감사 증거로 보고하지 않는다.

CPU4배 throttle의20회 선택 응답 최대 **442.275275ms**, 관측 JS heap 최대 **60,004,236bytes**다.
Playwright 입력·대기까지 포함한 emulator 관측이며 실제 저사양 기기나 WSL 전체 메모리가 아니다.
새 native child peak RSS는 이번 단계에서 측정하지 않았다. 임시 Vite5190과 시험 Vite5189를 종료하고
검토용3개 파일을 삭제했다. 이 단계에서는 PostgreSQL/농장 role을 만들지 않았다.

최초14통과/2실패는 CSS `zoom`을 실제 브라우저 확대처럼 이름 붙인 시험과 잘못된 버튼 이름이었다.
기존 suite 방식의200% 글자 확대와 실제 버튼 이름으로 수정해2개/24.1초를 통과했다.
후속19개 실행 도중 직접 source를 수정해 Vite가 페이지를 새로 연1실패/18통과도 보존했다.
최종 source를 고정한 새16개와 기존3개 실행은 모두 통과했다. assertion/timeout을 완화하지 않았다.

## 디자인·검토와 남은 의존성

`12ui-design`의 기존 시안/자산 재사용과 최종 실제 컴포넌트·원 LayerDoc 비교를 수행했다.
main24.7%·empty19.2%·past21.2%의 DOM 일치율은60% 기준보다 낮다. **pixel fidelity는 미수용**이다.
모든 close kit는 종료했고 새 구매0회다. 실제 제목/입력을 가짜38% 진행률·과학 도표에 대응시킨
낮은 일치 계획은 적용하지 않았다. 기존 유효 cutout4개·실제 수치·접근 가능한 조작은 유지했다.
기능 수용과 디자인 일치 수용을 분리했다.

현재 실제 Codex CLI `gpt-6.1-sol / xhigh`의 `2026-10-06T03:08:12.573Z` turn_context,
원 line hash와 자체 다섯 축 검토를 영수증에 기록했다. 재귀 CLI0회이며 독립 농장/제품 작업자 검토 증거가 아니다.
`d61bcb3` backend CI는 관측 시 p1완료·p0/p2실행 중·p3/p4/p5대기다.
현재 로컬 화면 판본의 hosted CI는 별도다. 실행 중인 backend를 취소할 새 push는 기다린다.

다음은 browser 자식의 남은2 core파일인 실제 smoke/native 시험과 생명주기·자원 검증이다.
수용 기준은 **새 실제 SCRAM 저장→표준 TLS→이 화면의27시점/5사건·각 페이지 경계·같은 ID/UTC/원량/mesh,
GET RHS0회·현재 권리 철회·계정 변경·hold/빈 출력·서버/DB/role/비밀·요청/renderer/차트/timer 정리**다.
기존 순서는 **생장 계산 → 불변 저장·같은 UTC3D → 실제 작기 부하/복구 → 생과·자원·Decimal 경제**다.
남은 실제 경로는 **2–3집중시간**, 하루4시간 기준 **2026-10-06–08 KST 잠정**이며 검증 실적으로 갱신한다.
전체166일 처리·생과 환산/자원 구매·수요/공급·미래 마진·농작물 추천의 완료 날짜는 아직 추정하지 않는다.
실제 품종/작기 입력·국내 독립 검증 자료·crop Run은0건, G0–G4는 `not_assessed`이며 해당 게시 조건을 유지한다.
