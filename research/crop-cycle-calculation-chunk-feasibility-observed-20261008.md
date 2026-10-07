# 같은 원값을 유지하는 4,096전이 계산 구간 관측

2026-10-08 KST. [관측 계약](../contracts/crop-cycle-calculation-chunk-feasibility-v1.md)의
순수 계산 가능성 시험을 **1통과·실제 종료0·정리로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-chunk-feasibility-reference-20261008.json)에
native CLI 문맥·실제 명령/종료/로그 SHA·268 source·checkpoint·비용·정리를 보존했다.
판단은 기존 Codex CLI `gpt-6.1-sol / xhigh`에서 수행했으며 재귀 CLI0회다.

## 실제 계산과 대사

순수 엔진이 이미 지원하는 `max_steps=10000, max_transitions=4096`을 사용했다.
고정 root와 8초 RK4·300초 출력·관리 사건·모델/매개변수는 그대로다.
비교 대상은 [최종 권한 경계 수정판](crop-cycle-calculation-prefix-attestation-implementation-20261008.md)의
실제128전이32호출이며 해당 profile SHA를 고정했다.

| 항목 | 실제 결과 |
| --- | ---: |
| 신규 순수 호출 / 전이 / 적분 걸음 | 1 / 4,096 / 3,990 |
| 확정 출력 / 관리 사건 | 105 / 2 |
| 실제 RHS 호출 | 20,056 |
| context 열기·start·advance | 37.853초 |
| 원 명령, 감사/대사 포함 | 55.567초 / 종료0 |
| FD 전후 | 12→12 |
| pytest primary 표본 최대 RSS | 196,734,976bytes |

두 계보 필드 `parent_sha256`/`checkpoint_sha256`를 제외한 checkpoint 전체가 같다.
121상태·seed·clock/cursor·누적·출력/사건 prefix를 포함한다.
기존 원166일 전체 순수 결과의 해당 행105개/사건2개와도 명시한 +273일 이동 뒤 정확히 같다.
원 checkpoint는 기존6 provenance 필드를 구분해 대사했다. 원행 조회 중 RHS 호출은 금지했다.

37.853초는 순수 계산의 해당 범위이며 등록 서버의 advance 시간과 직접 비교한 속도 개선율이 아니다.
농장 현재 권리·서명·저장·DB/API 비용을 포함하지 않는다. 전체 작기 완료 시간으로 외삽하지 않는다.

## 저장 용량의 가능성

실제 artifact의 page packer를 메모리에서 호출했다. `_put`은 길이/해시를 검사하는
메모리 sink이며 파일·HEAD·서명을 발행하지 않았다. metadata의 header hash는 길이용 자리 값이다.
이는 실제 게시/reader 검증이나 물리 delta QC 수용이 아니다.

| 형식 | 관측 | 기존 한도 |
| --- | ---: | ---: |
| sample/event delta | 954,171bytes | 8,388,608bytes |
| 단일 최대 page | 921,583bytes | 2,097,152bytes |
| page 수 | 2 | 16 |
| metadata | 4,779bytes | 131,072bytes |

각 page의128행 한도도 지켰다. 이 한 구간의 결과를 다른 출력/사건 밀도의 안전성으로 일반화하지 않는다.
현재 artifact는4,096전이 budget을 실제 거부했다. artifact/서버의128전이 제한을 변경하지 않았다.

## 보존과 다음 단계

원/새 각750개 입력·원29,141개 artifact의 bytes/hash/mode/identity와 고정 baseline을 보존했다.
268 source·context/cache/FD·원 pytest/감독자 시작 identity와 실제 종료·임시 경로 제거를 확인했다.
nice19·소유 계산1개로 실행했고 PG/브라우저/컨테이너는 시작하지 않았다.
RSS는 process 표본이며 WSL 전체/PSS가 아니다. 종료/정리 감사 뒤 source freeze를 해제했다.

다음은 명시 판본으로 큰 계산 구간을 artifact/서버에 연결하는 작은 구현이다.
원량·수지/최종 QC, 출력이 조밀할 때의 bytes/page/메모리 거부, 현재 권리/입력·HEAD 경계,
수치 hold·별도 프로세스 재개·실제 SCRAM 저장/조회와 원 판본 분리를 검증해야 한다.
자료 검사를 생략하거나 시간 간격·출력 격자를 바꾸는 방식으로 처리량을 맞추지 않는다.

전체166일 등록 terminal/DB/API/같은 UTC3D, 생과/자원/Decimal 경제 연결은 남아 있다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
이번 순수 관측으로 전체 실행 예산이나 최종 제품 완료 날짜를 고정하지 않는다.
