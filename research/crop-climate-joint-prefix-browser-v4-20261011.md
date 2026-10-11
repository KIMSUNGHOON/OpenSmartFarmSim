# v4 실제 브라우저와 종료 전환 진단 — 2026-10-11

**P6a 실제 계산 중 WebGL과 P6b 사용자 적용은 미수용이다. 두 기존 사용자 화면은 복구·검증했다.**

[기계 증거](artifacts/crop-climate-joint-prefix-browser-v4-reference-20261011.json)의 SHA-256은
`c24617b4ee18167b1655ea93a8fc4d69e357936a9a89068899bca2bf50952912`이다.
판단은 현재 native Codex CLI `gpt-6.1-sol`/`xhigh`에서 수행했다. 실제 turn context 해시는
`89678cb8368aa10639d20235d8f32c2c0af23c572c360bf42c3e453e734f2db6`이며 재귀 CLI 실행은0이다.
[전진 읽기 v4의 기존 고유265개 수용](crop-climate-joint-prefix-forward-read-implementation-20261011.md)을
실제 사용자 브라우저 수용으로 확대하지 않는다. 제품 reader/HTTP·수치·writer·웹 화면 코드는 이번에 변경하지 않았다.

## 실제 제품 브라우저

메모리 제한 때문에 두 원 서비스의 진행 중/대기 공동 계산0을 확인하고 정상 종료했다.
원 foreground30865/60788의 실제 exit0과 모든 기존 root 종료를 확인한 뒤 후보를 기동했다.
기존 P6a0 빌드의171자산 해시와 웹 소스 pin을 대조했다. 차이는 설명 문서 `web/README.md`뿐이었다.

원 실행73518은 실제 SCRAM/TLS·독립 자동 worker(chunk8)·제품 App/Chromium을 사용했다.
API mock·worker 정지/지연·임의 생장 프레임은 없다.

| 관측 | 결과 |
| --- | --- |
| 공개 접수 |202 |
| 확정 요약/같은 선택자의 사건 |200/200 |
| 같은 선택자의 생장 페이지 |503 |
| 계산 중 WebGL |관측0, assertion 실패 |
| 계산 작업/후보 서비스 |succeeded/exit0 |
| 실제 browser/외부 guard |exit1/exit1 |

원 브라우저 기록에서 사건 응답은08:01:05.072 UTC, 생장503은08:01:15.869 UTC다.
뒤의 정상 진행 응답에는 작업 종료 시각08:01:12.184740 UTC가 있다.
생장 요청과 종료 전환이 겹쳤지만 **이 추적 없는503의 정확한 내부 거부 줄은 확정하지 않는다.**
내부430MiB soft limit도 기록됐다. 외부0.25초 관측 최고 단일/합산은402,599,936/963,039,232bytes이며
512MiB/1GiB 이내였다. 두 관측을 하나의 실패 원인으로 단정하지 않는다.

## 같은 v4의 API 요청 순서 진단

브라우저를 제외하고 실제 SCRAM/TLS와 별도 unpaused worker에서
진행→공개 요약→같은 선택자 사건→생장 순서를 추적했다. 두 사용자 서비스를 보호한 별도 scratch PG다.
요청 순서를 확인한 진단이며 전체 UI의 타이머·오류 상태 전이를 재현하는 시험은 아니다.

최종 원88744는 **집중 진단1개 통과**, 모든9요청의 trace·observer 오류0·worker exit0·원 terminal summary bytes 일치를 확인했다.
조회 중 계산 호출은0이다. 이는 API 진단 수용이며 WebGL이나 전체 P6 수용이 아니다.

- 요약200의 계측 시간22.109초, 사건200은21.696초였다.
- 뒤의 생장409는 `read:386`의 `JointPrefixSelectionConflict`다. 해당 요청의 실제 DB 상태는 이미 succeeded였다.
- 요약503 한 건은 첫 확정 publication이 추가되는 `read:400`의 빈 결과 bundle 변경 검사였다.
- 수용 요약/사건 각각 `_current`6회에7.777/7.665초, `_refresh`에는6.405/6.270초가 누적됐다.
  **이 수치들은 중첩 호출을 포함하므로 서로 더하지 않는다.** 전체 병목 함수를 아직 특정하지 않았다.
- 계측은 API 스레드에만 적용했고 worker는 추적·지연하지 않았다. 계측 시간이 일반 사용자 성능을 보장하지 않는다.

앞선 진단90160/70328은 trace coverage assertion 실패다. 70328의 원 기록을 보존해
비공개 HEAD의 `custody_sequence`를 공개 `publication_sequence`로 읽은 observer 오류를 확인했다.
이 오류는 해당 진단의422와 이후 trace 누락을 만들었다. observer가 제품 예외를 만들지 않도록 격리하고
올바른 필드와 오류0/전 요청 coverage를 최종88744에서 확인했다.
이 원인 설명은 **이번 진단기에만 해당하며 과거 미추적422의 원인을 설명하지 않는다.**

기동6298/47265도 각각 과거 시험 이름 충돌/유지보수 이전 작업을 소유 작업으로 분류한 assertion 실패였다.
브라우저/새 계산 시작 전 실패로 수용하지 않는다. reference에는 경로 해시를 포함한 고유 실행 이름,
기존 run의 기동 전 거부, baseline 작업의 정리 제외를 추가했다. 최종 실제 기동에서 이 경로를 확인했다.

## 사용자 화면 복구

5173은 frozen166일 재생, 5174는 frozen 상태/확정 checkpoint 자동 조회·종료 후3D로 복구했다.
두 HTTP200/원 HTML 해시, 인증된 기존 공동 결과7응답·기존 생장/수확 summary 원값,
이전 token401·복구 worker 새 시도0을 확인했다. 새 안내는 [web README](../web/README.md#joint-execution-user-preview)다.

유지보수 직전 jobs103/job_events232/job_attempts19행과252파일, 키·DSN·현재 권리 보존을 확인했다.
실제 수는 기계 증거의 `restoration.row_counts/files_preserved`를 기준으로 한다.
원본2,148항목·두 frozen source/자산·보호 root4를 모든 최종 guard에서 보존했다.
FD4→4, 소유 프로세스/PG/passfile/임시 PG 잔여0이다. 계속 실행하는 사용자 세션74892/21652는 최종 종료로 세지 않는다.

## 다음 구현과 일정

다음은 **P6a2c1: 같은 HTTP 요청의 함수별 비용 프로파일**이다.
권리/입력·코드 결속·HMAC/현재 DB 검사 중 비용을 구분하고, 실제 종료 거부와 정상 전진을 별도로 기록한다.
그 근거로 P6a2c2의 작은 조회 수정 범위를 정한 뒤 실제 P6a 정상/hold/cancel·재접속/권리·WebGL과 복구를 다시 확인한다.
worker를 늦추거나 종료된 작업의 prefix를 공개해 관측 창을 늘리지 않는다.

이번 실제 브라우저 guard는131.304초, 최종 API 진단 guard는159.266초였다. 준비·실패·복구·분석은 별도다.
기존 P6a0.5–1.5시간/P6b0.5–1시간 추정은 새 조회 비용 의존성 때문에 갱신 대상이다.
첫 프로파일/수정 범위 결정0.5–1집중시간을 잠정으로 두며, **사용자 계산 중3D 완료 날짜는 아직 확정하지 않는다.**
실제 작기/국내 독립 농장 자료0, G0–G4 `not_assessed`, 실제 생산·미래 마진·추천 hold를 유지한다.
전체 CI·remote 작업은 실행하지 않았다.
