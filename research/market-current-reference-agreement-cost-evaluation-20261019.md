# 보호된 현재 참조 검증의 비용 평가 — 2026-10-19 KST

상태: **실제 계산 구간의 비교·진단은 수용, 연결 후보는 비용 증가로 미채택**.
[기계 증거](artifacts/market-current-reference-agreement-cost-evaluation-20261019.json) ·
[시험 전용 helper](artifacts/market-current-reference-agreement-cost-evaluation-20261019-helper.py.txt) ·
[비교 검사](artifacts/market-current-reference-agreement-cost-evaluation-20261019-pair-test.py.txt) ·
[비용 진단](artifacts/market-current-reference-agreement-cost-evaluation-20261019-profile-test.py.txt) ·
[연결 관측](artifacts/market-current-reference-agreement-cost-evaluation-20261019-connection-test.py.txt).

기준은 `e5f4f713b931ed95b1ce46f3c0730b8a33835117`이다. 제품 app260파일과 시험은
수정하지 않았다. 기존 v2, [guard37](market-current-reference-dependency-guard-20261019.md),
[primitive48](market-current-reference-receipt-primitive-20261019.md), primitive34,
조건부 대조12와 HTTP58의 수용 범위는 그대로다. 제품의 새 getter 생략 호출은0이다.
조사·판단은 현재 native Codex CLI `gpt-6.1-sol/xhigh`에서 수행했고 실제 문맥 시각/해시를
기록했다. 재귀 CLI·하위 에이전트는 사용하지 않았다.

## 실제 비교

같은 실제 SCRAM DB·기존 합성 입력의 별도 custody에서 원 경로와 후보를 두 번 준비하고,
step2는 원→후보, step3은 후보→원 순서로 비교했다. 별도 API/자동 worker의64단계 검증은 아니다.

후보는 같은 등록 수명의 guard와 원문 지문을 결합했다. 최초 원 full trace가 전후 같은 지문과
실제 최종 역할 감사를 통과한 뒤에만 anchor를 고정했다. 이후 같은 기대를 대사하면서 각 논리
조회의 현재 tenant 검사와 실제 동적 getter를 실행하고 순수 자료 재구성을 생략했다.
이 helper는 정상 비용의 타당성을 먼저 평가하기 위한 시험 전용 코드다. 공격·변경·오류 경로의
완전한 통합 회귀를 통과한 제품 구현으로 수용하지 않는다.

| 실제 계산 구간 | 원 경로 초 | 후보 초 | 후보 시간 증가 |
| --- | ---: | ---: | ---: |
| step2, 원→후보 | 7.086337230 | 8.420348388 | 18.83% |
| step3, 후보→원 | 7.127252663 | 8.367791461 | 17.41% |

두 구간 모두 원 수치·UTC·checkpoint·counts·상태·provenance/artifact hash를 대사했다.
각 구간 역할 감사183회와 역할 SQL2,745회는 같았다. 후보의 anchor1·자료 증거1,672·동적 getter264와
활성 프레임1/미지원0·종료 뒤 프레임0을 확인했다. SQL 결과를 가로채지 않았다.

원천 조회는1,824→152회, 전체 SQL은7,113→5,291회이며 후보 지문 SQL은48회였다.
원천 조회 trace hash도 달라졌다. 따라서 원 getter 횟수·순서 보존을 주장하지 않는다.
SQL 수 감소에도 실제 총 시간이 두 구간 모두 늘어 **이 후보를 제품에 연결하지 않는다**.
단일 fixture의 두 구간 관측이므로 일반 처리량·통계적 성능 추정으로 확대하지 않는다.

## 비용 분리

별도 실제 advance에 Python 함수/SQL 호출 계측을 적용했다. 아래 함수 시간은 하위 호출을
포함해 서로 겹친다. **합산하지 않으며 계측 전체 시간을 처리량으로 사용하지 않는다.**

| 관측 | 원 경로 | 후보 |
| --- | ---: | ---: |
| 등록 `_current` 호출 / 포함 초 | 23 / 8.711773 | 23 / 11.466412 |
| guard `_snapshot` 호출 / 포함 초 | 없음 | 49 / 4.476849 |
| guard `check` 호출 / 포함 초 | 없음 | 48 / 4.556198 |
| 역할 감사 호출 / 포함 초 | 183 / 3.170605 | 183 / 3.134828 |
| `connect_runtime` 호출 / 포함 초 | 144 / 0.973235 | 144 / 0.979124 |

guard의 구조 점검과 지문 처리 비용이 관측됐다. 역할 감사는 양쪽 모두 유지됐으며
구조 점검 시간을 제거하면 얼마가 빨라질지 이 표만으로 계산하지 않는다.
수용된 guard의 검사를 약화하거나 앞선 보호 없는 후보의 개선 수치를 대신 사용하지 않는다.

## 다음 수정의 연결·트랜잭션 근거

변경하지 않은 원 경로의 별도 실제 advance에서 다음을 확인했다.

