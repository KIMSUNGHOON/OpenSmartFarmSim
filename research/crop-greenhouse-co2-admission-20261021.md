# CO₂ 작업 접수·취소 기능 수용 — 2026-10-21 KST

[CI39520744344](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39520744344)의
source `43c0a98b4dfb239a53aca1c1076659333aacc0c9`에서17검사(제어4/실제 SCRAM13)가 통과했다.
[기계 증거](artifacts/crop-greenhouse-co2-admission-20261021.json)의17개 산출물/305개 현재 source 지문을 대사했다.
전체 backend/새 브라우저는 실행하지 않았다. 작은 합성 입력의 접수 기능이며 실제 작물 생산/농장 검증은 아니다.

## 확인한 기능

[실행 핵심 계약](../contracts/crop-greenhouse-co2-execution-core-v1.md)의 접수 자식만 수용한다.
기존 JobStore의 simulation 작업에 exact Co2FarmBinding 원 요청·농장 결속·resolver 판본을 고정했다.
별도 입력 판본/intent domain과 원64KiB 한도를 사용하며 새 schema/권한·worker를 추가하지 않았다.

| 검증 | 결과 |
| --- | --- |
| 멱등/충돌 | 같은 원 job/input·다른 입력의 같은 revision 충돌·다른 revision의 별도 queued 작업 |
| 닫힌 입력 | JSON/크기/unknown 필드/다른 family4개 거부 |
| 늦은 접수 변경 | 실제 insert 뒤 권리/create scope/review/resolver4종, job/input/event 전체 rollback |
| 현재 접근 | 다른 tenant·현재 create scope·자료 권리3개 거부, 삽입0 |
| 취소 | queued/claimed 소유자, 자료 권리 철회·simulation 범위 없는 상태에서 취소 가능; 다른 model/tenant/scope/terminal 거부 |
| 취소 fence | cancel scope 철회 뒤 queued/claimed 변경 rollback2, 자체 판본/domain/code 변경3개 거부 |
| 부작용 | 각 실제 사례의17개 수치/context/restore/UTC/CLI 진입점0·custody 디렉터리 빈 상태 |
| 자원/정리 | 167.060340초, 단일112,050,176/합198,365,184bytes·.25초 표본657개·FD6→6, schema/role/소유 process/passfile/임시 DB 항목0 |

접수·취소는 의도한 job/event SQL쓰기를 수행한다. SQL쓰기0이나 모든 산술0을 주장하지 않는다.
claimed 취소 시험의 ack는 기존 JobStore가 수행했고 CO₂ worker는 아직 구현하지 않았다.
원600초·512MiB/PID·합1GiB·4MiB log 한도를 유지했다.

개발 기록을 localhost5173/5174의 같은 JSON/HTTP200/no-store로 게시했다. 원 HTML·환기 frozen2,173파일,
원 자료2,148항목/보호5root·FD4→4와 소유 정리를 보존했다. 새 DOM/WebGL 시험은 실행하지 않았다.

## 다음 단계

접수 기능 수용 뒤 별도 checkpoint에서 확정 HEAD/provenance·UTC, 임대/취소/현재 입력 fence와
중복 사건/최초 시각 보존·계산0을 실제 DB로 검증한다. 그 뒤 자동 worker/발견→진행/HTTP/runtime→같은 UTC3D다.
[공통 WSL 용량](api-crop-greenhouse-co2-replay-20261021.md)·새 CO₂ 사용자 적용/전체 작기·자원/경제·
실제 CLI 종단 간·독립 농장 자료와 G0–G4는 남는다. 전체 완료일은 미정·goal active다.
