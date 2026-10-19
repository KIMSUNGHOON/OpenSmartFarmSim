# 기존 두 UI 인증·TLS 갱신 — 2026-10-20 KST

[기계 증거](artifacts/frozen-preview-authentication-renewal-20261020.json).
기존 공통/환기 인증 종료2026-10-19T23:01:39.008992Z를 확인하고 같은 사용자 경로를 만료 전에 갱신했다. 운영 유지가 필요한 근거는 실제 만료 시각이며 성능 시험을 위해 서비스를 정지한 작업이 아니다. 새 Solar나 새로운 작물 모델 배포가 아니다.

## 순서와 보존

현재5root와 불변 원본2,148항목을 대사하고 frozen controller·같은-token wrapper·proxy 보존을 준비했다. 기존 환기를 소유 boot/start/PID·pidfd로 정상 종료해 route를 복원했다. legacy→joint→환기 순으로 같은 frozen source와 키·토큰·원 결과를 복원했다. 모델 source와 frontend code는 유지했다.

legacy는 읽기 전용 합성166일 manifest에서 DB를 다시 복원했다. 종료 시 원 DB counts 불변·원본 보존과 새 DB counts 일치를 확인했다. joint DB·artifact와 환기 namespace/결과는 기존 것을 유지했다. 공통 runtime의 변경은 issued_at/expires_at뿐이며 model/integrity key와 모든 나머지 값은 같다. API의 변경은 새 실행 directory의 TLS/DSN/key 파일 경로이고 DSN/모델 key 파일 bytes는 같다. 환기는 auth와 원 runtime SHA를 갱신했고 다른 설정은 같다. TLS 인증서/키는 새 private directory에 생성했다. 토큰/DSN/key/원 응답 본문은 공개 기록이나 프롬프트에 쓰지 않았다.

롤오버65.585518초·단일124,735,488/합739,958,784bytes였다. 기존5root의 종료와 새5root의 실제 생존을 확인했다. 이전 boot 복구 때 잃었던 joint 감독도 현재 새 controller의 실제 생존으로 복원했다. 자동 재기동/장기 운영/G4 수용은 아니다.

## 실제 인증·원 데이터 대사

| 실제 검사 | guard 초 | 합 RSS 최고 bytes |
|---|---:|---:|
|legacy 생장/수확·권한8응답|54.781238|934,326,272|
|joint 원 입력3·저장9시점·HTTPS/SCRAM|29.552129|972,251,136|
|환기 정상/보류 원8응답·UI proxy/직접 HTTPS|47.824061|921,387,008|

legacy의47,809생장시점·47,813수확행은 저장된 합성 fixture의 행 수이며 실제 농장 생산량이 아니다. 현재8응답은200×6/403/404이고 원 생장/수확과 frontend 원문을 확인했다. 서비스 FD8→8·계산/게시 호출0이다.

joint는 동일 bearer로 원 입력3개와 저장9시점의 원 수치/UTC를 대사했다. 관측 시각만 다르고 조회 계산/쓰기21후크는0이다. 환기8응답은 원 normal/hold bytes와 같고 CA/호스트/시각 검증 TLS, UI proxy·직접 HTTPS를 확인했다. query audit8건의 계산/쓰기 후크0·API FD identity8→8과 frozen source2,173파일을 확인했다.

각 guard는 기존5root를 유지하며512MiB/PID·합1GiB·0.25초, 원본2,148/두 frozen source·자산·감독FD4→4·시험 소유 비좀비/PG/임시/passfile0을 통과했다. 새 서비스/API/작업자와 서비스 PG는 보호 상태로 실행 중이다. 전체 backend/원64 CI·browser DOM/WebGL·새 작물 계산은 재실행하지 않았다.

## 사용자 경로와 다음 작업

기존 http://localhost:5173/ 와 http://localhost:5174/#ventilation-execution 및 같은 접근 토큰을 사용한다. 사설 안내는 legacy run-v29/service/OPEN-UI.private.txt, joint serve-v29/OPEN-UI.private.txt다. 공통/환기 인증 종료는 **2026-10-20T22:43:18.087628Z**다. legacy는86340초 수명을 유지했으므로 다음 갱신 준비를 더 이른 **2026-10-20T21:40Z 이전**으로 잡았다. 내부 미리보기의 운영 시각이며 전체 완료일이 아니다.

주 작업은 [권한 matrix snapshot 반례 뒤](solar-role-matrix-conditional-review-20261020.md)의 원 SQL/statement 순서를 유지하는 bound-array 표현 검토다. 원 계측 OFF64 미완료→정상/hold/취소→계산 중WebGL→WSL 사용자 적용, 실제 농장 자료/독립 작기·G0–G4와 전체 완료일은 남는다. 새 Solar 미배포·실제 농장 Run0·goal active다. 실제 native CLI gpt-6.1-sol/xhigh의 문맥·코드/출력 해시를 결속했고 재귀 CLI/하위 에이전트는0이다.

## 상태 게시

[게시 증거](artifacts/frozen-preview-authentication-status-publication-20261020.json): 두5173/5174 HTTP200·동일 최신 상태/no-store·frozen HTML/환기2,173/5root/원본2,148·FD4→4·시험 소유 잔여0을 확인했다. guard1.369299초·합927,227,904bytes다. UI code·browser DOM/WebGL·전체 backend/원 정상64는 재실행하지 않았다.
