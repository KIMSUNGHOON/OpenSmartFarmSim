# 현재 HTTPS→저장 WebGL 검증과 로컬 용량 보류 — 2026-10-17

[기계 기록](artifacts/crop-solar-current-webgl-verification-20261017.json) ·
[수용 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md).

## 현재 범위

S1a/S1b/S2a는 기존 수용을 유지한다. **S2b·S2 부모·S3·S4는 미완료이며 새 Solar는 미배포다.**
현재 보호 서비스와 전체 앱의 로컬 동시 실행이 합 RSS 한도를 넘었다.
새 호스팅 실제 검증은 실행 중이며 성공으로 세지 않는다.
실제 농장 Run0/G0–G4 미평가/승인False·전체 goal active다.

## 통과한 전체 웹 회귀와 검증 빌드

`28e7a28`의 [전체 웹 CI39020017901](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39020017901)는
타입·단위1,864개/35파일·브라우저243개·빌드·audit를 통과했다.
이 브라우저 회귀는 기록 응답을 사용하며 실제 현재 API 수용을 대신하지 않는다.
새8줄 artifact 단계로 성공한 빌드를 보존했다. artifact12096407087의 ZIP5,859,385bytes와
SHA-256 `df95479f320664c1c4e348b259f888a74d6c638a2ffb0798bf554022c63789ff`,
184파일·경로/중복/심볼릭 링크·Solar chunk와 원 웹 소스 일치를 확인했다.
오래된 로컬 dist로 새 Solar 검증을 시도하지 않았다.

## 로컬 실제 시도와 분리 계측

| 단계 | 실제 결과 | 시간 | 합 RSS 최고 bytes |
| --- | --- | ---: | ---: |
| 새 로컬 Vite 빌드 | RSS 중단, 미수용 |1.189초|1,094,057,984|
| 실제 정상 브라우저 v1 | 실행 보조 코드의 mode 인자 누락, 화면 이전 실패 |74.361초|1,053,462,528|
| 실제 정상 브라우저 v2 | Chromium 시작에서 RSS 중단, 미수용 |75.906초|1,088,266,240|
| 브라우저만 분리 v1 | 제어 선택자 치환이 `Node.TEXT_NODE`와 충돌, 실패 |1.112초|980,869,120|
| 브라우저만 분리 v2 | 앱 초기 화면 이후 RSS 중단, 미수용 |0.904초|1,111,031,808|

모든 시도는 원5root/동적 자식과 소유 시험 주체를 함께 계수했다.
512MiB/PID·합1GiB·nominal0.25초와 원 identity/pidfd 정리를 유지했다.
각 종료의 FD4→4·소유 비좀비/PG/임시 PG/passfile0·원2,148항목/기존 source·자산/두 UI를 확인했다.
브라우저 v2의 합 최고에서 Chrome140,173,312bytes를 관측했다. API가 없는 분리 v2에서도
실제 앱을 연 뒤 Chrome277,032,960bytes였다. 이 두 관측을 일반적인 Chrome 상한으로 해석하지 않는다.

보조 코드의 두 결함을 수정하고, 실제 stderr의 쓰기 가능한 font cache 부재에 따라
새 소유 프로필에만 `XDG_CACHE_HOME`을 지정했다. 분리 v1에서 보존한 stderr에는 그 font cache
오류가 없었으나 분리 v2의 자원 수용으로 이어지지 않았다. heap/flags 반복 조절·한도 상향·기존 서비스
종료·응답 mock이나 정적 애니메이션으로 실패를 대체하지 않았다.
원 guard/signal helper의 hash는 보존했다. 로컬 실제 저장 WebGL을 확인한 시점은 아직0개다.

## 재현 가능한 실제 호스팅 검증

core `dee52e5`, CI 문맥 수정 `3dd211c`에 네 파일을 추가/수정했다.

- [실제 브라우저 참조](crop-greenhouse-solar-browser-read.py): 기존 native producer와 현재 API의
  원 응답을 사용한다. 정적 파일 서버는 실제 HTTPS API에 인증 헤더와 요청을 전달하며, 성공
  원문 bytes를 대사한 뒤 그대로 반환한다. fixture 응답/fetch mock/새 생장 계산은 없다.
- [소유 실행기](../backend/tests/web_crop_greenhouse_solar_smoke.py): 같은 SCRAM DB의 별도
  producer/reader·현재 공유 reader·정상/hold를 순서대로 실행한다. 기존 소유 helper로
  시험 주체의 RSS·벽시계·identity/pidfd 정리와 FD를 검사한다.
- [기존 CDP 실행 보조](crop-isolated-ventilation-pipe-reference.py): 명시된 소유 인증서의
  SHA-256 SPKI pin을 선택적으로 전달한다. 기존 호출의 기본 flags는 같다.
