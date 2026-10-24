# 불변 잎 생애 결과와 생장 계산 없는 조회 — 2026-10-24

상태: **불변 수치 결과/typed reader를 소프트웨어 범위로 수용**.
[계약](../contracts/crop-leaf-lifecycle-artifact-v1.md), [기계 증거](artifacts/crop-leaf-lifecycle-artifact-20261024.json),
[독립 나이·면적 47행](artifacts/crop-leaf-lifecycle-artifact-rows-20261024.csv)을 제공한다.
구현 commit은 `794364b0f2303ff4bee193f2884f0e14db441e1c`이다.
[현재 화면](leaf-appearance-execution-web-20261024.md)은 이전 정책 잎 생장이며 새 제거 결과는 미적용이다.

## 구현과 검증

[원 입력 준비](crop-leaf-lifecycle-preparation-20261024.md)의 appearance/관리 bytes·준비 결과·초기 state,
원 stem graph와 40개 code SHA를 별도 결과 그래프에 저장한다. 원 stem sample 순서/UTC·기관 ID를 유지하며
producer에서만 lifecycle을 전진한다. 각 결과의 원 입력 state/input/output state·stem result SHA/byte 수를
결속하고 원 준비·source/target bytes·현재 file policy·코드를 재검사한 뒤 완료 manifest를 마지막에 저장한다.
실패는 새 완료 root를 만들지 않으며 이전 완료 결과는 보존한다. 동일 producer 재실행의 root/bytes는 같지만 계산은 다시 한다.
제품 접수의 중복 계산 방지는 이후 실행 작업의 별도 수용 기준이다.

reader는 생장/준비/producer 모듈을 import하지 않는다. 기존 typed parser/reader와 schema·단위·hash·고정 선언을
검증하고 원 저장 면적을 반환한다. 지문 계산·시간/forcing 범위 검사·개수/면적 합계 검증은 수행한다.
manifest 조회는 source graph/descriptor를, 선택 frame 조회는 초기/출현/제거 state·receipt/시각·합계를 검사한다.
선택/직전 결과를 검증하고 반환 전에 전체 graph의 bytes/file policy를 재확인한다.
제거 잎의 나이/면적은 제거 시각의 마지막 값이며 현재 active 면적에 포함하지 않는다. pending은 현재 state/형상이 없다.
신뢰된 private root와 ContentAccess를 받는 이 reader는 농장 SourceRecord/계정 권한·서명 승인이나 G0 판정기가 아니다.

같은 최종 source에서 **새68/관련523·고유591검사**가 통과했다. 이전 준비631이나 초기10/shape probe를 더하지 않는다.
무제거 원12시점/47상태·반복 동일 root, 초기/새 잎 즉시 제거·빈 active와 pending/last 구분,
원 input/state chain·잘못된 index·재지문 manifest15/준비9/result14 변형을 확인했다.
관리/appearance 재배포False는 내부 조회에서 보존된다. 저장/완료 실패·code drift·원 source/권한/디렉터리,
선택/비선택 결과의 늦은 변경은 보류됐다. 독립 프로세스의 성장 import/DB/CLI/network/파일쓰기0과 FD 보존도 통과했다.

최초 red는 새 모듈 부재 exit2였다. shape-red라는 phase는 실제로1검사가 통과했다.
공유 parser가 비객체 JSON을 이미 거부했으므로 발견·수정한 제품 버그로 보고하지 않는다.
첫 fences는 존재하지 않는 시험 파일 경로 때문에 exit4/실행0이었다. 실제 producer 시험 파일로 고쳐 최종591을 통과했다.

## 실제 두 결과와 독립 조회

원 appearance52blob·stem29blob과 실제 ContentAccess를 사용했다. 원 자동 출현2개는 준비에서 다시 도출했으며
제거 시나리오는 이전에 보관한 관리 원문을 그대로 사용했다. 원 준비 SHA도
`7ff0702a68899f0ef108fef3a6471157c5485524dd29127bf4d4c56c94e3e9ec`로 이전 반환과 같다.

| 결과 | 완료 root SHA | 불변 파일 | 시점/추적 상태 | 처음 → 마지막 active/removed/pending |
| --- | --- | --- | --- | --- |
| 무제거 | `c1ae9fc67c6eb045b114cc0a0f38d8164b31384989ea5c9e9722d85302aad8fd` | 31 | 12/47 | 3/0/2 → 5/0/0 |
| 명시 제거 | `33b77aa4ab641918ec249701bab59d7e645b5a8083bc456a9f51b2788ffe9ff9` | 31 | 12/47 | 2/1/2 → 3/2/0 |

