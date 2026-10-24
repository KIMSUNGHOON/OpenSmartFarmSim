# 잎 면적 상태를 재맞추지 않는 분할 재개 — 2026-10-24

상태: **사건 없는 합성 연구 계산의 재개 자식 수용**. 현재 농장/UTC·정확 제거/생산 검증은 미수용이다.
[계약](../contracts/crop-growing-geometry-continuation-v1.md), [구현](../backend/app/crop_growing_geometry_continuation.py),
[검사](../backend/tests/test_crop_growing_geometry_continuation.py), [근거](artifacts/growing-geometry-continuation-20261024.json),
[후속 순서](../contracts/crop-geometry-carbon-coupling-research-v1.md).
기존 수치 식/계수·프로필·정확/canonical 상태/저장3D·서버·DB/키를 바꾸지 않았다.

## 실제 변경과 경계

기존 short.integrate는 새 초기화 전용이며 끝 면적을 initial_area로 다시 넣으면 canonical 초기화가 반복된다.
새 Context는 원 요청·정규 program·초기 a/A/영수증/D0·최초 RHS를 불변 bytes로 한 번 고정한다.
정책·프로필/코드와 Python/platform/float 환경·원 격자도 manifest에 결속한다.
public program property는 원 요청 복사본이므로 다른 프로세스에서 같은 context를 구성할 수 있다.
현재 실제 a/A·C/N/Uref/공기/증기는 초기값과 별도로 보존한다. 이후 면적을 다시 canonical로 만들지 않는다.

start는 초기 sample을 확정한 checkpoint를 추가 RHS 없이 만든다. restore는 현재 endpoint1회,
advance는 현재 endpoint 검증1회 뒤 새 걸음당4stage만 평가한다.
short의 원 evaluate/advance/weighted/flux/sample/balance helper를 그대로 재사용하며 새 농업 식/계수는 없다.
누적량을 chunk 단위로 다시 더하지 않고 각 걸음의 원 순서로 누적한다. D0/초기 영수증도 원 seed를 유지한다.
각 sample의 prefix를 연결해 chunk 크기·복원 횟수/시각이 최종 bytes에 들어가지 않게 했다.

체크포인트는256KiB 이하 닫힌 canonical JSON·외부 trusted SHA·동일 context와 일치해야 한다.
float64 벡터/단위·현재 시각/유도량/곡선 차이/전역 장부·예산을 대사하고 과거를 다시 적분하지 않는다.
자체 해시는 인증이 아니며 향후 서버의 권한 있는 불변 저장/서명이 trusted digest를 제공해야 한다.
이 구현은 Python 내부 필드 재작성의 보안 경계·농장 권한/영속 게시가 아니다.
완료 checkpoint는 읽을 수 있지만 재전진하지 않는다. 수치/도메인 hold는 마지막 확정 prefix와 checkpoint=None을 반환한다.
입력 오류는 전진 전에 거부하고 외부 crash를 정상 hold로 삼지 않는다. 검토에서 context/용량 hold 사유 보존도 보완했다.

## 실제 검증

- **RED/부분/첫 전체:** 모듈 부재 collection exit2, transport10선택 검사·첫69검사가 통과했다.
- **최종 고유211:** 새160 + 원 short51이다. 앞의10/69/136을 중복 합산하지 않는다.
  독립6프로그램×분할 크기1/3/128과 모든 단일 cut1–15의 sample/현재 상태·21장부·잔차/예산,
  최종 checkpoint bytes/SHA가 원 전체 실행/다른 분할과 정확히 같았다.
  현재 초기화 helper를 막은 복원/advance, 원 요청/응답 복사, 초기/중간/완료·코드/환경/프로필·격자/형상/단위/
  SHA/비정규/중복/비유한/큰 입력·1/512잎/예산·초기/늦은 hold/용량 사유/외부 crash를 확인했다.
