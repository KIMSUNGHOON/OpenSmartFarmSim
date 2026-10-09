# 첫 작물 탄소 유량 모듈 — 2026-10-04

상태: **순수 유량 계산의 로컬 소프트웨어 수용**. 시간 적분·저장 Run·성장 3D·
품종 보정·현장/미래 예측은 아직 수용 전이다. [계산 계약](../contracts/crop-growth-research-v1.md),
[모델 조사](crop-tomato-model-baseline-20261004.md)를 따른다.

## 구현과 사용자가 확인할 결과

[crop_growth_rates.py](../backend/app/crop_growth_rates.py)는 고정 프로필 바이트와
단위/출처 ID를 가진 상태·수관/PAR/CO₂·명시적 제거 유량으로 광 동화·기관 분배·
생장/유지 호흡·기관 변화율·잎 면적·탄소 잔차를 계산한다. 입력을 적분하거나
승인 Run을 발급하지 않는다. 출력 범위는 `software_research_only`다.

[연구 계산 결과 파일](artifacts/crop-growth-rates-reference-20261004.json)에 합성 사례
4개의 입력·유량·단위·잔차와 profile/code/input 해시를 저장했다. 네 사례는 관측된
Axiany 생산량/생장이나 독립 검증 자료가 아니다. 다음 생산 모델을 위한 수식 구현의
참조 사례이며 `run_id`를 만들지 않는다.

| 합성 수식 사례 | 광 동화 | 생장 호흡 | 탄소 수지 잔차 |
| --- | --- | --- | --- |
| source-initial-day | 0.048231512373808155 | 0.050119043565052604 | −4.77×10⁻¹⁸ |
| night-with-removal | 0 | 0.13922903214090876 | 0 |
| cool-canopy-day | 0.5473591257684907 | 0.07153363781415364 | 0 |
| warm-canopy-day | 0.6638107538096066 | 0.14555452337082514 | 0 |

표의 단위는 모두 **mg CH₂O/m² floor/s**다. 과실의 생과 kg·전력 사용·이익과
같은 양이 아니다. source-initial-day의 상태 값은 일반 구현 초기값을 참고해 명시적으로
작성한 합성 입력이며 실제 품종의 초기 상태가 아니다.

## 고정 근거와 수식 대조

[참조 프로필](../fixtures/crop-growth-reference-parameters-v1.json)은 고정 원문에서
필요한 **const 35개·식 내부/변환 상수 17개, 합계 52개**를 기록한다. 기존 연구 등록부의
39개 const 중 자동 적엽/수확·최대 잎 등의 4개는 이 kernel에서 사용하지 않는다.
수확·적엽·줄기/뿌리 제거는 명시적 외부 탄소 유출이며 새 관리/수확 규칙을 만들지 않는다.
CO₂ 보상점·평활 분배/온도·고정 RGR 가정의 범위는 계약에 기록했다.

52개 값/식 내부 상수의 원 JSON 경로를 실제 원문 바이트와 대조했다.
Q10의 온도 간격 10°C는 원식의 `0.1` 지수 계수의 역수임을 별도 기록한다.
`cRgr` 시간 s·CO₂ 비율의 무차원·CH₂O/면적 차원 정정과 원 학위논문의 근거를
보존한다. [GreenLight BSD-3-Clause-Clear 원 고지](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt)의
바이트도 원 라이선스와 동일하다.

프로필 SHA-256은
`d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca`다.
프로필 바이트 변경·잘못된 타입/단위·출처 생략·비유한/음수·지원 범위 밖 값은
거부한다. 참조 프로필이 G0 승인이나 품종 보정을 뜻하지 않는다.

## 실제 검증

기존 CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`에서 실제 turn context
`2026-10-04T09:25:53.843Z`의 **gpt-6.1-sol / xhigh**를 확인했다.
재귀 CLI를 실행하지 않았다. 이전 goal 턴은 조사·계획·수용 증거의 실제 변경이며,
이번 턴은 다음 코드 작업을 구현한 진행이다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q tests/test_crop_growth_rates.py
```

RED는 `app.crop_growth_rates` 부재로 수집 오류였고, 최종 **86 passed / 0.12초**다.
처음 PYTHONPATH 없는 명령의 `app` import 오류도 확인해 실행법을 수정했다.
수정 뒤 실패 원인이 대상 모듈 부재임을 재확인한 다음 구현했다.

