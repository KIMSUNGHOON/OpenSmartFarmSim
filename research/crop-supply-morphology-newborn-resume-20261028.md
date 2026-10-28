# 공급 제한 새 기관의 원 격자 재개 — 2026-10-28 KST

[수용된 실제 조달 후 Context](crop-supply-morphology-context-20261028.md)에서
분수 잔여와 원 격자를 전진했다. **후속 기관 조달·일정 추가 소비·새 저장 결과/3D는 아직 없다.**
[재개 모듈](../backend/app/crop_supply_morphology_newborn_resume.py)과
[장부](../backend/app/crop_supply_morphology_newborn_books.py)는
[내부 계약](../contracts/crop-supply-morphology-newborn-resume-v1.md)을 따른다.

기존 진짜 Context를 그대로 사용하며 새 전진 CP 타입을 발급한다. seed-only 검증기를 바꾸거나
이전 타입의 가짜 handle을 만들지 않았다. 실제0 길이를 epsilon으로 바꾸지 않고 같은 newborn
stage의 C/면적/길이·기후를 공동 RK4로 전진한다. 점 장부·원/새 k·기관/부모/ID·birth는 유지한다.
원 물리 root와 공급 제한 형상 분기의 누적 원점을 구분해 실제 원 식과 global=seed+branch를 대사한다.
현재 기관 나이는 원 birth/air integral·현재 벡터로 재구성하며 Context의 seed metadata를 덮어쓰지 않는다.

| 검증 | 실제 결과 |
|---|---|
| 집중 검사 | **33개 한 실행 통과**. 실제0길이→분수 잔여/원 격자, 전체/분할/cold 동일 CP, 공유4stage·모든 유량, 다음 문턱/확정 prefix, rehash 변조12, budget5, 도중 source/profile/code/caller/stage-input 변경, domain/RuntimeError·raw cap/hash·old handle 거부 |
| 별도 생성·복원 | **10개 seed/전진CP·다음 문턱 구간 동일**. 원4Context·잎 포함/미포함·0/양수 길이·원 k 조건 유지. 각5확정 구간:264·272·280·288·296초, 다음 문턱은296–304초의 미정밀 구간에서 보류. 일정/점 장부 추가 소비0 |
| 실제 호출 | 각 원 owner 준비는 old RHS2·원 receipt 자금 산술16회로 따로 계측. 생성의 전체/분할/현재 복원 총510새 RHS, 소비의 현재 CP검증/같은 다음 구간 총60새 RHS. 과거/old RHS·old CP/point·자금 차감·잎 초기화·DB/network/write0. 새 CP 복원은 현재 RHS1회; start/export0회 |
| 독립 산술 | app import/RHS0의 Fraction/Decimal200으로50확정 구간·10pending, stage 좌표21,630·상태7,210·적산량5,540, local710/global 합710·원점 형상식372·기관 clock124·prefix50·schedule10·hash20/code800 대사 |
| 반올림 경계 | Decimal200과 정확 이진 중간점9사례의 차이를 별도 확인. 인접 binary64 값·정확 midpoint·짝수 bit와10^-180 상대 범위로 판정. 실제 커널/계산값·수지 예산 변경0 |
| 보존 | 이전194source/1output·원 source38파일 bytes/metadata, private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존. 외형5175 HTTP200;5180은 원 만료/PID 없음·저장 보존 |
| WSL·시간 | 순차 guard512MiB/PID·1GiB combined·600초/.25초. 집중255.30초, 별도 생성/복원546.59초. 수용 phase 최대 PID110,206,976/합계175,022,080bytes. owned remaining0·FD4→4·보호 프로세스 유지. 전체 호스트 메모리/한 작기 성능 수용 아님 |

