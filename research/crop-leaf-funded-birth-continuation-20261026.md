# 새 잎 조달 뒤 원 시계로 계산 재개 — 2026-10-26 KST

**수용: 명시 새 구조 성장의 합성 재개.** [계약](../contracts/crop-leaf-funded-birth-continuation-v1.md)에 따라
원 현재 CP에 새 잎 Ci/성장호흡 비용·유입 현열을 반영한 뒤 실제 공동 RK4를 이어간다.
여러 시점/같은 시각의 추가 출현도 사건 이력에 결속하고 기존 ID의 재차 차감을 거부한다.
원 시계·기존 Ci/a/A/D0·과실/공기·이전 prefix/누적량과 점 장부를 보존했다.
[JSON 증거](artifacts/crop-leaf-funded-birth-continuation-20261026.json)와
[원60시점/258잎의 짧은 합성 경과초 CSV](artifacts/crop-leaf-funded-birth-continuation-20261026.csv).
기존 화면에는 이 새 출현 결과가 아직 연결되지 않았다.

## 검증과 범위

- **신규153검사**: 원6조건/초기·중간·끝 조달, 모든4걸음 composition48개와
  2회 출현/두 구간 분할24개에서 동일 sample·장부/최종 CP bytes를 확인했다.
  기존1→2잎/최대512잎·고갈/성공/완료·2MiB/1MiB/scalar/격자 경계,
  닫힌 current/frozen 입력·단위/타입·hash/정책/코드/profile·원 clock/장부,
  같은 시각 phase/순서·중복 사건·부분 stage/원 source 변경 때 마지막 확정 prefix를 검증했다.
- **기존 조달점74회귀**: 계산 본문을 검증된 현재 상태용 내부 경계로 추출했다.
  public API/계수·산술은 유지했다. 별도 원36조건에서 **code_sha256/calculation_sha256 이외
  모든 필드가 이전 불변 산출물과 같았다.** 과거 증거는 ec105a6e의 코드 지문을 유지한다.
- **fresh producer/reader**: 최종 source로24문맥/18실제 구간/60시점을 생성했다.
  별도 native reader는 root12개를 최초1회씩 준비하고 문맥24개를 RHS/점 재실행0으로 복원했다.
  각 현재 CP만 RHS1회로 검사해 원 bytes를 보존했다. 조달점 채택은 현재1+새 목록1회,
  시간 전진은 현재 검증1+새 걸음당4stage임을 계측했다.
- **독립 Decimal110**: app import0인 기존 독립 식에서 실제 RK4를 다시 계산했다.
  상태7,194수량·segment 적분810수량, 독립 전역/잎별372장부와 prefix60개를 대사했다.
  모델 수량의 기존64ulp/step 예산 중 최대 사용비는 약0.0322였다. 실제 작물 오차율이 아니다.

원 buffer/잎과 같은 floor의 CH2O 단위를 유지한다. 누적 연속량은 이전 prefix와 현재 segment를
보관하고 lifetime을 1회 합으로 파생한다. 조달된 구조 C는 내부 전이이며 광합성으로 추가하지 않는다.
전역 C에는 점 성장호흡 유출을, canopy/reduced 현열과 용량에는 점 유입을 각각 반영한다.
잎별 나이/C는 각 출현 시점의 기준과 공기온도 누적량에서 검사한다. 원 A를 curve에 재맞추지 않는다.
입력/변조 오류는 typed hold이고 부분 단계 실패는 원 확정 상태·장부/CP=None을 유지한다.
frozen context의 단위/leaf 선언을 검사하면서 과거 생장식/초기 면적을 재계산하지 않는다.

최종 unit153 단계는100.390초/PID115,085,312/WSL 소유+보호 합계168,779,776byte다.
512MiB/PID·1GiB 합계/0.25초·600초·로그4MiB 상한을 유지했고 원4500항목·보호2root/
source 보존·잔여 소유0/FD4→4를 확인했다. Windows 프로세스 RSS는 측정 밖이다.
최종 fresh bundle1,822,635byte/SHA36bb47c6e80859e04225450b895c6344f962c1c134bfdad8d25744dcf8cd29da.
검증을 추가한 이유는 최저/최대 목록과 동결 선언의 단위 경계였고 수치식/합격 예산은 완화하지 않았다.
전체 backend/UI suite·새 hosted CI 통과는 주장하지 않는다. 변경되지 않은 이전297회귀는 반복하지 않았다.

## 판단 근거와 다음 단계

이번 구조 판단/구현은 이미 실행 중인 **Codex CLI gpt-6.1-sol / xhigh**에서 수행했다.
turn_context2026-10-25T23:44:49.382Z, raw LF SHA
`9860923b3b32f4d1d8bfc8b31e7aa46bb14c3c4b323138e37a751d8c0886925b`;
관측2026-10-25T23:45:14.479553Z, 재귀 CLI0. 출력은 본 계약/코드/검증이다.
이전 [원문·자료 권리/가정](crop-leaf-funded-births-design-20261026.md)을 유지했고
새 계수/자료/실제 측정 채택0이다. 버전은 source/정책/profile/원 root와 불변 해시로 결속한다.
snapshot/CP의 expected SHA는 외부 신뢰 저장이 공급해야 하며 자기 계산 hash는 권한 증명이 아니다.

다음은 이 실제 출현 전후/적분 결과의 **불변 저장·무계산 reader**다.
원 context/CP/point 이력·정확 시각/phase/가변 ID·current/전역/점 장부와 권리/notice를 보존하고
새 프로세스 조회의 모델 import/계산·DB/CLI/network·쓰기0, 변조/부분 실패/512경계를 검증한다.
자체 합성 저장 개발과 원 시계/줄기 attachment·초기 질량 출처 결속/독립 자료 확보를 병행한다.
SDK/같은 상태의 실제 새 잎3D는 이 저장과 부착 근거 뒤에 연결한다.

현재 모델은 양의 수관/명시 조달의 합성 가정이며 실제 출현 법칙/공급 제한 A·빈 수관/동시 제거는 후속이다.
실제 품종·독립 농장/작기0·생산량/자원·구매량/경제·거시/수급/자율 비교·제품 통합과
G0–G4/R2·전체 완료일은 미완료/미정이다. 기존 표시 창·주앱 전체 build/WSL 보류도 유지한다.
