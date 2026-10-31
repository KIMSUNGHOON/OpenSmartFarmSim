# 미수확 생산 batch의 조건부 기간 비용 — 2026-10-31

[새 계산 커널](../backend/app/economic_production_batches.py)과
[schema4/원장 v10 계약](../contracts/economic-production-batches-v1.md)을 수용했다.
평가기간 안 수확이 없는 소유 선언 batch의 생산비를 원 V/F와 현금에 반영한다.
**계산 커널만 구현했다. 제품 저장소/등록·API/worker·3D 비용 UI는 아직 연결하지 않았다.**
[현재3D](http://localhost:5184/supply-material-quantities-replay.html)는 기존 상태로17:03 KST까지 유지한다.
[기계 증거](artifacts/economic-production-batches-20261031.json).

## 변경과 의미

기존 schema3와 경제 원장 v9의 코드는 변경하지 않았다.
새 판본은 필수 batch ID/revision 목록과 trusted repository의 `get_production_batch`를 추가하고,
원 불변 scenario/input pin·tenant·시장 hold 검증 및 Decimal128 exact-domain 산술을 상속한다.
소유 batch의 사용자 가정/시작 시각·적용 기간·이용 가능 시각/권리·불변성을 전후 대사한다.
기초 판매 재고 batch 재사용·미선언 batch·시작 전/기간 밖 비용·중복과 변경된 소유 입력은 거부한다.

수확·판매·수확0 사건을 생성하거나 production을 period로 바꾸지 않는다.
공통 비용·sale 비용을 생산 batch로 배분하거나 새 합계에 다시 넣지 않는다.
미수확 batch의 생산비는 기간 비용이며 판매 가능 kg/재고 가치나 매출을 만들지 않는다.
같은 기간 나중 수확이 있는 원 사례는 기존 수치·재고·현금 결과를 보존한다.

batch별 변동/고정 발생액·기간 지급액·기말 잔여 미지급액과 수확 사건 선언 여부를 제공한다.
돈은 Decimal/KRW이고 새 가격·구매량/단위 변환이나 반올림 정책을 만들지 않았다.
지급일·금액이 미확인이면 현금/잔여 미지급액도 null과 기존 hold를 유지한다.
기간 뒤 지급하기로 명시한 가정은 현재 지급0·기말 미지급·미래 schedule로 분리한다.
지급일이 없지만 미지급은 확정된 별도 상태를 이번 입력에 추가한 것은 아니다.

결과 ID는 원 scenario SHA·소유 batch SHA·새 코드/기존4구성 코드·formula 판본을 결속한다.
같은 입력은 같은 bytes로 재생한다. 원 거래/숫자/비용 입력은 생성·수정하지 않는다.

## 통과한 검증

- **신규37 + 기존 경제169 = 고유206검사**를 같은 최종 코드에서 통과했다.
  미수확/후속 수확·여러 batch/공통비·고정비/부분 지급·미확인/미지급·KST 월 경계,
  기초 재고/과거 비용 재부과 차단, 소유권/현재/늦은 변경·record/불리언 불변 표시·우회 입력,
  Decimal 대수/128자리 초과·512/513batch·입력/소유 record/응답의 독립2MiB 제한을 확인했다.
  기존 세 경제 시험 파일 전체를 포함하며37을206에 다시 더하지 않는다.
- 실제 별도 프로세스에서 소프트웨어 전용 자체4사례(지급·기간 뒤 지급·지급 미확인·동일 기간 수확)를
  **300자리 Decimal**의 직접 발생액/입출금·월 합계·미지급/배치 합계와 대사했다.
  각2회 계산의 bytes/결과 ID가 같고 원 입력·수확/판매 사건 개수를 보존했다.
  전체8회 계산/대사는0.055149초였다. 이는 합성 QA이며 농장 비용/구매량 관측이 아니다.
- 같은 프로세스에서 crop/job/thermal import0, DB/network/process·CLI0과 FD4→4를 확인했다.
  결과의 숫자 입력/돈은 JSON 문자열이며 이진 float 결과가 없음을 확인했다.
  입력·소유 기록·결과/원문 해시는 private 불변 영수증에 보존했다.
- 최초 missing-module RED 뒤 구현했다. 첫27pass/1fail은 우회 입력을 계산기에 전달하기 전
  시험용 저장소가 잘못된 dict를 읽은 시험 설정 오류였다. 이를 분리한 확장 검사에서
  숫자1을 true로 받는 실제 경계를 발견해 JSON boolean만 받도록 수정했다.
  이후 추가 시험의 함수 삽입 범위 오류1을 고쳤고37/206·별도 프로세스가 최종 통과했다.

## 보존·자원·실행

기존701source/2output/private23/phase6·추가2pin, 원 CAS/기존 GUI 계보와
현재238파일의 실제 HTTP bytes/hash/no-store/CSP·PID/boot/ticks·첫 만료를 보존했다.
기존 경제 코드와 schema3/제품 worker/API/화면 변경0이다.
새 kernel/type·집중 검사 외 전체 backend/frontend suite·새 browser/배포/hosted CI는 실행하지 않았다.

WSL 단일 phase/PID512MiB·합계1GiB·600초 guard를 사용했다.
최종37은2.048초/PID76,668,928bytes/합계247,562,240bytes,
전체 관련206은3.098초/79,110,144/250,097,664,
별도 프로세스는1.527초/46,981,120/217,952,256,
보존은6.111초/62,971,904/234,119,168이었다.
모든 phase에서 원4500감시 항목과 source를 보존했고 소유 자손 잔여0·FD4→4였다.
Windows/전체 host RSS는 측정하지 않았다.
실제 native gpt-6.1-sol/xhigh·CLI0.157.1 turn `2026-10-31T02:27:02.881Z`의 지문/출력을 기록했다.
재귀 CLI·새 agent·실제 자료/계수·요금 채택은0이다.

## 다음 연결과 외부 의존성

다음은 **소유 생산 batch/schema4 입력의 불변 등록·현재 조회 연결**이다.
현재 `market_source_store`의 typed kind/SQL CHECK는 batch/schema4를 지원하지 않고,
기존 source/candidate/scenario repository에도 `get_production_batch`가 없다.
이번 별도 프로세스는 명시 시험용 소유 저장소이며 실제 제품 권한/DB 수용으로 보고하지 않는다.
새 버전의 저장 경계를 기존 소유권·불변 job 입력/권리·원장 검증에 연결해야 실제 사용자 입력을 받을 수 있다.

수용 기준은 실제 소유 등록/참조 조회·원 bytes/최초 기록·같은 요청 재시도/충돌/rollback,
다른 tenant/판본/기간·현재/늦은 변경 거부, 조회 계산·쓰기0과 기존 schema3/원 표·행/권한/화면 보존이다.
새 선언·권한/저장 경계1–2집중시간 + 작은 등록/조회·실제 검증2–4시간의 초안이며,
기존 typed kind/역할 감사의 정확한 변경 범위 확인 뒤 갱신한다. worker/SDK/3D 연결은 포함하지 않는다.
그뒤 원 저장 창/소유 경제 입력 결속→실제 계산 worker→strict SDK/같은 선택 UI로 진행한다.

작물 한 작기/반복 성장과 실제 품종/독립 농장 raw0, 설비·급배액/계량·구매/청구 권리,
생과중·다회 수확/판매·거시/수급·자율 비교·최종 제품/R2는 남는다.
개발과 외부 자료 확보를 병행하며 실제 예측/추천 게시에는 원 관문 증거가 필요하다.
G0–G4 미평가/R2 미승인·전체 goal active/incomplete·전체 완료일 미정을 유지한다.
