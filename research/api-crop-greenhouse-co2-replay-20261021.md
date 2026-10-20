# CO₂·일사 저장 결과의 공개 응답 기능 검증 — 2026-10-21 KST

**기능 자식 수용, WSL 동시 용량과 부모 작업 미완료.**
[CI39510460411](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39510460411)의
source`d7167c20ab4a18849ba57426c66f1a6a264f8024`를 검사했다.
[기계 증거](artifacts/api-crop-greenhouse-co2-replay-20261021.json)는 내려받은9개 산출물의 SHA와
현재 작업 트리의282개 원 코드/시험/fixture 지문을 대사했다. 전체 backend CI는 실행하지 않았다.

## 산출물과 검증

[새 공개 응답](../contracts/api-crop-greenhouse-co2-replay-v1.md)은 이미 저장된 원 summary/samples/events를
닫힌 타입으로 표현한다. 109상태·8파생량·44연속 장부·6사건 합계·17수지와 원 단위/UTC,
사건의 전후 상태·10수지/예산을 보존했다. 원 v2 journal에 없는 after_rhs/Solar 사건 진단은 만들지 않았다.
ppm의 wet/dry는 같은 검증된 원 program의 SHA와 원 forcing_step_index로 연결했다.
확정되지 않은 새 forcing이 같은 시각에 실패해도 마지막 확정값의 기준을 바꾸지 않는다.

| 검증 | 실제 결과 |
| --- | --- |
| 순수 projection | 37개 통과: 원 정상/보류·10프로그램·실패 시각의 미확정 forcing·닫힌 타입/단위/페이지·비공개 필드 |
| 실제 SCRAM 등록/조회 연결 | 정상·보류2개 통과, 원 progress38,616/20,092bytes·최초 recorded_at·원 값/시각 |
| 별도 fresh 프로세스 | 실제 등록 원문의 정상·보류 각3응답 SHA 정확 일치, SQL 호출0 |
| 읽기 부작용 | 수치/context/restore/새 UTC binding/CLI17진입점0, 실제 연결 SQL쓰기0·원 행 수 동일 |
| hosted 자원/정리 | 78.386458초, 단일124,628,992/합228,556,800bytes, .25초 표본310개, FD6→6 |
| DB/프로세스 | schema/role0, 살아 있는 소유 프로세스0, passfile/임시 DB 항목0 |

최대 응답은 정상 samples99,408bytes로 원2MiB 상한 안이다. 이 표의39개는 로컬37개를 더한76개가 아니다.
fresh는 projection 자체를 검증하며 새 프로세스의 현재 DB 권한 확인을 대신하지 않는다.
그 확인은 후속 current query의 별도 수용 범위다.

두 localhost5173/5174의 개발 기록도 같은 JSON/HTTP200/no-store로 게시하고 원 HTML·frozen 소스를 대사했다.
새 브라우저 DOM/WebGL 검사는 하지 않았으며 모델/화면 배포를 바꾸지 않았다.

## WSL 시험과 설정 진단

[사전 증거](artifacts/api-crop-greenhouse-co2-replay-preflight-20261021.json)의 실제 DB 시험은
기존5서비스를 포함한 합산1GiB 상한으로 종료됐다. 마지막1,073,930,240bytes도 **미수용**이다.
내부 예외는 AdminShutdown까지 이어졌고 감시기는 메모리 초과 시 소유 프로세스에 SIGTERM을 보낸다.
이를 저장 계산 결함의 증거로 판정하지 않았다. 원2,148자료·두 화면의 frozen 자산/소스·5root·FD/정리는 보존했다.
로컬 순수37개와 템플릿 fresh의 원 SHA/계산0은 별도로 통과했다.

실제 소유 PG에서 환경변수 기본 work_mem64kB/jitoff가 명시 연결 options 사용 시4MB/on으로 바뀌는 것을
확인했다. 호출자가 직접 지정한 값이 환경변수 기본보다 우선한다는
[PostgreSQL16 문서](https://www.postgresql.org/docs/16/libpq-envars.html)와 일치한다.
새 시험 DB의 시작 옵션과 실제 인증 연결에만 같은 예산을 적용했다. 기존 제품/공통 fixture·SQL/권리 검사·
원 입력/단계 수/시간/512MiB·1GiB 상한은 바꾸지 않았다. 생산자 뒤 GC를 앞당겨도 WSL 용량은 미수용이었다.
특정 query의 JIT가 전체 메모리 초과를 만들었다는 측정은 하지 않았다.

## 남은 수용과 다음 단계

`co2-result-projection` 부모의 WSL 동시 등록 용량은 미완료로 유지한다. 같은 실패 조건을 반복하지 않는다.
기능/계약 수용은 후속 현재 조회의 개발 착수 조건이며 WSL 사용자 적용 조건은 그대로 남는다.

다음 `co2-current-query`는 같은 store/custody 읽기 세션에서 원 program을 가져오고, 투영 전후와 직렬화 뒤
현재 계정/권리·DB/HMAC/최초 시각/원 progress·선택 HEAD와 페이지를 재확인해야 한다.
정상/보류·fresh 현재 조회, 늦은 철회/행·파일 변조·경계값, 조회 계산/SQL쓰기0과 자원/정리가 수용 기준이다.
그 뒤 보호 HTTP/명시 runtime→worker/prefix→같은 UTC3D 순서다.

새 CO₂ HTTP/사용자3D는 배포하지 않았다. 실제 농장 Run0, 전체 작기·물/양분·구매 에너지·경제·최종 UI와
실제 CLI 종단 간/독립 자료·G0–G4는 남는다. 검증 실행 시간을 개발 공수로 환산하지 않으며 전체 완료일은 미정이다.
