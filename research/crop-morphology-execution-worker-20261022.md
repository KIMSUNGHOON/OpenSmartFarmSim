# 형태 실행 E2 worker 수용 — 2026-10-22

[실행 계약](../contracts/crop-morphology-execution-v1.md)의 E2를 소프트웨어 연구 범위로 수용했다.
[기계 증거](artifacts/crop-morphology-execution-worker-20261022.json)에 원 코드 지문/결과와 자원·정리를 기록했다.
공통 JobStore·runtime_roles/수치·입력·서명 코드는 변경하지 않았다. 작은 immutable opaque 참조를 기존 job_publications에 넣는다.

참조 제어9검사와 실제 PostgreSQL16.15/SCRAM5그룹이 통과했다. 실제 producer1회로 원12시점의 root를 만들고
publication/결과 사건/outcome/terminal state를 같은 거래에서 게시했다. 완료된 동일 접수/worker 재시도는 계산0이며
다른 모델의 queued simulation은 보존했다. 계산 시작은 deterministic 사건에 기록하고 가짜 CLI invocation을 만들지 않았다.

사전 자료 권리 철회는 계산0/hold였다. 실제 계산 직후 독립 DB 연결의 취소, 임대 만료와 publication INSERT 뒤의
늦은 권리 철회는 publication/결과 사건/succeeded 사건0이었다. 마지막 경우 provisional 행/outcome도 rollback했다.
private signed artifact가 남아도 완료 job 참조가 없으며 제품 공개 결과가 아니다. 원 농장 Run/수확 결과 등록0이다.

첫 native 정상 경로는 진행 사건의 `outputs` 오기 때문에 queued로 끝났다. 원 필드 `output_times`로 수정했다.
수정 후2그룹을 통과했고, 참조 source 고정 검사를 보완한 최종 source로5그룹과 참조9검사를 통과했다.
중간 fences 실행1건은 guardian 인수 전달 오류로 pytest 시작 전에 종료했으며 최종 전체5검사로 대체했다.

최종 native95.014060초/345표본·WSL 합994,734,080bytes/PID124,948,480bytes,
원3,160지문/2,148항목·6root·FD4→4·schema/role/PG/temp/passfile0을 확인했다.
.25초/512MiB·합1GiB/600초·로그4MiB를 유지했고 기존 사용자 화면/DB는 변경하지 않았다.
기존 수용653/E1은 코드가 같아 광범위 재실행하지 않았다. 전체 회귀·G0–G4/실제 품종·농장 검증은 수용하지 않았다.

다음은 E3 계산 없는 현재 query/독립 프로세스·보호 HTTP와 제품 화면이다. 실제 품종 계수/초기 개체/독립 측정 확보는0이다.
판단 CLI: native `gpt-6.1-sol / xhigh`, context20:20:28.168Z/LF SHA
`88b892130bd446bdbc3a4d06d7ba58ff7736eb679dd4856efa30c9fad5feb47a`, 재귀0.
