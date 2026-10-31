# 생산 batch 계산의 자동 소비 — 2026-10-31

기존 [discovery](../backend/app/deterministic_job_discovery.py)와
[foreground loop](../backend/app/deterministic_work.py)에 정확한 batch 입력/worker/outcome을 연결했다.
[계약](../contracts/economic-batch-automatic-consumer-v1.md),
[기계 증거](artifacts/economic-batch-automatic-consumer-20261031.json),
[실제 자동 처리 사례](artifacts/economic-batch-automatic-case-20261031.json)를 남겼다.
**실제 HTTPS 접수→별도 Python 프로세스의 발견/1계산/불변 게시→새 runtime의 원 bytes 조회를 수용했다.
자체 합성 계산 처리이며 작물 자동 선정·실제 예측·사용자 배포/비용 UI 수용은 아니다.**

## 구현과 실제 경로

새 economic-batch-calculation-input-v1·EconomicBatchWorker/BatchCalculationOutcome만 명시 등록했다.
loop가 batch worker의 _access로 원 객체/root·현재 권한을 검사한다.
원 tenant/stage·due/만료 lease·불변 입력의 정확 판본 필터와 기존 worker의 현재 근거·원자 게시를 재사용한다.
기존 worker·다른 입력 판본/이벤트/CLI·DB 역할·모델/Decimal 코드는 변경하지 않았다.

API는 원 request-bound principal을 사용하고 worker는 별도의 operator 조립·최소6scope 서비스 principal을 사용했다.
둘은 같은 실제 owned host SCRAM DB/정책·원 source/서명 context/hold를 검증한다.
서명 context/경제 입력은 자체 fixture에서 준비했고 새 HTTP 계산 의도를 접수했다.
작업 ID를 child에게 넘기지 않고 기존 python -m app.deterministic_work --factory로 자동 발견했다.
이 명령은 프로젝트 Python CLI이며 Codex CLI 재귀 실행이 아니다.

## 통과한 검증

- **신규16 + 기존351 = 고유367검사**를 최종 같은 production 코드에서 통과했다.
  소비자/worker 묶음132과 API/이전 모델 소비자 묶음235은 서로 다른 테스트 파일 집합이다.
  초기15/별도1과 반복 결과를 다시 합산하지 않았다.
- 실제 HTTPS 접수202/미완료404→별도 프로세스의 started/attempt succeeded/stopped·정상 exit0과 원1계산을 확인했다.
  page_size2의11조회에서 대상1개만 발견했고 완료 뒤 새 전체 scan의 재선택0을 대사했다.
  다른 판본9개/다른 tenant1개의 원 queued 상태·attempt0을 보존했다.
- 두 실제 ApiRuntime.service TLS listener를 순차 기동하고 인증서 검증을 사용했다.
  새 runtime의 원10,460bytes·최초 publication ID/시각, 실행 scope 없는 읽기 grant를 대사했다.
  현재 authoritative scope 변경 시422·복원 뒤 원문 일치, 금액 진입 차단/실제 SQL 계측의 재계산/쓰기0을 확인했다.
- 실제 discovery 직후6scope 각각의 철회와 값이 같은 다른 source/root 교체는 claim 전 차단됐다.
  실제 계산 뒤 취소는 canceled/게시0, 실제1초 lease 만료 뒤 재임대는 attempt2/게시1이고 옛 token은 거부됐다.
  현재 evidence hold는 금액 진입 없이 hold를 내고 unclosed는 정상 이벤트로 바꾸지 않는다.
- 기존 discovery/foreground CLI·batch worker24·보호 HTTP/서버 조립/API와
  leaf appearance/population·morphology·joint·CO₂·Solar의 닫힌 소비자 경계를 회귀했다.
  전체 backend/frontend suite·새 브라우저/사용자 배포는 실행하지 않았다. CI는 커밋 뒤 exact-head receipt로 기록한다.

