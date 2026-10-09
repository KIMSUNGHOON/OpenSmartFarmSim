# 가변 수관 열용량 운반·적엽 — 2026-10-10 로컬 수용

## 완료한 범위

core `9f7dea97707761e1dd123162f3c123104059fb51`의
[순수 계산](../backend/app/crop_canopy_energy_transport.py)·
[닫힌 계약](../contracts/crop-canopy-energy-transport-v1.md)과 독립 사례를 수용했다.
`crop-climate-variable-canopy-energy` 자식만 완료다. 전체 작물·기후 결합은 미완료다.
사용자가 확인할 산출물은 [15개 합성 사례·검증 수치](artifacts/crop-canopy-energy-transport-reference-20261010.json)다.
새 UI/API/DB·공동 RHS/적분·실시간 진행은 추가하지 않았다.
Artifact SHA-256: `ab81cc9abf57ccdef03a1f70372a4df10252effa2a06a01a35be684ad2dce1fa`.

`capLeaf*(sla*leaf)`의 표현된 열용량에 대해 총 allocation/maintenance/removal을 각각 기록한다.
명시 유입 온도와 현재 온도의 유출을 사용하며 물질 경계의 현열을 별도 장부에 둔다.
순 LAI 변화가 0이어도 총 유입/유출이 있으면 온도 변화가 생기는 반례를 통과했다.
부분 적엽은 leaf/C/U를 함께 줄여 온도를 유지하고 부호 있는 유출 열을 보존한다.
기준온도가 잎 온도보다 높아 U/유출 열이 음수인 경우도 허용했다.
빈 수관·전량 제거·초과 제거·표현 불가능한 입력은 명시 hold다.

이는 탄수화물과 잎 수분을 동일시하는 물리 모델이 아니다.
maintenance에 따른 용량 감소도 현재 `LAI=sla*leaf`에 부여한 **합성 재고 경계 선택**이다.
대사열·실제 물질의 수분/현열·실측 품종 물성은 계산하지 않는다.
기존 참조 SLA만 재사용했고 `capLeaf/Tin/Tref`는 숨은 기본값 없이 명시 입력이다.
실제 계수/농장 자료 채택·관문 승격은 0이다.

## 원문·CLI 근거

[원문/현재 인터페이스 검토](crop-variable-canopy-energy-review-20261009.md)의 고정 GreenLight
Chapter8/9·고지, 원 thesis 식/페이지와 단위를 부모가 대조했다.
원 `C*Tc'=Φ`는 그 경계를 명시하면 가능하며 자동으로 오류라고 판정하지 않는다.
현재 선택은 별도 incoming temperature와 signed energy 원장을 갖는 새 합성 경계다.
원문/계수·자료의 권리·available-at 미확인은 해당 노트의 hold를 유지한다.

부모의 실제 native CLI는 `gpt-6.1-sol` / `xhigh`, turn-context
`2026-10-09T14:55:35.684Z`, 원 JSONL 한 줄 LF 포함 SHA
`e00638a94ca659eda567ababe51563708ac68fb25e7d3cd3586f18174bfddbcb`다.
실제 확인 도구 `576d44`, 별도 root가 같은 native 문맥을 재확인했다. 재귀 CLI 실행은 0이다.
research 스킬의 기존 background agent는 정확한 모델/강도로 요청된 orchestration attestation을
명시했으며, 본인 native 사건 미확인을 부모의 문맥 해시로 채우지 않았다.
이 개발 검토는 제품 runtime CLI·독립 해제/관문 증거가 아니다.

## 실제 실행·검증

별도 소유 controller가 동일 보호 미리보기 3개 identity와 원본 2,148항목을 보존했다.
각 실행은 wall 120초·로그 4MiB·0.25초 RSS 표본과 정확한 소유 정리를 사용했다.
현재 checkout의 Python3.12.3(`fb30d7` 실제 확인)을 사용했고 새 패키지·PG·브라우저는 기동하지 않았다.

| 실행 | 실제 결과 | 원 도구·종료 |
| --- | --- | --- |
| 새 집중 시험 | 48 passed / pytest 0.12초; controller 0.560초 | 97978 → `3ba96c`, 0 |
| 새 + 기존 생장/startup·열·교환·고정 LAI 회귀 | 412 passed / pytest 2.42초; controller 2.859초 | 67792 → `7f8b89`, 0 |
| 별도 Python root 대사 | Decimal 참조 bytes·195스칼라·source/notice·FD·native 문맥; controller 0.564초 | 28039 → `7ee847`, 0; root 출력 `269c08` |

