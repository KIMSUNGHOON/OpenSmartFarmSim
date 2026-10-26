# 새 개별 기관 CP의 한 RK4 구간과 첫 출현 기준 — 2026-10-27

[계약](../contracts/crop-organ-next-threshold-v1.md) · [모듈](../backend/app/crop_organ_next_threshold.py) · [검사](../backend/tests/test_crop_organ_next_threshold.py) · [기계 증거](artifacts/crop-organ-next-threshold-20261027.json).

현재 가변 잎/줄기/뿌리 CP에서 실제 다음 RK4 한 걸음과 첫 미소비 출현 기준의 수치 근 구간을 계산했다. 최종 신규83/관련27, 총110개 검사가 통과했다. 새 기관·사건 상태·일정 채택/분수 CP·형상/새3D는 아직 생성하지 않는다. 기존 [현재 시계124검사](crop-organ-current-shoot-clock-20261027.md)와 [가변 재개406검사](crop-organ-funded-continuation-20261027.md)의 산출물·증거를 보존했다.

## 실제 산출물과 방법

`probe_next_shoot_threshold`는 실제 Context/외부 신뢰 raw CP SHA·명시 exact 초 허용 폭을 검증한다. 현재 CP RHS1회를 첫 stage로 사용하고 원 step/global index의 k2/k3/k4/endpoint RHS4회를 계산한다. 원106+3n+m state/모든21+3n+3m 유량·현재 C/A/나이/D0·초기 source·point 이력/장부를 유지한다. 네 stage의 state/rates/flux와 명시 state 배치/유량 이름·단위/순서·hash를 반환한다. prospective endpoint는 원 sample/segment/lifetime/개별·전체 장부·cursor/prefix와 같지만 integrator checkpoint로 발급하지 않는다.

