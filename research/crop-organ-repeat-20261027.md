# 반복 출현·조달 채택과 원 격자 재개 — 2026-10-27

실제 successor 조달 결과를 별도 Context/체크포인트로 채택하고 다음 출현까지 반복 전진하는 **합성 소프트웨어 연구 기능**을 수용했다. [계약](../contracts/crop-organ-repeat-v1.md), [상태/재개](../backend/app/crop_organ_repeat.py), [후속 후보/조달](../backend/app/crop_organ_repeat_events.py), [영수증 산술 검증](../backend/app/crop_organ_repeat_proofs.py), [경로 검사](../backend/tests/test_crop_organ_repeat.py), [경계 검사](../backend/tests/test_crop_organ_repeat_boundaries.py), [기계 기록](artifacts/crop-organ-repeat-20261027.json).

## 구현 범위

원 capture를 진짜 불변 authority로 유지하며 새 Context/CP 타입을 발급한다. 원 stock 출처 쌍과 최신 조달 부모 Context/CP 쌍을 구분한다. 초기/기존 기관과 새 기관의 C/면적/나이/D0·birth 시각/기온 적분 기준을 보존하고 새 연속 유량 채널만 정확한0에서 시작한다. 조달점의 전역 잔차는 원 root에서 직접 산출한 값이 before-global + point 잔차와 정확히 같아야 하며 예산도 기존 두 예산의 합이다. 논리 threshold 순서와 material-event count는 별도로 관리해 일정을 한 번만 소비한다.

분수 시각의 남은 구간→원 시간 격자→다음 실제 문턱을 계산한다. 새 타입을 직접 받는 후보·조달 API로 후속 기관을 채택한다. 옛 Context/107벡터 handle 가장, 과거 적분/조달점 함수 재실행·기존 잎 초기화나 문턱 건너뛰기는 없다. 같은 원 격자의 단계만 확정하고 실패 구간은 마지막 확정 prefix만 남긴다.

완전한 불변 조달 영수증은 해시로 참조하며 원문은 복원 때 별도로 요구한다. 과거 Context나 전체 경로를 영수증 안에 다시 중첩하지 않는다. Context/각 영수증2MiB·CP512KiB·원 horizon/step·512기관·32768 잔여 scalar 한도를 유지하고 영수증 묶음에는 별도16MiB/512사건 한도를 둔다. 실제8영수증은2,858,352bytes다. 신뢰한 저장 해시가 필요하며 사용자의 self-hash를 농장 인증으로 해석하지 않는다.

생성/복원에서 전체 영수증 산술을 검증한다. 이후 같은 불변 객체·원 capture bytes/hash·전체 영수증 hash·현재 코드가 같을 때만 그 산술 검증을 재사용한다. 매 호출에서 canonical 원문/크기·현재 source/권리/전체 profile 객체·code를 검사하고, 현재 CP/RHS는 재검증한다. 약한 객체 참조로 옛 Context를 붙잡지 않는다. 프로필 값/원문·domain metadata 변경과 warm-cache 변조/철회 반례를 통과했다.

## 실제 수용 증거

