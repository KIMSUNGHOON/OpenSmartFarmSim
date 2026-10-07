# 검증 계산 결과의 현재 조회·전체 재생 — 개발 계약

2026-10-07 KST. [작은 signed DB/농장 결속 수용](../research/crop-cycle-calculation-result-publication-implementation-20261007.md)
뒤의 누락된 조회 의존성을 고정한다. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI0회다.
기존 [현재 조회 계약](crop-cycle-current-query-v1.md)의 권리/원 trace·전후 대사와
[부하 계약](crop-cycle-burden-v1.md)의 원량·30초/2MiB·복원 조건을 유지한다.
이 문서는 개발 계약이며 아래 작업과 전체 등록 작기/관문은 아직 미수용이다.
[원166일 증명 실제 비용](../research/crop-cycle-full-result-evidence-cost-observation-20261007.md)은
6,111,094bytes/기존8MiB·발행175.675297초·별도 Python 검증1.589495초와 선택 page/정리를 확인했다.
원 판본의 순수 관측이며 새 계산 증명/농장·HTTP 수용을 대신하지 않는다.

## 현재 경계와 구현 순서

기존 result evidence/reader/current query는 exact 원 artifact/context/store와 구형 manifest를 받는다.
공개 DTO도 구형 engine/result/artifact ID·dependency map만 받으며 운영자 flag/runtime factory도 구형 선택이다.
새 signed row를 기존 ID나 private token으로 위장하면 원 코드·입력 proof provenance를 잃는다.
과거 서명/행·영수증과 원 소스를 보존하고 다음 작은 순서로 연결한다.

1. `crop-cycle-calculation-result-evidence`: 새 artifact의 전체 수지 검증 증명과 현재 bytes 대사.
2. `crop-cycle-calculation-result-read-context`: 그 증명으로 조회만 하는 별도 타입과 bounded 원 page.
3. `crop-cycle-calculation-current-query`: 현재 farm/DB/등록·권리와 새 server의 전체 선택/부모 서명 결속.
4. `crop-cycle-calculation-api-runtime`: 공개 판본·명시 operator 설정/factory·실제 HTTPS 응답/투영 후 철회.
5. `crop-cycle-calculation-client-view`: 새 result ID/provenance를 보존하는 client와 같은 원 UTC 표/장면.

`crop-cycle-calculation-prefix-cost`는 위 읽기 개발과 독립적으로 실제 등록 계산/저장 누적 비용을 측정한다.
읽기 개선은 계산 단계의 반복 prefix 검사 비용을 해결했다고 주장할 수 없다.
전체 replay-restore 수용에는 full-rhs, 등록 실행/비용과 저장·조회/동일 UTC3D의 실제 증거가 모두 필요하다.

## 다음 한 단계: 새 결과 검증 증명

core4파일은 `backend/app/crop_cycle_calculation_result_evidence.py`,
`backend/tests/test_crop_cycle_calculation_result_evidence.py`,
`research/crop-cycle-calculation-result-evidence-reference.py`, 이 계약이다.
새 queue/service/DB 표나 외부 자료 채택 없이 순수 소프트웨어부터 검증한다.

`CalculationResultEvidenceAuthority(exact InputEvidenceAuthority, *, integrity_key, issuer_id, key_id)`는
서버 제공 key/ID·profiles/notice와 현재 source/dependency를 고정한다.
key는 입력 증명 key와 다른32..4096bytes다. 농장 query 연결 시 DB/server/input/result 네 key도 별개여야 한다.
판본은 `crop-cycle-verified-result-evidence-v1`, HMAC domain은
`b'ossf-crop-cycle-verified-result-evidence-v1\0'`이며 사설 canonical 증명8MiB 한도를 유지한다.

