# 과실 50구획의 순간 이동 — 2026-10-05 KST

상태: **고립된 순간 이동의 로컬 소프트웨어 수용**.
[개발 계약](../contracts/crop-fruit-cohorts-v1.md),
[원식/계수와 보류](crop-fruit-cohorts-baseline.md),
[입력/출력·검증 해시 증거](artifacts/crop-fruit-transport-reference-20261005.json)를 함께 읽는다.
실제 Axiany 전체 작기·착과/기관 생장·수확 생과 kg·자원/경제/추천의 수용은 아니다.

## 실제 판단·구현과 사용자 산출물

동일 CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn context
`2026-10-04T15:56:17.675Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
이 세션에서 원식/단위/수치 정책을 검토하고 구현했다. 재귀 CLI는 없다.
독립 제품 runtime CLI/G1 실행 증거는 아니다.

[crop_fruit_transport.py](../backend/app/crop_fruit_transport.py)는 원 Vanthoor
9.31/9.32/9.34의 piecewise h=1 생식기 범위를 받는다. 고정 참조 프로필의
50구획과 온도 계수 2개, 명시된 연속 과실 수/탄수화물 배열·평활 온도/온도 합으로
순간 이동률, N/C 변화율과 마지막 구획 유출, 개수/탄소 수지를 계산한다.
온도 합이 원 onset을 초과하는지만 검사하며 시간을 적분/예측하지 않는다.

사용자는 증거 JSON의 **15개 합성 사례별 50구획 유량/변화율·합계·두 수지**를
읽을 수 있다. 마지막 유출은 terminal 연구량이며 실제 수확/생과/판매로 표시하지
않는다. 개별 열매 모양/색·실제 정수 과실 수·기존 3D는 만들거나 변경하지 않았다.
새 모듈은 원 전체 배분의 보존/W1/초기/gate 문제를 해결했다고 주장하지 않는다.

[고정 매개변수](../fixtures/crop-fruit-transport-reference-parameters-v1.json)의 SHA-256은
`09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070`이다.
원 계수 3개를 연구 등록부와 대사했고 원 PDF hash/시각·권리·단위·검토자를
보존했다. 일반 참조이며 Axiany 보정 프로필은 아니다. 이 파일이나 원 출처/단위/
고지 bytes가 바뀌면 새 검토/판본 없이 계산하지 않는다. 원문 PDF는 저장소에 없다.

원식의 rDev 적용 근거 17–27°C 중 현재 생장과 공통인 17–23°C를 사용한다.
최대 50개씩/100 quantity와 256문자 ID로 입력량을 제한한다. 타입/단위/배열·
비유한/음수·C>0,N=0·영역 밖·미검토 프로필, 표현 불가능한 양의 이동/변화와
합계 overflow는 명시적 hold다. 질량/계수를 clip하거나 배열/초기 seed를 채우지 않는다.

## RED→GREEN·독립 참조와 수치 반례

먼저 시험/독립 참조를 작성했다. RED는 대상 `app.crop_fruit_transport` 부재로
수집 오류였다. 최초 참조 생성 명령의 작업 디렉터리 오류는 경로를 수정했고,
참조 파일을 생성한 뒤 같은 모듈 부재 RED를 재확인했다.

첫 GREEN은 73개였다. 별도 nearly-equal 사례의 추가로 큰 edge 유량끼리 빼면
작은 구획 변화가 손실되는 **3 failed / 73 passed** 반례를 확인했다.
기대한 작은 변화값과 실제 실패 수치는 해시한 로그에 보존했다.
미분을 `lambda*(이전 상태-현재 상태)`로 평가해 원식과 동등하게 수정했다.
구획 차이가 0이 아닌데 미분이 0으로 underflow되면 hold하는 회귀도 추가했다.

[독립 참조 계산기](crop-fruit-transport-reference.py)는 제품 모듈을 import하지 않는다.
원 계수의 십진 표현과 60자리 Decimal로 17/20/23°C × zero/first/last/multiple/
nearly-equal의 **15개 사례·3,090수치**를 만든다. 입력 상태는 코드에 명시한 수식
검사용 합성이며 현장 관측/초기 기관량이 아니다. 큰 nearly-equal 상태도 반올림
조건을 검사하는 합성 수치 사례이지 재배 범위의 근거가 아니다.
생성 코드를 계획의 4파일에 추가한 이유는 양 계산의 독립성·버전/해시·동일 재실행을
보존하기 위해서다. 두 생성 출력은 byte-identical이며 SHA 연결을 확인했다.

최종 실행:

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_fruit_transport.py tests/test_crop_growth_rates.py \
  tests/test_crop_photosynthesis_domain.py tests/test_crop_growth_integration.py
```

