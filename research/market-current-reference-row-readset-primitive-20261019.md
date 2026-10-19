# 닫힌 참조 행 조회 primitive — 2026-10-19 KST

[v3 계약](../contracts/market-current-reference-row-readset-v3.md) ·
[선행 후보 비교](crop-solar-current-read-candidate-evaluation-20261019.md) ·
[기계 증거](artifacts/market-current-reference-row-readset-primitive-20261019.json).

상태: **최종 module의 고유34 실제 SCRAM 검사·검토로 primitive만 로컬 수용**.
기존 pure verifier/작물 계산에는 아직 연결하지 않았다. v2 baseline과 로컬 HTTP58은 그대로다.
판단은 실제 native `gpt-6.1-sol/xhigh` 문맥에서 했으며 시각/원 해시를 기계 증거에 기록했다.
재귀 CLI/하위 에이전트나 변경 없는 native CI 반복은 실행하지 않았다.

## 구현과 경계

새 `market_reference_row_readset.py`의 `verify_rows`는 기존 `_Bundle`과 실제 동일
SCRAM/읽기 전용 Read Committed 연결 안에서만 동작한다. server 내부 callback에만
복사된 원 행을 제공하며, callback은 `None`만 반환할 수 있다. 전후 실제 행 비교를
통과하면 `None`을 반환한다. **호출 바깥의 기존 source scope가 최종 실제 role 감사를
수행하기 전에는 전체 검증 수용이 아니다.** 이 module을 새 승인/관문/공개 응답으로 쓰지 않는다.

동적 SQL interception이나 tenant 전체 조회 없이 파라미터화한 정확한 키로만 읽는다.
source의 원 payload와 원 source-job stage/input/hash, candidate 입력과 명시적 부재를
구분한다. 알 수 없는 키는 부재와 구분해 전체 수명을 무효화한다. source/job 원 해시를
대사하며, 도메인 getter의 기존 schema/권리 검증은 이후 integration에서도 모두 실행해야 한다.

Thread/Task/Context/slot·owner/provider/connection/키/code/table 메서드가 달라지면
실패한다. 중첩·복제·닫힘·예외 뒤에는 행/연결/토큰을 정리하고 다음 호출은 새 DB 조회를 한다.
primitive는 연결 참조를 제거하며, 실제 연결은 소유자인 바깥 source scope가 닫는다.
행 lookup은 현재 principal·binding·수명을 검사하되 SQL을 추가하지 않는다.
실제 session/읽기 전용/isolation 검사는 capture와 재확인 경계에서 기존 bundle guard로 수행한다.

키 합계128개, 보수적으로 계산한 보관 크기1MiB가 상한이다. SQL의 각 batch에서도
한도 초과 raw 필드는 NULL로 억제하며, 두 종류의 합계를 callback 전에 다시 검사한다.
따라서 개별 batch 한도와 전체 보관 한도를 구분한다. 향후 integration은 초과/부적합한
경우의 v2 경로를 명시해야 하며 현재 일반 getter 동작을 좁히지 않는다.

## 압축 원문의 실제 RED/GREEN

4976:1은 source payload9개와 연결된 job input을 각각64KiB로 만든 실제 DB 사례에서
크기 제한 위반을 거부하지 못했다. `DID NOT RAISE ValueError`였고 source/5root/정리를 보존했다.
저장 크기에만 의존한 계산을 수정해 원문의 `octet_length`도 합산했다.
이후 최종 boundary10에서 SQL이 raw/source-job 값을 NULL로 억제하고 callback을 호출하지
않는 것을 확인했다. [PostgreSQL16 문서](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADMIN-DBOBJECT)는
`pg_column_size`가 저장 압축을 반영한다고 설명한다. 원문 길이를 별도로 계산하는 것은 이 구현의 보수적 한도 판단이다.
공식 문서 참조이며 농업/경제 자료 채택이 아니다.

## 최종 검증

| 경로 | 고유 검사 | 실제 도구 종료 |
| --- | ---: | --- |
|존재/부재·키/개수·바깥 호출·원 source-job·압축 raw 한도|10|61923:0|
|도중 metadata/job·등장/삭제/교체·role/principal 변경|8|32357:0|
|복제/Task/thread·중첩·닫힘/예외·code/slot/key/provider/연결/table·반환 제한/새 호출|16|42928:0|

각 stage에서 최종 app source pin과 종료0, 실제 pytest 수, 원본2,148항목·5root/frozen 두 화면,
512MiB/PID/합1GiB·FD4→4·소유 PG/임시/passfile0을 대사했다.
실제 guard 합계411.670초(약6.9분), 합산 최대 RSS1,012,367,360bytes였다.
이전 source의1/5/15검사와 RED1은34에 합산하지 않았다.
검사1은 두 종류의 capture/recheck SQL4개와 정확한 bound 키를 확인했으며 읽기 중 SQL mutation과
개별 lookup의 추가 SQL은0이었다. 복사한 행을 바꿔도 내부 원문은 바뀌지 않았다.
거부 경로는 바깥 verifier의 결과가 반환되지 않고 정리되는 것을 확인했다.

검토에서 정확성/단순성/구조/보안의 미해결 지적은 없다. 성능 수용은 아직 하지 않았다.
새 module/test 외 기존 source/candidate/bundle/registration·custody/query/worker·role 코드와
수식·원 actor/입력/chunk/poll/retry360/상한은 변경하지 않았다.

## 다음 한 단계

primitive를 기존 pure verifier에 연결한다. 초기 full 검증과 일반/대체 경로를 보존하고,
recorded trace에서 source/candidate의 정확한 키를 도출한다. 모든 논리 getter/중복 순서,
현재 principal/right/validator와 기존 전후 role 감사를 유지한다. 원 source/job/candidate/
callback/grant 변경과 수명/오류, current12/registration24/reconstruction1·논리 source1,824·
원 수치/UTC/proof, worker/query/HTTP 회귀·paired 비용을 확인한 뒤 통합 수용 여부를 정한다.

원64 trace-OFF 정상/독립 hold/HTTP 취소/계산 중 WebGL·WSL 용량/사용자 적용은 여전히 후속이다.
이번 source의 전체 backend/browser·fresh exec/SIGKILL은 실행하지 않았다. 실제 농장 Run0,
권리/관문 승인False·G0–G4 미평가·새 Solar 미배포와 전체 완료일 미정을 유지한다. goal은 active다.

61369:0에서 primitive34 로컬 수용/미통합과 다음 연결을 두 UI에 같은 no-store bytes로 게시했다.
현재 app pin/새2syntax·기존3syntax/두 파일 pin·로컬 링크2,341개·원 actor/header·frozen HTML/환기2,173파일·
5root/상한/FD/소유 정리를 확인했다. 실제 app caller0도 대사했다. 합산 RSS889,311,232bytes였으며
UI 코드/DOM/WebGL은 변경·재검사하지 않았다.
