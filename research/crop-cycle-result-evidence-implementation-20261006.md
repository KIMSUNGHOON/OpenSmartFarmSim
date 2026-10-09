# 원 terminal 결과의 검증 증명과 현재 bytes 대사

2026-10-06 KST. [계약](../contracts/crop-cycle-result-evidence-v1.md)의3 core파일을 구현했다.
**자작 작은 terminal 결과의 수학 QC 증명 primitive를 로컬 수용했다. 전체166일·농장 권리·API/3D 수용은 남아 있다.**
[확정 과거 결과 비용](crop-cycle-result-prefix-read-cost-observation-20261006.md)에서 원 prefix QC가73.71초였으므로,
원 전체 QC의 발행과 요청 시 현재 bytes 대사를 분리했다. 공개30초/2MiB·기존 artifact 한도는 유지했다.

## 구현과 신뢰 범위

[ResultEvidenceAuthority](../backend/app/crop_cycle_result_evidence.py)는 정확한 기존 입력 authority와
서버 제공 전용 키/issuer/key ID를 고정한다. 별도 HMAC domain·판본·source/Python과 최대8MiB의
사설 canonical proof를 사용한다. 키 서비스·DB 표·서버를 추가하지 않았다.

발행은 원 `InputPacket`·`prepare_context`·`open_artifact`를 실제 호출해 terminal root의 원
전체 commit·checkpoint·시계/출력/사건 prefix·수지를 검사한다. 발행 전후 현재 입력/context와
result HEAD/root·모든 content-addressed bytes·inventory·소유 inode를 대사한다.
원 reader가 참조하지 않은 부가 blob도 거부한다. 원 summary/index/math manifest·completed/hold와
확인된 과거를 그대로 증명하며 원 객체/private token을 만들거나 계산 이력을 바꾸지 않는다.

재조회는 서명·닫힌 canonical schema·판본/issuer/key/source/Python을 먼저 검사한다.
현재 입력을 result 전체 bytes 검사 전후에 대사하고 input/result inode·HEAD/root·inventory·
원 bytes/files 한도를 확인한다. 원 parser/context 준비/수지 검사·RHS를 재실행하지 않는다.
반환되는 별도 불변 `VerifiedResultEvidence`의 summary/index/context/identity는 JSON 사본이다.
source/profile/notice/Python·키/ID가 바뀌거나 디렉터리를 복사/교체하면 기존 증명을 거부한다.
새 원 전체 QC 발행은 같은 계산 manifest를 보존한다.

no-follow·서버 소유0700 directory/0400 regular·단일 링크/ACL·읽기 전후 metadata를 확인한다.
기존 소유600/0byte writer-lock은 읽기만 하며 lock을 획득하거나 원 디렉터리에 쓰지 않는다.
증명은 검사한 bytes의 증거이며 미래 변조·프로세스/키 침해나 현재 농장 권리를 보장하지 않는다.
`rights_or_gate_approval`은 false다. 참조 proof는 실제 농장 등록·DB row·원 server custody trace를 대체하지 않는다.

## 집중 검증

[시험](../backend/tests/test_crop_cycle_result_evidence.py)의 미구현 RED는1오류/0.16초·종료2,
첫 구현은38통과/51.38초(session9986 종료0)였다. 인증된 미상 판본의 조기 거부와 result 검사 중
입력 변조/같은 bytes 디렉터리 교체의3개 회귀를 추가해 **3실패/5.16초**(session67955 종료1)를
실제 재현했다. metadata 조기 검사·입력 후검사/inode 대사 뒤 **41통과/55.28초**(session38870 종료0)다.

정상3사례·숫자 hold의 원 summary/index/context/counts/manifest·보류 과거를 대사했고,
서명/키/ID/source/판본·비정규/중복/NaN/한도·HEAD/root/blob 변조/누락/부가 파일·
쓰기 허용/hardlink/symlink/소유 directory 교체/writer-lock·발행 중 HEAD 변경·원 QC 실패를 거부했다.
조회에서 원 parser/RHS 금지·사본 격리·실패/별도 Python의 FD 정리도 확인했다.

관련 입력 영수증33개·입력 조회 문맥15개·새41개를 함께 실행해 **고유89통과/56.46초**
(session37427 종료0)를 확인했다. 반복 실행을 합산하지 않았다. 전체 backend/web/browser는 이 단계에서 실행하지 않았다.

```bash
cd backend
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_result_evidence.py -q
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_input_evidence.py tests/test_crop_cycle_input_read_context.py tests/test_crop_cycle_result_evidence.py -q
```

## 별도 작은 실제 계산과 보존 키 재시작

현재 native CLI는 `gpt-6.1-sol / xhigh`, 문맥 `2026-10-06T10:05:50.264Z`,
원 줄 SHA256 `a72b7bc3b737debdc1022a0ec55a4768f96b5c386c30b5fe33ee07313f63e4e8`다. 재귀 CLI0회.

```bash
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-result-evidence-native-small-measure-20261006.py issue
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-result-evidence-native-small-measure-20261006.py verify
```

issue session84699·별도 Python verify의 즉시 종료 모두 exit0이다. 새 자작5시간positive-tail을 원 driver로
**1,800실제 step/61출력/3관리 사건**으로 계산했다. 과거 별도5시간runner나 실제166일과 같은 실행이 아니다.
원 checkpoint/manifest·입력root·artifact SHA·proof SHA/counts는 두 process에서 같았다.

