# 새 검증 계산 판본의 서버 실행·서명 이력 — 로컬 수용

2026-10-07 KST. [계약](../contracts/crop-cycle-calculation-server-custody-v1.md)의
`crop-cycle-calculation-server-custody`만 수용한다. DB 게시·농장 연결 부모·전체166일/API/3D는 후속이다.

## 구현과 실제 수정

[서버 모듈](../backend/app/crop_cycle_calculation_server_custody.py)은481줄이며 exact 새 농장 binding·
공식 계산 context·검증 artifact와 별도 identity/intent/proof 판본·HMAC domain을 사용한다.
원36함수(중첩 포함) 중 이름 정규화 뒤29함수 AST가 같고7함수의 입력 검사/소유권·판본·게시 경계 변경을 검토했다.
원파일/서명/lock/한도와 이전55 source를 보존하며 새 queue/service/DB schema는 추가하지 않았다.
resolver가 반환한 소유 context를 모든 종료 경로에서 닫고 원/조회/외부 authority/하위 타입을 거부한다.

초기 이식판에서 **proof fsync 뒤 권리를 철회하면 HEAD가1commit 진행하는 실제 반례**를 확인했다.
1실패/1통과 뒤 HEAD 교체 직전에 현재 권리를 재검사하도록 수정했다. 수정 후 해당2개와 아래 시험을 통과했다.
초기 작업 경로/fixture 준비 오류는 동작 실패나 통과로 세지 않았다.
여러 외부 정책을 하나의 원자 snapshot으로 잠근다는 주장은 하지 않는다.

## 실제 검증 범위

| 범위 | 실행 결과 |
| --- | --- |
| 순수 journal/서명·계산/조회 | 49개/55.87초·종료0 |
| 원 signed 이력과 같은 root 공존 | 추가1개/2.19초·종료0, 앞49개 함수 AST 보존 |
| 현재 등록 농장·실제 SCRAM | 12개/423.51초·종료0 |

**고유62개를 분할 수용**했다. 중간2개/3.48초·DB 중간2개/128.29초는 중복 합산하지 않는다.
제품 module은49개·추가1개·최종 DB12개 실행 모두 동일하다. 단일 전체62개/백엔드/새 브라우저/hosted CI 수용은 아니다.

DB 실행기의 초기 source 목록에는 이전 authority의 두 경로가 남아 있었다. 실제 실행한 farm 시험 파일 SHA와
저장 progress의 `custody_code_sha256`은 해당 코드 판본을 대사했다. 목록을4 core파일로 바로잡은
추가 정상1개/86.26초도 통과했으며 중복 합산하지 않는다. 제품 소스는 동일하다.
이 추가 검증의 첫 PG 기동은 fixture 단계에서 실패했다.109byte 소켓 경로를 확인해 임시 root를 줄였고,
동일 PG 기동 한도로 재실행했다. 이 준비 오류를 제품 동작 실패나 검증 통과로 세지 않는다.

- 순수6프로그램의 원 sample/event/UTC·계산량, 확인 과거/수치 hold·정상 완료 재시도와 조회 RHS0을 대사했다.
- selected proof의 서명/parent/sequence/schema·unsigned delta·다른 key/canonical bytes·7판본/domain 변경,
  입력/파일 보안·디렉터리 교체·orphan/합산 예산·잠금·같은 revision 충돌을 거부했다.
- 실제 fork child를 proof 전후·HEAD 전후에서 `os._exit(41/42/43/44)`했다. 선택 commit1/1/1/2와
  실제0/0/0/1step만 복원하고 원 연속 결과로 완료했다. **외부 SIGKILL/전원 장애 시험은 아니다.**
- 별도 fresh Python exec에서121상태의 hex·전체 checkpoint/clock/counter를 정확히 복원했다.
  실제 계산 뒤 parent 재열기와 같은 완료 checkpoint/원 sample을 대사했고 조회 RHS0·FD4→4·cache/child 정리를 확인했다.
- 같은 tenant/study/revision의 실제 원 signed 부분 이력과 새 계산을 같은 private root에 만들었다.
  domain별 intent 경로가 다르고 원 파일 SHA/mode·FD를 보존하며 합산 예산을 대사했다. 원 이력을 재발급하지 않았다.
- 실제 SCRAM 농장에서120걸음·3시점/0관리사건을 원 적분과 대사했다. 별도 wrapper의 완료 조회/재시도 RHS0,
  현재 계정/원천 철회·proof 저장 뒤 철회·페이지 투영 뒤 철회를 확인했다.
- 실제 등록 농장의7걸음 중단을 새 서비스에서 전체121상태/clock/counter가 같은 checkpoint로 재개해120걸음으로 완료했다.
  이 농장 재접속은 같은 Python 프로세스이며 위 순수 journal의 fresh exec와 구분한다.

## 실측 비용과 정리

최종 DB 정상 호출은 advance26.843334초·inspect7.914683초·sample page8.174914초·빈 event page8.398749초다.
progress985bytes, artifact38,072bytes/6파일이다. 작은 합성 등록 농장의 내부 서비스 실측이며
전체166일·TLS/HTTP·실제 농장 정확도·생과 생산량의 근거가 아니다.

같은 정상 시험에서 새 context factory7호출은0.005688–0.006383초, 농장 prepare1호출2.493094초,
current25호출(거부 호출 포함)은1.351042–2.905241초, 실제 계산1호출1.246524초,
journal publish3호출은5.055827–5.346886초였다. **중첩 계측이므로 이 시간을 더하지 않는다.**
원 parser/preflight 반복을 금지했고 완료 뒤 advance/RHS를 호출하지 않았다.
DB 최종 시험 주 프로세스의200ms 표본 최대 VmRSS는132,001,792bytes다. PG/자식 전체 합계나 확정 peak가 아니다.
코드 검토상 각 서비스 호출은 writer를 재열고 `_progress`에서 선택 prefix 전체를 검증한다.
전체 registered 작기의 누적 재열기/수지·서명 검사 비용은 기존 replay-restore 부하 단계에서 별도로 실측한다.

세 성공한 DB 시험 실행의 schema/role/passfile 잔존0, 각 PG PID/데이터·임시 test tree 제거를 확인했다.
순수 실행·fork4개/fresh exec·FD/cache/lock 정리도 확인했다. 현재 원55 source와
750입력 파일/113,920,841bytes·모든 named blob SHA·root/spec/감독자 SHA를 보존했다.
actual 새 작물 DB row/농장 Run0, G0–G4는 `not_assessed`다.

native Codex CLI `gpt-6.1-sol / xhigh`·재귀 CLI0·판본별 실제 로그/소스/검토·정리는
[불변 영수증](artifacts/crop-cycle-calculation-server-custody-reference-20261007.json)에 결속한다.

## 다음 단계와 외부 의존성

다음은 새 판본의 SQL/role·HMAC/metadata·원자 게시/재조회와 이전 DB 이력 공존의 현행 경계 대조다.
그 뒤 실제 전체166일 종료·저장/복원·같은 UTC3D와 부하를 수용한다.
현재 서버 자식의2–4집중시간/10월7–8일 잠정 추정은10월7일 로컬 수용 실적으로 대체한다.
DB 게시의 날짜는3–4 core파일 계약·실제 비용/의존성 대사 뒤 갱신한다.
생과 수확량 → 물/양분·구매 에너지 → Decimal 경제 연결 순서와 운영 기반 동결을 유지한다.
채택된 실제 품종 입력·국내 독립 자료는 각0건이며 생산 예측·미래 마진·작물 추천은 계속 보류다.
