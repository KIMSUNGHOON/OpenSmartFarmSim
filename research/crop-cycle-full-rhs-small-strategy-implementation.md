# 전체 작기 runner의 작은 실행 전략 수용

2026-10-06 KST. [전체 RHS 계약](../contracts/crop-cycle-full-rhs-v1.md)의
**runner와 자작5시간 저장/재개 전략만 로컬 수용**한다.
[불변 기록](artifacts/crop-cycle-full-rhs-small-strategy-reference-20261006.json)에
실제 CLI 문맥·호출·입력/코드 해시·모든 출력 해시·원 checkpoint·실패/통과 로그와 정리를 남겼다.
`crop-cycle-burden-full-rhs`는 실제166일 종료/수지 검증 전까지 미완료다.

## 구현과 검증

core는 [runner](crop-cycle-full-rhs-reference.py),
[집중 시험](../backend/tests/test_crop_cycle_full_rhs_reference.py), 계약3파일이다.
기존 계산/입력/저장/API49파일과 수용된 profile2파일은 바꾸지 않았다.
profile의 uniform 입력 generator와 원 writer의 지원된 유지/재개 방식으로 실행한다.
수식·계수·원8초 RK4·300초 출력·사건·저장 한도·검증/현재 권리 정책은 유지한다.

최종 집중17개가13.35초에 통과했고 프로세스 종료0을 확인했다.
세 원 프로그램의 모든 행/상태, deadline과 현재 RSS 예산, invalid budget/root/code,
입력/commit 물리 변조, 원 수치 hold/확인된 과거, HEAD commit 뒤 예외/복원과
닫힌 writer의 자원 거부 뒤 실제 HEAD 복원을 검증했다. 같은 시험의 중간14/16개 통과를 더하지 않는다.
최초 미구현8오류, 벽시계 parser 시험의1실패, 예산/peak guard2실패와
저장 예외 복원1실패도 실제 종료/로그 SHA로 보존했다.
이번 단계의 전체 backend·웹·브라우저 재실행은 하지 않았다.

## 실제5시간 저장/별도 프로세스 재개

| 실제 단계 | 걸음 | RHS 호출 | wall초 | 상태 |
| --- | ---: | ---: | ---: | --- |
| 첫 chunk 뒤 명시 중단 | 123 | 620 | 1.226036 | incomplete / OPERATOR_CHUNK_PAUSE |
| 같은 root/HEAD로 별도 Python 재개 | 최종2,280 | 10,842 | 21.392898 | completed |
| terminal의 새 Python 재조회 | 최종2,280 | 0 | 0.645898 | completed |

준비0.133561초는 위 실행 시간과 별도다. 첫 chunk의 checkpoint 전체가 재개 직후와 같았다.
61개 원 출력/2사건의 행 SHA, 상태121성분·seed·UTC/clock·phase·전역 수지/cursor/
순서·출력/사건 prefix가 앞선 순수/매 chunk 재개 기준과 정확히 같았다.
그 기준은 독립 whole-program 제어 흐름과도 대사했지만 고정 rate를 공유하므로 독립 농업 검증이 아니다.
옛 기준의 program ID/solver max_steps는 다르므로 input root와 전체 manifest가 같다고 주장하지 않는다.
checkpoint 비교에서 원 입력 root와 chunk 계보 hash를 구분했다.

원19commit·665,368bytes/43파일이며 최대64행 페이지535,164bytes다.
완료 reader의 RHS0회와 terminal 재조회의 RHS0회를 확인했다.
재개 wall에는 저장과 최종 전체 reader/페이지 해시 검증을 포함한다.
첫 호출과 재개를 합친 RHS는11,462회다. 각 프로세스 FD4→4·nice10이며 순서대로 실행했다.
재개 process peak는45,854,720bytes, 관찰된 active RSS 최대는41,218,048bytes다.
관찰되지 않은 chunk 내부의 RSS 상한이나 WSL 전체 메모리라고 해석하지 않는다.
실험 입력/artifact directory를 실제 제거했고 비밀 PG/브라우저는 시작하지 않았다.

## 다음 실제166일과 보류

global wall은 준비 시작부터6시간으로 계약/검증에서 고정했다. 재개해도 deadline은 유지한다.
현재 active RSS256MiB·원512MiB/65,536파일/16,384commit·128transition 한도를 유지한다.
이는 자작 수치 실험의 예산이며 완료 날짜나 강제 프로세스 종료 상한이 아니다.
만료·자원 거부는 확인된 HEAD/checkpoint와 `incomplete`, 원 수치 hold는 원 사유/확인된 과거다.
조기 종료를 전체 작기 성공으로 표시하지 않는다.

다음은 고정된 자작166일/1,816,704걸음·47,809출력/5사건의 실제 RHS다.
첫 실제 checkpoint 중단/같은 spec 재개도 기록하고, 종료 후 모든 원행/수지·bytes/files·자원을 검증한다.
[실제 시작 관측](artifacts/crop-cycle-full-rhs-started-reference-20261006.json)은 준비96.928058초·
첫123걸음/620RHS/중단 종료0 뒤 같은 spec의 별도 Python 재개와16,086걸음 진행을 확인했다.
이 관측 시각의 상태는 실행 중이며 전체166일 완료는 아니다. 고정 deadline은
2026-10-06T12:45:32.620491Z(21:45:32 KST)로, 시작부터6시간 예산이다.
실험 directory를 재개/검증을 위해 보존하고 nice10의 단일 계산 프로세스만 사용한다.
별도 등록 농장/전체 HTTPS/같은 ID·UTC3D는 다음 `crop-cycle-burden-replay-restore`에서 수용한다.
원 입력 반복 검증31.073760초의 관측 비용을 줄이는 수정은 전체 공개 조회에 필요한 근거가 있다.
byte/hash/schema/QC/격자·현재 권리·변조 거부를 보존하는 수정과 실제 수용 전에는
전체30초 API/3D 완료 날짜를 고정하지 않는다. 5시간 단순 비례4.83시간도 완료 상한이 아니다.

실제 Axiany forcing/초기/관리 채택0건·국내 독립 검증0건·제품 crop Run0개다.
이 실험은 생과kg·자원 구매·미래 마진·추천을 게시하지 않는다. G0–G4와 운영 기반`d19f7c0`를 유지한다.
현재 실제 Codex CLI는`gpt-6.1-sol / xhigh`,2026-10-06T06:39:07.225Z이며 재귀 CLI0회다.
