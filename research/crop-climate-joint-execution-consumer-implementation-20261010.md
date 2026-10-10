# 공동 작물·기후 자동 소비 — E5b 로컬 수용

2026-10-10 KST. core `a3acae0`의 기존 loop·전용 시험·계약 세 파일을 수용했다.
[실행 증거](artifacts/crop-climate-joint-execution-consumer-reference-20261010.json)는
126,927bytes, SHA-256 `5d53948540afa35cb345dcafffe11ed1be0be9da51369c9c07f5e5519a1e4095`다.
원32초·16걸음의 합성 연구 구성에 대한 소프트웨어 증거다.

## 연결과 검증

기존 `DeterministicWorkerLoop`에 정확한 `JointExecutionWorker`/`JointExecutionOutcome`과
명시 판본 `joint-crop-climate-execution-input-v1`을 등록했다.
기존 발견·대기·임대·재시도·중지 경로를 재사용하며 새로운 queue나 실행 상태 소유자는 추가하지 않았다.
전용 [시험 파일](../backend/tests/test_joint_deterministic_work.py)에 joint 권한 fixture를 두어 기존37개 시험 bytes를 그대로 유지했다.

신규 **16개**(isolated12/실제 SCRAM 프로세스4)와 기존 **37개**(32/5), **고유53개**를 통과했다.
최종 수용 여섯 묶음의 loop/계약/기존 시험 SHA는 같다. 전체 backend나 단일 명령의 두 module 실행은 아니다.

| 검사 | 실제 확인 |
| --- | --- |
| 타입/판본 | joint 전용 판본, 미래/경제 판본 거부; 다른 outcome 타입·미종결/잘못된 시도/ID/사유 거부 |
| 출력 | 닫힌 다섯 상태의 제한된 attempt metadata; private result ID 미출력 |
| 자동 정상/신호 | UUID 인자 없이 E1 작업 발견→실제16걸음→원 terminal progress/UTC·단일 registry/publication; 다음 작업은 queued/시도0 |
| 취소 | 실제 claim 뒤 취소/SIGTERM→canceled; 수치8종0·registry/publication0·다음 작업 시도0 |
| 실제 재시도 | custody 파일 잠금→시도1 queued/계산0; 잠금 해제 뒤 같은 consumer가 기존 일정으로 다시 발견→시도2 성공·16걸음·단일 저장 |
| 미종결 | 소유 시험 임대 만료 주입→unclosed; 실제 프로세스 종료3·고정 unresolved 오류·닫힌 attempt 출력/결과/후속 실행0 |
| 기존37개 | 경제/손익분기 자동 처리·경쟁/재개·취소/신호·idle·구성/FD 경계 보존 |

SIGTERM의 제어 지점은 실제 claim 뒤 첫 수치 `_before` 직전이다. 정상 경우 원 worker가 이후 모든16걸음을 계산했다.
미종결 검사는 같은 소유 시험 DB에서 임대를 과거로 설정했다. 자연 임대600초 경과나 수치 함수 도중의 신호 시험은 아니다.
기존 E4의 구간 취소/실제 crash 복원 수용을 대체하지 않는다.

최초 신규/기존 검사는 모두 통과했다. 검토에서 live parent가 시험용 attempt JSON을 쓰는 도중 읽을 가능성을 찾아,
private 임시 파일의 fsync 후 atomic replace로 보완했다. 변경 정의는 `joint_factory` helper 하나이며
모든 test/fixture 정의와 제품 loop bytes는 같다. 실행 중 기록을 읽는 retry 한 검사만 재검증해 통과했다.
이전/최종 시험 SHA·최초 통과 기록을 보존하고 중복 검사는 고유 수에 더하지 않았다.

기본 명령은 `nice -n 19 backend/.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short`이며
선택식·원 로그 SHA·실제 child/root 종료를 묶음별로 보존했다. DSN/비밀번호·원 argv는 private에만 있다.

## 시간·자원·보존

native Codex CLI `gpt-6.1-sol/xhigh`의03:43:17.965Z context를 확인했다.
원 LF 행 SHA는 `b74b85ba26814270a0190215dedbed59a9dff3bc5d26728cbf2f27c5a2aaf78a`이며 recursive/runtime CLI 실행은0이다.
native→최종 집중 terminal은853.598초(약14분)였고 문서/commit은 별도다.

.25초 표본·child nice19에서 최대 단일138,248,192/소유+보호 합480,096,256bytes로512MiB/1GiB 안이었다.
controller FD4→4·소유 process/PG·임시 PG directory/passfile 잔존0,
새 joint 실제 시험의 schema/role0을 확인했다. 원본2,148항목·각 묶음 source·고정 사용자
source/assets·보호3 identity·5173 HTTP200을 보존했다.
전체 backend/web·빌드·전체166일 계산·hosted CI·새 사용자 runtime/배포는 실행하지 않았다. push hold를 유지한다.

## 다음 사용자 경로와 외부 의존성

다음은 E6a 같은 job/input/farm의 현재 진행 DTO다. 확정 checkpoint와 DB 수용 시각,
현재 임대/권리, 완료/수치 hold의 닫힌 결과 연결과 registry/publication을 계산 없이 대사한다.
그다음 보호 HTTP/명시 runtime → typed client → UI 자동 갱신/완료 저장3D → 실제 사용자 경로를 검증한다.
현재5173은 기존 완료 합성166일을 읽으며 계산 상태·새 checkpoint 자동 갱신은 미구현이다.
계산 도중 확정 prefix3D·전체 작기 forcing/자원/경제·최종 통합 UI는 별도 수용이다.
실제 농장 crop Run/국내 독립 자료0건·G0–G4 not_assessed와 생산/미래 마진/추천 hold를 유지한다.
