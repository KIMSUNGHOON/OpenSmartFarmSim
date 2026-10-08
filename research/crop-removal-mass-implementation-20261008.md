# 명시 합성 계수의 제거 질량 환산 수용

2026-10-08 20:02 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·판단했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-removal-mass-implementation-reference-20261008.json)에
원 명령·계수 입력/출력/코드 hash·실제 종료·독립 Decimal 대사·현재 권리·정리를 연결했다.
선행 [C/N 원장](crop-removal-ledger-implementation-20261008.md)의 수치와 원 artifact는 보존했다.

## 구현과 확인할 산출물

[같은 모듈](../backend/app/crop_harvest.py)의 `iter_removal_mass`는 검증된 현재 조회와 원장을 읽어
명시 eta/DMC로 `kg_DM/m2_floor`·`kg_FW/m2_floor`를 계산한다. N>0일 때만 같은 제거의
`kg_FW/fruit_equivalent`를 내며 N=0은 `null`이다. 실제 개별 과중·생산 예측을 뜻하지 않는다.
원 C/N·사건 벡터·UTC·결과/모델 hash와 계수 원문 hash/판본을 출력에 보존한다.

계수 입력은 원 result/payload/input/artifact/math manifest/상태, 모집단과 바닥 면적 분모,
근거 ID·`available_at`·구간·정책을 명시한 canonical JSON이다. 현재 개발 경로는
`origin=synthetic`·`evidence_level=assumed`만 허용한다. 실제 계수 채택·권리 검토·관문 승인을 만들지 않는다.
eta/DMC 기본값이나 Brix 대체값은 없다. 부분 구획·다른 면적·등급으로 자동 확장하지 않는다.

terminal 표본 구간은 한 계수 구간에 전부 포함되어야 한다. 중간 계수 변경의 원량 해상도가 없으면
보류하고 보간하지 않는다. 경계 순간 사건은 새 구간, 마지막 끝 사건은 마지막 구간에 배정한다.
계수 누락·잘못된 단위/분모·출처 불일치·겹침/빈 구간·실제 원천/승인 표시 입력을 거부한다.
빈 선택 창에도 원본 대응과 현재 권리를 검사한다.

입력 float64를 Fraction의 정확한 유리수로 계산하고 각 출력에서 가장 가까운 float64로 반올림한다.
중간 연산의 불필요한 overflow/underflow를 피하고, 출력의 overflow·양수→0 underflow는 보류한다.
금액 계산은 추가하지 않았다. `summarize_removal_mass`는 두 제거 종류의 합계와 행 순서 hash를
각각 보존하며, 원 행 전체를 보관하거나 두 종류를 실제 수확량으로 합치지 않는다.

사용자는 공개 영수증의 명시 합성 계수·6개 파생 행·`separate_kind_summary`를 확인할 수 있다.
시험의 eta1·DMC0.5/0.25는 소유 산술 예제이며 실제 품종 계수로 채택한 값이 아니다.
새 HTTP·저장 표·3D·농장 작물 Run은 이번에 생성하지 않았다.

## 통과한 검증

| 대상 | 실제 근거 |
| --- | --- |
| 최종 순수 시험 | [시험 파일](../backend/tests/test_crop_harvest.py)의105개·원 종료0·1.04초. 기존 원장61개와 질량44개이며 중간79/101/105개를 중복 합산하지 않음 |
| 독립 산술 | 손계산/Decimal 역환산·2200자리 Decimal과 극단값 비교·단위/분모·구간별 합산·계수 결측·수치 hold |
| 구간/원본 | 초기/끝·계수 경계·표본 사이 사건, 전체/구간/한 행 페이지 일치·완료/hold 범위·빈 창의 출처 불일치·마지막 철회 거부 |
| 실제 DB | PostgreSQL16.15/TCP SCRAM의 등록 농장/서버/불변 결과/증명/현재 조회1개·원 종료0·pytest158.94초 |
| 실제 원량/환산 | 원3표본/4사건 → 원장6행/질량6행·2계수 구간. 원 C/N·UTC·hash/ID·계수 원문을 root에서 대사하고 행별 질량/종류별 합계를 별도 Decimal로 재계산 |
| 현재 권리 | 권리 철회·읽기 scope 제거·다른 계정·페이지 뒤 철회에서 원장과 질량 요약 모두 거부/복원 |
| 원본/정리 | 조회 RHS0·새 증명0·FD13→13·DB 행 수/입력·custody SHA/mode/inode·source404개 보존·DB schema/role/passfile0·소유 PG/controller/임시 경로 종료 |

실행은19:58:55→20:01:34 KST, 준비부터 정리까지159.548초였다. 원600초 마감을 유지했다.
0.1초 간격1499개 표본에서 주 프로세스 RSS 최대124,583,936bytes≤512MiB,
PG/controller를 포함한 소유 PID RSS 합 최대264,478,720bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS·WSL 전체·일반 운영 부하를 보장하지 않는다.
20:02 KST root 감사가 통과한 뒤 시험 당시 세 파일을 불변 보존하고 source freeze를 해제했다.
원 전체166일 계산은 반복하지 않았다.

## 남은 의존성과 다음 단계

[환산 계약](../contracts/crop-harvest-v1.md#명시-계수의-질량-환산)의 개발 수용만 확인해
`crop-removal-mass` 자식을 체크한다. 실제 계수·생과 수확·`crop-harvest-events`와 부모는 미수용이다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run은0건, G0–G4는 `not_assessed`다.

다음은 같은 세 core파일에서 수확/적과/폐기/채취의 명시 배정과 미배정량 보존,
같은 원 제거의 이중 배정 금지·실측/모델 분리·모집단/날짜/면적 대사다.
실제 H/P/S·등급·판매·경제 연결에는 각 근거가 별도로 필요하다.
전체 작기의 질량 저장/API/3D는 [작업 목록](../tasks/todo.md)의 `crop-harvest-replay`로 명시했고,
배정 개발 뒤 기후/자원 모델 개발과 병행한다. 자원/경제 연결도 후속이며 이번 작은 DB 시험으로 수용하지 않는다.
전체166일 질량 경로·전체 Backend/web suite·새 API/브라우저·hosted CI·실제 품종 검증은 실행하지 않았다.
마지막 원격 Backend 실패/push hold와 구형 native25시간 원 종료 기록 누락 hold는 유지한다.

질량 개발 자식은10월8일20:02 KST에 로컬 수용했다. 실제 계수·현장 자료의 확보일이
정해지지 않아 실제 생산 예측·추천과 전체 production 완료일은 확정하지 않는다.
