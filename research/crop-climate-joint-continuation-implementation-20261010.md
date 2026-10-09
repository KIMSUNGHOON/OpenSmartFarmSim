# 작물·기후 분할 실행/체크포인트 복원 — 2026-10-10 로컬 수용

## 완료 범위

core `2eb3dfef4ec6a942654732b815e79cd8d48274d5`의
[분할 실행기](../backend/app/crop_climate_joint_continuation.py)와
[핵심3 계약](../contracts/crop-climate-joint-continuation-v1.md)을 로컬 수용했다.
[독립 참조·분할/복원·원 종료 영수증](artifacts/crop-climate-joint-continuation-reference-20261010.json)을 확인할 수 있다.
Artifact SHA-256: `2c6160627a251c0ec48f2ba80dc64732f246d9dca483b7496a020daff6be9e5b`.

immutable context에 정규화 프로그램/seed·초기 RHS와 모델/코드/프로필·정책/수치/환경 identity를 고정한다.
checkpoint는108상태·연속22장부/사건6합계·전역7수지·다음 경계/출력·사건 cursor와 prefix를 보존한다.
경계0 사건 전/후를 next_index0/1로 구분한다. 각 원 걸음/사건/출력의 순서는 기존 자동 실행과 같다.
chunk로 묶은 합계를 다시 더하지 않으므로 임의 분할에서도 상태/장부·journal/선택 출력·최종 checkpoint bytes가 같다.
원 RK4/장부/관리 kernel을 재사용했다. 새 농업 식/계수나 가짜 성장 상태를 만들지 않았다.

복원 시 **외부에서 신뢰한 exact bytes digest**가 필수다. 닫힌64KiB canonical JSON·중복 key/비유한 값,
현재 context/code/profile/환경·현재 상태의 RHS/전역 수지·cursor/단위·원 elapsed를 검사한다.
과거 걸음/관리 사건을 재실행하지 않는다. hash는 진본/권한 증명이 아니며 서버의 권한 있는 불변 저장/서명 연결은 후속이다.
이 단계의 context/checkpoint는 신뢰된 process 내부 frozen 객체이며 공격자의 Python 내부 재작성에 대한 인증 경계가 아니다.

최대 원4,096걸음/600초·128사건/512선택, chunk 예산1–128경계, context2MiB/checkpoint64KiB다.
명시 상수 forcing/RGR의 짧은 연구 구간이다. 새로운 UTC/forcing 구간·영속 저장/API/3D·실시간 U3는 미구현이다.
현재5173은 완료 합성166일의 기존 저장 생장·수확을 읽으며 이 새 checkpoint를 표시하지 않는다.

## 실제 CLI와 보존한 근거

native Codex CLI `gpt-6.1-sol / xhigh`, turn-context `2026-10-09T16:54:38.012Z`, 도구 `363203`이다.
원 JSONL 한 줄 LF 포함 SHA:
`8a89c51d4e71f39762492011fe0900ef3a6d2be2dc76b9ea668e585b05502be6`.
별도 root에서도 같은 원 줄과 exact model/effort를 확인했다. 재귀 CLI0회다.
개발 검토이며 제품 runtime CLI·독립 해제/관문 증거가 아니다.

[자동 경계 실행](crop-climate-joint-boundary-implementation-20261010.md)과 그 공동 RHS/짧은 적분/관리의
4개 core20파일, 의존 코드9개와 독립 참조16개 입력 SHA를 대사했다.
원 profile/BSD 고지·signed Uref/가변 용량·동적 T24/Tsum과
`cohort-decimal-rational-removal-v1` 정책을 보존했다. 실제 조직/품종/농장 자료를 채택하지 않았다.

## 원 실행과 통과한 검증

| 원 실행 | 실제 결과 | terminal 도구 / 종료 |
| --- | --- | --- |
| smoke11483 | 4통과/1.09초; controller1.582초 | `405beb` / 0 |
| 집중52361 | 128통과/42.92초; controller43.290초 | `fcc956` / 0 |
| 최종56553 | 새138+기존648=786통과/66.06초; controller66.565초 | `767257` / 0 |
| 별도 root52404 | 원 bytes 재생성/5,973수치·60비율·별도 Python/크기·보존; controller33.022초 | `2ed601` / 0; 출력 `c73b12` |

첫 smoke 뒤 코드/정책/환경 변경 검사와 더 많은 격자 회귀를 추가했다. 모든 원 실행은0이며 실패를 재시도해 가리지 않았다.
9개 기존 프로그램을 예산1/2/3/7/128과 mixed1/7/1/2/1/5로 실행했다.
원 자동 실행의 모든 snapshot/유도량/전역7잔차·예산·22/6장부·사건 전후/선택 시각과 정확히 같다.
분할별 원 checkpoint의 정규 bytes를 복원하고 최종 bytes/prefix가 한 번 실행과 같은지 검사했다.

