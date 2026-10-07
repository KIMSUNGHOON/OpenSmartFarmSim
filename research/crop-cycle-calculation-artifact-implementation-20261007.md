# 새 계산 판본의 불변 결과 저장·재개

2026-10-07 KST. [계약](../contracts/crop-cycle-calculation-artifact-v1.md)의4 core파일을 구현했다.
**순수 연구 저장 단계만 로컬 수용했다. 전체166일·등록 농장/custody·DB/API/3D는 후속이다.**

## 구현과 경계

[새 모듈](../backend/app/crop_cycle_calculation_artifact.py)은 수용된 정확한 `CalculationContext`와
전용 checkpoint를 받아 `crop-cycle-verified-artifact-v1`의 header/commit/HEAD/root를 만든다.
원 artifact·계산식·정규화·과거 입력/결과를 수정하지 않았다.
원36개 함수 중32개는 명시한 함수/예외·내부 helper 이름 변경 뒤 AST가 같다.
변경한4개는 context/code/limits 검사, HEAD 전 검사, 페이지 인자의 형 검사, reader의 빌린 context 연결이다.
추가10개 함수는 공개 전후 검사와 기존 본체의 분리다. 이 대조는 별도 수치/실행 검증을 대신하지 않는다.

공개 연산은 현재 증명과 모든 입력 bytes를 진입/정상 반환 전에 검사하며 쓰기는 HEAD 게시 전에도 검사한다.
정상 검증 횟수는 create/finalize3, open/summary/page2, advance5다.
advance5에는 새 계산 API 자체의2회가 포함된다.
prefix 검증은 검사 경계 안의 명시 private helper를 사용하며 commit마다 전체 parser/증명 검사를 반복하지 않는다.
원 페이지/디렉터리/commit/계산 budget을 유지하고 canonical limits도 고정한다.
writer/reader는 자신이 연 FD·lock/cache만 소유한다. 정상 close 뒤 caller의 context는 열려 있고,
현재 입력/문맥 불일치 시 context와 결과 handle을 모두 닫는다.

## 실제 집중 검증

[시험](../backend/tests/test_crop_cycle_calculation_artifact.py)의 최종 실행은
**새68개 + 계산 문맥57개 + 원 입력 증명33개 = 고유158통과/151.23초·종료0**이다.

```bash
cd backend
nice -n 19 .venv/bin/python -m pytest tests/test_crop_cycle_calculation_artifact.py tests/test_crop_cycle_calculation_context.py tests/test_crop_cycle_input_evidence.py -q
```

| 검증 범위 | 실제 증거 |
| --- | --- |
| 원6프로그램 | 원 physical 결과와 순수 새 계산의 모든 sample/event·상태/수지·UTC·manifest·checkpoint를 writer/reader와 대사 |
| 원 hold7개 | 초기/사건/분수 걸음·수치 hold, 빈 과거와 last_confirmed·출력/사건 일치; 실패 checkpoint 없음 |
| 입력 검사 비용 | 공개 횟수3/2/5 및 parser/prepare 재호출 금지; commit 수와 독립 |
| 현재 입력 | root/blob·쓰기 mode·directory mode·symlink·키 변경, 실제 RHS/HEAD 전후·페이지 투영 도중 변경의 반환 차단 |
| 결과 변조 | 재해시한 counter/parent/prefix/clock/수지/예산/개수/UTC/LAI/제거량/shape/root 순서·상태13개 거부; 조회 RHS0 |
| 파일/범위 | 잘못된 root hash·symlink/FIFO/oversize/missing/UTF-8/중복 key7개, 페이지 범위·닫힌 handle, 선택 blob 재해시·복사 격리 |
| 원자성/자원 | HEAD 전후 예외 후 실제 prefix 복원, lock/오래된 HEAD/고지/코드/한도·기존 directory 거부, 실패 생성/FD/cache 정리 |

원512MiB를 넘는 orphan은 **sparse 파일의 논리 크기**로 시험했다. 실제512MiB 할당 부하가 아니다.
commit 한도는 writer의 메모리 목록을 원16,384개 길이로 만든 합성 경계 시험이며
16,384개 실제 commit의 전체 저장 부하를 주장하지 않는다. production 한도를 낮추지 않았다.

