# 환기 모델 접수·자동 계산 핵심 — 2026-10-12

상태: **로컬 수용**. [계약](../contracts/crop-greenhouse-ventilation-execution-core-v1.md) · [검증 영수증](artifacts/crop-greenhouse-ventilation-execution-core-reference-20261012.json).

## 구현과 사용자 범위

새 입력·checkpoint·publication/result-link 판본과 사건 이름으로 기존 simulation 작업표를 사용한다.
현재 농장/입력/권리를 고정해 멱등 접수하고, 같은 revision의 다른 입력은 거부한다.
작업자는 임대를 갱신하며 제한된 구간을 계산하고 서명한 HEAD를 작업 사건에 확인한다.
정상/보류 결과·result link·attempt outcome·작업 종료는 같은 DB 거래로 저장한다.
정상만 기존 job publication에 추가하고 보류는 원 prefix와 사유를 가진 보류 결과로 유지한다.
취소·권리/입력 변경·임대 상실·마지막 fence 실패는 부분 결과 게시를 막는다.

기존 `DeterministicJobDiscovery`와 `DeterministicWorkerLoop`에 새 판본과 정확한 worker 타입만 추가했다.
독립 자동 소비자는 작업 ID 지시 없이 새 판본을 발견한다. 다른 판본의 대기 작업은 소비하지 않는다.
새 queue/schema·권한 grant·패키지·사용자 서비스 재시작은 추가하지 않았다.
새 모델의 현재 진행/접수/취소 HTTP·명시 실행 runtime·웹/3D·사용자 적용은 다음 단계다.
이번 핵심만으로 부모 실행 작업을 완료하지 않았다. 검증 입력은 합성32초이며 실제 작기 예측이 아니다.

## 통과한 검증

| 범위 | 원 도구 handle | 검사 | 종료 | guard 시간 |
| --- | ---: | ---: | ---: | ---: |
| 기존 대기열/소비자 호환성 |3752|77|0|1.918초|
| 실제 정상/보류·원 수치/UTC·독립 재조회 |29118|2|0|291.796초|
| 임대 만료·SIGKILL 뒤 독립 재개 |79151|2|0|205.146초|
| 계산 중/종료 직전 취소·저장 rollback |3454|4|0|207.980초|
| 완료 직전 scope/권리/resolver 변경 |89462|3|0|183.355초|
| 독립 자동 소비·접수·중복 checkpoint |26004|3|0|156.060초|

고유91개이며 실제 DB/독립 프로세스 사례는14개다. 모든 원 도구 종료를 수집했다.
여섯 guard의7개 핵심 파일 SHA가 동일하다. 검증 뒤 시험 파일의 EOF 빈 줄 하나만 정리했고 전후 AST가 동일함을 확인했다. 실행/수치 코드는 그대로다. 정상/보류의 원108상태·25장부/10수지·사건/UTC와 최종 checkpoint를 대사했다.
정상은 registry/publication/outcome/link 각1개, 보류는 registry/outcome/link 각1개와 publication0이다.
독립 reader는 실제 SCRAM으로 원 bytes·최초 recorded_at·페이지/요약을 읽고 검토 철회도 거부했다.
조회·중복 확인의9수치 entrypoint 호출은0이다.

임대 만료와 실제 자식 SIGKILL 뒤 새 시도는 원 prefix를 수치 호출0으로 먼저 채택했다.
생산자/재개자의 실제 step 합은16이며 남은 구간만 계산했다.
계산 도중/완료 직전 취소, 사건 저장/최종 UPDATE 오류, 완료 직전 권리 변경에서 부분 결과0을 확인했다.
접수는 중복·충돌·닫힌 입력·삽입 중 권리 철회 rollback을 확인했다.
중복 checkpoint는 임대 갱신·독립 객체·권리 복원 뒤에도 최초 사건과 UTC를 유지했다.
별도 Python 자동 소비자는 새 작업을 실제 계산했고 다른 입력 판본의 작업은 queued로 유지했다.

정상/보류 작업자 실행은 각각78.270/78.946초였다. 작은 합성 사례의 관측이며 전체 작기 성능 추정에 사용하지 않는다.
검증 guard 합은1046.254초다. 준비·설계·구현·기록 시간은 별도다.

## 보존과 진행 화면

기존 baseline260 중258파일은 동일하다. 공유2파일의 전후 SHA와 새 핵심 파일은 영수증에 기록했다.
원본2,148·frozen source1,911/자산171·prior UI171/현재172자산·source194·현재 권리/안내·4보호 root를 유지했다.
FD4→4, 소유 non-zombie/PG/passfile/임시 PG 잔여0이다.
검증6묶음의 최대 단일 RSS152,010,752/보호 포함 합1,038,401,536bytes로512MiB/1GiB 안이다.
기존 API/결과/두 URL200과 원 index/NGINX 설정을 유지했으며 사용자 백엔드/worker 재시작0이다.

[진행 화면](http://localhost:5174/#crop-execution)에91검사 통과와 다음 실행 API→같은 UTC3D→사용자 적용을 게시했다.
HTTP200/no-store·main/published/handoff SHA를 대사했다. 5173은 기존 완료166일 재생이며 개발 패널은5174다.
기존 사용자 작업64/64는 완료 상태다. 새 모델은 현재 사용자 두 화면에 미배포다.
원75621의 실제 브라우저/guard0·4.072초에서 인증 없이91검사와 API 완료/실행 다음 단계를 확인했다.
390px overflow0·API쓰기0·pageerror0, 브라우저 단일258,949,120/보호 포함 합994,336,768bytes도 한도 이내다.
새 모델3D 자체의 브라우저 검증은 후속이다.

## 다음 단계와 외부 의존성

다음 한 단계는 **`crop-greenhouse-ventilation-execution-current-http-runtime`**이다.
같은 작업의 현재 checkpoint·terminal/result 연결을 읽는 typed query와 보호 접수/진행/취소 HTTP·명시 실행 runtime을 연결한다.
수용: 실제 정상/보류/취소·원 값/UTC·현재 계정/자료 권리·새/구 판본 구분·조회 계산0·기존 두 화면/WSL 보존.
이어 typed web·같은 UTC의 확정 부분/완료3D·실제 브라우저·사용자 적용을 진행한다.
남은 실행 HTTP/runtime·웹2–4와 사용자 검증/적용1–2의 합3–6집중시간은 잠정 작업량이다.
전체 작기 동적 기후·자원/경제·최종 제품 UI와 독립 농장 자료 검증은 별도다.
실제 농장 Run·독립 국내 자료0, G0–G4 not_assessed, 실제 품종 생산·구매 자원·미래 마진/작물 순위는 보류한다.
native Codex CLI `gpt-6.1-sol / xhigh`의 실제 turn context/원 행 SHA를 기록했다. 재귀 CLI0이다.
전체 CI/remote·새 실행 HTTP/runtime/웹3D·사용자 배포·전체 작기 성능·실제 자료 검증은 미실행이다.
