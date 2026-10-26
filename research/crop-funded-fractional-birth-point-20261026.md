# 분수 시각의 명시적 구조 조달점 — 2026-10-26 KST

**분수 시각의 재료 전이 계산을 구현했습니다.**
[계약](../contracts/crop-funded-fractional-birth-point-v1.md),
[구현](../backend/app/crop_funded_fractional_birth_point.py),
[33개 검사](../backend/tests/test_crop_funded_fractional_birth_point.py),
[검증 JSON](artifacts/crop-funded-fractional-birth-point-20261026.json).
일반 54점의 독립 검증은 통과했으며 별도 512잎 요청 1건은 하위 직렬화 한도로 보류했습니다.
전체 분수 재개/최대 목록 지원·생물학적 출현·실제 줄기 부착·G0–G4/R2 승인을 수용하지 않았습니다.

## 구현 경계와 선택

기존 [조달점](../backend/app/crop_leaf_funded_birth_point.py)의 `_apply_current`는 원 manifest의
`step_seconds * step_index`를 요구합니다. 기존 context/token·dt/index를 꾸며서 분수 시각을 넣지 않았습니다.
[검증된 후보](crop-funded-event-state-20261026.md)를 실제 원본에서 계산한 뒤 새 내부 context에
program·앵커·선택값/시각·이미 적용된 event ID·프로필/code/후보를 불변 bytes로 캡처합니다.
이 버전에는 외부 context 복원이나 farm 서명/보관 권한 승격이 없습니다.

새 점 입력은 원 후보/문맥 SHA·exact 시간·공통 floor와 event/leaf ID·곡선/명시 초기 탄소·
0 나이/양의 F(0)·유입 온도를 요구합니다. 기존의 시간 독립 산술 `_new_leaf`, `_fund`,
`_rounded`, `_quantity`, `_balance`와 RHS를 재사용합니다. 새 생리 계수·기본 종자 질량·SLA 역산은 없습니다.
새 탄소/성장호흡은 기존 buffer에서 차감하고 열용량·현열 유입은 별도 기록합니다.
기존 first107의 buffer/U104 이외 상태와 기존 나이/A/C·앵커/원 prefix·연속/점 장부는 보존합니다.
새 snapshot은 같은 원점/분수 시각이며 정수 step 번호를 만들어 내지 않습니다.

원 source의 과거에 적용된 event와 기존 leaf ID는 재사용할 수 없습니다.
고정된 context에 대한 반복 호출은 같은 계산의 재현이며 바뀐 상태에 두 번 채택하는 의미가 아닙니다.
새 checkpoint의 한 번 채택/새 이력 재생 차단·global 누적/phase/cursor·격자 잔여 전진은 다음 경계입니다.
새 부착 ID는 선언만 기록하며 실제 줄기 ID/출현 근거 검증으로 승격하지 않습니다.

## 검증 결과

- **최종 33검사:** 실제 후보의 root/기존 두 조달 이후 문맥,
  exact 시각·옛 상태/앵커/prefix, 두 RHS 평가, 독립 Decimal 탄소 비용과 copy 보존을 확인했습니다.
  기존 여섯 조건의 실제 whole-grid 점에서 after-program/vector/rates·영수증/유량/장부가
  원 연산과 같았습니다. 잘못된 형식/정책/시간/SHA/floor/수량/중복/자금 부족·늦은 code/권리,
  rehash된 잘못된 program·미확정 after-RHS와 외부 효과를 거부했습니다.
- 실제 분수 시각의 한 512잎 결과는 원 byte cap 안에서 통과했습니다.
  별도 긴 ID의 최대 목록은 하위 cap을 보존한 채 실패하고 원 context가 보존됨을 확인했습니다.
  이는 모든 512잎 조합의 성공 주장이 아닙니다.
- [자체 QA 선언](../fixtures/crop-funded-fractional-birth-point-fixtures-v1.json)과
  [재현·독립 대조 프로그램](verify-funded-fractional-birth-points.py)을 작성했습니다.
  기존 자체 공개 이벤트 값과 기존 온도 시험값을 명시해 사용하며, 새 측정/작물 계수를 채택하지 않았습니다.
  기존 6조건/497파일을 새로 해석하지 않고 재사용했고 private False 패킷을 공개로 바꾸지 않았습니다.
