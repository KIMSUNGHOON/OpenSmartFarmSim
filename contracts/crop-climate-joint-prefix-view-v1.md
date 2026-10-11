# 계산 중 확정 작물·기후 페이지 조회 v1

상태: **P0–P5 구현·[reader v5](../research/crop-climate-joint-prefix-read-cost-implementation-20261011.md)·[P6a 실제 정상/hold/취소 브라우저와 두 화면 복구](../research/crop-climate-joint-prefix-cancel-browser-20261011.md) 수용; P6b 사용자 활성화·최종 디자인 미수용**. 최초 계약 기준 checkout은 `625baab6ff2ad68c36487b7caf4928584f94882b`/2026-10-10이며 최신 브라우저는 제품 core `89c23d8`/2026-10-11이다.
선행은 [실행/체크포인트](crop-execution-link-v1.md), [서명 이력](crop-climate-joint-server-custody-v1.md),
[불변 페이지](crop-climate-joint-storage-v1.md), [완료 결과 투영](api-crop-climate-joint-replay-v1.md)과
[E9b 사용자 연결](../research/crop-climate-joint-execution-user-preview-20261010.md)이다.
이 계약은 새 prefix reader의 구현 기준이다. 현재5174의 계산 상태 자동 조회/완료 저장3D를 계산 중 성장3D 수용으로 바꾸지 않는다.

2026-10-11 [P6a2a reader v3](../research/crop-climate-joint-prefix-lease-guard-implementation-20261011.md)는 [임대 갱신 계약](crop-climate-joint-prefix-progress-guard-v1.md)을 적용했다. 같은 작업의 두 시각만 UTC 단조 전진할 때 원 snapshot을 유지한다. HEAD/최신 수용 이력·lifecycle/input/권리 변경 검사는 유지했다. 당시 실제 prefix 브라우저/사용자 활성화는 미수용이었다. 아래 reader v2 설명과 source 대조표는 선행 구현의 경계다.

이후 [실제 요청별 전진 진단](../research/crop-climate-joint-prefix-progress-diagnosis-20261011.md)에 따라 [P6a2b1 전진 읽기 계약](crop-climate-joint-prefix-forward-read-v1.md)을 분해하고 [v4 구현](../research/crop-climate-joint-prefix-forward-read-implementation-20261011.md)과 v5 조회 비용 수정을 수용했다. 불변 선택 판본·관측 HEAD/DB 사건의 현재 계보·권리를 증명하며 실제 page200과 P6a 브라우저도 확인했다. 사용자 활성화 P6b는 남아 있다.

## 현재 구현에서 확인한 경계

| 현재 source | 확인한 사실 | 새 구현에 필요한 연결 |
| --- | --- | --- |
| [`JointExecutionQuery._checkpoint`](../backend/app/crop_climate_joint_execution_query.py) | DB 수용 사건과 현재 서명 HEAD를 대사해 hash/counts/계산 UTC를 제공한다. 현재 HEAD가 앞서면 unavailable이다. | 원 sample/event의 읽기와 고정 판본 선택 |
| [`JointExecutionCheckpointStore._history/_snapshot`](../backend/app/crop_climate_joint_execution_checkpoint.py) | 최대4,099개 사건의 연속 publication sequence·같은 입력/attempt를 확인한다. 최초 수용 시각을 보존한다. | 특정 수용 사건을 다시 선택하고 원 proof에 결속 |
| [`_Session._proof/_selected`](../backend/app/crop_climate_joint_server_custody.py) | intent/binding과 HMAC로 보호한 HEAD 계보가 있다. | 선택한 수용 HEAD가 현재 서명 계보에 속하는지 확인 |
| [`_Files._load(head)`](../backend/app/crop_climate_joint_storage.py) | 명시한 HEAD의 header/commit/page·원 값/UTC/prefix를 검증한다. terminal root를 요구하지 않는다. | 권한이 있는 DB 수용 HEAD만 이 내부 메서드에 전달 |
| `ArtifactReader._load_root`와 `JointServerCustody.page` | 기존 공개 page reader는 completed/hold의 terminal root를 요구한다. | 이 제한을 제거하거나 임시 root를 만들지 않고 별도 prefix 진입점 제공 |
| [`_prepare`](../backend/app/crop_climate_joint_boundary.py), [`advance_chunk`](../backend/app/crop_climate_joint_continuation.py) | 출력 격자는0과 마지막 경계를 포함하지만 모든 계산 경계를 출력하지 않는다. ready에는 저장 sample이 없고,0 경계 사건 실패도 첫 출력을 막을 수 있다. | 계산 UTC와 마지막 저장 sample UTC를 구분하고 빈 결과 처리 |
| [`jointSceneSample`](../web/src/jointCropClimateGeometry.ts) | 원 sample의 LAI/50구획/온도를 기존 장면의 입력으로 변환한다. | 같은 sample 타입의 재사용; result ID 위조 없이 별도 prefix 화면 연결 |

