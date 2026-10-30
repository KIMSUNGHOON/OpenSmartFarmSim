# 작기·생산 연결의 현재 경계 — 2026-10-31

상태: 실제 코드/저장 원본의 준비 검토. [출처 목록](season-source-inventory-20261031.md)을
부모 native gpt-6.1-sol/xhigh에서 검토했다. **과실 모델을 새로 만들기보다 이미 있는
구획 상태와 유출을 현재 저장 결과에 연결하는 것이 다음 단계**다.

## 코드와 실제 자료 대조

| 대상 | 현재 증거 | 남은 구현/검증 |
| --- | --- | --- |
| 과실 상태/순간 식 | `crop_supply_morphology_birth_stage.evaluate`가 기존 `crop_explicit_lai_carbon_cohorts`를 호출한다. 원38프레임 모두 C/N 각각50구획이 비영이다. 기존 수요/분배/호흡/terminal 식을 재구현할 이유가 없다 | 현재 DTO/3D 화면은 잎·줄기에 집중한다. C/N 모델 구획은 개별 실제 과실 ID/위치·색/생과 크기가 아니다 |
| 현재 생산 원장 | `crop_supply_morphology_books.flux`와 repeat books에 `terminal_carbon`, `terminal_number`의 원점 기준 정확 누적이 있다 | 기존 `crop_harvest._terminal_row`는 별도 cycle query/UTC·float 누적 계약이다. 현재 rational at/출현 전후·Context/CP를 그 객체로 가장할 수 없다. 새 버전의 직접 조회 연결 필요 |
| 전체 작기 | 이전 crop-cycle 경로의166일 합성 계산/수확 대사는 존재한다. 현재 성장/공기·수증기 결합과는 다른 모델/결과 계보다 | 이전166일 수용을 새 형태 결합의 전체 작기 수용으로 이전하지 않는다 |
| 길이·상태 용량 | 이번 자료의 원 horizon은512초. 기반 `crop_stem_root_stock_dynamics.integrate`는4096 step/600초/32768 scalar를 제한한다 | 512초 자체가 보편적 hard cap은 아니다. 긴 기상 forcing·수렴·연속 수지/현재 권리/저장을 보존하는 새 장기 계산 경계 필요. 상한 숫자만 늘리지 않는다 |
| Context 용량 | 실제 공개6Context는181551→2034765bytes. 마지막 receipts1814076, descriptor142040, root CP78555bytes(각 값의 canonical 크기) | 2MiB까지62387bytes. 계보/조달 증거가 대부분이다. 실제 다음 출현 용량이나 전체 작기를 외삽하지 않는다. 불변 이력과 현재 계산 상태의 분리/참조 및 cold 검증은 별도 수용 |
| 관리·기후 | 현재 stage는 vegetative removal/capacity outflow0을 요구한다. 공기 온도·증기/수관 에너지 상태와 외부 열·증기 forcing, 입력 CO₂/PAR를 사용한다 | 기존 제거/환기/CO₂ 모델을 같은 상태/관리/경계와 연결해야 한다. 현재 prefix를 지역 기상·관리 전체 작기 또는 완전한 CO₂/물/양분 수지로 표시하지 않는다 |
| 자원 | 수관 증기 교환/외부 증기·열의 누적이 존재한다 | 증기 교환은 급액/배액/구매 용수가 아니다. net 외부 열은 기기의 구매 전력/연료가 아니다. 별도 설비/변환/계량 대응 필요 |
| 생과·등급·경제 | 기존 harvest 질량/배정 및 Decimal 경제 계산기가 존재한다 | 같은 출처/면적·기간·실제 제거/수확·η/DMC·판매·원가와 연결이 필요하다. terminal C/N을 생과kg·판매로 바로 변환하지 않는다 |

이 표의 코드 경로와 양적 관측은 [기계 증거](artifacts/season-production-readiness-20261031.json)에
원 파일 지문과 함께 남긴다. 실제 공개101파일의 hash/bytes를 확인하고62개 고유 CAS 파일로
별도 사본을 구성했다. 원 reader의 전체 그래프 검증에서38프레임이 공개 DTO와 모두 같았다.
검사 내부1.598초는 이 한 환경의 관측이며 처리량 보장이 아니다. 생장 모듈10개를 import 차단했고
새 모델/DB/network/subprocess 실행0이었다. 첫 CAS 조립은 root descriptor 중복으로 실패해
동일 hash/bytes 중복만 대사·제외한 새 출력에서 통과했다. 원본은 변경하지 않았다.

