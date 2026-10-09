# 작물·기후 공동 순간 RHS — 2026-10-10 로컬 수용

## 완료 범위와 확인할 산출물

core `f8f5902d48ebe186fb3cf052fb86e3c391c53d58`의
[한 trial 공동 계산](../backend/app/crop_climate_joint_rhs.py)과
[새 입력/상태 계약](../contracts/crop-climate-joint-rhs-v1.md)을 수용했다.
[10개 합성 사례·1,290개 독립 수치·수지](artifacts/crop-climate-joint-rhs-reference-20261010.json)를 확인할 수 있다.
Artifact SHA-256: `9e45177113e740e1a0d38efe17433fae123cff6ebcd891d4be8f2060bdca9b7f`.
`crop-climate-joint-rhs` 자식만 완료다. **시간 진행·공동 적분·새 저장/API·3D·실시간 U3는 없다.**

한 trial의 leaf→LAI→열용량→signed 저장 열에서 유도한 Tc를 기존 startup/과실50구획과
순간 열·수증기 교환에 공유한다. crop·exchange·gross capacity 공개 함수를 각각 한 번 호출한다.
실제 leaf allocation/maintenance/removal에서 용량 현열을 계산하고,
수관 Uref·공기 현열·수증기/잠열·탄소/개수·용량 장부를 따로 대사했다.
잎 면적/저장 열 변경이 photosynthesis·교환·동적 T24/Tsum 미분을 바꾸는지 확인했다.

기존 121상태/checkpoint·상수 Tcan Fraction clock을 확장하지 않았다.
새 stage schema는 기관5 + 과실 C/N100 + 기후3 = 108개의 모델 상태와 그 초당 미분을 정의한다.
RGR50은 명시 진단 forcing이며 새 적분/추정 상태가 아니다.
광량/CO₂·외부 열/수증기·유입 온도는 명시 합성 입력이다. 자동 온실·품종 예측이 아니다.
기존 프로필·source·결과·서버/미리보기·라이브러리는 보존했다.

## 실제 CLI·원식 근거

부모 실제 native CLI는 `gpt-6.1-sol` / `xhigh`, turn-context
`2026-10-09T15:13:23.447Z`다. 원 JSONL 한 줄 LF 포함 SHA:
`835cd6bee2fe828ec49e3051d0e4bc5c73c9eb66f7db441d5a066eec4bdf916d`.
실제 도구 `c93aa8`과 별도 root가 확인했고 재귀 CLI 실행은 0이다.
개발 판단은 제안/소프트웨어 검토이며 제품 runtime CLI·독립 해제·관문 증거가 아니다.

원식/단위/권리는 [기후 인터페이스 검토](crop-climate-interface-audit-20261009.md)와
[가변 용량 원문 검토](crop-variable-canopy-energy-review-20261009.md)를 사용했다.
프로필4개·기존 독립 참조4개와 source fixture의 9개 입력 SHA,
제품 의존 코드9개·선행 가변 용량 core6·BSD 고지를 재확인했다.
실제 품종 물성·조직 수분·maintenance 대사열·유입 물질 온도는 여전히 미확인이다.
이번 모델은 표현된 용량의 합성 경계이며 실제 농장 자료 채택은 없다.

## 실행과 독립 검증

Python3.12.3의 현재 checkout을 정확한 소유 controller에서 실행했다.
각 실행은 wall120초/로그4MiB·0.25초 RSS 표본·단일512MiB/소유+보호1GiB,
원본2,148항목·미리보기3개 boot/PID/start identity·FD·소유 정리를 검사했다.

| 원 실행 | 실제 결과 | terminal 도구/종료 |
| --- | --- | --- |
| 첫 집중88451 | 1 failed, 50 passed / 0.29초; 수용 아님 | `4b8337` / 1 |
| 수정한 집중20351 | 51 passed / 0.29초; controller0.815초 | `207a67` / 0 |
| 새51 + 기존412의 최종69375 | 463 passed / 2.57초; controller3.118초 | `444a3f` / 0 |
| 별도 root77567 | 독립 참조/원 bytes·1,290스칼라·code/source/수지/FD/native; controller0.561초 | `1bac90` / 0; root 출력 `4ad6cf` |

첫 실패는 시험의 overflow 가정이 틀린 경우였다. 해당 작은 LAI에서는 큰 capLeaf도 유한했고,
보존한 U에 대해 derived Tc가 먼저 허용 창을 벗어나 `TEMPERATURE_HOLD`였다.
시험이 더 큰 leaf도 명시해 실제 Ccan overflow를 검사하도록 고쳤다.
원 실패 로그/시험 bytes/SHA를 보존했고 제품 코드와 사전 오차 기준은 바꾸지 않았다.