| 실제 범위 | wall초 |
| --- | ---: |
| 새5시간 실제 수학 계산 | 15.916351 |
| result proof 발행(원 terminal QC 포함) | 0.135727 |
| 발행 process의 현재 bytes 재검증 | 0.010200 |
| 보존 키의 별도 Python 현재 bytes 재검증 | 0.012837 |

증명은16,265bytes·참조33blob/HEAD 포함597,278bytes다.
원 checkpoint SHA는 `233070663da110104aa328a4328c52feffd1035b062b7fe7ccda3a254d77088f`,
math manifest SHA는 `3ca7d8d8f4a7293801d697ce833c0ec87e7dbba43d5412953c626cc529ca090a`다.
두 process의 증명 작업 RHS0·FD4→4·nice15·원53 source/새3 core 보존을 확인했다.
process peak RSS는92,327,936/86,466,560bytes다.
record 직전까지 wall16.179623/0.029877초·CPU16.000876/0.027952초는 **app import 이후**의 관측이다.
최종 record 쓰기/process 종료·farm/DB/API/브라우저는 제외했다. RSS는 import를 포함한 process 전체 peak다.
원166일 nice10과 병행했으며 OS cache는 통제하지 않았다. 별도 Python은 cold-cache/저사양 기기 증거가 아니다.

측정 script SHA는 `ad7ab6d9285681c1c2f504dec3839fff3b9b39c8410329610afacc0365c67425`다.
[불변 receipt v2](artifacts/crop-cycle-result-evidence-reference-20261006-v2.json)의 SHA는
`b9f3fac42f03f4ba184911eecbae578cd6bf09270c3434339383ed376d9bd00f`다.
[v1](artifacts/crop-cycle-result-evidence-reference-20261006.json)의 process wall 시작 설명을 바로잡은 새 판본이며,
원 v1과 모든 실측/시험/source hash를 보존했다. 비밀 키/합성 raw 입력은 공개 receipt나 Git에 넣지 않았다.

## 다음 단계의 수용 기준과 남은 의존성

다음 작은 작업은 별도 **결과 조회 타입**의 module/시험/계약3 core파일이다.
현재 입력/결과 증명 뒤 실제 page를 읽고 원 reader의 출력/관리 원값·UTC/순서/count/cursor·
완료/hold 과거와 대사한다. page SHA/파일 보안·bounded cache/byte-short·반환 직전
전체 입력/결과 재대사·변조/교체/닫힘·별도 Python/FD 정리를 검증한다.
원 v1 private token·객체를 위조하거나 원 RHS를 실행하지 않는다.

이후 현재 Farm/Scope/등록/권리와 **실제 원 DB row/custody trace** 연결 → 원 전체166일
저장·중단 복원/같은 ID/UTC3D 순서다. 원81574의53 source·spec/격자/출력·고정deadline은 변경하지 않았다.
실제 전체 terminal·proof 크기/발행·모든 원 출력/수지·30초/2MiB PG/TLS/3D는 별도 수용해야 한다.
replay-restore/부하 부모는 미체크다. remote8fe의 실패와 별도e310의 로컬18개 수정 수용은
[종료 CI 보류](crop-cycle-full-rhs-ci-hold-20261006.md)에 있으며 main 반영은 원166일 종료 뒤다.

실제 품종/작기 입력·국내 독립 검증 자료는0건이고 G0–G4는 not_assessed다.
전체/API 실측 후 작업 날짜를 갱신한다. 생과 → 자원 → Decimal 경제 순서와 생산 예측/추천 보류를 유지한다.

## 변경 검토와 문서 대사

원 전체 QC와 현재 byte 조회의 신뢰 경계·실패 정리·판본/서명 조기 거부를 검토했고,
조회 중 변경의 실제3실패를 수정한 뒤 수용했다. 기존 module 경계를 보존한277줄의 새 module이며
표준 라이브러리/기존 canonical/file helper를 사용했다. 추가 의존성·공유 경로 변경은 없다.
성능 수용은 위 작은 실제 결과로 한정하며 실제 전체 proof/조회 비용은 남아 있다.

PROJECT_SPEC·IMPLEMENTATION_SLICE·plan/todo·README의 수용/다음 순서를 대사했다.
로컬 Markdown 링크/anchor2,464개·99/89edge의 비순환 의존성 그래프·기존 영수증/source 핀·
원53 source/새3 core hash·`git diff --check`를 통과했다. 새 primitive만 체크하고 부모는 유지했다.
원166일 종료 뒤 별도 CI 시험 수정과 검증된 변경을 묶어 정상 push하고 새 hosted 결과를 확인한다.

## 10월7일 재개 확인

[원 세션/임시 보존 상태 유실](crop-cycle-full-rhs-missing-state-20261007.md)을 확인했다.
위5시간의 raw 입력/보존 키/측정 원본도 현재는 없으므로 v2의 과거 관측 범위로만 유지한다.
이전 비용/byte 대사를 현재 재실행하거나 원 raw 결과를 복구했다고 표시하지 않는다.
현재3 core hash는 동일하며 관련 고유89개를 다시 실행해 **89통과/57.36초**(session42759 종료0)였다.
[재확인 receipt](artifacts/crop-cycle-result-evidence-resume-20261007.json)는 기존 수용·현재 source·새 로그 hash와
과거 raw의 부재를 구분한다. 새 로그/후속 증거는 Git 밖의 지속 저장 경로에 보존한다.
