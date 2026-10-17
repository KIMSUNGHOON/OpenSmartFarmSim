# 현재 권한 행렬 조회 비용 감소 — 2026-10-17

[계약](../contracts/runtime-role-matrix-query-v1.md) ·
[기계 증거](artifacts/runtime-role-matrix-implementation-20261017.json) ·
[직전 원 실행의 실제18/64](crop-solar-unpaused-postmortem-20261017.md).

## 실제 비용과 변경

실제 Solar fixture의 farm 등록 조회 한 번을 계측했다. 첫 조회는0.514초였으며
권한 감사21회가0.279초를 사용했다. 세부 계측에서 table15,288행·column8,736행,
합24,024행을 Python으로 반환했다. 함수 시간은 중첩·계측 비용을 포함한다.

`runtime_roles.audit_runtime_roles`의 두 행렬만 DB에서 불일치를 판정하도록 바꿨다.
기존 `_allowed`에서 이번 감사의 기대 권한을 만들며 현재 권한을 캐시하지 않는다.
전체 role/table/privilege 조합·두 statement 순서·column에서 현재 table/column 권한과
grant option을 검사한다. NULL은 거부한다. 성공은0행, 불일치는최대1행을 반환한다.
owner/역할·멤버십/DDL/sequence/routine/default/추가 ACL 검사와 정책·설치 코드는 같다.
수식·경제 산술·API/worker·원 입력·64/chunk1·재시도/조회 주기·상한은 바꾸지 않았다.

수정 뒤 같은 등록 조회는21회 감사·두 행렬0행이었다. 그러나 별도 실행의 전체 시간은
0.505→0.928초로, 변경하지 않은 SQL 시간까지 함께 증가했다. 이를 속도 개선 근거로 쓰지 않는다.
같은 실제 DB·연결에서 기존/수정 감사를 ABBA 순서로3회, 표본마다21회 감사했다.
각 방식6표본의 중앙값은 **0.405311→0.355695초(약12.24% 감소)**였다.
254회 감사의 반환 정책 metadata가 같았다(각 방식 timed126회+warm1회).
이는 권한 감사 컴포넌트의 관측이며 전체 계산 처리량·완료일 추정이 아니다.

## 통과한 검증

- 31018:1: 수정 전 성공 감사가728/416행을 반환해 새 전송 상한 검사2개가 실패했다.
- 51842:0: 선택/미선택 저장·누락/추가 table 권한·grant option·worker column·supervisor,
  추가 객체·두 statement 사이 철회·scope 뒤 객체 삭제의 **12검사**를 통과했다.
- 27737:0: 기존 NOLOGIN 역할·실제 SCRAM 로그인, PUBLIC/열/기본 권한·membership/속성,
  DDL·역할 상승 거부·설치 rollback·재설치·외부 definer 등 **39회귀 검사**를 통과했다.
- 21391:0: 정상/수치 hold 저장 결과의 원 metadata·UTC/해시·성공 게시1/hold0,
  조회 모델/CLI/SQL 변경0·직렬화 후 원천 권리 철회 거부의 **3검사**를 통과했다.
  해당 terminal 검사 자체는 별도 프로세스 reader 수용 증거가 아니다.
- 36683:0/81413:0/69214:0은 실제 등록 조회의 비용 관찰이다.
  46703:0은 위 paired 감사 비교이며54개의 고유 수용 검사 수에 더하지 않는다.

로컬 **고유54검사**를 수용한다. 최대 합 RSS1,061,945,344bytes·단일143,671,296bytes였다.
모든 실행에서 원5root·원2,148항목·frozen source/assets·두 UI·512MiB/PID/합1GiB,
감독FD4→4·소유 비좀비/PG/임시/passfile0을 보존했다. 실제 역할/namespace 정리를 확인했다.
현재 backend/browser 전체 회귀는 실행하지 않았다.

## 검토와 다음

정확성: 기존 boolean 행렬과 같은 기대 권한을 사용하고 NULL/중간 철회를 실제 DB에서 거부한다.
보안: SQL 매개변수 바인딩·기존 거부 사유·매번 현재 감사와 나머지 검사를 유지한다.
구조: 공통 권한 감사의 두 query만 바꾸며 새 의존성·캐시·연결 수명 변경은 없다.
성능: 반환량0행과 paired 컴포넌트 관측만 수용한다. 정책/설치/discovery 함수와
행렬 이외 감사의 앞18/뒤4 statement AST가 같다. 검토는 현재 native CLI에서 수행했다.

다음은 계측하지 않은 원 API/worker의 독립64단계 정상 한 사례다. 같은 source로 근거 없는
반복 실행은 하지 않는다. 성공 뒤 독립 hold→실제 취소→계산 중 WebGL 순서를 유지한다.
S3/S4·WSL 동시 용량·새 Solar 사용자 적용·실제 품종/독립 농장·경제 전망/추천·G0–G4와
전체 완료일은 미완료/미정이다. 실제 농장 Run0·권리/관문 승인False·goal active를 유지한다.

근거 문서는 PostgreSQL16의 [권한 inquiry](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)와
[NULL 비교](https://www.postgresql.org/docs/16/functions-comparison.html)다. 공개 문서 참조이며
농업/경제 입력으로 채택·복제한 자료는 없다. 판단은 기록된 `gpt-6.1-sol/xhigh` 현재 세션에서 수행했고 CLI를 재귀 실행하지 않았다.
