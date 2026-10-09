# 작은 수관의 광합성 적용 정책 — 2026-10-04

상태: **원식 유지/지원 영역 제한 정책과 로컬 검사 수용**.
[정책 계약](../contracts/crop-photosynthesis-domain-v1.md),
[첫 유량 모듈](crop-growth-rates-implementation.md)의 적용 영역을 구체화한다.

## 실제 조사와 근거

기존 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn context
`2026-10-04T10:07:46.899Z`, **gpt-6.1-sol / xhigh**에서 판단했다. 재귀 CLI는 없다.
원 학위논문 PDF p253~254(인쇄 p249~250)과 고정 저자 JSON의 식/초기조건을
실제 읽었다. 이번 web open에서 PDF는 403이라 이전에 받아 해시를 확인한 공개
바이트를 사용했다. [WUR 원 연구 등록](https://research.wur.nl/en/publications/a-methodology-for-model-based-greenhouse-design-part-2-descriptio/)도 확인했다.

원식은 잎 수준 Gamma의 온도 관계 Eq9.22를 수관 수준 Eq9.23으로 조정한다.
원문은 잎 식을 수관에 직접 적용할 때 낮은 광/CO₂에서 최적 온도가 지나치게
낮아지는 문제를 설명한다. 따라서 코드의 LAI 역수는 오타로 고칠 대상이라고
판단하지 않는다. [원 학위논문](https://edepot.wur.nl/170301),
[고정 저자 구현](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json).

| 근거 | 고정 바이트 SHA-256 | 용도/권리 |
| --- | --- | --- |
| Vanthoor 원 학위논문 | `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38` | 수식/설명 대조. PDF/원문 재배포 없음 |
| GreenLight crop JSON, `7a7b368` | `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033` | BSD-3-Clause-Clear, [원 고지 보존](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt) |
| 이번 참조 프로필 | `d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca` | 일반 참조, 품종 보정/G0 아님 |

게시/조회 시각·판본·원문 권리/단위·QC·reviewer는
[기존 원천 등록부](crop-tomato-source-register-20261004.json)의 해당 source/parameter ID를
유지한다. 이 검토는 새로운 측정 자료를 채택하지 않는다.

## 직접 도출한 적용 구간

양의 LAI `L`에서 Gamma는 `cGamma * (20 + (Tcan-20)/L)`이다.
따라서 `0 <= Gamma <= Ci`는 `20L + Delta >= 0`와 `AL - Delta >= 0`의
두 조건으로 바꿀 수 있다. 여기서 `Ci = eta * co2`, `Delta = Tcan-20`,
`A = Ci/cGamma-20`이다. 이는 아래 원문 검증 결과가 아니라 **이번 독립 대수 도출**이다.
세 부호별 구간은 계약에 명시했다. 낮은 CO₂에서는 단순 LAI 하한 외에 상한도 생긴다.

아래는 고정 프로필에서 읽은 cGamma/eta/20으로 60자리 Decimal 계산한 **수식 사례**다.
수관 온도/CO₂는 합성 검사용 숫자이며 지역/품종의 권장 온도나 CO₂가 아니다.

| Tcan (°C) | 주변 CO₂ (ppm) | 양의 PAR에서 LAI 적용 구간 (m² leaf/m² floor) |
| --- | --- | --- |
| 10 | 400 | L ≥ 0.5 |
| 17 | 400 | L ≥ 0.15 |
| 23 | 400 | L ≥ 0.0217948717949… |
| 34 | 400 | L ≥ 0.101709401709… |
| 17 | 40 | 0.15 ≤ L ≤ 0.708333333333… |

L=1에서는 Eq9.22와 일치한다. L→0에서는 Tcan<20의 Gamma가 −∞,
Tcan>20이면 +∞로 향한다. Tcan=20의 Gamma만 34 ppm으로 일정하다.
PAR=0은 광 동화 0이므로 Gamma를 평가하지 않는다. 온도/CO₂/기관 입력의
다른 범위 검사는 야간에도 유지한다.

Gamma>Ci에서 원문의 `P`와 광호흡 `R=P*Gamma/Ci`가 모두 음수일 수 있고,
차이 `P-R`만 양수로 돌아올 수 있다. 양의 순 동화 숫자가 나왔다는 이유로 그
영역을 생리적으로 허용하지 않는다. Gamma<0은 분모의 특이점까지 만들 수 있다.
v1은 이러한 영역을 이미 명시적으로 거부하며 새 0/최솟값 대체를 만들지 않는다.

## 품종 초기조건과 대안 판단

저자 코드의 일반 초기 잎 CH₂O 4,368 mg/m² floor와 참조 SLA의 곱은
LAI **0.1161888**이다. 이것은 Axiany 측정 초기조건이 아니다. 이 일반 초기값을
합성 입력으로 사용할 경우 위 17°C/400 ppm 사례는 거부하고 20°C/400 ppm은
허용한다. 초기 LAI를 조건에 맞게 늘리거나 낮은 온도를 20°C로 바꾸지 않는다.
Axiany 실제 초기 기관 상태/LAI·수관/PAR/CO₂와 관리 사건은 자료 감사까지 hold다.

| 검토 선택 | 근거와 확인한 한계 | 이번 판단 |
| --- | --- | --- |
| 원 Eq9.23 + 명시적 지원 영역 | 고정 저자 코드와 독립 수식 재현 가능. 작은 수관/온도/CO₂에서는 중단 필요 | **v1 적분 개발에 사용**. 품종 입력 채택/예측 승인 아님 |
| 잎 Eq9.22를 그대로 수관에 적용 | 공개 원식은 있으나 원문이 수관 수준의 낮은 광/CO₂ 문제를 설명 | 미채택. 새 모델 판본·독립 canopy 검증과 품종 적용 근거 필요 |
| 잎별 광/온도·CO₂를 계산해 수관으로 합산 | 별도 층/광 분포·기공과 매개변수 모델이 필요 | 현재 미채택. 근거/권리·실측이 확보된 별도 비교 모델로 검토 |

이 선택은 원식을 모든 재배 조건에 적합하다고 인정한 것이 아니다. 선언된 합성
연구 상태의 적분은 개발할 수 있고, 미지원 실제 초기 수관은 이유와 시각을 남기고
중단한다. 국내 초기 수관의 식 수정/매개변수 검증은 독립 자료 확보와 병행한다.

## 실제 수용과 다음 구현

`backend/tests/test_crop_photosynthesis_domain.py`에서 독립 Decimal 영역과 실제 유량의
경계 양쪽·낮은 CO₂ 상한·L=1/잎 0·일반 초기값 반례를 비교한다. 기대 영역은 제품
함수의 Gamma/유량 출력으로 만들지 않는다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q tests/test_crop_photosynthesis_domain.py tests/test_crop_growth_rates.py
```

새 영역 시험 **32개**와 기존 86개를 합쳐 최종 **118 passed / 0.18초**다. 새 식을
구현한 것이 아니라 기존 거부/계산의 지원 영역을 독립 도출과 대조한 검사다.
경계 표·저자 일반 초기 LAI를 고정 프로필의 60자리 Decimal 계산으로 확인했고,
원 crop JSON/PDF 바이트의 SHA-256도 다시 대사했다. 모델/프로필 바이트는 동일하다.
실제 Axiany forcing/초기기관 QC·국내 보정·독립 작기는 여전히 미확보다.
추가한 A=0의 실수 경계 사례는 냉 수관의 구간·20°C의 동화 0·온 수관 거부를
확인했다. 이 경계는 실수로 평가된 Ci/Gamma를 기준으로 하며 정확한 실수 영역을
넓히지 않는다. 추가 시험의 최초 실행은 잘못 옮긴 시험 본문에서 `NameError`로
1개 실패/117개 통과였고 시험 배치를 바로잡아 위 최종 결과를 확인했다.
최종 링크/진행 검사는 새·수정 로컬 링크 26개, 기존 작업 체크 81개 중 증거가
생긴 적용 영역/이미지 입력 2개만 변경했음을 확인했다. 요청한 네 문서의 의존성과
G2/G3a/G4 경계를 대조했고 `git diff --check`도 통과했다. 원식 유량 코드/프로필은
변경하지 않았다.

다음 코드 단계는 `crop-growth-integration`이다. 솔버/UTC 사건·양수성/고갈·
누적 탄소 수지·수렴·고정 입력 재실행과 실패 단계/시각을 먼저 확정한다.
이 정책 수용은 국내 자료 0건·전체 G1/G2/G3/G4 hold를 바꾸지 않는다.
