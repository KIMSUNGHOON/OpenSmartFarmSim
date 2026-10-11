# 순수 환기 현열·수증기 경계 수용 — 2026-10-11

2026-10-11 21:44 KST, [원문 검토](crop-greenhouse-boundary-source-review-20261011.md)와
[새 핵심5파일 계약](../contracts/crop-greenhouse-ventilation-v1.md)의 **순수 순간 계산**을 로컬 수용했다.
[기계 증거](artifacts/crop-greenhouse-ventilation-reference-20261011.json)에 파일/프로필/고지/CLI/검증 receipt 해시를 고정했다.
전체 온실·작물 결합, 동적 환기 적분, 사용자 배포와 G0–G4 수용은 아니다.

## 계산과 근거

명시 환기량과 같은 시점의 실내 온도·수증기 질량, 실외 온도·수증기압,
부피/바닥면적·공기 현열 밀도·명시 Rv로 공기에 들어오는 현열 Q와 수증기 Fv를 계산한다.
기존 pinned profile의 cp/L을 재사용하고 잠열 L·Fv는 별도 장부로 둔다.
공기 현열에 잠열을 중복 반영하지 않는다. 입력/code/policy/profile/source/notice 해시와
국소 반대 전달을 반환하며 상태·DB·API·UI를 쓰지 않는다.

GreenLight Chapter8 원식과 단위·부호·권리는 위 원문 검토에 기록했다.
현재 joint의 Rv461.5를 보존한 이상기체 감소 모델이며 원8314/18과 다른 판본이다.
8314/18에서 원 압력/온도 식과의 동등성을 별도로 검증했다.
실외 온도의 수학적 양수 Kelvin 조건은 현장 정확도·포화/QC 승인 범위가 아니다.
negative flow/누락 실외 수증기압/단위 오류·비유한·overflow/underflow 등은 명시 hold다.

조사/설계의 실제 native CLI는 `gpt-6.1-sol`, effort `xhigh`, turn timestamp
`2026-10-11T12:27:31.060Z`, context SHA
`8023c0df9afd8951f8c39b62bb1f44b9e421e2044177ad365ce1b1406d8bb02a`다.
CLI 재귀 실행0이며 제안과 관문 승인을 구별했다. 연구 스킬이 요구한 배경 원문 조사1건을 사용했다.

## 통과한 검증

| 검증 | 실제 결과 |
| --- | --- |
| 독립 Decimal 참조 | precision80, 합성6사례/36수치, 상대2e-14/절대0·기대0 정확 일치, 생성 fixture 원 bytes 재현 |
| 새 집중 검사 | 50통과: 부호/0환기/등온 수증기·flow 선형성·질량/부피·원 Rv 동등성/461.5 차이·원 입력/identity·입력/수치 hold |
| 기존 관련 회귀 | joint RHS51 + canopy exchange35 =86통과 |
| 전체 집중 결과 | 고유136통과, pytest0.52초; 원 guard6252/child/tool exit0, 0.867273908996초 |
| 실제 공동 RHS 순간 연결 | 같은 trial에서 Q/Fv만 한 번 가산한 ΔTair'=Q/Cair·Δm_v'=Fv, crop/수관/plant RHS 불변, 기존7수지 예산 통과 |
| 독립 fixture 생성 guard | 원25086/child/tool exit0, 0.347864241005초, application import0 |
| 보존 | 기존 계산/fixture228파일 SHA 동일; 원본2,148항목·frozen 두 source/기존 자산 동일; main 검증 중 고정 |
| WSL/소유 정리 | 두 guard 각각 protected roots4 live, FD4→4, 소유 잔존/PG/passfile0·서비스 중단0 |
| RSS | .25초 표본; 집중 단일136,704,000/합660,004,864bytes, 생성 합620,388,352bytes; 512MiB/1GiB 이내 |
| 최종 별도 보존/링크 검사 | 원75108/child/tool exit0·0.605859361초, accepted frozen source1,911/자산171·기존228·두 HTTP200/index hash·권리/검토/DSN/키·guide 권한·로컬 링크1,993·diff check 통과 |

최종 private 보존 검사 v1은 이전 토큰 회전 전 runtime snapshot을 현재와 통째로 비교해 실패했다.
차이는 기존 승인된 `token_digest/issued_at/expires_at`3항목뿐이고 다른 runtime/권리/검토 값은 동일했다.
v2의 토큰 확인도 private 검사 자체에서 plain SHA를 사용한 오류로 실패했다.
v3은 실제 domain-separated digest 함수와 현재 ready/guide/handoff를 함께 대사해 통과했다.
실패 원77298/22224의 exit1을 보존했으며 제품/계수/수치 허용 오차 변경0이다.

국소 반대 전달의 잔차0만으로 온실 전체 보존을 주장하지 않는다. 독립 값 대사와 기존 공동 RHS
장부의 순간 합성까지 확인한 범위다. 두 guard는 실제 원 종료를 수거했으며 사용자 서비스는 계속 살아 있다.
새 package/build/Chromium/전체 CI·remote 검사는 실행하지 않았다. 새 child의 배포 수용이 아니다.

## 현재 UI 연결과 다음 순서

`http://localhost:5173/`은 완료 합성166일 저장 결과 재생이다.
`http://localhost:5174/`는 **그 사용자 DB에 접수한 작업**의 진행/확정 부분 결과를 자동 조회한다.
[A2 실제 갱신](crop-climate-joint-prefix-advance-browser-20261011.md)은 합성128초/계산 중 원5시점,
완료9시점/3사건을 확인했다. 응답 뒤10초 대기와 조회 처리로 실제 관측33–34초 간격이었다.
별도 개발 DB의 검증 계산이나 이 새 환기 함수는 현재 UI에 자동 공개/배포되지 않는다.
접속/새 요청 파일은 [사용자 안내](../web/README.md#joint-execution-user-preview)를 따른다.

다음 한 단계는 **공동 적분의 각 현재 stage에서 환기 재계산**이다. 새 identity/명시 실외 입력과
독립 짧은 궤적·해상도 수렴·전역 장부/0환기/hold를 검증한다. 그 뒤 새 저장/현재 권리 API와
같은 UTC3D·실제 worker/브라우저·사용자 기동을 별도로 수용한다. 기존 모델/결과를 덮어쓰지 않는다.
작업 분해와 잠정2–4집중시간은 [계획](../tasks/plan.md)의 온실 경계 표에 기록했다.

복사/PAR/NIR·CO₂/기공·시설 환기량과 실외 QC 정책은 미완료다.
PAR 이중 차광·sRsSlope 단위 불일치·top 구획 감소를 자동 보정하지 않는다.
실제 품종/농장 Run과 국내 독립 자료는0건이며 확보와 개발을 병행한다.
G0–G4는 `not_assessed`; 실제 생산/미래 마진/작물 추천은 hold다.
전체 작기·최종 통합 UI·전체 제품 완료일은 이 순간식의 비용으로 산정하지 않는다.
