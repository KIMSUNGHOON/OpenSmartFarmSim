# 독립 면적의 수관 열용량·현열 경계 1차 검토 — 2026-10-24

상태: **검토 제안**. 명시 LAI의 순간 열 경계를 정하며 공동 RHS/적분·실제 물성·기후 검증을 승인하지 않는다.
기준 HEAD는 `7e24abd935b2d2edf48256639f4f254f1093ea2f`다. [기하·탄소 계약](../contracts/crop-geometry-carbon-coupling-research-v1.md), [기존 운반 계약](../contracts/crop-canopy-energy-transport-v1.md), [선행 열 검토](crop-variable-canopy-energy-review-20261009.md), [명시 LAI C/N 결과](crop-explicit-lai-carbon-20261024.md)를 읽었다.
실제 부모 spawn 요청/응답: `task_name=explicit_area_heat_sources`, `fork_turns=none`, `model=gpt-6.1-sol`, `reasoning_effort=xhigh` → `/root/explicit_area_heat_sources`; 부모가 확인했다.
자체 native CLI command/session/turn-event/hash는 확보하지 못했다. 부모 `2026-10-24T05:20:58.755Z`의 native proof는 부모 증거이며 이 자식의 증거로 재사용하지 않는다. 재귀 CLI/하위 agent 실행0이다.
reviewer는 이 연구 자식이며 독립 부모 검토/자료 채택 reviewer는 미확정이다. 출력은 이 문서1개이며 원 자료/프로필·코드·계약·계획을 변경하지 않는다.

## 원문이 직접 뒷받침하는 범위

고정 GreenLight Ch8 `/Capacities/capCan`은 `capCan=capLeaf*lai`(Eq8.20), `/Parameters/Table 8.1/capLeaf`는 잎 면적당 상수 열용량이다. 단위는 각각 `J/m2_floor/K`, `J/m2_leaf/K`다. 이 프로젝트 품종의 측정 물성으로 채택하지 않는다. [S1]
`/State equations/Temperature states/tCan`(Eq8.1)은 복사·현열·잠열 순열률을 `capCan`으로 나누는 온도 미분이다. 검토한 이 식에는 용량 미분이나 별도 성장/제거 물질 현열 항이 없다. 전체 문헌의 모든 식에 대한 부재 주장은 아니다. [S1]
따라서 원식 `C*Tc'=Φ`와 변동 용량의 저장 에너지 미분 `U'=Φ`를 자동으로 동일시하지 않는다. `U=C*(Tc-Tref)`의 곱 미분에는 `(Tc-Tref)*C'`가 추가된다. 이는 원식에서 도출한 수학이며 원문이 아래 새 운반 경계를 검증한 것은 아니다.
MIT 제어체적 제1법칙은 열·일 외에 경계를 통과하는 질량의 에너지를 포함하고, 유체의 유동 일과 내부 에너지를 엔탈피로 합친다. 아래 용량률은 실제 질량/엔탈피 유량으로 측정된 것이 아니므로 그 일반 원리를 그대로 실제 잎 열수지의 증거로 삼지 않는다. [S2]
Smoleňová의 면적/생체량 분리와 미사용 기후 feedback은 [앞선 원문 검토](continuous-leaf-carbon-primary-sources-20261024.md)의 범위다. 이는 독립 면적·탄소·열 hybrid나 실제 기후 feedback의 검증이 아니다. 새 열계수/자료 채택0이다.

## 가장 작은 새 프로젝트 경계

독립 면적이 나타내는 **표현된 열용량 재고**만 계산한다. `L=LAI`와 부호 있는 `Ldot`은 같은 stage/footprint/추적 범위에서 명시하며 SLA×C 또는 면적/SLA 질량을 만들지 않는다.
`k=capLeaf>0`은 판본 안에서 고정된 명시 합성 가정이다. 실제 잎 수분·건물량·질량당 비열·수분/조직 유입·대사열은 미상이다. 면적 변화는 실제 물질의 발생/유출을 증명하지 않는다.
모든 아래 입력을 호출자가 제공한다. 알려지지 않은 유량/열/온도를0·기온·현재 수관 온도로 기본 설정하지 않는다. 명시0은 허용하되 순변화율의 양/음 부분에서 총 유량을 자동 생성하지 않는다.

