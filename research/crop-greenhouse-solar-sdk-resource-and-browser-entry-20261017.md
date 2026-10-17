# 실제 SDK 자원 보류와 브라우저 연결 절차 수정 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-sdk-resource-and-browser-entry-20261017.json) ·
[저장 웹 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md).

## 현재 범위

S1a 저장 클라이언트 수용은 유지한다. **실제 SDK→현재 HTTPS(S1b)는 미수용**이다.
새 일사 화면·저장/계산 중3D·사용자 배포도 미완료다. 이번 실제 동시 시험은 세 번 모두
합 RSS 관문에서 중단했다. 데이터/모델·권리/타입·원본/기존 다섯 root와 한도를 바꾸지 않았다.
제품 API/작업자/계산/사용자 UI 코드는 이번에 변경하지 않았다.

후속 CI에서 확인한 기존 브라우저 시험의 연결 절차를 수정했다. `64217ec`는 진행 reporter만,
`f1aba2f5e1031aea841a10d2eecff1be7be2f968`는 시험 진입 helper·회귀 사례만 바꾼다.
새 helper의 전체 브라우저 수용은 아래 원격 실행의 실제 종료로 판단한다.

## S1b 실제 동시 시험과 제외한 후보

실제 SCRAM/독립 producer·fresh 현재 API/검증 TLS와 새 TypeScript SDK의 native fetch를
연결하는 전용 시험 후보를 준비했다. 원 값/단위/UTC·limit1 페이지·현재/직렬화 후 권리·
잘못된 계정/판본·취소/전송 정리·GET 계산/SQL 변경0을 대사하도록 구성했다.
입력은 기존 소유 합성16걸음 프로그램이며 fixture를 live 응답으로 바꾸는 fallback은 없다.
이 후보는 **전체 통과하지 못해 사설 증거에 보존하고 제품/공개 시험 경로에는 채택하지 않았다.**
정상 시험부터 중단되어 hold 경로의 SDK 동시 검증은 실행하지 않았다.

| 실제 시도 | 도구/guard 종료 | 시간 | 합 RSS 최대 bytes |
| --- | --- | --- | --- |
| pytest 부모+실제 API/SDK |21055:1|82.609초|1,101,926,400 |
| 같은 시험 본문·가벼운 부모 |60447:1|81.965초|1,079,422,976 |
| 부모를 API로 exec 교체 |47446:1|88.199초|1,086,345,216 |

후속 두 시도는 시험 준비의 GC/allocator trim을 사용했다. source pin으로 각 당시 시험 본문과
원 실행/로그를 구분했다. exec 후보는 RSS 중단 뒤 `runner_save` 미정의 정리 오류도 남겼다.
SQL 종료 후의 rollback/후속 단언 실패를 독립적인 클라이언트 정확성 판정으로 사용하지 않는다.
이들은 운영 조립 수정이나 native SDK 수용이 아니며 정상 결과/페이지·모든 철회·취소의 통과를
주장하지 않는다. 새 합성 source/모델/계수를 채택하지 않았다.

제한된 별도 Node 메모리 진단(`47846:0`)은 예약한 비수신 loopback 포트의 연결 실패만 사용했다.
실제 API나 성공 응답 시험이 아니다. 기본/size 최적화/32MiB heap+size 최적화의 RSS는
61,284,352/61,374,464/61,140,992bytes였다. heap 사용은 약8.3MB로, 설정 변경의 관측 차이는
실제 초과량을 해결할 근거가 못 됐다. 앞선 두 진단 실패와 `--jitless`의 native fetch
`WebAssembly is not defined` 오류를 별도로 보존했고 해당 flag를 채택하지 않았다.
근거 없는 같은 동시 시험/heap 조정을 추가로 반복하지 않는다.

