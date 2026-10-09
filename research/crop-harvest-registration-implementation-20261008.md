# 수확 산술 파일의 서버 서명·DB 등록 개발 수용

2026-10-08 21:35 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·검토했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-harvest-registration-implementation-reference-20261008.json)에
원 명령/종료·421 source·실제 파일/서명/DB·현재 권리·독립 대사와 정리를 결속했다.
선행 [등록 스키마](crop-harvest-registry-schema-implementation-20261008.md)와
[불변 질량·배정 저장](crop-harvest-artifact-implementation-20261008.md)을 보존한다.

## 구현과 사용자 산출물

[등록 제공자](../backend/app/crop_harvest_registry.py)의 `HarvestRegistry.put`은 정확한 현재 crop query와
원 result/farm·명시 합성 질량/배정 원문에서 서버가 저장 key·artifact·결과 ID를 결정한다.
원 부모/농장·원문 SHA·code를 고정하고 현재 계산/표시 권리와 쓰기 scope를 검사한다.
서버가 불변 파일/HEAD를 먼저 생성·전체 행 순서를 검사한 뒤 별도 domain/key의 metadata HMAC과
실제 SCRAM publisher 거래로 DB에 등록한다. DB/로그인·실제 역할/객체/권한도 거래 전후 감사한다.
기존 원 store/schema/runtime role·서명/수식을 수정하지 않았다.

private root는0700·소유자/ACL/symlink/inode 검사·단일 registry lock을 사용한다.
전체1GiB/131,072파일/128등록 디렉터리·생성 전 최대 artifact 예약을 검사하며
기존 artifact512MiB/65,536파일·64행/2MiB page 제한을 유지한다.
고객은 임의 key/path/hash·서명/승인 bool을 등록 인자로 제공할 수 없다.
재시도는 같은 서명 record·최초 DB 시각을 보존하고 질량/배정 행을 재생성하지 않는다.
파일 완료 뒤 DB 실패는 private orphan을 허용하며 재착수 시 같은 입력에서 writer의 기대 hash를 다시 구한다.

사용자는 실제6행·4저장 파일·원문/판본·서버 key/서명·DB 등록1건과 rollback/재시도 증거를 확인할 수 있다.
이는 소유 **합성 입력·시험용 key**의 실제 소프트웨어 경로다. 실제 품종/계수·독립 농장 생산량을 채택한 것이 아니다.
임시 DB/서버는 정리했으므로 사용자 계정의 저장 이력에는 생성되지 않는다.

## 통과한 검증

| 대상 | 확인한 범위 |
| --- | --- |
| 최종 집중 시험 | [시험 파일](../backend/tests/test_crop_harvest_registry.py) 전체38개·원 종료0·135.10초. 순수37개/실제 DB1개이며 앞선37개 시험은 중복 합산하지 않음 |
| 순수 검사 | 닫힌/canonical metadata·서버 key/ID·HMAC/SQL 열·code/policy 변경·hash/행 수/중복 key/bytes·암묵 설정·root 이름/symlink/용량 거부 |
| 실제 DB/파일 | PostgreSQL16.15/TCP SCRAM·실제 최소 권한 publisher·원6행 artifact→서명/DB1건·두 원문/원 부모/농장·code/행 순서 결속 |
| 거래/권리 | 실제 INSERT 직후 **계산 권리만 철회, 표시 권리 유지**→최종 검사 거부/DB0·private HEAD1. 권리 복원 뒤 writer 재착수·실제 등록1건 |
| 동일 재시도 | writer/질량·배정 행 생성 함수를 금지한 재시도에서 같은 record/최초 `recorded_at`·DB1건 유지 |
| 거부7종 | 쓰기 scope·다른 계정·계산 권리·혼합 source/농장·reader 게시·잘못된 서명. 원 행/파일/DB 수 보존 |
| 독립 감사 | 실제 저장 bytes/SHA/mode·서버 key/metadata/code·시험용 HMAC·두 원문·page/행 순서 대사. 2200자리 Decimal로 C/N·건물/생과 배정/미배정·관측 차이 대사 |
| 보존/정리 | 기존 부모 query/runtime role 감사·입력/custody SHA/mode/inode·DB 행 수 보존·RHS0/새 proof0·FD13→13·421 source 불변·새/기존 schema/role/passfile0·소유 PG/controller/temp 종료 |

실제 시험은21:32:11→21:34:27 KST, 준비부터 정리까지135.607초였다.
원600초 상한·0.1초 감시1275개 표본에서 primary RSS 최대125,349,888bytes≤512MiB,
PG/controller 포함 소유 PID RSS 합 최대268,316,672bytes≤1GiB다.
공유 page 중복 가능 RSS 합이며 PSS/WSL 전체/production 동시 부하의 증거는 아니다.
21:35 KST root 감사 뒤 시험 당시3파일을 보존하고 source freeze를 해제했다.

## 다음 한 단계와 외부 의존성

[등록 계약](../contracts/crop-harvest-registration-v1.md)의 `crop-harvest-registration`만 추가 체크한다.
다음은 서버 등록 result ID에서 서명 key/hash를 해석해 현재 **읽기 scope·표시 권리** 아래
summary/page를 제공하는 `crop-harvest-registered-query`다. 원 result/농장·등록 signature/code·현재 원 source와
파일을 전후 검사하고 혼합/변조/철회/다른 계정을 거부한다. 없는 등록/미등록 파일을 결과로 채택하지 않는다.
새 Python 프로세스에서 같은 실제 DB 권한을 재구성하고 수확 행 재생성/RHS0·페이지/자원/비밀 정리를 확인한다.
그 뒤 HTTP/SDK→같은 UTC 표/3D→기후/물·양분/구매 에너지·기존 Decimal 경제 계산으로 진행한다.

전체166일 새 질량/배정 등록 부하·등록 현재 query/fresh 실제 DB 복원·새 HTTP/SDK/3D·
전체 Backend/web suite·hosted CI·실제 제품 CLI/품종 검증은 실행하지 않았다. 전체166일 RHS도 반복하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`,
생산/미래 마진/추천·원격 Backend/push·구형 native25시간 원 종료 기록 보류는 유지한다.
이 개발 자식의 실제 수용 시각은10월8일21:35 KST이며 외부 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
