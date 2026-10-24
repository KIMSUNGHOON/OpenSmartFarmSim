# 개별 잎 탄소 재고의 공동 RHS 수용 — 2026-10-25 KST

[새 계약](../contracts/crop-leaf-carbon-stock-rhs-v1.md)의 합성 순간 계산을 수용한다.
[구현](../backend/app/crop_leaf_carbon_stock_rhs.py)은 같은 footprint의 잎별 C_i(`mg_CH2O/m2_floor`)를 기준으로
집계 C_leaf와 명시 제거율을 조립하고 [선행 배분 공동 RHS](crop-leaf-partition-climate-rhs-20261025.md)에 연결한다.
집계 leaf 탄소/제거의 중복 입력은 같은 값이어도 거부한다. 면적/SLA 역산이나 사후 재맞춤은 없다.
원 과실·기후/열/물과 나머지 미분은 보존하며 새 aggregate leaf 미분은 잎별 미분 합계의 파생 진단이다.
아직 C_i를 시간 전진하거나 새 잎/한 작기를 예측하지 않는다. 기존 사용자 화면/서비스도 변경하지 않았다.

현재 native Codex CLI context는 `2026-10-24T15:39:37.535Z`, model=`gpt-6.1-sol`, effort=`xhigh`,
원 LF SHA-256은 `1ac67681d43003d0694a05ac973a10e932092a8140d1efe04366c3e9fab7b0a3`다. 재귀 CLI0이다.
부모가 현재 source/단위/호흡식을 직접 대조해 상태와 정책을 판단했다. 별도 독립 검토자/관문 승인은 없다.

기존 [원 `_non_optical`](../backend/app/crop_explicit_lai_carbon_cohorts.py)의 leaf 유지호흡은
같은 T24/고정 profile에서 C_leaf에 선형이다. 이번 **명시 연구 가정**은 그 공통 질량당 비용을 각 잎에 적용해
원 M을 `M_i=M·C_i/(정확 ΣC_i)`로 배분하는 것이다. 나이별 실제 호흡의 검증 결과가 아니다.
원 profile 계수만 쓰며 새 계수·외부 원문/측정/자료 채택0이다.
[기존 근거·권리 조사](leaf-carbon-sink-primary-sources-20261024.md)를 재사용하고 저자 VTC 코드/CSV의 권리 보류도 유지한다.

각 잎의 제거율 R_i는 명시 입력이다. `C_i′=g_i−M_i−R_i`에서 C_i=0이고 최종 미분<0이면 보류한다.
유입과 유출이 정확히 균형인0재고의 연속 flow-through를 허용하며, 음수를0으로 자르거나 임의 dt로 제거율을 제한하지 않는다.
양의 재고에서 음의 순간 미분은 가능하다. 전체0재고/빈 수관·원 buffer 고갈의 기존 domain은 확대하지 않았다.
원 집계와 기관 합계의 반올림 차이를 기록하고 마지막 잎에 잔차를 몰지 않는다.

| 검증 | 실제 결과 |
|---|---|
| RED | 새 모듈 부재의 ImportError/exit2를 확인했다. |
| 신규 집중 | **101 passed**. 합성6조건×4stock 분포×3sink 패턴의 독립 잎별/전체 C 장부,0/부분0·고갈/flow-through·분모/단위/중복 집계·코드/해시/실패·512/상한/양수 호흡 유실을 확인했다. |
| 관련 회귀 | 집계 overflow 검사 추가 뒤 새101+기존 배분/공동 RHS293=**394 passed**. 전체 백엔드 시험은 실행하지 않았다. |
| 독립 프로세스 | 새 RHS72결과의 전체 SHA가 생산 프로세스와 같았다. Decimal180의864잎별 유입/호흡/제거/미분+360합계+72원 호흡식=**1,296수량**, 잎별/전체 C 수지를 대사했다. |
| 수치 | 새 잎별 계산의 연산 규모 기준 최대 차이0ULP. 기존 집계 호흡식의 독립 고정밀 상대차 최대1.508512984651177e-16, 전체 C 잔차/계산 예산 최대0.0003015924079137848. 생물학적 오차/정확도가 아니다. |
| 단일 계산/보존 | fresh의 stage/joint/carbon/optical/exchange/area/partition 각각72회(평가당1회). 원 상태/과실·기후/나머지 미분·입력 bytes와 원 hash 보존. 옛 SLA 전체 생장 호출·DB·CLI/network/쓰기0, FD4→4. |
| WSL/자료 | 성공 집중/회귀/fresh 종료0·원 소스/감시4,500항목·현재4root 보존·소유 잔여0. PID 최대74,690,560bytes/소유+보호 합계 최대420,081,664bytes. 기존512MiB/PID·1GiB 상한 유지, Windows 전체 자원 측정은 아니다. |

[증거 JSON](artifacts/crop-leaf-carbon-stock-rhs-20261025.json)에 phase/명령·native context·소스/입력 hash를,
[CSV](artifacts/crop-leaf-carbon-stock-rhs-20261025.csv)에72조건을 고정했다.
이는 자체 합성 **순간 계산**72조건이며 실제 식물/작기·농장 관측이 아니다.
512검사도 선언한 소프트웨어 용량 경계이며 실제512잎 수관의 검증이 아니다.

자체 검토에서 단일 재고 권위·명시 분모/ID·선형 호흡의 새 조건부 해석과 원 고정 계수,
소스 hash/입력 결속·닫힌/유계 입력·0재고 미분/독립 장부를 확인했다.
새 모듈 외 기존 모델/프로필/잠금·웹/DB/제품 CLI는 변경하지 않아 웹 build/브라우저·DB/실제 CLI를 다시 실행하지 않았다.
현재 A′는 C 공급을 읽지 않는다. 개별0C를 실제 양의 잎 면적/새 조직의 물성 증거로 제시하지 않는다.
기존 새 제거3D의 무모사 표시 창/R2 보류는 [해당 기록](growing-geometry-removal-3d-20261024.md)을 유지한다.

다음은 독립 상태에서 aggregate leaf slot을 제외하고 실제 C_i를 같은 a/A·기후 stage에서 적분하는 새 짧은 구간이다.
원 초기 C_i/ID/floor·현재 A를 보존하고 독립 RK4/잎별·전체 장부·고갈/실패 prefix·분할 재개를 먼저 검증한다.
조달된 새 잎/열용량·불변 저장/같은 상태3D, 실제 품종/한 작기·생산/자원/Decimal 경제·거시/수급/자율 비교,
farm/제품 CLI·독립 국내 측정/미사용 작기0·첫 품종 미확정·R2/G0–G4와 전체 goal/완료일은 미완료·미정이다.
