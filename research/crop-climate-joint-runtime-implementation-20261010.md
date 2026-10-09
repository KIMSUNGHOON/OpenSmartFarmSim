# 공동 작물·기후 결과의 명시 서버 조립 수용 — 2026-10-10

[계약](../contracts/crop-climate-joint-runtime-v1.md)과
[실행 기록](artifacts/crop-climate-joint-runtime-reference-20261010.json)을 대조해
`crop-climate-joint-runtime-assembly`를 **로컬 합성 소프트웨어 범위**로 수용한다.
core commit은 `5c022adc18e792340e9013e937bee05f4eabf384`다.
기록은20,883bytes/SHA256 `398a3d87aabca81d8cedf92816161073499cf20fae0ad76643a672c4cc51dff5`다.
운영 기반 고정 `d19f7c0`을 유지한다. 실제 품종/농장 작물 Run·국내 독립 검증 자료는0건이며 G0–G4는 `not_assessed`다.

## 구현과 판단

현재 native Codex CLI의 실제 turn context는 `2026-10-09T22:39:00.025Z`, `gpt-6.1-sol / xhigh`다.
원 LF SHA는 `6d2a06907ac91a0e536974e1893886e599ce7e09d090499e899809c24b36a683`이며
원 확인 도구 `2e6d5c`/보호 보존 `97b101`에 기록했다. 재귀 CLI/새 제품 runtime CLI 실행은0회다.

착수한 core4는 기존 `api_runtime.py`, 새 보호 설정 loader, 집중 검사, 계약이다.
기존 operator/calculation loader·수식·서명 저장소·HTTP/OpenAPI·웹 소스는 수정하지 않았다.

- 새 `operator-joint-crop-climate-api-config-v1`은 정확한 boolean flag를 요구한다.
  기존 두 판본의 joint flag 누락/False 호환과 True 거부를 유지한다.
- 현재 native farm binding이 기존 cycle 권한을 요구하므로 legacy cycle flag/factory도 명시한다.
  이 저장소는 별도 빈 root로 조립하며 기존 계산/입력을 실행하거나 결과를 생성하지 않는다.
- 동일 jobs/farm/current_principal의 정확한 joint store/query를 만들고 기존 HTTP에 연결한다.
  input/server/DB의3개 키를 분리한다. 잘못된 flag/factory는 I/O 전에 거부한다.
- 기존 보호 파일 검사를 재사용하고 factory/조립 후 설정·DSN·TLS·키 파일 bytes와 현재 metadata를 재검사한다.
  변경은 고정 `operator_config_rejected`로 거부한다. 파일을 수정하거나 권한/기본 키를 공급하지 않는다.

조립 시 검사하는 것은 타입·코드/키 결속과 provisioned 권한이다.
특정 결과의 실제 farm/source/권리·서명은 현재 조회에서 검사한다. 기동 성공으로 자료를 승인하지 않는다.
운영자는 보호 설정과 trusted factory를 공급한 뒤 기존 foreground 진입점에서
`--factory app.crop_climate_joint_operator_config:api_service`를 사용한다.
기본 operator module, 자격증명 또는 새 사용자 서버를 자동 배포하지 않았다.

## 실제 검증

core4의 SHA가 같은6그룹에서 **새62개(일반58/실제 SCRAM4)와 기존 회귀300개, 고유362개**가 통과했다.
이번 시도의 실패는0회다. 실제 native 정상/보류는 각1개이며 selector 중복은 없다.

| 그룹 | 원 exec session → terminal 도구 | 통과 | guard 초 |
| --- | --- | ---: | ---: |
| pure-v1 | 1824 → f2832b | 58 | 4.161 |
| completed-v1 | 87697 → 00a07d | 1 | 82.472 |
| hold-v1 | 82676 → b43390 | 1 | 81.739 |
| faults-v1 | 93830 → 374fa8 | 1 | 65.641 |
| late-v1 | 97623 → 8bc920 | 1 | 71.062 |
| regression-v1 | 16843 → 86e4da | 300 | 148.562 |

