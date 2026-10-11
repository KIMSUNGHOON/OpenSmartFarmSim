# 5173에서 개발 진행 직접 확인 — 2026-10-12

상태: 로컬 사용자 화면 적용 수용. **http://localhost:5173/** 을 새로고침하면 상단에서 인증 없이 개발 단계·남은 작업·기록 시각을 확인한다. **http://localhost:5174/#crop-execution** 도 같은 기록을 제공한다.

## 원인과 수정

5173에는 현황 화면으로 가는 링크만 있었다. 사용자가 원래 주소에 머무르면 단계 기록을 직접 볼 수 없었다. 현재 서버의 원 계산도 이미 끝났으므로, 이 화면에서 계속 계산 종료를 기다리는 상황은 적절하지 않았다.

[기존 안내 조각](../web/preview-progress-notice.html)에 직접 표시 영역을 추가하고 [작은 조회 모듈](../web/preview-progress.js)로 같은 공개 `/development-status.json`을 읽는다. 별도 인증이나 새 작업을 만들지 않는다. 정상·실패 응답이 끝난 뒤15초 대기하고, 요청은5초 상한·16KiB 제한을 둔다. 실패 시 마지막 검증 기록을 유지하며 새 기록이30분 이상 없으면 명시한다. 기록 조회 시각과 실제 기록 갱신 시각을 구분한다.

5173 NGINX에는 개발 기록과 조회 모듈의 정확한 경로만 추가했다. 기존 SPA·JS/CSS·저장 결과·DB·API/worker는 유지했다. 기록의 완료/다음/대기는 개발 단계이며 계산 진행률이나 전체 제품의 완료 비율을 뜻하지 않는다.

## 확인한 결과

[기계 기록](artifacts/product-ui-inline-development-progress-20261012.json).

| 확인 | 결과 |
| --- | --- |
| 원64962 / 사용자 적용 | 실제0·0.872초. NGINX 설정 검사·동일 master의 PID/start_ticks/boot/pidfd HUP·두 주소200·같은 원 feed/올바른 MIME/no-store |
| 원1970 / 실제 Chromium | 실제0·39.123초. 두 화면의 원5단계·인증 없음·자동 조회 오류/마지막 기록 유지→새로고침 없는 복구·링크 이동 |
| 브라우저 전용 거부/오래된 기록 | HTML fallback·다른 schema·알 수 없는 필드·16KiB 초과를 거부. 오래된 기록을 표시. 격리된 브라우저의 응답 override이며 공유 기록/서버에는 쓰지 않았다 |
| 모바일/쓰기 | 두 화면390px에서 scrollWidth390. API쓰기0·인증된 상태 요청0·pageerror0 |
| 원8147 / 현재 실제 작업 조회·최종 보존 | 실제0·8.270초. 원 작업 `succeeded`/현재 checkpoint `completed`64/64·9시점/3사건. 새 계산 접수0 |
| 보존/WSL | 기존271계산파일·원본2,148항목·두 frozen source/자산·현재172자산/194source·보호4root 보존. FD4→4·소유/임시PG/passfile잔여0. 최대 단일247,996,416bytes/합983,502,848bytes로512MiB/1GiB 이내 |

현재 작업의 실제 조회 시각은2026-10-11T20:32:47.811121Z다.64/64는 기존128초 합성 작업이며 새 환기 모델의 사용자 적용이나 실제 농장 생산 계산이 아니다. 브라우저 검증 후 확인한 수정 내용으로 개발 기록을 게시했고, 두 주소와 저장 원본/handoff의 같은 SHA를 최종 보존 검사에서 대사했다.

같은 native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context를 기록했다. 재귀CLI·새 패키지·API/worker 재시작0이다. 전체CI·새 환기 모델3D·새 작물 계산·현장 검증은 이번 표시 수정에서 실행하지 않았다.

## 남은 작업과 일정

다음은 `crop-greenhouse-ventilation-web-terminal-3d`다. 새 결과 GET의 typed client를 기존 화면에 연결하고, 같은 result/UTC의 원108상태·25장부/10수지·환기 진단을 표·그래프·수치3D와 대사한다. 완료/보류·현재 권리 거부 시 장면 제거·기존 client 보존·실제 저장 응답/브라우저 검증을 통과해야 수용한다.

그 뒤 확정 부분 조회 API→계산 중3D→실제 정상/보류/취소/재접속→사용자 적용 순서다. [작업 분해](../tasks/plan.md#새-환기-모델의-화면-연결-순서)의 남은 **2–5집중작업시간**은 짧은 합성 모델 연결/적용에 한정된 추정이다. 전체 작기·생산/자원·경제·최종 제품 UI의 완료일은 미정이다. 실제 농장 Run/독립 국내 자료0, G0–G4 `not_assessed`와 실제 생산/미래 마진/작물 추천 보류는 유지한다.

## 복구 시 유지할 파일

private handoff의 `current_legacy_progress_navigation`은 적용된 별도 HTML entry·JS·NGINX 설정의 경로/SHA를 기록한다. `current_ui_development_status_feed.current_file`이 두 서버의 동일 공개 기록이다. frozen 원 index를 변경하지 않는다. 복구 시 해당 정확한 경로 alias와 `/`→`/index.html` 내부 이동을 유지한다. 이전 NGINX 설정과 HTML entry도 private 상태 디렉터리에 보존했다. 접속 토큰/권리/DB 키는 이 기록이나 공개 artifact에 넣지 않는다.