첫 미구현 import는 collection 오류였다. 이후 실제28개 통과 뒤 추가한 페이지 형/문맥 정리 시험에서
`TypeError` 전파와 invalid context의 FD 잔존을 실제2실패/2.47초로 재현했다.
페이지 kind의 명시 str 검사와 context 자체의 `recheck`를 먼저 거치는 경계로 수정했다.
그 앞의 profile 시험은 immutable mappingproxy에 쓰려다 시험 준비/teardown 오류가 났으므로
제품 회귀 재현으로 세지 않는다. 중간28/30/68개의 반복 성공을 최종158개에 합산하지 않는다.

## 실제25시간·별도 프로세스

[참조 실행](crop-cycle-calculation-artifact-reference.py)은 소유한 합성 입력의 최초 전체 QC/증명을 발행하고,
각 새 Python에서 공식 factory를 연 뒤 parser/prepare 재호출을 금지했다.
전체 실행은 **249.435초·종료0**이다. 원 수식의 독립 제어 흐름을 공유하므로 독립 농장 검증이 아니다.

- 6개 짧은 프로그램과25시간 사례의 **별도 Python 재개/읽기7개**에서 전체 checkpoint·121개 float64와
  남은 결과를 대사했다. 각 child FD4→4·실제 PID 종료·context/cache 정리를 확인했다.
- 초기/commit 뒤/내부 걸음과 forcing·관리 사건·출력이 함께 pending인 경계에서 재개했다.
  긴 사례는4,864걸음·10:40 UTC·active segment127의 step-end에서 닫았다.
- 긴 사례는300 forcing·11,400걸음·93commit·**27sample/5event**이며 독립 전체 원값/UTC·
  최종121상태/seed·누적·counter/prefix와 일치했고 checkpoint clock 검사도 통과했다.
  저장은**758,946bytes/127파일**, temp0개다.
- HEAD 전/후 child가 `os._exit(73/74)`로 즉시 종료하도록 실제 실행했다. 게시 commit은각0/1개였고,
  새 writer가 실제 HEAD/prefix부터 재개해 원 결과와 일치했다. 외부 SIGKILL/전원 손실 시험은 아니다.
- 읽기의 RHS/advance/원 integrator는각0회다. 긴 전체 읽기0.666초,
  확인한 전체 참조 페이지 중 최대32,918bytes다. HTTP30초 수용으로 확대하지 않는다.

별도100ms 표본은 긴 참조 실행 도중 시작했다. parent 활성 RSS 최대96,374,784bytes,
긴 child86,843,392bytes이며 FD 표본 최대각9개다. 짧은6개 child 전체와 순간 peak를 포착한 값이 아니다.
`ru_maxrss`의 parent/child 최대91.973MiB는 별도 지표로 보존한다. fork/exec 계승의 영향을
받을 수 있으므로 이 값을 실제 child 활성 RSS로 표시하지 않는다.
실행 tree를 삭제하고 소유 합성 증거321파일을 사설0700/파일0400 archive로 보존했다.
새 서버/DB는0개다. 실행 중 원55 source SHA·113,920,841bytes/750입력의 모든 blob SHA·root/spec/감독자 SHA를 대사했다.

실제 native CLI `gpt-6.1-sol / xhigh`와 소스/로그·원 계약·프로세스/원량/자원 대사는
[불변 receipt](artifacts/crop-cycle-calculation-artifact-reference-20261007.json)에 결속한다. 재귀 CLI는0회다.

## 다음 단계와 남은 의존성

`crop-cycle-calculation-artifact`만 체크한다. 다음은 새 계산/저장 판본의 현재 farm/Scope·계산/표시 권리·
등록/custody/DB 결속과 실제 SCRAM의 작은 계산·중단 복원이다. 이어 전체 저장 조회/같은 UTC3D를 확인한다.
원166일은 별도 실행 중이며 이25시간 수용으로 완료 처리하지 않는다.
다음 농장 결속의 파일/의존성 감사를 마친 뒤 해당 단계의 시간 추정을 갱신한다.
생과 수확 → 물/양분·구매 에너지 → Decimal 경제의 후속 순서와 운영 기반 동결을 유지한다.
실제 품종 입력/국내 독립 자료/actual crop Run은각0건, G0–G4는 `not_assessed`이며 생산 예측·추천은 보류다.
전체 backend·새 hosted CI·새 브라우저 시험과 실제 농장/전체166일 API·3D는 이번 검증에 포함하지 않는다.