source 해시·심볼과 실제 native CLI 판단 근거는 [P0 기계 기록](../research/artifacts/crop-climate-joint-prefix-contract-reference-20261010.json)에 고정한다.
이는 source 검토 증거이며 아래 런타임 수용 항목을 통과했다는 뜻은 아니다.

## 판본 선택과 현재 권한

읽기의 권위는 인증된 tenant의 같은 joint job 입력, **DB에 commit된 `joint_checkpoint_confirmed_v1` 사건**,
그 사건의 `publication_sequence/head_sha256/proof_sha256`와 원 서버 서명 이력이다.
브라우저가 제출한 hash나 private HEAD의 존재만으로 읽기 권한을 얻지 않는다.

1. 같은 실제 jobs/server/farm/input authority에 결속된 실행 reader를 사용한다. 현재 metadata·작물 읽기·자료 표시권을 전후 검사한다.
   기존 [농장 결속](crop-climate-joint-farm-binding-v1.md)의 farm/source/context/time/evidence·입력 판본을 대사한다.
   simulation_create/execute·작물 쓰기 권한을 읽기의 조건으로 추가하지 않는다.
2. readonly repeatable-read DB snapshot에서 job/불변 입력과 전체 bounded 수용 이력을 검증한다.
   기본 선택은 최신 DB 수용 사건이다. 페이지 요청의 세 값은 **같은 job의 실제 수용 사건**과 모두 같아야 한다.
3. 기존 nofollow·소유 directory·bounded regular file 경계에서 intent/binding/HMAC와 현재 서명 HEAD의 계보를 검증한다. P3b에서 실제 조회 잠금이 계산 재시도를 소진한 실패를 재현했으므로 reader v2는 계산의 배타 잠금을 취득하지 않는 불변 snapshot을 사용한다. 현재 signed intent/원 HEAD·DB의 전후 변경은 수치를 반환하지 않고503으로 재조회한다. 기존 writer/terminal reader의 잠금·입력/증명 형식은 유지한다.
   선택한 proof/HEAD가 그 계보의 실제 조상 또는 현재 HEAD인지 확인한다. 현재 HEAD가 뒤로 갔거나 선택 이력이 갈라졌으면 hold다.
4. **선택한** HEAD로 원 header/commit/pages·checkpoint/counts/context/UTC/prefix를 검증한다.
   새 private tail이나 orphan/temp의 숫자는 반환하지 않는다. terminal SHA가 있는 선택이면 그 원 root도 대사하되 결과 registry를 만들지 않는다.
5. 조회 종료 전에 현재 권리/입력, 같은 수용 사건과 job 상태를 다시 검사한다. 요청 중 관련 job/DB 상태가 바뀌면 Pending으로 종료한다.
   이후 새 요청은 이전 수용 사건을 다시 선택할 수 있다. 기존 진행 DTO의 전후 snapshot 검사를 약화하지 않는다.

