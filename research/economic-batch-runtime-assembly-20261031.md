# 소유 생산 batch의 명시 서버 조립 — 2026-10-31

[ApiRuntime](../backend/app/api_runtime.py)에 선택한8종/schema4 source를 연결했다.
[계약](../contracts/economic-batch-runtime-assembly-v1.md),
[기계 증거](artifacts/economic-batch-runtime-assembly-20261031.json)와
[실제 TLS 사례](artifacts/economic-batch-runtime-case-20261031.json)를 남겼다.
**기존 서버 조립에서 두 source family를 함께 사용하고 새 runtime 객체가 저장된 원문을 읽는다.
자동 소비자·SDK/비용 UI와 사용자 서비스 배포는 후속이다.**

## 구현과 보존 경계

ApiRuntimeDependencies의 keyword-only economic_batch_source_factory는 기본 None이다.
None/callable을 검사하고 policy.economic_batch_source_storage와 제공 여부가 맞아야 한다.
불일치는 JobStore 생성/factory/사설 경로 접근 전에 거부한다.
선택하면 기존 market_source_factory가 정확한 MarketSourceStore를 계속 제공해야 하며
새 factory는 같은 current_principal과 정확한 EconomicBatchSourceStore를 제공한다.
서버의 기존 JobStore/hold/context로 EconomicBatchAuthority를 조립하고 create_app에 명시 주입한다.
추가 runtime 객체는 economic_batch_authority이며 기본 None이다.
새 클래스/큐/운영 프로필·DB 역할이나 의존성을 만들지 않았다.

기존7종/schema3 source 등록과 새8종/schema4는 별도 표/판본·scope를 유지한다.
같은 provider/DSN/schema/정책/로그인과 source/hold/context의 원 identity를 확인한다.
오류는 고정 API runtime assembly rejected이고 private 값/원문을 반환하지 않는다.
이 단계는 서버 조립 라이브러리 수용이다. 기존 사용자 DB/키·설정과 실행 서비스를 변경하지 않았다.

## 통과한 검증

- **최종 신규12 + 기존149 = 고유161검사**를 같은 production 코드에서 통과했다.
  이전 보호 HTTP20·원 source 등록/조회/인증/ApiRuntime129를 포함한다. 단독12/반복 결과를 다시 합산하지 않았다.
- factory 부재/flag 불일치와 비 callable을 거부했다. 불일치 때 JobStore/factory 호출0을 계측했다.
  잘못된 source type/legacy source·다른 provider/DSN 문자열/schema/profile과
  기존 factory에 새 source를 바꿔 끼우는 경우를 거부했다.
  create_app 직전 source provider의 늦은 변경도 기동을 차단했다.
- 실제 소유 host SCRAM의 같은 DB에서 두 source family를 등록했다.
  실제 ApiRuntime.service를 두 번 순차 기동해 인증서를 검증하는 HTTPSConnection으로 통신했다.
  실제 생산 batch 접수/재시도와 기존 source 등록→계산 접수202/queued404→**명시 worker** 완료를 확인했다.
- 같은 프로세스에서 새 runtime/JobStore/authority 객체를 조립해 원10,460bytes와 최초 publication ID/시각을 읽었다.
  이전 객체의 결과 cache를 사용하지 않았다. 별도 OS 프로세스/자동 consumer 수용을 뜻하지 않는다.
- 실행 scope 없는 읽기 grant·인증401, 같은 resolver의 현재 authoritative scope 변경 시422와 복원 뒤 원문 일치를 확인했다.
  금액 진입 차단/실제 SQL 계측으로 새 runtime 결과 조회 계산/SQL쓰기0을 대사했다.
- 첫 RED는 optional factory 계약 부재의 TypeError였다. 이어 테스트가 dict getter를 DTO로 잘못 취급한1fail은
  기존 OwnedEconomicRecord 검증/JSON 변환을 사용해 고쳤다. 제품 getter/원 숫자를 바꾸지 않았다.
  최종 실제 서비스 객체의 TLS와161검사/정리를 수용했다.

PG16.15 별도 소유 클러스터·16MiB shared_buffers를 사용했고 기존 사용자 DSN/비밀번호를 읽지 않았다.
PID512MiB/합1GiB·600초 감독, FD/소유 잔여0과 원4,500항목·repo source 보존을 기록했다.
전체 backend/frontend suite·새 브라우저·사용자 배포는 실행하지 않았다. 커밋 뒤 CI exact head는 별도 receipt로 기록한다.

## 원 자료·화면·판본

부모737source/2출력·private12/external12와 accepted supplement4/external2,
공유 integration11의 원 Git snapshot/current bytes를 확인했다.
이번 변경인 ApiRuntime은 부모의 Git bytes와 새 회귀를 연결하고 새 수용 커밋의 integration snapshot에 넣는다.
수치/모델과 기존 HTTP/DTO 코드는 변경하지 않았다.
UI745private/46external·원 source687/출력4, 5184의238정적 파일/실제 HTTP·원 identity/첫17:03 KST 만료를 보존했다.
만료된5181은 원 종료/233정적 파일·정책/과거 실제 증거 지문으로 확인했고 재시작/연장하지 않았다.
이전 모든 raw archive를 이번에 재실행하지는 않았다.

native gpt-6.1-sol/xhigh·CLI0.157.1 turn 2026-10-31T05:43:16.607Z와 판단/출력을 기록했다.
재귀 CLI/새 agent·실제 농장 자료/계수/요금 채택0, 독립 국내 raw0·G0–G4 미평가/R2 미승인을 유지한다.

## 다음 한 단계

`economic-batch-automatic-consumer`로 기존 discovery/loop의 닫힌 판본/worker/outcome 목록을 확장한다.
정확 economic-batch-calculation-input-v1만 발견하고 새 worker의 _access 결속을 명시 검사한다.
실제 HTTP 접수→자동 계산/원자 게시→fresh 원문 조회, 다른 queued 작업 배제·중복 재선택0,
취소/lease/reclaim·현재 권한/근거·기존 소비자와 원 자료/화면/WSL 보존이 수용 기준이다.
새 큐/서비스 체계를 만드는 작업은 필요하지 않다. 이 단계2–3집중시간 초안이다.

이후 원 저장 창/독립 가정 비용의 기간 결속1–2시간→strict SDK/같은 선택 UI2–4시간 초안이다.
제한된 합성 비용 연결의 남은5–9집중시간이며 달력 완료일/전체 제품 약속은 아니다.
실제 품종/긴 작기·설비/구매/청구·다회 수확/경제·거시/수급·자율 비교와 독립 농장/배포·R2는 별도다.
외부 자료/검증 일정이 없어 전체 제품 완료일은 미정이고 전체 goal active/incomplete다.