첫 RED는 batch worker/판본이 기존 loop에 아직 등록되지 않아 발생한 LoopHold였다.
처음 전체 묶음은600초 wall 한도로 종료되어 수용에서 제외했다. 그 phase의 부분 통과/끝 F를 수용 검사 수에 넣지 않았다.
종료 후 정확한 소유 PG/pytest 종료·해당 테스트 클러스터 디렉터리 삭제를 확인했다.
관련 검사를 두 묶음으로 나눠 각각 정상 PG 정지·FD4→4·소유 잔여0까지 확인했다.
worker의 사설 설정 파일은 정상 처리/오류 경로 모두 부모가 삭제하며 최종 실제 사례에서도 부재를 확인했다.

## 보존과 주장 범위

PG16.15 별도 클러스터·16MiB shared_buffers·host SCRAM을 사용했고 원 사용자 DSN/비밀번호를 읽지 않았다.
PID512MiB/합1GiB·phase600초 상한, 원4,500항목/전체 repo source 보존과 최종 두 묶음의 정상 정리를 기록했다.
부모741source/2출력·private10/external8와 accepted supplement4/external2,
공유 integration13의 현재 bytes/수용 Git snapshot을 대사했다.
이번 discovery/loop 변경은 부모 Git bytes와 관련 회귀를 연결해 새 수용 커밋의 integration snapshot으로 남겼다.
UI745private/46external·원 source687/출력4, 5184의238고정 파일/실제 HTTP·원 identity/첫17:03 KST 만료를 보존했다.
만료된5181은 종료/233고정 파일·정책/과거 증거 지문으로 확인했고 재시작/연장하지 않았다.
이전 모든 raw archive를 이번에 재실행하지는 않았다.

native gpt-6.1-sol/xhigh·CLI0.157.1 turn 2026-10-31T05:55:13.116Z와 판단/출력을 기록했다.
새 agent·재귀 Codex CLI·실제 농장 자료/계수/요금 채택0, 독립 국내 raw0·G0–G4 미평가/R2 미승인을 유지한다.
전체 goal은 active/incomplete다.

## 다음 의존성 보완

원 [결속 계약](../contracts/supply-material-resource-economics-binding-v1.md)은 Cost.id와 포함/누락 범위를 구분해
기존 원장이 산출한 항목 금액을 사용해야 한다.
하지만 현재 [EconomicResult](../backend/app/economics.py#L118)와
[ProductionBatchCosts](../backend/app/economic_production_batches.py#L63)는 총액/batch 합계만 저장한다.
[기존 _costs](../backend/app/economics.py#L651)는 항목 금액을 계산한 뒤 합계로 반환하므로
일부 자원 Cost.id의 독립 금액 근거가 현재 결과에는 없다.

따라서 다음은 `economic-cost-line-trace`다. 같은 기존 Decimal 수식으로 Cost.id별 금액/입력 판본·단위·
variable/fixed·목적/batch/판매 참조·발생/지급·미확인 상태를 산출하고 원 총액/batch 합계와 대사한다.
혼합 품목·부분 선택/중복·미지급/기간후 지급·현재/늦은 입력 변경·독립 Decimal oracle와 기존v10 보존을 검증한다.
기존 v10 결과를 덮어쓰거나 조회에서 금액을 재계산하지 않고 새 versioned 산출물로 남기는 경계를 확정한다.
첫 커널/독립 산술 slice1–3집중시간 초안이며 저장/실행/조회 연결은 그 실제 출력 계약 뒤 분해한다.

그뒤 원 material root/projection/result SHA·정확 window와 독립 사용자 가정 Cost/input·구매/청구 기간을 결속한다.
열/수분8counter를 구매 전력·물로 바꾸지 않고 수초 창과 월별 비용을 다른 범위로 표시한다.
현재 연구 root의 FarmScenario 결속 부재는 제품 게시 hold로 유지한다.
그다음 strict SDK/같은 선택 UI와 실제 브라우저를 수용한다.

기존 남은3–6시간의 단순 합산은 항목별 금액 근거의 누락을 포함하지 않아 사용하지 않는다.
전체 연결 공수는 새 trace의 저장/실행 경계까지 분해한 뒤 갱신한다.
실제 품종/긴 작기·설비/구매/청구·다회 수확/경제·거시/수급·자율 비교와 독립 농장/배포·R2,
전체 제품 완료일은 외부 자료/검증 일정이 없어 미정이다.
