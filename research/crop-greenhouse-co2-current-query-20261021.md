# CO₂ 저장 결과의 현재 권리 조회 기능 수용 — 2026-10-21 KST

**기능 자식 수용, 공통 WSL 용량/사용자 적용 미완료.**
[CI39512608538](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39512608538)는
source`0394540b12262d79a814d0792aba4e03fbaa82c7`의 집중11검사를 통과했다.
[기계 증거](artifacts/crop-greenhouse-co2-current-query-20261021.json)에서 내려받은13개 산출물 SHA,
현재285코드/시험/fixture 지문과 기존278개 제품 파일의 보존을 대사했다. 전체 backend CI는 실행하지 않았다.

## 구현과 확인

[현재 조회](../contracts/crop-greenhouse-co2-current-query-v1.md)는 기존 Solar의 경계를88줄로 구분했다.
exact Co2ResultStore·같은 custody/등록 읽기 세션에서 원 row/manifest/UTC/페이지를 읽고 같은
검증된 reader의 program만 투영에 전달한다. 사용자 program/basis를 받거나 원 경계를 다시 계산하지 않는다.
투영 전과 직렬화 뒤 DB/HMAC/원 progress·컬럼·최초 기록 시각/HEAD·현재 권리를 재확인한다.
읽기 세션 종료와 마지막 계정/권한 검사 뒤에만 원 bytes를 반환한다.

| 검증 | 실제 결과 |
| --- | --- |
| exact 저장소 | 미구성/다른 타입·미초기화·기존 Solar 저장소5개 거부 |
| 실제 SCRAM 정상·보류 | 원 summary/samples/events bytes/SHA·값/단위/UTC·마지막 확정/실패·최초 recorded_at 동일 |
| 실제 fresh 현재 DB | 정상/보류 별도 프로세스2개, 각3응답 SHA·원문/최초 시각 일치, 현재 검토 철회 뒤 각3응답 거부 |
| 초기/늦은 철회 | 입력 권리·검토·읽기 범위·계정·농장 원천5종×3view, 투영/직렬화 두 단계에서 총60거부(초기30/늦은30) |
| 직렬화 뒤 변조 | DB lookup8종과 실제 소유 page/HEAD 파일2종, 총10거부 |
| 경계/조립 | 요청12개·농장4개 거부, 미존재None·다른 테넌트/가족·페이지 끝/커서·바뀐 store/코드/농장·2MiB·busy |
| 읽기 부작용 | 계산/context/restore/새 UTC binding/CLI를 포함한17계측 항목0, SQL쓰기0·원 행/최초 시각 보존 |
| 자원/정리 | 166.513784초, 단일124,268,544/합278,224,896bytes, .25초 표본660개, FD6→6 |

각 부모 조회의 FD13→13, fresh의 FD5→5이며 schema/role0·소유 프로세스0·passfile/임시 DB 항목0이다.
11개에는 기본5개와 실제 DB6개가 포함된다. fresh2는 정상/보류 검사 안에서 실행했으며13개 pytest라고 세지 않는다.
DB 변조는 반환 row에 대한 fault injection이며 page/HEAD는 실제 시험 소유 파일을 바꾸고 복구했다.
연결된 농장/경제 입력의 기존 결정론적 재검증은 유지한다. 모든 산술0을 주장하지 않는다.
개발 기록은 localhost5173/5174에 같은 JSON/HTTP200/no-store로 게시하고 원 HTML/frozen 소스를 보존했다.

## 남은 조건과 다음 단계

로컬 기본5개/전체11개 수집은 원5root·2,148자료/두 화면 frozen 소스·자산·FD/자원/정리를 보존했다.
로컬 실제 DB의 같은 메모리 실패를 반복하지 않았다.
[공통 WSL 동시 등록 용량](api-crop-greenhouse-co2-replay-20261021.md)의1,073,930,240bytes 미수용을 그대로 남긴다.
hosted 기능 검증으로 WSL 용량·새 사용자 적용이나 projection/current-query 부모를 완료하지 않는다.
기능/계약 수용은 다음 보호 HTTP 개발의 선행이다.

[보호 HTTP 계약](../contracts/api-crop-greenhouse-co2-route-v1.md)은 계획 상태다. 닫힌 GET·exact graph/
원 bytes·전후 인증/권한·실제 SCRAM/TLS 정상/보류와 늦은 철회·취소/전송 실패, 기존 OpenAPI/경로/import를
검증한 뒤 명시 runtime→worker/prefix→같은 UTC3D로 진행한다.
전체 CI·새 브라우저 DOM/WebGL·새 CO₂ 사용자 배포는 실행/수용하지 않았다.

작은 합성32초 소프트웨어 결과이며 실제 농장 Run0·전체 작기/자원/경제·실제 CLI 종단 간·독립 농장 자료와
G0–G4는 남는다. 검사 실행 시간을 개발 공수로 환산하지 않으며 전체 완료일은 미정·goal active다.