- **별도 producer:** 원 Decimal110 fixture의6프로그램/822최종 수치와 대사했다.14개0은 정확0,
  최대 상대 차이2.772652936392501e-15였다. 새로운 독립 방정식 참조를 만들지 않고 원 고정 fixture/hash를 재사용했다.
  자체 합성 producer의 원/중간 checkpoint와 전체 예상 결과를 private0400의781,966bytes 묶음으로 보관했다.
- **별도 읽기 전용 consumer:** 원 묶음 SHA를 명시해6프로그램의 초기0/중간8, 총12capsule을 복원했다.
  남은144걸음/반환 sample과 최종2,016개 domain 수량, 최종 checkpoint 원 bytes/SHA가 producer와 같았다.
  54chunk에서 원 초기 context 구성6회·현재 상태 검증66회·새 stage576회=실제648평가,
  새 걸음의 상태/장부 update720회였다. 복원 중 전진0과 검증되는 벡터가 해당 현재 checkpoint임을 계측했다.
  현재 면적 재초기화/과거 걸음 replay0·옛 SLA joint/옛 적분 import0·옛 advance/정확 시계/DB/CLI/network/쓰기0·FD 보존을 확인했다.
  trusted digest는 이 자체 합성 producer의 증거이며 실제 농장 서명/권한 승인이 아니다.
- **WSL:** .25초/512MiB PID·합1GiB/600초/로그4MiB를 유지했다.
  최종211은 PID peak80,646,144/합508,047,360bytes, producer는 합438,112,256,
  consumer는 합456,478,720bytes였다. 원2,966항목/repo source·4root 생존·감독FD4→4/소유 잔류0을 확인했다.
- **미실행:** 전체 backend/호스티드 CI·브라우저·새 저장/공개 조회·정확 제거·현재 농장/실제 품종·미래/비교/배포 검증.
  현재3D는 이전 수용 결과를 유지하며 새 면적/기후 계산은 화면에 아직 연결하지 않았다.

부모 native context2026-10-24T06:36:56.883Z의 gpt-6.1-sol/xhigh와 원 LF SHA
`078ba2202f88e2d1f9da71c5c16f87c31d71771aba50282608805c926a86acae`를 기록했다. 재귀 CLI/새 연구 agent0이다.
기존 [연속 계산/원문·권리](crop-growing-geometry-climate-20261024.md)를 재사용했으며 새 원문 GET/측정/계수 채택0이다.
실제 제품 CLI G1·SourceRecord/G0–G4 해제나 실제 작기/자원/경제·추천의 근거가 아니다.

다음은 **고정 목록 계산 결과의 불변 저장/무계산 조회→기존 사실적3D**다.
사용자가 검증된 면적 상태를 볼 수 있도록 원 program/코드·policy/profile·state layout/leaf ID·elapsed·원 수량을 먼저 저장한다.
표시용 epoch는 명시 자체 합성 선언으로 받으며 실제 관측/농장 UTC로 꾸미지 않는다. reader/SDK/UI는 재개/생장 계산을 다시 실행하지 않는다.
기존 artifact/현재 권리·export/renderer 구조를 재사용하고 실제 계산 면적과 제작 stem/pose를 구분한다.
정확 제거/새 출현 질량·공급 제한·독립 면적의 탄소/용량 사건과 전체 작기·자원/경제는 후속으로 유지한다.
첫 저장/조회는 계약15–25 + 최소 재사용 writer/reader25–45 + 불변/무계산·실패/fresh30–50 + 기록10–20 =
**80–140집중분**, 낮은 신뢰의 개발 추정이다. SDK/화면 작업은 기존 컴포넌트와 저장 계약을 확인한 뒤 별도 분해한다.
원 측정/미사용 독립 국내 작기0·첫 국내 품종 미확정이며 farm/현재 권리 실행·자료 확보는 병행한다.
전체 완료일·실제 생산/자원/경제·자율 비교/추천/R2/G0–G4는 미정/미완료다.
