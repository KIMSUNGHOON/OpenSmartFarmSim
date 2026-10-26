# 초기 기관 탄소와 저장 줄기·원 탄소 상태의 연결 — 2026-10-27 KST

[계약](../contracts/crop-stem-root-initial-binding-v1.md)·[구현](../backend/app/crop_stem_root_initial_binding.py)을 자체 합성 입력의 초기 출처 연결로 수용한다. [기관별 재개](crop-stem-root-stock-continuation-20261027.md) Context를 실제 선택 저장 stem과 **별도로 저장한 원 잎 탄소 결과의 초기 sample0**에 연결했다. 새로운 시간 전진·출현·공급 제한 형상이나 실제 품종/한 작기 예측을 수용한 단계는 아니다.

원 aggregate stem/root C를 새 Context 자체에서 재생성해 검증하는 순환을 피했다. 독립 원 crop 기록의107+3n 상태와 새106+3n+m 초기 상태의 집계 projection을 canonical 값 그대로 대사한다. 원 요청/정규 program의 나머지·잎 ID/C/나이/면적·초기 면적 영수증/D0·curve residual·forcing/단위·4profile도 보존한다. 임의 중간 crop sample을 초기값으로 재정규화하는 기능은 없다.

저장 stem에는 면적·C 근거가 없다. **한 추적 shoot를 명시 model floor에 연결하는 별도 자체 합성 선언**을 요구하며 원 stem의 측정 footprint/재식밀도라고 제시하지 않는다. 실제 선택 초기/저장 상태의 UTC·shoot ID·절간 순서/완전한 ID와 별도 root를 검사한다. 후기 선택에는 실제4번째 절간이 있어 초기3개만 선언하면 보류한다. 개별 C_i는 모두 명시 입력이다. 길이/면적/aggregate로 C_i를 역산하거나 미배정 C를 root에 몰아넣지 않는다.

원 aggregate C/제거와 정확 binary64 개별 합계를 한번 반올림한 값을 대사하고 **exact signed residual**을 분수로 남긴다. 합계가 다르면 `CARBON_BALANCE_HOLD`와 signed 미배정/초과 잔량을 반환한다. 한번 반올림한 값이 같아도 sub-ULP 잔차를 숨기지 않는다. CH₂O 기준이며 생체중/건물중/원소 C 변환은 수행하지 않는다.

실제 native CLI turn context2026-10-26T19:54:01.762Z는 **gpt-6.1-sol/xhigh**, 관측19:54:31.443891Z/raw LF SHA `3a70c9f5f68adcd807592e89eb359a3653a5f20c93f7c0efac87d0745f4a068e`다. 현재 세션에서 판단/구현했고 재귀 CLI0·새 외부 자료/품종 계수 채택0이다. [기존 1차 문헌/권리 조사](stem-carbon-growth-primary-sources-20261027.md)와 [VTC 보류](artifacts/stem-root-allometry-data-screening-20261027.json)를 유지한다.

## 검증 범위

| 검사 | 실제 결과 |
|---|---|
| 신규/관련 | 신규46 + 기존 잎 탄소 artifact/유리수 줄기 artifact134 = 고유180검사 통과. 전체 backend/frontend 검사는 아니다. |
| 실제 source | 6조건, 초기−1/실제 저장0/1을 각2번 선택. 원 전체 상태·완전한3/4절간/별도 root·실제 시각/명시 footprint·4profile·권리/hash를 대사했다. 초기 C 배분은 자체 합성 선언이며 측정값이 아니다. |
| 잔량/0 | C 부족/초과의 signed 잔량과 제거 불일치는 보류, 명시 root C=0은 허용했다. root2000의 nextafter 변경으로 한번 반올림한 합계20000을 유지하는 경우 exact 잔차−1/4398046511104 mg_CH2O/m2_floor를 보존했다. |
| 변경/거부 | 닫힌 선언·bool index/개수·미지원 basis·다른 shoot/floor/시각/원 상태·leaf/순서/누락·권리·code/current/late raw 변경을 거부했다. 실제 소유 시험 폴더 교체도 열린 store handle로 감지했다. 원 source를 수정한 시험은 아니다. |
| 독립 원 상태 | 새 seed/manifest를 자체 재해시해 buffer 또는 초기 면적 영수증을 바꿔도 별도 원 crop 기록과의 대사에서 보류했다. 자체 재해시를 신뢰 발급으로 취급하지 않았다. |
| 별도 프로세스 | producer/consumer 각1개·각6문맥. 원 요청/정규 program/seed/manifest hash와6개 연결 결과의 canonical bytes가 같고82개 소유 source 파일의 bytes/metadata가 보존됐다. 연결 결과 크기는23,142–25,559bytes이며 모든 최대 입력의 보증은 아니다. |
| 호출/부작용 | 각 프로세스의 문맥 준비6회 뒤 연결6회 동안 RHS/재준비/과거 전진·원 줄기 initialize/advance·DB connect/socket/Popen/write-open/BlobStore.put0. 기존 저장 모듈을 통해 psycopg는 import되며 연결0과 구별한다. |
| 권리/출력 | 원 crop/stem/선언 권리를 보존하고 하나라도 redistribute=False면 재배포 승인False다. 법적 권리 진본/현재 농장 권한/G0를 승인하지 않는다. scope=software_research_only, time_kind=synthetic_model_clock_not_observation, G0–G4=not_assessed다. |

