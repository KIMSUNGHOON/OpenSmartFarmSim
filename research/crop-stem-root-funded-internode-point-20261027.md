# 명시 새 절간의 탄소 조달점 — 2026-10-27 KST

[계약](../contracts/crop-stem-root-funded-internode-point-v1.md)·[구현](../backend/app/crop_stem_root_funded_internode_point.py)을 **검증된 현재 CP에서의 명시 새 구조 형성점**으로 수용한다. [초기 source 연결](crop-stem-root-initial-binding-20261027.md)과 [기관별 재개](crop-stem-root-stock-continuation-20261027.md)를 실제 호출한다. 임의 길이/질량을 추정하거나 자동 출현을 판정한 단계는 아니다. 새 CP/시간 전진·새 잎 점·가변 목록 재개·형상 feedback·불변 저장/3D 연결은 남아 있다.

새 절간의 초기 C는 독립 명시한 mg_CH2O/m2_floor다. 실제 원 crop/stem의 완전한 초기 연결을 전/후 재검증하고 전체 canonical 연결 hash를 입력에 결속한다. 외부에서 신뢰한 원 CP raw SHA/문맥·현재 상태/장부를 검증하고 실제 CP의 exact step×index/원 floor와 실제 기존 internode 부모 ID를 맞춘다. root/같은 batch의 새 기관을 부모로 삼거나 기존 ID/중복 event를 채택하지 않는다. 원 stem의 측정 밀도·allometry·기관 실질량 승인은 없다.

[원 고정 프로필](../fixtures/crop-growth-reference-parameters-v1.json)의 **cStemG=0.3**을 사용한다. [원 식/단위 판단](stem-carbon-growth-primary-sources-20261027.md)의 줄기·뿌리 성장호흡 비용이며 농장 품종 계수로 새 채택한 값은 아니다. 정확 binary64 새 질량 합 S에 대해 structural=round(S), Rg=round(cStemG×S), debit=round((1+cStemG)×S), B_after=round(B_before−debit)>0이다. 기존 잎 조달점의 원 산술을 계수만 명시해 재사용했다. cLeafG/유지호흡을 대입하거나 연속 조달분을 환급·재차감하지 않는다. 이미 지불한 숨은 조직의 출현은 별도 이동 모델이 필요하며 이 추가 조달 정책의 대상이 아니다.

원106+3n+m 상태의 buffer0만 바꾸고 끝에 명시 새 C를 붙인다. 기존 leaf age/A/C·모든 기존 stem/root C·과실/기후U103/Ta104/W105·원 초기 영수증/D0·root/ID/곡선은 보존한다. leaf 면적/열용량/수관 현열의 점 변화는0이다. 나타낸 전체 C 변화는−Rg이며 chemical heat/완전한 물질·열 첫 법칙은 포함하지 않는다. 원 CP/연속 장부/prefix와 별개로 buffer·new stock·각 새 기관·whole-C point 장부를 보존한다. 반복 계산은 동일하지만 **한 번 채택/재개를 보장하는 CP는 아직 발급하지 않는다**.

실제 native turn context2026-10-26T20:32:18.916Z는 **gpt-6.1-sol/xhigh**, 관측20:34:19.053262Z/raw LF SHA `dc70b55481f3b56f1e44a2ac831846f2fb304f82cc08a1c670bfb564bfd52876`이다. 현재 CLI 세션에서 판단/구현했고 재귀 CLI0·새 외부 자료/품종 계수 채택0이다. scope=software_research_only, time_kind=synthetic_model_clock_not_observation, G0–G4=not_assessed다.

## 실제 검증

| 범위 | 결과 |
|---|---|
| 집중/회귀 | 신규54 + 기존 초기 연결46/잎 조달점74/기관 CP148 = 고유322검사 통과. 전체 backend/frontend 검사는 아니다. |
| 현재 부모/보존 | 6조건의 초기·완료 CP에서 단일/batch·실제3/4절간 source와 별도 root를 사용했다. 비대상 현재 상태·곡선/D0·원 CP/prefix/누적량/장부를 보존하고 복사·같은 입력 반복·실제 raw SHA를 대사했다. |
| 독립 산술 | 단일/소수/batch의 Decimal110 원 비용·buffer/whole-C를 검사했다. 별도 app-free parent가 fresh6결과의 비용/버퍼·비대상 상태/새 C·전체 수지752항목을 독립 Decimal110으로 대사했다. 최대 exact whole-C 잔차는 원64ULP 예산의0.0007812976837158203125배다. 농업 타당성 검증이 아니다. |
| 거부/한계 | 잘못된 source/CP/context hash·시각/floor/부모/root/새 ID/중복·권리/양·단위/부족·current/late code/source/profile·after domain을 거부했다. 예상 밖 RuntimeError는 정상 hold로 숨기지 않는다. 결과256기관 통과·512하위 출력 cap hold·513사전 거부를 유지했다. 모든 최대 입력 지원 보증은 아니다. |
| 호출/부작용 | 각 point에서 현재 CP RHS1회+after RHS1회, 초기 재준비/과거 전진/초기 면적 정규화·DB/socket/Popen/write-open/BlobStore.put0. 기존 저장 모듈의 psycopg import와 연결0은 구별한다. source 권리/입력 권리는 명시 보존하며 원 redistribute=False를 True로 승격하지 않는다. |
| 별도 프로세스 | producer/consumer 각1개·6문맥/6동일 canonical point 결과. 원82개 source 파일 bytes/metadata를 그대로 재사용했다. 각 프로세스 Context 준비6회 뒤 point RHS12회, producer는 준비 중 CP6step을 계산했고 consumer는 CP raw를 받아 과거 전진0이다. |

