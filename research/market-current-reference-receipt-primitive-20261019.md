# 원문 의존성 지문 primitive — 2026-10-19 KST

상태: **독립 조회 기능만 실제 SCRAM 고유48검사·검토로 로컬 수용**.
[구현](../backend/app/market_reference_receipts.py) ·
[검사](../backend/tests/test_market_reference_receipts.py) ·
[기계 증거](artifacts/market-current-reference-receipt-primitive-20261019.json) ·
[v4 계약](../contracts/market-current-reference-receipt-agreement-v4.md).

기존 v2 계산 경로·primitive34·capture Pending HTTP58의6파일은 원 bytes를 유지했다.
새 조회 함수를 호출하는 제품 경로는 없다. 순수 getter 생략·동등성·통합·성능 개선은 미수용이다.
이전 [v3 통합 미채택/연구 시험](market-current-reference-row-integration-evaluation-20261019.md)의
약12.6%/9.7% 관측을 이 구현의 성능으로 옮겨 주장하지 않는다.
판단·구현은 현재 native Codex CLI `gpt-6.1-sol/xhigh`에서 수행했고 실제 turn context 시각/해시와
코드·시험 산출물 해시를 남겼다. 재귀 CLI·하위 에이전트는 사용하지 않았다.

## 구현과 경계

`verify_receipts(owner, tenant, source_keys, candidate_keys, pin_keys, consume) -> None`은
기존 owned bundle의 같은 실제 SCRAM/Read Committed/read-only 연결을 빌린다.
정확한 source3요소·candidate input2요소·candidate pin2요소 키를 받는다.
입력은 중복 없는 tuple이며 세 범주 합128키·비압축 의존성1MiB 이하다.
원 source-job stage/input/hash도 source 범위에 포함한다.

하나의 매개변수 SQL이 정확한 키/tenant의 세 범주를 함께 선택한다.
물질화 CTE에는 키와 크기만 두고, 모든 범주의 크기를 합산한 뒤 `CASE` 안에서만
원 bytes SHA와 고정 metadata 배열의 SHA를 계산한다. 압축 저장 크기에 원 bytes 길이를 더한
보수적 크기이며, 초과하면 SQL의 지문은 NULL이고 callback은 시작하지 않는다.
클라이언트에는 raw payload가 전달되지 않는다. 저장된 hash 열만 신뢰하지 않는다.
metadata에 저장 hash도 포함하되 실제 원문을 별도로 해시한다.
세 pin 원문은 각각 고정32byte SHA 블록으로 결합한다.

고정 field/type/typmod/nullability·ordinary table/RLS/generated/identity descriptor와
같은 물리 relation OID를 전후 대사한다. 임의 스키마 지원이나 전체 CHECK 정의의 검증은 아니다.
PG16/UTF8·실제 server version number·프로토콜을 고정하고, 시각은 epoch 숫자로 직렬화한다.
`TimeZone`/`bytea_output` 표시 설정 변경에도 동일 원문 지문이 유지되는 것을 실제 확인했다.
미지원 field shape는 callback 전에 거부한다. 제품 fallback 선택은 후속 연결의 책임이다.

내부 callback은 신뢰된 코드이며 `None`만 반환해야 한다. 요청한 키의 조회는
고정32byte 지문 또는 명시적인 부재 `None`만 제공하고 추가 SQL은 없다.
중간 결과를 외부에 게시할 수 없다. 원문 유효성·DTO 의미·자료 권리·관문을 지문이 승인하지 않는다.
callback 후 다시 새 DB 지문을 구해 동일성을 확인하고 참조·연결·token을 정리한다.
바깥 source scope가 실제 연결과 최종 역할/권한 감사를 소유하며 그 성공도 필요하다.

## 실제 검증

| 실행 | 고유 검사 | 검증 범위 | guard 초 |
| --- | ---: | --- | ---: |
|67888:0|11|정확한 키·존재/부재·pin-only·다른 tenant/무관 행·시간대·bytea·일반/범주 합산 크기·진입/닫힘|131.388|
|40020:0|1|source scope 철회 후 추가 지문 SQL 이전 거부|15.422|
|59901:0|18|source/job/candidate/pin 원 bytes·같은 저장 hash·시각·삭제/교체·부재→존재·grant/principal|213.196|
|24869:0|18|중첩/복제/Task/thread/닫힘·code/version/keys/slot/provider/table/tenant/connection·예외/재호출·미지원 field|218.600|

합48개이며 실제 guard 합578.605초(약9.6분)다. 준비·실패 진단·문서/게시 시간은 포함하지 않는다.
각 실행의 app source SHA는 `e93170b4…`로 같다. 시험 fixture 정리/추가에 따른 시험 파일 판본은
각 stage에 별도 기록했다. 이전 시험·실패·관찰을48에 더하지 않았다.

