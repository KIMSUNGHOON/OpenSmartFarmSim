# 현재 작물 모델의 장기 계산 준비: 상태·이력·forcing

2026-10-31 KST. **설계/제한 탐색 수용, 새 실행 module 미구현.**
[계약](../contracts/supply-season-state-history-forcing-v1.md)과
[기계 판독 증거](artifacts/supply-season-state-history-forcing-contract-20261031.json)를 함께 읽는다.
전체 goal은 active/incomplete, 독립 국내 raw0, G0–G4 `not_assessed`, R2 `not_approved`다.

## 확인한 현재 범위

앞 단계의 [동일 저장 상태3D·과실 수량 화면](supply-production-stored-screen-20261031.md)은
자체 합성의305181/1024초부터512초까지38시점을 표시한다.
[사용자 화면](http://localhost:5182/supply-production-replay.html)은 기존 고정 수명인
**오늘15:19 KST**까지다. 이번 설계 작업으로 화면이나 모델을 교체하지 않았다.

실제 원 공개 root `84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476`를
기존 strict reader로 다시 검증하고62개 원 blob·6Context/33CP/38프레임을 확인했다.
별도 공개 frame38개의 전체 원값도 대사했다. 마지막 상태는176좌표,11잎/13stem-root stock/12절간,
global124/lifetime185/point7장부다. 저장 branch 유량에서 shoot 시계를 독립 Fraction 산술로
다시 구성한33CP가 모두 일치했다.

| 실제 관측 | 설계에 미치는 영향 |
|---|---|
| Context가181,551→506,491→849,761→1,222,293→1,613,418→2,034,765bytes로 증가 | 과거 영수증을 현재 상태와 분리해야 한다. |
| 마지막 Context의 receipts1,814,076bytes, descriptor142,040bytes, seed129,826bytes | 현재2MiB 상한의 여유는62,387bytes다. 상한 증가보다 이력 paging을 먼저 설계한다. |
| [repeat Context](../backend/app/crop_supply_morphology_repeat_context.py)의 복구가 모든 receipt를 검증/seed 재구성 | hash만 빼내고 검증을 없애면 안 된다. cold는 페이지 검증, warm은 충분한 현재 상태와 현재 fence가 필요하다. |
| [현재 stage](../backend/app/crop_supply_morphology_birth_stage.py)는 canopy energy/LAI로 온도를 계산 | [옛 stream](../backend/app/crop_cycle_stream_execution.py)의 직접 canopy 온도 forcing/해석적 시계를 그대로 쓸 수 없다. |
| [현재 flux](../backend/app/crop_supply_morphology_books.py)도 forcing/fruit entry를 직접 읽음 | RHS와 flux가 같은 active span을 받아야 열·수증기·개체 유입을 일관되게 적분한다. |
| [기존 generator](../backend/app/crop_stem_root_stock_dynamics.py)는600초/4096step/32768scalar 범위 | 512초는 이번 fixture의 끝이다. 모든 기존 계산이600초라는 뜻이 아니며 새 family는 별도 수용을 받아야 한다. |
| 옛166일 cycle은121좌표·whole-second UTC와 다른 법칙/계보 |128record CAS page·예산/실패 prefix 방식은 참고할 수 있지만 old handle/수용을 이전하지 않는다. |

## 비교한 세 설계와 판단

`codebase-design`의 `DESIGN-IT-TWICE.md`가 명시한 병렬3안 절차를 적용했다.
세 native 위임 세션은 읽기/설계만 했고, 테스트·solver·DB·network·서비스/원 코드 변경을 하지 않았다.
root가 실제 코드와 제한 수치 탐색을 대조해 아래 선택을 했다.

| 대안 | interface/이점 | 채택 범위와 부담 |
|---|---|---|
| Minimal | `open_season` / `advance`. 시계·수지·사건 대기·이력 게시를 한 module에 둔다. | 작은 호출면과 현재 상태/이력 분리를 채택한다. 첫 codec만으로 생장 진척을 완료하지 않는다. |
| Forcing-flexible | capture/write/open/start/restore/advance/history/replay. timeline stream과 epoch를 명시한다. | 동일 active view·정확 edge·단계 순서를 채택한다. 외부 호출면을 모두 노출하면 현 시점의 caller가 배워야 할 것이 커진다. |
| Common caller | stored notebook의 from-result/advance/replay, sealed continuation plan | 실제 저장 CP를 시작점으로 삼고 plan을 고정하는 방식을 채택한다. 수치 실행과 무계산 화면 조회를 한 객체에 결합하지 않는다. |

선택은 **두 연산 + 고정 definition + 별도 reader**다. 순수 RHS/장부는 in-process 함수로 재사용하고
POSIX CAS는 local-substitutable 저장 의존성으로 둔다. 새 agent framework/queue/DB/server는
이 수치 자식에 필요하지 않다. 외부 기상 수집과 farm/worker 통합은 해당 실행 계약에서 수행한다.
기존 accepted module과 테스트는 유지한다.

## 실제 제한 수치 탐색

검증한 원 graph에서 현재 program/organs/costs와 네 고정 typed profile을 읽었다.
기존 pure stage/정확 RK4 combine/flux/장부 함수만 호출했고 old Context/CP handle을 만들지 않았다.
이 탐색은 새 model owner·cursor·저장/복구 구현이 아니며 결과를 제품/화면에 게시하지 않았다.

- 504→512초의 저장 상태176개와 derived가 일치했다.
- 유량을 먼저 구간별로 반올림해 더하면185항 중167항만 원 누산기와 일치했다.
  원 branch 누산기와 stage별 계산 순서를 보존했을 때185항 전체, branch/global124장부와
  lifetime185가 원 결과와 일치했다. 이 차이는 새 판본의 누산 순서를 고정해야 하는 근거다.
- 원 누산기를 계속 사용한512→520초에서는 global124잔차가 기존 예산 안에 있었다.
  shoot age는 정확히 `30939182195569941857/6079859496950169600 degC_day`로 다음 threshold
  `509/100 degC_day`보다 작았다.
- 이어서520→528초를 시도하면 threshold에 도달/통과한다. 이 시도는 수치 탐색에만 썼다.
  새 family의 근 정밀화/물질 입력 없이528초를 확정 상태로 저장해서는 안 된다.

최종 탐색은 RHS20회, 약3.75초, PID최대112,566,272bytes/합계217,133,056bytes였다.
기존4500항목/원 소스와5175·5181·5182 프로세스를 보존했고 owned child0/FD4→4로 종료했다.
이는0.25초 간격의 WSL 관측이며 Windows/전체 host RSS 측정은 아니다.

첫 두 private 감사 시도는 reader의 `(raw,metadata)` 구조와 quantity의 `{value,unit}` 구조를
잘못 읽어 TypeError로 종료했다. 각 guard의 보존/정리를 확인하고 private script를 새 판본으로
수정했다. v3에서 원 상태/clock와 순수 수치 탐색을 통과했고 v4에서185누산기/124장부 대사를
추가 통과했다. 원 코드/자료의 오류 수정이나 제품 테스트 통과로 기록하지 않는다.

## 다음 한 단계와 남은 의존성

다음은 [계약의 첫 자식](../contracts/supply-season-state-history-forcing-v1.md#첫-구현-자식-현재-상태에서-실제-한-구간-계산)
`supply-season-current-state-continuation`이다.
새 판본의 원 상태 import와504→512 oracle,512→520실제 계산,185누적/124장부,
독립 고정밀 수지·2step/full/split/cold·pending528/실패·현재 상태/별도 이력 저장을 함께 수용한다.
**아직 구현/통과하지 않았다.** 잠정3–6집중시간이며 첫 모듈의 실제 결과로 갱신한다.

그 뒤 forcing edge → 실제 pending/물질 전이 → paged 반복/600초 초과 → 주야/응축/관리·기관 수명 →
긴 합성 작기의 수렴/수지 → 저장/같은 시점3D → 생산/자원 환산 → Decimal 경제/거시·수급 →
대응 후보 자율 비교/최종 제품 UI 순서다. 저온/빈 수관/포화·영구기관 증가·제거·CO₂ stock/control 등
현재 미지원 domain을 긴 계산이 저절로 해결하지 않는다.

독립 국내 raw0·실제 첫 품종/초기조건/forcing/관리·물질 전이 및 생산 환산 계수/권리 확보는
합성 개발과 병행한다. farm custody/worker·현재 권리와 G0–G4는 실제 게시 조건이며
이번 수치 개발의 외부 선행 조건으로 확대하지 않는다. 실제 자료 확보일과 추가 물리/관리
구현 분해가 미정이므로 **전체 제품 완료일은 미정**이다.

## 실행/증거 범위

현재 root native CLI는 `gpt-6.1-sol/xhigh`·CLI0.157.1, 세 위임 native CLI는 같은 model/effort·
CLI0.166.0으로 관측했다. 각 실제 session_meta/turn_context의 원 LF 포함 줄 hash와 산출물 hash를
보관했다. shell의 재귀 Codex CLI 실행은0이다. 설계 제안은 gate/승인 자료가 아니다.
원 session/개인 식별자/비밀/제한 자료를 이 문서에 복사하지 않았다.

통과 범위는 원 graph 재검증·38원 프레임·33독립 clock·위 pure 수치 탐색과 최종 보존/문서 검사다.
새 module 단위/통합·cold 수치·전체 backend/frontend suite·전체 제품 CI·실제 농장 검증은 실행하지 않았다.
현재 고정 preview 수명과 원 공개/비공개 권리는 유지했다.
사용자의 `/goal clear` 완료 회신 이후에도 도구는 이전 전체 objective의 active를 반환했다.
교체 완료로 표시하거나 전체 goal을 완료 처리하지 않고, 최신 지시의 model/구현 순서로 계속한다.
