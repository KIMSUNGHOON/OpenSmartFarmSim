# 일사 저장 결과 클라이언트 — 2026-10-17

[웹 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md) ·
[기계 증거](artifacts/crop-greenhouse-solar-web-client-implementation-20261017.json).

## 변경과 수용 범위

core `3ec7e10d26f2766cf8ed8c50824f87c8f415941f`에 저장 결과 해석기와 공통 인증 요청 연결을
구현했다. 후속 `d82861f3d19f95f04de9430a94c38dc6eb563302`는 진행표 시험 fixture만 수정했다.
**S1a를 로컬 원문/단위 검증과 hosted 타입·단위·빌드 검증 범위로 수용했다.**
작성 당시 원격 브라우저 단계의 종료를 확인 중이었다. [최종 취소/후속 진입 수정](crop-greenhouse-solar-sdk-resource-and-browser-entry-20261017.md)을 확인했으며 전체 웹 CI는 미수용이다.
실제 TypeScript SDK→현재 HTTPS(S1b), 저장 WebGL(S2), 계산 중 WebGL(S3), 사용자 적용(S4)은
이번 구현의 수용 범위가 아니다. 새 일사 화면은 아직 사용자에게 배포하지 않았다.

`greenhouseSolarReplay.ts`는 별도 Solar ID/판본의108상태·41연속/6사건 장부·15수지,
PAR/NIR/환기 진단과 관리 전후 상태를 해석한다. 닫힌 keyset·단위·유한 수치·50구획·
수지 예산·원 UTC microsecond/격자·출처/진행 해시·False 승인을 검사한다.
summary/page의 공통 참조와 원 시각을 대조하고 samples64/events8·응답2MiB/30초·
취소/시간 초과·전진/종료·혼합 판본/요청 중 변조를 확인한다.
`api.ts`에는 기존 공통 인증/no-store 요청을 사용하는 factory 연결 두 줄만 추가했다.
프론트엔드에서 생장·열/증기·수확·구매 에너지·돈을 계산하지 않는다.

## 원 응답과 검증

소유 합성 입력을 실제 SCRAM DB에 저장하고 fresh Python의 보호된 현재 API를
검증 TLS/Bearer로 읽었다. 정상/hold 각각 summary/samples/events의 원 HTTP body bytes를
수집했다. 공개 fixture는 이 여섯 원문을 그대로 담으며331,274bytes,
SHA `b9be03e0dc7ea9e5ac9aa80bfbf7e013d855acdbfc77dc6f89f2e14df672a908`이다.
private 연결·계정·키 필드가 없음을 재귀 검사했다. 합성 자료이며 현장 측정이나 G0 자료가 아니다.

| 증거 | 실제 도구/종료 | 결과 |
| --- | --- | --- |
| 정상 원문 확보 |71984:0|102.602초, 실제3응답/원 bytes·값·단위·UTC·조회 수식/SQL 변경0 |
| hold 원문 확보 |91873:0|102.192초, 실제3응답/실패 관리 경계와 앞선 확정 행 구분·조회 계산0 |
| 웹 집중 회귀 |60655:0|424검사/4파일: 새 Solar156 + 기존268 |
| 진행표 원 실패 재현 |93980:1|동일 과거 상태 가정의2실패, 자원/정리 관문은 통과 |
| 진행표 fixture 수정 |78520:0|28검사: React/5173 파서·과거 상태와 최신 게시 형식 분리 |

원문 확보는 기존 native 시험의 capture 전용 부분이다. 현재 권리의 정상 재검사와 원문 동일성은
실행했지만12철회/전송 실패 회귀 전체는 재실행하지 않았다. 앞선205검사/67검사를 새 검증 수에
더하지 않는다. 424검사는 기록 원문과 mocked transport를 사용하며 live SDK/브라우저가 아니다.
이전 green/red의 중복과 초기 RSS 중단·잘못된 단언은 최종424개에 더하지 않는다.

## 로컬 TypeScript 자원 보류와 CI

전체 `tsc --noEmit --singleThreaded`의 일곱 로컬 실행은 모두 child0/빈 compiler 로그였지만
합 RSS 관문 때문에 guard1이다. 이를 로컬 타입 검사 수용이나 운영 용량 증거로 세지 않는다.
합 최대는1,074,806,784–1,097,756,672bytes로1GiB를 넘었다.
TypeScript7.0.2의 실제 실행기는 Go native binary다. Node heap 제한만으로 이 컴파일러의
RSS를 제한할 수 없다. v1–v5는 실행기 후반의 상속 설정으로 실효 `GOMEMLIMIT=160MiB`였다.
v6–v7에서 중복 설정을 제거하고128MiB/GOGC25를 기록했지만 통과하지 못했다.
v7의 supervisor가 사용하지 않는 handoff 이력만 회수해1,503,232bytes를 줄였으며 제품 코드·
보호 대상·타입 검사 범위·tsconfig·한도를 바꾸지 않았다. 같은 조건의 반복 시도는 중단했다.

