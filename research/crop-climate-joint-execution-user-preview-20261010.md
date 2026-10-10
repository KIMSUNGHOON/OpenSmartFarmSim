# E9b 계산 상태와 저장3D 사용자 연결 — 2026-10-10

## 사용자가 확인할 화면

**`http://localhost:5174/`에서 기존 제품 App·실제 HTTPS API·PostgreSQL/SCRAM·별도 자동 계산 작업자를 함께 기동했다.**
[접속 안내](../web/README.md#joint-execution-user-preview)에 따라 합성 접수 파일로 계산을 시작하거나, 이미 완료된 작업에 재접속할 수 있다.
단일 자동 조회가 같은 job의 상태·확정 checkpoint·완료/hold 결과를 연결하며, 완료 뒤 같은 저장 UTC의 수치3D를 연다.
기존 `http://localhost:5173/`은 전체 합성166일 저장 생장/수확 재생용이다. 두 주소를 하나의 최종 제품 흐름으로 통합하는 U0–U5는 미완료다.

core `6120db37dd9c84d4232b3a902c015b9f75e79004`의 operator/prepare·serve/browser/lifecycle reference4파일과 이 기록/기계 증거를 수용했다.
[기계 증거](artifacts/crop-climate-joint-execution-user-preview-reference-20261010.json)의 SHA-256은 `1616222a3a416c223e8e8abab7c9f78ee6e02c3aa7def5e650a4e390813e80e8`이다.
E9a 뒤의 **E9b 로컬 합성 사용자 연결**만 수용한다. 계산 중 확정 prefix3D·최종 제품 UI·실제 생산/마진/추천 관문은 미완료다.

## 실제 기동과 보존

기존 owned fixture builder로 농장/자료를 준비하고 private role·DB snapshot을 별도 영속 PostgreSQL에 복원했다.
런타임은 [명시 실행 조립](../backend/app/crop_climate_joint_operator_config.py)과 기존 `app.deterministic_work`를 사용한다.
HTTP 요청 principal과 명시 worker principal을 분리하고 현재 권리/검토·서명·farm/context 연결 검사를 유지했다.
입력 증거/custody/result 키와 접속 토큰은 새 random private 값이다. 기존 합성 열/경제 기준선의 시험 키는 해당 owned 범위에만 사용한다.
실제 사용자 grant는 `BearerRegistry`의 실제 clock과24시간 이내 수명을 사용한다. 시험 checkpoint 정지·브라우저 가짜 시계·모의 route는 없다.

준비·서버2회의 정상 종료를 확인했고 DB/data·불변 계산 파일·private dump를 보존했다.
재시작 뒤3개 원 작업의 job/checkpoint/result는 observed_at을 제외하고 같았다. 저장 summary/sample4개 응답 bytes와 원 불변64파일도 같았다.
새 토큰의 조회200·이전 토큰401, 재시작 직후 worker 신규 attempt0을 확인했다. 이후 검증 작업은 새 판본으로 추가했고 원64파일 hash를 보존했다.
이는 정상 종료/재기동 수용이며 강제 전원 종료·일반 운영 복구/G4 수용은 아니다.

현재 서버는 별도 frozen worktree의 core6120db3와 E8의 수용된 제품 dist를 사용한다. main의 다음 개발이 현재 서버 코드를 바꾸지 않는다.
새 실제 API는 `https://127.0.0.1:8446`, 사용자 웹은 같은 출처 `http://localhost:5174`이며 NGINX가 upstream 인증서를 검증한다.
현재 인증 종료는 **2026-10-11 17:24 KST**다. 보호된 안내/토큰/접수 JSON/DB/role dump는 저장소 밖600/700 경로에 있다.
실제 사용자 controller·service·worker·PG는 의도적으로 계속 실행한다. PID/start_ticks/boot·5초 live receipt·0.25초 RSS·bounded 종료와24시간 수명을 기록한다.

## 통과한 검증

| 최종 실제 Chromium 경로 | 검증 | phase 시간(초) |
| --- | --- | ---: |
| 새 정상 계산 | 접수→자동 실행 조회→완료→원3시점/실제 WebGL→재접속 | 106.932 |
| 새 수치 hold | 같은2시점/보류 진단·원 수치/실제 WebGL·재접속 | 118.926 |
| 새 취소 | 실행 중 서버 취소 수락→작업자 확인→결과/임의3D0 | 40.019 |
| 재시작 정상 조회 | 원 job/checkpoint/result·3시점/실제 WebGL·재접속 | 31.648 |
| 재시작 hold 조회 | 원 job/checkpoint/result·2시점/실제 WebGL·재접속 | 31.032 |

최종 **고유5경로**에서 원 UTC·readout·50과실 구획·LAI/온도 장면을 대사했다. 실제 새 정상/hold의 모든 sample 값은 E9a의 원 값과 정확히 같았다.
canvas를 화면에 표시해 draw call과 원 값 결속을 확인했고 실제 screenshot을 검토했다. 동시 진행 GET 최대1·page error0이었다.
응답 body 완료→DOM 대사 완료 상한은21–1,013ms이며 검사 도구 스케줄링/검증 비용을 포함한다. 순수 렌더 지연이 아니다.
정상 자동 조회는 응답 완료 뒤10초 대기한다. 작은16걸음 예제의 중간 checkpoint가 조회 사이에 지나갈 수 있으며 즉시 push/전체 작기 처리량을 뜻하지 않는다.
E9a의 관측 정지 중 확정15/16 대사도 계속 유효하지만 현재 사용자 서비스에는 그 정지를 넣지 않았다.

처음3개의 기능 검증 뒤, resource 보호 root가 API tree만 포함해 재부모화된 PostgreSQL을 빠뜨린 것을 확인했다.
기존 receipt를 보존하고 최종5개에서는 서비스 guardian 전체 tree·동적 자식을 합산했다. 앞선3개를 고유 검사/최종 합산 수용으로 다시 세지 않았다.
최종 최대 PID424,079,360bytes / 합1,035,988,992bytes로512MiB/1GiB 안이었다.
준비/조회/브라우저 phase는240초·로그4MiB 한도, 지속 서버는 명시 TTL과 종료 여유를 적용했다.
종결16phase 중14개 종료0·원 실패2개를 보존했다. 시험 소유 PG/프로세스/임시 PG/passfile0·controller FD4→4,
원본2,148·기존3프로세스·고정 source/assets·5173 HTML 원 hash/HTTP200을 확인했다. 영속 서비스의 DB/권한 passfile/전용 socket 경로는 재시작용으로 보존한다.

첫 기동 거부는 unused legacy resolver의 필수 version 속성을 누락한 조립 오류였다. 원 예외 위치를 기록하고 속성을 추가했으며 검증을 완화하지 않았다.
첫 lifecycle probe422는 farm body 필드를 조회 query로 사용한 검사 도구 오류였다. 실제 SDK가 전송한 원 query를 재사용하도록 수정했다.
제품 backend/web source는 변경하지 않았다. Python/Node 구문·staged diff 검사를 통과했고 E8 타입/제품 build·288개는 재실행하지 않았다.
전체 suite·remote CI·push/fetch/merge/workflow 변경은 실행하지 않았다.

## 판단 근거와 다음 단계

현재 native CLI의 실제 turn context는 `gpt-6.1-sol` / `xhigh`, `2026-10-10T07:49:15.867Z`,
row SHA-256 `b26ae17ad8ae0cbb660aaabc362038212395580619fe92befbab39cf2c288eee`다. CLI를 재귀 실행하지 않았다.
판단 결과는 영속 DB/기존 조립 재사용·실제 수명 토큰·독립 작업자·frozen 사용자 기동과 위 원 실패/합산 범위 수정이다.
native 근거→마지막 집중 시험 종료2,931.046초(약49분), 문서/commit은 별도다. 최초 E9b1.25–2.5집중시간 추정을 이 실측으로 갱신한다.

다음 한 단계는 **확정 prefix 읽기 계약**이다. DB가 수용한 proof/sequence만 원 sample/event 페이지와 결속하고,
미수용 private HEAD·동시 writer/취소/권리 철회·계산 UTC와 마지막 저장 sample UTC 차이를 다룬다.
그 뒤 backend→HTTP/SDK→계산 중 저장 시점3D를 작은 단계로 수용한다. 현재 terminal page를 미완료 결과에 재사용하지 않는다.
계약/의존성 대조0.5–1집중시간 잠정이며 이후 구현/사용자 날짜는 실제 reader 계약·비용 관측으로 산정한다.
실제 crop Run0·독립 국내 농장 자료0·G0–G4 `not_assessed`와 생산/미래 마진/추천 hold는 유지한다.
