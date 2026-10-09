# 실제 웹 감사 실패의 단일 잠금 수정

상태: **로컬 수용·수정 판본 hosted CI 전**, 2026-10-06 KST.
`e9c2431`의 [불변 영수증](artifacts/source-map-js-audit-fix-reference-20261006.json)을 고정했다.
운영 기반 `d19f7c0`의 완료 범위는 유지한다. 실제 핵심 웹 CI 실패를 해소하는1개 잠금 보완이다.

`d61bcb3`의 [웹 CI37405273365/job112081328555](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37405273365/job/112081328555)는
첫 시도에서 typecheck/unit/build를 통과한 뒤 `npm audit --audit-level=high`에서 실패했다.
Chromium 설치/브라우저 시험은 실행되지 않았다. 테스트 오류나 사용자 자료 유출을 관측한 기록은 아니다.

공식 [advisory GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q)는
source-map-js1.0.0–1.2.1의 indexed-map offset에 의한 event-loop 서비스 거부와 수정판1.2.2를 명시한다.
9월18일 발행·10월5일 갱신을10월6일 확인했다.
공식 [1.2.2 릴리스](https://github.com/7rulnik/source-map-js/releases/tag/v1.2.2)는9월30일 발행됐으며
indexed-map 수정과 unsafe-eval을 허용하지 않는 브라우저 CSP의 crash 수정을 함께 포함한다.
전체 스택을 업데이트하지 않고 기존 Vite→PostCSS→source-map-js의 `^1.2.1` 범위를 사용했다.

`npm update source-map-js --package-lock-only --ignore-scripts --no-audit`로 생성한 잠금을 검토했다.
변경 package node는 **1개**이며 버전/공식 registry tarball/무결성만 바뀐다.
개발용 여부·BSD-3-Clause와 다른 모든 package node, 직접 의존성과 install script는 보존한다.
기존 정적 앱이 indexed source-map 입력 기능을 제공하는 것은 아니지만 빌드/개발 경로와
필수 CI 감사가 이 의존성을 사용하므로 수정판을 검증한다.

| 실제 로컬 검증 | 결과 |
| --- | --- |
| `npm ci --strict-peer-deps --ignore-scripts` | 종료0·script 실행0 |
| 전체 웹, 수정 전/후 | 각각503개 통과; 수정 후7.09초 |
| `npm run build` | 타입 검사 포함 종료0·Vite850ms |
| `npm audit --audit-level=high --json` | 종료0·알려진 취약점0개 |
| 기존 cycle client5개 source hash | 동일 |

기존500kB chunk 경고는 유지했다. 현재 실제 `gpt-6.1-sol / xhigh` CLI에서
공식 출처·잠금 diff와 결과를 검토했고 재귀 CLI0회다. 농업/경제 산식·G0–G4와
서비스/schema·작업자 한도 변경은 없다. 실패한 hosted 판본은 계속 미수용이며
수정된 SHA의 CI와 새 cycle 화면/실제 브라우저 수용은 후속이다.
