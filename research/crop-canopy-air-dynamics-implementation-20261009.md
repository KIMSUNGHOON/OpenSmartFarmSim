# 고정 잎 면적의 수관·공기·수증기 동적 계산 수용

2026-10-09. core `ec18ea64393b1c1f3f62ab1e0a551dbe0b630940`.
[인터페이스 조사](crop-climate-interface-audit-20261009.md),
[새 결합 단계/첫 자식 계약](../contracts/crop-climate-coupling-v1.md),
[실제 종료·수치·자원 기록](artifacts/crop-canopy-air-dynamics-reference-20261009.json)을 연결한다.
완료 범위는 **짧은 합성 고정 LAI의 세 상태 동적 계산**이다.
전체 작물 생장 피드백·온실/생산 예측·실시간 UI 수용은 아니다.

## 산출물과 계산 경계

[모듈](../backend/app/crop_canopy_air_dynamics.py)은 별도 수관 온도·공기 온도·바닥면적당
수증기 질량을 같은 RK4 stage에서 계산한다. 기존 순간식 E/H/LE를 재사용하고,
수관 현열에서 H+LE를 빼며 공기 현열에는 H만 더한다. 수증기에 L*m_v를 저장한다.
기존 열 v1의 공기+수관 합성 열용량/잠열 차감을 다시 사용하지 않았다.
수증기압은 새 질량과 기온으로 매번 유도하므로, 고정 압력의 임의 애니메이션이 아니다.

LAI·잎 열용량·V/A·용량용 밀도·기공 저항·수증기 기체 상수와 세 외부 forcing은
모두 명시 입력이다. 새 계수 기본값·시설/품종 채택은 없다.
fixture의1200은 원 capLeaf 예와 같은 **합성 시험 값**,461은 명시 합성 기체 상수 가정이다.
원 R/mWater 비의 채택이나 국내 농장 계측으로 표시하지 않는다.
수관 물은 계산하지 않는 외부 공급 경계이며, 증산을 급액/구매 용수로 바꾸지 않는다.
음의 E는 원식의 역교환 수학 시험이며 잎 결로/액막 모델이 아니다.
bulk 불포화만으로 차가운 잎/커버의 결로 부재를 주장하지 않는다.

사용자는 [실제 합성 결과 JSON](artifacts/crop-canopy-air-dynamics-reference-20261009.json)의
`short_synthetic_results`에서 네 사례의 입력·60초 종료값·누적 전달·수지 잔차를 확인할 수 있다.
예를 들어 **warm 합성 사례**의 수관20→16.6999589414°C, 공기18→17.9844329671°C,
수증기0.04→0.0432631919586kg_water/m²_floor는 외부 열0의 축소 계산 결과다.
실제 작물의 관측/예측 값으로 해석하지 않는다. 새 모델의3D/API/DB 연결은 아직 없다.

## 통과한 검증

| 단계 / 원 도구·실제 종료 | 결과 |
| --- | --- |
| RHS / 98246·0 |24개/pytest0.09초, controller0.558초. 독립 Decimal RHS·방향/저장·압력·단위/hold |
| 짧은 적분 / 45222·0 |56개/0.20초, controller0.561초. 네60초 사례·공동 stage·정상/역교환·hold |
| 최종 같은 core 판본 / 62863·0 |새56+기존230=고유286개/2.04초, controller2.348초 |
| 별도 감사 / 2945·0 |0.814초. 참조 bytes 재생·기존12source핀·고지·원 종료/원본/자원 보존 |

최종56개에는3사례 각각 상태3개와 누적 E/H/LE의 dt=4/2/1초 대조를 포함한다.
독립 Decimal80의 dt=0.25초 해 대비 오차는 매 반분에서 최소**16.359배** 줄었으며
사전에 고정한8배 조건을 통과했다. 수지 잔차만으로 적분 정확도를 인정하지 않았다.
독립 RHS36수치와 dt1 종료 상태/누적 전달24수치를 대사했고 참조 생성기는 app을 import하지 않는다.
같은 고정 JSON bytes를 별도 재생성해 정확한 일치도 확인했다.