- **최종 소스의 집중44검사 통과:** 기본 경로/경계와 advanced CP 복원·4종점의 모든8분할 조합을 한 번에 실행했다. 앞선42묶음/단독2개와 반복 관측은 별도로 보존하며 중복 합산하지 않는다.
- 별도 producer/consumer는 같은 한 출처에서 **후속 출현7회·총8조달점·원 격자37시점**을 재현해512초 끝의 Context/CP/영수증 원문과 전체 시점을 동일하게 반환했다. 초기5→최종13잎/13줄기·뿌리 재고,158상태/47전역 장부다. 실제 농장이나 한 작기13식물의 검증을 뜻하지 않는다.
- producer는8개 큰 chunk, consumer는44개 한 종점 chunk와7회 cold Context 복원을 사용했다. 원 Root 준비 RHS6씩을 별도로 기록했고 계산 RHS는755/791이다. 차이36은 chunk별 현재 검증 횟수 차이다. 새 잎 초기화는 각8회뿐이며 과거 point/RHS/기존 초기화·DB/CLI/network/write0을 계측했다. 영수증의 과거 산술 재검증은 수행하며 과거 조달점 함수 실행과 구별한다.
- 제품 모듈 import/RHS0인 독립 Decimal200/정확 유리수 산술이 Context seed/hash8개를 모두 재구성했다. old 상태1,104값·논리 ID24·비용48/순차 차감8·점 잔차88/예산88·dense 상태1,120/유량576·근 경계16·root-global 잔차607/합성1,214·birth clock157·선택 첫/끝 RK4 stage864/종점288·누적156을 대사했다. 전체 원 prefix/point totals·일정·출처와 최종512초도 결속했다.
- 실제 마지막 raw Context의 별도 cold 복원은 과거 RHS0/초기화0, 마지막 CP 복원은 현재 RHS1이며 원 bytes가 같았다. 중간 advanced CP의 현재1RHS 복원 뒤 후속 bytes도 같았다. source85파일의 bytes/metadata를 보존했다.
- 초기 후속 조달의 직렬화 함수 누락은 3통과/1실패 관측으로 보존했고 수정했다. 불변 영수증을 매번 전부 재검증하던 경로는 원600초 한도에서 종료됐다. 한도를 늘리지 않고 정확한 불변 객체의 검증 재사용과 매번 현재 fence를 연결해 같은 경로4검사가290초에 종료됐으며 최종 원문44검사는405초에 종료됐다. 독립 검사 별칭 누락과 reader 도구의 역사 fixture 경로 치환 오류도 원 실패를 보존하고 수정 후 통과했다. 마지막 EOF 빈 줄1개를 정리하면서 AST가 같음을 확인했고, 원문 hash가 달라지는 계약에 맞춰44검사/별도 두 프로세스·독립 산술/cold reader/보존을 최종 원문으로 다시 검증했다. 이전 코드의 관측을 최종 코드 시험으로 합산하지 않는다.
- 원154 source/1 output·private:false132blob·GUI1,502파일·sealed3D4,865파일/공개4,732파일·834시점·원 최대 요청528,002bytes의512KiB hold를 보존했다. 5180은 원10월27일13:09KST 만료대로 종료됐고 PID/HTTP 종료와 저장 bytes를 확인했다. 기간을 연장하지 않았다. 외형5175 HTTP200은 유지한다.
- 모든 phase는 단일 heavy process·원 WSL 한도·source/원4500항목·소유 잔여0/FD4→4를 유지했다. 전체 backend/web suite·주앱 build, 새 browser/DB/API/worker·이번 결과의 UI 연결은 실행/수용하지 않았다. hosted CI 수용으로 해석하지 않는다.

실제 native turn metadata `gpt-6.1-sol/xhigh`와 코드·출력 지문을 보존했고 재귀 CLI0이다. 전체 goal은 active/incomplete다. G0–G4 not_assessed/R2 not_approved, 실제 품종/allometry 채택·독립 국내 측정0, VTC 권리/대응 측정 미확인과 한 작기·수확/구매·마진/추천 보류를 유지한다.

## 다음 한 단계

**탄소 공급 제한 형상 식·단위·입력 계약**을 먼저 확정한다. 새 Context/현재 CP의 실제 기관별 C/정확 birth·clock/ID/부착 근거를 사용하고, `mg_CH2O/m2_floor`를 건물중/생과중으로 임의 변환하지 않는다. 기존 길이·면적에서 C를 역산하지 않는다. 잎 면적/절간 길이의 원 식·매개변수 단위/권리·적용 범위를 기존 primary 자료와 추가 허용 근거에서 확인하고, 검증된 품종 계수가 없을 때는 명시 합성 가정/게시 hold를 구분한다.

초기/birth A와 C가 새 제한식을 만족하는지, 제거/유지 호흡/고갈·음수/빈 수관에서 어떤 domain·사건 정책이 필요한지 명시한다. 후처리/렌더링에서 단순 clamp하거나 D0·열용량/수관 에너지를 숨겨 바꾸지 않는다. 필요한 현재 시계/lineage 계산은 형상 입력 계약 안에 결합하며 또 다른 옛 typed handle로 우회하지 않는다.

수용은 출처/원 식·단위·권리/매개변수 미확인 이유, 실제 own CP/원 source/clock/기관·C/A/D0/공통 footprint 입력, 탄소/면적/길이·열/물 수지와 birth/제거/실패·동일 저장값3D의 검사 기준을 고정한 계약/연구 기록이다. 자료·단위 검토20–35 + 상태/birth/제약 설계20–35 + 수용/source5–15 + 보존5–10 = **잠정50–95집중분**. 식과 계수 근거를 먼저 확인해야 하는 낮은 신뢰 작업량이다. 그 뒤 실제 coupled RHS/재개는 해당 계약에서 다시 분해한다. 과거160–265분 반복 재개 초안은 이번 실제 수용으로 대체한다.

독립 농장 자료 확보는 개발과 병행하며 예측/추천 게시 조건은 별도다. 이후 공급 제한 생장 계산 → 불변 저장/같은 상태의 실제3D → 한 품종/한 작기 생산·자원 → Decimal 경제/거시·수급 → 대응 후보 자율 비교 → 제품 farm 권리/worker/UI 통합 순서다. 실제 품종/현장·최종 사실감 R2/전체 주앱 build와 전체 제품 완료일은 자료 확보·후속 분해 전 미완료·미정이다.