[참조 생성기](crop-canopy-energy-transport-reference.py)는 app을 import하지 않는다.
Decimal80의 열린 에너지 식으로 온도율을 유도하며, 적엽 참조는 제거한 용량의 열을 먼저
계산해 에너지에서 뺀다. 제품의 축약 온도식/에너지 용량 비율과 다른 경로를 대사했다.
10개 연속 사례/5개 사건의 195개 독립 스칼라와 fixture 원 bytes 재생을 확인했다.
기존 growth/startup의 실제 총 leaf 흐름과 순 leaf/LAI도 대사했다.
성장 호흡을 잎에서 다시 빼거나 순변화만 사용하는 오식을 수용하지 않는다.

사전 상대 기준 3e-13, 사건 온도 절대 2e-13 K를 바꾸지 않고 통과했다.
관측 최대 물질 RHS 잔차는 `1.6653345369377348e-16 W/m2_floor`,
사건 에너지 잔차는 `1.8189894035458565e-12 J/m2_floor`, 사건 온도 잔차는 `0 K`다.
기준온도 변경·음의 에너지/유출·0 제거/0 열·전체 제거/초과/수치 정체·
닫힌 필드/단위/비유한/overflow/underflow와 입력 불변을 시험했다.
실제 농업 정확도·전 기간 모델 수렴을 증명하는 수치는 아니다.

검증 당시 source 1,679개, 검토 snapshot 9개와 원본 2,148항목을 확인했다.
새 core6(핵심5 + source 검토)의 SHA는 artifact에 있다. 이후 계획 문서 수정은 별도 commit이다.
controller FD는 각 4→4, root FD 4→4, 소유 non-zombie 잔존 0,
보호 미리보기 identity/원 source/기존 웹 자산은 보존했다.
표본 최대 단일 PID `147,255,296 bytes`, 소유+보호 합 `316,006,400 bytes`로
512MiB/1GiB 안이다. 표본 측정이며 모든 운영 부하의 용량 수용은 아니다.

사용자 원 미리보기 handle 24180은 `3c1b0a` 관측에서 계속 실행 중이다.
`localhost:5173` HTTP200, 서비스 FD8·조회 재계산/게시0을 확인했다.
정상 종료했다고 주장하지 않으며 완료 합성 생장/수확의 기존 조회·3D를 보존한다.
실시간 U3와 이번 모듈의 화면 연결은 미완료다.

## CI·남은 작업과 날짜

별도 exact `4b7fe6f` [Backend37941890045](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890045)는
2026-10-10 00:06 KST 관측에서 0/1 성공, 2/3 실행 중, 4/5 대기다.
집계 queued는 중단이 아니며 동일 작업을 유지한다. 이 새 core는 hosted 미수용이다.
현재 실행을 취소하는 push를 보류하고 로컬 commit을 보존한다.

다음 작은 단계는 **새 공동 RHS**다. 같은 trial의 leaf→LAI→C/Tc→작물·교환→
총 용량 흐름을 연결한다. 기본 수관 상태는 signed `Uref`이고 Tc는 유도한다.
`Uref'=Qcan-H-LE+Qmaterial`, 기존 공기 현열/수증기와 crop 탄소·T24/Tsum을 대사한다.
새 상태/단위/입력/clock identity를 계약하고 기존 121상태/checkpoint를 확장하지 않는다.
그 다음 짧은 공동 적분/관리 사건·수렴 → 온실 경계 → 새 저장/같은 UTC3D →
물/양분·구매 에너지 → 사용자 실행/Decimal 경제다.

이 자식 수용일은 2026-10-10이다. 다음 RHS의 사전 범위/독립 사례를 먼저 고정하고,
짧은 공동 적분 비용·새 저장 경계가 확인되기 전에는 전체 모델/제품 완료일을 산정하지 않는다.
실제 품종 물성/유입 물질·온도·독립 농장 자료·온실/시장/가격 증거는 외부 의존성이다.
독립 자료 확보는 합성 개발과 병행할 수 있다. 실제 농장 Run/국내 독립 자료는 0이며
G0–G4, 생산·미래 마진·순위·production은 `not_assessed`/`hold`다.
