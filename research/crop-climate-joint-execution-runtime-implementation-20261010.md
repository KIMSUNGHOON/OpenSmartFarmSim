# E6c 명시 작물·기후 실행 runtime — 2026-10-10

상태: **로컬 수용**, core `eb65671`. 새35/기존215 = **고유250개** 집중 검사가 통과했다.
[고정 근거 artifact](artifacts/crop-climate-joint-execution-runtime-reference-20261010.json)는22,568bytes,
SHA-256 `2b313e0d887186e75b136554cb7fce2146baf3b34ed275769f519f766d4f853b`다.
[runtime 계약](../contracts/crop-climate-joint-runtime-v1.md)의 명시 실행 설정과
[E1–E9 계획](../tasks/plan.md#작물-계산과-ui의-실행-연결--2026-10-10)을 따른다.

## 구현과 판단

`ApiRuntimeConfig.crop_climate_joint_execution`은 정확한 bool이며 기본값False다.
True에는 기존 joint/cycle 저장 권한과 두 저장 조회 factory가 필요하다.
명시 실행 설정 `operator-joint-crop-climate-execution-api-config-v1`은 이 top-level flag를 필수로 받는다.
기존 reader 판본은 그 필드를 거부하고, 기존 generic/calculation loader는 새 판본을 거부한다.
설정·DSN·TLS·key의 보호 파일 검사를 trusted factory/조립 뒤 다시 수행한다.

활성화한 runtime은 같은 joint 결과 저장소의 server/binding/input resolver에서
접수 서비스·checkpoint 저장소·진행 query를 직접 조립하고 보호 HTTP에 같은 인스턴스를 전달한다.
별도 resolver/key/농장 선택이나 새 queue/패키지/SQL 권한은 추가하지 않았다.
기존 독립 `JointExecutionWorker`/`DeterministicWorkerLoop`가 같은 보호 구성과 authority를 사용한다.
API의 `current_principal`은 요청 범위에 남는다. 요청이 끝난 뒤 그 identity로 배경 계산을 실행하지 않는다.
독립 소비기는 자신의 명시 principal로 기존 발견/임대 경로를 사용한다.
프로세스 사이에서는 같은 설정·저장 원본을 대사하며 Python object identity를 주장하지 않는다.

예정 네 파일의 경계를 실제 네 파일로 구현했다. 기존 두 application 파일과 전용 실행 runtime test,
기존 runtime 계약이다. 전용 test는 기존 reader의 수치 호출 금지 fixture와 실제 소비기 계산을 분리한다.
수치 모델/E1–E6b/결과 store/기존 발견·소비기8개 파일의 원 source SHA는 보존했다.

## 통과한 검증

| 범위 | 실제 근거 |
| --- | --- |
| 새 설정31개 | 엄격 bool·폐쇄 판본/필드·prerequisite·기본False·구형 loader 거부·보호 파일 변경14경계 |
| 실제 자동 소비2개 | 검증된 TLS로 접수→queued GET→별도 프로세스의 자동 발견/임대→simulating GET→정상/수치hold 완료 |
| 같은 결과 | 동일 job/farm/result·원 진행 query bytes·기존 저장 summary bytes 일치; 각 소비기16걸음 |
| 실제 실행 중 취소1개 | HTTPS 취소 수락 후 실제 소비기의 확인으로canceled; 직접 `ack_cancel` 호출0·수치 호출0·결과/게시0 |
| 기본 비활성1개 | 실제 SCRAM/TLS runtime의 세 실행 경로503·세 실행 객체None·custody intent 생성0 |
| 기존 회귀215개 | 설정/runtime/config214개와 기존 reader의 실제 SCRAM/TLS 원3응답·UTC/계산0 호환1개 |

접수·진행/저장 조회는 원 E6a/E6b 서비스다. 새 actual-service 시험은 queued/running/terminal을 확인한다.
실행 중 양수 checkpoint의 개별 원 counts/최초 시각 검증은 선행 E6a/E6b 증거를 유지하며
이번 검사를 그 독립 수치 대사나 실제 브라우저 polling 시험으로 확대하지 않는다.
조립 시21개 금지 호출 계수와 진행/저장 조회 시21개 계수는0이다.
소비기에는 target UUID를 전달하지 않았다. claim 뒤 소유 SIGTERM을 보내고 제어용 대기 flag를 제거해
현재 작업 완료/취소 뒤 종료0을 확인했다. 사용자용 상시 서비스 전환은 E9에 남아 있다.
원 pytest 실패 phase는0이며 실제 전체 suite와 CI는 실행하지 않았다.

## 관측 시간과 자원

기존 native Codex CLI의 `gpt-6.1-sol`/`xhigh`를 실제 turn context에서 확인했다.
시각은 `2026-10-10T05:21:38.011Z`, LF 포함 SHA는
`f1fa3b280d641452f789af6ebf8e5989780b46d786ce6f902309fa0756e5253d`다.
CLI 재귀 실행0·runtime CLI 실행0이며 native→마지막 집중 terminal은682.088초(약11분), 문서/commit은 별도다.

| 작은 실제 HTTPS 관측 | 초 |
| --- | ---: |
| 접수 |1.837–1.875|
| queued/running 진행 GET |2.894–2.943|
| 완료/hold 진행 GET |7.611 / 7.905|
| 기존 완료/hold 저장 GET |5.108 / 5.071|
| 실행 중 취소 요청 |0.075|

각 값은 단일 합성 fixture 관측이다. 운영 평균/분위수·장기 작업의 UI 지연이나 용량 수용이 아니다.
E7/E8은 요청 중복 없는 단일 polling과 마지막 확인 시각을 유지하고 E9에서 화면 비용을 측정해야 한다.

일곱 소유 controller 모두 terminal0이다. 단일 PID 최대149,450,752bytes·보호 서비스 포함 합 최대463,298,560bytes로
512MiB/1GiB 안이며 .25초 감시·phase240초 상한을 지켰다. FD4→4, 소유 PG/프로세스/임시 PG 디렉터리/passfile0이다.
원본2,148항목과 기존 preview source/assets·세 보호 identity를 보존했다.
실제5173은HTTP200이고 HTML SHA
`5e5ba2733288afc0422a03481431ba4e3804e3fc265a7ac7bd3bdb3167f1c9e1`를 유지한다.
원 private manifest/log/종료/프로세스 identity는 보호 state에 보존하고 공개 artifact에는 해시·개수·비밀 없는 결과만 둔다.

## 사용자가 볼 수 있는 범위와 후속

현재5173은 완료 합성166일의 저장 생장/수확3D이며 이 실행 runtime으로 전환하지 않았다.
이번 산출물은 실제 API/소비기 조립의 검증이며 웹 실행 UI는 E7 typed client→E8 polling 화면→E9 실제 사용자 전환이 남았다.
그 raw 작업 합은2.5–5시간, 문서/검토/통합 여유를 포함한 **4–7집중시간 잠정**이다.
10월10일 오후 연속 진행·하루6집중시간 가정의10월10일 밤–11일 KST 추정이며 E9 실측 뒤 갱신한다.
계산 중 확정 prefix3D·최종 UI 전체·공동 전체 작기/자원/경제·외부 CI/운영·자료 확보 날짜는 포함하지 않는다.

독립 국내 농장/실제 품종 자료와 실제 crop Run은0건이다. G0–G4 미평가·생산/미래 마진/순위 hold,
운영 기반 고정과 push hold는 유지한다. 다음 한 단계는 **E7 typed client**다.
