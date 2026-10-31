# 소유 생산 batch 계산의 서버 권한·접수 — 2026-10-31

[서버 라이브러리](../backend/app/economic_batch_calculation.py)와
[계약](../contracts/economic-batch-calculation-admission-v1.md)을 실제 소유 PostgreSQL에서 수용했다.
[기계 증거](artifacts/economic-batch-calculation-admission-20261031.json).
**실제 등록 입력·서명 hold/결정 문맥으로 계산 작업의 불변 의도를 접수한다.
금액 계산·결과 게시·제품 HTTP/자동 worker·UI는 이번 단계에 추가하지 않았다.**

## 동작과 경계

EconomicBatchAuthority는 실제 JobStore·EconomicBatchSourceStore·MarketHoldStore·ThermalRunStore의
같은 schema/authority 정책/DSN·동일 principal provider와 고정 객체를 검사한다.
명시 batch source 프로필과 실제 grant audit가 필요하다. 허용된 읽기 getter만 노출하며
각 호출 전후 현재 scope와 연결을 검사한다. 테스트 facade나 메모리 숫자 원장은 사용하지 않는다.

요청은 scenario ID/revision/SHA·idempotency key만 받는다.
등록된 schema4/최초 작업 UUID·원문 SHA를 현재 조회하고, 원 v10 커널의 계산 전 검증을 재사용한다.
숫자/소유 batch·기간·decision_at와 실제 서명 hold/결정 문맥을 대사한다.
원 시나리오/pin·검증된 입력/batch·hold/context의 지문을 새 작업 입력에 고정한다.
commit 전 같은 현재 근거·권한·객체 연결을 다시 검사한다.

`economic-batch-calculation-input-v1`은 v10·원 scenario SHA/최초 source 작업 UUID·근거 SHA를 저장한다.
같은/동시 요청은 최초 작업과 bytes/시각을 반환하고 key 충돌·늦은 철회/연결 변경은 rollback한다.
접수는 실행 scope를 요구하며 읽기용 참조 준비는 읽기 scope만 요구한다.
참조 검증 성공은 금액 산술이나 실제 농장 비용/추천의 승인이 아니다.

## 통과한 검증

- **최종 신규23 + 기존 source20 + 기존 경제206 = 고유249검사**다.
  최초 missing-module RED와 읽기 준비에 실행 scope를 요구한 실제 DB의1fail RED를 보존했다.
  초기248 회귀 뒤 읽기 scope 경계를 고쳤고, 최종 신규23 전체를 다시 통과했다.
  기존226의 production 파일은 전후 동일하다. 반복된22개를 다시 합산하지 않았다.
- 실제 SCRAM/등록 입력·서명 hold, 같은/동시 재시도·충돌, 원 source UUID/bytes/시각,
  5개 현재 scope, 늦은 scope/객체 변경과 작업/사건 rollback, 누락 입력·batch/기간·서명 키,
  다른 tenant/DSN/schema/provider/profile, fresh authority와 한글 UTF-8 지문을 확인했다.
- 접수에서 두 ledger의 calculate와 내부 금액 계산을 차단한 채 성공했다.
  실제 SQL command tag/대상은 작업·사건 INSERT만 허용됐다. source 행과 publication은 생성/변경하지 않았다.
  별도 fresh 실제 authority에서 원 v10의 합성20원 비용/현금−20원·hold를 대사했다.
  이는 자체 가정 QA이며 농장 관측이나 신규 결과 worker의 실행 증거가 아니다.

PG16.15의 별도 소유 클러스터·16MiB shared_buffers·host SCRAM을 사용했다.
원 사용자 서비스 DSN/비밀번호를 읽거나 연결하지 않았고 각 소유 서버/암호 파일을 정리했다.
최종23은 guard75.180초/PID141,824,000bytes/합계385,294,336bytes,
248회귀는92.389초/143,630,336/419,803,136이었다.
한 phase/PID512MiB/합계1GiB/600초, 소유 잔여0·FD4→4·보호 root/4,500항목을 유지했다.

원716source/1output/private25/external45와 이전 통합5지문을 실제 cb23286e Git 판본/현재 파일로 대사했다.
기존 숫자·CAS/GUI·238파일의 실제 HTTP/원 PID·boot/ticks·첫 만료를 보존했다.
이전 cold proof 재사용은 신규 계산/검증 수에 넣지 않았다.
현재 [저장3D](http://localhost:5184/supply-material-quantities-replay.html)의 첫 만료는17:03 KST다.
기존 DB/설정·API/경제 입력v1–v3·worker·3D 빌드의 변경/배포는0이다.
전체 backend/frontend suite·새 브라우저/hosted CI는 실행하지 않았다.

native gpt-6.1-sol/xhigh·CLI0.157.1 turn `2026-10-31T03:51:15.858Z`와 판단/출력 지문을 기록했다.
재귀 CLI·새 agent·농장 자료/계수·요금 채택은0이다. G0–G4 미평가·R2 미승인을 유지한다.

## 다음 단계와 일정 근거

다음은 `economic-batch-execution-worker`다. 정확한 접수 입력의 실제 lease→현재 근거/코드·환경 확인→
원 v10 계산→취소/만료·현재/늦은 권한/원 입력·근거 전후 대사→불변 결과/manifest·성공 원자 게시를 구현한다.
기존 JobStore의 파일·publication·lease 구조를 재사용하며 별도 결과 테이블 필요성은 아직 확인되지 않았다.
그뒤 `economic-batch-stored-result-query`에서 fresh 읽기의 실제 입력/근거·원 결과 SHA와
현재 권한을 검사하고, 금액 재계산/SQL 쓰기 없이 동일 결과를 반환해야 한다.
worker1–2h + 결과/조회1–2h + 실제 DB/취소·fresh 검증1–2h = **3–6집중시간 초안**이다.
이는 코드/작업 계약을 확인한 추정이며 전체 제품이나 UI 완료 날짜가 아니다.

이후 원 저장 창·독립 사용자 가정 비용의 기간 관계→strict SDK/같은 선택 UI를 연결한다.
열·수분 적분을 구매량으로, 탄소/과실 수량을 생과 수확·매출로 간주하지 않는다.
실제 품종/긴 작기·독립 국내 raw0·설비/계량/구매/청구·다회 수확/정산·거시/수급·자율 비교,
최종 제품/배포·G0–G4/R2와 전체 완료일은 미완료/미정이다. 전체 goal active/incomplete다.
