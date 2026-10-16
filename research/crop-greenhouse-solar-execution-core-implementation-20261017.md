# 일사 접수·자동 계산 핵심 로컬 수용 — 2026-10-17

[실행 계약](../contracts/crop-greenhouse-solar-execution-core-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-execution-core-implementation-20261017.json).

## 구현과 검증

기존 jobs/lease 위에 별도 SolarExecutionService·CheckpointStore·Worker를 연결했다. 새 입력/intent/checkpoint/publication/result-link 판본과 사건 이름을 사용한다. checkpoint의 닫힌 필드 집합·literal False 승인과 provenance SHA를 고정하며, 이력도 접수한 불변 farm binding의 provenance와 대사한다. 현재 권리 검증은 행 잠금 밖에서 수행하고 짧은 NO KEY UPDATE 확정 잠금에서 임대·취소·원 입력·최신 checkpoint를 다시 확인한다.

정상/수치 보류의 결과 행·연결 사건·attempt outcome·terminal을 같은 DB 거래에서 저장한다. 정상만 job publication을 만든다. 권리 철회·취소·임대 상실·최종 입력 변경은 게시를 막는다. 서명한 기존 HEAD는 새 시도가 채택하며 원 prefix를 다시 계산하지 않는다. 기존 discovery/consumer에 정확한 새 판본/worker/outcome만 추가했고 구 판본의 명시 선택을 유지했다. 모델/계수·custody·결과 저장·현재 query·공개 HTTP/runtime·역할/키·사용자 서비스는 변경하지 않았다.

**새41/기존90=고유131검사**를 통과했다. 실제 native27개와 새 소비자 경계14개, 기존 발견/소비 경계89개·실제 명령 진입점1개다.

| 배치 | 원 tool session | 통과 |
| --- | --- | --- |
| 접수·provenance/승인·중복 checkpoint·scoped 취소 | 10031 | 6 |
| 최종 코드 정상/보류의 원 수치·원자 저장 | 94290 | 2 |
| 게시 실패·늦은 scope/권리/resolver rollback | 38313 | 5 |
| 구간/종료 취소·임대 만료 뒤 prefix 채택 | 71422 | 3 |
| 증거 검증 도중 취소 경합 | 23040 | 6 |
| 검증 뒤 입력 변경/임대 만료 최종 fence | 88409 | 2 |
| 독립 자동 소비·normal/hold·독립 fresh reader | 74652 | 2 |
| 실제 SIGKILL 뒤 독립 자동 소비·재개/fresh reader | 74198 | 1 |
| 새 Solar/기존 소비·발견 경계 | 40209 | 103 |
| 별도 실제 consumer 명령 진입점 | 70313 | 1 |

실제 SCRAM 정상/보류에서 원108상태·41연속/6사건 장부·15수지·관리 사건·UTC와 저장 결과를 비교했다. 접수·중복 checkpoint·권리 검사·결과 조회는 수치/CLI 호출0이다. 정상의 원16걸음·3checkpoint와 보류 prefix/사유, 최초 확정 시각·불변 결과/연결/작업 종료를 대사했다. 다른 판본의 합성 미지시 작업은 queued 상태로 남았다.

소유한 작업자를 HEAD 저장 뒤 DB checkpoint 확인 전에 실제 pidfd SIGKILL로 종료했다(실제 종료-9). 그 시점의 확인 checkpoint/결과/publication은0이었다. 시험 제어로 임대를 만료시킨 뒤 새 독립 소비자가 기존 HEAD를 첫 확인에서 계산0으로 채택했다. start0/restore1·원 prefix와 나머지 step의 합16을 확인했고, 또 다른 reader가 같은 DB/파일에서 원 bytes/UTC/해시/최초 시각을 재계산·SQL 변경 없이 읽었다. 준비 A→계산 B→조회 C를 순차 실행하며 모든 Python assertion을 유지했다.

취소 경합6종은 검증 barrier를 유지한 채 취소가5초 안에 수락됨과 worker 확인·부분 checkpoint/결과 rollback을 입증했다. 입력 사용 권리가 철회돼도 소유자의 현재 취소 권한을 검사한다. 잘못된 provenance/승인 이력 검사는 실제 조회 결과의 fault injection이며 실제 DB 변조라고 주장하지 않는다. 임대 만료/입력 변경 등 의도된 시험 제어 SQL과 제품 조회 SQL0은 구분한다.

## 자원·보존과 실패 기록

필수5root/동적 자식·원본2,148항목·기존 API/worker·두 서비스 frozen source/자산·키/배포 역할을 유지했다. 감독 FD4→4·소유 프로세스/PG/임시 PG/passfile/시험 schema·roles0을 확인했다. 512MiB/PID·합1GiB·명목0.25초·numeric thread1/nice19를 준수했다. 관측 합 최대1,040,125,952bytes·단일 PID 최대139,718,656bytes다. 소유 시험 PG만 shared_buffers1MiB/JIT off를 사용했다. 전체 작기·API/worker/브라우저 동시 운영 용량 증거는 아니다.

첫 선택자는 복합 fixture ID를 빠뜨려 검사를 실행하지 못했다. 독립 시험의 SignalStop API 사용과 set의 JSON 인계도 처음 두 시도에서 실패했다. 실제 API와 명시 직렬화로 수정했으며 실패를 통과 수에 넣지 않았다. provenance 이력 비교 보완 전 예비 정상/자동 소비 검사도 최종 수에서 제외했다. 무거운 pytest 부모와 새 계산 자식을 겹치는 구형 시험 경로는 순차 독립 프로세스 시험으로 대체했으며, 원 값 비교·실제 계산·강제 종료·현재 권리·원자 저장 기준을 유지했다.

## 사용자 산출물과 다음 단계

실행 계약·코드·131검사/기계 증거와 두 UI의 최신 개발 기록을 확인할 수 있다. 원 session55596 실제 종료0으로 두 주소의 기록 HTTP200/no-store·원 bytes, 기존 HTML·환기 frozen2,173파일을 확인했다. 기록 시각2026-10-17 05:23:13KST·SHA d0c7ebcc7a5eaafcaef693ed0c6f62bf3e4dd75265a698be64707727b7707de7이다. 새 일사 실행을 사용자가 접수하거나 현재 진행/확정 prefix를3D로 보는 경로는 아직 적용하지 않았다. 기존 환기 사용자 실행은 유지한다. 현재 DOM/WebGL·전체 CI는 재실행하지 않았다.

다음 한 단계는 **현재 일사 실행 진행 조회**다. 같은 jobs/admission/checkpoint/custody/result의 정확한 조립에서 현재 계정·농장·자료 권리를 확인하고, 최초 DB 확정 시각·원 HEAD/progress/UTC·완료/hold result link를 제공해야 한다. 조회 중 계산/새 행0·fresh 동일 응답·철회/변조/임대·취소/재접속·기존 서비스/자원/소유 정리가 수용 기준이다. 이어 확정 prefix의 원 sample/event reader→접수/진행/취소·prefix 보호 HTTP/명시 runtime→typed 웹/같은 UTC3D→사용자 재접속/재시작을 연결한다.

합성32초·실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False이며 새 일사 모델은 미배포다. 국내 한 품종/작기·독립 농장/시설/광학·시장 자료와 권리/QC 확보는 병행하며 실제 예측/추천 관문은 유지한다. 전체 생산·자원 구매·경제·최종 UI·운영 수용과 완료 날짜는 미정이다. 전체 goal은 active다.
