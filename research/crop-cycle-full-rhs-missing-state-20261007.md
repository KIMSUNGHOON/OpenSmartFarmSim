# 원166일 실험의 세션·보존 상태 유실

2026-10-07 KST. 재개 시 실제 session81574 조회는 `Unknown process id 81574`를 반환했다.
현재 `/proc`에도 원 driver를 실행하는 Python이 없고 원 `/tmp` 실험 directory·checkpoint/terminal
receipt·로그·source map·사설 handoff가 존재하지 않았다. 별도 CI 수정 worktree의 임시 경로도 없지만
Git commit `e310e27581828a1a22a25148aa4e57d8805d9e2e`와 branch는 남아 있다.

**원 실험의 terminal exit·완료/hold/예산 종료 여부는 확인 불가다. 전체166일 수용은 보류한다.**
[시작 관측](artifacts/crop-cycle-full-rhs-started-reference-20261006.json)과
[확정 prefix 관측](artifacts/crop-cycle-result-prefix-read-cost-reference-20261006.json)은 과거 부분 증거로 유지한다.
과거 진행률·현재 시각이 deadline 뒤라는 사실·작은 결과의 통과로 terminal 성공을 추정하지 않는다.
이전 실험을 처음부터 재시작하거나 같은 manifest의 global budget을 재설정하지 않았다.

[현재 상태 관측 receipt](artifacts/crop-cycle-full-rhs-missing-state-20261007.json)의 SHA256은
`44fc831434cab8e5f50b0cba758c8581333e56951b737f06aa5966b3145f442a`다.
관측 당시 원49 source·profile2·runner/test2의53개 bytes를 versioned receipt들과 다시 대사했다.
원 spec SHA는 `9f0415126674a2ab1dd4ccd6fc216c27cdd8cfadf063735c3053d25bc1ee5df6`,
deadline은 `2026-10-06T12:45:32.620491+00:00`이며 변경하지 않았다.
현재 kernel boot ID/uptime과 경로 부재를 기록했다. 부재 원인·원 종료 시각을 증명하지는 않는다.

## 이어갈 수 있는 구현과 전체 수용 조건

보호할 원 프로세스의 부재를 확인했으므로 실행 중 source 동결은 끝났다. 별도 Git commit의
CI 시험 격리 수정을 정상 cherry-pick한 뒤 현재 bytes·집중 검증과 새 hosted CI를 확인한다.
원256MiB·6시간·격자/출력·CI timeout/workflow는 바꾸지 않는다. 실패한8fe CI는 그대로 보존한다.
운영 기반 `d19f7c0` 고정과 기존25시간 저장→3D 소프트웨어 수용 범위도 유지한다.

작은 실제 terminal 사례에서 결과 증명 → 별도 결과 조회 타입 → 현재 Farm/Scope/등록/권리와
실제 원 DB/custody trace 연결의 개발은 계속할 수 있다. 전체166일·복원/부하 부모는 체크하지 않는다.
전체 수용에는 원 실험의 복구 가능한 terminal/checkpoint/raw 결과와 모든 원 출력/수지·자원 증거,
현재 농장/API/같은 UTC3D의 실제 검증이 필요하다. 원 자료를 복구할 수 없다면 별도 설계·판본·
지속 저장 경로·고정 예산을 갖춘 새 실험의 증거가 필요하며 원 실험의 재개/성공으로 표시하지 않는다.

새 로그·관측·handoff는 Git 밖의 소유0700
`/home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-result-evidence-resume`에 보존한다.
현재 CLI `gpt-6.1-sol / xhigh` 문맥은 `2026-10-07T01:57:57.942Z`, 원 줄 SHA256
`2f2ce09f71ab416702b664816fc4ac532fba2f2a8e3c001241276dac216eae9a`다. 재귀 CLI0회.
권리 확인된 실제 품종 입력·국내 독립 검증 자료0건·G0–G4 not_assessed·예측/추천 보류를 유지한다.

## 보존 CI 수정의 현재 통합

후속 `4bf9af3ec502e10d790140dd7f83fa4a37d8f885`는 e310의 정상 cherry-pick이다.
현재18개/24.30초(session28492 종료0)·원10개 시험 본문/parameter marker와
나머지52개 source 보존·문서/새 primitive9 core hash를 확인했다.
[통합 receipt](artifacts/crop-cycle-full-rhs-test-isolation-integration-20261007.json)는 현재 집중 시험과
원 결함 재현의 과거 증거를 구분한다. 원 수식/자원 한도·workflow/timeout을 변경하지 않았다.
새 hosted 성공과 원166일 완료를 뜻하지 않는다. 검증된 커밋을 한 번의 정상 batch push로 전송한다.
