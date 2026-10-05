# 전체 작기 실행 명세·원 격자 대사 수용

2026-10-05 KST. **실행 계약/작업 분해의 로컬 수용**이다.
[명세](../contracts/crop-cycle-execution-v1.md),
[원 solver/격자·표현 대사](artifacts/crop-cycle-execution-reference-20261005.json),
[실제 CLI·파일/초안·검토 증거](artifacts/crop-cycle-execution-contract-reference-20261005.json).
새 모델의 실제 continuation·긴 입력/저장·전체 작기 수용은 아니다.

## 사용자 산출물과 실제 대사

- 실행 계약은 기존 startup의128 forcing/128 event·512 output·10,000 step·1일과
  기관 단독 v1의20,000 배열/100만 step을 구분한다. 실제 archive의47,809시점/후보166일은
  채택된 UTC/forcing이 아니다. 처리 계약과 실제 입력/품종 승인 경계를 유지한다.
- 고정 계산 경계와 저장/3D 출력 선택을 분리한다. 원 seed·121성분 벡터(105상태+16누적),
  전역 steps/event_count·정확한 Fraction clock·phase와 next cursor를 보존한다.
- 단계는 순수 continuation → bounded input stream → 불변 결과/조회·같은 UTC 3D →
  실제 RHS의 규모/재현 시험이다. 각 단계의 확인할 산출물과 독립/실제 경로 시험을 명세에 기록했다.

버전 있는 [독립 연구 script](crop-cycle-execution-reference.py)를 실행했다.
원 기존 solver6프로그램의 **630개 실제 RK4 걸음**을 별도 divmod/range 재구성의 UTC/길이와
대사했다. 실제 boundary-after-event의 시각과 journal/input event 시각·선택된 output 순서도 확인했다.
원 입력은 변경되지 않았으며6프로그램은 모두 completed였다.

원 순서에 대한5개 chunk 예산(1/2/7/64/10000)의 **30가지 grouping**에서 같은 순서를 확인했다.
이는 이미 고정한 격자의 분할 시험이다. 새 모델 driver의 중단/재시작 시험으로 표시하지 않는다.
23개 snapshot의121성분·**2,783개 float64**를 canonical JSON으로 저장/복원하고 binary bytes를
정확히 대사했다. source code와 고정 parameter 파일을 변경하지 않았다.

스칼라 y'=y 반례에서는 h7/원 경계0,10,20의 걸음7,3,7,3이 chunk 경계5 추가로
5,5,7,3이 되어 결과가 달라졌다. 원 경계10에서 grouping하면 같은 float 결과였다.
이는 농업 방정식·작물 restart/수렴 증거가 아닌 격자 의미의 독립 반례다.

자작 clock 반례에서는 initial0.1/temp0.1·1초+1초에서 정확한 Fraction prefix를 현재
float로 반올림해 새 시작값으로 사용하면 최종 float가1ulp 달라졌다. numerator/denominator
복원은 원 결과를 보존했다. 이 수치는 작물 coefficient/forcing 채택값이 아니다.

전체 독립 실행은 **5.508초·최대RSS22.89MiB**, 새 DB/서버0개였다. Python3.12.13·stdlib와
기존 고정 계산/프로필을 사용했고 새 의존성/CLI 재귀 실행이 없다.

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-execution-reference.py \
  --output /tmp/ossf-cycle-execution-recheck.json
```

초안/연구 script/첫 영수증은 `0b1fac6`에 고정했다. 그 영수증의 contract hash는 그때의
초안이며 현재 상태 문구/검토 링크와 다르다. Git의 초안 내용으로 hash를 대사했다.
현재 수용 명세의 hash와 위 draft/영수증 연결은 별도 contract 영수증에 기록한다.
이전 관측 입력/시험 증거를 덮어쓰지 않는다.

## CLI·설계 검토와 범위

현재 CLI turn_context `2026-10-05T05:15:37.838Z`의 **gpt-6.1-sol / xhigh**를 확인했다.
기존 사용자 위임 안에서 그 세션으로 판단·구현/검토했으며 재귀 CLI는0회다.
실제 context line hash, 출력 파일/로그 hash를 영수증에 보존한다.

검토에서 다음을 확정했다.

- `initial-ready`는 정규화 입력의 시작 위치이며 정상 crop snapshot/last_confirmed가 아니다.
  t0 검증/제거 실패는 과거 없는 hold다.
- `step-end`가 원 경계에 도착한 경우 아직 pending인 forcing 전환·사건·output을 재시작에서
  한 번 처리한다. `boundary-committed`는 다시 적용하지 않는다. 운영 cancel/crash를 numeric hold로 바꾸지 않는다.
- 실제 재시작 동일성은 기존6프로그램과 과거/빈/소수 초 hold·별도 Python checkpoint 복원에서
  상태/16누적·수지·사건·확인 과거/phase를 비교하는 다음 driver 작업의 수용 조건이다.
  단순 grouping·serialization을 이 결과로 대체하지 않는다.
- root/hash/profile·seed/clock/counter·cursor를 checkpoint에서 검증한다. SHA 자체는 진본/현재
  farm/source/program 권리/관문 승인이 아니며 실제 custody와 atomic delta commit은 후속 별도 수용이다.
- 원 legacy 모델의 함수/파일을 재구성하면 현재 immutable artifact의 code pin이 바뀐다.
  새 provider는 고정 point calculators/guard/ledger/update를 재사용하고 별도 버전의 실행 제어를 만든다.
  긴 입력/새 cycle manifest를 기존 v3 API/decoder로 통과시키지 않는다.

source/profile/hash를 보존했고 새 운영 기반/큐/service를 만들지 않았다.
새 모델 continuation, 실제 저장/조회·새 웹 화면, hosted 실행은 이 구획에서 실행하지 않았다.
동시에 기존92cade3의CI5개가 모두 완료돼[백엔드3,408개/UID4·여섯 목록/정리·집계](artifacts/crop-startup-storage-ci-20261005.json)를
수용했다. 이는 startup 수학/저장까지이며 후속 API/client/3D와 이 실행 계약은 포함하지 않는다.

## 다음 한 단계와 일정

다음은 `crop-cycle-continuation`: 처음에는 현재 짧은 입력으로도 원 상태와 실제 RHS를
step chunk로 양보/복원할 수 있는 순수 provider를 구현한다. 모델·계수/원 격자와121벡터,
seed/clock·전역 counters/사건/output·hold를 보존하고 별도 Python/JSON 복원을 검증한다.
기존 고정 코드/hash와 수치 결과를 유지한다. 긴 입력/전체 작기와 권리/저장 API는 후속이다.

계약/독립 대사는 **10월5일 KST 로컬 완료**다. 다음 provider는 context/kernel·step 상태/
checkpoint 검증2–3시간,6프로그램/hold·변조·별도 프로세스/회귀/보고2–3시간의
**4–6 집중시간** 잠정이다. 하루4시간/CI 대기 제외 기준 **10월5–7일 KST**가 목표다.
source stream/저장·전체 작기 부하 날짜는 provider 실적 뒤 추정한다. 실제 참조 입력/초기/관리/
품종은0개 채택, 국내 독립 자료0건·actual crop Run0개다. G0–G4·생과/자원/경제·예측/추천은 보류한다.
외부 자료를 모델 개발의 선행으로 잠그지 않으며 실제 생산 예측·추천 날짜는 산정하지 않는다.
