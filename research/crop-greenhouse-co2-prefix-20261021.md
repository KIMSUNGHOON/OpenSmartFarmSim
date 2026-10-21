# CO₂ 확정 구간 원 조회 — 구현/검증 진행

[계약](../contracts/crop-greenhouse-co2-prefix-v1.md) · [사전 증거](artifacts/crop-greenhouse-co2-prefix-preflight-20261021.json).

`Co2ExecutionPrefixQuery`를 기존 Solar의 원 조회/현재 권리·서명 이력/owner witness 경계에서
CO₂ authority·HMAC/버전·원109상태/장부/UTC에 연결했다. 수치·저장 커널/기존 공개 경로는 변경하지 않았다.
선택 페이지를 직렬화 뒤 재검사하며, DB 미확정 HEAD는 선택하지 않는다.

현재 순수 제어7개와31개 전체 수집·원 계수의128초 밀집65시점 준비만 로컬 통과했다.
첫 missing-module RED를 보존했다. 512MiB/PID·합1GiB/600초·기존5root/원자료2148항목·
원 두 미리보기 source/assets를 유지했고 소유 PG/임시/passfile/process 잔존0이다.
128초 변형은 저장 페이지 계약을 시험하며 독립 물리 검증은 원32초 범위다.

## 미수용인 실제 검증

원 Solar23개를 모두 유지하고 late page1/제어7을 추가한31개다.
`co2-prefix-core`13 → `co2-prefix-fences`10 → `co2-prefix-concurrent`8을 원600초씩 분리한다.
현재 실제 DB/동시 actor/독립 fresh는 미수행이며 전체 원 조회 부모는 미완료다.
동시 actor의 의도된 SQL·미리 계산한 HEAD 공개와 제품 조회31계측0을 구분한다.
독립 fresh는 실제 producer 전진 뒤 종료한 별도 reader의 원 선택/UTC·철회 시험이다.
원 wrapper의 자동 worker 문구를 unpaused 동시 수치 계산의 증거로 사용하지 않는다.

다음은 전체31개 수용 뒤 닫힌 공개 투영 → 보호 실행 HTTP/runtime → 같은 UTC3D다.
공통 WSL/사용자 적용·전체 작기/자원/경제/최종 UI·실제 CLI 종단 간·독립 농장 자료/관문은 남는다.
실제 농장 Run0/G0–G4 not_assessed·새 CO₂ 미배포, 전체 완료일 미정·goal active다.
