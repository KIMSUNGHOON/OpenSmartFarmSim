# 검증 계산 결과의 공개 투영 — 로컬 수용

2026-10-07 KST. 새 결과 공개 형식의 순수 소프트웨어 자식만 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-api-projection-reference-20261007.json)에 실제 실행·로그 SHA,
native Codex CLI `gpt-6.1-sol / xhigh` 문맥과 source 대사를 기록했다. 재귀 CLI·새 agent0회다.
실제 API/농장 권한 승인·전체166일 연결·농업 정확도는 이번 수용에 포함하지 않는다.

## 구현과 검토

[새 공개 모듈](../backend/app/api_crop_cycle_calculation_replay.py)은 새 result/artifact ID와
공식 계산 manifest를 그대로 받는다. 원 validated context와 실제 calculation context,
input proof SHA를 구분하고 DB validation8필드·server dependency7필드·runtime role code를 보존한다.
manifest의 원 판본 변환을 역으로 대사해 일관되게 재해시한 잘못된 validated SHA도 거부한다.
원량·단위·UTC·수지·hold/확인 과거, sample64/event8·2MiB·cursor/빈 끝 페이지를 유지한다.
공개 객체는 닫힌 형식이며 private checkpoint·키/증명 원문·경로·tenant·권리 선언을 내보내지 않는다.
투영의 packet 검사는 권한이나 HMAC 검증을 대신하지 않는다. 후속 route는 현재 query 안에서 호출해야 한다.

정확성·가독성·경계·보안·비용을 검토했고 원55 source와 선행 조회/구형 투영을 포함한
**67 source SHA를 전후 보존**했다. 새 module의 계산/store/server import는 실행 시점에 둔다.
세 시작 순서의 별도 Python 시험과 추가 독립 import 관측에서 FD4→4를 확인했다.
추가 관측에서는 새 계산/store/server 모듈이 `sys.modules`에 없음을 직접 확인했다.

## 실제 검증

| 실행 | 실제 결과 |
| --- | --- |
| 구형 투영에 새 공식 결과를 전달한 정상 반례 | 1실패/2.05초·종료1 |
| 새 형식 구현 뒤 같은 정상 사례 | 1통과/2.23초·종료0 |
| 새 전체63개 첫 실행 | 61통과/2실패·125.15초·종료1 |
| 증거 파일 이름 수정 후 관련 hold3개 | 3통과/2.04초·종료0 |
| 구형 형식 회귀, 구형25시간 사례 제외 | 42통과/9.98초·종료0 |

첫 전체 실행의 두 실패는 응답/FD 대사 뒤 증거 저장에서 발생한 `FileExistsError`다.
hold 시험의 루프 변수가 매개변수 이름을 덮어써 세 증거 이름이 같아졌다. 변수 한 곳만 수정했고
제품 SHA는 같다. 원 시험 파일·실패 로그와 잘못 명명된 첫 증거는 보존했다.
**새 고유63개와 구형42개, 고유105개 분할 검증**이며 단일105개 성공으로 표시하지 않는다.
최초 workspace cwd의 import 수집 오류도 별도 준비 오류로 보존했으며 행동 반례로 세지 않는다.

자체 소유25시간 실행은 실제11,400걸음·27시점/5사건·7페이지이며 원 모든 행/UTC가 같다.
투영 구간은 parser/context/QC/RHS를 금지한0.119068초, 요약9,502bytes·FD12→12다.
정상120걸음/3시점/3사건과 관리 전·사건·분수 시각의 세 hold도 원 진단/확인 과거를 보존했다.
원량 대사·혼합/재해시/추가 필드·수지·잘못된 페이지와 정확한 byte 경계를 확인했다.
nice19·첫 전체 시험의 표본 최대 주 프로세스 RSS112,844,800bytes이며 OS cache는 통제하지 않았다.
소유 시험 프로세스 종료·임시 tree/비밀번호 파일0개를 확인했다. 실제 PG/HTTP/browser 실행은0회다.
계약은 시험 뒤 수용 기록을 추가했다. 영수증의 계약 SHA는 시험 당시 판본이다.

## 다음 작업과 외부 의존성

순수 투영 자식만 완료했다. 명시적 runtime factory → 원 loader를 보존하는 별도 operator 설정 →
인증 route/실제 SCRAM·TLS30초/2MiB → client/같은 UTC3D 순서로 진행한다.
설정/factory2–4시간과 route/TLS1–2시간의 **남은3–6집중시간 잠정**은 작은 API 연결 범위다.
CI·전체166일 등록 prefix/복원·3D·외부 자료 확보와 최종 제품 날짜를 포함하지 않는다.

현재 remote `353bffb`는 C0/웹/작성 PG 성공, 앱 실패, Backend 대기 상태로 관측했다.
[앱 실패](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37622257162)는 구형 operator config의
정책 필드 검사(line99)에서 발생했다. 현재 dataclass와 구형 loader의 허용 집합 차이는
기본 false인 `crop_cycle_calculation_result_storage` 하나이며 설정 생성기가 `asdict(policy)`를 쓴다.
구형 서명 dependency 파일을 수정하지 않는 설정 생성 호환 보완이 필요하다. 실제 Compose 수정 수용은 아직 없다.
Backend가 끝나기 전 추가 push는 하지 않으며 위 CI는 새 미커밋 투영의 hosted 검증이 아니다.

실제 품종 입력·국내 독립 검증 자료·실제 작물 Run0건, G0–G4 `not_assessed`다.
전체 작기 연결 뒤 생과/수확 → 물/양분·구매 에너지 → Decimal 경제를 연결한다.
생산 예측·미래 마진·최적 작물 추천과 최종 제품 완료일은 필요한 실제 자료/독립 검증 전까지 보류다.
