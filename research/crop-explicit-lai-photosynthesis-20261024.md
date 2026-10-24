# 명시 잎 면적지수의 광 동화 부품 — 2026-10-24

상태: **연속 결합 부모의 순간 광 동화 자식만 수용**했다.
[설계/후속 순서](../contracts/crop-geometry-carbon-coupling-research-v1.md),
[API 계약](../contracts/crop-explicit-lai-photosynthesis-v1.md), [구현](../backend/app/crop_explicit_lai_photosynthesis.py),
[검사](../backend/tests/test_crop_explicit_lai_photosynthesis.py), [기계 근거](artifacts/explicit-lai-photosynthesis-20261024.json).
기존 SLA 기반 탄소 모델/프로필·저장 결과와 사용자3D/서버/DB·키는 유지했다.

## 모델 판단과 구현

[1차 대조](continuous-leaf-carbon-primary-sources-20261024.md)는 S1의 일정 SLA closure와 LAI 광학 항을 구분했다.
S3 pp6–7은 기관 면적/biomass의 별도 계산 사례지만 우리 탄소·열 feedback의 승인이 아니다.
부모도 원 p6/7/15를 직접 대조했다. p15의 향후 세 변수 분리 제안은 pp6–7과 표현상 긴장이 있어
독립 면적/생체량/길이 전체가 이미 검증됐다는 뜻으로 바꾸지 않았다. 원 note의 잎/절간 혼동은 확인되지 않았다.

기존 모델 A의 권위는 그대로 유지한다. B/C의 연속 모델을 승인하는 대신, 새 연구 함수에서 명시 LAI를 받아
원 광 동화 helper만 평가했다. 기존52개 parameter/원식·PAR0/0LAI/낮은CO2 적용 한계를 유지했다.
leaf mass를 LAI/SLA로 만들어 전체 탄소 함수를 호출하지 않는다. 재고/미분·분배/수확·열/경제를 생성하지 않는다.
원 raw 입력 SHA와 정규 입력/코드/프로필/component SHA, P와 Γ/J 진단을 기록한다.
이 값은 명시 합성 입력의 조건부 산술이고 실제 전체 수관/생산량이나 새 hybrid의 유효성이 아니다.

## 통과한 검증

- **RED:** 새 모듈이 없는 상태의 import 오류를 실제 확인했다.
- **고유254검사:** 새136와 기존 탄소 유량86/광합성 domain32=118이다.
  [독립 oracle](crop-explicit-lai-photosynthesis-reference.py)의110자리 Decimal은 app/helper를 import하지 않고
  별도 광 호흡 차감·직접2차식 전자전달 계산으로 [96사례](../fixtures/crop-explicit-lai-photosynthesis-reference-v1.json)를 만들었다.
  82수용/14영역 보류, 기존4유량의 P/진단 동일, 낮/밤·0/작은 LAI·낮은CO2 상한/양쪽 경계,
  unit/타입/비유한·원 raw/정규 hash/출력 alias·buffer/LAI 독립성을 확인했다.
- **fresh96사례:** 원 참조 fixture를 byte 단위로 재생성했다. P/Γ/J의198개 수치와100개 정확0을 대사했고
  최대 상대 차이는5.50211166704629e-16, 사전 한도5e-12 이하였다.14회 원 domain hold는0으로 대체하지 않았다.
- **원 저장 합성 자료의 조건부48건:** lifecycle 두 root/24원 시점의 현재 면적을 명시 자체 합성 floor0.5m²로 환산했다.
  각 시점에 기존 **별도 소프트웨어** forcing 사례0/3을 각각 적용해28수용/20원 domain hold를 독립식과 대조했다.
  그 forcing은 같은 작물의 관측/기온→수관 대체가 아니며 면적·forcing을 통과시키려고 보정하지 않았다.
  추적 목록/분모·forcing의 실제 수관 권위가 생긴 것은 아니다. 원 UTC/정확 초/result SHA와62blob bytes/메타데이터를 보존했다.
- **실행 경계:** optical helper144회(96+48), 전체 carbon RHS/기관·생애 advance/적분·DB/CLI/network/파일 쓰기0,
  FD 보존을 확인했다. 허용한 두 광학 모듈/기존 readonly reader 외 crop module import는 거부했다.
- **WSL:** .25초 샘플/512MiB PID·합1GiB/600초/로그4MiB를 유지했다.
  집중254는 PID peak91,918,336/합537,759,744bytes, fresh는 합488,693,760bytes,
  원2,966항목/검사 전후 source·4root 생존/감독FD4→4/소유 잔류0을 확인했다.
- **미실행:** 전체 backend/호스티드 CI·브라우저 시험, 새 C/50과실 RHS·열 경계·연속 궤적/재개,
  실제 농장/품종·현장/미래/추천·배포 관문. 이전 web CI는 그 UI commit의 증거로만 유지한다.

## 실제 모델과 다음 작업

부모 native CLI는 gpt-6.1-sol/xhigh, context2026-10-24T04:35:59.972Z와 raw LF SHA
`81628c328dbffaf7a324b5ee944f23b8c154f63cc34203c8a5d2887e8a07b5a7`를 기록했다. 재귀 CLI0이다.
research 스킬의 실제 자식 spawn도 같은 모델/effort/fork none이며 부모가 제안과 원문·현재 코드를 대조했다.
새 매개변수·원 측정·자료/관문 승인0이다. 원문 게시/직접 수신/hash/미확보 available_at/권리는 위 조사에 있다.

다음은 **명시 LAI의 P를 기관/buffer·50과실 RHS에 한 번 결합**하는 것이다. 기존 RHS를 부른 뒤 덮어쓰면
옛 SLA domain과 중복 P가 남을 수 있어 호출/수지 경계를 먼저 분리한다. 같은 LAI에서는 기존 결과와 일치하고,
다른 LAI에서는 독립 C/N 수지와 고갈/domain hold를 검증한다. 그 뒤 면적 기반 열 경계→짧은 연속 구간/정확 사건/재개다.
출현 질량·관리 C·공급 제한·실제 전체 수관/품종과 독립 검증이 해결되기 전 전체 작기나 예측/추천으로 표시하지 않는다.
관리 SourceRecord/현재 농장 실행과 국내 자료 확보는 병행한다. 원 측정/미사용 독립 국내 작기0·첫 국내 품종 미확정이다.

앞의80–155집중분은 위 조사/설계·순간 부품의 실적으로 갱신하며 연속 부모 완료로 처리하지 않는다.
다음 C RHS는 호출/단위 분해20–35 + 최소 조립25–45 + 독립 C/N 참조/회귀25–45 + 기록10–20 =
**80–145집중분**, 낮은 신뢰 추정이다. 후속 열/전체 연속 구현·실제 자료 획득/검증·전체 제품 완료 시간은 포함하지 않는다.
전체 완료일과 생산/자원·경제/추천/R2/G0–G4는 미정/미완료다.
