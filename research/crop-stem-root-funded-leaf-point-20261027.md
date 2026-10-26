# 개별 줄기·뿌리 재고를 보존하는 새 잎 조달점 — 2026-10-27 KST

[계약](../contracts/crop-stem-root-funded-leaf-point-v1.md)·[구현](../backend/app/crop_stem_root_funded_leaf_point.py)을 **검증된 현재 CP의 명시 새 잎 구조 형성점**으로 수용한다. [기존 잎 점](crop-leaf-funded-birth-point-20261026.md)의107+3n 벡터를 [새106+3n+m 상태](crop-stem-root-stock-continuation-20261027.md)에 이식했다. [원 초기 source 연결](crop-stem-root-initial-binding-20261027.md)과 [새 절간 점](crop-stem-root-funded-internode-point-20261027.md)의 전/후 권리·코드·source fence를 재사용하며 기존 모듈/입력/계수는 수정하지 않았다. 새 CP/시간 전진·자동 출현·공급 제한 A/3D 연결과 실제 품종 검증은 후속이다.

각 새 잎은0나이·명시 C/curve/F(0)·sink/removal·입력 T와 실제 현재 internode 부모 ID를 요구한다. 원 초기 source의 전체 canonical 연결 hash·실제 CP raw SHA/현재 상태/장부·원 floor/정확 elapsed step×index를 검사한다. source가 제공하지 않는 실제 밀도/질량을 추정하지 않는다. 원 logistic F(0)>0과 초기 요청의1e-12상대 오차/영수증·정규 면적을 유지하고 **현재 기존 잎의 면적/나이/C/D0는 재초기화하지 않는다**.

[원 pinned 프로필](../fixtures/crop-growth-reference-parameters-v1.json)의 cLeafG=0.28과 [기존 연구 가정/원문·권리](crop-leaf-funded-births-design-20261026.md)를 재사용했다. 새 질량의 정확 binary64 합 S에서 structural=round(S), Rg=round(cLeafG×S), debit=round((1+cLeafG)×S), buffer_after=round(buffer_before−debit)>0이다. cStemG로 대체하지 않는다. 연속 조달을 환급/재차감하지 않으며 이미 지불한 숨은 조직의 공개는 별도 이동 모델이 필요하다. 면적→C/SLA/기본 초기 질량·새 농업 계수를 채택하지 않았다.

각 새 잎의 ΔK=round(k_leaf×canonical_F(0)/floor), E=round(ΔK×(T_in−T_ref))를 원 산술로 계산한다. 합계의 한번 반올림을 U103에 반영한다. buffer0/U103 외 원 첫106scalar·기존 leaf age/A/C·**모든 기존 stem/root C**를 같은 값으로 보존하고 새 leaf 블록만 삽입한다. after RHS가 같은 상태의 수관 온도/열용량을 계산한다. 화학 에너지를 임의 열로 바꾸지 않고 완전한 물질·열 첫 법칙을 주장하지 않는다.

내부 `_jump(program,state,profiles,events,anchors)`는 이미 검증된 현재 데이터의 재료점 산술이며 public wrapper가 원 source/CP/time/권리 검증을 소유한다. 후속 가변 목록은 자신의 typed CP를 검증한 뒤 이를 호출할 수 있고 old token/Context를 가장하지 않는다. 결과는 원 CP/prefix/연속 장부와 분리된 point 영수증/흐름·buffer/new leaf/whole-C/U/K 장부·after program/sample/anchors/rates/layout이다. CP=None/시간 전진0이며 한 번 채택/중복 이력 보장은 후속이다.

실제 native turn context2026-10-26T20:55:04.231Z는 **gpt-6.1-sol/xhigh**, 관측20:55:53.191011Z/raw LF SHA `48adf04a08d8882348d12ca20a988fa390d956a5ac02b9c0d79ed1ab15245a28`이다. 현재 세션에서 판단/구현했고 재귀 CLI0·새 실제 자료/품종 계수 채택0이다. scope=software_research_only/time_kind=synthetic_model_clock_not_observation/G0–G4=not_assessed다.

## 실제 수용 증거

