# 같은 실제 DB의 수확 표·생장 3D — 작은 통합 수용

2026-10-09 02:22 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[불변 영수증](artifacts/crop-harvest-view-native-reference-20261009.json)의 SHA는
`023dbe6c158461aa990b153cb8fb211d24030bcd825664a53eb8e260cb46dbf2`다.
원 도구69379의 **종료0·2통과·226.498초**, 828 source 보존과 소유 자원 정리를 감사했다.

## 확인할 산출물과 범위

[3 core 계약](../contracts/crop-harvest-view-native-v1.md),
[수동 native 시험](../backend/tests/crop_harvest_view_native_smoke.py),
[standalone 브라우저](../web/e2e/harvest-replay-native-smoke.mjs)를 추가했다.
기존 실제 SCRAM fixture의 동일120걸음 계산 부모·3sample·4event에서 생성·등록한 수확6행을
보호 loader/표준 ApiRuntime과 실제 빌드 App·Nginx·HTTPS로 조회했다.
원 metadata·시각·DB·HTTP 응답을 바꾸어 결속을 맞추지 않았다. 제품 코드·수식 변경은0개다.

[같은 DB의 실제 3D](artifacts/harvest-native-3d-desktop.png),
[수확 표](artifacts/harvest-native-table-desktop.png),
[모바일 표](artifacts/harvest-native-table-mobile.png)를 직접 확인했다.
1024×768 viewport의 3D와820×1085 수확 패널,390×844 viewport의366×1299 수확 패널이다.
모바일 표는 가로로 스크롤해 나머지 열을 읽는다. 모든 열이 한 viewport에 보인다는 수용은 아니다.
합성 가정의 연구 수치이며 실제 품종의 형상·숙기·생과 생산·판매량은 검증하지 않았다.

## 통과한 검증

| 대상 | 실제 수용 범위 |
| --- | --- |
| 원 저장 수량 | 원6행/UTC·질량/목적별 수량·단위·정확 분수·미배정과 전체 저장 합계·합성 비교/미평가 표시 |
| 같은 시점 3D | 저장3시점 각각의 실제 WebGL2·draw calls·50구획 C/N 원값과 단위·LAI 면적. 같은 UTC 버튼의 키보드 선택/3D focus |
| 대응 없는 사건 | 원90초 사건은 저장 sample이 없어 이동 비활성화. 가까운 시점으로 보간하지 않음 |
| 현재 권리/계정 | 표시권 철회 때 수확/부모 3D 제거, 원 권리 복원 뒤 새 조회. 실제 부족한 scope의 crop UI와 별도 harvest 직접 fetch가403 |
| 취소·늦은 응답 | 실제 서버 요청을 대기→클라이언트 취소/계정 변경→서버 해제. 이전 수확/부모 장면이 다시 나타나지 않음 |
| HTTP | 서버/클라이언트 각각13요청, 완료200응답9개의 bytes/SHA 동일. 별도 취소 fetch1개와 지연 서버 응답1개를 구분. 정상·오류/지연 서버의 원 본문 최대32,659bytes/22.717170초, 클라이언트 최대22.7219초 |
| 요청 순서 | 서버/클라이언트 active peak1. 기존30초/2MiB·no-store 유지 |
| 읽기 불변성 | 조회 중 RHS·질량/배정 행 생성·증명 발행·게시를 금지하고0회. 같은 DB의 jobs/결과/Run 개수·원 파일 bytes/mode/inode 보존 |
| 종료·정리 | 원 pytest2통과/225.90초·도구69379 종료0. FD identity·custody·서버 thread, PG/Nginx/Node/Chromium·schema/role/passfile·보호 파일·소유 temp 정리 |

harvest 계정 거부는 부모가 제거된 UI에서 SDK 조회를 만들 수 없어 명시적 실제 fetch로 확인했다.
이를 UI 버튼을 통한 SDK 조회로 표시하지 않는다. 지연 요청은 응답을 바꾸지 않고 서버 진입만 대기시켰다.
취소된 클라이언트는 `fetch-error`, 지연 서버는 해제 뒤 완료 응답으로 별도 기록했다.

새2개는 import 자원 부작용 검사1개와 실제 공동 DB/HTTPS/WebGL 통합1개다.
선행 화면의 Chromium10개/기존15개·웹851개·타입/빌드는 별도 수용 증거다.
이번 실행에서 다시 수행하거나 새2개에 합산하지 않았다.
현재 제품 빌드 입력97개와 dist 전체 파일 해시가 이전 종료0 빌드와 같음을 다시 검사해 재사용했다.
Nginx1.30.5의 공식 서명/실행 파일 해시와 실제 built index·upstream 인증서 검증도 유지했다.