모든 원 종료 코드는0이다. 회귀에는 기존 runtime/보호 loader/계산 loader·새 HTTP 일반65개·OpenAPI를 포함한다.
기존 calculation loader의 실제 SCRAM 조립도 포함해 기존 저장소/flag와 공존함을 확인했다.
기존 operator의5개 `actual_scram` 거부 경우와 새 HTTP native7개는 이번 회귀에서 제외했다.

소유32초/16걸음 producer로 등록한 정상/보류 결과를 새 loader의 실제 공유 DB·검증된 HTTPS로 읽었다.
요약/시점/사건6응답 전체 bytes가 seed current query와 같다. 원108상태/장부와 마이크로초 UTC를 보존한다.

| 상태 | summary bytes/초 | samples bytes/초 | events bytes/초 |
| --- | --- | --- | --- |
| completed | 18,904 / 4.840 | 35,046 / 5.053 | 73,566 / 8.466 |
| hold | 18,995 / 5.078 | 24,764 / 5.285 | 49,736 / 5.190 |

이는 작은 합성 조회의 실측이며 전체 작기나 동시 사용자 용량으로 외삽하지 않는다.
다른 farm/jobs의 store/query·잘못된 타입·입력 키 재사용2종·코드 pin·DB grant 변경의8거부 뒤 정상 재조립을 확인했다.
같은 조립 App/실제 DB의 보호 ASGI에서 직렬화 도중 권리 철회422·계정 만료401을 확인했다.
수치8종 진입점 호출0·producer/등록 금지·원 DB counts/등록1행·설정/입력 bytes와 빈 legacy root를 보존했다.
TLS FD10→10, 잘못된 조립 FD11→11, controller FD4→4다.

## 보존과 남은 범위

nice19/.25초 관측의 단일 PID 최대185,724,928bytes·소유+명시 보호 합 최대510,488,576bytes로512MiB/1GiB 안이다.
감시 합453.635초다. 원본2,148항목·고정 UI source/assets·기존3프로세스/5173 HTTP200,
소유 PG/process·schema/role/passfile/temp 정리를 확인했다. 다수의 PG 접속 PID 원 목록은 보호 기록에 두고 공개 기록에는
그 개수와 원 terminal SHA를 보존했다. core Python AST3개·계약 링크3개·diff 공백 검사도 통과했다.

기존 사용자 화면은 완료된 합성166일 생장/수확의 저장 재생이다. 새 공동 모델 화면·실시간 U3는 아직 연결되지 않았다.
전체166일/기존 공동 수치 suite·새 브라우저/WebGL·hosted CI는 재실행하지 않았다.
이전 f06fb67의 Web success/다른4개 registry 장애와 후속 push/hosted 수용 보류는 유지한다.
실제 자료·품종/독립 현장·forcing/전체 공동 작기·생산/구매 자원/미래 마진/추천 관문은 미완료다.

## 다음 단계와 일정

다음은 `crop-climate-joint-web-client`다. 기존 typed client242줄/검사379줄과 새 public projection447줄을 대조해
새 응답을 기존121상태로 위장하지 않고 원108상태/22장부·관리 사건·UTC/hold를 검증하는 작은 SDK부터 추가한다.
same result/farm/identity·현재 scope·페이지64/8·2MiB·취소/늦은 응답·잘못된 판본 거부를 확인한다.
사용자 화면은 그 뒤 같은 선택 시점의 표/그래프/수치3D와 실제 API/브라우저를 연결해 수용한다.

runtime의 이전2–4시간 추정은 native22:39Z→core/검증22:53Z 약14분과 위453.635초 감시 관측으로 갱신한다.
기록/검토·commit은 별도다. SDK는 위 실제 파일 범위와 닫힌 DTO 검사를 근거로 **2–4집중시간 잠정**이며
2026-10-10 연속 작업/새 계약 오류 없음 조건이다. 3D는 SDK 수용 뒤 실제 adapter/화면 범위를 고정해 다시 추정한다.
이는 최종 UI·실시간 U3·전체 공동 작기·production 완료일이 아니다. 독립 자료와 관문 확보일은 미정이다.