**238 passed / 0.71초**: 새 순간 이동 92개와 기존 생장/적분 146개다.
프로필/값 불변·같은 입력 해시/재실행, provenance/상태 변경의 해시 차이,
0/첫/마지막/빈 중간 구획·스케일, 두 보존/단위·잘못된 타입/배열/quantity/
범위·overflow/edge·미분 underflow 거부를 포함한다.

독립 참조의 최대 비영 상대 차이는 **6.7117e−16**이다. 단위별 최대 절대 차이는
증거 JSON에 기록했다. 약 1e11 규모의 합성 유량에서 1.5259e−5의 절대 차이가
있지만 relative 5e−12/absolute 5e−14 예산을 통과했다. 작은 차감 미분도 같은
독립 검사를 통과했다. 수치 예산은 실제 품종 생산 정확도의 기준이 아니다.
두 수지는 50항 반올림의 ULP 예산 안에서 확인했다.

## 변경 검토

원 이동식/단위·동일률의 telescoping 개수/탄소 수지와 60자리 독립 계산을 대사했다.
작은 차감의 부정확성은 실제 실패 후 수정했다. 입력 구조/범위와 양의 underflow는
명시적으로 거절하며 매개변수 bytes/값과 호출 입력을 바꾸지 않는다.
순수 모듈은 기존 저장/API/3D/호흡 코드에 연결하지 않고 새 의존성을 도입하지 않는다.
계산량은 고정 50구획으로 제한되고 파일/네트워크/로그 부작용은 없다.
미해결 필수 결함은 이 순간 이동 범위에서 발견하지 않았다. 전체 모델·이미지·
hosted 수용은 아래 후속 범위이며 이번 로컬 검토로 merge/게시를 승인하지 않는다.

## 남은 입력·배분/적분·이미지 범위

새 순수 모듈/fixture 외에 프로젝트 의존성·장기 서버·DB를 추가하지 않았다.
합성 해시/검사는 G0–G4를 열지 않고 새 crop-result-v1/Run을 만들지 않는다.
국내 동의/독립 작기는 0건이다. 해외 UTC/면적·수관/초기상태/관리·형식/QC,
전체 작기 처리 한도와 실제 품종·생과 환산은 기존 보류를 유지한다.

현재 Docker 허용 목록은 새 고정 참조 프로필을 제외한다. 해당 파일은 이 계산을
배포 이미지에서 사용할 때 필요한 입력이므로 `crop-fruit-transport-image-inputs`의
최소 허용/해시·실제 loader와 제외 검사를 다음으로 둔다. 로컬 Docker Engine은
없고 실제 이미지 수용은 기존 hosted CI가 통과한 뒤 기록한다.
현재 `d76410f`의 웹/C0/앱/작성 CI는 성공, 전체 backend 집계는 진행 중이다.
새 순간 이동 판본의 전체 hosted 회귀는 아직 실행 전이며 이 로컬 시험과 구분한다.

다음 핵심 단계는 `crop-fruit-allocation-policy`: 원 9.36/9.37의 보존 문제와
W1 Gompertz 경계/초기 seed·빈 sink·gate의 원/수정 정책을 근거·새 판본·
독립 수치로 결정한다. 이후 착과/배분·구획 적분/사건을 기존 기관/버퍼 수지와
연결한다. 순수 개발은 국내 자료 접근을 기다리지 않고 그 확보와 병행한다.