수용 이력에 없는 private HEAD는 선택할 수 없다. 반면 유효한 새 private tail이 DB 수용을 기다리는 동안에도
**이미 수용된 이전 판본**은 위 검사를 통과하면 읽을 수 있다. 현재 진행 DTO의 `unavailable`을 새 수용 사건으로 해석하지 않는다.
최신 사건이 추가된 뒤에도 명시한 이전 수용 selector는 같은 job/input/계보·현재 권한을 확인해 읽는다.
summary와 두 종류 page의 selector가 다르면 화면에 합치지 않는다. 경로·tenant·키·서명 원문을 selector로 받지 않는다.

## 저장 시각과 값

다음 시각을 서로 대체하지 않는다.

| 필드 | 의미 |
| --- | --- |
| `observed_at` | 현재 요청의 서버 조회 시각 |
| job `updated_at` | 현재 작업 상태 갱신 시각 |
| `checkpoint_recorded_at` | 선택한 HEAD를 DB가 최초 수용한 시각 |
| `computed_through_utc` | 선택한 체크포인트의 마지막 확정 계산 경계; ready이면 null |
| `last_sample_utc` / `last_event_utc` | 선택한 불변 페이지에 실제 존재하는 마지막 sample/event의 원 UTC; 해당 행0이면 null |
| 선택 sample `time.at` | 표·그래프·수치3D가 함께 보여주는 원 저장 시각 |

원 마이크로초 UTC와 step index/elapsed·단위·유한 float·108상태/50구획·22장부/사건 합계/수지 값을 보존한다.
3D는 sample의 원 LAI/기관 구획/온도만 사용한다. `last_confirmed`에 상태가 있어도 저장 sample이0이면 장면을 만들지 않는다.
마지막 sample 뒤의 계산 시간, 사건 사이, 앞으로 계획된 output에 보간·외삽 프레임을 만들지 않는다.
수용 checkpoint가 `completed/hold`여도 job/결과 게시가 끝나기 전에는 최종 결과가 아니다.
prefix를 승인 Run·생과 수확·자원 구매·경제 예측·추천으로 표시하지 않는다. 원 합성 범위와 G0–G4 `not_assessed`를 유지한다.

조회는 Context/binding 생성·checkpoint restore/advance·RHS·적분·관리 계산·행 생성·checkpoint 수용·결과 등록/게시를0회 실행한다.
기존 raw profile/형식/hash/시간 검증은 읽기의 일부다. 새 물리 입력이나 계수를 받지 않는다.

## 모듈과 공개 HTTP 계약

P1의 새 `JointExecutionPrefixQuery`는 기존 `JointExecutionQuery`와 그 실제 jobs/server를 받는 readonly 서비스로 한다.
인터페이스는 `read(tenant,job_id,selector=None,view='summary',start=0,limit=None)`이며 없는 대상은 None,
있으면 검증된 내부 `PrefixRead`를 반환한다. Hold/Pending/SelectionConflict는 구분하고 P2만 이를 공개 DTO로 투영한다.
선택/파일 검증은 새 prefix 모듈에 둔다. 기존 terminal reader/worker·입력/증명 형식이나 수치 코드를 수정하지 않는다.
기존 `_Files._load` 등 내부 재사용은 exact source pin과 집중 검증으로 관리한다. public helper인 것처럼 취급하지 않는다.

P2/P3의 응답 판본은 `joint-crop-climate-prefix-replay-v1`이다. 다음은 구현할 **닫힌 discriminated DTO**다.

