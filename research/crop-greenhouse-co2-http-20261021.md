# CO₂ 결과 보호 HTTP 기능 수용 — 2026-10-21 KST

**기능 자식 수용, 공통 WSL 용량/사용자 적용 미완료.**
[CI39516513080](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39516513080)는
source `f8620cb720d18862f58a1bba55c805de42d3332c`의 집중215검사(213 제어/계약·실제 SCRAM/TLS2)를 통과했다.
[기계 증거](artifacts/crop-greenhouse-co2-http-20261021.json)에 내려받은15개 JSON의 SHA와
현재294개 코드/시험/fixture 지문 대사를 기록했다. 전체 backend CI와 새 브라우저 검증은 실행하지 않았다.

## 구현과 검증

[보호 GET 계약](../contracts/api-crop-greenhouse-co2-route-v1.md)에 따라 exact CO₂ store/query와 같은
jobs/farms/principal을 명시 조립한다. 현재 query의 검증된 원 bytes를 전후 인증/권한 검사 뒤 반환한다.
새 program/basis/forcing·계수는 받지 않는다. 기본 operator 활성화는 추가하지 않았다.

| 검증 | 결과 |
| --- | --- |
| 집중 inventory | 새 route68 + 실제 native2 + 기존 Solar route65 + OpenAPI80 = 215통과, skip0 |
| 실제 SCRAM/검증 TLS | 별도 정상/보류 reader2, 각 summary/samples/events 원 bytes/SHA·값/단위/마이크로초 UTC·no-store/코드 헤더 일치 |
| 늦은 철회 | 정상의 input-rights/review/farm-source/credential ×3view = 12응답 차단 |
| 전송 정리 | cancel/send-failure 뒤 reader/현재 principal/FD 복구 |
| 기존 계약 | 기존64경로/398스키마의 canonical 값/참조 유지, 새65경로/477스키마·공통 scope inventory 대사 |
| fresh import | 새/기존 각각3개 import에서 DB/socket 접속0·현재 query 미로드 |
| 읽기 부작용 | kernel/context/restore/새 UTC/CLI를 포함한17계측0·SQL쓰기0·원 row/count 보존 |
| 자원 | 349.663600초, 단일210,288,640/합433,242,112bytes, .25초 표본1,380개 |
| 정리 | guard FD6→6·각 reader4→4, schema/role/소유 프로세스/passfile/임시 DB 항목0 |

원600초·512MiB/PID·합1GiB·4MiB log 한도를 유지했다. 정상/보류의 HTTPS 최대 응답은99,408bytes이며
동시 사용자 처리량 시험은 아니다. 연결된 농장/경제 입력의 기존 결정론적 재검증은 유지하므로 모든 산술0을 주장하지 않는다.

[첫 CI39515461476의 실패/수정](artifacts/crop-greenhouse-co2-http-scope-fix-20261021.json)은 보존했다.
실제 native2는 통과했지만 공통 scope 시험의 새 ID/query 생성이 빠져422가 나왔다. 제품 코드는 그대로 두고
유효 요청을 구성하도록 시험만 보완했다. 기대403/저장소 읽기0과 같은215개·원 한도는 유지했다.
로컬 수정1검사 통과 뒤 위 CI로 전체 집중 범위를 수용했다.

개발 기록을 localhost5173/5174에 같은 JSON/HTTP200/no-store로 게시했다. 원 HTML·환기 frozen 소스2,173파일,
원 자료2,148항목/보호5root·FD4→4와 소유 정리를 보존했다. 새 DOM/WebGL 검증은 실행하지 않았다.

## 남은 조건과 다음 단계

[공통 WSL 동시 등록 용량](api-crop-greenhouse-co2-replay-20261021.md)의1,073,930,240bytes 미수용은 남는다.
이 결과는 hosted 기능 수용이며 projection/current-query/HTTP 부모와 사용자 적용을 완료하지 않는다.
같은 용량 장애를 중복 공수로 세지 않고 다음 [명시 읽기 runtime](../contracts/crop-greenhouse-co2-runtime-v1.md)을 진행한다.
기존 config/loader의 암묵적 True 거부를 유지하며 명시 동의/같은 factory graph를 실제 DB/TLS로 검증한다.
그 뒤 자동 worker/prefix→같은 UTC3D→사용자 적용이다.

작은 합성32초 조회 기능이며 새 CO₂ 사용자 배포·전체 작기/자원/경제·실제 CLI 종단 간·독립 농장 자료와
G0–G4는 남는다. 검사 실행 시간을 개발 공수로 환산하지 않으며 전체 완료일은 미정·goal active다.