각 저장소의 현열/수증기 장부와 결합 에너지 잔차의 최대 절댓값은
**1.0368239600211382e-10J/m²_floor**, 수증기/외부 물 경계 잔차는
**2.6725583551767684e-17kg_water/m²_floor**다.
사전1e-7J/1e-13kg 기준 안이며 현장 정확도의 증거가 아니다.
등온의 명시 균형 외부 forcing에서는 상태를 정확히 유지했다.
빈 수관·음수 질량·bulk 포화·stage 온도 이탈·비유한/overflow/underflow·수치 정체는
hold하고 마지막 확정 상태를 보존한다. clamp/임의 온도·LAI 대체는 없다.

명시 소유+보호 트리의0.25초 관측 RSS는 단일 최대147,255,296bytes,
합321,839,104bytes로512MiB/1GiB 안이다. controller/별도 감사 FD4→4,
소유 비좀비0·현재 source1,671개·기존 검토 코드/프로필12개·원본2,148항목을 보존했다.
기존 고정 미리보기 source/배포 파일·원 controller/서비스/PG 생존과 frontend200을 유지했다.
이것은 해당 작은 소유 실행의 관측이며 일반 서비스 용량 수용이 아니다.

```sh
PYTHONPATH=backend nice -n 19 backend/.venv/bin/python -m pytest -q --tb=short \
  backend/tests/test_crop_canopy_air_dynamics.py backend/tests/test_crop_canopy_exchange.py \
  backend/tests/test_crop_growth_rates.py backend/tests/test_crop_growth_integration.py \
  backend/tests/test_thermal.py backend/tests/test_thermal_parameter_fixture.py
```

조사·설계·원문 검토는 실제 native CLI `gpt-6.1-sol / xhigh`, 재귀0회다.
부모의 실제 context는2026-10-09T14:15:13.666Z, 원 LF 포함 SHA
`809bf52d2cf604a3dc7e1a19444ef86e676ca7190df70c87619e96e9cb1f5ad6`이며
background 조사자의 unavailable metadata와 구별해 공개 기록에 남겼다.
새 패키지·전체 DB/API/브라우저·전체 작기 RHS/writer는 실행하지 않았다.
이번 자식의 hosted CI는 미수용이며 앞선4b7fe6f 회귀가 진행 중이다.

## 다음 단계와 외부 의존성

1. 잎 면적 변화/적엽에 따른 **열용량과 물질 현열 운반 정책**을 먼저 확정한다.
   `Ccan*dTcan`만 대사하며 변하는 Ccan을 무시하지 않는다.
2. 새 공동 RHS/짧은 적분에서 현재 crop state→LAI→교환과
   동적 Tcan→생장/T24/Tsum을 같은 stage로 연결한다. 기존 Fraction 고정 forcing clock과
   121상태 checkpoint는 새 동적 모델에 재사용하지 않는다.
3. 복사/CO₂·기공·온실 경계와 새 연속 계산/저장·같은 UTC3D를 나눠 수용한 뒤
   물/양분·구매 에너지→사용자 실행/Decimal 경제로 이어간다.

첫 동적 자식은2026-10-09 완료했다. 후속은 위 정책/모델 입력·수치 경계를 확정한 뒤
짧은 프로그램 비용을 실측해 일정에 반영한다. 이60초 실행2.348초를 전체 작기나 제품 완료일로
외삽하지 않는다. 실제 품종 입력·농장 작물 Run·국내 독립 자료는0건이고,
수관/환경·급배액/에너지/수확/경제의 독립 자료 확보일은 미정이다.
G0–G4/생산·자원 예측/미래 마진/추천·배포 hold와 전체 goal을 유지한다.
`localhost:5173`은 완료 전체 생장·수확의 저장 재생을 계속 제공하며 실시간 U3는 미구현이다.
