# 계산 중 확정 페이지 — P1 로컬 수용

2026-10-10 KST. core `b05d407`의 새 reader·집중 시험2파일을 수용했다.
[원 실행 증거](artifacts/crop-climate-joint-prefix-reader-reference-20261010.json)는 25,546bytes,
SHA-256 `cb9031cc1b6fad368af902cd5fff6b6118fd8914c5e1de27ad0fa566fafdb9d8`다. 짧은 합성 작물·기후 계산의 내부 읽기 계층이며 공개 API/화면 수용은 아니다.

## 산출물과 사용자 연결

`JointExecutionPrefixQuery(existing_query).read(tenant, job_id, selector, view, start, limit)`는
DB가 수용한 판본의 원 sample/event 페이지를 읽는다. 기본 summary는 최신 수용 판본을 선택하고
page는 publication sequence·HEAD/proof hash가 일치하는 명시 selector를 요구한다.
64 sample/8 event와 page2MiB를 제한하며 끝 페이지는 빈 행과 next_offset null을 반환한다.
내부 `PrefixRead`에는 farm binding/권리 검토 metadata가 포함된다. HTTP로 직접 반환하지 않으며 P2 공개 whitelist가 필요하다.

유효한 새 private/수용 tail 뒤에도 이전 수용 판본을 읽는다. 현재 서명 계보는 **최신 DB 수용 판본**과
선택한 이전 판본 모두를 포함해야 한다. 현재 권한·자료 표시권·검토·입력/농장 결속을 전후 재검사한다.
취소 요청/terminal 상태는 prefix를 닫고 수치를 반환하지 않는다. 조회 도중 DB 상태가 바뀌면 Pending으로 버린다.
계산 확정 UTC와 마지막 실제 저장 sample/event UTC를 구분한다. ready의 행0과 UTC null에 가짜 프레임을 만들지 않는다.
terminal checkpoint가 있어도 작업/결과 게시 전에는 최종 결과로 승격하지 않는다.

현재5174는 작업/확정 checkpoint 자동 조회와 완료 저장3D,5173은 완료166일 저장 재생을 제공한다.
터미널의 연구·시험 계산은 사용자 작업 DB와 별도다. P1을 두 사용자 서버에 배포하지 않았으며 계산 중 성장3D는 미완료다.

## 통과한 검증

최종 두 source SHA가 같은 **고유12개, skipped0**를 실제 PostgreSQL/SCRAM에서 순차3그룹(5/4/3)으로 통과했다.
전체 module 단일 실행·전체 회귀가 아니다. 앞선 smoke/초기4검사의 중복 통과는 고유 수에 더하지 않았다.

| 검증 | 확인한 내용 |
| --- | --- |
| running/원 시각 | 원 수치와 UTC의 타입/값 보존; sparse 출력 뒤 계산 UTC를 저장 sample UTC로 사용하지 않음 |
| 이전 판본/fresh | private tail 미수용·새 수용/시도2 뒤 원 판본·최초 수용 시각 유지; 별도 Python/SCRAM에서 관측 시각 외 같은 record |
| signed rollback | 실제 유효한 과거 HEAD bytes로 되돌리면 최신/이전 selector 모두 거부; 원 HEAD 복원 뒤 조회 |
| ready/65행 | 서명 초기화 뒤 제어된 fixture 중단의 행0/null;65개 원 sample을64+1로 읽어 같은 값/UTC·원 pagination |
| 권한/권리 | metadata/read scope 누락·현재 source rights/검토 철회·읽은 뒤 늦은 철회 거부; 쓰기/실행 권한 없이 조회 |
| 취소/변조 | 요청/ack 상태 구분·부분/최종 결과 게시0; 원 intent/proof/HEAD/commit/sample 소유 fixture 변조 거부 |
| 동시 변경/범위 | 별도 프로세스의 실제 취소를 Pending으로 검출; 잘못된 selector/limit/범위·미수용 선택 거부·실제 잠금 Pending |
| 기존 결과 | 정상/수치 hold의 원 결과 참조를 기존 reader에서 조회; prefix는 closed |

reader의 수치 준비·복원·RHS·advance·서명 수용·결과/작업 쓰기21개 호출 계수는 모두0이다.
무변경 검사에서는 DB digest가 동일하다. 별도 actor 취소의 의도적 DB 변경은 무변경 주장에 포함하지 않는다.
원 P0 기준13파일 SHA는 모두 보존했고 기존 numerical/worker/result 코드나 schema·의존성을 바꾸지 않았다.
첫 smoke는 JobStatus 객체를 JSON에 직접 넣어 실패했다. `model_dump(mode='json')`으로 고쳤으며
실패 receipt/log와 수정 전 원 source를 정확한 SHA로 보존했다. 서명 rollback 경계는 검토에서 찾아 실제 회귀를 추가했다.
ready 검사는 제어된 초기화 중단이며 실제 hard kill 시험으로 주장하지 않는다.

## 비용·자원·남은 범위

running의 summary/sample/event 원 reader 실측은 6.877–6.905초다.
원 페이지 bytes는 sample8,666/event26,683이고65행의64/1 페이지는 658,115/10,387bytes다.
인증/전체 prefix 검증을 포함한 관측이며 일정 비용 보장은 아니다. 누적 commit/page에 비례하는 `_load` 비용은 전체166일로 확대 검증하지 않았다.
P3/P4에서 실제 HTTP/SDK 시간과 순차 갱신 비용을 확인한다. 사용자 화면은 요청 정산 뒤 대기하며 무제한 동시 polling을 추가하지 않는다.

native CLI `gpt-6.1-sol/xhigh`의09:26:11.652Z context를 확인했다. 재귀/runtime CLI0이다.
native→최종 guarded terminal은 2554.329초(약43분), 문서/commit은 별도다.
nice19/threads1/.25초 RSS의 최종 그룹 최대 단일147,017,728/소유+보호 합813,441,024bytes로512MiB/1GiB 안이었다.
각 실제 종료0·FD4→4·소유 process/PG/temp/passfile0, 원본2,148항목과 두 사용자 guardian/source/assets를 보존했다.
전체 backend/web·새 HTTP/브라우저·build·사용자 서버 전환·166일 공동 계산·remote CI/fetch/push는 실행하지 않았다.

다음은 P2 typed prefix 공개 투영이다. P3a/b 보호 API/조립→P4 SDK→P5 같은 저장 UTC의 부분3D→P6 실제 브라우저/사용자 기동 순서를 유지한다.
남은 **6–12집중시간 잠정**, 작은 합성 사용자 화면은 연속 작업·검증/WSL 여건에서 **2026-10-11 KST 조건부**다.
실제 Run0/독립 국내 농장 자료0·G0–G4 not_assessed·생산/자원 구매/미래 마진/추천 보류와 전체 U3/최종 UI 미완료를 유지한다.
독립 자료 확보·기후 경계/자원·Decimal 경제 연결은 병행 의존성이며 전체 제품/현장 관문의 완료 날짜는 미정이다.