- [웹 workflow](../.github/workflows/web-tests.yml): 명시 `native_solar` 선택 시 선행 웹 검증 빌드의
  digest를 검사하고 실제 저장 결과→WebGL 정상/hold를 실행한다. 자격 증명·원 fixture·passfile·
  private stderr를 artifact로 올리지 않는다.

원 UTC/값/단위·참조·50구획/실제 mesh·온도 marker·그래프·41/6장부·수지·PAR/NIR·관리 전후,
현재 권리 철회 시 장면 제거·복원·재접속, 조회의 작물/CLI13진입점·SQL 변경0을 검사한다.
경제 참조의 현재 재검증 산술을 생략하거나 모든 산술이0이라고 주장하지 않는다.
브라우저는 소유 SPKI pin을 사용하고 API 전달 구간은 CA/호스트명/시각을 검증한다.
일반 공개 브라우저 인증서 배포 수용은 아니다.

로컬 Python3조각·workflow shell6블록/내장 Python 구문 검사를 통과했다.
최초 구문 검사 실행기의 YAML 들여쓰기 추출 실패를 보존했고 그 실행기만 수정했다.
첫 workflow39021667248은 job env의 허용되지 않은 `runner` 문맥 때문에 **시험 전에** 거부됐다.
`github.run_id` 기반의 소유 경로로 수정했고
[첫39021689429](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39021689429)는 아래 입력 진입 실패로 종료됐다.
이 run은 선택 웹 범위 `solar`이며 앞선 전체243개 회귀와 구별한다.
기존 Backend6004735의39018578815/이전39015742702는 중단하지 않았고 성공으로 세지 않는다.

첫 호스팅 run의 웹38브라우저/1,864단위·빌드/audit는 통과했다. 실제 정상 사례는128.765초에
소유 자식 exit1, reason없음·단일248,606,720/합436,654,080bytes·FD7→7·소유 잔여0이었다.
`저장 결과 판본` 제어가 나오지 않았고 연결 상태가 미설정이었다. **실제 API 요청0/저장3D0이며
hold 사례와 DB 역할 정리 단언은 실행하지 않았다.** PNG도 없다. 자원 한도 통과가 기능 수용은 아니다.
원 artifact12096663099의 digest와 안전한 경로를 확인해 진단을 보존했다.

`0920f70`은 소유 입력 제어에 font 준비 대기·명시 즉시 스크롤/실제 클릭 적중·포커스 진단·연결
상태 전환 단언을 추가했다. 제품 코드는 바꾸지 않았고 클릭이 적용되지 않은 원인은 아직 미확정이다.
구문 검사 시 새 진행 JSON까지 불변 웹으로 간주한 실행기의 단언 실패를 보존했다. 해당 JSON의
차이만 명시해 검사했고 Python/내장 script·원 helper·웹 앱 소스 보존 검사를 통과했다.
두 번째 [39022453909](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39022453909)도
미수용이다.66.626초·자식 exit1/reason없음·단일211,652,608/합400,105,472bytes·FD7→7·소유
잔여0이었다. 연결 설정은 실제로 성공했으나 다음 탐색 버튼의 중심y829.4375가 viewport768 밖이었다.
원 native 좌표/적중/포커스가 이를 보이며 실제 API 요청/프레임은0, hold/DB 역할 정리 단언은 미실행이다.
`ca9f9cf`는 scroll 다음 프레임에서 화면 안의 실제 적중 영역이 생길 때까지 대기한다.
원 값/권리/페이지/정리 단언과 timeout은 유지했다. 제품 CSS/동작을 수정하거나 DOM click으로
대체하지 않았다. 구문·원 source/5root·FD/소유 정리를 확인했고
[현재39023069641](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39023069641)를
따라간다. 이전 두 실패를 성공이나 동일 source의 무조건 재실행으로 처리하지 않는다.

호스팅 시험 성공은 해당 환경의 실제 기능 증거로만 추가한다. **현재 WSL5root와의 동시 용량
보류와 S2b/S3/S4의 기존 조건은 해제하지 않는다.** 로컬 동일 실패를 새 근거 없이 반복하지 않는다.

## 다음 순서와 일정

1. 같은 호스팅 run의 정상/hold 원 응답·실제 프레임/PNG·권리/재접속·최종 종료/정리를 대사한다.
2. 로컬 전체 앱의 관측 용량 문제를 별도로 좁힌다. 기존 보호 서비스·한도와 원 검증을 유지한다.
3. S3의 독립 unpaused 정상/hold/취소·전진 prefix와 동시 자원 → 계산 중3D → S4 사용자 적용 순서다.
4. CO₂/기공·시설 유량·물/양분·구매 에너지·생산/경제·최종 UI/실제 자료의 기존 작업을 유지한다.

전체 회귀의 브라우저 단계는 실제10.8분이었다. 로컬 위 시도 시간은 구현·조사·CI 대기와
구별한다. 새 호스팅 실행의 실제 비용과 아직 보류인 동시 실행/외부 자료를 확보하기 전에는
전체 완료 날짜·남은 집중시간을 확정하지 않는다. 독립 지역/시설/품종·농장 계량과 미래
생산/판매/정산/비용·시장 자료의 권리/검증은 병행할 외부 의존성이다.

