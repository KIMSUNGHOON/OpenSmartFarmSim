# 환기의 현재 공동 stage 적분 수용 — 2026-10-11

2026-10-11 22:09 KST, [핵심5파일 계약](../contracts/crop-greenhouse-ventilation-joint-v1.md)의
사건 없는32초 합성 궤적을 로컬 수용했다. [기계 증거](artifacts/crop-greenhouse-ventilation-joint-reference-20261011.json)에
원 code/fixture/CLI/guard receipt 해시와 실제 검증 범위를 고정했다.

## 구현과 검증

매 RK4 stage의 현재 Tair/m_v와 같은 parent h/rho/Rv로 환기 Q/Fv를 다시 계산해
기존 다른 강제 항에 정확히 한 번 합성한다. 잠열은 별도 장부이며 공기 현열에 중복 반영하지 않는다.
기존108상태와25연속 장부가 같은 stage/가중치를 쓰고, 원7전역 수지에 환기 분할3수지를 추가했다.
새 model/code/policy/input/numerical identity가 기존 RHS/적분 helper/교환·작물 프로필 해시를 결속한다.
기존 코드/프로필·22장부 context/checkpoint와 저장 결과를 변경하지 않았다.

| 실제 검증 | 결과 |
| --- | --- |
| 독립 Decimal80 | application import0의133-vector RK4,6궤적×(108상태+25장부+3유도량)=816수치 대사·원 fixture bytes 재현 |
| 시간 수렴 |3사례×12물리/장부 지표×2반분=72비율이 모두>8; 독립 dt0.25 대 dt8/4/2. 최솟값은 별도 기록하지 않아 수치로 보고하지 않음 |
| 새 집중 검사 |51통과: 실제 stage/합성1·endpoint/sample·입력 불변,0환기 원 물리 결과 정확 동일, 초기 항 고정 반례, signed/0 Uref, 장부/hold/identity |
| 기존 회귀 | 순수 환기50 + 공동 적분44 + 공동 RHS51 + 수관35 =180통과 |
| 최종 집중 실행 | 고유231통과/pytest26.05초·원56935 child/tool exit0·guard26.576577015초 |
| 첫 실제 smoke | 원58608 child/tool exit0·0.347281813초,17sample/25장부/10수지. 환기 Q가−36.0→−39.1117597323 W/m², 마지막 Tair18.1728755407°C |
| 독립 참조 생성 | 원73424 child/tool exit0·20.282443845초 |
| 보존/정리 | 기존230계산 파일·원본2,148항목·frozen 두 source/기존 자산 동일, protected roots4 live·FD4→4·소유 잔존/PG/passfile0 |
| 관측 WSL RSS | .25초 간격, 최대 단일136,704,000/보호 서비스 포함 합673,984,512bytes;512MiB/1GiB 이내 |
| 최종 보존/문서 검사 | 원84380 child/tool exit0·0.60498638초, accepted source1,911/자산171·기존230·두 HTTP200/index hash·DSN/키/현재 권리/검토·guide 권한·로컬 링크1,996·diff check 통과 |

66회 중1회는 입력 정규화용 RHS, 나머지65회는 환기1/공동 RHS1의 같은 현재 trial이다.
RHS와 snapshot 대조·독립 원량/장부·10수지 예산과 사전 절대 기준을 확인했다.
양수 tail6사례의 짧은 합성 계산이며 실제 착과/품종 정확도나 전체 작기 안정성 근거가 아니다.
새 package/build/API/Chromium/전체 CI·remote 검사는 실행하지 않았다. 기존 사용자 서버는 중단/전환하지 않았다.

실제 native CLI: `gpt-6.1-sol / xhigh`, turn timestamp `2026-10-11T12:52:13.530Z`,
context SHA `034722d93b4d68cd4a9b5fa7a44eaa275a42b0dd16c69d4910733f62b68041c0`, 재귀 CLI 실행0.
환기 원식·권리·Rv 변형·실외 QC 미확인은 [기존 원문 검토](crop-greenhouse-boundary-source-review-20261011.md)를 따른다.

## 다음 사용자 연결 의존성

기존 [분할 실행](../contracts/crop-climate-joint-continuation-v1.md)을 대조했다.
그 context는 old driver/code/22장부에 exact 결속되므로 이25장부 결과를 끼워 넣을 수 없다.
다음 순서는 **원자 관리/선택 출력 program →새 context/checkpoint/UTC →현재 권리 불변 저장/API →worker/typed web/같은 UTC3D/사용자 적용**이다.
관리 뒤 바뀐 수관/온도,25연속/6사건 장부, 임의 chunk의 정확 동일성과 fresh 과거 적분0을 선행 수용한다.
[계획](../tasks/plan.md)과 [작업 목록](../tasks/todo.md)의 저장/3D 부모를 네 자식으로 보완했다.

다음 program은 계약/사건 장부0.5–1집중시간, driver1–2시간, 독립 참조/실패·자원0.5–1시간의
잠정2–4시간이다. 이번 stage의 이전2–4시간 추정은 실제 수용으로 대체하며3guard 합47.206초,
개발/분석/기록은 별도다. 전체 배포/제품 완료일은 program/context 비용과 자료 확보 상태를 보고 갱신한다.

현재5173은 완료166일 저장 재생,5174는 기존 [A2](crop-climate-joint-prefix-advance-browser-20261011.md)의
합성128초 접수/진행·확정 부분 결과 자동 조회다. **이 새 환기 적분은 UI 미배포**다.
실제 품종/농장 Run·국내 독립 자료0건, G0–G4 `not_assessed`, 실제 생산/미래 마진/추천 hold는 유지한다.
복사/PAR/NIR·CO₂/기공·시설 환기량·물/양분·구매 에너지·경제와 최종 통합 UI는 남아 있다.
