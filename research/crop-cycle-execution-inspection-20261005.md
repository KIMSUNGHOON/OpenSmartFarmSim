# 전체 작기 실행 계약의 착수 코드 감사

2026-10-05 KST. **코드 관측/설계 보류 목록**이며 계약·연속 실행·전체 작기 수용이 아니다.
현재 Codex CLI `gpt-6.1-sol / xhigh`에서 판단했다. 재귀 CLI 없이 같은 실제 turn_context를
[화면 단계의 영수증](artifacts/web-crop-startup-replay-reference-20261005.json)에 기록했다.
파일 hash와 관측을 [별도 기록](artifacts/crop-cycle-execution-inspection-20261005.json)에 고정한다.

## 한도를 판본별로 구분

| 대상 | 입력/시간/걸음 한도 | 실제 근거 |
| --- | --- | --- |
| 기관 단독 연구 v1 | segments/events/output 각20,000, max_steps1,000,000, max_step_seconds1–86,400 | [입력 준비](../backend/app/crop_growth_integration.py) |
| 기관·50과실 구획과 현재 startup | segments128/events128/output512, max_steps10,000, max_step_seconds1–3,600, 기간≤86,400초 | [공유 입력 준비](../backend/app/crop_plant_cohort_integration.py), [startup 호출](../backend/app/crop_plant_startup_integration.py) |
| 공개 참조 archive의 관측 형태 | 47,809시점/47,808 interval·후보166일 | [이전 실제 파일 감사](crop-forcing-audit.md); UTC/QC/초기조건은 미채택 |

166일/10초의1,434,240 step은 형태 산술이다. 현재 startup solver의 적정 간격·전체
작기 성능/정확도가 아니다. 기존20,000/100만을 현재 과실 모델의 한도로 오해하지 않는다.

## 재시작에 필요한 현재 의미

[startup 적분](../backend/app/crop_plant_startup_integration.py)은105개 상태 성분(기관·온도5 +
N50 + C50)과16누적 유량의121성분 벡터를 사용한다. 시작 seed는 같은 원 벡터이며
누적은 처음에0이다. 수지 허용 한도는 전역 steps+event_count에 의존한다.
다음 chunk를 단순히 기존 API의 새 initial_state로 실행하면 seed와 누적·operations,
프로그램 hash/계산 ID가 다시 시작된다. 이를 연속 실행으로 수용하지 않는다.

계산 경계는 출력 UTC·forcing 끝·관리 사건 시각의 합집합이다. 각 경계까지
h=min(max_step_seconds, 남은 정수 초)로 적분한다. 새로운 chunk 끝/출력 시각을
그 합집합에 넣으면 RK4의 걸음 길이와 결과가 바뀔 수 있다. 전체 프로그램의 원 계산
경계·걸음 순서를 먼저 고정하고 저장/표시 출력 선택을 그 계산과 분리해야 한다.
전역 격자는 단순한 t0+n×h가 아니라 원 경계까지의 짧은 마지막 걸음을 포함한다.

온도 합은 Fraction의 원 초기값/각 forcing 구간의 정확한 prefix/slope에서 계산한다.
새 initial_state의 반올림된 온도 합만 가지고 prefix를 재구성하면 동일성 증거가 없다.
프로필/code/policy/원 입력 hash와 이 clock의 정확한 정의·active segment를 보존해야 한다.

경계의 처리 순서는 도착 걸음 검증 → forcing active 변경 → 제거 사건의 후보 계산 →
현재 RHS/기관·두 수지/새 요청·호흡 수지 검증 → journal/이벤트 개수 → 원 output snapshot이다.
걸음 끝의 last_confirmed와 사건 뒤 상태는 다르다. checkpoint의 위치/phase·다음 boundary/
event/output cursor를 고정해야 중복 제거와 누락을 막을 수 있다. RK4 중간 trial을 정상
checkpoint로 저장하지 않는다. 수치 hold를 자동으로 완료로 바꾸지 않는다.

## 다음 한 단계의 수용 기준

`crop-cycle-execution-contract`에서 다음을 reviewable 문서/독립 대사로 제시한다.

1. 새 version의 실행 입력·원 경계/걸음·state121/원 seed·전역 counters·clock·phase/cursor,
   불변 checkpoint/hash와 현재 farm/source/program 권리 계약.
2. 원 합집합과 걸음 경계를 유지하는 분할 정책. 경계 바로 전/후, forcing 전환,
   사건+output 동시 시점·영 초기/전량 제거/재유입·hold의 중단/재시작 검증표.
   동일성의 대상(고정 모델 상태/누적/사건/수지)과 실행별 외부 metadata를 구분한다.
3. 계산 경계와 저장/3D 출력 선택의 분리, bounded 입력 읽기/원자료 보존·출력 페이지,
   WSL의 동시 실행/메모리·wall-time·실제 작기 부하 측정 계획.
4. 순수 연속 실행 → 불변 파일/저장/조회 → 부하/재현의 작은 후속 작업과 수용 증거.
   기존 짧은 v1/v2/v3 artifact/decoder를 새 cycle manifest로 넓히지 않는다.

관측 가능한 위험을 확인했지만 **독립 걸음/재시작 대사·새 실행 계약/모듈과 실제 작기
부하는 아직 실행하지 않았다**. 체크박스는 유지한다. 실제 입력/품종·초기/관리 채택은0개,
국내 독립 농장 자료는0건이다. 개발은 자료 확보와 병행하고 실제 생산/생과·자원/경제/
예측·추천의 G0–G4는 유지한다. 계약/분해2–4 집중시간 잠정 뒤 구현 날짜를 다시 산정한다.
