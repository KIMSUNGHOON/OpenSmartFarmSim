# Prefix의 임대 갱신과 조회 무효화 구분 — 설계 v1

상태: **P6a2a 설계 준비·구현/수용 전**. 2026-10-11.
근거는 [실제 예외·DB/HEAD 분류](../research/crop-climate-joint-prefix-page-diagnosis-20261011.md)다.
현재 실행 코드는 [prefix reader v2 계약](crop-climate-joint-prefix-view-v1.md)의 전체 전후 비교를 유지한다.
이 설계만으로 기존 source·API 동작·관문을 변경하거나 P6를 수용하지 않는다.

## 범위와 판단

실제 별도 작업자가 같은 simulating 작업의 임대를 갱신하면 `lease_until`과 `updated_at`이 바뀐다.
기존 reader의 DB bundle 비교와 HTTP의 직렬화 후 job 비교는 이 변화도503으로 버린다.
선택한 불변 계산 판본의 유효성과 worker 생존 확인의 시각을 구분하는 작은 자식을 먼저 구현한다.

대상 core는 `backend/app/crop_climate_joint_prefix.py`와 `backend/app/api_crop_climate_joint_prefix_routes.py`다.
검증 대상은 대응 reader/HTTP test2파일이다. 새 queue/DB schema/캐시/백그라운드 서비스는 필요하지 않다.
reader의 내부 판본과 source hash를 갱신하되 기존 공개 DTO와 선택자·입력/수치/custody/checkpoint/result 형식은 유지한다.
공개 HTTP가 실제 새 reader를 사용할 때만 새 source header를 제공한다. 사용자 활성화는 전체 P6a 뒤 P6b다.

## 허용 조건

다음 조건을 **모두** 만족하는 임대 갱신만 같은 조회로 수용한다.

1. 전후 row가 모두 같은 `simulating`, `cancel_requested=false` 작업이다.
2. 같은 tenant/job/input·stage·attempt와 **같은 실제 lease token**이다.
3. `lease_until`, `updated_at` 이외의 **모든 row 필드**가 같다. 새 DB 컬럼은 자동으로 무시하지 않는다.
4. 두 시각의 타입/UTC 의미를 확인하고 각각 뒤로 가지 않는다. 누락·타입 변경·시각 역행은 거부한다.
5. reader의 나머지 bundle, 선택한 DB 수용 사건, 원 proof/HEAD와 현재 계보, 입력/권리·계정 검사는 통과한다.

queued→simulating, attempt/token 교체, 취소·종료·reason·입력 변경은 허용하지 않는다.
simulating 이외의 상태는 기존 전체 비교를 유지한다.
임대 갱신을 계산 걸음·생장·새 수용 사건·현재 자료 권리의 증거로 해석하지 않는다.

## Reader와 HTTP 후검사의 연결

reader는 검증한 row의 비교 근거를 **서버 내부 witness**로 반환해 HTTP 후검사와 연결한다.
허용되는 두 시각을 제외한 검증된 전체 row와 실제 lease identity를 결속하고, 시각 단조성도 확인할 수 있어야 한다.
단순한 public job 필드 비교만으로 lease token 또는 비공개 입력 교체를 놓치지 않는다.
직렬화 뒤 witness 누락/오조립·다른 row·다른 token·비허용 상태 변화는 거부한다.
witness·token·내부 hash/row는 공개 payload/헤더/오류/로그에 넣지 않는다.

원 snapshot의 job/observed_at은 실제 확인한 시점의 값이어야 한다.
최종 DB probe의 row를 사용할 경우 같은 probe의 실제 시각과 결속한다.
HTTP 후검사에서 임대만 갱신됐다는 이유로 수치·checkpoint·관측 시각을 만들어 갱신하지 않는다.
요청 전후 현재 입력·표시권·계정 검사는 생략하거나 캐시하지 않는다.

## 이 자식에서 유지할 경계

- HEAD 변경과 최신 수용 이력 변화의 기존 Pending 처리를 유지한다. 정상 HEAD 전진의 별도 개선은 P6a2a 후 실제 필요를 확인해 분해한다.
- 취소/종료와 HMAC/rollback/변조·늦은 권리/계정 거부를 임대 갱신으로 허용하지 않는다.
- 현재 E6 진행 DTO의 전체 snapshot 검사, writer 임대/잠금, 모든 수치/파일/입력 증거 형식을 유지한다.
- 조회에서 계산·writer 잠금 취득·수용/결과 등록·DB 쓰기를 하지 않는다.

## 수용 기준

1. 현재 v2에서 **실제 독립 heartbeat만** 조회 중 발생시키면 거부하는 red를 보존한다. 새 reader에서 같은 원 selector/행/UTC를 확인하는 green이 필요하다.
2. 실제 HTTP의 직렬화 후 임대 갱신도 원 snapshot으로 수용한다. 서버 witness가 입력/lease identity를 결속했음을 확인한다.
3. 시각 역행·다른 token/attempt/input·비공개 row 필드·선택 이력·취소/종료는 거부한다. 외부 실제 취소와 늦은 권리/계정 거부를 회귀한다.
4. 공개 값/단위/binary64/UTC·선택자/최초 수용 시각·schema/기존 비활성 API와 과거 입력/결과 source pin을 보존한다.
5. 실제 unpaused worker 정상/hold/cancel의 prefix와 원 terminal·조회 계산/쓰기0·WSL/보호 사용자 서버/원본/FD/소유 정리·실제 종료를 확인한다.
6. 각 source 판본과 실제 실행/미실행 범위를 기록한다. P6a2a 통과를 실제 WebGL 또는 사용자 prefix 활성화로 보고하지 않는다.

이 작업은 조사에서 확인한 불필요한 거부를 줄이는 내부 소프트웨어 변경이다.
실제 농업 예측의 검증 범위는 [제품 관문](../docs/PROJECT_SPEC.md)과 [첫 구현 경계](../docs/IMPLEMENTATION_SLICE.md)를 따른다.
