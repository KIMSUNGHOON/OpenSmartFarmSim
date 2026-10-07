# 서버 입력 재검사 중복 비용 개선

2026-10-08 KST. [실행 전 계약](../contracts/crop-cycle-calculation-recheck-cost-v1.md)을
고유199개 집중 검증의 분할 실행과 같은 전체 입력의 첫3회 계산으로 로컬 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-recheck-cost-reference-20261008.json)에 실제 명령·종료·로그,
source/호출자·비용·원량/권리·정리 증거를 결속했다.
native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는0회다.

## 변경과 검증

`_Journal._guard`의 첫 전체 입력 검사를 정확한 열린 문맥·코드/프로필·입력 FD 검사로 바꿨다.
현재 정책 callback과 반환 binding 비교 뒤의 전체 파일 검증은 유지한다.
callback이 입력을 검사하지 않는 순수 journal 반례에서도 전체 bytes를 확인한다.
실제 농장 binding의 입력 전후 검사2회·현재 권리/등록 검사는 그대로다.
입력/권리/행 결과 cache는 없다.

제품 변경은 서버 module의 한 함수·2줄 추가/1줄 제거다.
다른34개 함수의 AST와 context/입력 증명/farm/artifact source bytes는 HEAD 기준과 같다.
생장 수식·solver·서명/게시 순서와 기존 public 계산/복원·HEAD 직전 검사를 유지했다.
새 custody source SHA는 새 이력 provenance에 기록하며 이전 이력을 재분류하지 않는다.

원 구현의 실제 호출자 추적은 `verify → recheck → _secure_input → _guard`2회였고,
한 번을 요구한 RED는1실패/0.89초·원 명령 종료1이다.
수정 후 current callback1회·전체 bytes 검사1회를 확인했다.
root/참조 block의 같은 크기·복원한 mtime 변조를 진입 전과 callback 중에 모두 거부했다.
닫힌 문맥/바뀐 code는 정책 callback 전에 거부하고, 권리 거부·proof 기록 전후 변조는
이전 HEAD를 유지했다. 조회 중 늦은 변조도 정상 반환을 막았다.

| 실제 명령 범위 | 통과 | pytest 관측 시간 | 원 명령 종료 |
| --- | ---: | ---: | ---: |
| 새 guard/변조 반례 | 11 | 3.87초 | 0 |
| 기존 context/artifact/server | 175 | 199.62초 | 0 |
| 실제 SCRAM 농장/server | 12 | 232.25초 | 0 |
| 같은 전체 입력의 초기3회 | 1 | 74.43초 | 0 |

네 명령의 고유199개이며 전체 Backend/브라우저 검증 수가 아니다.
기존 fresh Python 복원·실제 중단/선택 HEAD 복원과 현재 권리 철회 회귀도 포함한다.
성공 단계의 원 source 목록을 전체 app module까지 확장해262개 SHA를 보존했다.
RED의 원 목록은137개이며 서버 source는 명령의 별도 source map에도 결속했다.
목록 확장 전 준비 스크립트의 assertion 실패는 child를 시작하지 않았고 별도 기록했다.

## 같은 전체 입력의 실제 비용

앞선 후보 연결 개선과 같은 별도 달력 root/증명·8초 RK4·300초 출력·128전이·첫3회를 썼다.
계측기 source와 비용 정의를 바꾸지 않았다. 아래 시간은 advance만의 비교이며
준비·원 결과 조회·별도 checkpoint 진단을 포함한 명령 전체 시간과 구분한다.

| commit | 걸음 | 시점/사건 | 이전 advance(초) | 수정 advance(초) | 전체 입력 검사 이전→수정 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 123 | 4/2 | 12.609 | 12.119 | 39→33 |
| 2 | 248 | 7/2 | 9.076 | 8.695 | 30→26 |
| 3 | 373 | 10/2 | 9.052 | 8.736 | 30→26 |

합30.737→29.551초, 전체 입력 검증99→85회/9.455→8.361초다.
현재 farm callback17회·prepare1회·farm input36회·등록 조회36회·시장 검증36회·
경제 검증/계산36회·RHS1,876회와 prefix 검사5회를 보존했다.
중첩 비용을 합산하지 않으며 이 표본을 전체 작기 지연 보장으로 사용하지 않는다.

앞선 같은 등록 계산과 **체크포인트 전체 및 context SHA가 동일**하다.
원 순수 결과와의 별도 대사는 명시한+273일 변환·판본/해시6필드 제외 뒤121상태/seed/clock/cursor와
모든 확정 행이 같다. 저장 files/bytes·새 서비스 복원·조회 RHS0·FD12→12,
현재 권리/계정 철회·미완료 게시 거부를 확인했다.
원750/새750 입력·원29,141 결과 파일과 DB 행을 보존했다.

실제 SCRAM/서버 HBA·schema/role/passfile0과 PG/data/temp/소유 process 정리를 확인했다.
농장 회귀의 schema/role0은 실행된 fixture assertion 증거이며 해당 JSON recorder는 활성화하지 않았다.
전체 입력 실행은 별도 cleanup JSON도 남겼다. 모든 실제 명령 종료와 감독자/자식 종료를 대사했고
현재 소유 실험은0개다. nice19의 순차 실행이며 측정 RSS는 WSL 전체 사용량이 아니다.

## 다음 단계와 보류

다음은 개선 판본의 증가 prefix 비용과 전체 등록 실행 예산을 고정하는 단계다.
초기3회에서 전체166일 완료 시간이나 제품 완료일을 외삽하지 않는다.
남은 누적 비용의 근거 없이 장시간 등록 계산을 시작하거나 prefix-cost 부모를 체크하지 않는다.
전체166일 terminal/DB/API/같은 UTC3D, 생과 kg·물/양분·구매 에너지·Decimal 손익 연결은 후속이다.

`2a3e615`의 CI는 다른4workflow 성공, Backend 분할0 실패·1/2 진행·3/4/5 대기다.
현재 source의 hosted/전체 Backend·새 브라우저 회귀는 실행하지 않았으며 기존 CI 종료 전 push를 보류했다.
최신 native 화면의 원 명령 종료 기록 누락 hold도 유지한다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건과 G0–G4 `not_assessed`, 예측/추천 게시 hold를 유지한다.
