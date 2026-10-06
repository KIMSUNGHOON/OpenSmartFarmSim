# 원 계산 판본을 보존하는 입력 조회 문맥

2026-10-06 KST. [계약](../contracts/crop-cycle-input-read-context-v1.md)의3 core파일을
[원 검사 영수증](crop-cycle-input-evidence-implementation-20261006.md)에 연결했다.
**조회 전용 타입과 입력 대사만 로컬 수용했다. 원 전체166일 계산 결과·현재 farm/권리/API/3D는 미수용이다.**

## 판본과 구현

[InputReadContext](../backend/app/crop_cycle_input_read_context.py)는 원 `InputPacket`/`StreamContext`와
다른 타입이다. 원 타입의 private token을 쓰거나 객체/캐시를 주입하지 않는다.
서버 authority의 현재 전체 byte/서명 대사 뒤 별도 no-follow/소유 FD를 열고 같은 inode·bytes를
다시 확인한다. 원 context/index·initial/121 seed·Fraction clock·plan·manifest SHA를 그대로 보존하며
조회 identity에 **새 조회 판본/코드·영수증 SHA와 원 계산 SHA**를 함께 기록한다.
원 코드가 새 조회를 실행했다고 재표시하지 않는다.

원 판본으로 고정된 record/cursor/segment/grid helper 규칙을 재사용한다. block 읽기는 기존
server 파일 계약과 실제 SHA·원 JSON/schema/정규화/시각 index를 확인한다.
cache hit에서도 파일 보안/metadata를 대사하고 바뀌면 다시 읽는다. cache는4kind 각각1block·grid1page다.
공개 반환 전 `recheck`가 현재 source/profile/authority·원 inode·전체 bytes를 다시 대사해야 한다.
future 변조·메모리/키 침해나 농장/권리 승인을 보장하지 않는다. v1 engine/start는 새 타입을 실제 거부했다.
현재 v1 farm/artifact/runtime의 exact type 검사와 원53 source는 유지했다.

## 집중 검증

[시험](../backend/tests/test_crop_cycle_input_read_context.py)의 미구현 RED는1오류/0.90초(session38118 종료2),
구현 뒤 **15통과/1.99초**(session84330 종료0)다. 원 작은6사례의 모든 records·시계·
boundary/cursor·전역 steps/positions, parser/preflight/RHS 재호출 금지·사본/단위·cache 한도·
캐시 후 변조/쓰기 허용·root/디렉터리 교체·잘못된 proof/query/code·재시작/FD/닫힘을 확인했다.
별도 Python에서도 같은 원 경계/identity를 확인했다. 전체 backend/web/browser는 이 단계에서 실행하지 않았다.

```bash
cd backend
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_input_read_context.py -q
```

최종 사설 로그 `/tmp/ossf-cycle-input-read-context-focused-20261006.log` SHA256은
`896da58e6ce2c064aa23e5943fb9214724fea90fc7c425e63d9a86985420248e`다.

## 고정166일 입력의 실제 원 대조·재시작

현재 native CLI `gpt-6.1-sol / xhigh`의 문맥은 `2026-10-06T08:37:53.288Z`,
원 줄 SHA256 `dd6db62c9755be2e614d0f10a8bf67e39f1db2f98a5d2948ba719c35d7d9f2ad`다. 재귀 CLI0회.

```bash
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-input-read-context-measure-20261006.py full
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-input-read-context-measure-20261006.py restart
```

실제 full session21062·restart session83708 모두 종료0이며 script SHA256은
`7ad9f5305ac174f0d0ea548c1bb7df95cc05d7e23ef1342aa849d1755fcc3c5c`다.
[불변 receipt](artifacts/crop-cycle-input-read-context-reference-20261006.json)는
`2026-10-06T08:57:52.159479+00:00`, SHA256
`a21395cc30e18c2931028db4cd2341f21f6771d1f43b318451b88ed3fba97dbe`다.

| 실제 범위 | full wall초 | 별도 restart wall초 |
|---|---:|---:|
| 원 reader/prepare_context와 전체 경계 대조 기준 생성 | 44.317378 | 재실행하지 않음 |
| 새 문맥 열기·현재 bytes 전후 확인 | 0.379797 | 0.391599 |
| 원47,811경계 각각의 동일 canonical hash·steps/positions 대사 | 13.178337 | 재실행하지 않음 |
| 시작/중간/끝·5관리 전후14경계/시계·3page/cursor | 0.494217 | 0.556411 |
| 마지막 전체 원본/code/authority 재대사 | 0.182401 | 0.182610 |

전체 원 context/index record SHA는 기존과 같은
`2704b2aa70c3b2d6539c2ed1d893024413ecfb9eb8840b8dde6c31e7f913cd37`다.
원 계산 manifest SHA도 같은 `d94147de8e2044b9a535657f89d76431dbcfbfc28a67748e6ecf687849940375`다.
전체 경계 hash는 `b4f285214300f83b62ae2f704a1695de8d85268cb4a230c56903d5f2b60987b6`이며
plan1,816,704걸음·47,811경계와5관리 입력 위치를 확인했다. 실제 RHS/작기 수지 검증이 아니다.
restart는14원 경계/시계와3page를 다시 대사했으며 전체47,811을 다시 검증했다고 합산하지 않는다.

두 프로세스 RHS0·FD4→4·nice15, source53/기존 영수증3 core unchanged·cache 정리를 확인했다.
process peak RSS93,966,336/89,395,200bytes와 import/원 대조/호출부터 record 직전까지
59.213332초/1.839811초는 해당 프로세스 관측이다. 마지막 record 저장/process exit·farm/DB/HTTP는 제외했다.
기존 nice10 전체 RHS와 동시였으며 OS cache는 통제하지 않았다. 별도 Python은 cold-cache/저사양기기 증거가 아니다.
검증용 보존 키는 기존 사설 directory에서 읽었고 Git/로그/공개 receipt에 넣지 않았다.

## 다음 수용과 외부 의존성

입력 조회의 새 타입과 원 계산 provenance 분리를 구현했다. 원 full166 종료/모든 출력·수지·
중단 복원 수용 뒤 **결과 artifact 검증과 현재 farm/Scope·등록/권리 조회에 이 타입을 명시적으로 연결**한다.
기존 v1 계산/저장 코드를 새 타입으로 속이거나 manifest를 수정하지 않는다.
원 결과의 검증/보관·현재 권리·30초/2MiB/공개 UTC page·3D·정리는 남는다.
원 전체/API 실측 뒤 날짜를 갱신한다. replay-restore/부하 부모·G0–G4는 체크하지 않는다.
실제 품종 입력/독립 국내 자료0건·생과 → 자원 → Decimal 경제 순서·생산 예측/추천 보류를 유지한다.
