# 작물·기후의 자동 구간/관리 사건 실행 — 2026-10-10 로컬 수용

## 산출물과 범위

core `12e6d7b4144579194eba04f902e9a85e3937952e`의
[자동 실행기](../backend/app/crop_climate_joint_boundary.py),
[핵심5 계약](../contracts/crop-climate-joint-boundary-driver-v1.md)을 로컬 수용했다.
[9개 프로그램·독립 대사/수렴·실제 종료 영수증](artifacts/crop-climate-joint-boundary-reference-20261010.json)은
SHA-256 `86ab9ba4c8814fb93ca7f0358e0fcc10501bb55778f64232ac96323791398267`이다.

명시 상수 forcing/RGR의108상태를 기존 짧은 공동 RK4의 한 걸음씩 진행한다.
각 경계에서 **앞 구간 적분→전역 확인→원자 관리→전역 확인→사건 후 선택 출력**을 처리한다.
0/마지막 경계도 같은 순서로 정확히 한 번 적용한다. 연속22장부와 사건6합계는 분리한다.
최대4,096걸음·600초/128사건·512선택 출력의 연구 호출이며, 독립 궤적 수용은 아래32초 사례 범위다.
전체 작기·온실 예측이나 영속 멱등/취소·재개를 제공하지 않는다.

기존 짧은 kernel이 중간 누적 장부의 prefix를 반환하지 않으므로 한 걸음 호출을 재사용했다.
식/RK4를 중복 구현하지 않으며 완료 RHS 호출은 `1+5*steps+2*events`다.
전역 seed→현재의 탄소/과실 개수·수관/공기 현열·수증기·용량·축소 열7수지를 매 걸음/사건 뒤 검사한다.
비영 누적 소실·단위/영역/수치 실패는 hold다. 마지막 확정 snapshot와 완료 selected output/journal prefix를 보존하며
실패 사건/걸음은 게시하지 않는다. checkpoint나 성공한 부분 Run으로 표시하지 않는다.

새 DB/API/UI·현재5173의 실시간 U3 연결은 없다. 현재 사용자는 완료 합성166일의 기존 저장 생장·수확을 조회한다.

## 실제 CLI와 선행 근거

native Codex CLI `gpt-6.1-sol / xhigh`, turn-context `2026-10-09T16:39:02.560Z`, 도구 `c676d6`이다.
원 JSONL 한 줄 LF 포함 SHA:
`e96a045ca3425f3853f4bf67a22c24ae4eb4f61a6bec0bb3aa711fb1d3dd284c`.
재귀 CLI 실행0회다. 개발/설계 검토이며 제품 runtime CLI·독립 해제/관문 증거가 아니다.

[가변 용량 근거](crop-variable-canopy-energy-review-20261009.md),
[공동 RHS](crop-climate-joint-rhs-implementation-20261010.md),
[짧은 적분](crop-climate-joint-integration-implementation-20261010.md),
[원자 관리](crop-climate-joint-management-implementation-20261010.md)를 그대로 사용했다.
앞선3개 core의15파일/9개 의존 코드·16개 독립 참조 입력 SHA를 확인했다.
동적 T24/Tsum, signed Uref와 과실 `cohort-decimal-rational-removal-v1` 정책을 변경하지 않았다.
새 농업/물성 계수·자료원·외부 자료/권리는 채택하지 않았다.

## 검증과 비용

| 원 실행 | 실제 결과 | terminal 도구 / 종료 |
| --- | --- | --- |
| smoke84965 | 2통과/0.61초; controller1.069초 | `f1b991` / 0 |
| 참조 생성6351 | 9프로그램/27선택 시점/10사건·877,047bytes; controller22.294초 | `532300` / 0 |
| 집중79885 | 72통과/11.47초; controller11.808초 | `50cd2f` / 0 |
| 최종87443 | 새72+기존576=648통과/18.98초; controller19.489초 | `9df4c3` / 0 |
| 별도 root56154 | 참조 bytes 재생성/5,973수치/60수렴/선행15파일·자원; controller24.856초 | `e8601c` / 0; 출력 `7bd04c` |

