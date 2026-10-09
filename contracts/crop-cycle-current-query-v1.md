# 현재 농장 권한을 확인하는 저장 작기 조회 — v1

2026-10-07 KST. [구현 순서](../tasks/todo.md)의 `crop-cycle-current-query`를
농장/DB/서명 결속과 API/runtime 연결로 나누어 검증한다. 전자는 이 계약·제품 모듈·실제
DB 시험의3 core파일이며, 후자의 실제 TLS 수용까지 부모 체크박스를 유지한다.

## 명시적 조회 인터페이스

`CurrentCycleQuery(store, authority, *, evidence_resolver)`는 정확한 기존
`CycleCropResultStore`와 `ResultEvidenceAuthority`를 받는다. 서버 구성에서 제공하는
resolver는 `version`을 갖고 `(tenant, packet)`에 대해 현재 원 입력 디렉터리와
`input_evidence_raw`, `result_evidence_raw`만 반환한다. HTTP 입력으로 경로나 proof/키를
받지 않는다. resolver는 받은 packet을 수정할 수 없다. 입력 root는 원 DB packet으로 고정하고,
결과 경로는 원 custody root/intent/artifact로 직접 계산한다. resolver의 새 판본을 기록하며
원 계산 resolver 판본으로 재표시하지 않는다. 기존 계산 타입/토큰을 만들지 않는다.

`read(tenant, result_id, farm_ref, *, kind=None, start=0, limit=None)`는 없는 ID에 `None`,
나머지는 private `{record, terminal, page, identity}`를 반환한다. `kind=None`은 summary,
나머지는 `samples`/`events`의 기존 bounded 페이지다. 값·UTC·checkpoint·manifest는 원 결과이며
새 조회 code/dependency, 두 QC 증명 SHA와 원 DB/intent/head/proof/binding SHA를 함께 기록한다.
이 private bundle은 공개 응답이 아니며 별도 명시적 API 투영을 거쳐야 한다.
`open(...)` context manager는 같은 bundle을 yield한 뒤 종료 전에 다시 결속한다.
API는 이 문맥 안에서 투영/전체 bytes를 준비해야 투영 후 철회도 반환 전에 거부한다.
`read(...)`는 이 문맥으로 즉시 사본을 받는 private 편의 함수다.

## 반환 전후 결속

현재 계정/Scope와 실제 DB row의 tenant·farm·HMAC/column·원 payload를 확인한다.
현재 등록 및 원천 권리와 입력 `research_display` 권리를 재확인하며 선언의 변경도 거부한다.
QC 증명의 현재 root/기간/계획/프로필/정규화/원 math context는 원 farm binding과 같아야 한다.
현재 등록의 입력 기간/점유/바닥 면적/품종 식별도 기존 검사로 대사한다.

소유한 no-follow 디렉터리/0400 파일에서 원 intent HMAC와 선택된 head의 **전체 부모 서명
사슬**을 검증한다. 기존의 순수 서명 해석 helper만 명시적으로 재사용하며 `_Journal`/writer나
기존 계산 문맥을 구성하지 않는다. 원 DB progress의 intent/binding/context/header/head/proof,
artifact/status/걸음/출력/사건/commit/실제 저장 bytes·파일 수가 QC 결과와 모두 같아야 한다.
원 서버가 계산/선택한 서명이 없는 순수 참조 결과는 조회 권한을 얻지 못한다.

페이지/summary 준비 후 같은 DB row·등록/권리·trace·현재 입력/result bytes를 다시 대사한다.
서버/authority/resolver/정책 판본과 경로 inode 교체도 거부하며 모든 FD는 성공/실패에 닫는다.
원 parser/context 준비/terminal QC/RHS를 조회 중 실행하지 않는다. QC 발행은 별도 서버 작업이다.
조회에서 DB나 custody 파일을 쓰거나 새 server progress를 발행하지 않는다.

## 수용과 보류

실제 SCRAM 등록/원 RHS/불변 DB 저장 후 원 모든 작은 sample/event·UTC·manifest 대사,
재구성한 서비스/별도 프로세스 재조회, 현재 Scope/계정/등록·원천/입력 권리 철회,
DB/intent/선택·부모 proof/HEAD/입력·결과 물리 변조와 조회 중 철회/변경 거부,
읽기 RHS/parser0·FD/DB/역할/비밀 파일/PG 정리를 집중 시험한다.
실제 API/runtime/TLS의 전체 본문30초/2MiB·거부 투영 검증은 다음 연결 수용에서 확인한다.

합성 연구 소프트웨어 검증이며 권리 채택/G0–G4 승인이 아니다. 실제 품종/독립 농장 자료0건,
원166일 종료 확인 불가와 전체 farm/API/같은 ID·UTC3D 부하는 계속 보류한다.
