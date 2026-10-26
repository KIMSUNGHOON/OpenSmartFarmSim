# 줄기·뿌리·잎 탄소 재고와 기후의 짧은 공동 적분 — 2026-10-27 KST

[계약](../contracts/crop-stem-root-stock-dynamics-v1.md)과 [구현](../backend/app/crop_stem_root_stock_dynamics.py)을 **고정 기관 목록의 자체 합성 짧은 적분**으로 수용한다. 원 [기관 재고 RHS](stem-root-carbon-stock-rhs-20261027.md)를 같은 네 RK4 stage에서 호출해 줄기·뿌리 C_i와 잎 C_i/나이/현재 면적·과실/기후를 함께 전진한다. 독립 상태는106+3n+m개이며 aggregate leaf/stem_root slot을 모두 제외했다. 실제 공급 제한 형상·출현/재개·실제 품종/작기 계산은 아니다.

초기 정규화와 순수 projection/수지/스칼라 RK4 helper를 재사용하며 옛 geometry/leaf whole RHS·적분은 호출하지 않는다. 초기 요청/정규 면적 영수증·D0와 현재 A를 보존한다. 각 stage의 현재 C_i 합계/명시 제거만 source에 조립하고 원 성장 원가/보류 환급·실제 유지호흡/제거 합계를21 global +3n leaf +3m stem/root 장부에 한 번 반영한다. 개별 C와 집계 C를 중복 적분하거나 재고를 비례 보정하지 않는다. 현재 면적 곡선이 C 공급을 읽지 않는 선행 연구 가정은 그대로다.

실제 native CLI의2026-10-26T18:46:17.008Z turn context는 **gpt-6.1-sol/xhigh**, 관측18:46:48.445565Z/raw LF SHA `eadf00f185015c421699727e3a8ad29010b4ac939af3421313a0e13774787ef3`이다. 이 세션에서 판단/구현했고 재귀 CLI0·새 농업 계수/외부 자료 채택0이다. [선행 1차 문헌·권리·초기 재고/길이 간극](stem-carbon-growth-primary-sources-20261027.md)을 유지한다.

## 검증과 실제 관측

| 범위 | 실제 결과 |
|---|---|
| 신규/관련 | 신규63 + 원 기관 재고278/개별 잎 동역학58 = 고유399검사 통과. 처음 모듈 부재의 수집 오류1건 뒤51→63검사를 수용했다. 전체 backend/frontend 검사는 아니다. |
| 원 식/ODE 독립 검증 | [app 없는 Decimal110 생성기](crop-stem-root-stock-dynamics-reference.py)/[fixture](../fixtures/crop-stem-root-stock-dynamics-reference-v1.json)를 제품 적분 전에 준비 커밋 `0f88b4d3e9f92d4c980dd07dcd1c654f86c2ee2e`에 고정했다. 원6조건의32초 계산마다119상태/42누적량/4파생량/3곡선 진단, 총1,008비교가 통과했다. 대표 dt8/4/2 반분 오차 감소 또는128ulp roundoff 바닥도 통과했다. |
| 같은 stage/상태 | 원6조건×3 stem sink의18조합, 양/일부0/전체0 재고·명시 제거/고갈/flow-through, 초기 정규화1회·target4N+1회·현재 A와 초기 요청 영수증 보존을 확인했다. |
| 별도 producer | 새 프로세스2개가6개32초 궤적/102시점을 계산했다. 전체441,723bytes가 같고 SHA `b5faea7ab1d048563db034fdd08a773f0bd9fe88a6f94034964c2fcd3d7ee8f8`이다. |
| 별도 산술/장부 | 또 다른 프로세스의 Decimal120 RK4 산술에 검토된 제품 RHS를 공급했다.12,138상태+204집계 진단+252누적량=12,594수량과1,836장부를 대사했다. 이 산술 oracle은 위 app-free 원 식/ODE 검증을 대신하지 않는다. 최대 비교 수량 상대차2.3807225804064666e-15, 잔차/정해진 예산 최대0.0008416451358546814다. 생물학적 정확도가 아니다. |
| 호출/부작용 | 각 producer 및 성공 산술 프로세스에서 dynamic stage/기관 재고와 원10구성 함수가 각각390회(평가당 각1회). producer별 초기 정규화6회, 산술0회. 옛 whole RHS/적분·socket/하위 프로세스/write-open0·FastAPI/SQLAlchemy/psycopg import0. |
| 실패/한계 | 작은 기관 재고 고갈·큰 열 k2·주입 k3 실패에서 마지막 확정 state/모든 누적량·잔차/예산을 보존했다. 별도 출력 cap hold도 완료 prefix를 보존한다.1/256기관 전진 통과,512기관은 하위512KiB 출력 cap hold·513사전 거부. 총600초/정수4096step·32768scalar/2MiB와 비영 증분 유실 hold를 유지한다. |

