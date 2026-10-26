# 명시 줄기·뿌리 탄소 재고의 순간 공동 계산 — 2026-10-27 KST

[입출력/수지 계약](../contracts/crop-stem-root-carbon-stock-rhs-v1.md)과 [구현](../backend/app/crop_stem_root_carbon_stock_rhs.py)을 **자체 합성 순간 RHS**로 수용했다. 명시 기관별 현재 C_i/제거 R_i만 권위이며 같은 floor의 정확 binary64 합계를 한 번 반올림해 [원 배분 공동 RHS](stem-root-partition-climate-rhs-20261027.md)에 조립한다. 집계 stem_root를 따로 입력하거나 중복 전진하지 않는다. 선언 기관 목록은 새 합성 상태의 완전한 재고이며 기존 저장 geometry나 aggregate로 실제 초기 C를 추론한 것이 아니다.

원 source/잎·기후·배분을 같은 stage에서 각각 한 번 계산한다. 원 G/성장 원가·buffer 환급/성장호흡·잎/과실/기후와 source 원문을 보존한다. 원 총 줄기·뿌리 M을 정확 ΣC_i에 대한 C_i 비율로 나누는 명시 연구 정책이며 기존 공통 온도의 선형 유지호흡 식/고정 profile을 재사용했다. 합계 C=0이면 원 M=0인 별도 분기다. 새 계수·기관별 호흡 검증·탄소→길이 법칙이 아니다. 선행 [1차 문헌/권리·초기 재고 간극](stem-carbon-growth-primary-sources-20261027.md)을 유지한다.

각 C_i′=g_i−M_i−R_i이며 각0재고에서 음의 미분을 거부한다. 전체 수지가 닫혀도 개별 고갈은 허용하지 않는다. 명시0재고의 유입으로 제거를 충당하는 연속 flow-through와 양의 현재 재고에서 음의 순간 미분은 가능하다. 제거/미분을 clipping하거나 마지막 기관에 반올림 잔량을 몰지 않는다. 최상위 stem_root 미분/총 M은 실제 기관 미분/호흡 합계의 파생 진단이다. 실제 잎·기관 합계와 원 과실/P/buffer/성장호흡으로 전체 C/기관 수지를 다시 검증한다.

실제 native CLI의2026-10-26T18:25:52.286Z turn context에서 **gpt-6.1-sol/xhigh**를 확인했다. 관측은18:26:35.221506Z이며 raw LF SHA는 `743f612552083df8183f0de90f0559b6ca869db493b67584380ba625efeb7993`이다. 이 세션에서 판단/구현했으며 재귀 CLI0·새 외부 자료/품종 계수 채택0이다.

## 검증과 실제 경계

| 범위 | 실제 결과 |
|---|---|
| 최종 집중 회귀 | 신규278 + 기존 공동 RHS96/배분58/잎 재고101 = 고유533검사 통과 |
| 정상 수치 | 원6조건 ×4재고(양/일부0/비정확 소수 합계/전체0) ×3줄기 sink ×3잎 sink =216조건. 독립 Decimal 원 M 식·기관 M/미분·정확 합계/전체 C/기관 수지·원 비탄소/나머지 값 보존 |
| 고갈/명시성 | 개별/합계0·정확 flow-through와 nextafter 한계·root-only/마지막 root/순서·같은 per-floor 값·중복 aggregate 입력 사전 거부 |
| 변조/오류 | 닫힌 schema/단위/ID/root/floor·원 code/profile/input/조립 집계/목록/재해시 출력·유입 수지·원 source hold·양수 underflow/overflow·행/bytes cap 거부 |
| 호출 | stem joint/leaf stocks/leaf joint/climate/leaf partition/stem partition/carbon/P/area-heat/vapor exchange의10함수가 target RHS당 각1회 |
| 독립 fresh | 새 Python 프로세스2개가 각각72조건/1,944수치를 대사. 두 출력11,458,109bytes가 완전히 같고 SHA `579860a0233cbf1404514660a852ddd7353556d1543fec67152c251cac373fa9` |
| fresh 비용 | fixture 준비 뒤10함수 각각72회. socket/하위 프로세스/파일 write-open 호출0·FastAPI/SQLAlchemy/psycopg import0 |
| 실제 출력 크기 | 같은 짧은 ID1/128/256기관 출력159,207/259,902/362,168bytes 통과.512기관은 새512KiB 출력 cap hold. 원 전체512잎 요청528,002bytes의 별도 hold도 그대로 유지 |