다음 threshold의 단조 dense polynomial은 구간 탐지만 확정한다. 새 후보의 정확 근/조달 시각을
발급하지 않고 원 확정 prefix와 미채택 bracket을 반환한다. 그 오른쪽 상태에 CP를 발급하거나
자동으로 기관을 추가하지 않는다. trusted 원 CP hash와 genuine Context가 여전히 필요하며
self-hash만으로 farm custody/외부 출처·관문 승인을 주지 않는다.

## 실패와 수정

첫 RED는 모듈 부재였다. 첫 실제 구간은 통과했지만 확장 검사에서17통과/16fixture오류가 났다.
다음 문턱 응답의 시간 원점이 이전 자료의 `initial`을 참조하고 있었다. 실제 새 seed의
`initial_sample`에 연결했다. 독립 전진 검사도 직렬화된 dict의 정렬 순서 대신 실제 trace의
`flux_order`를 사용하도록 고쳤다. 수정 후33검사와 별도10조건이 통과했다.

독립 Decimal200 검사의 첫 실행은 정확 이진 midpoint에서 실패했다. 유한 소수의1/3 근사가
중간점의 양쪽으로 치우칠 수 있어, 해당 사례는 정확 분수·인접 값과 짝수 반올림을 추가 확인했다.
나머지 Decimal200 결과는 동일하다. 실패 로그와 수정된 독립 검사를 모두 보존했으며 실제 계산
커널·계수·입력이나 수지 허용치를 바꿔 통과시키지 않았다.

[구조화 증거](artifacts/crop-supply-morphology-newborn-resume-20261028.json)에 현재 raw pin·phase·호출 수와
보존 결과가 있다. 개인 영역 원문은 공개 저장소에 전재하지 않았다. 새 외부 자료/품종 계수 채택0이다.

## 다음 한 단계·의존성과 일정

다음은 `supply-morphology-repeated-funded-events`다. 첫 하위 작업은 **실제 새 전진 CP의 다음
후보**다. 다음 수용 기준을 충족한 뒤 명시 조달·반복으로 이어간다.

1. 수용 CP/current stage와 그 다음 실제4stage·단조 certificate에서 exact 근 구간과 상한 상태/
   부분 적산량·local/global·현재 clock/ID를 계산한다. 이전 trajectory의 후보/typed handle을 이식하지 않는다.
2. 같은 후보 시각의1/2/4진단·단위/원/새 k·권리·현재/late code/profile/source·tolerance/size/실패를 검증한다.
   후보만으로 schedule 소비·material point·CP/새 기관을 발급하지 않는다.
3. 독립 근/상태/누적/장부·fresh/원 자료·GUI/WSL 검증을 기록한다. 다음 명시 seed 조달과
   새로운 owner/일정 단일 소비·반복 전역 체인은 따로 수용한다.

후보45–75 + 명시 조달35–60 + owner/반복·독립 체인40–65 = **잠정120–200집중분**의 낮은 신뢰
작업량 추정이다. 다음 후보 한 단계는45–75집중분이며 실제 proof/owner 분해 결과에 따라 갱신한다.
그 뒤 불변 저장/무계산 reader/strict SDK/같은 상태 실제3D180–300집중분 초안을 재검토한다.
새 전체 작기 성능·farm/worker 통합/최종 R2·독립 자료 확보의 기간을 포함하지 않는다.

실제 품종/국내 독립 측정0·G0–G4 미평가/R2 미승인이다. 자료 확보는 합성 개발과 병행한다.
전체 작기·과실/수확·자원 구매·Decimal 경제/거시·수급·자율 비교·제품 UI 통합은 미완료이며
전체 완료일은 미정이다. 새 DB/API/worker/browser·전체 backend/frontend suite는 실행하지 않았다.
whole goal은 active/incomplete다.

실제 native turn2026-10-28T13:06:58.297Z의 gpt-6.1-sol/xhigh를 관측했다.
원 LF SHA는 `cfb9344d80f802bdd9aa679cde36ca4c4d853bc2d86a024750b8fa0b5175347b`, 재귀 CLI0이다.
