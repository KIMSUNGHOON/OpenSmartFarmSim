# 원 수치를 보존하는 제한된 계산 묶음 구현

2026-10-08 KST. [개발 계약](../contracts/crop-cycle-calculation-bounded-chunks-v1.md)을
**고유177개·실제 종료0·정리로 로컬 소프트웨어 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-bounded-chunks-reference-20261008.json)의 SHA는
`d294aed1c22c7e4df2141b9e566fe63e760d55aab06f9e6b82d3cd7a53f6cf7b`다.
기존 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했으며 재귀 CLI는0회다.

## 구현한 정책

실제 writer가4,096전이 요청을 거부하는 것을1실패/14미선택·종료1로 먼저 확인했다.
artifact의 요청 상한을4,096으로 바꾸고 **RHS 전에 원 경계를 최대128개 처리하는 실효 budget**을 계산한다.
현재 checkpoint 이후128번째 경계 또는 마지막 경계의 `steps + index + 1`을 사용한다.
경계 하나당 출력/사건이 각각 최대 한 개이므로 종류별128행 이내다.
forcing만 있는 경계도 세기 때문에 출력이 드문 입력에서도 이 추가 제한이 적용될 수 있다.
원 격자와 모든 출력/사건은 그대로이며 남은 항목은 다음 호출에서 처리한다.

요청 dict를 바꾸지 않고 실제 실효 budget을 commit에 보존한다.
독립 delta validator도 경계 제한과 종류별 행 수를 검사한다.
기존2MiB page/8MiB delta·128행/page·16page/commit·128KiB metadata와
파일/디렉터리/commit 한도는 같다. 물리 형식과 공개 필드도 같다.
새 artifact code SHA를 header에 결속하고 서버/intent/HEAD 및 HMAC domain은 명시v3로 구분했다.
v1/v2 이력이나 입력을 새 코드로 재발급·변환하지 않는다.

제품 소스 변경은 artifact와 서버 custody 두 모듈이다.
생장 수식·입력·계산 문맥·prefix validator·저장/API/SDK 소스는 보존했다.
새 집중 시험과 수동 실제 저장 관측을 추가했고 기존 잘못된 budget 반례의 상한을4,097로 바꿨다.
선행 가능성 시험의128전이 거부는 당시 고정 코드의 역사적 증거다.
현재 판본의 실제 저장/복원은 새 `crop_cycle_bounded_chunks_smoke.py`로 검증했고
과거 관측 코드·영수증을 현재 허용 상태로 덮어쓰지 않았다.

## 실제 저장과 별도 Python 재개

고정된 전체 합성 입력의 첫4,096전이를 실제 artifact 파일/HEAD로 저장했다.
비교 대상은 앞선 최종 권한 경계 판본의128전이32호출이다.

| 항목 | 실제 결과 |
| --- | ---: |
| 전이 / 적분 걸음 / commit | 4,096 / 3,990 / 1 |
| 확정 출력 / 관리 사건 | 105 / 2 |
| 실제 page 수 / 최대 page bytes | 2 / 921,583 |
| context 열기·실제 생성/저장 advance | 42.466초 |
| 원 명령, 전체 대사·자식 포함 | 63.181초 / 종료0 |
| FD 전후 | 12→12 |

`parent_sha256`/`checkpoint_sha256` 두 계보 필드 외의 checkpoint 전체가 기존32회와 같다.
121상태·seed·clock/cursor·누적·출력/사건 prefix를 포함한다.
원 전체 순수 결과의 해당105행/2사건과도 명시한 +273일 달력 이동 뒤 정확히 같다.
원 checkpoint는 기존6 provenance 필드를 구분해 대사했다.

별도 Python은 저장 checkpoint/현재 bytes를 RHS0으로 복원한 뒤 실제 한 전이를 더 처리했다.
복원 checkpoint SHA와 추가 전이 뒤 checkpoint 전체가 부모의 독립 계산과 같다.
sequence4,096→4,097에서 추가 전이는 경계 처리였고 RHS1회다. 적분 걸음 하나 증가로 표시하지 않는다.
두 프로세스의 FD/cache·임시 경로/실제 종료를 확인했다.

이 관측은 실제 파일에 저장한 **yielded prefix**다. terminal artifact·등록 농장/DB 게시·HTTPS/3D가 아니다.
42.466초를 기존 등록 서버32호출과 직접 비교한 속도 개선율이나 전체 작기 완료 시간으로 외삽하지 않는다.

## 검증과 최종 감사

| 명령 범위 | 통과 | 실제 wall / 종료 |
| --- | ---: | --- |
| 새 정책:6프로그램·조밀 출력/사건·분할·과대 결과/이전 domain 거부 | 20 | 145.981초 / 0 |
| 기존 artifact·signed custody·prefix·입력 재검사 | 155 | 150.685초 / 0 |
| 실제4,096 저장·원량/별도 Python 재개 | 1 | 63.181초 / 0 |
| 현재 공개 summary/page 투영 | 1 | 2.549초 / 0 |
| 기존 잘못된 budget: 소스 고정 보강 재검사 | 4, 중복 | 1.538초 / 0 |

고유177개, 실행된 통과 항목181개다. 마지막4개는155개에 포함되므로 다시 더하지 않는다.
기존 회귀는 수치 hold/빈 과거·현재 bytes 변조·권리 철회·늦은 철회·HEAD 전후 중단/복원을 포함한다.
새 정책은 초기·step-end 경계 대기·경계 처리 뒤의 조밀한181출력/181사건을 빠짐없이 대사한다.
현재 공개 투영은 작은 정상 사례 하나이며 전체 API/새 TLS/WebGL 수용은 아니다.

첫 최종 감사는 이전 source 목록에 변경한 기존 budget 시험 파일이 있다고 잘못 가정해 종료1이었다.
해당 파일의 pin 누락을 확인하고 현재 소스를 고정해 관련4개 시험을 다시 실행했다.
첫 감사 원본/종료1과 보강 명령을 보존했고 최종 감사는274 source·각 실제 로그 SHA/종료·
원 PID/감독자/자식 종료·임시 tree·passfile/PG 잔재 없음으로 종료0이었다.
이 감사 뒤 source freeze를 해제했다. nice19·소유 무거운 작업 하나씩 실행했고 PG/브라우저/컨테이너는 시작하지 않았다.
원/새 각750개 입력·원29,141개 artifact의 bytes/hash/mode/identity도 보존했다.

## 다음 단계와 유지하는 hold

다음은 실제 등록 농장/SCRAM에서 큰 묶음 두 번과 별도 재개·현재 입력/권리 철회·비용을 관측하는 단계다.
그 증거로 현재 전체 bytes/HMAC 순회 비용과 실행 예산을 정한 뒤 전체166일 저장/API/같은 UTC3D로 진행한다.
현재 HTTP30초·worker lease/cancel·CI 설정은 바꾸지 않았다.
전체 Backend·새 PG/SCRAM 큰 묶음·새 TLS/WebGL·전체166일 등록 terminal 경로는 실행하지 않았다.
최신 native의 원 명령 종료 기록 누락 hold와 원격 Backend CI 실패도 별도다.

생과 수확·물/양분·구매 에너지·작물 결과와 Decimal 손익 연결, 실제 제품 CLI/독립 G1은 후속이다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
