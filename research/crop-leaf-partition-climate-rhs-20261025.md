# 잎 탄소 배분과 같은 stage 공동 RHS 수용 — 2026-10-25 KST

[새 계약](../contracts/crop-leaf-partition-climate-rhs-v1.md)의 합성 순간 계산을 수용한다.
[이전 배분 산술](leaf-carbon-partition-20261024.md)의 조정량을 실제 원 공동 RHS의 buffer/leaf 미분과
전체 생장호흡에 한 번씩 결속했다. [구현](../backend/app/crop_leaf_partition_climate_rhs.py)과
[검사](../backend/tests/test_crop_leaf_partition_climate_rhs.py)는 새 별도 경로다.
기존 모델·프로필/저장 결과·사용자 화면·서비스는 변경하지 않았다.
개별 C 재고/시간 적분·새 잎·공급 제한/면적 feedback과 생산 예측은 이 단계의 결과가 아니다.

현재 native Codex CLI의 실제 context는 `2026-10-24T15:19:13.452Z`,
model=`gpt-6.1-sol`, effort=`xhigh`, 원 LF SHA-256은
`a2842786b4fea1133399d4ca7571411aa8b58347ef7c0a8d3f3f91058c12bfd4`다. 재귀 CLI0이다.
부모가 현재 원 탄소/공동 RHS·동적 a/A 조립과 원 배분 산술을 직접 대조했다.
이 판단은 [원문·권리/의존성 조사](leaf-carbon-sink-primary-sources-20261024.md)를 재사용한 모듈 결합 판단이며,
새 외부 원문·계수/농장 자료나 독립 관문 승인을 채택한 것이 아니다.

같은 stage의 원 공동 RHS가 요청한 G와 고정 cLeafG를 배분기에 전달한다.
명시 상대 sink가 전부0이면 미사용 D=G, 아니면 D=0이다.
원 buffer′에 D+cD, leaf′에−D, 전체 생장호흡에−cD를 반영하고 실제 leaf allocation을 G−D로 반환한다.
원 P·50과실 C/fruit number N·기후/열/증기·나머지 미분은 원 source에 그대로 남긴다.
완전한 원 source와 원 배분 결과/hash를 따로 보존하고 새 조정 결과에 새 calculation SHA를 만든다.
선언된 현재 ID 순서와 sink를 일대일로 결속하지만 저장 문맥/농장 provenance의 검증은 후속이다.

| 실제 검증 | 결과 |
|---|---|
| 신규 집중 | **79 passed**. 원 합성6프로그램×7weight 패턴의 독립 Decimal180 조정량/전체 C·leaf 수지, 원 출력/입력·해시/ID/순서·512/byte 상한·profile/수치/코드/단계 실패를 확인했다. |
| 관련 회귀 | 신규79+기존 배분/명시 C/명시 공동 RHS214=**293 passed**. 전체 백엔드 시험은 실행하지 않았다. |
| 독립 프로세스 | 실제 새 RHS42평가의 전체 결과 SHA가 생산 프로세스와 일치했다. 독립126잎 유입량과210개 조정된 미분/비용·실현/미사용 예산=**336수량**, 전체 C·leaf 수지를 대사했다. 이는 합성 순간42조건이며42작기/현장 측정이 아니다. |
| 중복/보존 | fresh에서 원 joint/carbon/optical/exchange/area/partition 각각42회(평가당1회), 원6상태/원 결과·과실/기후 보존. 옛 SLA 전체 생장 호출·DB·CLI/network/쓰기0, FD4→4. |
| 수치 | 독립 조정량의 연산 규모 기준 최대0.5ULP, 전체 C 잔차/계산 예산 최대0.001555538485174374. 생물학적 정확도나 측정 오차가 아니다. |
| WSL/자료 | 성공 집중/회귀/fresh 종료0, 원 소스/감시4,500항목·현재4root 보존·소유 잔여0. 최대 PID74,690,560bytes/합계443,265,024bytes. 512MiB/PID·1GiB 합계 상한 유지; Windows 전체 자원은 측정하지 않았다. |

첫 RED는 새 모듈 부재로 exit2였다. 첫70개 검사에서는 고갈 시험 입력이 과실 유입 예산에서 먼저 거부되어
69pass/1fail이었다. 명시 유입을0으로 한 입력으로 고갈 조건을 직접 검사해70pass를 확인했다.
검토 중 배분 결과 hash의 반환 검사가 빠진 점을 새 회귀로 확인하고 보완한 뒤 최종79/293을 통과했다.
초기 실패 기록을 [증거 JSON](artifacts/crop-leaf-partition-climate-rhs-20261025.json)에 보존했다.
42조건 요약은 [CSV](artifacts/crop-leaf-partition-climate-rhs-20261025.csv)다.

원 RHS의 domain/hold를 그대로 따른다. 고정 profile/원 domain에서 leaf 요청은 양수이며
0요청 사례를 만들어 내지 않았다(0예산 산술은 선행54검사에서 검증).
원0 buffer·고갈 hold를 새 배분 후 가능 상태라고 가정해 우회하지 않는다.
긴 ID/중첩 결과는256KiB 상한에서 hold할 수 있다. weight는 절대 수요 상한/실제 품종 계수가 아니다.
현재 A′는 C 공급을 읽지 않으므로 sink0을 면적 확장0으로 해석하지 않는다.

자체 코드 검토에서 source/partition hash와 입력 결속, 세 조정의 단일 적용, 독립 전체 장부,
닫힌/유한/유계 입력·원 코드/profile/정책 보존을 확인했다. 별도 독립 검토자나 실제 자료 승인 증거는 아니다.
웹·DB·제품 CLI는 변경하지 않아 다시 실행하지 않았다. 기존 새 제거3D의 무모사 표시 창/R2 보류는 유지한다.
다음은 권위 개별 C_i 상태/분모·ID/합계, 유지호흡 배분·고갈 정책과 순간 RHS를 먼저 정의·검증하고,
같은 stage의 짧은 적분/분할 재개→탄소/현열이 조달된 출현→불변 저장/같은 상태3D로 진행한다.
실제 품종/독립 국내 자료·미사용 작기0·생산/자원/Decimal 경제·거시/수급/자율 비교·farm/제품 CLI와
R2/G0–G4·전체 goal은 미완료이며 전체 완료일은 자료 확보 근거가 없어 미정이다.
