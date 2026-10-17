# 한 청크의 현재 연결 검증 비용 — 2026-10-18 KST

[관찰 계약](../contracts/crop-solar-current-binding-cost-v1.md) ·
[기계 증거](artifacts/crop-solar-current-binding-cost-20261018.json) ·
[선행54검사/원 독립16/64 미완료](runtime-role-matrix-implementation-20261017.md).

## 실제 관측

현재 source9144809의 기존 합성 fixture(planned16)에서 초기0 경계와 첫 계산1단계를
실제로 실행한 뒤 다음 `advance(budget=1)`을 계측했다. 원 독립64 입력/프로그램을 바꾼 시험이 아니다.
`97293:0`에서1검사가 통과했다. 원 UTC `00:00:02.123456Z`→`00:00:04.123456Z`,
1→2단계·yielded·기존 proof3개의 dev/inode/mode/size/mtime/ctime/hash와 directory identity를 보존했다.

| 경로 | 호출 수 | 포함 시간(초) |
| --- | ---: | ---: |
| custody advance | 1 | 14.758640 |
| 현재 binding 재검증 | 12 | 14.322975 |
| farm registration | 24 | 12.602328 |
| 역할·권한 전체 감사 | 528 | 7.070496 |
| 수치 advance_chunk | 1 | 0.048147 |

벽시계 시간은14.760040초다. 위 시간은 **중첩·계측 overhead를 포함하므로 합산하지 않는다**.
한 fixture/호출의 비용 관측이며 처리량·실제 농장 예측·전체 완료일 근거가 아니다.
`_Session._guard`11회와 open의 current 호출을 합쳐 current12회였고,
각 `_bind`의 앞/뒤 registration 때문에 조회24회가 생겼다. 권리 검사는 제거하지 않았다.

## 관측 도구 교정과 보존

71728:1은 초기0 경계를1단계로 잘못 가정한 관측 단언의 실패다.
42699:1은 UTC를 snapshot의 `at`에서 읽어 생긴 KeyError다.
현재 schema의 `times.last_confirmed.at`로 교정하고 초기 경계를 별도로 실행한 최종 도구의
source SHA·이전 실패·실제 terminal/로그 hash를 보존했다. 두 실패는 수용 검사 수에 더하지 않는다.
제품 코드·입력·권리·수식·원 unpaused 프로토콜은 이 관측 동안 바꾸지 않았다.

최종 감독60.013초·합 RSS1,042,456,576bytes·단일143,671,296bytes,
원5root·2,148항목·frozen source/assets·두 UI·FD4→4·실제 역할/schema0·
소유 비좀비/PG/임시/passfile0을 확인했다. 앞선 두 관측 실패도 같은 보존/정리를 통과했다.
표본만으로 WSL의 독립 API/worker 동시 용량을 수용하지 않는다.

## 다음 구현 한 단계의 수용 기준

1. 이12개 current 경계에서 읽는 변경 가능 참조·권리·source/farm 판본·역할·해시를 먼저 대조한다.
2. full binding 재구성과 현재 참조 검사를 나누는 최소 변경을 정하고, 각 경계의 현재 검사는 유지한다.
   요청 사이의 권한 캐시나 원 상한/청크/조회 주기 변경으로 처리량을 만들지 않는다.
3. 같은 원 binding bytes/UTC·HMAC/ancestry·디렉터리 identity, 원천/농장 권리 철회·판본/내용 변조·
   취소/만료/예외 전후의 차단을 실제 DB/파일 검사로 확인한다.
4. 같은 관측 조건에서 full registration 반복 수가24보다 줄어든 근거와 paired 비용을 기록한다.
   그 후 계측하지 않은 원64단계 독립 실행의 완료·두 prefix·원 값/UTC·정리를 별도로 통과한다.

아직 이 최적화는 구현하지 않았다. 원 정상→독립 hold→취소→계산 중 WebGL→WSL 용량/사용자 적용을 이어간다.
실제 지역/품종 자료의 권리·독립 농장 측정·향후 생산/경제/후보 비교와G0–G4는 별도 외부 의존성이다.
실제 농장 Run0·관문 미평가·새 Solar 미배포·전체 완료일 미정·goal active를 유지한다.
판단은 기록된 native `gpt-6.1-sol/xhigh` 세션에서 수행했다. 재귀 CLI나 subagent를 실행하지 않았다.

9142:0에서 이 관찰/다음 단계와 실제16/64 미완료를 두 UI의 no-store 동일 bytes로 게시했다.
원 HTML·frozen2173파일·기존5root/원본/자원을 보존했고 브라우저/디자인 재검사는 하지 않았다.