| 범위 | 실제 결과 |
|---|---|
| 집중/회귀 | 신규69 + 기존 잎 점74/새 절간 점54 = 고유197검사 통과. 전체 backend/frontend 검사는 아니다. missing-module RED와 초기54통과를 보존하며 앞54는 최종69의 부분집합이므로 더하지 않는다. |
| 원 상태/흐름 대조 | 실제 owned source6조건의 초기·후기 CP에서 단일/batch와10/22/34°C를 확인했다. 별도로 준비한 **실제 old Context/CP**의 원 잎 점과6조건의 집계 projection 상태/point 흐름/초기 영수증이 동일했다. old token/typed handle을 만들어 가장하지 않았다. |
| 독립 산술 | unit의 Decimal110 단일/소수/batch·9온도/질량 조합 외에 별도 app-free parent가 fresh6결과의 탄소 비용/버퍼·비대상 상태/새 C·ΔK/U/전체 수지812항목을 독립 Decimal110으로 대사했다. exact 잔차/원64ULP 예산의 최대 비는 whole-C0.000937521457672119140625, U/K각0.0078125다. 농업 타당성 검증은 아니다. |
| 보존/초기화 | 원 stem/root C 전부·원 leaf age/A/C/D0/초기 요청·곡선/기후·원 CP/누적량/장부를 보존했다. 새 초기 A의 허용된 작은 요청 차이는 영수증에 남기고 새 canonical 면적을 사용한다. 기존 잎 초기화0·선언한 새 잎만 초기화했다. |
| 조립/실패/한계 | stem→leaf에서 실제 직전 새 stem ID를 부모로 사용하고 leaf→stem에서도 변경 목록으로 계산했다. source/CP/time/floor·ID/부모/root/중복·초기 A/질량/부족/T·권리/code/profile/current/late 변경과 after domain을 거부했다. 예상 밖 RuntimeError는 정상 hold로 숨기지 않는다.128잎 통과/512하위 출력 cap hold/513사전 거부를 유지했다. 모든 최대 입력의 지원 보증은 아니다. |
| 별도 프로세스 | producer/consumer 각1개·6문맥/6동일 canonical point 결과·원82개 source 파일 bytes/metadata 보존. 각 프로세스 Context 준비6회 뒤 point RHS12회·새 leaf 초기화12회/old 초기화0. producer는 준비 중 CP6step을 계산했고 consumer는 받은 raw CP로 과거 전진0이다. |
| 외부/권리 | point 중 초기 재준비/과거 전진·DB connect/socket/Popen/write-open/BlobStore.put0. 기존 저장 모듈의 psycopg import와 연결0을 구별한다. 원 source/입력 rights·reviewer를 보존하고 어떤 redistribute=False도 True로 승격하지 않는다. 법적/현재 농장 권한/G0 승인을 발급하지 않는다. |

fresh producer579,477bytes/SHA `d6faec65962994db20787b712f64e0a3c26913a71a305e8444c73d2381aff166`, consumer579,477bytes/SHA `4c92e2d033374f9e8a068b5f1d31bbd5be0183c8832bdf1a509c0a0addb49f71`이다. 역할/관측 시각이 다른 외부 packet 전체를 같다고 하지 않으며 내부6결과만 동일하다. point 결과 관측 크기는68,482–78,331bytes다. 자체 합성 redistribute=False인 raw/source는 비공개로 보존하며 공개 JSON에는 hash/수량만 남겼다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도를 유지했다. 신규69의 최대 PID/합계 RSS는104,587,264/165,089,280bytes, 관련128은93,884,416/154,484,736bytes, fresh는57,413,632/136,245,248bytes다. 각 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. 전체 호스트 자원 계측이 아니다.

직전 절간 점116/초기 연결113·이전 CP110/short103/저장3D104 지문·공개4,732파일·private:false132blob·원 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일·원 최대 요청·5175/5180 HTTP200을 보존 검사했다. [구조화 증거](artifacts/crop-stem-root-funded-leaf-point-20261027.json)를 남긴다. [기존 저장3D](complete-crop-stored-replay-20261027.md)/[5180 미리보기](http://localhost:5180/complete-crop-replay.html)(10/27 13:09KST 원 만료)는 같은 빌드다. **새 point는 UI/runtime 미연결**이며 새 browser/실제 DB/API/worker·전체 주앱 build를 실행하지 않았다. 기존 최대 요청/최종 R2/첫 shader warning 보류를 유지한다.

## 다음 한 단계와 남은 외부 의존성

다음은 **두 point 종류를 한 번 채택하는 가변 기관 목록의 같은 격자 재개**다. 실제 root Context/초기 source·입력/현재 CP hash와 typed 원본을 결속한 새 version의 Context/Checkpoint를 만들고, 현재 after state/원 D0·새 초기 영수증/기관별 birth baseline·전역 elapsed/air integral·원 전체+point+segment 장부를 캡처한다. 양쪽 point의 단일 채택/반복 event 거부·같은 시각 순서·변경 C/A/나이/목록과 같은 원 RK4 격자·모든 수용 분할/최종 bytes·외부 raw 복원/실패 prefix·late source/권리·원 자료/GUI/WSL 보존이 수용 기준이다. old CP를 새 CP로 가장하거나 after program을 다시 prepare해 현재 상태를 재초기화하지 않는다. 실제 원본 [기존 잎 재개](../backend/app/crop_leaf_funded_birth_continuation.py)의 capture/global/segment 검증 패턴을 참조하며 그대로 호환된다고 하지 않는다.

계약/Context20–35+두 point/장부45–75+재개/분할/실패40–70+보존15–25=잠정120–205집중분으로 분해했다. 이는 완료 날짜 약속이 아니다. 이어 새 벡터의 동적 indoor-air threshold/분수 후보·실제 기관 시계/ID 결속→공급 제한 길이/면적→불변 저장/같은 상태3D→한 작기/생산·자원/경제·거시·수급/자율 비교다. 실제 품종 allometry/독립 국내 측정0건·VTC 권리/대응 측정 미확인·새 실제 자료/계수 채택0·G0–G4=not_assessed/R2=not_approved다. 실제 자료 확보는 합성 개발과 병행하고 예측/추천 게시 조건은 유지한다. 전체 완료일은 자료 확보/후속 분해 전 미정이며 전체 goal은 active/incomplete다.