## 실패와 자원 판단

원84186은 HTTP 문맥 없는 기대 값 준비에 API query를 사용해 실패했다.
기대 값은 기존 fixture의 명시적 권한 query로 준비하고 실제 HTTP의 current principal 검사는 유지했다.
원66585는 RSS 상한으로 중단됐다. 저장 canonical JSON과 API DTO의 키 순서가 달라 기존 문자열
단언이 틀린 것을 재현했다. 화면 JSON을 파싱해 모든 값/단위/분수를 deep 비교하도록 수정했다.
오류 기록을 캡처보다 먼저 남기고 실패 진단 캡처는 viewport로 제한했다.

원46908/18014도 정상 조회 구간의 RSS 상한으로 중단됐다. 원 pytest-15/도구241을 보존했으며,
자동 fixture teardown이 끝나지 않아 소유 PID/start identity를 확인한 PG만 명시적으로 종료하고
소유 temp/비밀번호 파일을 제거했다. 이 실행들을 정상 정리·통과 시험으로 기록하지 않았다.
사설 controller의 잘못된 계약/이전 helper 경로 사전 실패2개도 보존했으며 DB/브라우저는 시작하지 않았다.

Linux 시험 부모의 GC/glibc trim, 조회 사이 Chromium/Node GC와 전후 RSS/heap을 기록했다.
시험 Chromium의 `--in-process-gpu`는 GPU를 브라우저 thread에서 실행한다
([Chromium 공식 switch](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/public/common/content_switches.cc), 조회 blob은 영수증 참조).
메모리 감소는 이번 관측에서만 확인했다. 기본 분리 GPU process의 브라우저 운영 용량 수용은 아니다.
원93482는 원6행/3시점을 확인했지만 모바일 resize 직후의 즉시 너비 단언에서 실패했다.
기존 차트의 ResizeObserver/animation frame 조정을 기다리며 동일 가로 넘침 조건을 검사하도록 수정했다.
최종 원69379에서 그 조건과 나머지 권리/취소 경로가 통과했다.

최종0.1초 표본의 단일 프로세스 최대295,022,592bytes≤512MiB,
PG/controller·재부모화된 소유 자식 포함 고유 PID RSS 합 최대**1,030,803,456bytes≤1GiB**다.
nice19·원600초와 같은6행/3시점·모든 단언을 유지했다.
지정 heap/viewport/SwiftShader/GC/GPU thread의 시험 수용이며 표본 사이 최대치·PSS·WSL 전체나
일반 운영 브라우저의 동시 처리 용량은 수용하지 않는다. 성공 실행에는 사후 PG 강제 정리가 필요하지 않았다.

## 다음 한 단계와 남은 의존성

`crop-harvest-view-native`와 작은 `crop-harvest-view` 부모만 체크한다.
**전체166일 질량 부하와 `crop-harvest-replay` 부모는 미완료**다.
다음은 완료된 전체 작기의 원47,809 sample/5event를 재계산 없이 읽는
`crop-harvest-full-capacity`다. 원 hash/UTC/수량·leaf/stem 분리·미배정/정확 분수와
질량·배정 모든 파생 행을 대사하며 기존64행/2MiB page·512MiB artifact/파일 한도와 예약을 측정한다.
초과·수치 불가를 발견하면 해당 근거로 보류하며 행/출력·계수·상한을 바꾸어 통과시키지 않는다.
용량 대사는 실제 전체 writer/등록 DB/별도 Python 권한 복원/API/대표 WebGL 실행과 구분한다.

첫 작업 분해는 원 archive/reader·계보 확인0.5–1시간,
전체 행/단위·정확 수량과 용량 대사0.5–1시간, 집중 검증·감사/문서0.5–1시간이다.
기존 저장물과 reader를 재사용할 수 있다는 조건의 **1.5–3집중시간/10월9일 KST 잠정**이다.
그 관측 뒤 실제 전체 질량 부하의 실행 시간·저장 공간과 복원 조립 범위를 정한다.
이후 기후·물/양분·구매 에너지→사용자 실행→같은 배치/달력의 Decimal 경제를 연결한다.

실제 품종 계수/농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold는 유지한다.
외부 자료의 접근/이용권·독립 검증 일정이 없어 production 완료일은 확정하지 않았다.
원격 이전 판본2a3e615의4 workflow 성공/[Backend 실패](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958)를 읽기 전용으로 다시 확인했다.
최신 로컬의 전체 Backend·새 hosted CI/push·실제 제품 CLI/독립 해제는 이번 범위에서 수행하지 않았다.
구형25시간 원 명령 종료 유실 hold와 전체 활성 goal도 유지한다.
