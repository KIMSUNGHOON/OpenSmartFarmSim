# 환기 모델 완료 결과의 웹·수치3D — 2026-10-12

## 수용 범위와 사용자 화면

`crop-greenhouse-ventilation-web-terminal-3d`를 **합성 저장 결과의 로컬 소프트웨어 범위**로 수용한다.
[기계 증거](artifacts/crop-greenhouse-ventilation-web-terminal-reference-20261012.json)는 실제 SCRAM/검증 TLS의
완료·보류 원 응답6개와 제품 App에서 기록 응답을 사용하는 Chromium12경로를 구분해 보존한다.
새 모델의 실제 API/worker와 제품 브라우저를 동시에 연결한 검증·사용자 서버 적용은 이번 수용이 아니다.

현재 두 사용자 주소는 복구했다. **http://localhost:5173/** 상단과
**http://localhost:5174/#crop-execution** 에서 인증 없이 최신 개발 단계를 확인한다.
기존 원 계산은 완료 상태이며, 새 환기 모델은 아직 사용자 서버에 미배포다.
공개 진행 기록은15초마다 조회하고 실제 단계 검증 뒤 게시한다. Codex 작업 로그의 실시간 중계는 아니다.
5173의 재기동 토큰은 [웹 접속 안내](../web/README.md#joint-execution-user-preview)의 `run-v12` 파일을 따른다.

## 변경

- 별도 `greenhouseVentilationReplay.ts`가 새 ID·판본·단위·유한 값·50구획·108상태·25장부·10수지/허용오차·UTC·페이지·공통 참조를 검사한다.
  구22장부 client, geometry, scene, chart와 해당125검사는 그대로 유지했다.
- `GreenhouseVentilationReplay`는 같은 result/농장/원 UTC의 저장 행을 표·차트·WebGL에 연결한다.
  환기 밀도·현열/수증기/잠열과 입력 SHA, 관리 before/after·ventilation_after를 보존한다.
  저장 행을 선택하는 재생이며 보간·생장 재계산·실제 식물 형태/수확량 추정을 하지 않는다.
- 보류는 실패 경계와 마지막 확정 상태를 구분한다. 새 조회 거부·선택/계정 변경·취소 시 이전 값을 제거하고 늦은 응답을 무시한다.
  현재 권리 재조회는 명시 버튼이며 읽은 화면의 지속 권리 감시는 아니다.
  빈 출력에 장면을 만들지 않고 reduced motion/WebGL 실패 시 표와 시점 이동을 유지한다.
- `api.ts`는 새 factory만 추가하고 `CropReplay.tsx`는 별도 선택지를 추가했다. 서버의 기본 비활성 정책은 유지한다.
  [API 계약](../contracts/api-crop-greenhouse-ventilation-replay-v1.md#완료-결과-웹-소비)에 웹 소비 범위를 덧붙였다.

실제 원 manifest의 `policy_sha256`은 합성 적분 정책이며 `identity.policy_sha256`은 원 작물 정책이다.
처음의 동등성 가정으로 발생한 실패를 수정하고 두 다른 원 SHA가 유지되는 검사를 추가했다.
웹은 digest 형식과 공통 모델/격자를 검사하며 정책의 암호학적 결속은 기존 결정적 서버가 검증한다.

## 검증

| 항목 | 결과 |
| --- | --- |
| 실제 SCRAM·검증 TLS 원 응답 확보 |2검사·완료/보류 각각 summary/samples/events3개·원 bytes 일치·조회9수치 호출0 |
| client/기존 호환 |254검사:새129·구 client113·구 geometry12 |
| 제품 Chromium |12경로·동일 UTC/수치·실제 WebGL draw calls·관리/보류·401/403/404/422·취소/선택/계정·잘못된 판본·빈 출력·모바일/WebGL loss |
| 타입/빌드 |최종 tsc 통과·의존성 추가 없이 제한된 nonminified Vite 빌드 통과 |
| 복구/최종 보존 |현재 두 HTTP200·같은 진행 feed/원 entry/script·원 DB/파일/권리/키·소유 정리 통과 |

고유268검사다. 정상 원 저장3시점은 `2026-10-01T00:00:00.123456Z`, `00:00:16.123456Z`,
`00:00:32.123456Z`이며50구획의 C/N·LAI·온도 표식/표·6개 차트 항목·장부·환기 진단을 대사했다.
Chromium12경로의 guard 합은62.895초, 원 응답 확보 guard는154.681초다. 개발 전체 경과 시간과 같지 않다.
브라우저의 응답은 격리된 기록 응답이며 API 쓰기0·pageerror0이다. 원 응답 fixture 전체 SHA는
`fce186ea3214157f73f63d6d51fd37627704f29bf680110b664f74ab13a9b1b1`이다.

원 도구 종료는 native28573·unit44464·최종 type38236·build58027·완료 browser56956·나머지11경로47096·
디자인 비교83044·복구 probe81394·DB/파일 대사75226·최종 root73812 모두0으로 수집했다.
hosted CI/전체 회귀·새 모델의 실제 backend와 동시 제품 브라우저는 이번에 실행하지 않았다.
판단은 현재 `gpt-6.1-sol`/`xhigh` native CLI 세션에서 수행했고 재귀 CLI는0이다.

## WSL 점검과 보존

두 UI를 유지한 최초 실제 WebGL 검증은 합 RSS 상한을 초과해 수용하지 않았다.
단일 실행기로 줄인 뒤에도 초과하여 **5173만 점검 중단**했고5174의 진행 현황·API·worker는 계속 유지했다.
중단 전 실제 readonly SCRAM으로 원 DB/파일/권리/키와 비실행 상태를 기록했다.
5173의89개 queued 행은10/09 원 backup의 attempt0/lease 없음인 시험 행이며 조회 전용 서비스에는 worker가 없다.
기동 중인 사용자 계산이89개라고 해석하지 않는다.

원 legacy guardian65028은 정확한 PID/start/boot·pidfd SIGTERM 후 종료0·소유 PG/프로세스0을 수집했다.
같은 인증 backup/source로 `run-v12`를 기동하고 후보5175의 실제 원 응답 대사 뒤5173으로 전환했다.
동일 inline 진행 entry/script/feed를 다시 적용했고 접속 토큰만 새 안내로 갱신했다. 원 안내 파일도 보존했다.
새 legacy guardian16126과 기존 modern49094는 계속 실행 중이며 종료0을 주장하지 않는다.

복구 뒤 modern의 jobs112/events370/attempts37행·기존464파일·권리/서명 키는 모두 동일했다.
legacy89행도 원값 그대로이며 생장47,809시점·관리5사건·수확47,813행/결과 키·원 DB counts가 일치한다.
원본2,148항목·기준271경로 중270개·기존 frontend7핵심 파일을 보존했다.
나머지1개는 위 API 계약의 append-only 설명 변경이며 전후 SHA를 명시했다.
현재 frozen assets172/source194·이전 assets171·원 frozen source/자산과 보호 root4를 확인했다.

수용 guard의 최대 단일 RSS434,012,160bytes·합1,043,132,416bytes는512MiB/1GiB 안이다.
0.25초 표본·FD4→4·소유 임시 프로세스/PG/passfile0을 확인했다.
최초 fixture import/정책 가정/시험 연결·중복 selector, build GC 설정, 메모리 초과,
디자인 도구의 browser 경로와 계약 설명 미선언 보존 실패는 기계 증거에 실패 그대로 남겼다.

## 디자인·남은 작업·일정

12ui-design의 완료/보류/빈 출력3상태를 **기존 원 LayerDoc**과 비교했다.
비교는 정상 종료했지만 요소 겹침28.6%/30.6%/18.4%로 최종 디자인 일치 수용은 아니다.
제안의 생산량·가짜 진행률/작물 문구와 정적 그림을 실제 WebGL 대신 적용하지 않았다.
새 표/진단·원값/단위/접근성·기존 승인 잎 자산을 유지했으며 최종 통합 UI의 디자인 작업은 남는다.

다음은 `crop-greenhouse-ventilation-confirmed-prefix-api`다. 확정 selector의 원 sample/event·현재 권리·
전진/취소·변조/미확정 거부·조회 계산/쓰기0·실제 SCRAM/TLS 정상/보류/취소·원 terminal 일치를 수용한다.
이어 계산 중3D에서 실제 unpaused worker와 같은 원 값/UTC/WebGL→terminal·재접속/취소를 확인하고 사용자 적용을 진행한다.
부모3D와 사용자 적용 체크는 열어 둔다.

잠정 남은 작업량은 API0.75–1.5시간+실제 웹0.5–1시간+사용자 적용0.75–2시간, 반올림 **2–5집중시간**이다.
WSL 점검과 실제 검증 실패가 발생하면 관측에 따라 갱신하며 완료 약속으로 표시하지 않는다.
실제 품종/독립 농장 자료0·전체 작기·생산량/자원 구매/Decimal 경제·최종 UI·G0–G4는 미완료다.
따라서 전체 production 제품 완료일은 아직 미정이다.
