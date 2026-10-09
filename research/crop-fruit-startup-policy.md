# 과실 시작·명시적 유입 정책의 조사와 다음 계산 경계

날짜: 2026-10-05 KST. **연구 정책·독립 대수 수용**이며 자동 착과/실제 품종/전체 작기는 미수용이다.
[수용 계약](../contracts/crop-fruit-startup-policy-v1.md),
[8개 원천 등록부](crop-fruit-startup-source-register.json),
[독립 수치](artifacts/crop-fruit-startup-policy-reference-20261005.json)를 함께 읽는다.
이 문서는 현재 CLI `gpt-6.1-sol` / `xhigh`, 세션
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, 실제 turn `2026-10-04T23:47:34.729Z`에서 작성했다.
재귀 CLI나 제품 runtime 판단을 실행하지 않았다. 원문/농장 자료를 새 계수로 승인하지 않는다.

## 시작 상태와 원천의 차이

| 원천 | 원문/고정 코드의 확인 | 현재 개발 판단 |
| --- | --- | --- |
| [Vanthoor 2011](https://edepot.wur.nl/170301), 인쇄 p253–256/식9.29–9.45 | 양의 초기 N1 요구, 숫자 없음. 첫 유입 S×W1. 개수 이동은 onset gate, 탄소 이동은 gate 없음. W1의 Gompertz 적분 경계 없음 | 실제 배열/seed·W1·자동 S·net RGR 채택 보류. 생식기 이전에 현재 C>0⇒N>0 불변을 적용할 수 없음 |
| [Greenhouses 고정 코드](https://github.com/queraltab/Greenhouses-Library/blob/89ae0e8097eb0751abce2013d304fa5f9c09b885/Greenhouses/Components/CropYield/TomatoYieldModel.mo#L183) | N/C 0, W1 0; W1은 전체 실행 시간에 GR1 누적. tail 분모에 epsilon; 과실 RGR=GR/GMax/day | 원식 정정/초기 실측으로 채택하지 않음. 빈 sink 보존·잠재 상대 성장과 실제 net RGR 구분 |
| [같은 판본 설명](https://github.com/queraltab/Greenhouses-Library/blob/89ae0e8097eb0751abce2013d304fa5f9c09b885/docs/cropyield.rst#L409) | 원 수요 배분/개수 이동을 설명 | 코드의 수정·초기조건을 원 문헌이 확정한 것으로 취급하지 않음 |
| [GreenLight 고정 단순화 모델](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json) | 전체 fruit 초기 탄소 312, 고정 RGR 3e−6/s; 50개 과실 개수/나이 없음 | 합계를 50등분하거나 고정 RGR를 실측으로 바꾸지 않음 |
| [de Koning 1994 원 학위논문](https://edepot.wur.nl/205947), p103–104/146–147/150 | Gompertz의 나이는 개화 후 시간; 모델 시작은 첫 화방 개화. 품종별 계수 필요. sink 제한의 잉여는 다음 날로 유지 | Axiany 착과 시각과 같은 것으로 가정하지 않음. 아래 buffer 유보는 이 원리와 탄소 수지에서 도출한 **별도 연구 변형**, Vanthoor 원식/생리 검증이 아님 |

de Koning PDF 8,021,488 bytes/SHA-256 `699212ee77083ab077b631afec902b946d00653b4fa3d97c893bb83c7138f52d`를
실제 내려받아 246페이지를 추출하고 PDF107/108/149/150/153을 직접 렌더링해 대사했다.
서지의 [1994-11-23/DOI](https://research.wur.nl/en/publications/development-and-dry-matter-distribution-in-glasshouse-tomato-a-qu/)와
원본문을 확인했다. 기존 Vanthoor/코드 6개 bytes hash도 다시 확인했고 이전 retrieval은 유지했다.
공개 접근은 전체 논문/그림 재배포 권리가 아니다. 원문·렌더링·HTML은 저장소에 넣지 않았다.
코드 두 라이선스의 기존 BSD 조건/고지는 유지하며 이번에는 연구·인용만 했다.
원천의 최초 공개 `available_at`은 재구성하지 못했으므로 과거 농장 결정에 채택하지 않는다.

## W1·S·RGR를 자동 생성하지 않는 이유

고정 Gompertz 질량 함수 H(t)의 미분이 GR(t)다. W1은 적분이라고만 기술되어
`H(FGP/50)−H(0)`, `H(FGP/100)−H(0)`, 초기 질량을 포함한 `H(FGP/50)`이 서로 다르다.
17/20/23°C의 기존 참조 계수로 세 대안을 **70자리 Decimal**로 대사했다.
어느 값도 품종의 진입 질량으로 채택하지 않았다. 전체 실행 경과 시간에 GR1을
누적하는 구현은 각 새 과실의 나이 구간 적분과 다르다. 온도가 변하면 적분 경로도 필요하다.

S의 원 자동식은 일반 화방/식재 밀도 가정이다. 명시적 유입의 실제 적용에는
개화·착과/탈락·적과·면적·시간 간격이 대응하는 기록이 필요하다.
첫 구획의 과실 환산 개수는 실제 수확한 정수 개수와 다르다.

RGR는 1/s의 net 상대 성장 입력이다. 잠재 GR/GMax, GR/H(t), 기관의 실측
로그 질량 변화는 서로 다르다. 구획 질량 변화에는 이동/유입/제거도 있어 단순 dC/C로
생리 RGR를 생성할 수 없다. 50개 명시적 유한·비음수 입력을 유지한다.
누락/음수/비유한은 hold이며, 실제 음의 net RGR 지원도 별도 호흡 정책 검토가 필요하다.
0질량에서 로그나 나눗셈을 하지 않는다. 기존 leaf/stem의 고정 RGR 가정도 유지 표시한다.

## 선택한 연구 변형: 빈 tail의 요청 유보

새 정책 `explicit-entry-empty-sink-deferral-research-v1`은 **생식기 이후**의
명시적 입력만 받는 작은 배분 adapter의 근거다. 기존 v1 식/결과/manifest는 유지한다.
원식의 자동 착과/seed·첫 구획 추가 생장·숙기/생과 환산은 도입하지 않는다.

Fq는 기존 kernel이 요청한 과실 구조 탄소 유량, A1=S×W1,
D2는 j=2..50의 고정 잠재 수요 합이다. A1>Fq 또는 S>0/W1≤0은 hold다.

- D2>0이면 기존 명시적 배분과 같게 Fa=Fq, 뒤 배분=(Fq−A1)×w/D2다.
- D2=0이면 Fa=A1, 뒤 배분=0, 미실현 요청 R=Fq−Fa를 유보한다.
  S=0인 빈 과실 상태에서는 Fa=0이며 새 과실을 만들지 않는다.
- 구조 배분 합계는 Fa, Fa+R=Fq, 개수 유입 합계는 S다. epsilon·clip·최소 seed는 없다.
- 새 whole-plant 판본의 과실 생장 호흡은 cG×Fa이고,
  기존 buffer 미분에는 **(1+cG)×R**를 더해야 한다.
  구조 탄소 R만 돌리고 호흡을 Fa로 줄이면 cG×R가 사라진다.
  기존 호흡을 유지하면 수지는 맞더라도 실현하지 않은 생장에 cG×R를 청구한다.
  이 adapter를 기존 v1 buffer/호흡에 단독 연결해서는 안 된다.

유보는 자동 생산량을 만들어내기 위한 분배가 아니다. 빈 sink에 소비를 강제하지 않는
명시적 연구 판본이다. 실제 sink 능력/저장·과실 성장 정확도는 독립 실측 검증이 필요하다.
기존 첫 구획의 추가 생장 배분이 없는 구조적 한계도 그대로다.

## 사례 수용·hold·다음 한 단계

[독립 계산기](crop-fruit-startup-reference.py)는 제품을 import하지 않고 **9개 정상 대수 사례**의
50개 C/N 유입과 요청/실현/유보·buffer/호흡 수지를 대사했다.
**5개 입력 hold**, 3개 온도의 미채택 W1/RGR 대안과 생식기 이전 원식 반례를 남겼다.
양의 초기 생식기·빈 tail/전체 빈 과실·첫 양의 진입·0/작고 큰 값의 보존을 확인했다.
원 pre-onset의 h=0에서는 N2=0인 채 C2>0이 될 수 있다.
탄소 이동에도 h를 붙여 문제를 숨기지 않고 현재 생식기 이전을 **hold**로 유지한다.
두 번 생성한 공개 증거가 byte-identical이고 코드/계약/등록부/기존 profile hash에 묶인다.
이것은 소프트웨어 정책 산술이며 제품 함수·농업 정확도 수용이 아니다.

다음 [순수 요청/실현 adapter 계약](../contracts/crop-fruit-startup-rates-v1.md)은
2개 코드/시험 파일로 위 독립 값과 상태/단위·hash·유한/underflow·보존을 검증한다.
그 후 별도 whole-plant 판본에서 buffer와 호흡을 동시에 연결하고 짧은 적분/사건을 재검증한다.
저장/3D는 새 판본·같은 UTC 값만 읽으며 임의 성장 애니메이션을 넣지 않는다.

현재 국내 독립 자료 0건·실제 forcing/Run 0개, G0–G4는 미수용이다.
실제 초기 기관/나이 분포·S/W1/RGR·onset·관리·과중/건물률·출하/정산은 외부 의존성이다.
모델 개발과 국내 권리/자료 확보는 병행한다. 예측/추천/production 날짜는 추정할 수 없다.
다음 순수 adapter는 **0.5 집중 작업일** 잠정, 이후 새 결합/적분은 **0.5–1일**로 나눠
실행 후 수정한다. 4시간/집중일 가정의 첫 검증 목표는 10월5–6일 KST이며 완료 약속은 아니다.
