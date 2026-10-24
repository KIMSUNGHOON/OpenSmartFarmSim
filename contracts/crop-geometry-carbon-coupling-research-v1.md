# 기관 면적·탄소의 연속 결합 연구 경계 v1

상태: **후속 구현의 설계 계약**. [1차 근거](../research/continuous-leaf-carbon-primary-sources-20261024.md)와
[명시 LAI 광 동화](crop-explicit-lai-photosynthesis-v1.md), [C/50과실 RHS](crop-explicit-lai-carbon-cohorts-v1.md),
[면적/현열](crop-area-canopy-energy-v1.md)의
순간 부품과 [같은 stage 공동 RHS](crop-explicit-lai-climate-rhs-v1.md),
[고정 잎 목록의 짧은 연속 구간](crop-growing-geometry-climate-v1.md)과
[면적을 보존한 분할 재개](crop-growing-geometry-continuation-v1.md)를 수용했다. 명시 zero-continuous-outflow의 단일 제거/다음 구간은 아래 별도 연구 자식으로 수용했으며, 전체 연속 부모는 미수용이다.

기존 Vanthoor/고정 GreenLight 모델은 C_leaf→SLA×C_leaf를 LAI의 권위로 유지한다.
그 프로필·함수·저장 결과를 바꾸지 않는다. 독립 logistic 기관 면적을 이 총면적에 조용히 맞추거나
면적/SLA를 새 기관 질량으로 사용하지 않는다. 원 입력에 따른 불일치는 기존 연구 대사에 남긴다.

새 연구 후보는 별도 면적/명시 model footprint→LAI와 buffer/기관/50과실 C를 구분한다.
Smoleňová의 분리 사례는 참고지만 이 둘의 결합은 새로운 hybrid 가정이다.
이번 후보 선택은 독립 LAI의 순간 광 동화 효과를 검증할 범위에 한정한다.
그 결과가 동적 생장·열/물 feedback·공급 제한·실제 품종의 정확도 증거는 아니다.
S3 pp6–7/15 표현의 긴장, 별도 코드/기관 sink·parameter 권리와 실행 순서는 조사에 남겼다.

## 구현 순서와 수용

1. **순간 광 동화:** 명시 LAI/buffer/Tc/PAR/CO2를 원식에 넣는다. 기존 SLA closure를 호출해 질량을 만들지 않는다.
   원 적용 영역·독립 Decimal/기존4사례·저장된 추적 비율/명시 합성 환경의 조건부 대사를 수용했다.
2. **같은 stage의 탄소·50과실 RHS 수용.** [324검사·독립9,810수치](../research/crop-explicit-lai-carbon-20261024.md)로 명시 LAI의 P를 buffer source에 정확히 한 번 사용한다.
   기존 분배/호흡·startup/50과실 유입·유출의 수지와 고정 profile을 보존하는 새 판본을 만든다.
   기존 전체 RHS를 호출한 후 P만 덮어써서 옛 SLA 영역 검사가 남거나 광 동화가 중복 계산되지 않게 한다.
   먼저 현재 호출 경계와 식을 대조하고 필요한 최소 조립을 정한다. 새 계수/보정값을 넣지 않는다.
   buffer+leaf+stem_root+Σfruit_C의 변화는 명시 P−생장/유지 호흡−외부 제거/말단 유출과 같아야 한다.
   Σfruit_N의 변화는 명시 유입−말단 유출과 같아야 한다. T24/Tsum은 원 수관 온도 forcing을 따른다.
   명시 LAI=SLA×C_leaf일 때 기존 RHS와 대사하고, 다를 때는 독립 C/N 참조·양쪽 domain을 검증한다.
   입력/코드·프로필/정책/원 LAI·재고/forcing SHA와 `not_assessed`를 보존한다. 아직 재고를 시간 전진시키지 않는다.
3. **면적 기반 순간 현열 경계 수용.** [260검사·독립1,900수치](../research/crop-area-canopy-energy-20261024.md)로
   명시 LAI/Ldot·고정 면적당 용량과 독립 총 유입/유출률·Tin/Tout/Q를 대사했다. 순량8ulp와 chain-rule 장부를 검증했다.
   면적 변화만으로 물질/온도/열을 추정하지 않는다. 실제 조직 물성/질량/열·기후 feedback 승인은 아니다.
4. **같은 stage의 명시 LAI 공동 C/N·공기/증기 RHS 수용.** [391검사·독립5,280수치](../research/crop-explicit-lai-climate-20261024.md).
   새 C/N·면적 현열 부품과 원 canopy exchange를 각1회 조립한다.
   같은 Tc/LAI와 고정 footprint·명시 상태/forcing·gross capacity flows를 결속하고 원 SLA 공동 RHS를 호출하지 않는다.
   비운반 순열은 명시 외부 열−동일 현열 H−잠열 LE이며 Qmaterial을 한 번 더한다. 공기 현열에는 H만,
   공기 수증기에는 E만 내부 교환으로 사용하고 외부 항/출입 경계를 별도로 보존한다. 유출 현열을 공기에 자동 가산하지 않는다.
   합성 순간 C/N·수관/공기/증기와 reduced-energy 장부·독립 Decimal/기존 같은 조건 대사·중복 호출/부분 입력/수치 hold,
   원 입력/자료·4root/WSL 보존을 수용한다. 태양/PAR/NIR·환기/CO2 확대·시간 전진과 실제 수분 공급은 별도다.