기존 Web workflow를 별도 `ci/solar-saved-client-20261017` 브랜치에 실행했다.
[첫39005288105](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39005288105)는
core3ec7e10의 타입 검사 성공 뒤 단위1,860통과/2실패로 종료했다. 두 실패 모두
`developmentStatus.test.ts`가 최신 진행표에서 과거 activation=next/미배포를 기대한 것이었다.
진행표의 실제 기존 환기 적용 완료 상태를 되돌리지 않고, 과거 상태는 고정 합성 fixture로,
최신 게시 파일은 양 파서의 원 필드 보존 검사로 분리했다. 원 실패와 로컬 red/green을 보존했다.

[후속39005600656](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39005600656)는
d82861f의 전체 타입·단위·build·audit는 성공했으나 브라우저 단계의15분 job 한도로 최종 취소됐다. 후속 원인/수정은 위 최신 기록을 따른다.
호스팅 환경의 검증을 로컬 RSS/WSL 용량 수용으로 대체하지 않는다. Backend/Compose 등
다른 workflow나 전체 저장소 CI를 이번에 실행했다고 표시하지 않는다.

## 보존과 사용자 산출물

위 로컬 실행은 원본2,148항목·두 frozen 서비스 source/assets·필수5root/동적 자식과
FD4→4·소유 비좀비/PG/임시 PG/passfile0을 확인했다. 새 Solar 회귀의 단일 최대240,713,728/
합1,063,952,384bytes는512MiB/PID/1GiB 안이다. 표본 간격은0.25초이며 순간값 전체의
원자 관측을 주장하지 않는다. 현재 두 사용자 HTML/기존 환기 source를 유지한다.

진행 기록을2026-10-17 14:20:15KST로 게시했다. 실제1269:0에서5173/5174의
HTTP200/no-store·동일 feed bytes·원 HTML과 기존 환기 source2,173파일 보존을 확인했다.
게시된 최신 기록에 대해서도 실제11036:0/28검사로 두 파서의 형식·원 필드 보존을 확인했다.
이28개는 앞선78520의 같은 사례를 재실행한 것이며 고유 수에 다시 더하지 않는다.
UI 코드·로컬 DOM/WebGL은 이번에 변경·재실행하지 않았다.

사용자가 검토할 새 산출물은 엄격한 저장 결과 SDK·원 여섯 응답 fixture·회귀/CI 기록이다.
실제 새 일사3D는 아직 없다. 기존5173의 전체 합성 저장 재생과5174의 기존 환기 경로를 유지한다.
native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 turn context와 출력 판본을 기록했으며
재귀 CLI0·실제 농장 Run0·G0–G4 `not_assessed`·승인False다.

## 다음 한 단계와 일정

다음 S1b는 새 SDK를 소유 합성 DB의 **현재 인증 HTTPS**에 연결하는 집중 시험이다.
1. 정상/hold의 원 summary와 제한된 sample/event 페이지를 실제 SDK로 조회해 원 bytes의
   값·단위·UTC·선택자·공통 참조와 정확히 대사한다. 기록 응답 재생으로 대체하지 않는다.
2. 현재 권리 철회/복원·잘못된 계정/판본·취소/전송 정리에서 결과를 거부하고,
   실제 서버 조회의 계산/SQL 변경0과 FD/소유 자원 정리를 확인한다.
3. 기존5root/두 UI/원본·512MiB/PID/합1GiB를 유지하고 실제 도구 종료/로그를 기록한다.

수용 후 S2에서 같은 원 UTC의 표·그래프·실제 WebGL을 연결한다. S3는 독립 unpaused
정상/hold/취소·전진 prefix·동시 자원 수용 뒤, S4는 두 장면/지속 판본의 재접속·재시작 뒤다.
외부 품종/시설·지역·독립 농장·미래 작기/시장 판본의 권리와 검증은 병행한다.
S1b의 실제 시험 구성·원 응답 비용을 확인한 뒤 잔여 작업량을 갱신하며 현재 전체 완료일과
남은 집중 시간은 미정이다. 사용자 제품·생산/미래 마진·작물 추천 관문은 완료하지 않는다.
