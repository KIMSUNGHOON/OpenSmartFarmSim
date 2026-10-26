# 기관별 탄소 재고·면적·기후의 분할 재개 — 2026-10-27 KST

[새 계약](../contracts/crop-stem-root-stock-continuation-v1.md)과 [구현](../backend/app/crop_stem_root_stock_continuation.py)을 **고정 기관 목록의 합성 분할 재개**로 수용한다. [공동 적분](crop-stem-root-stock-dynamics-20261027.md)의 일반106+3n+m 상태/21+3n+3m 장부(원6조건119/42), 잎/줄기·뿌리별 현재 C_i·현재 A/나이·과실/기후·원 초기 영수증/D0·ID/분모를 그대로 보존한다. 새 기관·실제 품종/작기·농장 UTC·생산/추천 승인은 아니다.

기존 [잎 재개](../contracts/crop-leaf-carbon-stock-continuation-v1.md)의 검증 패턴을 새 모듈/typed Context/Checkpoint·schema/code identity로 분리했다. 기존 모델/결과를 수정하지 않았다. 원 요청/정규 program/seed/manifest는 canonical immutable bytes이며 새 short/component/4profile/float 환경·정책/단위/layout/격자를 결속한다. start는 추가 RHS0, 복원/전진의 현재 검증은1회, 새 걸음은4stage다. 과거 전진·현재 C_i/A의 재초기화/비례 보정0이다.

외부 신뢰 raw SHA가 필수다. 자체 재해시가 진본을 증명하지 않으며 권한 있는 서버 저장/서명은 후속이다. frozen handle은 Python 내부 필드 재작성 공격의 보안 경계가 아니다. 수치 실패는 마지막 확정 sample/장부만 보존하고 미확정 CP를 발급하지 않는다. DB/worker·제품 CLI·UI/서명 게시 기능을 새로 기동하지 않았다.

실제 native CLI의2026-10-26T19:19:59.811Z turn context는 **gpt-6.1-sol/xhigh**, 관측19:20:33.768623Z/raw LF SHA `9b9c937dd46534f840ae517d8d5e1ca5244a157bd739b7422558bead65326766`이다. 이 세션에서 판단/구현했고 재귀 CLI0·새 농업 계수/외부 자료 채택0이다. 선행 [1차 문헌/권리·초기 재고/길이 간극](stem-carbon-growth-primary-sources-20261027.md)을 유지한다.

## 검증과 실제 관측

| 범위 | 실제 결과 |
|---|---|
| 신규/관련 | 신규142검사 + 뒤에 추가한6검사 + 원 공동 적분63/잎 재개138 = 고유349검사 통과. 추가 batch는6통과/142deselected이며 앞142검사 source prefix bytes를 보존/대사했다. 전체 backend/frontend 검사는 아니다. |
| 모든 분할 | 원6조건×4step의 모든8 composition(48조합), 대표32초의 모든15단일 cut, dt0.1/1⁄3·7step의 각6cut에서 원 short와 sample·모든 누적량/잔차/예산 및 최종 CP bytes가 같다. |
| 현재 상태/실패 | 초기/중간/완료·원 C_i/A/D0·공통 floor/ID/순서·trusted canonical roundtrip/복사/old typed handle·schema 거부를 확인했다. k2/k3/k4/endpoint/장부/seal 실패는 마지막 확정 값만 반환하고 CP=None이다. cancel/외부 RuntimeError를 정상 hold로 바꾸지 않는다. |
| 거부 | 재해시한 잘못된 코드/profile/환경/context·schema/UTF8/중복키/비canonical·비유한/bool/벡터/단위/시각/파생량/장부·잘못된 단계/예산과 완료 재전진을 거부했다. |
| 실제 한계 | 잎1/root1의110상태/27누적량과1/256기관 roundtrip·전진 통과.512기관은 하위 출력 cap hold/513사전 거부. 원6조건 sample budget의243step 허용/244거부,600초/4096step·chunk1–128·context2MiB/CP512KiB를 유지한다. |
| 별도 프로세스 | producer/consumer 각1개,6문맥/18원 CP(초기/8/16step). 다른 프로세스에서 manifest/원 요청·program·seed SHA·context root가 같고 원 CP raw bytes를 복원했다. 18복원과 중간 뒤48시점의 총7,854상태값과 최종 CP bytes/장부가 원본과 같다. 원 short102시점도 그대로 대사했다. |
| fresh 원본 | producer209,935bytes/SHA `2b5c2aeb4d2ee6e64ca029f6ffd89723df121e48a9d6331df509a4975a55f4ec`. 원 별도 short의441,723bytes/SHA `b5faea7ab1d048563db034fdd08a773f0bd9fe88a6f94034964c2fcd3d7ee8f8`와 현재 short code/profile/program identity를 확인해 비교 기준으로 재사용했다. |
| 호출/부작용 | 12구성 함수가 producer각402/consumer각222회. consumer는 준비한6문맥 뒤18복원+6전진 검증/192새stage이며, 이후 초기 준비·과거 whole 적분·socket/하위 프로세스/write-open0·FastAPI/SQLAlchemy/psycopg import0이다. 각 새 프로세스의 초기 준비 helper는 각각6회이며 이후 차단했다. |

