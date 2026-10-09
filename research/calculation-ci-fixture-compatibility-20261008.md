# 계산 경로 CI 시험의 Python·원격 PG 호환 수정

2026-10-08 KST. `f2dc10f` Backend CI의 분할1/2/3 실패를 실제 job 로그로 확인했다.
[고정 영수증](artifacts/calculation-ci-fixture-compatibility-reference-20261008.json)에
로그 SHA·실패 재현/수정·실제 SCRAM·집중 검증과 source SHA를 보존한다.
native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI0회다.
제품 계산/모델·권리·schema·SDK/UI·의존성/잠금·CI 설정은 수정하지 않았다.

## 실제 CI 실패

| 분할 | 통과 | 실패 | 정리 오류 | 확인한 원인 |
| --- | ---: | ---: | ---: | --- |
| 1 | 1,198 | 3 | 0 | fresh import 전후 FD 차이 |
| 2 | 584 | 9 | 2 | 같은 FD 차이와 호스트의 PG 설정 파일 읽기 |
| 3 | 721 | 0 | 1 | 호스트의 PG 설정 파일 읽기 |

확인 시 분할0은 성공,4/5는 진행 중이었다.
이 수정은 기존 hosted 실행에 들어 있지 않다. 전체 CI 성공으로 표시하지 않는다.

## 표준 라이브러리 초기화와 프로젝트 import 구분

원 시험12개는 WSL Python3.12.3에서는 통과했지만 CI와 같은 uv CPython3.12.13 빌드에서
모두 실패했다. 별도 private venv에 같은 lock을 설치했으며 기본 venv나 lock을 바꾸지 않았다.
새 Python에서 FD 대상을 직접 확인해 표준 라이브러리 `secrets`의 첫 import만으로도
`/dev/urandom` 하나가 유지되는 것을 재현했다. 프로젝트 import 전 카운터4가5로 변한 원인이다.
이 관측은 해당 빌드의 실측이며 모든 Python 설치의 보장으로 일반화하지 않는다.
[Python 공식 문서](https://docs.python.org/3.12/library/secrets.html)는 이 모듈이 운영체제의 난수원을 사용한다고 설명한다.

fresh child에서 `secrets`만 먼저 import한 뒤 프로젝트 import 직전 FD를 기준으로 측정한다.
프로젝트 모듈은 미리 로딩하지 않는다. 기존 FD 동등성과 계산/store/query 모듈 미로딩 assertion은 유지했다.
특정 FD 대상이나 추가 개수를 허용하지 않는다.
세 import 순서의 별도 음성 대조에서 실제 파일 하나를 더 열면5→6으로 변하고 모두 실패했다.
정상 세 대조는5→5/종료0이다.

최종 **12개 모두 CI Python3.12.13에서10.90초, WSL Python3.12.3에서11.91초**로 통과했다.
고유12개의 두 환경 검증으로24개의 서로 다른 시험이라고 세지 않는다.

## 서버에서 HBA 검사

CI의 `/var/lib/postgresql/18/docker/pg_hba.conf`는 DB 컨테이너 내부 경로다.
호스트 Python의 파일 읽기로 실제 정리 검증 세 곳이 실패했다.
공통 시험 helper가 admin 연결에서 `pg_catalog.pg_hba_file_rules`를 조회하고,
오류 행·host 규칙 부재·SCRAM 이외 host 인증을 거부하도록 바꿨다.
로컬 admin용 Unix trust와 host SCRAM을 구분한다.

[PostgreSQL 공식 문서](https://www.postgresql.org/docs/18/view-pg-hba-file-rules.html)에 따르면
이 view는 현재 파일 내용을 보여주며 마지막으로 로딩된 설정의 증명은 아니다.
따라서 별도 실제 host 접속에서 `require_auth=scram-sha-256`과 `used_password`를 확인했다.
운영 계정에 이 superuser view 권한을 추가하지 않았다.

미구현 helper의 수집 실패를 먼저 확인한 뒤 **새7개/1.93초**를 통과했다.
그중6개는 빈/비 SCRAM/파싱 오류 행의 거부와 정상 host 규칙 검사다.
나머지는 실제 로컬 PG16.15/SCRAM과 변경한 세 정리 fixture의 직접 실행이다.
호스트 `Path.read_text`를 금지한 상태에서도 schema/role/passfile0과 인증 규칙 검사를 통과했다.
fixture의 실제 PG 종료와 소유 임시 디렉터리 정리도 확인했다.

## 범위와 다음 작업

고유19개 집중 검증이다. 전체 Backend·세 loader/runtime/HTTP 계산 시나리오나
수정 후 hosted PostgreSQL18을 다시 실행한 것은 아니다. 기존 hosted run을 취소·재시작하거나 push하지 않았다.
남은 job의 실제 종료를 확인하고 이후 일반 push 판본에서 hosted 수용을 따로 확인한다.

작물의 다음 핵심 작업은 [작은 비용 측정](crop-cycle-calculation-prefix-cost-observed-20261008.md) 뒤
전체166일의 실제 농장·경제 달력 등록과 누적 비용이다.
전체 저장/복원·API/같은 UTC3D → 생과/자원 → Decimal 경제 순서를 유지한다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건과 G0–G4 `not_assessed`는 그대로다.
