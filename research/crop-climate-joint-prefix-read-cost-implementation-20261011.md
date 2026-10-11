# 계산 중 조회 비용 감소 — reader v5 로컬 수용

2026-10-11. **P6a2c1 계측과 P6a2c2 소프트웨어 수정 수용. 실제 브라우저 P6a와 사용자 적용 P6b는 미완료다.**
[수정 계약](../contracts/crop-climate-joint-prefix-read-cost-v1.md),
[기계 증거](artifacts/crop-climate-joint-prefix-read-cost-reference-20261011.json).
기계 증거 SHA256: `97998f523bcce06813eabb2fa2e005b73f9a02ff588b70892d43a7d306a8d229`.
실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 turn context를 확인했으며 재귀 CLI는0이다.

## 계측과 수정 근거

기존 진단 reference1파일에 API 스레드의 prefix route 범위 cProfile을 추가했다.
실제 SCRAM/TLS·별도 unpaused 작업자·chunk8에서 공개 요약이 제공한 선택자로 사건/생장 페이지를 순차 조회했다.
모든 요청의 추적과 prefix 요청의 프로파일이 있고 observer 오류는0이다.
작업자 추적·지연·정지 장벽과 조회의 계산/쓰기는0이며 원 terminal summary bytes를 독립 current query와 대사했다.
진단명에 남은 v4는 기존 이름이다. 각 실행의 실제 reader 판본은 기계 증거에 별도로 기록했다.

| 사건 페이지 한 요청 | v4 | v5 |
| --- | ---: | ---: |
| 계측된 HTTP 시간 |25.502초|10.210초|
| 전체 binding.current |17회|6회|
| 농장 등록 조회 |34회|12회|
| 실제 DB 연결 함수 |547회|195회|
| 실행 역할 감사 |615회|219회|
| 입력 증거 검증 |34회|34회|

accepted 요약도24.480→10.155초였다. v5는 같은 선택자의 사건/생장 페이지를 모두200으로 받았고 생장 조회는10.180초였다.
이는 한 쌍의 계측 실행 관측이며 일반 지연/SLA 보장이 아니다. 중첩 cumulative 시간은 합산하지 않는다.
진단은 요청 순서를 재현하며 실제 UI의 모든 polling/backoff와 동일하지 않다.

v4 계측의 생장503에서는 조회 전후 `simulating→succeeded` 전환을 직접 추적했다.
v5에서도 나중 요약503을 기록했다. 계산이 끝난 중간 결과를 공개하도록 바꾸지 않았다.
[앞선 실제 브라우저의 생장503](crop-climate-joint-prefix-browser-v4-20261011.md)은 내부 줄이 추적되지 않았으므로 같은 원인으로 단정하지 않는다.

## 구현과 검토

제품 변경은 `crop_climate_joint_prefix.py`1파일의 private session callback과 내부 판본 v5다.
서명 파일 검사마다 전체 농장/시장/경제 등록을 다시 읽던 호출을 줄였다.
`read`와 직렬화 후 `_after_projection`의 기존 전체 current 검사6회는 유지한다.
내부 callback은 매번 같은 입력 증거·정규화 값·현재 표시권·scope·정책/코드를 검사한다.
서명 intent/binding과 HEAD/proof/commit/page 검사도 유지하며 전역/시간 기반 캐시는 추가하지 않았다.
callback이 응답을 발행하지 않고 전체 경계 검사가 이후 농장 접근 거부를 차단한다.

늦은 농장 접근 거부 회귀1개를 추가했다. 실제 SCRAM 환경에서 private page를 읽은 뒤
농장 등록 제공자의 거부를 합성 주입하고 응답 거부·원 조회 복구·DB 불변·조회 계산0을 확인했다.
이를 실제 DB 권한 변경이나 독립 현장 검증으로 세지 않는다.
공유 farm binding/custody, HTTP core·DTO, 입력·수치 모델·writer·checkpoint·결과 저장과 DB schema는 변경하지 않았다.
명시적 기존 경계에 변경을 한정했고 새 프레임워크/의존성은 없다.

## 최종 동일 코드의 고유267개

| 범위 | 통과 |
| --- | ---: |
| HTTP |158|
| reader |18|
| 공개 투영 |44|
| runtime/설정 |43|
| 별도 unpaused 정상/hold/cancel 작업자 |3|
| v5 실제 API 프로파일 |1|

각 최종 묶음의 제품·시험·reference 해시를 현재 파일과 대사하고 고유 node ID267개를 확인했다.
v4 기준선1개와 이전265개는 합산하지 않았다. 최종 guard12개의 실측 합은2,330.091초(약39분)이며 기준선/조사·문서/commit 시간은 별도다.
정상 자동 계산에서는 같은 공개 선택자의 사건/생장1행 및2행을200으로 읽고 원 terminal records의 canonical bytes·binary64·UTC와 대사했다.
원 terminal summary·독립 작업자 종료0, hold/cancel과 현재 권리·늦은 거부·서명/rollback·잠금·빈/64+1행도 확인했다.

원 핸들29917은 재개 시 사용할 수 없었다. 해당 immutable guard의 child0·3 PASSED·controller 종결·보존/정리를 대조했다.
기계 증거의 그 original tool exit는 `null`로 유지하며 tool 반환을 추정하거나 검사를 재시작하지 않았다.
나머지 최종 묶음은 실제 원 tool 종료0과 guard/통과 목록을 함께 기록했다.

최종 단일/합산 최대 RSS는170,115,072/1,046,384,640bytes로512MiB/1GiB 이내다.
원본2,148개·두 frozen source/dist·보호 root4와 FD4→4를 보존했다.
소유 프로세스/PG·임시 PG/인증 파일 잔여0, 사용자 서버 중지0·원격 작업0이다.
웹 코드는 변경하지 않았다. 전체 저장소/원격 CI와 이번 v5의 실제 브라우저/WebGL은 실행하지 않았다.

## 다음 단계와 사용자 범위

다음은 **P6a 실제 제품 브라우저**다. 기존 P6a0 빌드로 정상/hold/cancel·빈/재접속·현재 권리,
계산 중 같은 selector/UTC의 원 LAI·50구획·온도·사건→terminal과 WebGL을 확인한다.
기존 WSL 유지보수/복구 창에서 두 주소의 원 결과·키·권리를 보존하고 실패 시 원 frozen 서버로 복구한다.
P6a 수용 뒤 **P6b**에서 사용자5174 적용·접속 안내·두 주소와 원 결과를 확인한다.
기존 작업 분해의 P6a1–2시간/P6b0.5–1시간은 조건부 집중 작업량이다. 이번 계측은 API 범위이므로 실제 브라우저 재측정 전 완료 날짜를 확정하지 않는다.

현재5173은 완료 합성166일의 저장 재생,5174는 상태/checkpoint 자동 조회와 종료 뒤 저장3D다.
계산 중3D는 현재 사용자 서버에서 비활성이다. 개발 시험 DB의 작업도 사용자 DB에 자동 노출되지 않는다.
실제 농장 Run/독립 국내 자료0, G0–G4 `not_assessed`, 생산량·미래 마진·작물 순위와 최종 제품 UI/전체 작기 수용은 남아 있다.