| 입력 | 단위·의미 |
| --- | --- |
| `L`, `Ldot` | `m2_leaf/m2_floor`, `m2_leaf/m2_floor/s`; 현재 L은 양수, Ldot는 부호 있음 |
| `k` | `J/m2_leaf/K`; 고정 양수, 물성 승인과 구별 |
| `gin`, `gout` | 각각 `J/m2_floor/K/s`; 독립적으로 명시한0 이상 총 용량 유입/유출률 |
| `Tc`, `Tin`, `Tout`, `Tref` | `degC`; 현재/유입/유출/고정 회계 기준 온도, 모두 명시 |
| `Q` | `W/m2_floor`; 용량 운반을 제외한 부호 있는 순열률, 양수는 가열 |

```text
C = k*L; Cdot = k*Ldot = gin-gout                 # 필수 독립 대사
U = C*(Tc-Tref)
Qin = gin*(Tin-Tref); Qout = gout*(Tout-Tref)
Qmaterial = Qin-Qout
Udot = Q+Qmaterial
Tdot = (Q+gin*(Tin-Tc)-gout*(Tout-Tc))/C
C*Tdot+(Tc-Tref)*Cdot = Q+Qmaterial
```

이 식들은 **새 프로젝트 회계 제안**이다. 단위는 C가 `J/m2_floor/K`, U가 `J/m2_floor`, Udot가 `W/m2_floor`, Tdot가 `K/s`다. 실제 질량·화학 에너지·수분을 계산하지 않는다.
`Tout`도 명시하는 일반 경계를 제안한다. 기존처럼 `Tout=Tc`를 명시하면 유출은 Tdot에서 소거되지만 Qout 장부에는 남는다. `Tout≠Tc`는 선택 유출/외부 용량 저장소의 가정이며 단일 수관 내부 온도분포가 검증됐다는 뜻이 아니다.
`gin=gout>0`의 순 Ldot0에서도 다른 Tin/Tout이면 온도가 변한다. 순 Ldot만으로 운반을 재구성할 수 없다. 유입·유출 용량률의 부호 제한과 기준 에너지의 부호 제한을 혼동하지 않는다.
Tc/Tin/Tout가 Tref보다 낮으면 U/Qin/Qout는 음수일 수 있다. Q/Qmaterial/Udot도 양/0/음 모두 가능하며 절댓값·0 clamp를 하지 않는다. 유출 에너지를 자동으로 온실 공기에 더하지 않는다.
`Tref_new=Tref+δ`이면 `U_new=U-δ*C`, `Qmaterial_new=Qmaterial-δ*Cdot`, `Udot_new=Udot-δ*Cdot`이고 Tc/Tdot는 불변이다. Tdot는 위 온도차 식으로 계산해 기준온도 상쇄 오차를 줄인다.
L 또는 k가 변하면서 C가 변하는 것과 물질 운반은 별도 선언이다. k의 시간 변화/판본 교체에는 `L*kdot` 등 별도 에너지 정책이 필요하므로 이 경계에서는 hold한다.

## 순수 API와 사전 수용 제안

새 판본의 순수 순간 함수1개가 위 입력·닫힌 단위/합성 origin·정책/입력 ID를 받고 C/Cdot/U, 총 운반별 signed 열률, Udot/Tdot, 독립 용량/chain-rule 잔차와 입력/정책/코드 hash를 반환하도록 제안한다. 기존 SLA 함수/프로필을 호출해 기하를 대체하지 않는다.
gin−gout와 k*Ldot는 **순량의 해상도**로 검사한다. 거의 같은 큰 총 유량의 합을 허용 오차 분모로 쓰면 틀린 순량을 통과시킬 수 있다. 정확 binary64 값의 Fraction 차이 또는 명시 순량 ULP 정책·독립 고정밀 대사를 계약에 정한다.
작은/0 총 유량에서도 Tin/Tout/Q를 명시하고 모든 입력/중간량의 유한성·단위·양수 C·표현 가능성을 검사한다. 기준 이동으로 온도 복원이 불안정하거나 곱/나눗셈이 소실/overflow하면 수치 hold이며 몰래 보정하지 않는다.
독립 Decimal 참조는 app을 import하지 않고 명시 입력/공식을 계산한다. 참조 판본·입력 생성·수용 오차는 구현 전에 고정한다. 이 메모는 수치 기대값이나 새 물리 오차 기준을 생성하지 않는다.

