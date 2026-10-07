# 검증 계산 결과의 조회 전용 문맥 — 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI0회다.
선행 [새 결과 증명 수용](../research/crop-cycle-calculation-result-evidence-implementation-20261007.md) 뒤
`crop-cycle-calculation-result-read-context`를 구현한다. 이 계약과 아래 수용 기준은 아직 미수용이다.
농장/현재 권리·DB/서버 부모 서명과 공개 DTO/runtime/3D는 [후속 순서](crop-cycle-calculation-query-v1.md)에 남는다.

## 구현 경계

core4파일은 `backend/app/crop_cycle_calculation_result_read_context.py`,
`backend/tests/test_crop_cycle_calculation_result_read_context.py`,
`research/crop-cycle-calculation-result-read-context-reference.py`, 이 계약이다.
원 reader와 증명·계산/artifact 소스는 보존한다. 새 module은 새 evidence authority의 exact 타입을 사용한다.
새 DB 표/서비스/queue·solver·자료 채택은 추가하지 않는다.

- 판본 `crop-cycle-verified-result-read-context-v1`와 `CalculationResultReadContext`,
  `open_calculation_result_read_context(..., *, authority)`를 명시한다.
- 기존 result/input directory·두 root SHA·두 증명 bytes를 받고 현재 proof/snapshot을 검증한다.
  official calculation context·원 parser/QC/RHS를 생성하거나 실행하지 않는다.
- summary/manifest/context_record/identity는 사본이다. 원 validated context SHA·새 calculation context SHA와
  input/result evidence SHA를 구분하고 새 read code/version/dependency를 identity에 추가한다.
  `rights_or_gate_approval=False`이며 농장 권리/관문을 승인하지 않는다.
- `page(kind, start=0, limit=None, *, max_bytes=2MiB)`는 samples64/event8 한도를 유지한다.
  반환은 `{kind,start,next,total,records}`다. 저장된 원 행·단위/UTC·순서·개수를 보존한다.
  byte 한도에는 실제 canonical 응답 전체가 들어가야 한다. 한 행도 들어가지 않으면 hold하며,
  비어 있는 끝 page와 수치 hold의 확인 과거를 임의 완료/전체 출력으로 바꾸지 않는다.
- 현재 bytes·HMAC·source/inode를 반환 전에 재대사하고, 중간 변경이면 사본도 반환하지 않는다.
  page는 보안 확인된 regular0400 파일만 읽으며 현재 hash/canonical/index/시각/개수를 검사한다.
  cache는 kind별 한 page이고, 명시 close/실패/with 종료에서 FD/cache를 정리한다.

## 다음 한 단계의 수용 기준

1. 실제 새 정상/수치 hold artifact의 summary·모든 원 sample/event·121상태/clock/cursor·manifest를 대사한다.
   원 입력 검증 provenance와 새 계산/조회 identity를 구분하고 구형 authority/증명 혼합을 거부한다.
2. 실제 별도 Python에서 parser/calculation factory/원 terminal QC/RHS를 금지한 채 재조회한다.
   원 행·UTC SHA와 첫/중간/끝·관리 전후·byte-short/빈 끝 page를 대사하고 호출0·FD/cache/프로세스 정리를 기록한다.
3. 잘못된 kind/index/limit/max_bytes·bool/범위/크기와 변조된 HMAC/index/code를 거부한다.
   입력/HEAD/root/page/source/inode 교체·권한/링크·읽는 중/반환 직전 변경은 hold와 close다.
4. 같은 입력의 반복 조회에 RHS 재실행이 없고 실제 응답2MiB·원 sample64/event8·기존 파일 한도를 유지한다.
   이전 소스/행과 증거를 보존하고 시험/참조 명령·실제 출력·비용/자원·남은 보류를 기록한 뒤만 체크한다.

이식/정리·계약 대사1시간, 실제 변조/별도 Python·원량/비용·검토/기록1–2시간의
**2–3집중시간 잠정**이다. 전체166일 새 proof/등록 DB/API/WebGL 성능과 독립 농장 자료 확보 날짜는 제외한다.
원 증명의 전체 metadata 대사 비용도 후속 전체 HTTP30초 수용에서 측정한다.
실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건, G0–G4는 `not_assessed`다.
