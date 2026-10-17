# 일사 실행 메모리 진단과 관측 중복 수정 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-reclamation-and-observer-20261017.json) ·
[관측/소유권 계약](../contracts/owned-research-process-scope-v1.md) ·
[선행 조회 연결 회수](crop-greenhouse-solar-before-connection-implementation-20261017.md).

**수용한 변경은 시험 자원 관측 helper의 중복 트리 순회 수정이다.** 새5/기존32=고유37개
집중 검사가 통과했다. 제품 작업자 GC나 공개 DTO의 지연 구축 후보는 채택하지 않았다.
수정한 관측기로 실제 독립 작업자/API를 실행해도 합 RSS 한도를 넘었다.
동시 실행·새 Solar3D·사용자 배포는 미수용이다.

## 1. 작업자 회수 진단

실제 소유 SCRAM DB에서 별도 fresh 작업자가 접수/claim→before→adopt→advance→confirm을
실행했다. 원 합성 입력의 8걸음 구간이며 API 동시 조회 수용은 아니다. 각 경계에서
GC와 Linux allocator trim을 의도적으로 호출한 **시험 전용 진단**이다.

| 별도 allocator 실행 | 실제 도구/종료 | 시간 | 관측 합 RSS 최대 |
| --- | --- | --- | --- |
| malloc | 17423:0 | 55.761초 | 1,006,649,344 bytes |
| pymalloc | 1263:0 | 52.492초 | 992,710,656 bytes |

malloc의 GC 단독 RSS 회수는 모든 경계에서0이었다. GC+trim의 회수량은
before 2,707,456 / adopt 2,584,576 / advance 4,751,360 / confirm 5,046,272 bytes였다.
malloc에서 `allocated_blocks=0`은 계측 불가이며 객체0이라는 뜻이 아니다.
pymalloc의 GC 단독 회수는 before에서606,208 bytes, 나머지는0이었다.
GC+trim의 총 회수량은 before 2,396,160 / adopt 2,314,240 /
advance 4,071,424 / confirm 4,141,056 bytes였다. 일반 성능/용량 보장 수치는 아니다.

진단용 GC+trim을 실제 동시 실행에 삽입한26706:1은28.056초/1,074,176,000 bytes에서
중단됐고 첫 회수 호출 전에 한도를 넘었다. claim 뒤에도 회수하는30327:1은
30.615초/1,074,237,440 bytes에서 중단됐다. claim/before/adopt의 회수는 각각
946,176 / 1,171,456 / 1,970,176 bytes였지만 동시 실행을 수용하지 못했다.
제품에 GC/trim을 추가할 근거로 채택하지 않는다.

95405:1은 수정 선행 명령의 assertion 실패 뒤 기존 진단을 잘못 다시 기동한 중복 실행이다.
29.285초/1,075,326,976 bytes로 종료됐으며 비교/수용에서 제외한다. 이후 수정 성공을
별도 확인한 다음30327을 기동했다. 중복 로그와 원 종료/정리 증거는 보존했다.

## 2. 공개 DTO 지연 구축 후보