무제거47개 잎 state의 SHA는 원 저장 population state와 같다. 제거 결과의47개 나이·면적과36개 합계를
독립 Fraction/100자리 Decimal로 대사했으며 최대 면적 상대오차는 약 `1.834e-16`이었다.
두 producer가 원12시점씩 총24회 lifecycle/73회 leaf를 전진했다. 출현 전 leaf 전진0,
제거 뒤 요청21건의 leaf 전진0을 확인했다. 기존 population/appearance producer·DB/CLI 호출은0이었다.

별도 Python 프로세스에서 허용한 crop reader/parser9개만 import해 두 결과의 각12 frame을 조회했다.
나머지 성장/준비 import·DB/CLI/network/쓰기0, FD4→4, 모든 DTO/원 UTC·ID가 저장 결과와 같았다.
조회 후 출력62파일의 bytes/metadata와 원52appearance/29stem·33legacy code를 보존했다.
fresh v1도 통과했지만 무제거 관리 선언의 시각을 실제 생성 시각으로 고친 revision r2를 v2로 보관했다.
제품 코드는 같으며 두 버전을 최종 시나리오4개로 합산하지 않는다. 자체 소유 합성 입력이며 농장 측정은 아니다.

## 자원과 범위

최종591 phase는66.20초·PID100,077,568bytes/보호+소유 합595,496,960bytes였다.
fresh v2는4.52초·PID96,387,072bytes/합540,450,816bytes였다.
.25초 표본·512MiB/PID·합1GiB/600초/로그4MiB와 기존4root/2,793감시 항목,
source 보존·FD4→4·소유 잔류0을 확인했다. Windows Chrome/전체 host 용량 수용은 아니다.
native CLI `gpt-6.1-sol/xhigh`, turn_context `2026-10-24T01:24:20.231Z` 원 LF SHA
`e9ef2cbf2a9d6cd15c70398c1777f4df9d2cd09b144691a98f5cd2328edd2496`·재귀 CLI0이다.
새 의존성/DB·키·배포 화면 변경0이며 전체 backend·새 hosted CI/브라우저는 실행하지 않았다.
이전 웹 CI의 성공은 이번 Python source 검증으로 합산하지 않는다.

기록 검증은 코드3개/graph code40개·JUnit591개·독립47행·실제 두 graph62파일과 이전 관리/준비 원문2개를 대사했다.
상대 링크3,346개와 새 파일 staging을 포함한 전체 변경의 공백/줄바꿈 검사도 통과했다.

## 다음 산출물과 외부 의존성

다음은 **appearance/관리/stem 각각의 권리를 확인한 연구 export**다. 원 root/두 입력/준비/초기 SHA와
같은 UTC/ID의12 frame을 별도 판본으로 내보낸다. 실제 두 결과의 active/removed/pending/last·합계가
원 reader와 같고, 재배포False·늦은 원본/권리 변경·부분 실패 때 완료 index0이어야 한다.
생장 import/재계산·DB/CLI0과 원 자료/화면 보존을 확인한다. 기존 exporter 패턴을 재사용한다.

이후 strict SDK와 기존 사실적 renderer adapter로 active만 같은 UTC3D·표·그래프에 연결한다.
removed 마지막 나이/면적·정확 제거 시각과 pending 예약을 분리한다. 이 자체 소유 합성 연구 경로는
농장/현재 SourceRecord·서명·기존 실행 HTTP 연결과 병행할 수 있다. 제품 Run 표시는 현재 권리/취소·멱등성·부분 게시의
별도 수용 뒤 허용한다. 연구 화면을 제품 권한 승인으로 취급하지 않으며 새 기반 서비스는 추가하지 않는다.

이전 저장/조회110–220집중분 예상은 위 실적으로 대체한다. 다음 export는 계약10–20분+구현/변경20–40분+
실제 결과/기록15–30분으로 **45–90집중분**이다. SDK/adapter25–50분+3D35–70분+브라우저/기록25–50분을 더하면
연구 화면까지 **130–260집중분**의 낮은 신뢰 추정이다. 농장/runtime·외부 자료 확보 시간은 포함하지 않는다.
[국내 자료 획득](independent-domestic-cherry-tomato-data-20261024.md)은 병행하며 원측정/미사용 독립 국내 작기0·국내 첫 품종 미확정이다.
면적에서 질량을 임의 변환하지 않는다. 생산/자원·Decimal 경제·시장/거시/수급·자율 비교,
R2/첫 cold shader·G0–G4와 전체 완료일 미정은 유지한다.