[Node22.22.3의 추가 CA 계약](https://nodejs.org/download/release/v22.22.3/docs/api/cli.html#node_extra_ca_certsfile)에
따라 소유 PEM은 Node 시작 시 지정했다. TLS 검증을 끄지 않았고 자격 파일은 저장소/공개 로그에
넣지 않았다. 이 문서 링크는 소프트웨어 전송 근거이며 농업 자료의 채택/권리를 뜻하지 않는다.

## CI의 실제 원인과 작은 수정

[39005600656](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39005600656)은
d82861f의 타입/단위/build/audit 성공 뒤 브라우저 단계에서 job15분 제한으로 취소됐다.
annotation의 원문은 `The job has exceeded the maximum execution time of 15m0s`다.
브라우저227개 시작 뒤 개별 진행이 없어서, 같은 제한/단일 worker/검사 집합에
[공식 line reporter](https://playwright.dev/docs/test-reporters#line-reporter)만 명시했다.

[39006683801](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39006683801)의
64217ec도 타입/단위/build/audit 성공·브라우저15분 취소다. 이번에는 첫25개 시험이
`getByLabel('접근 토큰').fill()`에서 보이지 않는 입력을 기다리는 것을 확인했다.
현재 App은 연결 전 `open={!api}`로 폼을 열지만 이 시험들은 summary를 무조건 눌러
폼을 닫았다. 첫 assessment의30초 timeout부터 계산 재생의90초 timeout까지 같은 진입 실패다.
테스트/브라우저 시작 자체가 멈췄거나 제품 계산이 느렸다고 해석하지 않는다.

공통 `connection-fixture.ts`는 닫혔을 때만 실제 summary를 누르고 입력 표시를 기다린다.
20개 시험 파일의28곳만 교체했고 기존 기대값·요청·의도적 닫기·이미 조건부인 경로는 보존했다.
변경 전 commit/변경 후 파일을 원문 역치환하여 그 외 byte가 같음을 확인했다.
추가1개 회귀는 처음 열린 폼 유지·사용자가 닫은 폼 재열기·입력 초안 보존을 확인한다.
입력 폼의 사용자 동작이나 제품 초기 상태를 시험에 맞춰 바꾸지 않았다.

로컬 수집 `28843:0`은 **228개/25파일**이며 실제 통과 개수가 아니다. 원227개는 모두 남았다.
초기 수집의96MiB heap 부족은160MiB로 구분해 기록했다. 로컬 첫 브라우저 시도의 grep 실패,
그 뒤 CLI RSS 중단·단일 실행기의 모듈 경로 실패/추가 RSS 중단은 검증 수에 더하지 않는다.
로컬 Chromium의 실제 열린/닫힌 동작 수용을 주장하지 않는다.

[후속39008217480](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39008217480)는
f1aba2f의 타입/단위/build/audit를 통과했고 브라우저 단계는 현재 진행 중이다.
Backend/Compose·전체 저장소 CI와 WSL 동시 운영 용량은 별도 미수용이다.

## 보존·다음 구현·외부 의존성

모든 로컬 종료에서 원본2,148항목·기존 source/assets·필수5root/동적 자식·FD4→4와
소유 비좀비/PG/임시 PG/passfile0을 확인했다. 마지막 inventory의 단일203,624,448/
합1,013,129,216bytes는512MiB/PID/1GiB 안이다.0.25초 표본이며 원자 RSS 관측은 아니다.
기존 사용자 서비스/키를 재기동하거나 원본을 수정하지 않았다.

진행 기록을15:04:21KST로 게시했다. 실제87697:0에서5173/5174의HTTP200/no-store·
동일 feed bytes·기존 HTML/환기 source2,173파일 보존을 확인했다. 이 게시 확인은 HTTP
범위이며 현재 기록의 DOM/WebGL 수용을 추가하지 않는다.

S1b의 동시 자원 보류가 저장 화면 **개발**까지 막을 이유는 없다. 수용된 S1a/원 응답으로
S2a의 별도 Solar 화면·선택 연결/기록 회귀를 진행하되, 실제 HTTPS/WebGL 수용 S2b에는
S1b를 계속 요구한다. 같은 원 UTC/수치/단위·50구획/장부/PAR/NIR·관리/보류와 거부 시 제거를
증명해야 하며 fixture fallback·임의 생장 애니메이션·사용자 적용 수용을 추가하지 않는다.
S2 부모와 S3/S4의 독립 unpaused/현재 권리/자원·재접속/재시작 조건은 유지한다.

native CLI `gpt-6.1-sol`/`xhigh`의 실제 context를 기록했고 재귀 CLI는0이다.
실제 농장 Run0·G0–G4 `not_assessed`·승인False다. 지역/품종/시설·독립 농장·미래 작기/시장
자료의 확보/권리와 검증은 병행한다. 이번 구현/진단 시간과 fixture CPU 시간은 서로 다르며,
S2a의 디자인·core 파일 경계를 고정한 뒤 잔여 작업량을 갱신한다. 전체 완료일은 미정·goal active다.
