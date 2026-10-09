# 새 계산 결과의 조회 전용 타입 — 로컬 수용

2026-10-07 KST. `crop-cycle-calculation-result-read-context`를 소유 합성 자료의 작은 소프트웨어 범위에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-result-read-context-reference-20261007.json)에 실제 시험/참조 호출·출력 SHA,
현재 source와 native CLI `gpt-6.1-sol / xhigh` turn context를 보존했다. 재귀 CLI0회다.
현재 농장/DB query·공개 API/runtime·전체166일/3D·실제 품종/관문은 이번 수용에 없다.

## 구현과 검토

[새 module](../backend/app/crop_cycle_calculation_result_read_context.py)은185줄이다.
원18함수 중10함수 AST가 그대로이고8함수는 새 이름/authority·예외·source pin·진입 검사를 검토했다.
계산 context나 private token을 생성하지 않으며 원 reader/evidence/계산/artifact와 원55 source를 보존했다.
새 증명의 product/test/driver3개를 더한58 source SHA도 전후 같았다. 새 package·service·DB 표는 없다.

- 새 `CalculationResultReadContext`는 exact 새 evidence authority만 받으며 원/새 타입·증명 혼합을 거부한다.
- 원 summary/manifest/context와 validated/calculation/input evidence/result evidence SHA를 보존하고 새 read 판본/code/dependency를 더한다.
- 보안 확인한0400 regular 파일의 hash/canonical/count/첫·끝 UTC와 읽기 전후 metadata를 확인한다.
  samples64/event8·응답2MiB를 유지하며 작은 byte 한도에서도 원 행을 줄이거나 바꾸지 않고 다음 cursor를 반환한다.
- 반환 전 현재 input/result 전체 bytes·proof/HMAC·source/authority/inode를 다시 확인한다.
  cache는 kind별 한 page, caller에는 사본만 반환하며 실패/close/with 종료에서 FD/cache를 정리한다.
- context 재진입도 현재 HEAD를 검사하고, 런타임 version/code/dependency/page 한도 변경은 거부한다.
  `rights_or_gate_approval=False`다. 권리 정책이나 농장 서버 이력의 검증은 후속 query에서 수행한다.

## 실제 시험과 보완

| 실행 | 실제 결과 |
| --- | --- |
| 이름 이식 후 새 authority 연결 전 정상3사례 | 3실패/5.19초·종료1 |
| context 진입/런타임 선언 반례 | HEAD·VERSION·MAX_PAGE_BYTES3실패, CODE/dependency2통과/9.77초·종료1 |
| 최종 새 reader49개 + 새 evidence79개 + 원 reader36개 | **164통과/251.75초·종료0** |

두 실제 RED의 기대값은 보존하고 새 exact authority, 진입 시 현재 recheck와 불변 선언 대사를 구현했다.
최종은 단일 집중164개이며 전체 backend 실행은 아니다. 이전 반복 실행을 합산하지 않는다.
정상3사례/수치 hold의 원 page·단위/UTC·count/manifest와 사본 격리·정확한 byte 경계/첫 행 초과 거부,
cache 후 input/HEAD/page·쓰기/hardlink/symlink·같은 bytes inode 교체·mode·proof/source/authority 변경,
실제 page/사본 준비 뒤 변경의 반환 거부·FD 정리, 구형 authority/증명 혼합과 계산 타입 위장 거부를 확인했다.
별도 Python 시험도 parser/context/QC/RHS를 금지하고 실제 원 첫 page와 FD 정리를 대사했다.

## 보존된 자체 합성 artifact의 별도 Python 재생

[참조 실행기](crop-cycle-calculation-result-read-context-reference.py)는 선행 단계의 소유5시간 새 계산 artifact와
원 key/proof bytes를 **그대로 조회**했다. 새 입력/증명/농장 이력을 재발행하지 않았다. 이 단계의 새 RHS 실행은0건이다.
원 기준은 선행 [실제 전체 QC/별도 Python 증거](crop-cycle-calculation-result-evidence-implementation-20261007.md)의
고정 원 summary/context/모든 행·UTC SHA다. 새 reader의 결과를 자기 자신과만 비교하지 않았다.

| 실제 fresh Python exec 범위 | 정상 | 확인 과거 hold |
| --- | ---: | ---: |
| 원 시점 / 사건 | 61 / 3 | 60 / 2 |
| 조회 타입 열기 | 0.035429초 | 0.035709초 |
| page 호출 수 / 최대 응답 | 27 / 535,169bytes | 25 / 526,368bytes |
| 가장 긴 page 호출 | 0.385778초 | 0.378922초 |
| 열기·전체 행/선택·사본/byte 경계·정리 | 1.165369초 | 1.161337초 |
| 프로세스 peak RSS | 86,712,320bytes | 86,884,352bytes |

첫/중간/끝과 실제 관리 사건 전후·기본 sample64/event8·빈 끝 page·정확히6,653bytes인 첫 행 byte-short와
그보다1byte 작은 예산의 hold/close, 다음 원 cursor·caller 사본을 대사했다.
전체121상태/seed/clock/cursor·원 summary/context와 수치 hold 이유/확인 과거도 원 SHA와 같다.
두 child 모두 금지한 parser/context/QC/advance/RHS8곳0회·nice19·FD4→4·cache≤2/close 후0·종료0/PID 부재다.
주 참조 호출은 종료0/4.678743초, 내부 기록3.893751초·FD4→4/peak RSS80,412,672bytes다.
서로 다른 프로세스 peak를 합친 메모리로 표시하지 않는다. 집중 pytest와 동시 실행했으며 OS cache는 통제하지 않았다.
이 작은 로컬 관측은 전체166일·HTTP30초나 저사양 장치 성능의 증거가 아니다.

원 key/proof/파일과 실제 명령·request/response/log는0700 사설 경로/0400 기록에 보존했다.
실행 당시 계약 SHA를 영수증에 남기고 수용 문서는 실행 후 갱신했다. 제품/test/driver SHA는 그대로다.
실제 PG/API/browser를 시작하지 않았으며 이번 단계의 PG 정리를 주장하지 않는다.

## 다음 단계와 남은 의존성

reader 자식만 체크한다. 다음 [현재 농장 query3 core파일 계약](../contracts/crop-cycle-calculation-current-query-v1.md)은
새 signed DB/현재 등록·Scope/권리·원 input proof/validation9+8·전체 부모 서버 서명과 이 reader를 결속한다.
실제 SCRAM·철회/변조·다른 계정/판본·재구성/별도 프로세스와 FD/DB/역할/비밀/PG 정리를 검증한다.
이식/검토1–2시간과 실제 시험/기록2–4시간의3–6집중시간 잠정이며 첫 실제 DB 비용으로 갱신한다.
앞 reader의2–3시간 잠정은 이번 수용으로 대체한다.

새 증명의 전체166일/metadata 읽기 비용과 등록 계산 누적 prefix 비용, query/API 공개 판본·operator runtime·
HTTPS30초/2MiB·전체 같은 UTC3D는 남아 있다. 이후 수확/생과 → 자원 사용 → Decimal 경제를 연결한다.
실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건이고 G0–G4는 `not_assessed`다.
독립 자료·전체 등록 경로를 확보하기 전 최종 제품 완료 날짜는 확정하지 않는다.
