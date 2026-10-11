# 환기 관리 사건·선택 출력 program 수용 — 2026-10-11

2026-10-11 22:29 KST, [핵심5파일 계약](../contracts/crop-greenhouse-ventilation-program-v1.md)을
사건 포함32초 합성 프로그램으로 로컬 수용했다. [기계 증거](artifacts/crop-greenhouse-ventilation-program-reference-20261011.json)에
core/fixture/CLI/원 guard receipt 해시를 고정했다. UTC/context/저장·사용자 배포와 생산 관문 수용은 아니다.

## 구현과 실제 검증

수용된 환기 RK 구간과 원자 관리를 연결해 각 원 경계에서 step→전역 수지→관리→수지/현재 환기→journal→선택 출력을 수행한다.
기존 다른 Q/Fv는 유지하고 매 현재 stage의 환기 항만 한 번 합성한다.
108상태·25연속/6사건 장부·10수지, signed 제거 열과 사건 후 수관/온도·현재 환기 진단을 보존한다.
원 management의 전후 validation과 새 combined forcing을 구분해 journal에 담았다.
실패 사건/출력은 commit하지 않으며 같은 시각의 사건 전 step-end와 확정 prefix를 보존한다.
기존 모델·프로필·결과·checkpoints를 변경하지 않는 새 program identity다.

| 실제 검사 | 결과 |
| --- | --- |
| 독립 Decimal80 | app import0의133-vector RK4/retention 사건,10프로그램·30선택/10journal·6,480수치 대사·원 fixture bytes 재현 |
| 시간 수렴 |16초 사건 고정3프로그램×12지표×2반분=72비율 모두>8, 독립dt0.25 대dt8/4/2; 최솟값 미기록 |
| 새 집중 검사 |35통과: 원 수치/10수지, 실제 호출/관리 후 forcing·입력 불변, 선택 불변/무사건 stage·0환기 구 관리 정확 동일, closed/bounds/실패 prefix/identity |
| 기존 관련 회귀 | 환기 stage51 + 원 driver72 + 원 관리69 =192통과 |
| 최종 실행 | 고유227통과/pytest71.87초; 원3143 child/tool exit0, guard72.255336365초 |
| 최대 구성 |512선택/128사건·512걸음/32초를 실제 완료, 보고 joint RHS3,458회·정렬/0제거 합계·상한 거부 확인 |
| 실제 multiple 호출 |16걸음/3사건에서 joint107회·환기84회와 metadata 일치; 입력 정규화/management/현재 coupled 호출을 구분 |
| 첫 smoke/독립 생성 | 원46531/66092 각각 child/tool exit0·0.606980591/22.647855591초 |
| 보존/정리 | 기존232계산 파일 SHA·원본2,148·frozen 두 source/기존 자산 동일; protected roots4 live·FD4→4·소유 잔존/PG/passfile0 |
| 관측 WSL RSS | .25초 표본, 단일136,704,000/보호 포함 합729,329,664bytes;512MiB/1GiB 이내 |
| 최종 보존/문서 | 원43252 child/tool exit0·0.606180084초, accepted source1,911/자산171·기존232·두 HTTP200/index hash·DSN/키/현재 권리/검토·guide 권한·로컬 링크2,000·diff check 통과 |

source case ID와 immutable hash로 기존 합성 program 입력을 참조하고 새 환기/독립 값을 기록했다.
사건 후 환기 실패와 global-event 수지 실패는 관리 결과를 journal/선택 출력에 넣지 않는다.
실제 온도 trial hold는 초기 선택 prefix를 보존했다. 기존7stock 수지와 환기3분할을 원량에서 별도 대사했다.
새 package/build/API/Chromium/전체 CI·remote 검사는 실행하지 않았다. 사용자 서버 중단/전환0이다.

실제 native CLI는 `gpt-6.1-sol / xhigh`, turn timestamp `2026-10-11T13:15:25.823Z`,
context SHA `2a7cfcdfee94fd1be361d4d51caff0393a7631ef52ac044f975f38dc2c081f2b`, CLI 재귀 실행0이다.
원식/권리·명시 Rv 변형·실외 QC 미확인은 [기존 원문 검토](crop-greenhouse-boundary-source-review-20261011.md)를 따른다.

## 다음 구현과 사용자 범위

다음은 새25장부/6사건/10수지의 **continuation/context/checkpoint**다.
임의 chunk 분할 정확 동일·fresh trusted digest 복원·과거 적분/사건 재실행0·초기/사건 전후/완료·변조/hold를 먼저 수용한다.
원 elapsed index의 UTC 결속은 그 다음 별도 자식이다. 이어 현재 권리 불변 저장/API→worker/typed web/같은 UTC3D→사용자 적용으로 진행한다.
[계획](../tasks/plan.md)/[작업 목록](../tasks/todo.md)의 의존성과 사전 수용을 갱신했다.
다음 checkpoint는 context/manifest0.5–1집중시간 + advance/restore1–2시간 + fresh/분할/변조·자원0.5–1시간의 잠정2–4시간이다.
이번 program의 이전2–4시간 추정은 실제 수용으로 대체했고3guard 합95.510초, 개발/분석/기록은 별도다.

현재5173은 완료166일 재생,5174는 기존 [A2](crop-climate-joint-prefix-advance-browser-20261011.md)의
합성128초 접수/진행·확정 부분 결과 자동 조회다. **새 환기 program은 UI 미배포**다.
실제 품종/농장 Run·국내 독립 자료0, G0–G4 `not_assessed`, 실제 생산/미래 마진/추천 hold를 유지한다.
다른 온실 경계/물·양분/구매 에너지/경제·최종 UI와 독립 자료가 남아 전체 제품 완료일을 이32초 계산 비용으로 산정하지 않는다.
