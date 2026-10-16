# 일사 실행 현재 진행 조회 로컬 수용 — 2026-10-17

[조회 계약](../contracts/crop-greenhouse-solar-execution-query-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-execution-query-implementation-20261017.json).

## 구현과 검증

읽기 전용 SolarExecutionQuery와 닫힌16KiB 응답을 추가했다. 같은 jobs/admission/checkpoint/custody/result의 정확한 조립·코드·현재 계정/농장/자료 권리를 확인한다. 다른 tenant/stage/입력 판본은 Solar 이력 파싱 전에 구분한다. 원 HEAD/progress/provenance·계산 UTC·최초 DB 확정 시각·완료/수치 hold 결과 연결을 대사한다. top/checkpoint/result의 승인 표시는 literal False이며 provenance가 같아야 한다.

읽기 전용 repeatable-read와 별도 DB probe에서 작업/결과 묶음을 확인한다. 미기동은 none, custody 잠금/미확정 새 HEAD는 unavailable이다. 확인된 진행만 current로 반환한다. 원 시각을 새 관측 시각으로 대체하거나 임의 진행률을 만들지 않는다. 직렬화 뒤에도 전체 현재 입력/농장/자료 권리를 재검사한다. 계산·복원·checkpoint 확정·작업/결과 쓰기와 SQL 변경은0이다.

**새24/기존5=고유29검사**를 통과했다. 새 순수 응답9·실제 SCRAM15(독립 fresh2 포함), 기존 환기 응답5다. 수정 후 정상 상태/최초 확정 시각/heartbeat·retry와 독립 정상/hold를 재검사했고 중복13개는 고유 수에서 제외했다. 총 실행은42개다.

| 배치 | 원 tool session | 통과 |
| --- | --- | --- |
| 닫힌 응답/승인·provenance 거부 | 46424 | 9 |
| 미기동/취소·다른 범위·읽기 권한/늦은 철회·작업 변경 | 12027 | 4 |
| 최초 시각/heartbeat·retry·미확정/실제 lock·확인 사건 오류 | 88593 | 5 |
| 정상/수치 hold의 원 결과 연결·UTC | 3426 | 2 |
| 별도 순차 프로세스 normal/hold 원 응답 | 79849 | 2 |
| 직렬화 뒤 권리 철회·완료 묶음 오류5종 | 2268 | 2 |
| 최종 코드 응답/상태 회귀(기존5·중복 새11) | 2858 | 16 |
| 최종 코드 독립 normal/hold 재검사(중복2) | 81652 | 2 |

같은 실제 DB/키/파일에서 준비 A→자동 worker B→읽기 C를 순차 실행했다. 별도 reader의 두 조회는 관측 시각만 새로 만들고 원 응답 해시·계산 UTC·최초 확인 시각을 유지했다. create/execute/write 권한 없이 조회했고 검토 철회는 차단했다. 정상 publication1·수치 hold publication0, 전체 결과·연결·outcome·terminal을 대사했다. 반환 묶음 fault injection5종을 실제 DB 변조라고 주장하지 않는다. 별도 actor의 의도된 job UPDATE1건과 제품 조회 SQL0은 구분했다.

## 자원·보존

필수5root/동적 자식·원본2,148항목·기존 API/worker·두 서비스 source/자산·키/배포 역할을 유지했다. 감독 FD4→4, 소유 프로세스/PG/임시 PG/passfile/시험 schema·roles0을 확인했다. 관측 합 최대1058537472bytes·단일 PID 최대146161664bytes로512MiB/PID·합1GiB 안이다. 명목0.25초 sampling·numeric thread1/nice19이며 소유 시험 PG만1MiB/JIT off를 사용했다.8개 검증 guard 합1570.196초는 준비/설계/기록 시간을 제외한 실측이다. 전체 작기·브라우저 동시 운영 용량의 증거는 아니다.

수치 모델/매개변수·기존 입력/custody/결과 저장·worker·HTTP/runtime·OpenAPI/기존 요청 계약은 변경하지 않았다. 새 모듈은 응답 타입과 내부 조회이며 실행 접수/진행 HTTP 경로를 아직 설치하지 않는다.

## 사용자 산출물과 다음 단계

조회 코드·계약·29검사/기계 증거를 확인할 수 있다. 두 UI(5173/5174)의 개발 기록을2026-10-17 06:07:00KST로 갱신했다. 원 session92508 종료0에서 HTTP200/no-store·기록 원 bytes(SHA e0764f2231a7599a742386737b27700f41c831fd70c7553b380631874cf65a35), 두 HTML·환기 frozen2,173파일 보존을 확인했다. 현재 DOM/WebGL와 전체 CI는 재실행하지 않았고 변경은 로컬 commit으로 저장한다.

다음 한 단계는 [확정 구간 원 조회](../contracts/crop-greenhouse-solar-prefix-v1.md)다. 실제 DB 확인 사건의 원 selector·sample/event·UTC·최초 시각을 유지하고, 정상 append/heartbeat·미확정 HEAD 뒤에도 이전 선택자의 원 페이지를 읽어야 한다. 현재/후검사 권리·취소·rollback/fork/변조·fresh 동일성·조회 계산/SQL 변경0·5root/원본/WSL/소유 정리가 수용 기준이다. 이어 공개 투영→접수/진행/취소·prefix 보호 HTTP/명시 runtime→typed 웹/같은 UTC3D→사용자 재접속/재시작을 각각 수용한다.

합성32초·실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False이며 새 일사 사용자 실행/3D는 미배포다. 기존 환기 사용자 실행은 유지한다. 국내 한 품종/작기·독립 농장/시설/광학·시장 자료와 권리/QC 확보는 병행한다. 전체 생산·자원 구매·경제·최종 UI·운영 수용과 완료 날짜는 외부 자료·후속 작업의 실측이 없어 미정이다. 전체 goal은 active다.
