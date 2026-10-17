# 일사 작업자의 검증 전 조회 연결 회수 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-before-connection-implementation-20261017.json) · [실행 계약](../contracts/crop-greenhouse-solar-execution-core-v1.md) · [앞선 할당 진단](crop-greenhouse-solar-allocation-diagnosis-20261017.md).

**연결 수명 수정의 새4/기존6=집중10개 native 검사를 수용했다. API/worker 동시 실행·새 Solar3D는 아직 미수용이다.** 판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 문맥/출력에 기록했고 재귀 실행은0이다.

추가 추적의 실제 자원 초과 시점에 열린 소유 DB 연결4개를 생성 call site와 대사했다. `_before`의 잠금 없는 작업 조회, 농장 등록 검증의 market source scope·candidate scope·thermal context 조회가 겹쳤다. 이 실행에서는 `_adopt`나 첫 수치 `advance`까지 도달하지 않았다. 자원 종료 이후의 오류를 제품 결함의 원인으로 채택하지 않는다.

제품 변경은 worker1파일이다. 최초 임대/입력의 SELECT 연결을 닫고 같은 전체 `_current` 검증을 수행한다. 이후 새로 감사한 연결에서 기존 확정 행 잠금·현재 임대/취소·원 입력 일치·갱신을 수행한다. 초기 조회에는 갱신 행 잠금이나 변경 SQL이 없다. 수식·자료/현재 권리·타입·역할 감사·최종 fence·worker 장벽·저장 형식/키/역할/모델 버전은 변경하지 않았다. 추가 연결 설정의 지연 비용은 있을 수 있으며 성능/SLA 개선으로 주장하지 않는다.

| 검증 | 실제 session | 통과 |
| --- | --- | ---: |
| 조회 연결 종료·정상/실제 취소/실제 만료/최종 입력 조회 fault | 52783:0 | 4 |
| 정상/수치 보류의 원 상태·장부·UTC/원자 저장, 임대 만료 뒤 기존 HEAD 채택·나머지만 계산 | 60726:0 | 3 |
| before/confirm-before/finish-before의 검증 중 취소·ack·부분 결과0 | 33432:0 | 3 |

원49887:1은 열린 조회 연결을 정확히 재현한 RED다. 첫 GREEN24176:1의 입력 변경 SQL은 DB의 불변성 trigger가 올바르게 차단했다. trigger를 유지하고 실제 최종 잠금 조회 뒤 반환값에만 불일치를 주입하는 시험으로 수정했다. 이 사례를 실제 DB 입력 변조로 주장하지 않는다.

최초 합배치69152:-15는 합 RSS1,075,302,400bytes로 중단됐다. 부분 통과와 후속 실패/정리 표시는 제외했다. 소유 PG 종료 뒤 controller의 자동 임시 디렉터리 제거를 별도 확인했다. 이후 정상/보류/재개와 취소를 나누고 기존에 검증한 소유 시험 PG 설정을 사용했다. 실제 `SHOW`로1MiB/연결12/work64kB/JIT·autovacuum·parallel worker off를 확인했다. per-test GC/trim·소유 backend 종료 대기도 적용했다. 이 설정은 사용자 DB/서비스 변경이나 production 튜닝 권고가 아니다.

최종 수용 묶음의 최대 합 RSS는1,042,776,064bytes다. 512MiB/PID·합1GiB와 원5root/동적 자식·원본2,148·기존 두 서비스/source/assets를 보존했다. 최종 세 묶음 모두 FD4→4·소유 process/PG/passfile/임시 PG 잔여0이다.

다음은 같은64걸음 합성 입력·chunk1·10초 조회·명시 API와 독립 unpaused 작업자의 실제 동시 재검증이다. 단독 수용이나 조회 연결1개 회수를 동시 용량 성공으로 외삽하지 않는다. 남는 중첩을 실제 call site로 확인한 뒤 다음 수정을 정한다. 실제 동시 정상/hold/취소·현재 권리·전진 prefix/원 UTC·저장 값 수용 뒤 typed 웹/같은 UTC3D와 사용자 적용으로 이어간다.

현재 전체 CI·DOM/WebGL과 새 Solar3D 사용자 배포는 미실행/미완료다. 실제 지역/품종/시설·독립 농장·시장 자료는 외부 의존성이다. 실제 농장 Run0·G0–G4 `not_assessed`·`rights_or_gate_approval=False`, 생산/경제 예측·추천 보류와 goal active를 유지한다. 전체 완료일과 남은 집중 시간은 미정이다.