압축 가능한64KiB source/job9쌍과, source·pin 각각은 한도 이내이지만 합은 초과하는 입력을
실제 DB에 넣어 `ok=False/receipt=NULL`·callback0을 확인했다.
원문만 바뀌고 저장 hash는 같은 검사는 시험용 CHECK를 조회 시작 전에 해제한 합성 fixture다.
제품 DDL이나 원본 자료 변경이 아니다. 전후 지문은 해당 변화를 거부했다.

5root·원본2,148항목·기존 두 UI source/assets·512MiB/PID·합1GiB를 유지했다.
수용 배치 합 RSS 최대1,012,928,512bytes·단일142,536,704bytes, FD는 각각4→4다.
소유 프로세스/PG/임시/passfile은 모두0으로 정리됐다. 전체 backend/browser·fresh exec/SIGKILL은 재실행하지 않았다.

## 초기 실패와 수정

34673:1은 실제 fixture 생성 뒤 모듈 부재를 확인한 최초 RED다.
67029:0의 초기1개는 수용 수에서 제외했다. 54608:1·54805:1에서는 시험이 source fallback 키를
물리 pin으로 잘못 취급했다. 실제 존재 pin과 명시 부재를 구분하고 범주별 한도 입력을 고쳐67888:0을 통과했다.
40020:0의 stage 이름에는 RED가 남아 있지만 실제로는 통과한 기존 scope 안전 검사다.
추가 권한 수정이 필요했다거나 그 시험이 실패했다고 기록하지 않는다.

30773:2는 시험 callback의 `DROP CONSTRAINT`가 같은 조회 transaction의 관계 잠금에 막힌 경우다.
실제 `pg_stat_activity/pg_blocking_pids`에서 확인하고, identity를 재확인한 해당 pytest에만
SIGINT를 보내 정리했다. 보호 서비스에는 신호를 보내지 않았다.
ACCESS EXCLUSIVE 시험 DDL을 조회 전 준비로 옮기고, 알 수 없는 field 검사는 진입 전 거부로 분리했다.
후속59901:0·24869:0을 통과했다. 모든 초기 실행도 원본/서비스/자원·정리를 보존했다.

## 근거와 검토

PostgreSQL16의 [bytea SHA 함수](https://www.postgresql.org/docs/16/functions-binarystring.html),
[CASE 평가와 상수 계획 시점 예외](https://www.postgresql.org/docs/16/functions-conditional.html),
[CTE 물질화](https://www.postgresql.org/docs/16/queries-with.html)를 확인했다.
크기 조건과 원문 해시는 행에 의존하며, 초과 시 지문 NULL을 실제 검증했다.
**설계 판단:** 지문 일치가 기본 getter의 재실행과 동등한지는 위 SQL 문서가 증명하지 않는다.
이번 검토는 정확한 SQL 범위·전체 크기 조건·프레임 구분·schema/code/수명·원문 비전송·
기존 전후 감사·정리·근거 범위에 한정하며 전체 제품 보안/성능 수용은 아니다.

## 다음 한 단계와 남은 의존성

다음은 default 순수 getter의 전체 의존성·동등성 증거다. 원 full trace와 DTO/지문을 대사하고,
code/schema/Decimal·동적 principal/scope·source fallback/파생 manifest를 목록화한다.
시간·외부 상태·callback 또는 미입증 의존성이 있는 경로는 기존 v2를 유지해야 한다.
그 증거 후에만 같은 registration 수명의 full anchor/현재 지문을 연결하고,
worker/HTTP 회귀·원 수치/UTC·paired 실제 비용을 통과한 경우 채택한다.

그 다음 원 계측 OFF64 정상→hold/취소→계산 중 WebGL→WSL 용량/사용자 적용이 남았다.
실제 농장 Run0·G0–G4 미평가·자료 권리/독립 현장/미래/비교 검증은 별도 외부 의존성이다.
새 Solar 미배포이며 전체 완료 날짜와 다음 단계 소요 시간은 아직 확정하지 않는다. 전체 goal은 active다.

## UI 게시와 최종 범위 확인

62073:0에서 새 코드/시험2파일의 해시·문법과 primitive48·기존6파일/primitive34/HTTP58 pin,
원 API/worker/header를 대사했다. 로컬 링크2,364개를 확인했다.
두 UI의 개발 기록은 HTTP200·동일 원 JSON bytes/no-store였고 frozen HTML과 환기2,173파일을 보존했다.
게시 guard2.396초·5root·합 RSS893,399,040bytes·단일141,316,096bytes·FD4→4와
소유 프로세스/PG/임시/passfile0을 확인했다. 화면 code/DOM/WebGL은 변경하지 않았다.
검토한 제품 app의 `verify_rows`/`verify_receipts` 호출은0이다. 새 모듈은 v3의 키 검사 helper만 재사용한다.
추가 native CI를 실행하지 않았고, 원64 정상이나 새로운 사용자 시뮬레이션을 수용한 것은 아니다.