| 객체 | 필드/조건 |
| --- | --- |
| 공통 envelope | `schema_version`, 원 `scope`, `claim_scope=synthetic_joint_crop_climate_confirmed_prefix_only`, `G0_G4`, 기존 `job`, `cancel_requested`, `observed_at`, `prefix_status=none/accepted/closed`, `reference`, `summary`, `page` |
| 수용 reference | `selector={publication_sequence,head_sha256,proof_sha256}`, 선택한 기존 `ExecutionCheckpoint`, 최초 `checkpoint_attempt`, study/revision·기존 공개 Farm/Input·원 Manifest/TimeGrid의 allowlist |
| summary | 선택한 counts와 `last_sample_utc/last_event_utc`; computed UTC는 reference의 checkpoint 값. 현재 job의 상태와 선택 판본의 상태를 섞지 않는다. |
| sample/event page | `kind`, `start`, 실제 `limit`, 선택 판본의 `total`, `next_offset`, 원 `{value,time}`의 typed records; sample은 기존 `Sample`, event는 기존 공개 `Event`와 같은 whitelist |

accepted summary는 reference+summary, accepted page는 reference+page만 갖는다.
none/closed는 reference/summary/page가 모두 null이며 수치/장면을 제공하지 않는다.
`result_id`·가짜 terminal artifact tag·private 원 checkpoint/프로필·event 입력·권리/검토 원문·자격증명은 공개하지 않는다.
event의 입력 제거/계산 SHA 대사 규칙은 기존 `_event` 투영을 재사용하고 서명/HMAC·페이지 소속 검사를 대신하지 않는다.

| 새 GET | query / 성공 |
| --- | --- |
| `/v1/jobs/{job_id}/crop-climate-joint-execution/prefix` | query/body 없음; 최신 수용 summary 또는 none/closed |
| `…/prefix/samples` | `publication_sequence`, `head_sha256`, `proof_sha256` 필수; `start=0`, `limit=64` 기본 |
| `…/prefix/events` | 같은 selector 필수; `start=0`, `limit=8` 기본 |

UUID/hash/sequence는 기존 canonical 규칙을 따른다. offset은0..선택 total, limit은 samples1..64/events1..8이다.
끝 offset은 원 total과 빈 records/next_offset=null을 반환한다. UTF-8 전체 응답2MiB 이하·추가 query/중복 query/body 거부를 적용한다.
현재 metadata+작물 읽기 scopes·요청 전후 인증과 `Cache-Control: no-store`, 기존 API 오류 envelope를 사용한다.
잘못된 요청422, 인증401/범위403, 같은 tenant 대상 없음404,
유효한 selector와 DB 수용 사건 불일치409, 현재 자료/선택 증거 거부422, 전후 변경/운영 불가503이다. reader v2는 불변 snapshot이 유효하면 writer 잠금만으로 거부하지 않는다.
none의 page와 closed의 page도409로 수치를 반환하지 않는다. HMAC/변조/철회를503의 일시 대기로 바꾸지 않는다.
새 경로는 명시 runtime 조립에서 같은 객체/factory/권한을 확인할 때만 켠다. 기존 설정의 생략/기본 비활성과 기존 API 응답은 보존한다.

## 상태 전환·취소·재접속

| 현재 실행 상태 | prefix 처리 |
| --- | --- |
| queued/simulating, 수용 사건 없음 | none; 계산/관측 프레임0 |
| queued/simulating, 유효한 수용 사건 있음 | accepted; 원 attempt/최초 수용 시각 유지. 재시도 자체는 재계산·새 수용 사유가 아니다. |
| `cancel_requested=true` | closed; 즉시 prefix 장면 제거. 실제 취소 완료는 기존 worker 확인을 기다림 |
| succeeded / 수치 hold | closed; 기존 E9 진행→현재 result 검증→terminal 저장3D 경로로 전환 |
| failed/canceled/자료·권한 등 그 밖의 hold | closed 또는 현재 권리 거부; 부분 결과를 최종 결과로 승격하지 않음 |
| busy/조회 중 변경 |503; 새로 읽어 대사하며 혼합한 부분 응답 없음 |