[독립 Decimal80 참조](crop-climate-joint-boundary-reference.py)는 app을 import하지 않는다.
고정 독립130벡터 RK4와 제거된 용량의 열/과실 retention을 사용한다.
무사건, 낮/밤·역 교환, 초기/마지막, 세 사건, 음/0 Uref의9프로그램을 완주했다.
27개 시점의108상태+22연속+6사건+3유도량=3,753개,
10개 journal의 전후108상태+6제거 합계=2,220개, 총5,973개 수치를 사전 기준과 대사했다.
선택 시각/사건 수/원 전후 값도 일치한다. 참조877,047bytes는 현재 fixture와 완전히 같다.

16초 사건을 고정한32초 낮/밤·역 교환의 dt8/4/2 대 독립0.25 비교는10관측량·60비율 모두8 초과,
최소 `15.956044650973858`이다. 기존 빈 과실 시간 수렴/착과 불확실성은 남는다.
전역 최대 절대 잔차는 탄소 `1.3882770475738548e-11 mg_CH2O/m2_floor`,
축소 열 `5.82989212460916e-11 J/m2_floor`, 수증기 `1.7442102449860553e-17 kg_water/m2_floor`다.
나머지7수지·허용 오차와 범주별 참조 차이는 영수증에 있다.

실제 RHS 호출/상수 forcing·현재 잎과 동적 이력, 무사건의 기존 kernel과 정확한 동일성,
선택 변경의 최종 상태/장부 불변, 처음/중간/마지막·다중 사건 순서를 확인했다.
입력 스키마/단위·ID/격자·profiles, 실제 적엽 초과/영역·trial 온도/underflow,
step/event 장부의 주입 오류와 늦은 사건 실패에서 미확정 출력 제거/입력 불변을 확인했다.
512선택/128개의0관리 사건을 실제512걸음으로 실행해2,817 RHS 호출과32초 종료를 확인했다.
정적 assert나 더 큰 reject 사례만으로 상한을 수용하지 않았다.

Python3.12.3, 각 controller wall120초/로그4MiB·0.25초 표본의 단일512MiB/소유+보호1GiB다.
최종/root source1,707개·원본2,148항목·고정 미리보기 소스/웹 자산을 보존했다.
FD4→4·소유 non-zombie 잔존0·원 미리보기3identity 생존/frontend200이다.
최대 단일 PID147,255,296bytes/소유+보호 합355,049,472bytes로 상한 이하다.
새 PG/브라우저·전체166일 계산/writer를 반복 실행하지 않았다.

## 다음 단계와 남은 의존성

짧은 공동 적분/원자 관리/자동 구성을 갖춘 **상수 forcing의 bounded 공동 구간/사건** 범위를 수용했다.
부모 `crop-climate-coupling`은 여전히 미완료다. 다음은 `crop-climate-joint-storage-replay`의
**분할 실행 context/checkpoint**다. immutable seed/정규화 입력·모델/프로필/수치 identity,
현재108상태·연속22/사건6·전역 수지·event/output cursor와 마지막 확정 경계를 고정한다.
분할과 한 번 실행의 상태/장부/순서 동일성, fresh 복원/변조 거부·hold/재시도·자원/비용을 검증한다.
기존121상태/Fraction clock·원 결과를 덮어쓰지 않는다.

그 뒤 명시 UTC/입력 경계→불변 저장/현재 권리 API→같은 시각 수치3D,
물·양분/구매 에너지→사용자 실행/Decimal 경제로 잇는다.
온실 복사/PAR/CO₂·기공·제어 경계의 원식/단위 조사는 명시 입력의 저장/재생 개발과 병행 가능하다.
이 분리는 자동 온실/생산 예측 게시의 선행 조건을 없애지 않는다.

이번 자동 core의 첫 native turn16:27 UTC부터 최종 검토16:47 UTC까지 약20분과
19.489초 회귀/24.856초 root를 다음 비용 추정의 근거로 쓴다.
context/checkpoint는 계약/상태·분할 실행/복원 검증/비용·기록의4묶음으로 **1–3집중시간** 잠정이다.
계속 작업·새 수치/복원 장애 없음 조건의2026-10-10 검토 목표이며 hosted 대기는 제외한다.
그 이후 저장/API/3D 날짜는 이 경계 비용을 측정한 뒤 갱신한다. 전체 제품/production 날짜는 미확정이다.
실제 품종 입력·농장 Run·국내 독립 자료0건, G0–G4·생산/미래 마진/추천 hold를 유지한다.
