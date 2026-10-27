# 실제 분수 기관 상태의 불변 저장·현재 복원 — 2026-10-27

[계약](../contracts/crop-organ-fractional-context-v1.md) · [모듈](../backend/app/crop_organ_fractional_context.py) · [검사](../backend/tests/test_crop_organ_fractional_context.py) · [기계 증거](artifacts/crop-organ-fractional-context-20261027.json).

실제 [첫 기관 탄소 조달점](crop-organ-fractional-point-20261027.md)을 새 immutable Context/typed CP에 채택했다. 최종 소스의73개 검사와 별도 프로세스12쌍의 바이트 재현을 수용했다. 원 격자 잔여 전진과 새 UI/runtime 연결은 아직 수행하지 않는다. 실제 품종/작기·생산·경제·추천 승인이 아니다.

## 저장 대상과 원 시간

`prepare_context`는 genuine mixed-organ source Context/외부 신뢰 raw CP·명시 입력/시간 정밀도로 실제37+1(+1) RHS의 point를 계산한다. 실제 source snapshot/초기 binding/point 입력·결과/code/profile·전후 C/age/area/D0와 원 selected simulation/development 원점을 결속한다. after-program으로 초기 상태를 다시 만들거나 old CP/token을 가장하지 않는다.

원 출현 기준/논리 ID의 첫 event만 소비하고 다음 순번/기준은 원 phyllochron으로 구한다. 선택된 수치 나이가 다음 기준도 지났다면 phase hold이며 건너뛰거나 snap하지 않는다. 새 stem/leaf의 exact 시각/기온 적분/C/나이0 기준과 기존 기관의 개별 baseline을 보존한다. 계산 시작 뒤8초에 생성된 기존 잎·절간도 실제 전진/다음 첫 사건으로 검증했다. root는 생리적 나이를 만들지 않는다. numerical material-point 기준을 실제 생리적 출현으로 부르지 않는다.

원 좌측 index·완료 grid index·정확 dt/부분 구간·다음 원 endpoint/남은 초를 따로 저장한다. 분수 시각을 정수 step으로 가장하지 않는다. source prefix→before/after sample 두 개의 각 hash와 cursor+2·논리 event sequence+1을 결속한다. 새 branch의 연속 유량은0이다.

## 비용·장부와 복원

원 source/segment float prefix와 actual dense partial의 정확 합을 구별하고 새 기관 유량만0으로 추가한다. 원 point totals와 새 internode→leaf per-kind 비용을 보존해 exact totals를 만든다. 순차 buffer 차감을 합산 한 번 차감으로 바꾸지 않는다. 전체 C·과실수·수관/공기 현열·vapor/capacity/reduced energy·개별 leaf age/C·stem/root C의 잔차를 source+local+point의 정확 합과 원 예산 합으로 검사한다. 임의 absolute epsilon/추가 집계 허용치는 없다.

`context_bytes/restore_context`는 외부 신뢰 SHA/actual Root/current source를 검사한다. 저장된 stage의 순수 dense 조합·이분 근거·점 비용/state/flow/영수증·F(0) 비교와 장부는 재검사한다. 과거 RHS·공개 point/`_jump`·leaf 초기화/정규화·실제 비용 재반영은0이다. diagnostic refinement는 신뢰 snapshot의 원 bytes로 보존하고 과거 ODE를 다시 적분하지 않는다. 자체 SHA 재작성은 농장 custody/인증 경계가 아니다.

`start`/serialization은 RHS0이며 `restore_checkpoint`는 실제 현재 RHS1회로 원 sample/rates/derived/curve를 대사한다. 발급 직전 source/code/profile/rights와 immutable snapshot을 재검사한다. 수정된 CP handle도 원 captured payload와 달라지면 발급하지 않는다. 실패 때 Context/CP를 발급하지 않고 RuntimeError를 정상 hold로 숨기지 않는다.

## 검증

- 최종73개: 실제 첫 사건/기관·정확 시각/grid·D0/기존·신규 상태/장부·일정, 원 state/flow/time/ID/birth/units/rights/예산과 보고 code/cubic certificate의 자체 재해시, 외부 SHA/Root/canonical/중복 key/typed/cap·늦은 source/profile/code/내부 snapshot 변경·현재 RHS/RuntimeError·반복·nonzero birth를 검사했다. 최초 missing-module red·발급 전4경로의 red를 보존했고 보완 뒤 전체73개를 다시 실행했다. 이전67개나 중간 단계는73에 중복 합산하지 않는다.
- 별도 producer/consumer가 genuine Root6/원 source12Context를 준비했다. producer는 actual point12개를 계산하고 각 Context/CP를 복원했다. consumer는12쌍의 같은 canonical bytes를 복원했다. producer point462+CP12=474 RHS, consumer CP12 RHS이며 Root 준비는 각6회로 별도다. Context restore는 producer12/consumer24회 모두 RHS0, consumer point core/leaf 초기화0이다. source82파일 bytes/metadata와 원 CP를 보존했다.
- 앱을 import하지 않는 Decimal180/Fraction 산술이 state1,506값·연속 prefix1,260량·global residual276/예산276·birth126·시계/grid/schedule72·prefix24링크를 대사했다. 기존 RHS를 공유한 소프트웨어 수치 검증이며 독립 작물 모델/현장 검증으로 부르지 않는다.
- 관측 Context342,716–349,488bytes/2MiB·CP24,900–26,251bytes/512KiB다. 여러 사례의 private packet 약5MB와 개별 API cap을 구별하며, 기존512 요청 byte-cap hold를 유지한다.

직전139 source/1 output과165검사의 증거를 보존했으며165개를 이번에 재실행하거나73에 더했다고 하지 않는다. private:false132 blobs·원 export/경계·봉인3D 빌드4,865파일/834시점·두 HTTP 화면과 WSL의512MiB/PID·소유+보호1GiB·600초/4MiB log·0.25초 sample·4,500감시 항목/소유 잔여0·FD4→4를 유지했다.5180 원 만료2026-10-27 13:09KST는 연장하지 않았다.

## 다음 수용과 외부 의존성

다음 `stem-root-stock-fractional-grid-remainder-resume`는 새 typed CP에서 정확 잔여→원 grid/후속 첫 사건·current C/A/age/D0·birth/schedule·branch/point/lifetime 장부·cursor/prefix·분할 최종 bytes와 실패 prefix를 수용한다. 새 문맥을 초기화하거나 old fixed CP로 바꾸지 않는다. 잠정 공수는 grid/CP 계약20–35+RK4 잔여/전진35–60+시계/장부/prefix25–45+분할/실패/독립/fresh35–60+보존15–25=130–225집중분이며 완료 날짜가 아니다. 이번110–185분 예상은 실제73검사/별도12쌍 수용으로 대체한다.

이후 기관 ID/시계→탄소 공급 제한 형상→불변 같은 상태3D→한 작기·생산·자원/Decimal 경제·거시/수급·자율 비교를 유지한다. 새 모듈의 API/worker/UI·전체 backend/frontend suite·새 browser/DB·전체 주앱 build는 실행하지 않았다. hosted CI는 실제 push HEAD를 별도로 조회한다. 독립 국내 측정0·새 품종/allometry 채택0·VTC 권리/대응 측정 미확인·512 byte cap·최종 R2/첫 shader warning·전체 제품/관문/goal과 완료일은 미완료·미정이다. 실제 자료 확보는 합성 개발과 병행한다.

실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 turn/모델/effort·raw LF SHA를 기계 증거에 기록했다. 재귀 CLI0이며 결과는 검토 가능한 소프트웨어 연구 증거다.
