# 현재 forcing의 물질 문턱: 근 범위와 순서 검증

2026-10-31 KST. **합성 수치 근 정밀화 수용; 새 기관/확정 상태 채택 아님.**
[계약](../contracts/supply-forcing-threshold-v1.md),
[코드](../backend/app/crop_supply_forcing_threshold.py),
[시험](../backend/tests/test_crop_supply_forcing_threshold.py),
[기계 증거](artifacts/supply-forcing-threshold-20261031.json)를 연결한다.

## 달라진 동작

이전 owner는520초 뒤 문턱을 만나는 구간을 미소비 pending으로 저장했다.
새 함수는 실제 확정 handle과 그 pending page를 검증하고, 같은 active forcing의 미확정 한 구간만
5RHS로 대사한 뒤 수치 다항식에서 문턱 도달 시각의 범위를 좁힌다.
과거 확정 구간은 다시 적분하지 않으며 기관/CP/현재 이력을 쓰거나 물질 사건을 소비하지 않는다.

기존 RK4 3차 continuous-extension/정확 Fraction 방법을 그대로 사용했다.
네 단계 기온에서 구성한 계수와 엄격한 미분 최솟값을 원 clock certificate에 대사하고,
최대128회 이분법으로 원점·정확 lower/upper·signed residual·폭을 기록한다.
1µs 허용 폭은 **해당 수치 다항식의 근을 감싸는 폭**이다. 실제 출현/물리 ODE의 정확도를 뜻하지 않는다.
원 누적 나이의 반올림 차를 그대로 보고하며 시계를 문턱에 맞추지 않는다.

기존 owner가 “bracket이 forcing edge에 닿는다”는 이유로 보류했던 사례도
근이 다음 입력 변경보다 엄격히 앞임을 수치적으로 증명할 수 있다.
원 owner/current/pending는 그대로이며 새 상태를 확정하지 않는다.
정확한 다항식 끝 일치는 순서 정책이 없으므로 ORDER_HOLD를 유지한다.

## 검증과 검토

최종 **신규21 + 기존 owner23/kernel12/상태28/terminal19 =103 passed**다. pytest339.41초/guard340.83초, PID최대180,846,592bytes/합계334,049,280bytes였다.
별도 실제 실행은 두 계획 모두1µs 허용 폭·잔차 부호/같은 root 결과와 locator 쓰기0을 확인했다. WSL RSS는0.25초 표본이며 Windows/전체 host 메모리는 측정하지 않았다.

- genuine source/handle bytes·같은 정의/확정 cursor의 pending page, 원 active span 전체 결과의 실제 재계산 일치.
- 과거 확정 RHS0·pending5RHS·CAS 쓰기0; full/split의 같은 pending hash와 같은 locator 결과.
- Decimal2200자리 독립 다항식·근180회 탐색으로 lower/upper 포함, 양쪽 잔차/허용 폭과 반올림 차 대사.
- root가 적용된 입력 시작 뒤/다음 edge 앞이라는 증명, 다항식 끝 일치 hold와 네 기온만으로는 부족한 단조성 반례.
- page의 다른 cursor/정의·trace/status 변조, 단위/0·음수/구간보다 큰 허용 폭·잘못된 code/handle 거부.
- 128회 정밀도 한도·계산 중 취소, 늦은 source/profile·pending blob 변경 때 root 제거/과거 참조 보존.
- pending 재계산 뒤 I/O 실패의 부분 RHS 횟수를 unknown으로 보고하고 private 경로를 사유에 노출하지 않음.

초기 module 부재의 RED를 보존했다. 자체5축 검토에서 호출자의 허용 오차 사전이 계산 중 바뀌면
계산에 쓴 값과 결과에 기록한 값이 달라지는 반례를 찾았다. 실제 실패를 보존하고 처음 접수한
불변 Fraction을 결과에 새 canonical rational로 기록하도록 수정했다. 최종 source로 회귀를 다시 통과했다.
독립 농장 검증이나 외부 code review로 자체 검토를 표시하지 않는다.

실제 별도 실행은 기존 genuine v1 source512에서 시작한 새 forcing 계획 두 개를 사용했다.
분수 입력 변경과 다음 forcing edge에 닿는 pending 사례 각각에서 full/split의 같은 확정 cursor/page,
별도 프로세스 cold open 중 과거 RHS0과 locator5RHS·같은 root 결과/허용 폭을 확인했다.
원 source CAS/19파일·이전 owner의 두16파일 archive와 원4500항목·기존 세 preview의 HTTP/고정 수명을 보존했다.
root/원 상태·입력 raw는 source redistribution:false에 따라 private에만 보관했다.

root native Codex CLI `gpt-6.1-sol/xhigh`·CLI0.157.1의 실제 session_meta/turn_context LF hash와
현재 판단/실행 결과를 기록했다. 재귀 CLI/새 subagent·새 농업 계수/요금/외부 자료 채택은0이다.
기존 원문/방법 수용을 재사용했으며 새 물리 법칙이나 실제 자료 QC/G0 승인으로 올리지 않았다.
전체 backend/frontend suite·새 UI 브라우저·제품 전체 CI/배포는 실행하지 않았다.
현재 UI는 원38시점이며 이번 root 계산은 연결하지 않았다.

## 다음 작업·일정·외부 의존성

다음은 **동일 시각의 상태/적분량 후보와 국소 간격 축소 진단**이다.
원 root bounds/upper-bound 선택과 전체176상태·185누적·124계정, 원 시계/point·기원/격자 잔여를 대조한다.
원 기관·기후 RHS 도메인과 동일 선택 시각의1·2·4 substeps를 검증하고 threshold에 시계를 맞추지 않는다.
아직 확정 CP/물질 point를 만드는 단계가 아니며 명시 조달·새 기관/layout/원자 채택은 다음 수용이다.

계약/기존 수치 대조0.5–1h + 후보/계정 계산1–2h + 독립/국소 간격 축소1.5–3h + 실제 실행·기록0.5–1h,
합계 **3.5–7집중시간의 낮은 신뢰 초안**이다. 보존 상태의 실제 수지/도메인 결과에 따라 갱신한다.
이번 근 정밀화의2.5–5h 추정은 실제 수용 증거로 대체하며 제품 완료 날짜로 쓰지 않는다.

그 뒤 명시 물질/새 layout의 원자 채택·남은 격자 → paged 반복/600초 초과·주야/포화/응축/관리·기관 수명 →
긴 합성 작기/같은 상태3D → 생산·자원 사용/구매량·Decimal 경제 → 거시/수요·공급·대응 후보 자율 비교·최종 UI다.
독립 국내 raw0·첫 실제 품종/현장 forcing·관리·매개변수·권리 확보는 병행 외부 의존성이다.
G0–G4/R2·실제 수확/예측·추천 게시와 전체 goal은 미완료이며 전체 완료일은 미정이다.
