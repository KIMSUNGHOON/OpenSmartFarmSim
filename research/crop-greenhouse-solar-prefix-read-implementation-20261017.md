# 일사 확정 구간 원 조회 로컬 수용 — 2026-10-17

[계약](../contracts/crop-greenhouse-solar-prefix-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-prefix-read-implementation-20261017.json).

## 구현과 검증

SolarExecutionPrefixQuery가 같은 Solar 진행 query/jobs/admission/checkpoint/custody/result의 현재 계정·농장·자료 권리와 원 서명 이력을 확인한다. DB 확인 사건의 원 selector·최초 기록 UTC/attempt를 선택하고 원108상태·41연속/6사건 장부·15수지·PAR/NIR·관리 전후 값을 읽는다. signed intent의 승인 False와 checkpoint/binding의 provenance도 대사한다. 별도 서버 소유 witness로 응답 후 현재 권리/입력·선택/이력/HEAD를 재검사하며 외부 payload로 witness를 복구하지 않는다.

summary는 선택자가 없으면 최신 확인 사건, 명시 선택자가 있으면 해당 사건이다. sample/event는 명시 선택자에 고정하며64/8개·페이지2MiB/끝 빈 배열과 원 offset/total을 유지한다. 미확정 private HEAD를 새 공개 구간으로 채택하지 않는다. append/heartbeat는 원 선택 사건·이전 latest·관측 HEAD/현재 signed ancestry가 같을 때 허용하고, 취소/종료/attempt/token/input 변경·rollback/fork/변조/권리 철회는 부분 응답을 막는다. none/closed에는 계산 프레임이 없다. 숫자를 만들거나 계산/복원/checkpoint 확정/SQL 변경을 호출하지 않는다.

**새 전용 고유23검사**를 통과했다. 기본 실제 SCRAM15·동시 변경/후검사7·독립 fresh1이다. 성공 배치의26회 중 witness 이동 재검사1·새 sample/event 추가 조건을 강화한 동시 시험2는 중복으로 제외했다. 실패 시도는 별도 기록하며 통과 수에 합산하지 않았다.

| 배치 | 원 tool session | 통과 |
| --- | --- | --- |
| 미기동/없는 작업·읽기 scope·원 witness | 17037 | 1 |
| 계산 중 원값/희소 UTC·초기 ready | 8499 | 2 |
| 선택/범위/실제 lock·현재/늦은 권리/농장·후검사 | 72656 | 4 |
| 독립 원 HEAD/확인 사건 공개·heartbeat/취소 | 3202 | 4 |
|64+1 페이지·이전 선택자/재시도/최초 시각 | 88460 | 2 |
| audit 불변성/원 파일 변조·provenance/False 승인·witness | 40154 | 5 |
| 유효 signed rollback/fork·최신 확인 이전 HEAD 거부 | 50701 | 2 |
| 정상/수치 hold·취소 요청/확정의 closed·기존 결과 연결 | 72518 | 3 |
| 실제 새 sample/event 추가 후 동시 원 구간 유지(중복2) | 42715 | 2 |
| 실제 producer 추가 저장 뒤 독립 readonly 원 구간/fresh | 89128 | 1 |

경량 독립 프로세스는 실제 SCRAM으로 heartbeat/취소 메타데이터를 변경하거나, 실제 계산으로 미리 만든 원 signed descendant HEAD/검증된 checkpoint packet을 공개한다. 이 actor의 의도된 시험 SQL과 제품 조회 SQL0을 구분한다. 실제 계산 작업자가 동시에 새 수치를 계산했다고 주장하지 않는다. 별도 순차 producer는 실제 production advance/confirm으로 새 sample/event를 추가했고 종료한 뒤 독립 reader가 이전 선택자의 세 view 원문을 재조회했다. 원값/UTC/최초 시각·응답 해시·후검사/권리 철회·읽기 권한만 사용·DB/수치 변경0을 확인했다. 기존 wrapper의 automatic worker 문구는 이 실행의 증거로 사용하지 않는다. unpaused 자동 worker/HTTP 동시성은 후속 수용이다.

실제 audit trigger의 변경/삭제 거부6건과 반환 사건 fault6종은 구분했다. 초기 동시성 준비 코드의 session/prepare tuple 해석, 모듈 종료 기록 파일명 충돌, 독립 출력 helper의 os import 누락을 수정하고 해당 배치를 재검증했다. 최초 controller의 중복 기록 디렉터리 오류는 자식/시험 기동 전이었다. 모든 실패 시도도 원본/5root·소유 프로세스/PG/passfile 정리를 보존했다.

## 자원·보존과 사용자 산출물

512MiB/PID·합1GiB·필수5root/동적 자식·원본2,148항목·두 서비스/HTML/자산·키/역할을 유지했다. 성공 배치 관측 합 최대1064857600bytes·단일 PID 최대157368320bytes, 감독 FD4→4·소유 프로세스/PG/임시 PG/passfile/schema·roles0이다. 명목0.25초·numeric thread1/nice19·소유 PG1MiB/JIT off이며 성공10개 guard 합2128.864초는 준비/설계/기록 제외 실측이다.32초 합성 기준에64걸음/128초 페이지 경계 변형을 추가했다. 전체 작기·브라우저 동시 용량이나 실제 농장 검증은 아니다.

원 조회 코드/계약·23검사/기계 증거를 확인할 수 있다. 두 UI(5173/5174)의 개발 기록을2026-10-17 07:13:18KST로 갱신했다. 원 session89576 종료0에서 HTTP200/no-store·기록 원 bytes(SHA 13714f3be088b15dcee277a849a21e875c0be438e762e7c40c9f6835b1a7a979), 기존 두 HTML·환기 frozen2,173파일 보존을 확인했다. 수치/입력/custody/결과/현재 진행 query·worker·HTTP/runtime/OpenAPI/기존 사용자 코드·키/역할은 그대로 보존했다. DOM/WebGL·전체 CI는 재실행하지 않았고 새 Solar 사용자 실행/3D는 미배포다.

## 다음 단계와 남은 의존성

다음 한 단계는 **확정 구간의 닫힌 공개 투영과 직렬화 후검사**다. 원 상태/단위/UTC·선택/최초 시각·provenance/False 승인·2MiB/범위/빈 응답·비공개 필드 차단과 owner-bound witness/현재 권리·수치/SQL 변경0을 수용해야 한다. 이어 접수/진행/취소·prefix 보호 HTTP/명시 runtime→typed 웹/같은 UTC3D→사용자 정상/hold/취소·재접속/재시작을 각각 검증한다. 부모는 미완료다.

실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False다. 국내 한 품종/작기·독립 농장/시설/광학·시장 자료와 권리/QC 확보는 병행 과제로 남아 있으며 실제 생산/자원 구매/경제/추천·최종 UI/운영 관문과 전체 완료 날짜는 미정이다. 전체 goal은 active다.
