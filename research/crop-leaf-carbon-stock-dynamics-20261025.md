# 개별 탄소·면적·기후의 짧은 공동 적분 수용 — 2026-10-25 KST

[새 계약](../contracts/crop-leaf-carbon-stock-dynamics-v1.md)의 **고정 잎 목록 합성 시간 적분**을 수용한다.
[개별 재고 RHS](crop-leaf-carbon-stock-rhs-20261025.md)를 각 stage에서 한 번 호출해 C_i·나이·현재 A와
기관/과실/기후를 같은 RK4 가중치로 전진한다. [구현](../backend/app/crop_leaf_carbon_stock_dynamics.py)의
독립 상태는107+3n개이며 aggregate leaf slot을 제외했다. 원21장부와 각 잎의 유입/호흡/제거3n누적량을 보존한다.
기존 모델/프로필·저장 결과/화면을 바꾸지 않았다. 분할 재개·불변 저장/같은 상태3D는 후속이다.

실제 native Codex CLI context는 `2026-10-24T16:00:29.972Z`, model=`gpt-6.1-sol`, effort=`xhigh`,
원 LF SHA-256은 `1e495f93cd6f8682118ce640d74f34c2359ec07f2bbe2c4dfaa44bb475af811a`다. 재귀 CLI0이다.
부모가 기존 동적 면적/연속·재개 코드와 새 stock RHS·단위/장부를 읽어 상태·호출 경계를 판단했다.
새 농업 계수·외부 원문/자료를 채택하지 않았으며 [기존 근거/권리](leaf-carbon-sink-primary-sources-20261024.md)의 보류를 유지한다.

초기 면적의 canonical 정규화와 순수 수지/스칼라 RK4 helper를 재사용했다.
old geometry `_evaluate/integrate`나 옛 SLA 전체 생장을 호출하지 않는다.
기존 helper에 주는 aggregate는 현재 C_i 합계의 **내부 임시 projection**이며 옛 결과/hash/독립 상태로 발급하지 않는다.
이후 A를 F(age)에 재맞추지 않고 D−D0를 기록한다. 현재 A가 곡선보다1e-8m² 큰 경우도 그 실제 A가 LAI에 쓰임을 확인했다.
개별 유지호흡의 질량 비례 가정·명시 제거와 동적 실내-Ta/명시 gross-capacity 정책은 선행 계약 그대로다.
새 면적은 아직 탄소 공급을 읽지 않으므로 이 시간 적분이 공급 제한/조달된 새 잎의 검증이라는 뜻은 아니다.

| 검증 | 실제 결과 |
|---|---|
| 신규/관련 | 최종 신규 **58개**를 포함한 **289 passed**. 원6합성 프로그램×3stock/sink 조건, 모든 순간/누적 장부·순서/단위/정책·0/음수·범위/코드·해시·호출·512경계·실패 prefix와 현재 A 보존을 검사했다. 전체 백엔드 시험은 실행하지 않았다. |
| 완전히 별도인 식/ODE | [app 없는 Decimal110 생성기](crop-leaf-carbon-stock-dynamics-reference.py)의6프로그램·원 식/RK4와 [새 fixture](../fixtures/crop-leaf-carbon-stock-dynamics-reference-v1.json)를 대사했다.32초의116상태/30장부/3파생량/3곡선 진단씩 총912비교, 대표 dt8/4/2의 반분 감소 또는128ulp roundoff 바닥도 통과했다. |
| 별도 프로세스/산술 | 6개32초 궤적·102시점의 전체 결과 SHA가 생산 프로세스와 같았다. 별도의 Decimal120 RK4 **산술**에 검토된 새 RHS를 공급해11,832상태+102집계진단+180누적량=**12,114수량**을 대사했다. 이 산술 oracle은 별도 물리식 검증을 대신하지 않으며 위 Decimal110 원식 검증과 구분한다. |
| 독립 장부 | 원 상태와 독립 산술의 유량으로 전체 C/fruit number·수관/공기/증기/용량/reduced energy·각 나이/개별 C의 **1,326장부**를 Decimal120으로 다시 계산했다. 최대 상태 상대차6.430104813680078e-16, 잔차/정해진 반올림 예산 최대0.026976252704969707. 생물학적 정확도가 아니다. |
| 호출/부작용 | fresh checker의 초기 정규화6회, 제품 재실행390stage+독립 산술390stage에서 stock/stage/joint/carbon/optical/exchange/area/partition 각각780회(각 평가당1회). 옛 geometry RHS/integrate·옛 SLA 전체 생장·DB·CLI/network/쓰기 시도0, FD4→4. 순수 old `_advance/_weighted` helper 재사용은 이 금지 범위와 다르다. |
| 실패/용량 | 고갈·큰 열 trial과 주입 k3 실패에서 확정 state·누적량/잔차/예산을 보존했다.512잎의1,643상태/1,557누적량·513거부·2MiB/32,768scalar·600초/step 상한을 확인했다. 실제512잎 수관의 검증은 아니다. |
| WSL/원 자료 | 전 phase 원 소스/감시4,500항목·현재4root 보존·소유 잔여0. 성공 phase 최대 PID74,690,560bytes/소유+보호 합계445,800,448bytes. 기존512MiB/PID·1GiB 상한 유지, Windows 전체 자원 측정은 아니다. |

[공개 증거 JSON](artifacts/crop-leaf-carbon-stock-dynamics-20261025.json)과
[102시점 요약 CSV](artifacts/crop-leaf-carbon-stock-dynamics-20261025.csv)에 명령/phase·native context·원 hash를 고정했다.
초기 RED는 새 모듈 부재의 exit2다. 초기46→기준 식/경계57→현재 A 검사 추가58을 순차 수용했다.
app-free 생성기6사례/110자리·app import0·raw SHA `26c5eff5df009486dddc2f68706d23b99dadac185dca052aecfd1ad1da7fca0f`를
독립 준비 커밋 `71e5d4e`에 먼저 고정했다. 이는 자체 합성 소프트웨어 fixture이며 실제 관측/자료 승인이나 새 품종 계수가 아니다.

자체 검토에서 단일 C_i 권위·코드/profile/입력 결속, 현 시점 Ta/A·기관/전체 수지와 helper projection의 범위를 확인했다.
별도 독립 검토자/실제 자료 승인 증거는 아니다. 웹·DB·제품 CLI는 변경하지 않아 관련 build/브라우저·DB/실제 CLI를 다시 실행하지 않았다.
현재 새 제거3D의 무모사 표시 창/R2 보류도 유지한다. 이 적분은 elapsed32초이며 새 UTC/농장/관리 checkpoint로 발급하지 않는다.

다음은 불변 context/신뢰한 raw SHA로 현재 C_i/a/A/D0·누적량을 복원하고 모든 분할에서 같은 bytes가 나오는 재개 계약이다.
그 뒤 조달된 출현·불변 저장/같은 상태3D, 실제 품종/한 작기·생산/자원/Decimal 경제·거시/수급·자율 비교를 연결한다.
국내 독립 측정/미사용 작기0·첫 품종 미확정, farm/제품 CLI·R2/G0–G4·전체 goal/완료일은 미완료·미정이다.