- 별도 프로세스에서 **54점·108잎 영수증·270장부**를 Decimal200/Fraction 식으로 대사했습니다.
  탄소/성장호흡/차감·buffer, 양의 logistic F(0), 같은 floor의 열용량·유입 현열/U,
  기존 상태·앵커/같은 exact 시각과 다섯 점 장부를 확인했습니다.
  새 source context 준비 6회의 RHS246회와 55요청의 현재/후 RHS110회, 합계 **356회**를 계측했습니다.
  과거 advance/prepare·기존 grid apply·DB/CLI/network·출력 밖 write open은 0회입니다.
  원 source497+처음 부분 출력9, **506파일**의 bytes/metadata를 보존했습니다.
  이전 일반 9점은 새 결과와 bit 단위로 같았습니다. 새 출력 56파일은 별도 namespace에만 만들었습니다.

## 수용하지 않은 경계

최초 검증은 case0의 512잎 요청에서 멈췄습니다. 요청/부분 출력과 실패 phase를 보존하고
harness가 같은 최대 요청의 hold를 기록한 뒤 나머지 일반 조건을 검사하도록 보완했습니다.
요청의 ID·수량·계수나 하위 모델/cap을 변경하지 않았습니다.

그 요청의 `app.crop_leaf_carbon_stock_rhs` 직렬화는 **528,002bytes**, 기존 cap은 **524,288bytes**였습니다.
원 요청 SHA는 `451718991a20d71c725a6d4e4cb3e70b5649f4fd0a38f01003355a4343165475`이며
검증 index에 `requested_case_accepted=false`, `all_requested_points_accepted=false`로 남깁니다.
원 자료를 줄이거나 cap을 올려 통과시킨 결과가 아닙니다.
초기 일반 9점/최대 요청의 부분 실행을 전체 55점 수용으로 보고하지 않습니다.
식별자와 숫자의 표현 길이 등 직렬화 payload가 cap에 영향을 줄 수 있으며 단일 원인만 단정하지 않습니다.

**같은 최대 요청의 지원**에는 원 수치·원 ID/단위·caps를 보존하는 bounded 표현 경계의 추가 검토가 필요합니다.
전체 목록/장기 재개의 해당 수용을 막는 구체적인 의존성으로 남겼습니다.
일반 조달점/새 CP 개발과 이 경계 검토는 나눠 진행하며 최대 목록 지원 주장은 보류합니다.

최종 검사 54.813초/PID95,342,592/WSL 소유+보호 합계131,825,664bytes,
별도 검증 253.401초/합계107,343,872bytes였습니다.
512MiB/PID·1GiB 합계·0.25초/600초/로그4MiB·보호1root·원4500항목/source,
소유 잔여0/FD4→4를 유지했습니다. Windows RSS는 측정 밖입니다.
기존 모델/SDK·전체 backend/build·브라우저/R2를 반복하지 않았습니다.

## 다음 수용 기준과 일정

다음은 별도 판본의 **분수 checkpoint·global/segment/point 장부와 정확 시각/phase/cursor**입니다.
원 source와 현재 점의 immutable 입력/코드/프로필, 출현별 나이/C/온도 적분 기준을 결속하고
원 current source 검토와 외부 신뢰 SHA의 복원 경계를 정의해야 합니다.
그 뒤 사건 전/후를 한 번 채택하고 원 출력 격자의 잔여 구간을 전진해,
분할 재개 동일성·중복/부분 실패·source/권리·최소/최대와 동시/경계 사건을 검증합니다.
기존 fixed-grid v1/원 blobs는 보존합니다. 현재 점은 CP가 없고 0초만 전진합니다.

그 후 실제 stem/leaf attachment·공통 floor/초기 C/조달·현재 farm 검토/서명,
불변 결합 결과→strict SDK→같은 상태의 실제 잎3D로 연결합니다.
남은 CP/잔여 경계의 기존 3–6시간 잠정 공수는 해당 분해와 크기 hold 검토 뒤 갱신합니다.
모든 최대 요청의 통과나 실제 농장 데이터 확보 시점을 가정한 완료 날짜를 제시하지 않습니다.
이번 결과는 UI에 미연결이며 [5175 제작 외형](http://localhost:5175/crop-appearance.html)을 유지합니다.
실제 품종/독립 국내 자료 0건·G0–G4/R2·빈 수관/제거·한 작기/생산/자원·경제/거시/수급,
자율 비교·제품 통합과 전체 완료일은 미완료·미정입니다. 전체 goal은 active입니다.

현재 판단/구현: **native Codex CLI gpt-6.1-sol / xhigh**, 재귀 CLI0회.
turn_context `2026-10-26T05:12:18.761Z`, raw LF SHA
`d12cf56e27addbf212a8100d4c01d7f6de8625c7470f33de05e25bca697fde84`,
관측 `2026-10-26T05:13:14.309889+00:00`. 출력은 계약·계산·시험 증거이며 관문 결정이 아닙니다.
