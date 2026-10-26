# 분수 시각 이후의 실제 재개 — 2026-10-26 KST

**분수 시각의 새 잎 조달 이후 원래 시간 격자로 계산을 이어가는 연구 엔진을 구현했습니다.**
[계약](../contracts/crop-funded-fractional-continuation-v1.md),
[구현](../backend/app/crop_funded_fractional_continuation.py),
[집중 검사](../backend/tests/test_crop_funded_fractional_continuation.py),
[검증 JSON](artifacts/crop-funded-fractional-continuation-20261026.json).
기존 fixed-grid v1과 원 자료/계수/cap을 보존했습니다. 자체 합성 소프트웨어 수용이며 G0–G4/R2 승인과 화면 적용은 아닙니다.

## 구현과 보관 경계

별도 context/CP 판본에 원 source/root·원 시작 상태/왼쪽 CP·원 격자·코드/프로필·새 점 입력/영수증과
정확 시각/phase/event/cursor/prefix를 결속했습니다. 이전 원본의 연속 누적량과 dense 부분 구간을 한 번 합치고,
새 segment·branch·lifetime의 연속 누적과 점 탄소/열용량/현열을 구분합니다.
기존 잎의 나이/C/A/앵커와 원 생성 기준은 유지하며 새 잎은 명시 C·나이0·새 기온 적분 기준으로 시작합니다.
과실 수 N은 질소가 아닙니다. source에 예정돼 있던 미래 점을 새 branch에 묵시적으로 적용하지 않습니다.

첫 걸음은 정확한 분수 시각에서 다음 원 격자까지의 잔여 시간입니다. 이후에는 원 dt를 따르고,
청크 경계가 수치 걸음을 임의로 세분하지 않습니다. 모든 상태와 유량은 같은 네 RK4 stage를 사용합니다.
원 해시와 같은 입력/수치 version의 청크 분할은 최종 CP 바이트까지 같습니다.
추가 점은 현재 확정 상태와 같은 시각에서 새 context로 채택합니다. 연속 누적량은 보존되고 cursor만 하나 늘어납니다.
동일한 원 before-state에 대한 재시도는 결정적이며 새 after-state에서 event/leaf ID를 재사용하면 거부합니다.
실패한 stage/장부는 새 CP를 게시하지 않고 마지막 확정 prefix와 실패 단계/목표 시각만 반환합니다.

복원은 **외부에서 신뢰하는 expected SHA**를 요구합니다. context 복원은 현재 원본/코드/프로필과 닫힌 schema를 읽어 검사하고
과거 ODE/점·잎 초기화를 하지 않습니다. CP 복원은 현재 RHS 한 번과 재구성한 현재 sample/장부를 대사합니다.
자기 해시나 Python 내부 필드는 농장 보관 권한/서명을 대체하지 않습니다. prefix의 전 역사를 다시 적분하는 검증도 아닙니다.
탄소/과실 수·열/수증기·열용량과 잎별 나이/C의 정확 유리수 잔차를 원 반올림 예산에 대사합니다.
그 예산과 이전 다항식 근 고립 폭은 물리/ODE 오차 보증이 아닙니다.

## 통과한 검증

- **최종 집중40검사:** 실제 분수 seed/잔여·세 source 조건, 여러 청크 분할과 매 청크 저장/복원 후 최종 CP의 바이트 일치,
  같은 시각/중간/마지막의 추가2잎·연속 이력·중복 ID/끝난 horizon·재해시한 잘못된 상태/단위/시각/원점/누적/장부,
  코드/원 source index/프로필·한도와 주입한 다음 k3 실패의 확정 prefix를 확인했습니다.
- **별도 여섯 조건, 초기/추가점12계산·418시점:** 상태52,868개, segment 누적486개,
  branch/lifetime 누적972개와 정확 최종 장부480개를 별도 산술로 대사했습니다.
  처음6잎에서 중간점 뒤7잎으로 이어지며 모든 계산이 원512초 horizon에 도달했습니다.
  초기6계산의 [128]과 [1,3,7,128] 청크는 최종 CP 바이트가 같았습니다.
  추가점의 별도 전체 분할 행렬은 이번 fresh에서 반복하지 않았으며 집중 검사의 분할/추가점 증거와 구별합니다.
- producer RHS2,856회와 독립 reference RHS1,684회를 계측했습니다.
  이전 prepare/advance/apply·DB/CLI/network와 출력 밖 write open은0회입니다.
  원 source497파일과 최초 부분 출력40파일, 합537파일의 bytes/metadata를 보존했고 새49파일만 별도 출력에 만들었습니다.
- **별도 cold12context/24CP:** context 복원 RHS/잎·점 초기화/과거 전진0회,
  CP당 현재 RHS1회(합24회)와 원 bytes를 확인했습니다.
  DB/CLI/network/write open·prepare/advance/birth0회, source/새 출력546파일의 bytes/metadata를 보존했습니다.
