# 합성 수확·적과·폐기·채취 배정의 개발 수용

2026-10-08 20:31 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·검토했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-harvest-events-implementation-reference-20261008.json)에
원 명령·실제 종료·입출력/코드 hash·독립 Decimal 대사·현재 권리와 정리를 연결했다.
선행 [원장](crop-removal-ledger-implementation-20261008.md)과
[명시 질량 환산](crop-removal-mass-implementation-20261008.md)의 소프트웨어 범위를 보존한다.

## 사용자 산출물과 구현 범위

[배정 모듈](../backend/app/crop_harvest.py)의 `iter_harvest_allocations`는 검증된 현재 조회와
명시 합성 질량/배정 원문을 읽어 원 제거마다 수확·적과·폐기·채취와 미배정량을 반환한다.
원 C/N·건물/생과·UTC·원 위치/hash·계수/배정 판본을 보존한다. terminal 제거를 기본 수확으로
간주하지 않으며 없는 실제 수확일·등급·판매량을 생성하지 않는다.

규칙은 동일 source/artifact·모집단·바닥 면적과 질량 계수 hash에 결속한다.
원 terminal 구간 범위 또는 관리 사건 index를 참조하므로 전체 작기를 행마다 입력할 필요가 없다.
확정된 원 개수를 넘는 참조는 빈 선택 창에서도 거부한다. 최대256규칙·64관측 fixture·262,144bytes다.
규칙/관측은 현재 `synthetic`/`assumed`만 허용하며 실제 자료 채택 경로는 아니다.

소수 문자열 비율을 정확한 유리수로 계산하고 각 원 구간의 배정 합이1을 넘으면 거부한다.
C/N/건물/생과 네 양의 배정과 잔여 합은 원 float64 값과 정확히 같다.
출력에 분자/분모와 반올림된 float64를 함께 남기고 양수 underflow/overflow는 보류한다.
선택적 크기·등급 분류 없이 전체 모델 과실 구획에 같은 비율을 적용한다.

`summarize_harvest_allocations`는 원 종류×목적별 합계·미배정량과 행 순서 hash를 만든다.
관측 fixture는 연결된 수확 배정의 모델 생과량과 비교하고 `관측−모델` 차이를 보존한다.
관측값을 모델 합계에 더하지 않는다. 일부 구간만 선택하면 `incomplete_selected_window`로 남기며
관측을 임의로 나누지 않는다. 완전한 비교에는 원 구간과 관측 기간의 대응을 검사한다.

사용자는 공개 영수증의 합성 배정6규칙·원6행/배정6묶음·목적별 합계·관측 비교1건을 확인할 수 있다.
이는 Python 연구 인터페이스의 산출물이다. 새 저장 표·HTTP·3D나 실제 농장 작물 Run은 생성하지 않았다.

## 통과한 검증과 실행 실패 기록

| 대상 | 확인한 범위 |
| --- | --- |
| 최종 집중 시험 | [시험 파일](../backend/tests/test_crop_harvest.py)의148개·원 종료0·1.09초. 기존 원장61/질량44와 배정43개이며 중간 실행은 중복 합산하지 않음 |
| 독립 산술 | 2200자리 Decimal로 네 양의 배정/미배정·종류×목적 합계·관측 차이를 별도 재계산. source·원 위치·행 ID/hash도 root에서 대사 |
| 구간/오류 | 전체/분할/한 행 페이지 동일·초기/끝·미래 참조/빈 창·배정 초과·중복 ID/관측 연결·잘못된 기간/단위/면적·실제 자료 표시 거부 |
| 실제 DB | PostgreSQL16.15/TCP SCRAM의 등록 농장/불변 결과/현재 조회1개·원 종료0·pytest258.74초. 원3표본/4사건 →6원장/6질량/6배정 묶음 |
| 의미 있는 배정 | 네 목적에 모두 양수 생과량·원 미배정 양수·잎/줄기만 제거한 과실0·관측 차이 비영. 단순 빈 사건 시험이 아님 |
| 권리/보존 | 현재 권리·읽기 scope·다른 계정·페이지 뒤 철회 거부. 조회 RHS0·새 증명0·FD13→13·원 파일 SHA/mode/inode·DB 행 수 보존 |
| 자원/정리 | 406 source 보존·DB schema/role/passfile0·소유 PG/controller/임시 경로 정리. 20:31 KST root 감사 후 시험 당시 세 파일 보존/source freeze 해제 |

수용한 v2는20:26:52→20:31:11 KST, 준비부터 정리까지259.317초다. 원600초 상한을 유지했다.
0.1초 간격2437개 표본에서 primary RSS 최대125,792,256bytes≤512MiB,
PG/controller 포함 소유 PID RSS 합 최대266,031,104bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS·WSL 전체·production 동시 부하의 수용은 아니다.

첫 v1은 `/usr/bin/nice`의 exec 전환 직전에 우선순위를 검사한 실행기 race로 원 driver가 종료1이었다.
실제 시험 PID/시작 tick·로그 FD를 확인한 뒤 같은 프로세스에 SIGINT를 보냈다.
원 pytest 종료 코드는 확인할 수 없어 미수용으로 보존했다. 원 마감 내 PG·역할·비밀/임시 경로·source 정리를
확인한 뒤 실행 전에 nice19를 설정하도록 수정한 v2를 별도 실행했다. v2의 종료0을 v1에 소급하지 않는다.

## 남은 의존성과 다음 한 단계

[계약](../contracts/crop-harvest-v1.md#수확-배정-개발-인터페이스와-다음-수용-기준)의
`crop-harvest-events` 개발 자식만 체크한다. 실제 품종 입력/환산 계수·국내 독립 자료·실측 농장 작물 Run은0건,
G0–G4는 `not_assessed`이며 부모 생산량·미래 마진·추천 보류는 유지한다.

다음은 [작업 목록](../tasks/todo.md)의 `crop-harvest-replay`다.
불변 파생 저장/현재 권리 조회 → HTTP/SDK → 같은 UTC 표/3D로 작은 자식을 나누며
첫 단계는 같은 원 결과·질량/배정 판본·단위·미배정/hold를 보존하는 저장과 별도 Python 복원이다.
합성 개발은 실제 계수 확보나 기후/자원 모델 완료를 기다리지 않는다. 실제 생산량 게시에는 별도 근거가 필요하다.
기후·물/양분·구매 에너지와 기존 Decimal 경제 계산 연결은 후속이다.

전체166일 질량/배정 저장·API/3D·전체 Backend/web suite·hosted CI·실제 품종 검증은 실행하지 않았다.
원 전체166일 계산도 반복하지 않았다. 마지막 원격 Backend 실패/push hold와 구형 native25시간
원 종료 기록 누락 hold는 유지한다. 이 개발 자식은10월8일20:31 KST에 수용했으며,
실제 품종·현장 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
