# 같은 원값·UTC를 보존하는 별도 결과 조회 타입

2026-10-07 KST. [계약](../contracts/crop-cycle-result-read-context-v1.md)의3 core파일을 구현했다.
원 계산 manifest를 보존하는 **작은 저장 결과 조회 소프트웨어** 범위다.
현재 Farm/Scope/등록/권리·원 DB/custody trace·전체166일/HTTP/3D·관문 수용은 별도다.

## 구현과 판본

[ResultReadContext](../backend/app/crop_cycle_result_read_context.py)는 원 `ArtifactReader`/`StreamContext`와
다른 타입이다. 현재 결과 authority의 서명·전체 bytes 대사 뒤 소유 no-follow FD를 열고 inode를
대사한다. 원 summary/context/manifest와 새 조회 code/판본·결과 증명 identity를 함께 보존한다.
원 private token/객체/캐시를 주입하지 않으며 v1 계산 engine은 이 타입을 실제 거부했다.

원 index의 page만 읽어 현재 파일 SHA·canonical JSON/count/첫·끝 UTC와 소유/0400 regular·
단일 링크/ACL·읽기 전후 metadata를 대사한다. cache는 sample/event 각각 한 page이며 caller에는
사본만 반환한다. sample64/event8·2MiB 한도를 유지하고 더 작은 `max_bytes`의 byte-short도 지원한다.
반환 직전 현재 입력/결과 전체 bytes·source/authority·inode/index/summary/context를 다시 확인한다.
원 full parser/context 준비/수지 검사·RHS를 호출하지 않는다. 실패하면 FD/cache를 닫는다.
키/메모리 침해·미래 변조·현재 농장 권리의 증명은 아니며 `rights_or_gate_approval`은 false다.

## 실제 시험과 수정

[시험](../backend/tests/test_crop_cycle_result_read_context.py)은 미구현 RED1오류/0.16초·종료2 후
31통과/42.74초(session47934 종료0), 추가 검증 뒤35통과/48.76초(session91303 종료0)였다.
검토에서 context 진입 직전 source 변경 시 열린 FD가 닫히지 않는 사례를 추가해
**1실패/2.32초**(session32758 종료1)를 재현했다. 진입 실패의 close를 보완한 최종 결과는
**36통과/51.83초**(session93848 종료0)다.

정상3사례·숫자 hold의 모든 원 page/UTC·summary/manifest/관리 과거·다른 위치/limit·끝을 대사했다.
실제 작은 byte 예산의 정확한 경계/다음 원 위치와 첫 record 초과 거부를 확인했다.
cache 후 입력/blob/HEAD·쓰기 허용/hardlink/symlink·같은 bytes 디렉터리 교체/소유 mode·
page 읽기 뒤 변경·summary 전 변경·source/authority/proof·잘못된 조회·닫힘을 거부했다.
caller 사본 격리·원 parser/RHS 금지·별도 Python/FD 정리·v1 engine 거부도 확인했다.

```bash
cd backend
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_result_read_context.py -q
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_input_evidence.py tests/test_crop_cycle_input_read_context.py tests/test_crop_cycle_result_evidence.py tests/test_crop_cycle_result_read_context.py -q
```

관련 네 primitive는 **고유125통과/106.31초**(session16674 종료0)였다.
새36·선행41/33/15개를 합친 목록이며 반복 실행을 합산하지 않았다.
전체 backend/web/browser는 이 단계에서 실행하지 않았다. 원86290 hosted CI의 범위와 구분한다.

## 새 지속 저장5시간과 최종 별도 Python

새 자작 positive-tail5시간을 원 driver/수식으로 실제 계산했다: **1,800걸음/61출력/3사건**,
계산15.906733초(session72037 종료0)다. 이 진단의 새 고정 global budget은300초이며 원 유실166일의
spec/deadline/예산을 재설정하지 않았다. raw/control·입력/결과 증명·보존 키는 Git 밖의 소유0700
`/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-result-evidence-resume/result-read-native-small`에 있다.