[독립 Decimal80 생성기](crop-climate-joint-rhs-reference.py)는 app을 import하지 않고,
고정된 기존 독립 crop/startup·교환·가변 용량 원식을 조합한다.
낮/밤·역 교환·빈/양의 과실 tail·다른 Tin/Tref·명시 제거와 gross turnover의
10개 사례에서 기관5/과실100/기후3 미분·유도량/교환/용량/진단을 비교했다.
전체 fixture bytes를 별도 프로세스에서 재생했고 1,290스칼라가 사전 상대5e-12/절대5e-14,
Tc 절대2e-13 K 기준을 통과했다. 시간 적분 수렴/현장 정확도 기준이 아니다.

같은 stage에 실제 전달한 Tc/LAI·총 leaf 흐름과 세 공개 함수의 호출 수1을 검사했다.
Tref 이동의 signed/0 U에 대해 crop·교환·물리 변화율이 같고 Uref'만 Cdot에 따라 변환됐다.
순 leaf 변화가 거의0이어도 유입 온도에 따른 열 변화가 남는 반례도 통과했다.
공기 현열에 잠열/물질 열을 더하지 않고 수증기와 외부 수관 물 경계를 대사했다.
닫힌 metadata/수치/단위/배열·profile·빈 수관/온도·bulk saturation·수치 실패,
입력 불변·canonical identity/코드·정책·4개 프로필의 결속을 확인했다.

관측 최대 절댓값 잔차는 artifact의 단위 있는 `max_abs_residuals`에 있다.
공동 축소 열은 `1.7631729409828267e-14 W/m2_floor`,
탄소는 `5.371544138307871e-17 mg_CH2O/m2_floor/s`,
수증기는 `2.752857078576476e-21 kg_water/m2_floor/s`다.
원 kernel의 예산과 새 열/용량/수증기 총 항 합 대비3e-13 예산을 유지했다.

검증 당시 source1,686개·원본2,148항목·선행 core6·기존 웹 자산/미리보기를 보존했다.
각 controller FD4→4/root4→4, 소유 non-zombie 잔존0이다.
표본 최대 단일 PID147,255,296bytes·소유+보호 합317,276,160bytes로 한도 안이다.
source/profile/hash 검증은 이 실행 당시 snapshot이고 후속 계획 문서 변경은 별도 commit이다.
새 PG·브라우저·전체 작기 RHS/writer를 실행하지 않았다. 일반 운영 용량 수용은 아니다.

## 현재 UI/CI와 다음 수용

원 사용자 서버24180은 `796a78` 관측에서 계속 실행 중이며 정상 종료를 주장하지 않는다.
현재5173의 완료 합성 생장/수확·같은 UTC3D는 유지한다. 이번 새 RHS/실시간 U3는 미연결이다.
별도 exact4b7fe6f [Backend37941890045](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890045)는
2026-10-10 00:28 KST의 `d5e8fb`에서0/1/2 성공·3/4 실행 중·5 대기다.
동일 실행을 유지하며 새 core의 hosted 수용으로 대신하지 않는다. 취소를 유발하는 push는 보류한다.

다음은 **새108상태의 짧은 공동 적분**이다. 명시 forcing/RGR의 sampling,
공동 RK4 stage·동적 T24/Tsum·signed U/비음수 상태 구분·초 단위 경계,
탄소/개수/열/물질/수증기 누적과 별도 Decimal 궤적/간격 축소를 먼저 계약한다.
원자적인 부분 적엽/과실 관리 사건은 후속 작은 자식으로 대사하고 마지막 확정 상태를 보존한다.
그 뒤 온실 경계·새 continuation/저장·현재 권리 API·같은 UTC3D→물/양분·구매 에너지→
사용자 실행/Decimal 경제다. 기존121상태/원 결과는 그대로 보존한다.

이 RHS의 수용일은2026-10-10이다. 다음 첫 짧은 적분의 상태·원장·독립 궤적/수렴·실행 비용을
확인한 뒤 후속 작업량/날짜를 갱신한다. 순간 시험 비용을 전체 작기 시간으로 외삽하지 않는다.
독립 농장 자료 확보는 개발과 병행한다. 실제 물성/품종·독립 계측·시설/시장/가격/운영 계정의
확보일은 미정이며 실제 농장 Run/국내 독립 자료0, G0–G4/생산·미래 마진·추천·production은 hold다.
