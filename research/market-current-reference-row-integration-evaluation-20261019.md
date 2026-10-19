# 참조 행 통합 후보 평가와 원문 지문 대안 — 2026-10-19 KST

[v3 primitive34](market-current-reference-row-readset-primitive-20261019.md) ·
[기계 증거](artifacts/market-current-reference-row-integration-evaluation-20261019.json) ·
[미채택 v3 patch](artifacts/market-current-reference-row-readset-integration-candidate-20261019.patch) ·
[연구 전용 v4 helper](artifacts/market-current-reference-receipt-feasibility-helper-20261019.py.txt).

상태: **v3 통합 미채택·제품6파일 원 bytes 복원. v4는 미구현 타당성 관측**.
기존 primitive34/HTTP58·v2 실행 경로는 유지한다. 실제 native `gpt-6.1-sol/xhigh`의
문맥 시각/원 해시를 기록했다. 재귀 CLI/하위 에이전트·변경 없는 native CI 반복은 없다.

## v3 실제 연결과 비용 기준 미충족

닫힌 trace에서 source/candidate 키를 도출해 기존 getter를 그대로 실행하고,
각 SQL lookup만 scoped row로 공급했다. 일반/부적합 경로는 원 lookup을 사용하도록 했다.
6개 app 파일의 후보였고 새로운 운영 계층·SQL interception·tenant 전체 조회는 없었다.
17113:0에서 실제 논리 조회/중복 순서·기존 값의 일치를 확인했다.

| 비교 | 원 구현2단계 초 | 후보2단계 초 | 원 구현3단계 초 | 후보3단계 초 |
| --- | ---: | ---: | ---: | ---: |
|초기 후보/74132:0|6.908494|7.132914|6.924931|7.116229|
|경계 검사 정리 후/23585:0|7.064943|6.980190|6.950928|6.992446|

초기 후보는 약3% 느렸다. 37607:0의 실제 한 청크 profiler는 SQL7,113→5,020,
row lookup2,640회·row check2,622회/포함0.594초를 관측했다. 중첩/계측 시간을 합산하지 않는다.
현재 principal/slot/binding 검사는 매 lookup에 유지하고, 전체 code/profile 검사는 capture/recheck
경계로 정리한 후보도 한 쌍 약1.2% 감소/다른 쌍 약0.6% 증가에 그쳤다.

두 후보 모두 실제 source SQL1,824→76, candidate 입력 SQL816→34와 추가 batch92개를 확인했다.
role 감사183/role SQL2,745·논리 source1,824/순서·원 수치·UTC/checkpoint/원량은 유지됐다.
하지만 유용하고 일관된 실제 비용 개선을 입증하지 못해 **통합을 기각**했다.
광범위 보안 회귀를 수용했다거나 원64가 빨라졌다고 주장하지 않는다.

후보 patch를 보존하고 source/candidate/bundle/registration/일사 binding/row primitive의6파일을
HEAD `536d8c0`의 원 bytes로 복원·SHA 대사했다. primitive34의 원 source587be5…도 복원됐다.
같은 실패 native64를 다시 실행하지 않았다. 앞선34검사는 기존 primitive 판본의 수용이다.

## 원문 지문 대안의 제한된 타당성

98196:0은 **검증 의미가 달라지는 연구 전용 시험**이다. 기존 getter1,824회를 모두
재실행하는 대신 한 registration 수명 안에서 최초 전체 trace 대조를 수행하고,
그 전후 실제 source/job/candidate 행의 SQL 지문을 대사해 기준을 고정했다.
이후에는 정확한 키의 DB 원문에서 새로 계산한 지문을 전후로 조회하고,
동적 getter와 각 logical reference의 현재 tenant/scope 검사는 실제 수행했다.
제품 코드는 변경하지 않았다. 이 시험을 기존 v3 검사와 동일하다고 부르지 않는다.

| 실제 항목 | 원 구현 | 시험 후보 |
| --- | ---: | ---: |
|2단계 초|7.073585|6.182102|
|3단계 초|7.088332|6.400657|
|source getter 실제 호출|1,824|152|
|role 감사/role SQL|183/2,745|183/2,745|
|새 SQL 지문 조회|0|138|
|전후 source 지문 행|0|3,404|
|전후 candidate pin 지문 행|0|46|
|전후 candidate 입력 존재 행|0|0|