## 원식·자료와 권리

[Vanthoor 등2011의 저자 등록](https://research.wur.nl/en/publications/a-methodology-for-model-based-greenhouse-design-part-2-descriptio/)
은 기후에 따른 토마토 수량 모델의 국외 검증을 다룬다. 이 구현/국내 품종의 검증 증거는 아니다.
고정 [GreenLight 설명](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/readme.txt)은
단순화된 작물 파일과 greenhouse/controls/weather의 조합을 구분한다. 전체 구획식·정책은
[기존 직접 원문 검토](crop-fruit-cohorts-baseline.md)와 [보존형 배분 판본](crop-fruit-allocation-policy.md)에 있다.
이번에 계수나 새 모델/저자 정정을 채택하지 않았다.

정확 commit의 readme2581bytes/SHA `9e5ca837f6be1524886550f2c00d0ddab0cf980fd4be778e7e8d3532f4239ad9`,
[BSD-3-Clause-Clear 고지](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)
1716bytes/SHA `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a`를 다시 읽었다.
파일 고지는May2025이며 정확 최초 공개/의사결정 `available_at`은 복원하지 않았다.
원 코드/계수의 신규 도입은 없다.

[공식 AGC2 v2 metadata](https://api.figshare.com/v2/articles/12764777/versions/2)는 이번 조회에서도
v2·게시2020-09-23T10:41:39Z·CC0 선언과 file24757220/8418715bytes를 반환했다.
8799bytes/SHA `47d0bc15e1fa886ba9939e8612754494e885a5dfa7c0e4e277c6576ed69e71e6`가 기존 명시v2 관측과 같다.
관측 작기는2019-12-16~2020-05-29이며 이번 원 측정 파일 재수신은0이다.
retrieval UTC/제품 ID/판본·QC·권리 검토와 원문 지문은 기계 증거에 있다.
metadata/고지 연구와 자체 요약·링크만 사용하며 원문을 Git/제품에 재배포하지 않는다.
과거 의사결정의 `available_at`은 unknown이다.

Axiany/Maxifort는 해외 개발 참조이고 국내 첫 품종은 미확정이다. 실제 입력의
시간대·수관/초기 상태·관리·면적/DMC hold는
[후속 확인](crop-harvest-reference303-dmc-followup-20261008.md)에서도 남았다.
국내 catalog/절차·통계 요약과 실제 독립 raw 측정을 구분한
[목록](season-source-inventory-20261031.md)을 검토했다. 현재 확보 국내 독립 자료는0이다.

## 수정한 구현 순서와 다음 수용 기준

1. **현재 저장 C/N·terminal 직접 조회** — [계약](../contracts/supply-terminal-window-v1.md).
   원38시점/50구획·정확 시각/원점/출현 전후를 보존하고 누적 차이와 합계를 독립 산술로 대사한다.
   새 생장/DB/network/CLI/원본쓰기0, 현재/늦은 원본 변경 거부·원 자료/GUI/WSL 보존을 확인한다.
2. **같은 결과의 생산/자원 표시 연결** — 원 수치와 단위·원본 시점/hold를 기존3D와 함께 확인한다.
   API/농장 연결은 해당 source custody·현재 권리의 별도 선행을 지킨다.
3. **장기 결합 수치** — 원점 유지 forcing 구간/관리·기후 결합 → 검증 가능한 상태/이력 크기와
   checkpoint/출력 paging → 기간 확대·간격 축소·전체/분할/cold/물질·에너지 수지 대사.
4. **질량/자원·경제 연결** — 명시 근거 있는 η/DMC/수확 배정, 급배액/설비 구매량·같은 기간
   Decimal 원장과 거시/수급을 연결한다. 현재 판매·추천 관문을 변경하지 않는다.

개발과 국내 독립 자료 확보는 병행한다. 자료 미확보를 합성 소프트웨어 개발의 선행으로
옮기지 않으며, 실제 품종 예측/마진/후보 비교 게시 조건은 PROJECT_SPEC §5.3/§6을 따른다.
다음 조회기의 계획 분해는 원 수치 연결0.5–1h, 현재 원본/fence0.5–1h,
독립·반례/보존 검증0.5–1.5h(합계1.5–3.5집중시간)다. 실제 검증으로 갱신한다.
전체 제품·독립 자료 확보 완료일은 미정이며 G0–G4 미평가/R2 미승인·전체 goal active/incomplete다.
