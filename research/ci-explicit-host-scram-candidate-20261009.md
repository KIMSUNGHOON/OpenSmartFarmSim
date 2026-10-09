# 작물 회귀 CI의 host 인증 초기화 후보 — 2026-10-09

상태: workflow 설정 후보와 소유 PG16 A/B만 확인. **새 hosted 전체 수용은 보류**다.
현재 native CLI `gpt-6.1-sol / xhigh`에서 판단했고 CLI를 재귀 실행하지 않았다.
[선행 고정 이미지/공식 source 조사](ci-host-scram-primary-evidence-20261008.md)를 재사용한다.

`dfc5a2c`의 [Backend run 37871758375](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37871758375)에서
분할0은731개 통과/2오류, 분할1은1,207개 통과/1실패·2오류다.
실패 위치는 원 DB를 쓰는 수확 registry 설정/시험/정리와 시장 정리의 `assert_host_scram`이다.
새 metadata/API 코드는 이 head에 없다. 실패 hosted HBA 원 행은 확보하지 못해 원인을 확정하지 않는다.

필요한 수정은 backend와 authored API 시험 컨테이너의 초기화 인자에
`POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=trust`를 명시하는 것이다.
기존 전체 host 감사·실제 require_auth 검사와 gate를 유지한다.
이는 작물 DB 회귀의 실제 실패에 필요한 설정 보완이며 운영 기반 범위를 확장하지 않는다.
`initdb`의 host/local 옵션은 각각 TCP와 Unix socket 초기 규칙을 지정한다.
[PostgreSQL18 공식 문서](https://www.postgresql.org/docs/18/app-initdb.html#APP-INITDB-OPTION-AUTH-HOST).
고정 entrypoint는 초기화 인자를 전달하고 뒤에 host 규칙을 추가한다.
[고정 공식 entrypoint](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/docker-entrypoint.sh).

두 fresh 소유 PG16.15 cluster에서 같은 broad SCRAM 행 추가를 비교했다.
기본 초기화 A는 host trust가 남아 전체 감사 기준과 loopback require_auth가 실패했다.
명시 초기화 B는 전체 host가 SCRAM이고 새 실제 연결의 used_password가 true였다.
이 결과는 로컬 초기화 재현이며 실패 Docker18 서버를 직접 조사한 증거가 아니다.
1.978896초/20표본, 기존 full/preview/두 DB와 집중 시험을 포함한 RSS 합755,929,088bytes,
단일155,357,184bytes다. 소유 두 PG·socket/passfile을 정리했다.
두 workflow의 bash block7+5개 문법 검사를 통과했다. Docker 이미지는 로컬에서 실행하지 않았다.
비밀/원 HBA/실험 로그는 private에 두고 [hash·수치 증거](artifacts/ci-explicit-host-scram-reference-20261009.json)만 보존한다.

새 head의 동일 이미지 실제 HBA/인증·전체 시험·UID·정리·집계 성공 뒤 hosted 수용을 판단한다.