5. **첫 짧은 연속/재개와 제한된 단일 제거 구간 수용.** [236검사·독립1,542수치](../research/crop-growing-geometry-climate-20261024.md)는
   새 명시 동적 실내 기온/나이·면적 companion과 독립 gout/각 온도의 별도 회계 정책으로32초를 대사했다.
   이 정책을 기존 함수의 기본값이나 실제 물질 흐름 추론으로 적용하지 않는다. 초기만 canonical하며 이후 면적을 재맞추지 않는다.
   [분할 재개211검사·별도12복원](../research/crop-growing-geometry-continuation-20261024.md)은 같은 원 프로그램/고정 footprint·
   실제 a/A·C/N/Uref/기후/누적량과 D0를 보존한다. 새 초기화로 checkpoint 면적을 바꾸지 않았다.
   고정 목록 결과의 불변 저장/무계산 조회·같은 저장 상태3D를 수용했고,
   [명시 단일 제거/다음 구간](growing-geometry-removal-next-interval-v1.md)과
   [새 저장3D 소프트웨어](growing-geometry-removal-3d-v1.md)도 원 a/A/D0/시각·장부로 대사했다.
   새 화면의 무모사 실제 표시 창 최종 확인은 보류이며 전체 출현·공급/복수 사건·빈 수관 승인은 아니다.
   이 제거는 연속 leaf C/용량 유출0과 명시 전체 현재 C 분포에 한정한다.
   명시 epoch/원 elapsed·ID/단위를 보존하고 줄기/기관 pose와 실제 계산된 면적을 구분한다.
   독립 면적에 옛 SLA 제거를 자동 적용하지 않는다.
   착수 전 기존 잎의 실내 기온 열적 시계와 동적 Ta, curve의 dA/d열적 나이→dA/d초,
   각 stage LAI/Ldot와 명시 총 용량 흐름의 일치·공급/물성 가정을 먼저 정한다.
   기존 piecewise-constant 정확 시계를 동적 Ta/Tc로 몰래 바꾸거나 Ldot에서 총 운반/온도를 자동 생성하지 않는다.
   고정 기관은 목록이 고정된 범위이며 면적을 상수로 대체해 연속 면적 수용을 완료하지 않는다.
   전체 구간과 분할/재개의 C/N·열/물 장부, 원 UTC/유리수 사건·실패 직전 확인 상태를 독립 참조와 대사한다.
   먼저 고정 기관의 짧은 범위를 검증할 수 있지만 새 출현/전체 작기 지원으로 표시하지 않는다.
6. **출현/공급·관리 확대:** [새 의존성/원문 검토](../research/leaf-carbon-sink-primary-sources-20261024.md)를 마쳤고 [첫 배분 산술](crop-leaf-carbon-partition-v1.md)을54신규/187관련·fresh72조건으로 수용했다. 현재 N은 fruit number다.
   [같은 stage 공동 RHS의3조정](crop-leaf-partition-climate-rhs-v1.md)을79신규/293관련·fresh42조건으로 수용했다. 원 P/과실/기후·미수정 미분/원 hash를 보존하고 각 component1회·전체 C/leaf 수지를 대사했다.
   [권위 개별 C_i/합계·유지호흡/고갈의 순간 RHS](crop-leaf-carbon-stock-rhs-v1.md)를101신규/394관련·fresh72조건으로 수용했다. 같은 floor의 기관 C와 명시 제거를 조립하고 원 선형 호흡의 질량 비례 가정·원 값/hash를 보존했다.
   [aggregate leaf slot을 제외한 C_i/a/A의 짧은 공동 적분](crop-leaf-carbon-stock-dynamics-v1.md)을58신규/289관련·app-free 식/별도102시점으로 수용했다. 원 과실/기후·개별/전체 수지와 실제 A·D0를 보존했다.
   다음은 현재 C_i/a/A·누적량의 불변 context/분할 재개→초기 C/현열이 조달되는 출현이다. 새 목록은 고정이며 공급 제한/면적 feedback은 미수용이다.
   순수 상대 priority 배분을 논문의 beta 수요/reserve/공급 제한 법칙으로 제시하지 않는다.
   새 잎의 양의 면적에 대응하는 C의 출처·buffer/기관 분배·생장호흡과 고갈 정책을 정한다.
   별도 잎 C 원장 없는 면적/질량 역산과 동일 사건의 연속/순간 중복 차감은 거부한다.
   현 순간 제거 v1은 SLA 일치 가정이므로 독립 면적 후보에 자동 재사용하지 않는다.
7. **저장/제품/검증:** 같은 농장/작기·shoot/plant·전체 수관 coverage/측정법·현재 권리·매개변수와
   실행/서명·불변 결과→같은 UTC3D를 수용한 범위만 붙인다. 독립 국내/미래/대응 비교와 G0–G4는 별도다.

## 남는 입력과 금지되는 해석

명시 footprint와 추적 목록의 전체성을 실제 농장으로 확대할 근거가 없다.
기관 curve의 단일 logistic만으로 공급 제한/기아·광 적응·새 조직 C·실제 품종을 식별하지 못한다.
진단비 LAI/C_leaf는 생장 법칙이 아니며0 C에서 정의되지 않는다. 다른 모델의 DM/CH2O/SLA도 자동 호환하지 않는다.
기존 태양/PAR/NIR·CO2/열·물 모델의 상태/계량과 새 area 권위가 일치해야 공동 RHS로 사용할 수 있다.
독립 자료 수신은 합성 순수 계산 개발의 선행이 아니며 실제 예측/추천 게시 조건을 대신하지 않는다.
