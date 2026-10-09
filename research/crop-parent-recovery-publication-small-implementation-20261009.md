# 중단 부모의 사전 게시 선언 복구 — 작은 로컬 수용

[4파일 계약](../contracts/crop-parent-recovery-publication-v1.md)의 작은 자식만 수용한다.
전체166일 부모·UI·제품 Run/예측·추천의 수용이 아니다.
[기계 판독 증거](artifacts/crop-parent-recovery-publication-small-reference-20261009.json)를 함께 본다.

## 구현과 계보

실제 중단 기록의 원 execution/게시 선언/config/reference/key hash와 첫 계산 요청 전 파일 시각을 검사한다.
원 source/version/input/farm/plan, 종료된 원 PG/worker와 이전 receipt/hash를 확인한다.
유실된 마지막 receipt/result만 중단으로 다루며 원 기록은 바꾸지 않는다.

새 감독은 같은 config/input/source/budget/RSS 한도/DB data를 사용하고 원 마감을 연장하지 않는다.
원 HEAD/걸음/commit에서 복원한 첫 로그/checkpoint·RHS/delta QC0, 정상 완료 receipt/SCRAM/FD를 요구한다.
새 게시 선언에서 supervision directory/SHA, 새 execution에서 publication file/SHA만 바꾼다.
원 계획/무작위 DB key는 보존한다. 기존 publisher/coordinator guard를 그대로 통과시키며
복구 manifest에 모든 원/파생 hash와 helper source를 묶는다. 코드/비밀/원 선언을 덮어쓰지 않는다.

판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 현재 turn에서 수행했다.
actual turn context SHA·4개 core SHA·원 명령/출력 hash를 보존했으며 재귀 Codex CLI0이다.
고정 producer checkout에는 새 파일을 추가하거나 guard를 수정하지 않았다.
실제 원 전체 실행의 사전 계보도 읽기 전용으로 검사해47,809시점/5사건/1,816,704걸음 계획을 확인했다.

## 통과한 검증

- 집중23개: 원13258 종료0, pytest1.73초/전체2.169초. 원량/파일/key 보존과 제한된 참조 변경,
  SHA·plan·farm·key/source·선언 시각·원 live PG/유실 경계·마감/budget/DB/input,
  미완료·복원 RHS·SCRAM/FD·HEAD/delta QC/worker/checkpoint와 파생 후 변조 거부다.
  이는 private document 계약 시험이며 실제 DB 증거는 아래 별도 실행이다.
- 실제 작은 native-v2: 원19677 종료0/148.830초, pytest1개126.71초.
  원40걸음/1시점/1사건 후 중첩 pytest -15와 worker SIGKILL 요청/종료를 확인했다.
  실제 원 PG 정지0/같은 data 재시작0·새 PID, 같은 원40걸음 HEAD에서 복원 RHS/delta QC0,
  최종120걸음/3시점/3사건/4commit과 전체 원 행/121상태 대사를 통과했다.
  정상 비교/게시 자식 모두0이며 게시 RHS0·실제 HOST SCRAM이다.
  원 무작위 DB key/plan/선언/입력은 그대로이며 원 실패 기록을 정상 종료로 바꾸지 않았다.
- 정상 backup/source 현재 query→계정/권리/다른 tenant 거부→source DB/roles/schema 정리 후
  현재 checkout의 fresh Python/PG 복원0/13.438초로 같은 ID/payload/최초 시각·대표 원 행을 확인했다.
  조회의 RHS/게시/증명 발행은 readonly guard로0이다. 새 실제 품종/농장 Run0이다.
- native-v2의 복원 단계는 별도 PG tree RSS가 빠져 전체 자원 증거로 확대하지 않았다.
  **추가 fresh-resource-v1 원10063 종료0/14.399초**로 같은 backup/현재 코드/원 작은 마감 안에서
  source 정리 후 fresh 복원을 다시 확인했다. 실제 복원 PG tree180표본을 포함한209표본/.05초,
  단일128,204,800bytes/합792,682,496bytes≤512MiB/1GiB다.
  같은 원 값/UTC·보호4 identity/source1,551개·소유 비좀비0/PG pidfile0을 확인했다.
- native-v2에서 source PG를 포함한 관측 최대는 단일131,870,720bytes/합977,514,496bytes,
  1,178표본/.1초였다. 원 고정 source397개·현재 source1,551개·미리보기 dist/보호4 identity를 보존했다.
  이 값과 위 독립 복원 자원 증거를 분리한다. 일반 운영/브라우저 용량 수용은 아니다.

## 실패를 보존한 수정

첫 native-v1 원41842는43.065초/종료1이었다. export 이전 시험 객체의 권한 문맥으로
다른 runtime에서 계산한 체크포인트를 읽으려 해 custody hold가 났다.
저장한 runtime을 정상 loader로 다시 구성한 객체로 조회하도록 **시험**을 고쳤다.
기존 custody 검사를 완화하지 않았고 실패 로그/종료·source/보호 identity 정리 증거를 남겼다.

## 전체 적용과 다음 단계

원 전체95086은 중단 실패이며 복구 원95915는 계속 별도 실행 중이다.
13:52의 실제 전체 미완료 상태에서 파생을 시도해 ValueError/새 파일0·게시0을 확인했다.
13:53의 확정은334commit/1,332,983걸음이며 전체1,816,704걸음이다.
원18:12:12 KST 상한은 유지한다. 작은 성공을 전체 수용으로 대신하지 않는다.

다음 전체 부모 수용은 실제 복구 종료→새 helper 파생/정상 validation→전체 원 행/121상태 대사
→원 key 정상 게시/인증 backup→원 DB 정리 후 fresh 현재 query·권리/계정/원 종료/자원 감사다.
복구 원95915와 후속 비교/게시/복원 명령의 실제 종료0을 확인해야 한다. 원95086의 실패는 보존한다.
그 뒤 전체 수확 writer/registry→실제 API/대표3D→기후/물·양분/구매 에너지/Decimal 경제를 연결한다.
전체 결과의 대사/backup 비용은 아직 실측되지 않아 전체 수용 날짜를 확정하지 않는다.

U1 전달 후보의 브라우저/전체 웹/빌드와 실제 선택 UI·실시간 U3는 미수용이다.
계산 대기 중 기존 Vite/정적 서버로 격리된 재생 harness를 빌드/제공해 dev server 메모리를
줄이는 작은 검증 준비를 할 수 있다. 원 동시 RSS 한도와 실제 브라우저 수용은 그대로 요구한다.
이 검증은 실제 공동 DB/API 증거와 구분한다.

remote `8dd386d`의 CI는13:49 관측에서 Backend 진행 중/다른4workflow 성공이었다.
이 새 로컬 변경의 hosted 수용은 아직 없다. 실제 국내 품종/독립 농장 자료0건과 G0–G4,
생산/미래 마진/추천 보류 및 운영 기반 고정을 유지한다.