fixture 준비 당시의 조회 후보 뒤 FD 실패를 수정했다. 준비 관측은 원 수학 결과/영수증의 생성 증거로
유지하고 그 후보의 조회 시간을 최종 code 성능으로 채택하지 않는다. **최종 별도 Python**
(session73254 종료0)은 같은 원 수학 artifact/QC 영수증·보존 키를 새 조회 code로 읽었다.
원 QC 발행자의 source/판본은 유지했고 조회 identity는 최종 code SHA를 기록했다.

| 최종 별도 프로세스의 실제 범위 | wall초 |
| --- | ---: |
| 조회 타입 열기·현재 전체 bytes/FD 확인 | 0.026181 |
| 원 summary·모든61출력/3사건의2page·canonical hash 대사 | 0.345095 |
| 마지막 전체 현재 입력/결과 재대사 | 0.013116 |

원 reader와 모든 기록 hash·checkpoint/manifest·count가 같았다. 최대 응답483,532bytes·cache2page·
원 parser/context/RHS0·FD4→4·nice15·닫힘/정리를 확인했다. process peak RSS90,509,312bytes,
app import 이후 record 직전 wall0.399597초·CPU0.399579초다. import/최종 record 쓰기/process 종료·
farm/DB/API/브라우저는 wall에서 제외했고 RSS는 import를 포함한 process peak다.
OS cache는 통제하지 않았으며 별도 Python은 cold-cache/저사양 기기 증거가 아니다.

현재 CLI `gpt-6.1-sol / xhigh` 문맥은 `2026-10-07T01:57:57.942Z`, 원 줄 SHA256은
`2f2ce09f71ab416702b664816fc4ac532fba2f2a8e3c001241276dac216eae9a`다. 재귀 CLI0회.
[수용 receipt](artifacts/crop-cycle-result-read-context-reference-20261007.json)는 최종3 core/실제 호출·
시험·측정·비밀 없는 hash와 준비 후보/최종 조회의 다른 source를 구분한다.
receipt SHA256은 `55c5bc3896892c9a8aed7dd1c49c0d4fc8da04d4e34a6b5216e1371c58a817bd`다.

## 다음 한 단계와 외부 의존성

다음 `crop-cycle-current-query`의3–4 core파일은 실제 원 농장 등록/result row와 서명된
server custody trace를 현재 Farm/Scope/권리·입력/결과 증명에 전후 결속한다.
권리 철회·다른 계정/등록/trace/물리 변조·재시작을 거부하고 원 manifest·원값/UTC와
현재 조회 판본을 보존해야 한다. 실제 작은 등록 농장의 PG/TLS·30초/2MiB·정리를 검증한다.
순수 참조 proof로 농장 서버 계산 이력을 만들지 않는다.

[원166일 상태 유실](crop-cycle-full-rhs-missing-state-20261007.md)로 전체 원 terminal·복원/부하 수용은
계속 보류다. 원 증거 복구 또는 별도 판본/지속 저장의 새 전체 실험과 실제 전체 저장/API/같은 UTC3D가
필요하다. 실제 품종 입력·국내 독립 자료0건·G0–G4 not_assessed를 유지한다.
전체 날짜는 이 실행/조회 실측과 자료 확보 뒤 갱신한다. 생과 → 자원 → Decimal 경제 순서다.

## 변경 검토와 문서 대사

원 수학/증명과 새 조회 타입의 경계·파일/caller 사본·실패 정리·bounded cache·재대사 비용을 검토했다.
진입 실패의 실제 FD 누수를 수정했으며 새 module은183줄·추가 package/공유 계산 경로 변경은 없다.
source/replay identity와 현재 권리의 후속 범위를 분리했다. 원52 source·선행9 core hash와
원 CI 시험10개 본문/marker를 보존했고 추가 필수 수정 없이 위 검증 범위로 로컬 수용했다.

PROJECT_SPEC·IMPLEMENTATION_SLICE·plan/todo·README의 다음 순서와 수용 범위를 대사했다.
Markdown 링크/anchor2,496개·99/89edge의 비순환 그래프·새3 core/실제 원값 hash·
`git diff --check`를 통과했다. 결과 조회 자식만 체크하고 current-query/전체166일·복원/부하는 유지했다.
이 새 조회 타입은 현재 진행 중인86290 hosted SHA 밖이며 로컬 수용과 hosted 범위를 혼동하지 않는다.
