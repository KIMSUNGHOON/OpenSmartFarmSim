# 명시적 착과의 순간 배분 — 2026-10-05 KST

상태: **순수 제품 배분 계산의 로컬 소프트웨어 수용**.
원 [개발 정책/계약](../contracts/crop-fruit-allocation-v1.md)은 `9ee10c6`의 조사 시점
기록이며, 후속 제품 구현 수용은 이 문서와 [실행 증거](artifacts/crop-fruit-allocation-reference-20261005.json)에
남긴다. 정책의 원천/독립 기대값을 덮어쓰지 않았다.
자동 착과·과실 시간 적분/실제 Axiany 수확·자원/경제의 수용은 아니다.

## 변경과 확인 가능한 산출물

계획의 2파일 `backend/app/crop_fruit_allocation.py`와
`backend/tests/test_crop_fruit_allocation.py`를 구현했다.
명시적 총 과실 탄소 유입 F·착과 S·진입 탄수화물 W1와 50개 잠재 수요를 받는다.
각 값은 닫힌 value/unit과 유한·비음수 수치, 상태는 닫힌 input_id/origin/values다.
ID는 1–256문자, origin은 기존 연구 enum이며 이 선언을 실제 자료 승인으로 바꾸지 않는다.

새 판본은 `explicit-entry-fruit-allocation-rates-v1`, 정책 ID는
`explicit-entry-fruit-allocation-research-v1`다. 정책/5개 원천 등록부의 실제 SHA
`edbc67cfe59a61a1573ef5b1f189c548c47a74b996d4ef6221adc663c1cc306a`를 코드/입력
hash에 연결했다. 생물 계수/자동 S/W1·미지 초기조건을 추가하지 않았다.
현재 `gpt-6.1-sol / xhigh` CLI의 실제 context는 `2026-10-04T16:25:20.568Z`이고
세션/재귀 없음은 실행 증거에 남겼다. 제품 runtime CLI 검증과 구분한다.

사용자는 증거 JSON에서 **6개 정상 사례의 50개 탄소/개수 유입과 두 수지**,
4개의 실제 hold·입력/정책/코드 hash를 확인한다. 이것은 순간 유입이며 상태를
적분하거나 수확/생과/잎·열매 3D로 바꾸지 않는다.
첫 구획은 명시된 S×W1만 받는 정책의 생리적 제약도 유지한다.
빈 sink/예산 초과/양의 착과·영 진입 질량을 추정/clip/탄소 환급으로 통과시키지 않는다.

## RED→GREEN와 독립 검증

제품 모듈 부재 RED는 실제 pytest exit 2였다. 첫 GREEN은 73개/0.09초였고,
검토에서 입력의 명시적 필드 접근·values/top-level 닫힘과 모든 스칼라의 hash
결합을 보완한 최종 새 시험은 **77개**다.

```sh
cd backend
env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q \
  tests/test_crop_fruit_allocation.py tests/test_crop_fruit_transport.py \
  tests/test_crop_growth_rates.py tests/test_crop_photosynthesis_domain.py \
  tests/test_crop_growth_integration.py
```

**315 passed / 0.70초**: 새 배분 77개·순간 이동 92개·기존 생장/적분 146개다.
독립 60자리 Decimal의 **600개 유입값/4개 hold**와 실제 제품 출력을 대사했다.
최대 비영 상대 오차는 **5.5511e−17**이다. 입력 불변/같은 재실행·원천/정책과
모든 값 변경의 hash 차이, 스케일, 단위/배열/타입/음수/비유한/닫힘·provenance,
진입 질량 곱/수요 합계 overflow·양의 진입/뒤 배분 underflow를 확인했다.
원천/독립 기대값은 제품 함수를 import해 생성하지 않았다.

뒤 수요는 첫 구획을 제외한 값만 직접 합해 큰 첫 수요의 차감 손실을 피한다.
배분은 `R*(w/D2)`이며 수지 예산은 `2*(50+1)*ulp(F)`/같은 개수 유입 예산이다.
예산 밖·표현 불가능한 양의 유입은 hold다. epsilon/잔차 재배분은 없다.
이 수치 예산을 실제 품종의 예측 정확도라고 보고하지 않는다.

## 검토·전체 CI·다음 한 단계

닫힌 입력/표현 한도와 원/선택 정책·정상/경계 보존을 시험과 독립 값으로 검토했다.
암묵적인 dict 순서에 의존한 스칼라 접근은 명시적 이름으로 바꿨다.
순수 모듈은 50구획으로 제한되고 파일/네트워크/DB/로그 부작용이나 새 의존성이 없다.
기존 API/저장/3D/호흡 코드는 변경하지 않았다. 로컬 범위에서 미해결 필수 결함은
발견하지 않았으며 전체 모델·hosted·merge/게시 수용은 별도다.

선행 `d76410f`는 웹/작성/C0/실제 앱 이미지·Compose와 전체 backend가 모두 성공했다.
전체 backend는 2,671개·별도 UID 4개, 여섯 동일 목록/정리·집계를 확인했다
([실제 선행 CI 증거](artifacts/crop-fruit-predecessor-ci-20261005.json)).
새 과실 코드 판본의 hosted CI는 아직 시작 전이다. WSL2에는 Docker Engine이 없고
로컬에서는 1개 낮은 우선순위의 집중 시험만 실행했다.
새 transport 프로필의 최소 포장은 구현/로컬 loader까지이며 실제 hosted 수용을 기다린다.

다음 핵심 단계는 `crop-fruit-cohorts`의 **순간 결합 계약/고정 Gompertz 수요 계산**이다.
50개 탄소/개수 상태와 이동·배분·호흡/기관과 buffer 경계를 원식/단위/판본으로 고정하고,
W1/S·RGR/초기/관리의 명시 입력과 실제 자동/품종 hold를 구분한다.
원 9.38–9.42의 고정 계산을 독립 수치로 확인한 뒤 작은 구획 시간 적분/사건·수렴/
전체 탄소와 개수 수지·저장 새 판본으로 이어간다. 국내 실측과 처리 한도 계약은 병행한다.
실제 농장 독립 자료는 0건이며 새 실제 crop Run/G0–G4는 만들거나 열지 않았다.