1. 고정 L/명시 gin=gout=0의 Q 양/0/음, 순성장/순감소와 Tout=Tc/서로 다른 Tout, 같은 순량의 다른 총 회전을 대사한다.
2. 모든 물리 온도는 고정하고 Tref를 이동해 U/Qin/Qout의 음/0/양과 Tc/Tdot 불변·Udot 변환을 확인한다.
3. 총 유량이 커도 순량 불일치,0 순량과0 총 흐름의 혼동, kdot 누락, 잘못된 단위/부호/누락/비유한을 거부한다.
4. L=0·완전 제거/재진입은 `EMPTY_CANOPY_HOLD`; epsilon C나 임의 Tc 초기화로 통과시키지 않는다. 현재 양의 C에서 순간 계산해도 뒤 적분의 고갈 통과를 승인하지 않는다.
5. 입력 불변/동일 재실행·기존 고정 LAI/기존 SLA 운반 회귀를 확인한다. 사건 제거·시간 전진/재개·같은 stage 기후 연결은 별도 자식이다.

반환 범위는 합성 소프트웨어 연구/`G0_G4=not_assessed`다. 실제 k·물질 기원/온도·물/건물·대사/유체 엔탈피·전체 수관 coverage·독립 국내/미래 작기·열/구매 에너지/경제/추천 검증은 hold를 유지한다.

## 실제 수신·권리·QC

아래3건은 이번 작업의 직접 GET 시작→완료(UTC), HTTP200, 원 bytes SHA-256이다. 관측 시각·역사적 `available_at`은 모두 `null`; 공개 문서 수신시각을 최초 이용 가능 시각으로 소급하지 않는다. raw는 저장소에 복사하지 않았다.

| 원천·게시/판본 | retrieval UTC·bytes·SHA-256 | 이용/표시/재배포·QC |
| --- | --- | --- |
| S1 Ch8, commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`; 파일 생성 고지May2025, commit/게시시각 미검증 | `2026-10-24T05:24:11.375394Z→05:24:11.620570Z`; 130649; `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3` | JSON pointer/식/단위 직접 대조, 기존 pin 일치. Clear BSD 조건 아래 사용/재배포; 고지·조건·면책 보존, 무단 보증/특허권 불부여. [S1L] |
| S1L 같은 commit LICENSE, ©2025 David Katzin/Wageningen Research Foundation | `2026-10-24T05:24:11.622260Z→05:24:11.844901Z`; 1716; `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` | 라이선스 원문/선행 hash 대조. 외부 논문/자료 권리로 확대하지 않는다. |
| S2 MIT §2.5.2, 게시/수정/정확 revision 미상 | `2026-10-24T05:24:11.844946Z→05:24:11.920204Z`; 57872; `438a9704182092ced15d8728a73f34c74ccd141308d557765b9737eda9e42117` | 제1법칙/질량 에너지·유동 일 문단 읽기·자체 요약/링크. raw/그림 표시·재배포권 미확인, 채택0. |

문헌 QC는 모델식/단위/권리의 읽기 대조이며 현장 자료 QC가 아니다. 이 문서의 링크·공백·줄 수만 검사하며 모델/수치·브라우저·농장 시험은 실행하지 않았다. 전체 hybrid/기후 타당성이나 G0–G4 통과를 선언하지 않는다.

[S1]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json
[S1L]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt
[S2]: https://web.mit.edu/16.unified/www/SPRING/thermodynamics/notes/node18.html
