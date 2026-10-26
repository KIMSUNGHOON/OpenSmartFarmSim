# 줄기·뿌리 배분의 같은 시점 공동 계산 — 2026-10-27 KST

[새 RHS](../backend/app/crop_stem_root_partition_climate_rhs.py)가 기존 개별 잎/작물/기후 계산을 한 번 실행하고, 그 결과의 실제 줄기·뿌리 성장 유입 G를 [배분 산술](stem-root-carbon-partition-20261027.md)에 한 번 전달한다. buffer·stem_root·전체 성장호흡의 세 조정을 함께 적용하고 원 잎·과실·기후 계산과 source 결과를 보존한다. [계약](../contracts/crop-stem-root-partition-climate-rhs-v1.md)의 합성 순간 RHS 자식만 수용했다.

## 같은 source의 결속

호출자는 G를 입력할 수 없다. G는 원 `allocation.stem_root`에서 읽으며 유지호흡/제거 뒤의 상태 미분이 아니다. 원 leaf-adjusted allocation·같은 input_id/floor·4profile·원 code/raw 입력/계산 hash와 대사한다. 배분의 원 입력/정규 입력·정책/code/프로필/hash·기관 ID/순서/단위도 대사한다. 조정이0이면 원 값을 그대로 유지한다. 새 길이·질량 환산 계수나 생리 계수는 채택하지 않았다.

명시 배분처는 합성 internode/root_system이다. source에는 해당 기관별 현재 C 재고와 저장 geometry 계보가 없으므로 이 결속을 실제 저장 줄기 ID/초기 조직의 결속으로 확대하지 않는다. `organ_carbon_stocks=not_allocated_in_this_instantaneous_inflow_stage`, `geometry_binding=declared_synthetic_sinks_only`를 명시한다. 시간 전진·기관별 유지호흡/고갈 적분·출현 비용·길이/면적 feedback·worker/제품 UI는 후속이다.

현재 native Codex CLI context는 `2026-10-26T17:21:07.400Z`, model=`gpt-6.1-sol`, effort=`xhigh`다. `2026-10-26T17:25:57.120658Z`에 원 LF를 읽었고 SHA-256은 `c49727b884ddf08ed1fb53050babeded6491127b5d0a6ff88d4f1e969be30413`다. 기존 세션에서 판단/구현했으며 재귀 CLI 실행0·새 외부 자료/품종 계수 채택0이다. [선행 1차 문헌/권리 판단](stem-carbon-growth-primary-sources-20261027.md)을 재사용했다.

## 검증과 발견한 경계

| 범위 | 실제 결과 |
|---|---|
| 신규/관련 회귀 | 신규96 + 기존 배분58/잎 재고101 = 고유255검사 통과 |
| 정상 stage | 6개 원 사례 ×3개 잎 sink ×3개 줄기/root sink의54조합. 독립 Decimal 유입·조정·전체 C/기관 수지와 원 source/잎·과실·기후·나머지 미분 보존/동일 재실행 |
| 함수 호출 | source leaf stocks/leaf joint/explicit climate/leaf partition/stem partition/carbon/P/area-heat/vapor exchange의9개 구성 함수가 RHS 호출당 각각1회 |
| 거부 | caller G, root/순서·floor/단위, source/partition의 재해시한 잘못된 code/input/profile/scope/기관/유량, 원 source hold·code/profile drift·count/실제 bytes cap |
| 수용 범위 경계 | 명시 compartment1/512 정상과513/bytes 초과 hold. 이는 원 전체512잎 RHS 수용이 아님 |
| 독립 fresh | 새 Python 프로세스2개, 각각72조건/594수치 대사·동일9,712,560bytes, SHA `be5186c3959dc173861cef91e34c66ccb1c0e288c8c320b4753af8421960fabf` |
| fresh 호출/쓰기 | 원 fixture 준비 후 계측한9함수가 각각72회. socket/하위 프로세스/파일 쓰기 호출0, FastAPI/SQLAlchemy/psycopg import0 |

