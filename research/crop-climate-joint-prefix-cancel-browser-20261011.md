# 계산 중 실제 WebGL 취소 수용과 두 화면 복구 — 2026-10-11

**실제 브라우저의 계산 중 원 수치3D → 취소 수락 → worker canceled·장면 제거·결과 미생성과 두 기존 화면 복구를 통과했다. 같은 제품 코드의 선행 정상/hold 증거와 합쳐 P6a를 수용한다. 사용자5174 활성화 P6b는 아직 미완료다.**

[기계 증거](artifacts/crop-climate-joint-prefix-cancel-browser-reference-20261011.json)의 SHA-256은
`4f80ecfaceeb3c68c096c270dc7093758b9c16f76373981fa21db774a393dc06`이다.
native Codex CLI `gpt-6.1-sol`/`xhigh` 실제 context SHA는
`030abfa51121481eb8ad9f59c870618f78d4f9b012945966b489eb2931481968`이며 재귀 CLI 실행은0이다.
제품 core `89c23d86f484e03462f8758dd180234593143b00`의 계산/reader/UI는 변경하지 않았다.
reference JS에서 취소 경로의 사전 screenshot 관측만 제외하고 이를 결과에 기록했다. 정상/hold screenshot과 모든 수용 assertion은 유지했다.

## 실제 취소 경로

원 tool9884의 실제 tool/guard/browser/service 종료가 모두0이다.
실제 SCRAM/TLS API·자동 worker(chunk8)·제품 App/Chromium이며 API mock·worker 정지/지연은 없다.
빈 화면에3D가 없음을 확인하고 새 합성 요청을 접수했다. 일시503 뒤 같은 공개 선택자의 사건/생장200을 읽고,
원 UTC `2026-10-01T00:00:00.123456Z`의 WebGL109회 그리기를 관측했다.
표·그래프·LAI·50구획의 C/개수·온도·사건 시각을 해당 원 응답과 대사한 뒤 실제 UI 취소 버튼을 눌렀다.

| 확인 | 결과 |
| --- | --- |
| UI 취소 | 1회,200·`cancel_requested=true`/`cancel_accepted=true` |
| 독립 worker | 앞선 busy 재시도2회 뒤 attempt3 `canceled` |
| 화면 | prefix 장면 제거, 완료 결과 열기 버튼 없음 |
| 같은 DB 사후 검사 | canceled; 해당 job의 결과·publication·성공/결과 사건 모두0 |
| page 오류 / API mock / worker 정지·지연 | 모두0 |
| 원본/자산·소유 정리·FD | 보존 통과, 잔여0,4→4 |

guard89.153초,0.25초 관측 단일/합산 peak RSS368,873,472/965,967,872bytes로512MiB/1GiB 이내다.
브라우저는 예측/보간 프레임을 만들지 않았다. 취소 전 PNG는 생성하지 않았으며 실제 DOM·WebGL·원 HTTP 응답의 관측으로 검증했다.
선행 [정상/hold의 실제 PNG와 원 terminal 대사](crop-climate-joint-prefix-browser-v5-20261011.md)는 유지한다.
이 결과를 일반 성능 보장이나 전체 작기/G4 수용으로 확대하지 않는다.

## P6a 수용 범위

선행 정상49259/hold7699와 이번 취소9884의 backend/app203·web/src115파일이 모두 현재 checkout과 같다.
각 경로의 reference Python/JS SHA는 별도로 보존했다. 최종 helper에서 정상/hold를 다시 실행했다고 주장하지 않는다.
정상/hold의 원 prefix→terminal·빈/재접속, 정상의 현재 권리 철회/장면 제거·원 파일 복원,
이번 취소의 실제 수락/worker 확인·DB 결과 없음과 아래 복구를 합쳐 P6a의 소프트웨어 범위를 수용한다.
선행 [API 취소 진단](crop-climate-joint-cancel-request-diagnosis-20261011.md)과 [reader v5 고유267개](crop-climate-joint-prefix-read-cost-implementation-20261011.md)의 범위도 유지한다.

준비 중 시스템 Python의 FastAPI 누락은 기존 backend 가상환경 사용으로 해결했으며 당시 중지 신호는 전송되지 않았다.
복구 중 옛 frozen ready 형식에 새 prefix 필드가 있다고 가정한 출력 오류도 있었다. 기존 형식/서비스는 유지하고 실제 operator 설정과 현재 identity를 사용했다.
두 오류를 제품 실패나 통과한 guard로 세지 않는다.

## 두 사용자 화면 복구

활성/대기 공동 계산0을 확인한 유지보수 창에서 정확한 v8 소유 프로세스만 pidfd SIGTERM으로 정상 종료했다.
원 도구62256/73699 모두 exit0이며 원본2,148항목·두 frozen source/자산은 보존됐다.
후보 종료 뒤 원 frozen 제품을 `run-v9`/`serve-v9`로 다시 기동했다. 지속 서버74111/35477은 실행 중이며 종료 검증으로 세지 않는다.

legacy 인증 원 생장/수확 probe65661은 exit0/14.824초다.
joint 원7응답의 실제 TLS 조회6307과 SCRAM 읽기 전용 DB/파일 검사75097은 모두 tool/guard exit0이다.
유지보수 전 jobs109/job_events319/job_attempts32행과381파일·원 키/DSN/현재 권리를 그대로 보존했다.
옛 token401·새 worker 시도0을 확인했다. 취소 job의 결과·게시·성공/결과 사건0도 같은 DB에서 확인했다.
2026-10-11 **20:03 KST**에5173/5174의 HTTP200·원 HTML 해시, 보호 root4 생존과 임시5175 폐쇄를 재확인했다.

새 접속 파일은 [web README](../web/README.md#joint-execution-user-preview)의 `run-v9`/`serve-v9`다.
현재5173은 완료166일 재생,5174는 같은 사용자 DB의 진행/확정 checkpoint polling·종료 후3D다.
**현재 사용자5174의 계산 중3D는 계속 비활성**이며 별도 개발 DB의 계산은 이 화면에 자동 노출되지 않는다.

## 다음 한 단계 — P6b 사용자 활성화

수용된 backend/web을 고정한 사용자5174에서 명시 prefix·자동 worker를 기동하고,
실제 장벽 없는 계산 중 같은 원 UTC/수치/WebGL·terminal, 현재 인증·기존 결과/키·권리와 두 주소 보존을 확인한다.
WSL 유지보수/복구 창과512MiB/1GiB 기준은 유지한다. 통과한 뒤 접속 안내를 갱신한다.
이번4회 guard 합127.941초와 legacy probe14.824초이며 준비·분석·복구 기동·문서/commit은 별도다.
P6b의0.5–1집중시간은 조건부 추정이며 실제 자원/현재 결과·복구 수용 전 완료 시각은 확정하지 않는다.
전체 CI·remote·새 제품 build·전체 작기 재계산·P6b는 실행하지 않았다.
최종 디자인/전체 작기·실제 농장 Run/국내 독립 자료0·G0–G4 `not_assessed`와 생산/미래 마진/추천 보류는 유지한다.
