# 질량·배정 결과의 저장과 같은 UTC 재생 — v1

2026-10-08 구현 전 계약. 선행은 [명시 배정 개발 수용](../research/crop-harvest-events-implementation-20261008.md)과
[현재 조회](crop-cycle-calculation-query-v1.md)다. `crop-harvest-replay`의 첫 자식은 `crop-harvest-artifact`다.
첫3파일은 이 계약, `backend/app/crop_harvest_replay.py`, `backend/tests/test_crop_harvest_replay.py`다.
현재 정확한 native Codex CLI `gpt-6.1-sol / xhigh`에서 설계하며 CLI를 재귀 실행하지 않는다.

## 첫 저장 경계

`write_harvest_artifact(directory, query, tenant, result_id, farm_ref, parameter_raw, allocation_raw)`는
정확한 `CalculationCurrentCycleQuery`만 받는다. 확정된 전체 작기의 저장 결과에서 명시 질량·배정 묶음을
순회하고, 재적분 없이 별도 immutable artifact를 만든다. 첫 버전은 전체 확정 과거를 저장한다.
원 status가 hold이면 그대로 보존하며 미래를 생성하지 않는다. 임의 행/승인 bool로 writer를 대체하지 않는다.

원 source/result/payload/input/artifact/math manifest/상태와 실제 query identity, 두 입력 원문/hash,
질량·배정 코드와 dependency hash·단위·원 UTC/위치·미배정/관측 비교·출처 등급을 보존한다.
동일 원문/원 결과의 재시도는 같은 hash를 내며 다른 원본/계수/배정으로 기존 HEAD를 바꾸지 않는다.
원 crop artifact·DB·수식은 수정하지 않는다. 합성 산술 결과를 승인 Run으로 승격하지 않는다.

## 저장과 읽기

소유자0700 디렉터리와0400 SHA 이름의 canonical JSON blob,0600 writer lock,0400 HEAD를 쓴다.
기존 nofollow/ACL/owner/link 검사·immutable blob·fsync·usage 검사를 재사용한다.
한 page는64행/2MiB 이하, root2MiB 이하, 전체512MiB/65,536파일 이하이며 orphan/temp도 포함한다.
한 행도 page bytes를 넘으면 보류한다. 원 행 전체를 list로 모으지 않고 bounded page와 root index만 보유한다.
pages/root fsync 뒤 현재 코드·원 결과·권리를 다시 확인하고 HEAD를 atomic replace/fsync한다.
HEAD 이전 중단은 미게시 blobs, 이후 중단은 완전한 기존 HEAD로 구분하며 재시도 시 실제 파일을 대조한다.

`open_harvest_artifact(directory, expected_artifact_sha256, query, tenant, result_id, farm_ref)`는
운영자/후속 서버 등록이 보관한 expected hash로 열고 동일 현재 원 결과·권리를 검사한다.
reader는 `summary()`와 `page(start=0, limit=64)`를 제공하고 자신이 연 FD만 닫는다.
새 프로세스의 읽기는 저장 bytes/hash/단위/시각을 검증하며 질량·배정 계산/RHS/증명을 재발행하지 않는다.
각 선택 page와 root/HEAD를 다시 해시하고 반환 전 현재 source/identity·권리를 재검사한다.
원본/코드/HEAD 변경·닫힌 handle·잘못된 범위/단위·symlink/FIFO/권한/초과/혼합을 거부한다.
선택 페이지 응답도2MiB 이하이며 전체 합계와 부분 선택을 혼동하지 않는다.

SHA는 파일 무결성과 고정 expected hash의 비교다. 이 첫 저장물은 외부 진본 인증이나 DB 등록 증명이 아니다.
서버 소유 등록·서명/현재 query와 공개 DTO·HTTPS/SDK·같은 UTC 표/3D는 다음 자식에서 연결한다.
클라이언트가 고른 hash를 서버 등록 대신 승인하지 않는다. 출력은
`synthetic_harvest_allocation_math_only`·`rights_or_gate_approval=false`다.

## 수용과 의존성

1. 전체 원 질량/배정 행과 저장/분할/한 행 조회의 canonical bytes·UTC·단위·순서 hash 일치.
2. 명시 계수/배정 원문·source/identity·가정/미배정/hold 보존. 다른 결과·원문/입력·권리 철회 게시 거부.
3. 별도 Python 복원에서 질량/배정 함수/RHS0·중단 전후 HEAD·동시 writer/변조·파일/응답 한도/FD 정리 확인.
4. 작은 실제 현재 DB 조회·SCRAM·현재 권리/다른 계정 거부·원 파일/DB 보존·WSL 상한/소유 자원 정리.
5. 원 명령 종료·입출력/코드 hash·CLI·독립 대사·보고서가 존재한 뒤 artifact 자식만 체크.

전체166일 저장 비용/전체 행 검증과 대표 WebGL 검증은 후속에 각각 기록한다. 실제 품종 계수·국내 독립 자료0건,
실제 생산량·미래 마진/추천·G0–G4 보류는 유지한다. 합성 저장 개발은 실제 자료 확보/기후·자원 완성을 기다리지 않는다.
[19개 집중/별도 Python·실제 SIGKILL2개·실제 SCRAM1개와 root 대사](../research/crop-harvest-artifact-implementation-20261008.md)로
10월8일20:48 KST artifact 개발 자식을 수용했다. 실제 DB 권한의 fresh Python 재구성과 전체 작기/공개 재생은 별도다.
