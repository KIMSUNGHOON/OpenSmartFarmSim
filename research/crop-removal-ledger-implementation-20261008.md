# 저장된 과실 C/N 제거 원장 구현 수용

2026-10-08 19:42 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·판단했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-removal-ledger-implementation-reference-20261008.json)은
원 명령·코드/입력/출력 hash·실제 종료·원량 대사·현재 권리·정리를 연결한다.
선행 [합성166일 DB/API/대표3D](crop-cycle-calculation-full166-same-db-completed-20261008.md)는 그대로 유지한다.

## 구현과 사용자 산출물

[원장 모듈](../backend/app/crop_harvest.py)의 `iter_removal_ledger`는 기존 검증된 저장 조회를 읽는다.
인접 표본의 terminal 누적 C/N 차이와 관리 사건의50개 과실 제거 C/N 합계를 다른 행으로 만든다.
잎·줄기/뿌리는 과실 합계에 들어가지 않는다. 원 단위는 `mg_CH2O/m2_floor`와
`fruits_equivalent/m2_floor`다. 생과 kg·실제 열매 개수·수확/판매량으로 해석하지 않는다.

행마다 원 result/payload/input/artifact/math manifest와 adapter/code/dependency 판본,
표본 쌍 또는 사건 위치/원 행 hash를 결속한다. 표본64개·사건8개 이하의 페이지를 읽고,
각 기존 조회가 현재 권리·원본을 검사한 뒤 연결을 닫는다. 원 solver·artifact·공개 응답은 바꾸지 않았다.
새 HTTP·DB 표·Run이나 사용자 화면을 추가한 단계는 아니다.

선택한 전역 표본 `[a,b]`를 나누어 읽어도 경계 사건은 한 번이며 행 ID와 원량이 같다.
초기 사건은 `a=0`에만 포함하고 같은 시각의 terminal 뒤 관리 사건을 둔다.
원 상태가 `hold`이면 확인된 과거 범위만 읽고 원 상태를 보존한다.
불완전 미래·음수/비유한·단위 오류·역순/누락/혼합 페이지는 거부한다.
늦은 권리 철회로 중단된 iterator는 완결된 원장이나 승인 Run이 아니다.

사용자는 공개 영수증의 `derived_software_test_rows`에서 소유 합성 예제의6개 파생 행과
원 위치/UTC·단위·hash를 확인할 수 있다. 실제 농장 생산량·예측 근거는 아니다.

## 검증 근거

| 대상 | 통과한 범위 |
| --- | --- |
| 순수 시험 | [시험 파일](../backend/tests/test_crop_harvest.py)의61개·원 종료0·0.95초. 독립 C/N 합계, 잎/줄기 제외,50개 벡터 보존, 초기/끝/구간/페이지·행 ID, 잘못된 값/혼합/누락·늦은 철회 |
| 실제 저장 | PostgreSQL16.15/TCP SCRAM의 등록 농장·서버 계산·불변 결과·증명·현재 조회를 사용한1개·원 종료0·pytest87.51초 |
| 비어 있지 않은 사건 | 원3표본/4사건 → terminal2행/관리4행. 시작·표본 경계·표본 사이·끝 사건을 실제 저장 조회와 대사 |
| 독립 원량 | 초기 혼합 제거의 과실 C4·N약0.02, 잎5/줄기3만 제거한 사건의 과실 C/N0. 원50개 벡터·누적 차이·UTC·행 hash/ID를 별도 root 감사에서 재확인 |
| 나누어 읽기 | 전체·두 구간·한 행씩 페이지 조회의 행/순서/ID/원량 일치. 경계 사건 중복 없음 |
| 현재 권리 | 권리 철회·읽기 scope 제거·실제 다른 계정 문맥·페이지 읽기 뒤 철회 거부/복원 |
| 재계산/보존 | 원 parser/context/advance/RHS·새 증명 발급 금지. 조회 RHS0·FD13→13·DB 행 수/입력·custody SHA/mode/inode 보존 |
| 원본/정리 | 보호 source402개 보존·원 종료 영수증 대조·DB schema/role/passfile0·소유 PG/controller/임시 경로 종료를 root에서 확인 |

실제 실행의 준비부터 정리까지88.117초였고 원600초 마감을 유지했다.
0.1초 간격823개 표본에서 주 프로세스 RSS 최대123,953,152bytes≤512MiB,
PG/controller를 포함한 소유 PID RSS 합 최대264,855,552bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS·WSL 전체·일반 운영 부하의 보장은 아니다.

첫 실제 시험도 원 종료0이었으나 사건0건이었다. 그 원 영수증·402개 원본/정리 감사와
시험 당시 세 파일을 보존하고 **표본 차이/현재 권리의 부분 증거**로만 기록했다.
관리 사건을 넣는 과정의 동적 fixture 의존성이 pytest의 `original_login_scope`를 가려
collection 종료2가 있었고, 명시적 fixture 의존성으로 고친 뒤 위61개와 실제 시험을 통과했다.
실패와 첫 부분 증거를 덮어쓰지 않았으며 전체166일 계산은 반복하지 않았다.

## 수용 범위와 다음 단계

[계약](../contracts/crop-harvest-v1.md#첫-구현-한-단계의-수용-기준)의 여섯 기준을 위 근거와 대조하고
`crop-removal-ledger`만 체크한다. 질량 환산·수확 의미 연결과 `crop-harvest-conversion` 부모는 미완료다.
실제 품종 채택 입력·국내 독립 자료·실측 농장 작물 Run은0건, G0–G4는 `not_assessed`다.

다음은 같은 세 core파일에서 명시 eta/DMC·구간/모집단·면적 분모에 따른 질량 환산이다.
소유 합성 계수로 차원·독립 Decimal/Fraction 역환산·구간 합산·결측/수치 hold를 검증할 수 있다.
실제 환산의 게시에는 해당 품종/구간의 계수·단위·권리·당시 판본·모집단/분모 근거가 별도로 필요하다.
근거 없는 기본 DMC·과중·등급 비율은 넣지 않는다. 이어 수확/적과/폐기 대응과 자원·경제 연결을 진행한다.

이번 단계는10월8일19:42 KST에 로컬 수용했다. 후속 코드 개발은 착수 가능하지만,
실제 자료 확보일이 정해지지 않아 생산 예측·추천 또는 전체 production 완료일은 확정하지 않는다.
전체 Backend/web suite·새 API/브라우저·hosted CI는 이번에 실행하지 않았다.
마지막 원격 Backend 실패/push hold와 구형 native25시간의 원 종료 기록 누락 hold는 유지한다.
