# 계산 상태503와 확정 생장 조회 분리 — 2026-10-11

**P6a0 소프트웨어 회귀 수정은 수용했다. 실제 계산 중3D인 P6a와 사용자 활성화 P6b는 미수용이다. 두 기존 사용자 서버는 복구했다.**

[기계 증거](artifacts/crop-climate-joint-progress-prefix-retry-reference-20261011.json)의 SHA-256은
`45fd7e1a70bc39585056d366853d5ca33a566c80e0dbf0fac9038af270063f6f`다.
판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh`에서 수행했다. 실제 turn context의 모델·effort·시각·원 해시를 기록했으며 재귀 CLI는0이다.
이 기록은 [앞선 기동 준비](crop-climate-joint-prefix-browser-preparation-20261011.md)와 P5 증거를 수정하지 않는다.

## 수정과 소프트웨어 검증

실제 정상 계산 v8은 처음 두 progress503 때문에 prefix 조회가 지연됐고, 뒤늦은 event 조회는 terminal 전환과 겹쳐409가 됐다. 계산은 완료됐지만 running3D를 관측하지 못했다.

Core **bb67a60**, 제품1파일/회귀1파일을 수정했다.

- progress503에서도 별도 현재 권리·서명 검사를 하는 prefix API를 같은 순차 요청 사슬에서 조회한다.
- summary·events·samples를 모두 검증한 원자 snapshot만 교체한다. 상태 확인 시각이나 checkpoint를 만들어 채우지 않는다.
- 인증·권리 거부, cancel/terminal, 숨김·연결 변경, 늦은 응답의 기존 중단/삭제 동작을 유지한다.
- prefix 조회가 성공하면10초 후 재조회한다. 실패하면 기존 최대60초 backoff를 유지한다.

| 확인 | 실제 결과 |
| --- | --- |
| 기존 P5 빌드의503-first 회귀 | 실패 재현: 확정3D 요소 없음; 실제 CLI/guard exit1 |
| 새503-first·현재 권리 거부·progress403 회귀 |3개 통과 |
| 기존 P5/E8 포함 실제 Chromium |38개 통과, 각 선언된 시험마다 표준 Playwright CLI/새 브라우저 실행·실제 exit0 |
| 실행/prefix/replay의 웹 단위 시험 |303개 통과, skip0 |
| TypeScript·제한된 unminified Vite build·Python AST/JS 구문/CLI 옵션 |각 실제 exit0 |

고유 소프트웨어 시험은 **341개**다. 브라우저38개는 기록 응답을 제공하는 회귀 시험이며 실제 running backend 통과로 세지 않는다.
한 브라우저를38개에 재사용한 첫 실행은 단일 RSS567,848,960bytes에서 중단했고, 첫 분리 실행은 grep 지정 오류로 시험0/exit1이었다.
이를 통과로 세지 않았으며 각 시험의 실제 CLI 종료를 별도로 확인했다. 최종38개의 wall164.131초·단일/합산 RSS408,297,472/733,052,928bytes였다.
빌드 최고 단일 RSS511,324,160bytes를 포함해 최종 검사들은 단일512MiB/합산1GiB 상한 안이었다.
원본2,148항목·두 frozen source/자산 보존, FD4→4, 소유 프로세스/PG/passfile 정리를 확인했다.
최종 디자인 일치와 전체 CI는 이번에 검증하지 않았다.

## 실제 백엔드에서 남은 문제

reference Python/JS2파일은 같은 영속 저장소의 후보 API·독립 자동 worker·실제 제품 App의 HTTP/DOM을 기록하도록 확장했다.
응답은 원 Fetch Response를 그대로 반환하고 clone의 원 bytes를 별도로 보존한다. API mock·worker 정지 장벽·계산 지연·가짜 프레임은 사용하지 않았다.
이 reference는 조사용이며 P6 통과 구현으로 수용하지 않았다.

5173을 유지한 후보4회는 합산 RSS1,083,916,288–1,125,646,336bytes에서 중단했다.
Node/브라우저 GC, API threadpool1, Chromium low-end mode 실험은 이 병행 기동을 해결하지 못했다. API 제한과 low-end 옵션은 최종 reference에서 제거했다.
이후 두 사용자 서비스를 정확한 소유 프로세스 단위로 정상 종료하고 후보를 직렬 검증했다. 이전 실패로 남은 자체 작업은 실제 인증 API로 취소/종료를 확인하고 다음 접수를 진행했다.

새 빌드의 실제 정상 v9는 다음 원 응답을 기록했다.

1. 접수202 → progress503 → **prefix503**: UI가 상태 실패 뒤에도 prefix를 요청하는 수정 경로를 실제로 확인했다.
2. progress200 → prefix503 → progress200 → accepted prefix200.
3. **같은 selector의 events200** → samples503 → terminal progress200.

실제 event-prefix200은 처음 관측했다. 그러나 완전한 원 snapshot과 running WebGL은 관측하지 못했다.
브라우저 assertion은 `must observe an actual running prefix WebGL scene`에서 실패했고, 내부430MiB soft limit도 기록됐다.
외부 guard의 단일/합산 관측 최고는373,190,656/969,637,888bytes, wall116.499초, 실제 guard/browser exit1이었다.
자동 worker는 장벽 없이 chunk8로 계산했고 작업은 succeeded, 서비스 정상 종료0, cleanup 오류0이었다.
원 event의 terminal binary64/UTC 대사, hold/cancel/현재 권리/재접속의 실제 UI 검증은 완료하지 않았다.
따라서 **event200 관측만으로 P6a/P6b나 사용자 실시간3D를 수용하지 않는다.**

갱신 중인 저장소의 읽기 일관성/검증 비용과 페이지 사이 전환이 다음 조사 대상이다. 이번 응답만으로 samples503의 내부 원인을 확정하지 않는다.
실패 v1–v9의 source SHA·실제 종료·응답·정리 증거는 기계 기록과 저장소 밖 원 로그에 보존했다.

## 사용자 서버 복구 확인

| 주소 | 복구한 범위 | 확인 |
| --- | --- | --- |
| http://localhost:5173/ |기존 frozen166일 합성 생장/수확 재생 |인증 summary2개·원 wire 동일·원 HTML·5175 종료 |
| http://localhost:5174/ |기존 frozen 계산 상태 자동 조회·종료 후 저장3D |정상/hold/cancel 기존7응답·원 저장 bytes 동일·이전 토큰401·자동 worker 새 시도0 |

5173은 새 `run-v6/service`, 5174는 `service-v1/serve-v6`의 보호 접속 안내를 사용한다.
5174 토큰 만료는 **2026-10-12 12:43 KST**다. 새 토큰은 [web README](../web/README.md#joint-execution-user-preview)의 로컬 파일에서 확인한다.
이번 복구에서 새 계산 접수는0이며 P6 UI 빌드를 사용자 서버에 적용하지 않았다.
새 브라우저 재실행은 하지 않았고 인증된 API/원 HTML과 이미 수용된 frozen 자산을 확인했다.

독립 SCRAM 읽기 전용 검사로 기존 jobs95/job_events146/job_attempts8행의 해시·기존109파일·서명 키·DSN·현재 권리를 확인했다.
이번 조사에서 만든 자체 작업8개는 모두 terminal이다. 기존 원본2,148항목·두 source/자산을 보존했으며 보호 root4개를 새 실제 PID/start/boot identity로 갱신했다.
복구 query guard는 exit0·단일/합산 RSS136,744,960/651,231,232bytes·FD4→4·소유 잔여0이었다.
계속 실행하는 사용자 서버의 최종 exit는 아직 없으며 살아 있음을 확인했다.

## 다음 한 단계와 일정

**P6a1: 같은 accepted selector의 events200 이후 samples503 원인 분류**를 먼저 한다.
원 입력·결과·키·권리와 현행 관문을 보존하고, 쓰기와 겹친 어느 검증 단계에서 보류했는지 제한된 진단 기록으로 확인한다.
진단을 근거로 reader 또는 페이지 재조회 중 필요한 작은 수정만 분해한다. worker를 늦춰 관측 창을 만들지 않는다.

| 남은 단계 | 의존성·수용 기준 | 작업 추정 |
| --- | --- | --- |
| P6a1 원인 분류 | v9 원 trace/source; 실제503의 검증 지점·원본 보존·소유 정리 |첫 조사0.5–1시간 |
| 필요한 reader/재조회 수정 |분류 결과; 원자 판본·현재 권리·무잠금 읽기·회귀 |범위 확인 뒤 산정 |
| 실제 P6a 전체 경로 |수정된 빌드; 동일 selector sample/event200·원 수치/WebGL→terminal·hold/cancel/권리/재접속 |관측 성공 후 재검증0.5–1.5시간 잠정 |
| P6b 사용자 기동 |전체 P6a; frozen 후보·두 주소/키/원 결과 보존·접속 안내 |0.5–1시간 잠정 |

앞선 남은2–4시간 추정에는 이제 실제 페이지503의 해결 범위라는 미확정 의존성이 있다.
**실시간3D의 완료 날짜는 P6a1 분류 뒤 다시 산정한다.** 기록 응답 통과나 정상 계산 완료를 근거로10/11 완료를 약속하지 않는다.
운영 기반 완료 범위 `d19f7c0`는 유지하며 후속 구현은 생장→저장/3D→생산량·자원·경제 순서다.
독립 농장 자료 확보는 병행 의존성으로 남아 있다. 실제 crop Run0/독립 현장 자료0, G0–G4 `not_assessed`, 실제 생산·미래 마진·추천 hold와 remote 작업0을 유지한다.
