# 환기 공동 계산의 분할 실행·복원 — 2026-10-11

**2026-10-11 22:54 KST 로컬 수용.** [핵심3파일 계약](../contracts/crop-greenhouse-ventilation-continuation-v1.md)과
[기계 증거](artifacts/crop-greenhouse-ventilation-continuation-reference-20261011.json)를 기록한다.
새25장부 context/checkpoint이며 원 program의 계산식을 변경하지 않는다. UTC/저장/사용자 배포는 후속이다.

## 구현과 확인한 증거

source의 다른 forcing과 실외 입력을 분리해 보관하고, 매 현재 stage의 환기를 한 번만 합성한다.
원108상태·25연속/6사건 장부·10수지와 사건 후 환기 진단을 고정한다.
각 원 경계의 RK4→전역 수지→관리/현재 환기→수지→journal→선택 출력 순서와 각 원 덧셈 순서를 유지한다.
경계0 사건 전 initial-ready와 경계0 완료를 구분한다. 최종 bytes/prefix는 chunk 크기·실행 시각과 무관하다.
복원은 trusted raw digest와 현재 endpoint·10수지만 확인한다. 과거 적분/관리 사건을 다시 실행하지 않는다.
구22장부 타입/판본·입력/코드/정책/환경/프로필과 새 결과를 혼합하면 거부한다.

| 실제 검사 | 결과 |
| --- | --- |
| 새 checkpoint |175통과:10program×예산1/2/3/7/128=50구성·혼합 분할의 samples/events/마지막 상태·최종 bytes/prefix 정확 동일 |
| fresh 복원 |별도 Python5지점(next_index0/1/8/9/17), 과거 step/event 재실행0·현재 endpoint 공동 RHS/환기 각1회·이후 원 접미 결과/최종 checkpoint 일치 |
| 관련 회귀 |기존 continuation138 + 환기 program35 + 환기 stage51 =224통과 |
| 최종 계산 실행 |고유399통과/pytest166.47초; 원20895 child/tool exit0·guard167.037288670초 |
| 독립 수치 보존 |기존 Decimal80 fixture bytes 재생·6,480수치/72반분 비율>8 재대사; 새 농업 식/계수0 |
| 최대 구성 |512출력/128사건·512걸음, chunk128 이하5개·checkpoint64KiB/context2MiB 이내 |
| 실패/변조 |closed 상태/단위·배열 길이·진단/장부/10수지/cursor·trusted digest·판본/JSON 거부, 실제 domain/underflow·step/event/사건 후 환기 실패 prefix 보존 |
| 관측 WSL RSS |.25초 표본, 단일136,704,000/보호 포함 합729,317,376bytes;512MiB/1GiB 이내 |
| guard 보존/정리 |원본2,148·두 frozen source/기존 자산 보존, protected roots4 live·FD4→4·소유 잔존/PG/passfile0 |

실제 multiple16걸음/3사건/6chunk는 endpoint 검사를 포함해 joint111/환기89회다.
확인된 계산 자체는 joint105/환기83회이고 checkpoint 검사6회씩과 구분한다.
실패 trial 호출을 confirmed 호출로 보고하지 않는다. 중단/취소 예외는 정상 yield로 바꾸지 않는다.

첫 private smoke37070은 backend/tests import 경로 누락으로 exit1이었다. 경로를 고쳐9545 exit0·0.867770289초로 정확 일치를 확인했다.
첫 집중91511은165통과/2실패·62.865507868초였다. 벡터 변환이 상태의 추가 필드/단위를 버릴 수 있는 복원 결함을
변환 전 닫힌 수량·float64 정규형 검사로 고쳤고, immutable profile을 deepcopy하던 시험 기록 오류도 수정했다.
plant/cohort/climate의 단위·추가 필드/배열 길이·bool/int 변조8검사를 보강한 뒤 최종399개를 통과했다.
실패 원 로그/terminal의 해시는 기계 증거에 보존했다. 성공 계산 guard 합167.905059초이며 전체4guard 합231.120327초다.
준비/설계·코드/분석·기록 시간은 별도다.

최종 보존 원49863 child/tool exit0·0.608938532초로 기존234계산 파일 SHA·accepted source1,911/자산171,
두 HTTP200/index hash·현재 runtime/권리·검토/접속 파일 권한·로컬 링크1,999·diff check를 확인했다.

실제 native CLI는 `gpt-6.1-sol / xhigh`, turn timestamp `2026-10-11T13:38:36.657Z`,
context SHA `96aaf33f994e34737e77d81fce0986044f6dd6698fafd0e452748b569e845583`, CLI 재귀 실행0이다.
농업 근거/자료 권리는 [기존 원문 검토](crop-greenhouse-boundary-source-review-20261011.md)를 따른다.
새 package/build/API/Chromium/전체 CI·remote 검사는 실행하지 않았다. 사용자 서버 중단/전환0이다.

## 다음 한 단계와 외부 의존성

다음은 **새 판본의 원 elapsed index에 UTC를 결속**하는 별도 자식이다.
원 sample/event/last_confirmed의 microsecond UTC·격자/범위·UTC/KST, 임의 분할/fresh 동일·혼합 판본 거부와
UTC 부여 중 수치 적분/관리/RHS0을 수용한다. 기존 UTC helper 대조·새 identity0.25–0.5집중시간,
원 record 결속/닫힌 검사0.25–0.5시간, fresh·정밀도/자원0.25–0.5시간으로 잠정0.75–1.5시간이다.
이번 checkpoint의 이전2–4집중시간 추정은 native22:38 KST→위 실제 수용 시각과 guard 관측으로 대체한다. 준비/분석/기록을 포함한 관측이며 운영 계산 처리량 보장은 아니다.
UTC 뒤 현재 권리 불변 저장/API→자동 worker/typed web/같은 UTC3D→사용자 기동을 별도로 수용한다.
[계획](../tasks/plan.md)/[작업 목록](../tasks/todo.md)을 따른다.

현재5173은 완료166일 저장 재생,5174는 기존 [A2](crop-climate-joint-prefix-advance-browser-20261011.md)의
합성128초 접수/진행·확정 부분 결과 자동 조회다. 새 환기 checkpoint는 UI 미배포다.
실제 품종/농장 Run·국내 독립 자료0, G0–G4 `not_assessed`, 실제 생산/미래 마진/추천 hold를 유지한다.
다른 온실 경계/물·양분/구매 에너지/경제·최종 UI와 독립 자료가 남아 전체 제품 완료 날짜는 아직 산정할 근거가 부족하다.