기준4e20178의 별도 worktree에서 `api_crop_replay._Public`의 `defer_build=True` 한 항목만
시험했다. 검증기·타입·단위·현재 권리·역할 감사·모델·경로는 유지했다.
설치된 Pydantic2.13.5/FastAPI0.141.1의 실제 코드를 확인했다.
공식 [설정 설명](https://pydantic.dev/docs/validation/latest/api/pydantic/config/#defer_build)과
[TypeAdapter 설명](https://pydantic.dev/docs/validation/latest/concepts/type_adapter/#rebuilding-a-typeadapters-schema)은
검증기/직렬화기 구축을 첫 사용으로 미루는 동작의 참고이며, 설치 판본의 동작 증거는 아래 실측이다.

88719:0의 default app 검사는 DB 연결을 금지하고 trusted store를 시험용으로 조립했다.
전체 OpenAPI64경로/68operation/395schema의 bytes/hash가 같았고, 대표 수량의 정상
직렬화와 bool/nonfinite/추가 필드/잘못된 단위/동결 위반5거부가 같았다.
이는 전체 도메인 회귀나 configured runtime 검증을 대신하지 않는다.

| 관측 지점 | 기준 RSS | 후보 RSS |
| --- | --- | --- |
| default app 정리 후 | 92,909,568 | 86,102,016 |
| 전체 default OpenAPI 생성 직후 | 112,611,328 | 132,186,112 |
| OpenAPI 생성·정리 후 | 105,713,664 | 111,747,072 |
| 실제 configured API 생성·정리 후 | 106,811,392 | 102,395,904 |
| 실제 prefix samples GET 뒤 | 126,787,584 | 121,819,136 |
| 실제 GET·정리 후 | 120,942,592 | 117,166,080 |

실제 configured API의 기준28786:0/후보89176:0은 같은 SCRAM DB에 별도 작업자로
먼저8걸음을 저장한 뒤 fresh API로 progress/summary/samples를 순차 조회했다.
세 HTTP200/no-store·원 수치/UTC를 확인했고 GET의 수식/CLI/SQL 변경은0이었다.
전체 envelope는 job/판본 ID가 달라 bytes가 같다는 주장을 하지 않는다. 비교한 물리
samples의 hash는 `ddf709a67165b9c7e3e0932541674806fcd20de7a004fd1b3f67fa544e17d55c`로 같았다.
tracemalloc은 사용하지 않았으며 빈 allocation 목록은 측정하지 않았다는 뜻이다.

후보의 실제 동시 실행32162:1은28.132초/1,087,008,768 bytes에서 중단됐다.
정상/hold/취소나 전진 prefix를 수용하지 못했다. OpenAPI 첫 구축 RSS도 악화됐다.
**후보는 채택하지 않으며 원본 API 코드와 별도 worktree2,345파일을 보존했다.**

## 3. 관측 중복의 RED/GREEN과 작은 수정

실제 helper의 `sample()`에 합성 트리 반환을 주입한55927:0에서 가능한 두 상태의 합37/32를
한 샘플이49로 합치는 반례를 재현했다. 이는 프로세스 관측 알고리즘의 합성 반례이며
실제 OS RSS나 과거 초과의 원인을 증명하지 않는다.

실제 변경은 `_forest()`에서 이미 관측한 identity의 하위 트리를 다시 읽지 않는 것이다.
보호 트리를 먼저 검사하고 알려진 보호/소유 고아와 새 자식 발견을 유지한다.
`identity/live/_tree/pidfd/remaining/signal_owned`와 초기화의 AST는 그대로다.
원5root·동적 자식·512MiB/PID·합1GiB·boot/PID/start/pidfd 신호 권한은 유지했다.
`/proc` 순회는 여전히 원자 스냅샷이 아니다.

| 검증 | 실제 도구/종료 | 결과 |
| --- | --- | --- |
| 새 반례/고아 RED | 27915:1 | 중복 순회2실패·고아2통과 |
| 기존+새4 GREEN | 21474:0 | 36통과 |
| 실제 낮은 owned8MiB 중단/정리 포함 최종 | 2342:0 | 새5/기존32=37통과 |
| 수정된 관측기의 실제 독립 작업자/API | 37370:1 | 합 RSS hold |

최종37검사에서 실제 normal/thread 자식, 보호 부모 종료 뒤 고아, 소유 부모 종료 뒤
정리, identity 변경·pidfd 실패/FD close, libc 오류와 선행 자식 보존을 확인했다.
새 낮은 한도 검사는 owned 가족의 실제 RSS가8MiB를 넘을 때 그 가족만 TERM으로
정리하고 보호 가족 생존/FD 불변을 확인했다. outer 실행기는 종전512MiB/1GiB를 유지했다.

37370:1은 같은64걸음/chunk1·응답 뒤10초 조회·전체 configured API와 독립 unpaused
작업자이며 GC/DTO 후보는 없다.25.273초/합1,079,226,368 bytes에서 중단됐다.
API의 POST 시작/종료는 관측됐지만 GET은0이었다. 양의 시간 적분·완료 checkpoint/
전진 prefix·최종 결과·동시 실행 수용을 주장하지 않는다. **관측 수정만으로 용량 문제는 해결되지 않았다.**

## 보존·다음 수용·사용자 산출물

모든 종료 실행에서 원본2,148항목·보호5root·두 서비스/frozen source/assets,
FD4→4·소유 process/PG/passfile/임시 PG 잔여0을 확인했다. 과거 고정 helper와 실행
로그는 수정하지 않았다. native CLI `gpt-6.1-sol`/`xhigh`의 실제 문맥·출력/판단 증거를
기록했으며 CLI 재귀 실행은0이다.

다음 작은 단계는 **configured API 생성/접수와 worker 첫 claim이 겹치는 구간의
영구 보유/일시 RSS를 분리**하는 것이다. 이번 실패는 worker 경계 회수 전에 발생했다.
실제 객체/할당 근거가 있는 수정만 분해하고, 동일 조건을 근거 없이 반복하지 않는다.
수용은 원 타입/단위·수치/UTC·입력/권리/역할 감사/소유권/필수 root/한도를 보존한
집중 회귀와 실제 동시 실행이다. 이어 정상/hold/취소·전진 prefix/조회 계산0→typed 웹/
같은 UTC3D→사용자 적용 순서다. 전제 검증 전에는 그 부모를 완료하지 않는다.

사용자는 기존5173/5174와 이번 진행 feed를 확인할 수 있다. 새 Solar3D나 UI 코드를
배포한 작업은 아니다. 실제 농장 Run0·G0–G4 `not_assessed`·승인False, 전체 CI와
새 DOM/WebGL은 미실행이다. 실제 품종/지역/시설·독립 농장·시장 자료는 남은 외부
의존성이다. 전체 goal active·완료일/남은 집중 시간 미정을 유지한다.

두 UI의 진행 기록을2026-10-17 12:42:51KST로 갱신했다. 실제56007:0에서 양쪽 HTTP200/
no-store·동일 feed bytes와 원 HTML·환기 frozen2,173파일 보존을 확인했다. DOM/WebGL은 재실행하지 않았다.