처음 새 모듈 부재로 수집 오류1건을 확인한 뒤27검사가 통과했다. 이후 profile 원문/hash를 유지한 채 cStemM/rgr의 메모리 값만 바꾼 두 반례에서 **2실패**가 났다. 이 새 경로가 사용 계수 사전 전체와 고정 원문을 직접 대사하도록 수정했다.525검사가 통과한 뒤 잎 tuple을 JSON capture가 list로 바꾸는 두 반례에서도 **2실패**를 확인했다. 원 leaf_ids/leaves의 list 조건을 capture 전에 검사하는 수정 후 최종533검사와 fresh를 통과했다. 앞선 시도/실패 로그는 보존한다. 기존 수용 모델을 소급 수정하지 않았다.

WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도에서 순차 실행했다. 최종533검사의 관측 최대 PID/합계 RSS는66,572,288/129,736,704bytes, fresh는86,745,088/182,042,624bytes였다. 종료 후 소유 프로세스0·FD4→4·원4,500항목을 보존했다. Windows/전체 호스트 메모리 계측이나 전체 backend/frontend 검사로 확장해 말하지 않는다.

기존 SDK68/배분79/공동 RHS84/저장3D104 source 및 각 output 지문, 공개4,732파일, private:false132blob과 이전 GUI1,502파일 bytes/metadata, 현재 봉인 GUI4,865파일 hash, 원 최대 요청 및5175/5180 HTTP200을 보존 검사했다. [구조화 증거](artifacts/stem-root-carbon-stock-rhs-20261027.json)를 남긴다. [기존 저장3D834시점](complete-crop-stored-replay-20261027.md)은 같은 빌드이며 새 재고 RHS는 **UI/runtime 미연결**이다. 새 browser·DB/API/worker·전체 주앱 build·시간 전진/작기·실제 품종 검증은 실행하지 않았다.

## 다음 단계와 남은 근거

다음은 이 기관 재고와 기존 잎 C_i/나이/면적·과실/기후를 **같은 네 RK4 stage에서 전진하는 짧은 고정 기관 목록 적분**이다. 기존 [개별 잎 동역학](../backend/app/crop_leaf_carbon_stock_dynamics.py)의 격자/장부를 비교 기준으로 삼되 독립 stem_root aggregate 상태를 제거한다. 각 stage의 현재 C_i 합계만 source에 조립하고 실제 기관 유입·호흡·제거 적분량과 재고 차이/전체 C·원 열/물 장부를 독립 대사한다. 면적 곡선은 아직 별도 연구 가정이며 공급 제한 법칙으로 승격하지 않는다.

첫 적분 수용 뒤 분할 재개/실패 prefix·초기 이력/미배정 잔량·새 기관 초기 탄소 비용과 source/geometry 계보를 순서대로 연결한다. 기존 aggregate 재고를 임의 배분하거나 aggregate와 개별 재고를 모두 적분/비례 보정하지 않는다. 저장 결과/같은 상태3D와 한 작기 생산·자원/경제·거시/수급/자율 비교는 그 뒤다.

[VTC 후보](artifacts/stem-root-allometry-data-screening-20261027.json)의 권리/대응 측정 구성은 미확인 그대로다. 실제 품종 allometry/초기 이력·독립 국내 측정0건·새 실제 자료 채택0이며 G0–G4=not_assessed/R2=not_approved다. 다음 고정 목록 적분은 계약/벡터20–35분+stage/장부20–40분+독립/고갈/거부45–75분+보존10–20분의 잠정95–170집중분으로 분해한다. 이는 실행 보장이 아니며 전체 완료일은 자료 확보와 후속 분해 전 미정이다. 전체 goal은 active/incomplete다.
