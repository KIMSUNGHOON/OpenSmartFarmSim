# 공급 제한 조달 후 Context·초기 체크포인트 — 2026-10-28 KST

[실제 조달점](crop-supply-morphology-point-20261028.md)의 상태와 장부를 진짜 새 Context와
초기 체크포인트(CP)에 채택했다. 일정은 채택할 때 한 번 소비한다.
**시간 전진·후속 반복·새 저장 결과/3D·제품 farm 통합은 다음 작업이다.**

[소유 모듈](../backend/app/crop_supply_morphology_context.py)과
[읽기 전용 증거 검사](../backend/app/crop_supply_morphology_context_proofs.py)는
[새 내부 계약](../contracts/crop-supply-morphology-context-v1.md)을 따른다.
기존 수용 모듈·원 입력·프로필을 변경하지 않았다. 실제 after C/A/L/나이·ID/부모/clock,
원/새 건설비, birth·lifetime·point/global과 원 수치 격자를 보존한다. 실제 길이0도 그대로다.

다음 threshold는 원 phyllochron을 한 번 더하며 계산 age를 threshold에 맞추지 않는다.
물리 누적량은 원 root, 형상 누적량은 공급 제한 분기 시작을 기준으로 유지하고 새 기관의
연속 형상 채널은0으로 시작한다. seed 형상 대응 탄소를 연속 유입으로 중복 계상하지 않는다.
원 prefix에 실제 before/after 두 시점과 phase·point hash를 연결한다. 새 CP의 branch 장부는
모두0이며 global은 실제 조달 후 preview와 같다. 영속 farm 사건 중복 방지까지 구현한 것은 아니다.

| 검증 | 실제 결과 |
|---|---|
| 집중 검사 | **39개 한 실행 통과**. 진짜 소유/일정·길이0/양수·선택 잎, rehash CP9/Context7/point8변조, 입력/권리 도중 변경, trusted hash/canonical, 현재 계산 도중 source/profile/code 변경·RuntimeError와 old handle 거부 |
| 별도 생성/복원 | 원4Context에서 수용된 **10개 Context·point·CP 바이트 동일**. 각 원 source38파일의 bytes/metadata 보존. 공개 저장소에 개인 영역 원문은 전재하지 않음 |
| 실제 실행 수 | 각 프로세스의 원 owner 준비는 old RHS2·원 receipt 자금 산술16회로 따로 계측. 생성 단계는 candidate340RHS·material14RHS·자금 차감14·새 잎 초기화4, CP 현재 검증10RHS. 복원 단계는 과거/후보/조달/자금/잎 초기화0·새 현재 RHS10(각 CP1회). DB/network/write0 |
| 독립 검사 | app import/RHS0, 기존 point 원 bytes10·hash30·code pin780, seed160·schedule90·grid50항목, 상태1,442값·lifetime1,108채널(물리612/형상 이월440/새0채널56), branch flow1,108·branch 장부0항1,420·global710·prefix20연결 대사. 실제0길이6사례 |
| 원 격자 | 기존8초×64/512초 horizon 유지. 사건은256–264초 사이이며 다음 원 시각264초까지의 분수 잔여를 정확 보존. **잔여 적분 자체는 미실행** |
| 보존 | 이전188source/1output, 원 source38파일·private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존. 외형5175 HTTP200;5180은 원 만료/PID 없음·저장 보존 |
| WSL | 순차 guard512MiB/PID·1GiB combined·600초/.25초. 수용 phase 최대 PID143,835,136/합계224,251,904bytes. 보호 프로세스·원 항목 보존, owned remaining0·FD4→4. 전체 호스트 메모리 측정 아님 |

Cold Context 복원·start/export에는 coupled RHS·조달·자금 차감·잎 초기화가 없다.
영수증의 순수 산술·현재 원본/프로필 확인은 수행한다. CP 복원은 실제 새 stage로 현재 상태를
한 번 확인한다. trusted 원 hash·genuine source가 필요하며 self-rehash나 hash 일치만으로
외부 출처·농장 custody·관문 승인을 부여하지 않는다. CP는 **초기 상태만** 지원한다.

## 실패와 수정

첫 RED는 새 모듈 부재였다. 추가 RED에서 실제 두 결함을 재현했다. 재해시한 point의 추가
주장 필드와, 조달 직후 호출자 권리가 바뀌는 경우가 차단되지 않았다. 원 point/candidate/stage
닫힌 필드 집합과 채택 반환 전 입력/tolerance 불변 확인을 추가했다. 수정 후3검사와 최종39검사,
별도10개 생성/복원·독립 검사 모두 통과했다. 실패 기록도 구조화 증거에 보존한다.

원 수용 point의 독립 Decimal200 조달/열/장부 검증은 그 immutable 원 bytes와 hash를 재사용했다.
이번 별도 검사는 새 채택·일정·격자·prefix·장부 이월을 독립 대사했다. 원 물리 모델 전체를
새로 독립 검증했다고 주장하지 않는다. 새 외부 자료/품종 계수 채택0이다.

## 다음 한 단계의 수용 기준과 일정

`supply-morphology-newborn-grid-resume`를 다음으로 진행한다.

1. 실제 새 seed를 입력으로, 길이0을 포함한 같은 newborn stage의 공동 RK4로 사건→264초
   잔여와 이후 원8초 격자를 전진한다. 새0길이를 epsilon/양수로 바꾸거나 과거 source를 재생하지 않는다.
2. 실제 state/ID/부모·birth/clock·원/새 k·phase·lifetime/point/global을 유지하고, 전체/분할/새
   프로세스 복원에서 동일 CP bytes를 보인다. 현재 RHS 검증은 과거 재생과 분리 계측한다.
3. 다음 threshold를 넘겨 조달하지 않고 확정 prefix로 보류한다. source/profile/code/rights·late
   변경·수치/예산·크기 실패는 마지막 확정 CP를 보존한다. 독립 잔여/적분/장부·fresh·원 자료/GUI/WSL을 검증한다.

잠정90–155집중분(잔여/격자40–65 + 소유 CP/복원/실패30–50 + 독립/fresh/보존20–40)이다.
다음 새 owner의 후보/조달·반복120–200집중분, 그 뒤 불변 저장/무계산 reader/strict SDK/
같은 상태 실제3D180–300집중분 초안을 유지한다. 남은 수치 재개/반복210–355집중분이며
자료 확보·제품 통합·최종 사실감의 기간을 포함하지 않는 낮은 신뢰 작업량 추정이다.

실제 대상 품종/국내 독립 측정0·G0–G4 미평가/R2 미승인이다. 자료 확보와 합성 개발은 병행한다.
한 작기·과실/수확·자원 구매·Decimal 경제/거시/수급·자율 작물 비교·제품 UI 통합은 미완료이며
전체 완료일은 자료 확보와 후속 분해 전 미정이다. 이번에 새 DB/API/worker/browser나 전체
backend/frontend suite는 실행하지 않았다. whole goal은 active/incomplete다.

실제 native turn2026-10-28T12:11:35.114Z의 gpt-6.1-sol/xhigh를 관측했다.
원 LF SHA는 `132d1bd50125673bd63bc3d7c4932edbc64f69934883e1e7868f0495318fc398`, 재귀 CLI0이다.
[구조화 증거](artifacts/crop-supply-morphology-context-20261028.json)에 phase·raw hash·호출 수와 보존 결과를 기록한다.
