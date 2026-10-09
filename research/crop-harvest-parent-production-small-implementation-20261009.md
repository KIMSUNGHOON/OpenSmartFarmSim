# 정상 계산·게시 producer와 부모 인증 보존의 작은 구성

2026-10-09 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 조사·설계했다. 재귀 CLI0회.
[불변 영수증](artifacts/crop-harvest-parent-production-small-reference-20261009.json)의 SHA는
`db4bf581ed449cd019809554accc2a73f30ba7540c9634578491e98ab8c89cd1`다.
원17264 종료0·집중11개/실제 DB1개·원 DB 정리 후 현재 checkout에서의 fresh 복원을 수용했다.

## 구현과 판본

[core3 계약](../contracts/crop-harvest-parent-production-v1.md),
[정상 producer 구성](crop-harvest-parent-production.py),
[실제 시험](../backend/tests/crop_harvest_parent_production_smoke.py)을 추가했다.
기존 supervisor/별도 Python 전체 행 대사/정상 publisher 뒤에
[수용된 backup](crop-harvest-parent-backup-implementation-20261009.md)을 연결한다.
수식·격자·계수·제품 모듈/API/잠금과 기존 source/서명 검사는 변경하지 않았다.

첫 현재 checkout 준비에서 구형 source guard가 수확 후속의 API/웹6파일 변경을 거부했다.
`api.py`, `api_runtime.py`, OpenAPI와 웹3파일이다. 구형 고정 목록을 현재 hash로 바꾸거나 우회하지 않았다.
정상 producer는 별도 detached worktree의 **`dc7b852`**에 고정했다.
원392개 source hash를 모두 대조하고 새 core3와 선행 backup 파일의 복사 hash를 기록했다.
계산 worker/비교/publisher는 이 고정 source에서 실행하고,
원 DB 정리 후 복원 worker는 **현재 checkout의 코드**로 실행했다.
원 입력/artifact·runtime가 참조하는 fixture 경로를 위해 이 비공개 worktree도 보존한다.
이를 제품 API의 구형 판본 배포나 구형 관문 승인으로 취급하지 않는다.

## 실제 검증

| 대상 | 결과 |
| --- | --- |
| 정상 producer | 준비 manifest를 fixture/DB 생성 전에 만들고 원600초 마감 유지. 실제 supervisor worker 종료0·120걸음/603 RHS·3sample/3관리 event 완료 |
| 별도 비교·게시 | fresh Python에서 모든 원 행/UTC와121상태·clock/counter/수지 대사 후 정상 DB publisher 종료0 |
| 인증 보존 | 무작위 custody/DB/result key·원 payload/서명·입력/artifact inode 보존, raw backup308,638bytes≤128MiB |
| 현재 조회 | 처음/마지막 sample·전체3event·원 ID/payload/hash/기록 시각 일치. 현재 권리/scope 철회·다른 tenant 거부·복원 |
| DB 정리 뒤 복원 | source schema/role/passfile/cluster 정리 후 현재 checkout의 별도 Python이 새 cluster에 정상 restore·실제 host SCRAM/current query·같은 원 행 조회 |
| 읽기 연산 | 복원·조회 중 parser/context/QC/RHS·새 게시/증명 발행 금지·0회. 생성603 RHS와 구분 |
| 원 종료·자원 | 집중11개1.18초·실제 DB1개86.44초·정리 후 복원12.199초. 전체101.710초/600초·원17264 종료0 |
| WSL2·정리 | nice19·0.1초 표본·단일130.61MiB≤512MiB/소유 합355.31MiB≤1GiB. 1,400 source/원 입력 보존·PG2개 종료·남은 자식0·원 임시 디렉터리 없음 |

정지된 clone/data·unit 임시 파일41,797,497bytes는 제거했다.
후속 복원을 위한 비공개 backup/runtime/모델 입력/artifact와 고정 worktree는 의도적으로 보존한다.
현재 main core3와 실행한 복사본 hash가 같다. 키/역할 SQL/DB 원본을 공개 기록에 넣지 않았다.

## 다음과 남은 범위

작은 `crop-harvest-parent-production-small`만 체크한다. `crop-harvest-full-parent-restore`와 전체 수확/replay 부모는 미완료다.
이 구성으로 **같은 원 모델/입력의 새 전체166일 판본**을 시작할 수 있다.
전체는 원9시간 마감·47,809sample/5event·1,816,704걸음이며, 모든 원 행과121상태를 게시 전에 대사한다.
기존 전체 수용의 후보 행 hash도 비교한다. 새 농장/결과/payload/source 판본과 보존 자료를 별도로 기록한다.
그 뒤 전체 수확 writer/등록→실제 API/대표3D→기후/자원/Decimal 경제다.

전체 실행은 이전7시간15분 근거로 준비 후7–9시간 잠정이다. 작은102초로 전체 비용을 외삽하지 않는다.
전체 시작/진행은 별도 기록이며, 원 종료·자원·정리·복원 증거 전에는 완료하지 않는다.
새 전체·수확 writer/HTTP/WebGL, 전체 Backend/web/type/build와 hosted CI/push는 이 작은 검증에 포함하지 않았다.
실제 품종 입력·농장 작물 Run·국내 독립 자료0건, G0–G4 `not_assessed`와 생산/미래 마진/추천 hold를 유지한다.