별도 Python의 next_index0/1/8/9/17 복원은 initial-ready/t0 완료·중간 사건 전후/최종을 포함한다.
현재 checkpoint 검사는 endpoint RHS1회이며 과거 적분/관리0을 실제 호출 계수로 확인했다.
별도 root의 추가 fresh PID1889243은 실제0, 중간 사건 후 next_index9에서 **남은8걸음·마지막 사건1개**만 실행했다.
3개 chunk·총RHS46(restore1+chunk검사3+걸음40+사건2), 같은 최종 checkpoint/prefix·남은 출력/event SHA다.
원 checkpoint bytes는 변경되지 않았다.

독립 Decimal80 참조를 재생성해 원877,047bytes·9프로그램의5,973수치를 대사했다.
16초 사건을 고정한 dt8/4/2 대 독립0.25의60반분 비율은 모두8 초과, 최소 `15.956044650973858`이다.
각 새 분할 격자도 원 자동 실행과 정확히 같다. 빈 과실 시간 수렴/실제 착과·농장 정확도는 이 증거에 포함되지 않는다.
전역 잔차와 참조 오차는 영수증에 보존했다.

원 입력 불변·같은 checkpoint 재시도의 동일성·읽은 property 변경의 격리,
현재 code/policy/profile/environment·context 혼합/JSON/단위/상태/위치·외부 digest 변조를 확인했다.
실제 늦은 적엽 초과·trial 온도/underflow와 step/event 수지 주입 실패에서 checkpoint=None,
마지막 확인된 상태/완료 prefix와 원 자동 실행의 같은 hold 경계를 확인했다.
cancel/crash의 KeyboardInterrupt는 정상 yield로 바꾸지 않았다.

## 자원과 저장 경계의 실측

원512걸음/512선택/128사건을 예산128로5개 chunk에 걸쳐 실제 완료했다.
최대 첫 chunk는128출력/128사건·127걸음이다. 독립 root의 실측은 다음과 같다.

| 항목 | bytes / 실제 호출 |
| --- | ---: |
| program+initial RHS+manifest context | 255,217 |
| 해당 checkpoint | 10,578 |
| 전체 첫 chunk의 canonical JSON | 4,995,778 |
| 해당 chunk 확인된 수치 RHS / checkpoint 검사 RHS | 891 / 1 |

checkpoint/context 상한은 통과했다. **chunk 전체는 기존 HTTP2MiB를 넘는다.**
이 모듈은 HTTP 응답을 만들지 않는다. 후속 writer에서 sample/event를 페이지로 나누고
API64 sample/8 event·2MiB 경계를 따로 검증해야 한다. 계산 chunk 전체를 API 응답으로 보내지 않는다.

Python3.12.3·wall120초/로그4MiB·0.25초 표본, 단일512MiB/소유+보호1GiB다.
최종/root source1,714개·원본2,148항목·기존 미리보기 source/assets를 보존했다.
controller/root FD4→4·소유 non-zombie 잔존0·원 미리보기3identity 생존/frontend200이다.
표본 최대 단일 PID147,255,296bytes/소유+보호 합365,334,528bytes로 상한 이하다.
새 PG/브라우저·수용된 전체166일 계산/writer를 반복 실행하지 않았다.

## 다음 단계와 일정

`crop-climate-joint-storage-replay` 부모는 미완료다. 다음은 **`crop-climate-joint-utc-binding`**이다.
명시 UTC origin/시각 정밀도·원 elapsed 격자의 결속을 계약하고, 새 입력/manifest에 시간 변환 판본을 묶는다.
같은 step_index의 snapshot/journal/마지막 확인 상태에 같은 시각을 부여하되
원 상태/장부·prefix·동적 온도 이력과 RK4 격자를 바꾸지 않는다.
naive/모호한 시간대·표현 정밀도 손실/범위 이탈·서로 다른 origin/모델 혼합을 거부한다.
수치 재계산 없이 원량 보존/UTC·KST·처음/중간/마지막·hold 경계를 검증한다.
forcing 변경/전체 작기에는 별도 입력 경계 계약과 수용이 필요하다.

이어 불변 writer/페이지/reader·복원(RHS0 조회)→현재 권리 저장/API→같은 시각 수치3D로 잇는다.
온실 복사/PAR/CO₂·기공 원식/단위 조사는 명시 입력 저장 개발과 병행한다.
물·양분/구매 에너지→사용자 실행/Decimal 경제, 독립 농장 자료 확보와 G0–G4는 기존 의존성을 유지한다.

이번 native16:54부터 검토17:15 UTC까지 약21분·회귀66.565초/root33.022초가 실측 근거다.
UTC binding은 계약/시간 매핑·identity/거부·보존 시험/기록의4묶음으로 **1–2집중시간** 잠정이다.
계속 작업/새 시각 정밀도 장애 없음 조건의2026-10-10 검토 목표이며 hosted 대기는 제외한다.
새 writer/API/3D 완료일은 해당 실측 뒤 갱신한다. 실제 품종/농장 Run/국내 독립 자료0건,
G0–G4·생산/미래 마진/추천 hold와 운영 기반 고정은 유지한다.
