# 새 잎 작업의 접수·멱등성과 commit 검증 — 2026-10-23

상태: [E1 계약](../contracts/crop-leaf-population-execution-v1.md)의 **합성 소프트웨어 수용**.
[현재 서명 결과](crop-leaf-population-signed-artifact-20261023.md) 다음의 접수 단계다.
새 leaf worker/게시·현재 query·보호 HTTP/runtime/제품3D 연결은 남는다.

## 구현

`LeafPopulationExecutionService`는 정확한 leaf authority와 판본 고정 trusted resolver를 받는다.
현재 farm·완료 parent job/result/root·원 leaf 입력/현재 검토와 양쪽 권리를 확인한다.
원 binding만 leaf private store에 보관하고 기존 simulation jobs 표에 참조 입력을 접수한다.
입력은2,509bytes, binding은32,605bytes였다. 원 program/source/evidence와 키는 job input에 넣지 않는다.
별도 version/domain의 intent HMAC은 원 요청/parent·binding/authority/code·resolver 판본을 결속한다.

동일 study/revision의 원 요청은 같은 queued job을 반환하고 다른 내용은 충돌로 거부한다.
기존 JobStore의 commit_guard가 현재 원본·권한/검토·binding을 다시 확인한다.
실패하면 job/event 삽입을 롤백하며 남은 private binding 객체를 결과로 게시하지 않는다.
접수는 수치 producer나 CLI를 실행하지 않고, 이전 모델·수치/서명·DB 스키마/역할도 변경하지 않는다.

## 통과한 검증

- **집중12:** intent의 원 요청/parent·binding/코드·issuer/key ID/resolver 판본,
  서명/타 계열 판본·닫힌 필드·정규 바이트/64KiB 상한과 다른 키 거부.
  먼저 모듈 부재의 RED를 확인하고 구현 후12개를 통과했다.
- **실제 SCRAM 정상1:** 별도 더 늦은 판단의 farm/실제 완료 parent 아래 동일 접수 두 번이
  **queued job1 + submitted event1**, attempt/publication 추가0이었다.
  원 binding/3개 입력 bytes·parent를 대사하고 simulation_create 없이 현재 read가 가능함을 확인했다.
  변경된 rights revision은 충돌, 현재 검토 철회 뒤 재접수는 이전 job 반환 없이 보류했다.
  새 job/event를 제외한 **25개 표의 모든 원 행 SHA**와 부모18파일의 bytes/metadata를 보존했다.
- **실제 SCRAM 변경 거부1:** foreign tenant·양쪽 현재 권리/검토와 세 원 입력 bytes 변경을 거부했다.
  INSERT 뒤 commit_guard 직전에 create scope, leaf/parent 검토, leaf/parent 권리, 원 program을
  바꾼 **6경우** 모두 rollback되어 **25개 표 원 행 SHA/건수**가 전후 같았다.
  부모18파일을 보존했고 남은 private binding1파일은 미게시 상태다.

두 native 시험 모두 **49개 생장/producer/CLI 진입의 호출0**, 소유 schema/role0과
짧은 임시 디렉터리 제거를 확인했다. 사용자 DB가 아닌 소유 scratch PostgreSQL을 사용했다.
검증 당시 source와 이전 signed 자식의 생산/시험 source는 그대로였다.
이번 수용은12+2=**14개**이며 이전 검사를 중복 합산하지 않는다.
별도 fresh admission·전체 backend 회귀/hosted CI·HTTP/브라우저 검사는 이번 범위에 없다.

## 자원과 응답 시간

정상 native114.413초/442samples·합 peak377,290,752bytes,
변경 거부137.100초/529samples·378,376,192bytes였다.
.25초 표본·PID512MiB/합1GiB·600초 안에서 원2root/2,148항목과 관련 저장 파일을 보존했다.
소유 child 잔여0·guard FD4→4이며 Windows Chrome과 공통 WSL 용량 수용은 포함하지 않는다.

단일 내부 관측은 최초 submit26.60초, 동일 재접수26.24초, 현재 입력 read12.70초다.
이는 이후 worker/HTTP30초·polling 조립의 시간 예산 검토 근거다. HTTP/U1 성능 수용으로 표시하지 않는다.
원 숫자·코드 SHA/로그 해시/각 단계 자원과 정확 native gpt-6.1-sol/xhigh·재귀0은
[기계 증거](artifacts/crop-leaf-population-execution-admission-20261023.json)에 기록했다.

## 다음 단계와 사용자 확인 범위

다음 **E2**는 해당 tenant/leaf input_version만 claim하는 worker와 작은 opaque 결과 참조다.
실제 signed producer1회 뒤 원 result/root·parent·최초 계산 시각을 대사하고,
같은 DB 거래에서 publication/outcome/events·terminal을 게시해야 한다.
계산은 job 잠금 밖에서 수행하며 다른 queued 모델 보존, 취소/임대 만료/늦은 권리 철회 때
참조 게시0·정리/원 결과 보존이 수용 기준이다. E3 현재 조회 뒤 보호 API/runtime·같은 작업3D를 잇는다.

E1의 이전3.5–6.5h 계획은 이번 실제 수용으로 대체한다.
E2의 구현/원자 게시 검토45–90분 + 실제 DB 정상/취소/임대·변경45–90분 + 기록15–30분 =
**1.75–3.5집중시간**의 낮은 신뢰 작업량이다. 기존 worker/JobStore 재사용이 전제이며
새 중첩 query가 임대/요청 예산을 넘으면 실제 검사 뒤 갱신한다. 제품 통합 완료 날짜가 아니다.

[현재 사용자3D](http://localhost:5176/leaf-population-replay.html)는 기존 저장 합성3→6잎 재생이다.
이번 접수 모듈은 사용자 runtime에 미배포이며 새 leaf 자동 계산/작물 예측을 보여준다고 표시하지 않는다.
실제 Axiany 계수/초기관측·독립 현장 작기0, 생산·자원/경제·자율 선정·최종 사실감/첫 셰이더 경고,
G0–G4 및 전체 제품 완료 날짜 미정을 유지한다.

사용자의 `/goal clear` 완료 회신 뒤 이번 실제 도구도 이전 목표 active와 unfinished goal 거부를 반환했다.
교체 성공이나 전체 완료로 표시하지 않고 재입력을 반복 요청하지 않는다. 현재 위임된 구현을 계속한다.