- [독립 참조 사례](../fixtures/crop-growth-reference-cases-v1.json)는 제품 모듈을 import하지
  않은 60자리 Decimal의 원식 계산이다. 원문의 차감형 근/평활 식을 사용하고 제품은
  안정형 근·`expm1`·등가 평활식을 사용한다. 4개 사례 **60개 수치 대조**를 통과했다.
- 비영 참조의 최대 상대 차이는 **1.379×10⁻¹⁴**다. 절대 차이는 결과 아티팩트에서
  단위별로 기록한다. 수치 허용 예산은 생물학적 정확도 기준이 아니다.
- 야간/지원되는 잎 0, 극한의 연속성·약한 광량의 양의 동화/비례, 명시적 제거와
  탄소 수지, 고갈·잘못된 보상점, 모든 입력 수치의 비유한/음수/타입과 단위·범위
  거부, 프로필 불변/미확인 바이트 거부·입력 비변경과 재실행 해시를 확인했다.
- `git diff --check`, 원문 52개 매개변수/상수·라이선스 동일 바이트,
  이미지 검사기의 실제 probe Python 구문 검사도 통과했다.
- 최종 검토에서 새/수정 로컬 링크 15개, profile/code/result 해시의 연결과 원 고지
  해시를 확인했다. 기존 작업 체크 79개 중 증거가 생긴 `crop-growth-rates`만 변경했다.
  독립 참조 시험부터 수식·입력 거부·불변 입력/해시·순수 모듈 경계와 반복 계산 비용을
  검토했고, 새 의존성이나 외부 호출은 없다.

[후속 적용 영역 정책](crop-photosynthesis-domain.md)은 새 32개/기존 86개의 합계
118개/0.18초로 수용했다. 새 kernel의 전체 호스팅 회귀는 아직 미확인이다.
[실제 Docker 프로필/고지 패키징](crop-rate-image-inputs-implementation.md)은 `207e20e`의
hosted 검사/로그·정리로 수용했다.
로컬 Docker Engine이 없어 이미지를 기동하지 않았고, 기존 WSL PostgreSQL을
사용하거나 추가 DB/장기 프로세스를 띄우지 않았다.

## 새로 확인한 모델 한계와 다음 단계

원 학위논문 p249~250 Eq9.23의 Gamma는 LAI 역수에 의존한다. 아주 작은 LAI에서
온도에 따라 음수 또는 주변 CO₂보다 커질 수 있다. kernel은 그 영역을
`COMPENSATION_POINT_HOLD`로 거부한다. Tcan=20°C의 잎 0 광합성 극한과
야간의 동화 0만 확인했으며 모든 온도의 잎 0 연속성을 주장하지 않는다.
[원 학위논문](https://edepot.wur.nl/170301),
[고정 저자 구현](https://github.com/davkat1/GreenLight/blob/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json).

평활 분배가 빈 버퍼에서도 작은 유출을 만들어 음의 상태로 향할 수 있으므로
`DEPLETED_STATE_HOLD`를 유지한다. **crop-photosynthesis-domain**에서 작은
수관의 원식/대안을 검토해 지원 영역 유지/영역 밖 중단을 수용했고, 적분에는 고갈·관리 사건·수렴/수지의 별도
수용을 둔다. 임의 clip으로 동작을 이어가거나 원 식을 조용히 바꾸지 않는다.

기존 Docker 허용 목록이 새 프로필/라이선스를 제외하므로 **crop-rate-image-inputs**의
최소 3파일 변경을 수용했다. 고정 프로필/원 고지의 포함·해시와 관련 없는 fixture/
라이선스 제외를 실제 hosted build로 확인했다. 이 변경은 새 작물 코드의 필수 입력/
재배포 고지 경로에 대한 보완이며 결합 원천 운영 조립을 재개한 것이 아니다.

실제 Axiany forcing/초기조건/관리 QC·국내 자료 동의/독립 작기는 남아 있고 국내
확보는 여전히 0건이다. 전체 G1·국내 G2·미래 G3a·추천 G3b·공개 G4는 열지 않는다.