- 집중 검사212.966초/WSL 소유+보호 합계141,230,080bytes,
  별도 수치 대조423.408초/95,666,176bytes, cold복원16.961초/84,393,984bytes였습니다.
  512MiB/PID·합1GiB·0.25초/600초/로그4MiB, 보호1root·원4500항목/현재 source·소유 잔여0/FD4→4를 유지했습니다.
  Windows RSS는 이 WSL 측정 밖입니다.

[자체 QA](../fixtures/crop-funded-fractional-continuation-fixtures-v1.json)와
[재현 프로그램](verify-funded-fractional-continuation.py)은 이전 여섯 자체 공개 source를 재사용합니다.
명시 초기 C와 유입 온도는 기존 자체 선언의 값을 사용하며 새로운 품종/생리 계수나 측정을 채택하지 않았습니다.
독립 검증은 RK4 조합/누적/보존식을 별도로 작성했지만 RHS/유량 oracle은 기존 검토 모듈을 공유합니다.
농업 모델의 독립 검증으로 승격하지 않습니다.

첫 별도 대조는 여섯 번째 조건에서 Decimal400과 binary64의 차이를 발견해 중단했습니다.
원 실패 terminal/로그와 앞선 다섯 조건의 40파일을 보존했습니다.
진단에서 매우 작은 코호트의 정확한 두 binary64 중간값 처리를 확인했습니다.
검증기는 모든 조합을 별도 Fraction 식으로 계산하고 Decimal400 결과와도 대사합니다.
차이가 있으면 인접 binary64의 **정확한 중간값인 경우만** 허용하며 round-to-even의 정확 결과를 사용합니다.
그 외 차이는 실패합니다. 모델/RHS/계수·입력/cap을 바꾸거나 허용 오차를 넓히지 않았습니다.
최종 별도 대조는 새 namespace에서 전 조건을 실행했습니다. 최종609개 조합에서 정확한 중간값 보정을 기록했고 그 외 차이는 없었습니다.

## 남은 경계와 다음 한 단계

기존 동일512잎 요청의 RHS **528,002/524,288bytes** hold는 그대로입니다.
[원 최대 요청 기록](crop-funded-fractional-birth-point-20261026.md)을 유지하며 이 작업에서 최대 목록 지원을 수용하지 않습니다.
새 CP의 2MiB context/1MiB CP·32768 sample scalar와 하위 cap도 유지합니다.
일반 재개 core와 최소/최대 API의 전체 경계 수용을 분리해 후자는 미완료로 남깁니다.
자동으로 후속 출현 threshold를 반복 검출하는 전체 작기 엔진도 아직 아닙니다.

**다음은 이 실제 CP의 잎을 원 줄기 ID/부착·출현 시각에 결속하는 작은 단계입니다.**
원 source의 선택 상태/개발 원점과 현재 동적 Ta 적분량, 공통 floor·명시 C/조달·원 ID를 보존하고,
없는 줄기/다른 원점/미래 부착·source/권리 변경을 hold해야 합니다.
원 수치 시계에서 실제로 확인한 기관만 사용하며 기존 고정22도 pose나 임의 mesh 복제를 출현 근거로 사용하지 않습니다.
자체 source 결속 개발과 실제 품종/독립 농장 자료 확보는 병행합니다.
그 다음 같은 결합 상태의 불변 저장/무계산 조회→strict SDK→실제 잎3D/표·그래프·exact 시각을 대사합니다.
새 최대 목록 hold 해결은 그 지원 주장의 선행 조건이며 정상 목록의 저장/3D 개발 전체를 막지 않습니다.

현재 [5175](http://localhost:5175/crop-appearance.html)는 기존 제작 외형입니다. 이번 결과의 새 UI는 미연결입니다.
기존5177의 유한 실행 권한은 만료돼 재기동/연장하지 않았습니다.
40개 집중 검사와 별도 수치 대조/복원은 통과했지만 전체 backend/build·새 브라우저/R2는 이번에 실행하지 않았습니다.
다음 부착 단계의 예상 공수는 원 source/기관 inventory 검토 후 갱신하며 완료 날짜로 약속하지 않습니다.
실제 첫 품종/독립 국내 농장 자료0건·한 작기/수확/자원·Decimal 경제/거시/수급·자율 비교·제품 통합과 전체 완료일은 미완료·미정입니다.
전체 goal은 active입니다.

판단/구현: **native Codex CLI gpt-6.1-sol / xhigh**, 재귀 CLI0회.
turn_context `2026-10-26T05:52:34.245Z`, raw LF SHA
`c19a5161a3b135a9729e4821215abe86891703895675b04903665669395f83bd`, 관측 `2026-10-26T06:09:26.785677+00:00`.
출력은 계약/구현/시험 증거이며 관문 결정이 아닙니다.
