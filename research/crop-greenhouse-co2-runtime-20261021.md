# CO₂ 결과 명시 서버 연결 기능 수용 — 2026-10-21 KST

**기능 자식 수용, 공통 WSL 용량/사용자 적용 미완료.**
[CI39518527650](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39518527650)는
source `8c1ba5d8b94d52571db5e4ba8230e3af6c347fbf`의 집중177검사를 통과했다.
[기계 증거](artifacts/crop-greenhouse-co2-runtime-20261021.json)에15개 curated JSON과302개 현재
source 지문 대사를 기록했다. 실제 farm 자료가 아닌 합성32초 조회 기능이며 전체 backend/새 브라우저는 실행하지 않았다.

## 구현과 검증

[명시 runtime 계약](../contracts/crop-greenhouse-co2-runtime-v1.md)의 별도 읽기 판본/정확한 bool 동의와
같은 Co2 store/query/jobs/farms/current_principal·키/코드/역할을 연결했다. 기존 직접 생성자의 암묵적
True 거부와 원 loader/helper를 유지했다. 새 loader는 같은 bytes로 다시 쓴 파일도 metadata로 거부한다.

| 검증 | 결과 |
| --- | --- |
| 집중 inventory | 새 control79 + 새 native2 + 기존 Solar control60/native2 + 기존 flag/loader3 + 공통 runtime31 = 177통과, skip0 |
| 실제 조립/전송 | 새 CO₂/기존 Solar 각각 정상·보류의 실제 SCRAM/검증 TLS, 총4 reader/원3view씩12응답 bytes·단위/UTC·헤더 일치 |
| 잘못된 조립 | 각 정상에서 wrong/foreign store/query·3종 key 재사용·code pin·실제 SELECT 철회9개 거부 |
| 늦은 권한/전송 | 각 정상에서 input-rights/review/farm-source/credential×3view=12거부·cancel/send-failure 정리 |
| 기존 설정 | 12판본/15맥락·누락/False30수용, True/잘못된 타입105개 factory 이전 거부, 기존 Solar True3맥락 유지 |
| 부작용 | CO₂의17계측(kernel/context/restore/UTC/CLI)·SQL쓰기0, 기존 Solar 계측/SQL쓰기0·원 row count/bytes 보존 |
| 자원/정리 | 415.620283초, 단일200,888,320/합418,045,952bytes, .25초 표본1,579개·FD6→6/각 reader4→4 |

원600초·512MiB/PID·합1GiB·4MiB log 한도를 유지했다. 각 정상의 시험 owner가 SELECT를 REVOKE/GRANT하는
2회 변조는 별도로 기록했으며 제품 조회 SQL쓰기0에 포함시켜 숨기지 않았다. 각 schema/role·소유 프로세스·
passfile/임시 DB 항목0, 설정 파일과 미사용 legacy custody도 보존했다.
연결된 농장/경제 입력의 결정론적 재검증은 유지하므로 모든 산술0을 주장하지 않는다.

개발 기록을 localhost5173/5174에 같은 JSON/HTTP200/no-store로 게시했다. 원 HTML·환기 frozen 소스2,173파일과
원 자료2,148항목/보호5root·FD4→4·소유 정리를 보존했다. 새 DOM/WebGL 검증은 실행하지 않았다.

## 다음 단계와 남은 조건

[공통 WSL 동시 등록 용량](api-crop-greenhouse-co2-replay-20261021.md)의1,073,930,240bytes 미수용은 남는다.
hosted 수용으로 projection/current-query/HTTP/runtime 부모나 사용자 적용을 완료하지 않는다.
[실행 핵심 계획](../contracts/crop-greenhouse-co2-execution-core-v1.md)에 따라 접수/취소→확정 checkpoint→
자동 worker/발견을 각각 검증한다. 이후 진행 query/HTTP/실행 runtime→typed web/같은 UTC3D→WSL 사용자 적용이다.

새 CO₂ 사용자 배포·전체 작기/자원/경제·실제 CLI 종단 간·독립 농장 자료와 G0–G4는 남는다.
검사 실행 시간을 개발 공수로 환산하지 않으며 전체 완료일은 미정·goal active다.
