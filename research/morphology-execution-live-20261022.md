# 실제 접수·자동 계산·저장3D 연결 — 2026-10-22

상태: **자체 합성 입력의 소프트웨어 경로 수용**.
[성장 실험실](http://localhost:5176/)에서 접수 → 실제 자동 계산 → 불변 저장 → 같은 UTC의 줄기3D를 확인한다.
사용자 전용 Chrome 탭은 마지막 저장 시점/정지로 열어 두었다. 새로 연 탭의 인증 설정은 별도이며 토큰은 공개하지 않는다.
전체 제품 UI·실제 품종/작기·생산량/경제·자율 작물 선정과 G0–G4는 미수용이다.

## 연결한 범위

[E1–E3](../contracts/crop-morphology-execution-v1.md),
[보호 HTTP](api-crop-morphology-execution-20261022.md),
[기존 자동 consumer](morphology-automatic-consumer-20261022.md)를 재사용한다.
`web/src/morphologyExecution.ts`의 닫힌 DTO/원 root 검증과
`MorphologyExecutionPage.tsx`의 접수·실제 단계/취소·현재 권리/저장 재생을 연결했다.
작업 ID는 localStorage, 접근 토큰은 탭의 sessionStorage에 보관한다.
응답이 유실된 접수는 원 요청으로 다시 확인하며, 미확정 새 접수가 있으면 이전 완료 작업으로 복원하지 않는다.
완료 화면은 유휴 중 렌더링/주기 조회를 멈추고 명시 새로 확인 또는 탭 복귀 때 현재 권리를 확인한다.

자체 합성 검토 전용 `research/serve-owned-morphology-preview.py`는 기존 역할·FarmAuthoringService,
입력/현재 검토·서명 authority, 표준 HTTP route installer와 deterministic loop를 조립한다.
원 서비스/DB를 복사하거나 교체하지 않고 별도 자체 합성 fixture DB/키를 쓴다.
772개 source 파일을 동결하고 현재 auth/TLS·검토/권리를 적용한다.
공개 제품의 일반 입력 목록·계정/배포 factory는 이 연구 도구의 수용에 포함하지 않는다.
새 제품 schema/role 정의·패키지는 추가하지 않았다. 자체 fixture 역할은 기존 설치 절차로 생성했다.

## 통과한 검증

| 경로 | 실제 확인 |
| --- | --- |
| hosted UI | [CI39680266179](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39680266179), source `6c2eb842b644cdd6e1f7c0fd7979381e6c088726`: typecheck·집중 unit50·Chromium16·build·audit0 |
| 실제 HTTP/Chrome | 가로채기/응답 mock 없이 접수2건, 실제 취소1건, 자동 계산/완료1건, 원12 DTO |
| 수치와3D | 첫/끝의 원 UTC·기관 ID/길이·정확 분수 출현, 표/그래프·실제 mesh와 geometry 변화 |
| 메뉴/새로고침 | 같은 job/result/최초 calculated_at 유지, reload 추가 POST0; 자동 재생/정지·유휴 renderer 정지 |
| 현재 권리 | 소유 합성 권리만 시험 철회 → 실제422 → geometry/표/그래프/결과 metadata 제거; 원 권리 bytes 복원 뒤 같은 결과/POST0 |
| cold restart | 새 API/PG만 정상 종료/재기동; 같은 DB/키·job/result/calculated_at 복원/POST0; DB25표 전체 행 SHA 전후 동일 |
| 보존/WSL | 기존190/223/137/175파일 보존, 새 정적 파일의 실제 HTTP200/bytes 대사, 원6root 보존·새 runtime v5 ready |

처음/마지막 추적 축 길이는 `0.045663424634695575 → 0.14526009414404015 m`, 절간은 `3 → 6`이다.
이 수치는 하루의 명시 합성 계산이며 실제 식물 키가 아니다.
고정 복엽3개·반경/표면은 제작 외형이다. 실제 잎 수/면적·과실/숙기·수확을 계산했다고 표시하지 않는다.

실제 화면: [처음](artifacts/morphology-execution-first-20261022.png),
[마지막](artifacts/morphology-execution-last-20261022.png),
[모바일](artifacts/morphology-execution-mobile-20261022.png),
[권리 거부](artifacts/morphology-execution-denied-20261022.png).
부모가 실제 마지막/모바일 이미지를 확인했다. 이는 사용자의 최종 사실감 승인이나 R2 완료가 아니다.

실제 browser 관측44.389초/171sample의 WSL 합계 peak1,065,050,112bytes,
권리13.255초/51sample의1,041,244,160bytes,
cold browser14.558초/56sample의1,043,066,880bytes였다.
모두 .25초 sample, PID peak124,948,480bytes로 지정 상한 이내였다.
Windows Chrome/Node 메모리는 포함하지 않아 공통 용량·전체 부하를 수용하지 않는다.
새 runtime은 계속 원6+자손/자체 tree의 상한을 감시한다.
의도적으로 종료한 v4는 owned remaining0, 기존6개 생존을 확인한 뒤 같은 동결 입력의 v5를 시작했다.
WSL 재부팅·자동 복구·장기 uptime 시험은 수행하지 않았다.

## 실패·수정과 수용 한계

- 처음 frozen snapshot의 LICENSES 누락과 비어 있는 blob 디렉터리0700을 수정했다.
  이 shared blob 운송은 ContentAccess의 디렉터리0750/파일0640을 요구하며 private 키/설정과 다르다.
- full API를 조립한 이전 owned runtime과 두 native 시도는1GiB 상한으로 미수용이다.
  소유 tree만 정리하고, 같은 생산 route installer의 최소 조립과 작은 PG 설정으로 위 최종 검증을 통과했다.
  검증·권리·역할 검사를 생략해 메모리를 줄이지 않았다.
- 첫 WebGL CI의5초 시간 초과는 미수용이다. 진단과 기존 renderer의60초 대기 범위 뒤 최종 CI를 수용했다.
- 미확정 새 접수의 이전 작업 복원과 H2의 status role 때문에 heading이 사라지는 문제를 수정했고 회귀를 포함했다.
- 실제 계산 중 상태 조회에서 일시503 한 건을 관측하고 다음 실제200/완료로 회복했다.
  정확한 원인을 이번 자료로 단정하지 않는다. 무한 완료/가짜 진행률로 바꾸지 않는다.
- 전체 web/backend 회귀는 이번에 실행하지 않았다. 재조회의 계산/import/쓰기0 계측은
  [E3 native/fresh](crop-morphology-execution-query-20261022.md)의 증거다.
  이번 실제 GUI의 재조회는 POST0·동일 원 결과/계산 시각·DB 행 지문으로 확인했으며 직접 계측0이라고 확대하지 않는다.

12ui draft/resume의 `Corpus inspiration response is ambiguous` 실패는 앞 외형/재생 기록과 같다.
새 승인 시안/디자인 일치 수용은 없고 기존 서체·색·3D 스타일을 재사용했다.
Chrome DevTools MCP가 없어 이미 승인된 전용 Windows Chrome/CDP를 사용했다.
새 패키지·외부 자산·제3자 연락/로그인·원 제한 자료 배포는0이다.

## 다음 경계와 외부 의존성

이제 고정 제작 잎을 계산 형태로 바꾸기 위한 **잎 면적 식/차원·명시 초기조건의 한 기관 커널**을 먼저 분리한다.
원 식/단위 대조 → 독립 고정 합성 수치/경계 → 현재 기관 시계·명시 초기/출현 목록 → 별도 불변 판본 → 같은 UTC3D 순서다.
각 수용 전 현재 동결 UI/수치는 유지한다. 지역 연구·자율 작물 선택·전체 한 작기/생산·자원/경제의 완료일은 미정이다.
실제 Axiany 초기 기관/계수·권리와 독립 농장 측정은 확보0이다. 이 확보일을 합성 소프트웨어 작업량으로 추정하지 않는다.

현재 native `gpt-6.1-sol / xhigh` context22:03:05.125Z,
LF 포함 SHA `dbc644831a351328d76893e8823fbe5f9b38ec4c60822ba20c977a8994dbd2cc`를 확인했다.
재귀 CLI0·실제 농장 Run0·독립 승인0이며 원본 private 증거의 hash와 관측은
[공개 증거](artifacts/morphology-execution-live-20261022.json)에 기록했다.