후보의 anchor 전체 trace는1회, 순수 data proof는1,672회, 반복 동적 getter는264회였다.
같은 원 수치·UTC/checkpoint/원량으로 약12.6%/9.7% 감소를 관측했다.
source getter 수와 순서는 달라졌으며 이전1,824회와 같다고 주장하지 않는다.
직접 worker/API 동시 실행·원64·전체 처리량 또는 보안 동등성 수용은 아니다.

DB에서 저장 hash 열만 신뢰하지 않고 원 bytea와 사용 metadata로 새 지문을 계산했다.
원 bytea는 명시적 hex, source/candidate timestamp는 epoch로 정규화했다.
`get_market_candidate`와 held/context/tenant 같은 동적 getter, 파생 scenario가 있는 getter는
실제로 실행했다. source fallback 여부는 실제 candidate 존재를 반영했다.
DB의 지문은 **권리 승인·관문·서명 또는 실제 농장 검증 증거가 아니다**.

공식 근거는 PostgreSQL16의 [SHA/encoding 함수](https://www.postgresql.org/docs/16/functions-binarystring.html),
[JSON 변환](https://www.postgresql.org/docs/16/functions-json.html)다.
**설계 판단:** 같은 원문/사용 metadata·모델 code/Decimal context가 유지될 때 반복하는
순수 재구성을 생략할 수 있는지는 별도의 동등성/철회/의존성 증거로 입증해야 한다.
공식 SQL 함수가 이 동등성을 승인하는 것은 아니다. 농업/경제 자료를 채택하지 않았다.

## 다음 구현 범위

[v4 제안](../contracts/market-current-reference-receipt-agreement-v4.md)의 닫힌 SQL 지문 primitive부터 구현한다.
정확한 키·부재·hash 계산/정규화·한도·동일 owner/connection/수명·코드 판본을 실제 DB로 검증한다.
그 다음 default 순수 DTO의 동등성 범위와 dynamic/unknown 경로를 분리해 full 검증에 대사한다.
늦은 source/job/candidate/권리·code/schema/Decimal/callback 변경과 원 worker/HTTP 회귀·paired 비용을
통과한 경우에만 새 프로토콜을 채택한다. v2 baseline은 그때까지 유지한다.

5개 supervised 실행은 반복/관찰이며 별도 고유 회귀 합계로 더하지 않는다.
각 실행은 source/원본2,148항목·frozen 두 UI/5root·512MiB/PID/합1GiB·FD4→4와
소유 PG/임시/passfile0을 보존했다. 전체 backend/browser·fresh exec/SIGKILL은 재실행하지 않았다.
실제 농장 Run0·권리/관문 승인False·G0–G4 미평가·새 Solar 미배포다.
독립 정상64→hold/취소→계산 중3D→WSL 용량/사용자 적용과 실제 자료/외부 검증·전체 완료일은 미완료/미정이다.
전체 goal은 active다.

## 게시·기록 검토

97143:0에서 현재 baseline6파일/primitive34·로컬58 source pin·미채택 patch/helper SHA,
원 API/worker 본문·계측 header를 대사했다. 문서 로컬 링크2,354개·연구 helper 문법을 확인했다.
두 UI의 development-status는 HTTP200·원 JSON bytes 동일/no-store였고 기존 HTML·환기2,173파일을 보존했다.
실제 guard1.364초·5root·합 RSS898,338,816bytes·단일141,316,096bytes·FD4→4,
소유 프로세스/PG/임시/passfile0을 확인했다. UI code/DOM/WebGL은 변경하지 않아 브라우저를 재실행하지 않았다.
최종 문서·증거 검토에서 미채택 코드의 제품 채택, 제한된 paired 관측의 전체 처리량 주장,
합성 시험의 실제 농장/관문 승격이 없음을 확인했다. 전체 backend/보안 동등성 수용 검토는 아니다.