취소는 기존 E9의 독립 취소 경로를 사용한다. 표시권 철회가 소유자의 취소를 막지 않는다.
fresh process는 DB 수용 사건/불변 파일/원 키로 재조회하며 context 재생성·writer 재개·재서명·수용 사건 쓰기를 하지 않는다.
재접속은 현재 권한부터 검사한다. 토큰·접수 원문·partial 값은 브라우저 영속 저장소에 저장하지 않는다.

## 화면 연결과 수용 기준

실행 갱신은 진행→prefix summary→같은 selector의 필요한 page를 순차 조회한 뒤 다음10초 대기를 예약한다.
계산 모니터의 무제한 동시 GET이나 별도 interval을 추가하지 않는다. cancel은 조회와 독립 전송한다.
선택한 수용 판본/원 UTC·같은 숫자를 표/그래프/장면에 표시한다. 신규 시점이 없으면 저장 시각을 유지하고 미래 애니메이션을 만들지 않는다.
새 selector의 필요한 응답을 모두 검증한 뒤 한 번에 교체한다. 인증/권리/응답 거부, 취소, 계정/작업 변경은 기존 값/장면을 제거한다.
숨김/해제/재연결의 Abort/epoch로 늦은 응답을 차단한다. terminal 전환은 prefix를 닫고 기존 완료/hold reader를 사용한다.

1. **P1 원 페이지/DB**: 실제 SCRAM의 running 중 최초/중간·sparse output/빈 ready·원 사건/UTC를 대사한다.
   DB 미수용 HEAD 선택 거부, 유효한 새 private/수용 tail 뒤의 이전 판본 조회, 현재 계보/변조·취소/늦은 철회,
   같은 입력의 재시도/최초 시각·fresh exec를 포함한다. 원 수치/시간 보존·조회 수치 호출/DB 쓰기0·read 비용/bytes·소유 정리를 확인한다.
2. **P2–P4 보호 전달**: typed whitelist·원 bytes/UTC·64/8/2MiB/끝 페이지·거부 상태·기본 비활성/조립·원 설정/결과 호환,
   실제 HTTPS/API/SDK와 현재 권한/늦은 응답·조회 계산0을 확인한다.
3. **P5/P6 사용자 3D**: 실제 running일 때 원 sample의 LAI/50구획/온도·표/장면 UTC와 WebGL을 대사한다.
   이후 완료/hold의 원 결과·취소/빈 출력·재접속/철회·선택 변경을 확인한다. 기록 응답과 실제 서버 검증은 별도 집계한다.
   제어된 관측 장벽은 원 수치 확인용 시험이라고 기록하며 사용자 서비스에는 넣지 않는다. 장벽 없는 사용자 계산 중 관측은 별도로 검증한다.

각 단계는 WSL의 기존5173/5174 guardian 전체 자식과 재부모화된 PG를 보호·합산한다.
단일512MiB/합1GiB·nice19/threads1·0.25초 RSS·원 source/assets/artifact·PID/start_ticks/boot·실제 terminal/FD/소유 정리를 기록한다.
전체 prefix를 검증하는 현재 `_load`의 비용은 누적 commit/page 수에 비례한다. **bounded 응답이 일정한 조회 비용을 뜻하지 않는다.**
P1에서 실제 비용을 관측하고 필요가 확인될 때 최적화한다. 짧은 합성 범위의 수용을 전체166일·운영 용량/G4 수용으로 확대하지 않는다.
수치/입력/custody/result pin이 바뀌는 작업은 새 판본/보존·호환 검증이 필요하다. 현재 frozen 사용자 서버를 검증 중 수정하지 않는다.

작업 분해/검증 명령·조건부 시간은 [계획](../tasks/plan.md#joint-prefix-view-20261010)과
[할 일](../tasks/todo.md#joint-prefix-view-20261010)에서 관리한다.
실제 품종/농장 자료 확보와 기후 경계/자원·Decimal 경제 연결은 계속 병행 의존성이다. 이 화면의 선행 조건에 독립 농장 자료 확보를 추가하지 않는다.
