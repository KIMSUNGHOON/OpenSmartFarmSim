# 과실 구획의 수요·순간 결합 — 2026-10-05 KST

상태: **문헌식 수요와 명시적 착과 구획의 로컬 소프트웨어 수용**.
[v2 계약](../contracts/crop-fruit-cohorts-v2.md),
[실제 입력/출력·검증 해시](artifacts/crop-fruit-cohort-reference-20261005.json)를 확인한다.
이는 전체 생장/시간 적분·관리 사건·실제 Axiany 작기/수확의 수용이 아니다.

## 실제 출처와 판본

동일 CLI `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 context
`2026-10-04T17:08:21.845Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
현재 CLI에서 조사/설계와 구현·원식/수치 판단을 수행했으며 재귀 CLI는 없다.
독립 제품 runtime CLI/G1 검증 증거로 취급하지 않는다.

[원 Vanthoor PDF](https://edepot.wur.nl/170301)는 기존 private cache의 실제 bytes를
불변 [원천 등록부](crop-fruit-source-register.json)의 hash와 다시 대사했다.
9.38–9.42/9.45·Table9.1의 등록된 14개 값/단위와 9.45의 온도 기준/간격 2개를
[고정 프로필](../fixtures/crop-fruit-cohort-reference-parameters-v1.json)에 연결했다.
profile은 5,273 bytes, SHA는
`b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb`이다.
원 URL·publication/available/retrieval·권리·raw hash·검토자를 유지했다.
원 PDF/전체 문장을 저장소에 복사하지 않았고 실제 품종 계수 채택은 없다.

새 코드 판본은 `explicit-entry-fruit-cohort-rates-research-v1`이다.
기존 고정 이동과 별도 보존 배분 함수를 호출하며 같은 개발 계수를 대사한다.
원/현재 파라미터·배분/이동 프로필과 입력 hash를 결과에 연결한다.
기존 v1 계약·배분 정책/고정 참조/저장 결과의 bytes는 수정하지 않았다.

## 계산과 사용자 산출물

`crop_fruit_cohorts.py`는 고정 Gompertz의 구획 대표 나이/잠재 생장률과
N×GR의 수요를 계산한다. 잠재 탄수화물 과중이나 대표 나이는 실제 과중/숙기가 아니다.
전체 유입 F와 명시적 S/W1을 기존 보존 배분으로 분배하고 50개 N/C 이동에
구획 유지 호흡을 한 번 차감한다. 과실 성장 호흡과 해당 buffer debit을 별도로
반환해 후속 전체 기관 결합이 기존 차감에 다시 더하지 않도록 계약했다.

RGR은 50개 명시 입력이다. 원 공개 구현의 근삿값이나 기존 고정 값을 생리 측정으로
섞지 않는다. 합성 varying RGR도 코드에 명시한 수식 입력이며 실제 관측/품종 계수는 아니다.
지원 영역은 생식기 온도 합>0과 공동 T24=17–23°C다. 닫힌 입력/단위·길이·
유한/비음수·C>0,N=0·미검토 프로필과 empty-sink/entry budget은 각각 hold다.
입력 origin 선언은 G0 승인이 아니다.

사용자는 증거 JSON의 **24개 합성 사례**에서 50개 잠재 생장률/수요·배분·유지
호흡·N/C 미분과 최종 연구 유출, 성장 호흡/debit·세 수지를 확인한다.
상태를 시간 전진하거나 과실 3D/생과 수확/판매를 만들지 않는다.

## 검증과 검토

먼저 제품 모듈 부재의 RED를 실제 exit 2로 확인했다. 첫 GREEN은 75개/0.18초였다.
닫힌 block/metadata와 성장 호흡 underflow/buffer debit overflow를 추가한
최종 집중 결과는 **401 passed / 0.89초**다. 새 구획 86개·기존 작물 315개다.
하나의 `nice -n 10` pytest로 실행했고 프로젝트 의존성/서버/DB는 추가하지 않았다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_fruit_cohorts.py tests/test_crop_fruit_allocation.py \
  tests/test_crop_fruit_transport.py tests/test_crop_growth_rates.py \
  tests/test_crop_photosynthesis_domain.py tests/test_crop_growth_integration.py
```

[독립 계산기](crop-fruit-cohort-reference.py)는 제품 import 없이 60자리 Decimal로
17/20/23°C × 0/균일/다중/진입만 × 0/명시 varying RGR을 계산했다.
**8,592개 수치**를 실제 제품 출력과 대사했고 최대 비영 상대 차이는
**2.0736e−15**였다. 생성 2회는 byte-identical이다.
단위와 세 수지·0/양의 호흡·성장 차감 한 번, 입력/프로필 불변·재실행/hash,
타입/양/형태/범위·overflow/양의 maintenance/growth underflow를 시험했다.
기대값을 제품 함수로 생성하지 않았다.

기존 순간 이동/배분의 공용 진입 함수를 재사용하고 source/profile의 개발률을
대사했다. 구획별 3항 미분은 fsum, 작은 호흡 인자는 expm1로 평가한다.
동일한 50구획 반올림 예산 안에서 개수·탄소·buffer 경계를 확인했다.
독립 대조의 오차 예산과 이 ULP 예산은 실제 농장 예측 정확도가 아니다.
문헌식·단위/범위·음의/0/양의 입력, 정책/권리와 결과 hash를 검토했으며 이 순간
범위의 미해결 필수 결함은 발견하지 않았다. 전체 모델/hosted/게시 수용은 별도다.

## 다음 코드와 남은 의존성

다음은 `crop-fruit-cohort-integration`의 전체 기관 결합/시간 적분 계약이다.
기존 fruit 유지 호흡/미분은 구획 값으로 교체하고 총 fruit를 합계에서 한 번 파생한다.
F+성장 호흡의 buffer 차감을 재사용하며 계수/출처가 다른 프로필을 조용히 섞지 않는다.
독립 일정 forcing/해석해·시간 간격 수렴·사건의 N/C 동시 제거·누적 호흡/terminal과
전체 저장/외부 수지·같은 재실행/manifest를 통과한 뒤 새 저장 결과/3D를 연결한다.

현재 문헌 참조 범위의 빈 초기 tail/양의 남은 유입은 실제 hold다. 자동 착과/W1/
RGR·초기 정책과 생식기 이전이 준비되지 않아 전체 작기 시작/예측을 지원했다고
주장할 수 없다. 이는 최종 전체 작기 모델에 필요한 후속 연구/구현이며 독립 자료 확보와
병행한다. 국내 동의/독립 자료는 0건, actual forcing/관리/QC·작기 처리 한도·생과
환산/자원·경제와 G0–G4 보류는 유지한다.

필수 새 cohort profile은 현재 Docker 허용 목록에서 제외된다. 이를 배포할 때는
정확한 한 파일 허용/실제 hash·loader·cases 제외/정리만 보완한다. WSL2에는
Docker Engine이 없으므로 실제 이미지는 기존 hosted workflow로 검증한다.
선행 `78b5d17`은 웹/C0/앱 이미지·작성 CI가 성공했고 전체 backend는 진행 중이다.
새 cohort 코드의 hosted 회귀는 아직 시작 전이다.

### 선행 판본의 전체 CI 완료

이후 `78b5d17`의 전체 backend도 2026-10-04 18:18:37 UTC에 성공했다.
[CI packet](artifacts/crop-fruit-transport-allocation-ci-20261005.json)에 CI 5개와 실제
백엔드 2,840개/별도 UID 4개·여섯 동일 목록/DB·비밀 파일 정리/집계를 기록했다.
각 partition/aggregate의 direct job API 로그를 대사했다. 이 SHA는 transport/배분과
이전 저장/웹의 회귀 증거이며 이 보고서의 새 cohort/기관 코드 수용 증거는 아니다.