방법은 [Izgin-Melnikov 원 논문 §4.2 식(28)](https://link.springer.com/article/10.1007/s42967-025-00480-8)의 명시 고전 RK4 3차 연속식이다. 기존 수용된 근 계산의 정확 유리수 다항식/도함수 최소/최대128이분법을 새 상태 배치의 실제 실내기온에 적용했다. 논문의 implicit MPRK/양수 보장은 채택하지 않는다. 원 출처/판본/일자 정밀도·raw SHA/CC BY4.0와 제3자 예외/검토자는 기계 증거에 보존했고 공식 출판사 페이지의 식/권리를 다시 확인했다. 새 농업 자료/품종 계수는 채택하지 않았다.

실제 선택 초기 shoot의 발달 이력과 현재 원 lifetime 기온 적분에서 왼쪽 나이를 계산한다. 첫 미소비 `next_threshold_exact`/순번/phyllochron을 원 source에서 읽고 호출자가 임의로 바꾸거나 이미 지난 기준을 건너뛰지 않는다. 왼쪽이 기준 이상이면 `SCHEDULE_HOLD`다. 최소 도함수가 양수여야 하며, 이상적인 다항식 우단과 저장 endpoint의 통과 판정이 다르면 `ROUNDING_HOLD`다. 보정/clip은 하지 않는다. 같은 판정으로 미통과면 `no_crossing`, 통과면 `threshold_bracket`/원 interval 안 exact 시각 범위와 signed residual을 반환한다. 같은 구간의 후속 기준을 소비하지 않는다.

## 통과한 검증

- 최종83개: 실제6조건×양쪽 point×초기/중간/끝전 CP의 모든 endpoint 필드/장부·현재 시계와 일치, 복수점/동일 시각 순서·원 C/A/D0/CP/Context bytes, 실제07시 source의 네 crossing/독립 Decimal200 근, RHS5/과거 전진·point·초기화·CP 발급0, exact 폭/단위/정밀도·완료/이미 지난 일정·반올림·source/권리/late code/profile/store 변경·stage 실패/RuntimeError·반환 복사본·원 CP/응답 cap을 검사했다.
- 기존 근 계산27개를 현재 원 source에서 재검사했다. 이 검사는 수식 차수 조건·비선형 국소 수렴·우단 근/도함수 내부 최소·양수 stage의 비단조 반례·기존 stored replay/rights/fence를 포함한다. 과거 단계의124/406을110에 더하지 않는다.
- missing-module red를 보존했다. 최초 prototype68검사는 stage 배치/유량 단위·이름을 명시하기 전 소스의 결과다. 추가 검사 첫 실행은 존재하지 않는 `derived.air_temperature`를 변조하려 해1실패/14통과했다. 실제 `air_capacity` 필드를 사용하도록 검사를 고쳤고 최종 소스 전체83개를 다시 실행했다. 공식·기온 domain·수치 허용 오차를 바꾸지 않았으며 prototype/실패 수를 최종 통과에 중복 합산하지 않는다.

최종 증거 포장 첫 검사는 전체 Context snapshot SHA와 manifest 기반 Context ID를 동일시해 실패했다. 실제 manifest SHA를 비교하도록 검증기를 수정했다. 원 계산/입력·110검사 증거는 변경하지 않았고 첫 실패를 보존한다.

## 별도 프로세스와 독립 산술

두 프로세스가 원6 Root·12개 실제 mixed Context를 복원하고18개 실제 다음 구간을 각각 계산했다. 기관 목록/같은 원 step의 결과18개가 일치했다. 16개 미통과와 실제 두 crossing을 포함하며, 실제 수용된 재개의 endpoint CP와 모든 prospective endpoint 필드가 같았다. Context 복원 RHS0/각 probe RHS5, 총90회였고 probe 중 과거 advance/point·기존 면적 초기화·새 CP 발급/DB/CLI/network/write0이었다. 준비 단계의 producer571/consumer6 RHS는 별도로 기록했다.

앱을 import하지 않은 별도 유리수 산술로 binary64 각 연산의 반올림 순서를 재현해 stage/endpoint 상태8,832값·segment/lifetime 적분1,728값과 shoot 나이36개·연속식72점을 대사했다. 기존 장부의 예산750항목도 확인했다. 두 근은 독립 Decimal200/256이분법으로 반환 범위에 포함됨을 확인했다. RHS 식은 기존 컴포넌트를 공유하며 독립 ODE/생물학 모델 검증으로 부르지 않는다.

자체 합성07시 원점에서 두 근은 각각 약177.455597초/252.453469초다. 두 반환 폭은1/1,048,576초이고 명시1/1,000,000초 이하이다. 이 폭은 이 연속 다항식의 근 고립만 제한하며 ODE 이산화·누적·계수/측정·실제 출현 오차를 제한하지 않는다. 실제 시각/품종 예측으로 게시하지 않는다. 관측 결과40,410–59,342bytes/state120–124이며 전체 최대 목록 지원으로 확대하지 않는다. 각 private packet은18결과/원 CP·문맥을 모은 검증 포장이고 개별 API cap의 대체가 아니다.

## 보존과 남은 의존성

원82 source 파일의 bytes/metadata·기존128 source/1 output 지문·private:false132 blobs/기존 공개 입력·export/경계 입력·원512요청 byte-cap hold와 보호된3D 빌드4,865파일을 보존했다. 모든 phase는512MiB/PID·소유+보호1GiB/600초/4MiB log·0.25초 sample·원4,500 감시 항목/source 안에서 종료했다. 소유 잔여0/FD4→4·보호 identity를 확인했다. HTTP5175/5180=200과5180 원 만료13:09KST를 유지하고 연장하지 않았다.

이번 기능은 UI/API/worker 미연결이다. 전체 backend/frontend suite·새 browser/DB/API/worker·전체 주앱 build를 실행하지 않았다. 실제 independent 국내 측정0·VTC 코드/자료 권리/대응 측정 미확인·실제 allometry/품종 채택0·512 byte-cap·최종 R2/첫 shader warning이 남는다. 한 작기/생산·자원/경제·거시/수급·자율 비교·제품 통합/G0–G4/전체 goal과 전체 완료일은 미완료·미정이다. hosted CI는 실제 push HEAD의 조회로 별도 기록하며 로컬110을 hosted green으로 바꾸지 않는다.

## 다음 수용 단위와 일정

다음은 같은 첫 후보의 upper exact 시각에서 전체106+3n+m 상태와 모든 partial 유량을 계산하는 `stem-root-stock-fractional-candidate`다. 실제 네 stage/hash/배치·선택 source 시계와 결속하고 exact 시각/원 C_i/A/leaf·stem/root 목록·local/기존 prefix+point/global 장부·domain·수치 반올림 차이를 검사한다. 원 endpoint를 임의 보정하지 않고 같은 시각의 부분 step1/2/4 축소 비교/독립 산술·fresh/실패 보존을 통과해야 한다. 여전히 새 integrator CP/기관/일정 채택은 발급하지 않는다.

잠정 공수는 원 계약20–35+전체 상태/부분 유량30–55+장부/단계 축소40–70+fresh/실패20–35=110–195집중분이다. 이번 한 구간 단계의90–155집중분 예상은 실제110검사/별도18구간·두 근 수용으로 대체한다. 이후 material point/일정 채택·원 격자 잔여 재개→기관 시각/ID→공급 제한 형상→불변 같은 상태3D→한 작기/생산·자원/경제·거시/수급/자율 비교로 이어간다. 실제 자료 확보는 합성 개발과 병행하며 예측·추천 게시 게이트를 유지한다.

조사·설계·구현은 현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 수행했다. 실제 turn/model/effort·raw LF hash/관측 시각은 기계 증거에 기록했으며 재귀 CLI0이다. 코드는 검토 가능한 연구 산출물이며 관문 승인이나 농장 자료가 아니다.