18개 원 CP의 관측 크기는6,405–9,457bytes다. 이는 이 원6조건의 크기이며 모든 최대 입력의 지원 보증이 아니다. 기존 원512잎 요청/새512기관 출력 hold를 상향하거나 ID를 줄이지 않았다. 이전 app-free Decimal110 물리식/ODE와 별도 Decimal120 산술의 검증은 [원 short 증거](artifacts/crop-stem-root-stock-dynamics-20261027.json)를 보존해 사용했으며 이번에 다시 생성했다고 하지 않는다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도를 유지했다.142검사의 관측 최대 PID/합계 RSS는85,622,784/147,718,144bytes, 추가6은90,304,512/152,354,816bytes, 관련201은101,138,432/163,110,912bytes, fresh는31,137,792/110,305,280bytes였다. 각 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. Windows/전체 호스트 자원 계측이 아니다.

기존 SDK/배분/공동 RHS/기관 재고/short103·저장3D104의 지문과 공개4,732파일·private:false132blob·이전 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일 hash·원 최대 요청/5175·5180 HTTP200을 보존 검사했다. [구조화 증거](artifacts/crop-stem-root-stock-continuation-20261027.json)를 남긴다. [기존3D](complete-crop-stored-replay-20261027.md)는 같은 빌드이며 **새 재개는 UI/runtime 미연결**이다. 실제 DB/서명/worker·새 browser/전체 주앱 build·실제 품종/작기 검증은 실행하지 않았다.

## 다음 단계와 남은 외부 근거

다음은 **명시 초기 C 재고와 선택한 저장 줄기/원 탄소 상태의 계보 결속**이다. 실제 선택 source의 시각/초기 기관 ID/순서·floor·현재 권리/코드·원 aggregate C와 명시 개별 C_i의 완전한 합계를 검증한다. root는 따로 명시하고 길이/면적/aggregate로 실제 C_i를 역산하지 않는다. 미배정 탄소가 남으면 잔량을 숨기거나 root에 몰지 않고 hold와 명시 잔량을 보존한다. 새 자체 합성 complete case의 개발은 가능하지만 실제 품종/독립 자료 승인은 아니다.

그 뒤 새 절간 출현의 초기 C/성장호흡 비용과 point/연속 장부·실제 부모/시간·가변 목록 재개를 연결한다. [기존 분수 stem binding](../contracts/crop-funded-fractional-stem-binding-v1.md)의 원 시계/ID/권리 검증을 참조하며 old CP를 새 CP로 가장하지 않는다. 공급 제한 길이/면적→불변 저장/같은 상태3D→한 작기/생산·자원/경제·거시/수급/자율 비교로 이어진다.

[VTC 후보](artifacts/stem-root-allometry-data-screening-20261027.json)의 권리/대응 측정 미확인·독립 국내 측정0건·새 품종/실제 자료 채택0·G0–G4=not_assessed/R2=not_approved를 유지한다. 초기 결속은 source/계약20–35분+명시 재고/잔량20–40분+독립/거부30–60분+보존10–20분의 잠정80–155집중분이며 실행 보장/전체 완료일은 아니다. 실제 자료 확보와 후속 분해 전 전체 일정은 미정이고 전체 goal은 active/incomplete다.