첫 fresh의 두 producer는 성공·동일 출력이었지만 이후 산술 검증기가 canonical JSON의 정렬된 object 순서를 물리 유량 벡터 순서로 사용해 carbohydrate 장부에 실패했다. 검증기를 명시 flux 이름/단위 순서에 결속하고 출력 필드 집합을 대사하도록 수정했다. 원 두 producer bytes와 실패 로그를 그대로 보존한 뒤, 제품 코드/원 식·격자/허용 오차 변경 없이 별도 수정 산술 프로세스를 통과했다. 첫 부모 phase 전체를 성공이라고 기록하지 않는다. CSV의 CRLF가 스테이징 형식 검사에 걸린 뒤에도 첫 커밋이 진행된 것을 확인했다. 원 CSV bytes를 보존하고 LF로 정리한 새 지문·수치 동일성·스테이징 검사를 별도 정정 판본에 기록한다. 계산 코드는 바꾸지 않았다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도를 유지했다. 신규63검사의 관측 최대 PID/합계 RSS는70,856,704/134,066,176bytes, 관련336은118,571,008/181,628,928bytes, 성공 fresh 산술은29,937,664/110,243,840bytes였다. 각 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. Windows/전체 호스트 자원 계측을 뜻하지 않는다.

기존 SDK/배분/공동 RHS/기관 재고88·저장3D104의 지문과 공개4,732파일·private:false132blob·이전 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일 hash·원 최대 요청 및5175/5180 HTTP200을 보존 검사했다. [102시점 CSV](artifacts/crop-stem-root-stock-dynamics-20261027.csv)와 [구조화 증거](artifacts/crop-stem-root-stock-dynamics-20261027.json)는 자체 합성 소프트웨어 산출물이다. [기존3D](complete-crop-stored-replay-20261027.md)는 같은 빌드이며 **새 적분은 UI/runtime 미연결**이다. 새 browser/DB/API/worker·전체 주앱 build·실제 품종/작기 검증은 실행하지 않았다.

## 다음 단계와 외부 의존성

다음은 **동일 격자의 불변 context/checkpoint와 분할 재개**다. [기존 잎 재개 계약](../contracts/crop-leaf-carbon-stock-continuation-v1.md)을 비교해 새106+3n+m 상태/21+3n+3m 장부·원 요청/정규 프로그램/영수증/D0·원 기관/같은 floor/현재 source/code/profile을 고정한다. 현재 C_i/면적을 초기값으로 재맞추거나 과거를 다시 적분하지 않는다. 외부 신뢰 raw SHA가 필수이며 원 short의 모든 분할에서 sample/상태/누적량·잔차/예산과 최종 bytes가 같아야 한다. 고갈/부분 단계에서 미확정 CP를 발급하지 않는다.

초기 이력/미배정 탄소 잔량·새 기관 초기 비용/출현 점과 실제 source/geometry 계보→공급 제한 길이/면적→불변 저장/같은 상태3D→한 작기/생산·자원/경제·거시/수급/자율 비교로 이어간다. 기존 aggregate/형태에서 실제 기관 C를 임의 역산하지 않는다. [VTC 후보](artifacts/stem-root-allometry-data-screening-20261027.json)의 권리/대응 측정 구성 미확인·독립 국내 측정0건·새 품종/실제 자료 채택0·G0–G4=not_assessed/R2=not_approved를 유지하며 실제 근거 확보와 개발을 병행한다.

다음 재개는 manifest/seed 계약20–35분+CP/전진·복원25–45분+모든 분할/변조·실패·fresh45–75분+보존10–20분의 잠정100–175집중분이다. 실행 보장/전체 완료일이 아니며 전체 제품 일정은 실제 자료 확보와 후속 분해 전 미정이다. 전체 goal은 active/incomplete다.