native Codex gpt-6.1-sol/xhigh의 현재 context/hash를 기계 기록에 남겼다. 재귀 CLI·다른 모델/
하위 에이전트는 사용하지 않았다. 농업·경제 입력 자료의 새로운 채택이나 관문 승인은0이다.
시험 PG16.15의 [공식 checksum](https://ftp.postgresql.org/pub/source/v16.15/postgresql-16.15.tar.bz2.sha256)과
[공식 빌드 절차](https://www.postgresql.org/docs/16/install-make.html),
고정 Playwright1.63.0의 [headless shell 설치 방법](https://playwright.dev/docs/browsers#chromium-headless-shell)을
확인했다. 제품 스택의 PostgreSQL18.6을 바꾼 것이 아니다.

진행 feed를 `2026-10-17T09:39:28.844543Z`로 게시했다. parser28개와 실제 두 UI의
200/no-store·새 원문 일치/기존 HTML·환기2,173파일 보존을 통과했다. 새 DOM/WebGL 수용을
이 게시 확인으로 대신하지 않았다.

두 호스팅 진입 실패와 새 visible-pointer source를 반영해 feed를
`2026-10-17T09:58:41.767632Z`로 다시 게시했다. parser28개·양쪽 실제 HTTP200/no-store/원문·
기존 HTML/환기2,173파일 보존과 원5root/원본/FD4→4·소유 정리를 통과했다.

## 조회 폼 준비 순서 보완

세 번째 [39023069641](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39023069641)는
129.316초·자식 exit1/reason없음·단일262,729,728/합451,080,192bytes·FD7→7·소유 잔여0으로
종료됐다. 연결/탐색 버튼과 Solar 선택까지 실제 입력이 진행됐지만 첫 조회 필드의 hit가 다른
문단이었다. API 요청/3D 프레임0이며 hold/DB 역할 정리 단언은 미실행이다.

lazy Solar 화면이 마운트되기 전의 `undefined`를 닫힌 details로 간주할 수 있는 코드와
원 summary 클릭 순서를 확인했다. 그 실패의 lookup open 상태는 보존하지 않아 런타임 원인
해석은 추론으로 구분한다. `cae7fc4`에서 실제 폼 존재를 기다린 뒤 열림을 구분하고 입력 전에
open을 확인한다. 실패 진단에도 그 상태를 추가했다. 원 데이터/권리/3D·정리 단언은 유지했다.
Python/내장 script 구문·원 helper/웹 앱·원5root/원본/FD·소유 정리를 통과했고
[후속39023732519](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39023732519)를
접수했다. 앞선 실패를 수용으로 세지 않으며 실제 저장 WebGL 수용은 여전히0시점이다.

최신 진행 feed는 `2026-10-17T10:09:33.079531Z`다. parser28개와 양쪽 실제
HTTP200/no-store·원문/기존 HTML·환기2,173파일/원5root/원본/FD·소유 정리를 확인했다.

## 현재 API→실제3D의 부분 증거와 스크린샷 경로 수정

네 번째 [39023732519](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39023732519)는
실제 정상 결과의 HTTPS summary/sample200 두 원문 bytes/hash와 **원3시점의 WebGL·표·그래프
대사**에 도달했다. 원 `00:00:00.123456Z`/`00:00:16.123456Z`/`00:00:32.123456Z`, 각50구획·
원 scalar/단위·41/6장부·수지·PAR/NIR/환기·원 참조/장면 UTC·온도 marker·실제 draw/SVG3을
검사한 뒤 세 frame JSON을 보존했다. 합성32초 소프트웨어의 부분 증거이며 농장/관문 승인은 아니다.

이후 스크린샷 이름에서 `Path / 'solar-' + status`가 되어 TypeError로 종료됐다. **PNG/사건/
권리 철회·재접속/hold/최종 조회·DB 역할 정리는 미검증**이며 전체 native 사례/S2b 수용은0이다.
82.079초·자식 exit1/reason없음·단일375,394,304/합585,203,712bytes·FD7→7·소유 잔여0이다.
`20831eb`에서 파일명을 괄호로 묶었다. 원 데이터·수용 단언과 한도는 유지했고 구문/원본/5root/
FD·소유 정리를 확인했다. [후속39024412408](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39024412408)을
따라간다. 세 시점의 부분 성공과 전체 정상/hold·현재 권리/정리 수용을 구분한다.

최신 feed는 `2026-10-17T10:20:15.870005Z`로 부분3시점과 최종 미수용을 구분한다.
parser28개·실제 양쪽200/no-store·같은 원문/기존 HTML·환기2,173파일·원5root/원본·
FD4→4/소유 정리를 확인했다. 로컬 새 Solar 배포/전체 goal 완료는 아니다.