fresh producer261,182bytes/SHA `00cfcc35d3c0688254236fe2978467303349ac1a69ef60d5c34442dade6bc047`, consumer261,182bytes/SHA `58ee09deba7e2794247ed4b1323ca4efae710d6203fe0f1bd42eab2ab1408f07`을 비공개로 보존했다. 타임스탬프/역할을 포함한 외부 packet은 다르며 내부6개 연결 결과 bytes가 동일하다. redistribute=False인 원 packet/blob는 공개하지 않았다.

초기 missing-module RED를 보존했다. 첫 fixture 시도는28통과/3실패였다. 후기 source에 실제4번째 절간이 있는데3개만 선언한2사례를 수정했고, floor=2 시험은 연결 전에 기존 온도 domain에서 보류돼 유효한1.125로 source mismatch를 시험했다. 생산 식/열적 domain을 완화하지 않았다. 합성 시간 구분 필드 누락도 별도 RED에서 확인하고 추가했다. 최종46/134에 실패 시도를 더해 합산하지 않는다. 중간 실행1회는 pytest 상대 경로 오류로 검사0/exit4였으며 올바른 경로로 최종46개를 실행했다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도를 유지했다. 신규46검사 최대 PID/합계 RSS는82,022,400/141,635,584bytes, 관련134는172,711,936/232,464,384bytes, fresh는54,816,768/132,268,032bytes다. 각 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. Windows/전체 호스트 자원 계측은 아니다.

이전 CP110/short103·저장3D104 source 지문·공개4,732파일·private:false132blob·원 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일·원 최대 요청·5175/5180 HTTP200을 보존 검사했다. [구조화 증거](artifacts/crop-stem-root-initial-binding-20261027.json)를 남긴다. [기존 저장3D](complete-crop-stored-replay-20261027.md)와 [5180 미리보기](http://localhost:5180/complete-crop-replay.html)(10/27 13:09KST 원 만료)는 같은 빌드다. **새 연결은 UI/runtime 미연결**이며 이번에 새 browser/DB/API/worker·전체 주앱 build를 실행하지 않았다. 기존512기관/원512잎 byte-cap·최종 R2/첫 shader warning 보류를 유지한다.

## 다음 단계와 외부 의존성

다음 한 단계는 **새 절간의 명시 초기 C와 성장호흡 원가를 같은 출현 점에서 한 번만 반영하는 순수 계산**이다. 초기 source 연결을 선행으로, 원 cStemG/profile 판본·실제 부모/출현 수치 시각·buffer 차감/부족/전체 C와 point 장부·비대상 상태 보존을 수용 기준으로 한다. 원가/임의 C_i를 형상에서 만들거나 무료 기관/중복 차감을 허용하지 않는다. 합성 초기 비용은 검토 가능한 별도 가정이며 실제 allometry/품종 검증을 대신하지 않는다. 원가/source 검토15–25분+점 전이20–40분+독립/실패25–45분+보존10–20분의 잠정70–130집중분으로 분해했다. 실행 보장이나 전체 완료 날짜는 아니다.

그 뒤 가변 기관 목록 재개→공급 제한 길이/면적→불변 저장/같은 상태3D→한 작기/생산·자원/경제·거시·수급/자율 비교 순서다. VTC 권리/대응 측정 미확인·독립 국내 측정0건·새 품종/실제 자료 채택0·G0–G4=not_assessed/R2=not_approved다. 실제 자료 확보는 합성 개발과 병행하며 예측/추천 게시에는 독립 관문 근거가 필요하다. 전체 완료일은 자료 확보와 후속 분해 전 미정이다. 전체 goal은 active/incomplete로 유지하며 도구의 기존 목표를 교체 완료라고 표시하지 않는다.