| 관측 | 결과 |
| --- | ---: |
| 물리 연결 / 감사한 실제 DB backend | 144 / 144 |
| job / market source / thermal 연결 | 72 / 24 / 48 |
| 역할 감사 | 183 |
| 연결당 역할 감사 분포 | 1회:120개, 2회:23개, 17회:1개 |
| driver `prepare_threshold` | 5 |
| 동일 policy 객체·authority 역할·DSN·principal 제공자 | 모두 참 |
| `_locked_job` 호출 | 초기 `_prepare` 1회, 현재 `_current` 23회 |

연결 정보 값·인증 자료·실제 backend ID는 공개하지 않았다. 이 관측은 실제 연결 재사용이나
prepared query의 속도 개선을 입증하지 않는다.

코드에서 `_current`의 작업 행 `FOR UPDATE`는 별도 job 연결의 트랜잭션 종료 때 풀리고,
그 뒤 authority snapshot·thermal snapshot·참조 검증이 실행됨을 확인했다.
전체를 하나의 읽기 전용 트랜잭션으로 묶거나 행 잠금을 더 오래 유지하는 후보는 이 경계를 바꾼다.

다음 한 단계는 **정확히 같은 authority 구성의 물리 연결을 원래 분리된 트랜잭션 사이에서
재사용할 수 있는지 작은 후보로 평가**하는 것이다. 범용 pool이나 교차 요청 캐시는 추가하지 않는다.
현재 `.connect()` 인터페이스와 `with`의 commit/rollback·잠금 해제 의미를 먼저 보존해야 한다.
현재 권한/identity·원 자료 조회·모든 감사와 tenant/Task/thread 수명도 유지한다.

첫 수용 기준은 같은 실제 step2/3의 순서 교대 비교에서 원 수치·UTC·원천1,824회/순서·감사183회와
원 트랜잭션/잠금 경계를 보존하고 유용하고 일관된 시간 감소를 관측하는 것이다.
그 뒤에만 실제 권한/identity 변경 거부·실패/rollback·취소·수명·정리와 관련 worker/HTTP 회귀를
수용한다. 물리 연결은 요청/등록 종료 때 닫고 미지원 구성은 기존 경로를 유지한다.
개선이 없으면 이 후보도 기각하며 권한 검사를 줄여 기준을 맞추지 않는다.

## 실행·보존 범위

| 실행 | 실제 결과 | guard 초 | 합산 최대 RSS bytes |
| --- | --- | ---: | ---: |
| 43121:0 | paired1검사 통과 | 84.454190366 | 984,354,816 |
| 30697:0 | 비용 계측1검사 통과 | 82.264026205 | 973,733,888 |
| 연결 footprint | durable terminal의 child0·1검사 통과 | 43.158786324 | 973,889,536 |

연결 footprint의 최초 exec handle은 문맥 축약 뒤 확인되지 않아 번호를 만들지 않았다.
실제 `started/terminal` 파일·시험 출력·관측/정리 hash로 결과를 확인했다.
합3개 진단 검사·guard209.877초다. 이전 guard37/primitive48을 재실행한 것으로 합산하지 않는다.

세 실행 모두5root·원본2,148항목·두 UI source/assets·512MiB/PID/합1GiB,
FD4→4와 소유 프로세스/PG/임시/passfile0·잔여 역할/schema0을 확인했다.
단일 PID 최대 RSS는141,316,096bytes다. 보호 서비스를 중단하지 않았다.

같은 원 계측 OFF64 CI는 반복하지 않았다. 새 연결 후보·통합 회귀·원64 정상은 미수용이다.
이후 순서는 변경 source의 독립 정상→hold→실제 HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용이다.
원 입력/actor/chunk1/조회·retry360/RSS 기준은 기존 계획을 따른다.
실제 농장 Run0·자료 권리/독립 현장/미래/비교 검증·G0–G4·새 Solar 배포·생산/경제 추천과
전체 완료일은 미완료/미정이다. 다음 후보의 통과 증거 전에는 완료 날짜를 제시하지 않는다.
전체 goal은 active다.

## 게시·최종 검토

50301:0에서 기존 수용의 source pin·현재 app260파일 불변·공개 helper/검사4개의 해시/문법,
세 진단 결과와 로컬 링크2,404개·원 API/worker 본문/단언을 확인했다.
두 UI의 개발 기록은 HTTP200·같은 JSON bytes/no-store로 게시했다.
기존 frozen HTML과 환기2,173파일을 보존했다. UI code/DOM/WebGL은 수정·재검사하지 않았다.
게시 guard2.674795440초·합 RSS894,074,880bytes·단일141,316,096bytes,
5root·FD4→4·소유 프로세스/PG/임시/passfile0이었다.

GitHub 확인에서 최근 진단 CI39211556239/원 정상 CI39210494752는 모두 종료된 실패였고
그 뒤 새 실행은 없었다. 이 기록의 비용 평가로 원64 정상이나 계산 중3D를 수용하지 않는다.
