# 일사 확정 구간 공개 응답 v1 — 로컬 수용

상태: [전용91검사로 로컬 수용](../research/crop-greenhouse-solar-prefix-projection-implementation-20261017.md). HTTP/runtime·사용자3D는 후속이다.

선행: [확정 구간 원 조회](crop-greenhouse-solar-prefix-v1.md),
[일사 공개 원량](api-crop-greenhouse-solar-replay-v1.md),
[현재 진행 응답](crop-greenhouse-solar-execution-query-v1.md).

`joint-solar-prefix-replay-v1`은 none/closed/accepted의 닫힌 discriminated union이다.
none/closed는 reference/summary/page=null이며 계산 프레임을 만들지 않는다.
accepted는 원 selector·최초 확인 UTC/attempt·farm/input·manifest/time grid와 summary 또는 page 하나를 제공한다.
원108상태·41연속/6사건 장부·15수지·PAR/NIR·관리 전후 진단/원량·단위/UTC를 기존 Solar 타입으로 보존한다.
원 부동소수량은 유한 binary64 float이며 int/bool/string/NaN/Inf와 잘못된 단위·50기관 배열을 거부한다.

`scope=synthetic_joint_solar_math_only`, `claim_scope=synthetic_joint_solar_confirmed_prefix_only`,
G0–G4 not_assessed·top/reference/checkpoint의 literal rights_or_gate_approval=False다.
checkpoint/input provenance가 같아야 하며 per_m2_floor·unvalidated_for_registered_crop와 원 정규화/QC/증거 판본을 표시한다.
현재 모델 코드/정책·원 manifest/context·정수 microsecond UTC 격자/계산 단계·원 선택/건수/범위를 대사한다.
samples/events의64/8개·전체 UTF-8 응답2MiB·끝 빈 배열/정확한 next_offset을 검증한다.
원 입력/params/forcing/event 명령·rights/review/provenance 원문·서명/개인 경로·자격증명은 반환하지 않는다.

순수 `project_prefix(record)`/`_public_bytes`는 현재 접근 권한이나 DB 수용을 승인하지 않는다.
`read_prefix(query,tenant,job_id,selector,view,start,limit)`는 정확한 SolarExecutionPrefixQuery만 받아 원 조회→투영→직렬화→
owner-bound witness/현재 권리·입력·DB 사건·signed ancestry/선택 원 페이지 후검사→bounded bytes로 반환한다.
없으면 None, 잘못된 요청/선택 충돌·Pending·현재 접근 거부는 원 경계를 유지하고 다른 오류는 generic ProjectionHold다.
정상 append/heartbeat는 원 선택자/페이지가 같을 때 허용한다. 취소/종료/attempt/token/input 변경은 부분 응답을 게시하지 않는다.
조회·투영·후검사에서 계산/복원/확정/SQL 변경은0이다. 이 모듈은 HTTP 경로를 설치하지 않는다.

## 수용 기준

1. 순수 닫힌 schema·유한 float/단위/배열·원 sample/event/UTC·False/provenance·코드/정책·2MiB/비공개 경계를 검증한다.
2. 실제 SCRAM의 none/ready/running/정상/수치 hold/취소·읽기 scopes·현재/직렬화 뒤 권리/농장·실제 페이지 변조·원 witness를 검증한다.
3. 직렬화 중 독립 heartbeat/취소·원 signed HEAD/확인 사건 전진 뒤 원 응답 유지 또는 Pending을 확인하고 actor SQL과 제품 SQL0을 구분한다.
4. 실제 producer의 새 sample/event 추가 뒤 같은 DB/키/파일의 별도 readonly 프로세스에서 원 공개 bytes(관측 시각 제외)/UTC·최초 시각을 대사한다.
5. 기존 모델/계약·원본2,148/두 UI/5root/동적 자식·512MiB/PID/합1GiB·FD/소유 프로세스/PG/passfile 정리를 유지한다.

다음은 접수/진행/취소·prefix 보호 HTTP/명시 runtime→unpaused worker·typed 웹/같은 UTC3D→사용자 적용/재접속/재시작이다.
합성32초 기준과 페이지 경계 변형의 소프트웨어 검증이다. 실제 작기/독립 자료/G0–G4/예측·추천·전체 완료 날짜는 별도다.
