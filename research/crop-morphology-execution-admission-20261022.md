# 형태 실행 E1 접수 수용 — 2026-10-22

[실행 계약](../contracts/crop-morphology-execution-v1.md)의 **E1만** 수용했다.
[증거](artifacts/crop-morphology-execution-admission-20261022.json)에 원 지문·DB/철회·0계산과 자원을 기록한다.
기존 simulation/jobs와 commit_guard를 재사용하고 JobStore/runtime_roles·수치/서명/입력 코드를 변경하지 않았다.

원 binding41,256bytes는 기존 private blob에, 닫힌 요청/참조·별도 intent HMAC는2,269bytes job input에 보관했다.
키/원 program/source/evidence를 job input·공개 상태에 넣지 않았다. 같은 study/revision의 동일 요청은 같은1행이고
다른 권리 판본은 충돌로 거부했다. SourceResolver·현재 farm/자료 권리/판단/서명 code를 전후 확인한다.

새 제어11검사와 실제 SCRAM2그룹을 통과했다. 기존653검사는 관련 코드가 같아 반복하지 않았다.
첫 native 검사는 공개 submit 응답에서 private input_bytes를 기대한 시험 오류로 실패했다.
실제 저장된 authenticated input을 별도로 읽도록 고쳤고 두 그룹이 같은 최종 code로 통과했다.
foreign/current 권리·review·원 bytes 변조와 commit 직전 simulation_create 철회는 거부/롤백했다.
jobs/events만88→89로 각각1증가하고 attempt/outcome/publication·작물 결과/Run은0이다. 생장/CLI26진입점0이다.

최종 native31.307117초/115표본·PID124,948,480bytes/WSL 합967,372,800bytes,
원3,154지문/2,148항목·6root·FD4→4·임시 schema/role/PG/temp/passfile0을 확인했다.
.25초/512MiB·합1GiB/600초·로그4MiB를 유지했다. 사용자 화면/DB는 변경하지 않았다.

다음은 E2 해당 input_version의 worker·실제 producer/lease/cancel·원자 완료 참조,
E3 현재 query와 보호 API/제품 UI다. G0–G4·실제 품종/독립 자료/전체 작기·자원/경제는 남는다.
검토 CLI: native `gpt-6.1-sol / xhigh`, context18:31:18.690Z/LF SHA
`b3c3ff5325fb029473061d116799c0f1468b096986e70ad8118f6979b5607ff9`, 재귀0.