fresh producer542,806bytes/SHA `31811f305783f78891ecb3ae79f0f8abde9f40a1822bdea7c7d51127eb898398`, consumer542,806bytes/SHA `4d1a7dacc781ce6181156c529fe9a01adf697e089a6159e20aeb2d8de47b4c0a`이다. 역할/관측 시각이 다른 외부 packet 전체를 같다고 하지 않으며 내부6결과만 동일하다. 개별 point 결과 관측 크기는65,770–71,564bytes다. raw/source는 자체 합성 redistribute=False로 비공개 보존하고 공개 JSON에는 hash/수량만 남겼다.

missing-module RED와 첫15실패/26통과를 보존했다. 실제 읽기 전용 profile.values를 deepcopy할 수 없어 dict snapshot으로 고쳤으며 계수/식/허용오차 변경은 없다. 다음41검사는 통과했다. 확장 시52통과/1실패는512기관 시험의 누적 초기 C가 먼저 funding hold를 일으킨 경우다. 한도 시험의 명시 C를 작게 수정한 뒤 확장53을 실행했고 부족 판정을 완화하지 않았다. 이 시도들을 최종322에 더하지 않는다. 후속 재개에서 원 token을 가장하지 않도록 검증된 현재 데이터에 적용하는 내부 `_jump`를 분리하고 새 기관을 다음 점의 부모로 사용할 수 있음을1검사로 추가했다. 추출 중 지역 별칭 누락의39실패/15통과를 보존하고 이를 수정한 최종54검사/fresh v2를 수용했다. 기존 관련268검사는 원 소스 지문이 그대로인 범위에서 재사용했으며 다시 실행했다고 하지 않는다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도를 유지했다. 신규54의 최대 PID/합계 RSS는84,316,160/144,744,448bytes, 회귀268은101,232,640/161,763,328bytes, fresh는56,848,384/135,548,928bytes다. 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. 전체 호스트 자원 측정은 아니다.

초기 연결113/이전 CP110·short103/저장3D104 지문·공개4,732파일·private:false132blob·원 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일·원 최대 요청·5175/5180 HTTP200을 보존 검사했다. [구조화 증거](artifacts/crop-stem-root-funded-internode-point-20261027.json)를 남긴다. [기존 저장3D](complete-crop-stored-replay-20261027.md)/[5180 미리보기](http://localhost:5180/complete-crop-replay.html)(10/27 13:09KST 원 만료)는 같은 빌드다. **새 point는 UI/runtime 미연결**이며 새 browser/실제 DB/API/worker·전체 주앱 build를 실행하지 않았다. 기존 최대 요청/최종 R2/첫 shader warning 보류를 유지한다.

## 보완한 의존성과 다음 수용

기존 [잎 조달점](../backend/app/crop_leaf_funded_birth_point.py)은107+3n/aggregate stem 벡터이고 새 Context는106+3n+m이다. 원 CP token을 가장하거나 stock index를 바꿔 호출할 수 없다. **다음 한 단계는 새 벡터의 잎 조달점 이식**이다. 기존 초기 면적/새 leaf0 나이·명시 C/cLeafG 비용·입력 T/열용량/유입 현열을 유지하고 U103 및 leaf 블록 삽입/후미 stem C 보존을 검증한다. 새 잎의 ID/부모·source/시각/권리·buffer·전체 C/K/U와 독립 산술/거부·원 자료/GUI/WSL 보존이 수용 기준이다. 기존 old leaf module은 수정하지 않는다. 원 source/계약10–20+이식20–35+독립/실패25–45+보존10–20=잠정65–120집중분으로 분해했으며 완료 약속은 아니다.

그 뒤 두 종류의 점을 한 번 채택하는 가변 기관 목록/같은 격자 재개→새 상태 벡터의 동적 기온 threshold/분수 후보·실제 기관 시계 결속→공급 제한 길이/면적→불변 저장/같은 상태3D→한 작기/생산·자원/경제·거시·수급/자율 비교다. 원 old fractional 후보/CP를 새 typed handle로 가장하지 않는다. 실제 품종 allometry/독립 국내 측정0건·VTC 권리/대응 측정 미확인·새 실제 자료/계수 채택0·G0–G4=not_assessed/R2=not_approved다. 실제 자료 확보는 합성 개발과 병행하고 예측/추천 게시 조건은 유지한다. 전체 완료일은 자료 확보/후속 분해 전 미정이며 전체 goal은 active/incomplete다.