최초70검사와 확장252검사는 통과했다. 이후0재고 경계의 독립 회귀를 추가하자 **1실패/2통과**로 실제 간극이 드러났다. source에서는 줄기/root C=0에도 들어오는 G로 제거 유출을 충당할 수 있었다. 하지만 새 전부0 sink 정책이 G를 보류하면 제거만 남아 조정 뒤 미분이 음수가 됐다. 전체 탄소 수지는 여전히 닫힐 수 있으므로 그것만으로 검증이 끝나지 않는다.

조정 뒤 buffer/stem_root가0일 때 해당 미분도 비음수여야 하는 조건을 추가했다. 불가능한 stage는 `DEPLETED_STATE_HOLD`이며 제거/재고/미분을 임의로0 처리하지 않는다. 양의 유입으로0재고 flow-through가 가능한 경우와, 유입/제거가 모두0인 경우는 통과한다. 이 수정 뒤255검사와 fresh 전체를 다시 통과했다. 앞선 probe/검사·red 반례/이전 fresh 출력은 보존한다.

실행은 WSL PID512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도에서 순차 수행했다. 최종255검사의 관측 최대 PID/합계 RSS는64,888,832/128,020,480bytes, fresh는76,816,384/170,344,448bytes였다. 종료 후 검사 소유 프로세스0·FD4→4이고 기존 외형과 유한 수명 미리보기를 보존했다. Windows/전체 호스트 메모리를 이 수치로 측정하지 않았다.

원 SDK68/이전 배분79/저장3D104의 source/output 지문·공개4,732파일·private:false132blob·이전 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일 hash·원512잎 byte-cap hold와5175/5180 HTTP200을 확인했다. [구조화 지문/증거](artifacts/stem-root-partition-climate-rhs-20261027.json)를 보관한다. 기존 [저장3D](complete-crop-stored-replay-20261027.md)는 같은 자료/빌드이며 새 RHS는 UI/runtime 미연결이다. 전체 backend/frontend·새 browser·DB/API/worker·현장/실제 작기 검증을 실행했다고 하지 않는다.

## 다음 단계와 외부 의존성

다음은 **명시 줄기·뿌리 기관별 C 재고의 순간 RHS**다. 새 합성 상태에서 각 기관 C와 같은 floor/ID를 명시하고, 합계를 한 번 반올림해 source aggregate로 넘긴다. 독립 aggregate 입력/중복 전진을 허용하지 않는다. 원 전체 유지호흡을 명시 재고에 보존적으로 나누고 제거는 기관별로 명시한다. source 원가/유입/상태·원 C/비탄소 수지와 각0재고의 조정 후 고갈 조건을 검증한다. 합계가0이면0유지호흡의 명시 분기가 필요하며 임의로0 나눗셈을 피하거나 균등 재고를 만들지 않는다.

이는 새 명시 합성 재고의 계산 개발이다. 기존 aggregate를 과거 기관의 실제 C로 자동 분배하지 않는다. 원 저장 source를 채택하려면 명시 초기 재고 합계/계보 또는 미배정 잔량의 별도 추적이 필요하다. 첫 순간 재고 RHS 뒤에 공동 적분/분할 재개·새 기관 초기 비용·불변 저장/같은 상태3D를 연결한다. 공급 제한 길이/면적의 합성 법칙 개발과 실제 품종 allometry/독립 농장 자료 확보를 병행한다.

[VTC 자료 후보](artifacts/stem-root-allometry-data-screening-20261027.json)의 권리·대응 기관 측정 구성은 미확인 그대로다. 독립 국내 측정0건·새 실제 자료 채택0·G0–G4 `not_assessed`/R2 `not_approved`이며 생산량·자원 구매·미래 수익/거시/수급·자율 작물 순위의 승인은 없다. 다음 순간 재고 RHS는 입력/초기 재고·0분기 대조20–30분 + 구현20–40분 + 독립 수지/고갈/거부30–60분 + 보존/기록10–20분, 잠정80–150집중분으로 추정한다. 적분/작기/제품과 전체 완료일은 이후 실제 분해·자료 확보 전 미정이다. 전체 goal은 active/incomplete다.