- `issue(result_directory, artifact_sha256, input_directory, input_root_sha256, input_evidence_raw)`는
  공식 `open_calculation_context`와 새 artifact의 원 전체 수지/commit 검사를 실제로 수행한다.
  완료/수치 hold·확인 과거·121상태/누적/clock/cursor·원량/UTC/manifest를 그대로 보존한다.
  발행 전후 현재 bytes/inode·HEAD/root/입력 proof·source를 대사하고 RHS는 호출하지 않는다.
- `verify(..., evidence_raw)`는 별도 Python에서도 HMAC/판본/키·입력 증명과 현재 결과 snapshot을 검증한다.
  원 parser/계산 context 구성·terminal QC/RHS를 다시 호출하지 않는다.
  입력 authority가 확인한 원 context와 공식 계산 manifest의 변환을 결정적으로 대사하고,
  원 validated context SHA와 새 calculation context SHA/입력 proof SHA를 구분한다.
  token/cache 주입이나 구형 판본 재표시는 허용하지 않는다.
- 반환하는 `VerifiedCalculationResultEvidence`는 명시 새 타입이다. summary/index/context/identity는 사본이며
  `rights_or_gate_approval=False`다. 닫힌 payload·code/dependency/Python·단위/원 정규화 의미를 유지한다.
  증명은 키·경로·원 입력을 공개 API로 보내는 DTO가 아니다.

### 수용 기준

1. 새 공식 artifact의 작은 정상/수치 hold·모든 원 시점/사건/manifest를 실제 검증하고 조회 RHS0을 확인한다.
2. 유효 HMAC로 다시 만든 잘못된 context/validation·summary/index/inventory/code도 거부한다.
   잘못된 key/판본·구형 증명 혼합·크기·중복 key/비정규 JSON과 파일 보안 위반을 거부한다.
3. 발행 중/후 입력·HEAD/root/page/파일/inode·source 변조와 orphan·재명명/교체를 거부한다.
   원 수지 검사를 생략하거나 snapshot/원 출력을 자르지 않는다.
4. 새 별도 Python의 실제 검증과 원 sample/event/UTC·121상태/proof identity를 대사한다.
   parser/context/QC/RHS를 금지한 상태의 재조회·FD/cache/프로세스 정리를 기록한다.
5. driver는 자체 소유 합성 입력/새 계산 artifact를 사용한다. 순수 참조 결과는 farm DB 이력이 아니다.
   실제 source/CLI·호출/출력·크기/시간/RSS와 이전 bytes 보존을 기록한 뒤만 자식을 체크한다.

코드 이식/문맥 대사·검토1–2집중시간과 시험/별도 프로세스/기록1–2시간의
2–4집중시간/10월7–8일 KST 잠정이다. 전체 registered 작기·CI·외부 자료 완료일은 제외하며 실측으로 갱신한다.

## 후속 수용과 보류

reader/current query·공개 DTO/runtime/client 각각은 선행 수용 뒤3–4 core파일로 계약을 구체화한다.
현재 API의 인증/오류 의미와 기존 응답을 보존하며, 원 result ID/engine/artifact provenance를 새 판본으로 명시한다.
기존 경제·열·3D와 다른 테넌트/구형 이력의 회귀를 검증한다. raw proof/HMAC·경로·권리 원문은 노출하지 않는다.

전체 시작/중간/끝·byte-short/관리 전후·원 ID/UTC와 현재 철회·변조/원량을 실제 DB/HTTPS/WebGL에서 대사한다.
한도 증가·출력 축소·임의 애니메이션으로 수용하지 않는다. 기존 내부 get39.668745초 관측을 HTTP 통과로 바꾸지 않는다.
현재 소유166일 원 artifact의 증명 발행/별도 조회 비용 측정도 registered 실행·새 판본/HTTP 증거와 구분한다.

채택 실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건, G0–G4는 `not_assessed`다.
전체 작기 계산/재생 뒤 수확·생과 환산 → 물/양분·구매 에너지 → Decimal 손익/현금 연결을 진행한다.
생산 예측·미래 마진·작물 비교/추천은 해당 독립 관문 전까지 보류한다.
