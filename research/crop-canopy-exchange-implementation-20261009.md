# 수관·공기 순간 교환 계산의 로컬 수용 — 2026-10-09

`crop-climate-coupling`의 첫 자식 `crop-canopy-exchange`만 완료했다.
[조사·판단](crop-canopy-exchange-baseline-20261009.md),
[원본·권리·CLI 등록부](crop-canopy-exchange-source-register-20261009.json),
[계약](../contracts/crop-canopy-exchange-v1.md),
[원 종료·자원·해시 기록](artifacts/crop-canopy-exchange-acceptance-reference-20261009.json)을 연결한다.
조사/설계는 현재 native CLI `gpt-6.1-sol / xhigh`에서 수행했고 CLI 재귀 실행은 없다.

## 확인 가능한 산출물

- [순수 계산 모듈](../backend/app/crop_canopy_exchange.py): 명시 LAI·수관/공기 온도·수증기압·
  용량용 밀도·기공 저항에서 부호 있는 E/H/LE와 단위·입력/모델/프로필 해시를 계산한다.
- [고정 참조 프로필](../fixtures/crop-canopy-exchange-reference-parameters-v1.json):
  고정 GreenLight 원문 6식·9계수/식 상수·원 단위와 프로젝트 차원 해석을 기록한다.
- [독립 Decimal 80자리 참조 생성기](crop-canopy-exchange-reference.py)와
  [5사례·35수치](../fixtures/crop-canopy-exchange-reference-cases-v1.json):
  증발/역방향·빈 수관·등온·큰 저항 사례다. 생성기는 app 구현을 import하지 않는다.
- 국소 전달은 물 −E/+E, 현열 −H/+H, 수관 열 −LE/수증기 에너지 +LE다.
  실제 저장소/온도를 적분하거나 전체 온실의 수지를 입증한 결과가 아니다.

## 통과한 검증

1. 첫 집중 실행은 **34 passed / 1 failed, 종료1**이었다. 큰 유한 입력에서 H=+inf,
   LE=−inf가 되어 `fsum`이 `ValueError`를 내는 경로가 선언한 `NUMERIC_HOLD`로 변환되지 않았다.
   수치 예외를 변환하되 이미 선언한 hold 원인은 보존하도록 수정했다.
2. 수정 후 집중 **35 passed / 0.09초, 종료0**과 기존 생장/적분·열 계산
   **195 passed / 1.75초, 종료0**을 확인했다.
3. 최종 같은 판본의 집중+회귀 명령은 원 도구 **25915 종료0**, **230 passed / pytest 1.85초**,
   전체 명령 **2.126초**, child max RSS **56,823,808bytes**였다.
   이 값은 이 순수 시험 프로세스의 관측이며 동시 전체 producer/UI를 포함한 운영 용량이 아니다.
4. 35개 독립 참조 수치를 상대 `2e-14`/0은 정확한 0으로 대조했다.
   역방향 부호·국소 전달 소유·LAI/밀도 선형성·저항 효과·현열 방향·빈 수관 0,
   canonical 재현/입력 불변, 단위·닫힌 입력·프로필 변조·온도 경계·비유한/overflow/underflow 거부를 확인했다.
5. 사설 보존 원문/고지 SHA, 6식과 9계수의 포인터·literal/원 단위를 대사했다.
   참조 생성기를 별도 Python으로 실행해 고정 사례 파일과 bytes가 정확히 같음을 확인했다.
   진행 중인 producer의 고정 3개 main 파일을 isolated 소스와 비교해 동일함을 확인했다.

```sh
PYTHONPATH=backend nice -n 19 backend/.venv/bin/python -m pytest -q --tb=short \
  backend/tests/test_crop_canopy_exchange.py \
  backend/tests/test_crop_growth_rates.py backend/tests/test_crop_growth_integration.py \
  backend/tests/test_thermal.py backend/tests/test_thermal_parameter_fixture.py
```

전체 백엔드/DB/API/브라우저 시험은 이 자식에서 실행하지 않았다.
새 패키지·worker·API·DB·실행 중인 UI 장면 연결은 없다.
완료 처리한 것은 합성 입력의 순간 교환 산술이다. 원본 공개 시각/`available_at` 미확인은
결정 시점의 실제 자료 채택 hold로 유지한다.

## 남은 작업·외부 의존성

전체 기후 결합에는 독립 수관/공기 열용량·복사/CO₂·기공 폐쇄·물/수증기 에너지 저장소의
새 경계가 필요하다. 기존 단일 온도 열 v1과 잠열을 이중 적용하지 않는다.
수관 온도를 공기 온도로 대체하지 않으며 LAI=0의 수관 온도 ODE 특이점도 별도 해소해야 한다.
급액/재순환·양분·구매 용수/에너지·Decimal 비용은 이 계산에 포함되지 않는다.

국내 독립 수관/환경·급배액/에너지 계측 자료 확보는 개발과 병행하고 현재 0건이다.
실제 품종/농장 작물 Run도 0건이며 G0–G4·생산/자원/미래 마진/추천 hold를 유지한다.
통합 순서는 전체 부모 최종 감사 → 전체 수확 writer/조회·대표 3D → 기후 결합 →
물/양분·구매 에너지 → 사용자 실행/경제다. 이 순수 자식은 전체 부모 실행과 독립 개발했다.
전체 producer의 원 종료·게시/복원·후속 모듈과 자료 확보일이 미확정이므로 제품 완료일은 갱신하지 않는다.
