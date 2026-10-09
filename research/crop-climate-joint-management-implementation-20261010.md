# 작물·기후의 원자적 관리 사건 — 2026-10-10 로컬 수용

## 완료 범위와 산출물

core `397c9a521e7835d41fb02350869a56aea20aa46c`의
[원자 적용](../backend/app/crop_climate_joint_management.py)과
[핵심5 계약](../contracts/crop-climate-joint-management-v1.md)을 로컬 수용했다.
[9개 제거 사례·5개 짧은 구성·수지/수렴 영수증](artifacts/crop-climate-joint-management-reference-20261010.json)을 확인할 수 있다.
Artifact SHA-256: `26fcd081e47e06411ed380849a68adf8ed314f5bac2dd6c3269eb32eac773280`.
관리 primitive와 명시 시험 호출자의 작은 구성만 완료다. 자동 구간/사건 실행·재개와 부모 결합은 미완료다.
새 DB/API/UI·현재5173의 실시간 U3 연결은 없다.

같은 순간의 leaf/stem_root·50개 C/N을 제거하면서 leaf/LAI/C와 signed 저장 열을 함께 갱신한다.
공개 수관 용량 제거 함수를 한 번 사용하고 사건 전후 공동 RHS·탄소/개수/열/용량·온도 보존을 검사한다.
실패하면 입력을 변경하지 않고 마지막 확인된 사건 전 상태·유도량과 phase를 남긴다.
공기 온도/수증기·buffer/T24/Tsum은 순간 사건에서 변하지 않는다.
과실 제거는 명시 연구 비율이며 수확 kg·등급/판매나 실제 조직 열을 추정하지 않는다.

## 실제 CLI·원식과 수량 판단

실제 native CLI는 `gpt-6.1-sol` / `xhigh`, turn-context `2026-10-09T16:01:45.768Z`다.
원 JSONL 한 줄 LF 포함 SHA:
`5b5e30e4893805129965a1eb09f9aca2461f7dcb859b903f639a80e09ad84061`.
도구 `e0cba9`와 별도 root에서 확인했으며 재귀 CLI 실행은0이다.
개발 검토이며 제품 runtime CLI·독립 해제·관문 증거는 아니다.

선행 [가변 용량/물질 경계 검토](crop-variable-canopy-energy-review-20261009.md),
[공동 RHS](crop-climate-joint-rhs-implementation-20261010.md)와
[짧은 적분](crop-climate-joint-integration-implementation-20261010.md)을 사용했다.
기존 [과실 구획의 같은 비율 제거](../contracts/crop-plant-cohort-integration-v1.md)와
[signed 수관 열 제거](../contracts/crop-canopy-energy-transport-v1.md)를 결합했다.
14개 독립 입력/참조·정책 SHA, 이전 짧은 적분 core5·의존 코드9개와 BSD 고지를 대사했다.
새 농업 계수/물성·농장/품종 자료는 채택하지 않았다.

첫 혼합 초기 사건에서는 `0.2*(1-0.25)`와 `0.3*(1-0.5)`의 수학적 잔량0.15가
곱/뺄셈 경로의 binary64 오차로 갈라졌다. 다음 N 전달 미분 `3.0331293032759275e-22`가
상태 ulp `2.7755575615628914e-17`보다 작아 기존 strict increment 검사가 k2에서 hold했다.
독립 Decimal80의 해당 미분은 `0E-14`이며 마지막 확정 상태는 초기 사건 후 상태였다.
원 로그/코드·시험·fixture bytes를 보존하고 별도 root에서 원 코드를 다시 불러 같은 hold를 재현했다.

**과실 구획 수량만** 정규화 decimal 문자열의 정확한 유리수로 제거량/잔량을 계산한 후 binary64로 반올림한다.
`cohort-decimal-rational-removal-v1`을 계산 identity에 결속했다. 같아야 할 잔량을 epsilon으로 맞추지 않는다.
비영 제거가 underflow/반올림으로 소실되면 여전히 hold한다. 잎/줄기와 공개 용량 연산은 기존 의미를 유지한다.
Fraction은 순간 수량에만 쓰며 동적 T24/Tsum의 RK4나 기존 온도 clock을 바꾸지 않았다.
수지·수렴·온도 허용 기준은 변경하지 않았다.

## 원 실행과 검증

Python3.12.3·정확한 소유 controller에서 wall120초/로그4MiB·0.25초 RSS 표본,
단일512MiB/소유+보호1GiB·원본2,148항목·미리보기/FD/소유 정리를 검사했다.

| 실행 | 실제 결과 | terminal 도구/종료 |
| --- | --- | --- |
| smoke98978 | 5 passed / 0.09초 | `0f9958` / 0 |
| 독립 생성11526 | 9사례·5구성 / controller19.477초 | `ea9df2` / 0 |
| 첫 집중90150 | 1 failed, 67 passed / 1.82초 | `528381` / 1 |
| 별도 진단42081 | 잔량/미분/ulp·Decimal 원인 확인 | `7a993e` / 0; 출력 `a32266` |
| 수정 집중39906 | 1 failed, 68 passed / 2.05초 | `747605` / 1 |
| 최종 집중87958 | 69 passed / 2.09초 | `39e8bf` / 0 |
| 새69 + 기존507 최종66217 | 576 passed / 7.81초; controller8.230초 | `da2c56` / 0 |
| 별도 root50429 | 원 bytes/3,728수치·60수렴 비율·원 실패 재현/source/FD/native; controller21.269초 | `91f8ce` / 0; 출력 `8a9b66` |

두 번째 실패는 smoke가 이전 binary 곱의 반올림을 정확히 요구한 경우다(`1.4*0.75` 대 명시 잔량1.05).
해당 시험/코드 원 bytes를 보존하고 정확한 decimal 잔량을 검사하도록 수정했다.
초기 사건의 완주나 수용 기준을 제거하지 않았으며 독립 fixture는 동일하다.

[독립 Decimal80 참조](crop-climate-joint-management-reference.py)는 app을 import하지 않는다.
제거된 용량의 열과 과실 retention을 독립 경로로 계산하고 고정 독립 RK4를 구성한다.
0/부분/혼합·줄기/과실 전량·음/0 Uref의9사례를 대사했다.
32초의 낮/밤·역 교환/16초 사건과 처음/마지막 사건의5구성을 모두 완주·대사했다.
초기/마지막에서도 사건 후 출력이며 전후 상태와 연속22장부/사건6합계는 별도로 유지했다.
전체3,728개 수치·원 fixture bytes가 사전 기준을 통과했다.

16초 사건을 고정한 dt8/4/2 해를 독립 dt0.25 해와 비교한10관측량·60반분 비율은
모두8 초과, 최소 `15.956044650973858`이다. 빈 과실 첫 진입의 기존 시간 수렴/착과 불확실성은 유지한다.
온도 관련 최대 독립 절대차는 `4.547473508864641e-13 K`다.
최대 사건 온도 변화는 `3.552713678800501e-15 K`, 사건 탄소 잔차는 `1.2605028132384177e-11 mg_CH2O/m2_floor`다.
구성 전역의 최대 축소 열 잔차는 `5.82989212460916e-11 J/m2_floor`,
탄소 `1.3882770475738548e-11 mg_CH2O/m2_floor`다. 전체7수지는 영수증에 있다.

최종/root source1,700개·원본2,148항목·선행 core5·기존 웹 자산/미리보기를 보존했다.
controller/root FD4→4·소유 non-zombie 잔존0, 표본 최대 단일 PID147,255,296bytes,
소유+보호 합328,740,864bytes다. hash 검사는 실행 당시 snapshot이고 이후 문서는 별도 commit이다.
새 PG/브라우저·전체 작기 RHS/writer를 실행하지 않았다.

## 다음 단계·일정과 외부 의존성

다음은 **bounded 자동 구간/사건 구성**이다. 명시 격자와 사건 순서 계약→공동 상태/연속22장부·사건6합계→
같은 경계의 전역7수지·사건 후 출력→독립 궤적/실패 prefix·source/원 종료/자원 검증으로 나눈다.
이 작업이 남아 `crop-climate-joint-integration` 부모는 미완료다.
그 뒤 온실 경계/새 continuation·저장/현재 권리 API/같은 UTC3D→물·양분/구매 에너지→사용자 실행/Decimal 경제다.
온실 원식/자료 조사는 순수 구성 개발과 병행 가능하다.

이번 core5는 실제 약20분의 개발/진단과 별도 root21.269초로 수용했다.
다음 자동 구성은 계약·코드·참조·집중/회귀·root/기록의5묶음으로0.5–2집중시간을 잠정 잡는다.
계속 작업하고 새 수치 장애가 없을 때2026-10-10 중 검토 목표이며 hosted CI 대기는 포함하지 않는다.
실측 뒤 갱신하며 전체 작기/최종 UI·production 완료일은 외부 자료 확보 전 확정하지 않는다.

현재5173은 완료 합성166일의 저장 생장/수확을 읽으며 새 계산·실시간 U3는 미연결이다.
exact4b7fe6f [Backend37941890045](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890045)는
2026-10-10 KST 관측 `83d6f5`에서0–4 success·5 in_progress다. 원 실행을 유지하고 취소를 유발하는 push를 보류한다.
실제 농장 Run/국내 독립 자료0건, G0–G4·생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.
