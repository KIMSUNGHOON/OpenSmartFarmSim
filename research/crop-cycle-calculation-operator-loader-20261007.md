# 검증 계산 결과의 운영 설정 로더 — 로컬 수용

2026-10-07 KST. [계약](../contracts/crop-cycle-calculation-operator-loader-v1.md)의 별도 로더와
명시 operator-runtime 부모를 로컬 소프트웨어 범위에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-operator-loader-reference-20261007.json)에 실제 native CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·명령/종료/로그/source SHA와 정리를 기록했다.
새 인증 HTTP·전체166일 등록 경로/3D·G0–G4는 후속이다.

## 변경과 검토

[별도 로더](../backend/app/calculation_operator_config.py)는 새 config 판본과 명시 bool을 읽는다.
활성 설정에는 기존 cycle flag도 필요하며 schema/정책 오류는 trusted dependency plugin import 전에 거부한다.
원 보호 파일·경로·JSON helper와 typed config/dependencies/runtime을 사용하고 입력 JSON을 다시 쓰지 않는다.
기존 `--factory app.calculation_operator_config:api_service`와 사설 `OSSF_API_CONFIG`로 선택한다.
기존 default entrypoint/Compose·서비스·한도와 원 loader/상수/전역을 변경하지 않았다.

정확성·가독성·구조·보안·비용을 검토했다. 새 로더만 조립을 담당하고 기존 파일 검사를 재사용한다.
별도 로더가 필요한 근거는 원 operator_config.py가 기존 서버 서명의 file-helper dependency라는 점이다.
이 파일과 선행 계산/저장/조회/공개 투영·runtime/회귀를 포함한 **75 source SHA를 전후 보존**했다.
설정 plugin은 운영자가 신뢰한 코드다. 정책 오류의 import 전 거부는 임의 plugin의 내부 DB 접근 금지 증명이 아니다.

## 실제 검증

| 실행 | 결과 |
| --- | --- |
| 원 로더에 새 설정 전달 RED | 2실패/0.75초·종료1 |
| 별도 로더의 명시 false/true | 2통과/0.80초·종료0 |
| 형식·보호 파일·오류·세 import 순서 | 56통과/3.07초·종료0 |
| 첫 실제 SCRAM 조립 | 1실패/12.67초·종료1 |
| 시험 속성명 수정 뒤 새 파일 전체 | **57통과/15.45초·종료0** |
| 기존 API/runtime/loader·설정 생성 회귀 | **155통과/44.99초·종료0** |

첫 SCRAM 시험은 실제 조립 이후 시험의 `binding.authority` 속성 참조에서 실패했다.
실제 선언 `binding.input_authority`로 고쳤고 제품 hash는 바꾸지 않았다. 실패 로그·자원 정리를 보존했다.
최종57개와 회귀155개는 같은 제품/시험 SHA의 **고유212개 분할 검증**이다.
반복 기본 시험/56개를 더하지 않으며 단일212개·전체 backend 수용으로 표시하지 않는다.

새 판본/필수 flag·기존 cycle prerequisite·알 수 없는 필드/중복 JSON·nonfinite·크기/UTF-8·factory reference,
보호 파일 mode/parent/symlink/hardlink/FIFO·키 길이/누락·ACL 검사와 실제 읽기 중 네 변경을 거부했다.
오류/비밀 비노출·FD 복원, optional authored key/ContentAccess와 env entrypoint를 확인했다.
구형 loader는 새 flag를 false/true 모두 계속 거부한다.
별도 Python 세 시작 순서에서 새 계산/store/query 모듈은 로드되지 않고 FD4→4였다.

실제 SCRAM과 보호 TLS 파일을 통해 같은 jobs/farm/current principal의 exact 새 store/query를 조립·재구성하고
env service를 확인했다. 네 키는 독립이며 parser/context/QC/RHS·증명 발행/advance/게시를 금지했다.
jobs88/events88·구형/새 작물 결과0행은 같고, 원 설정/DSN/키/TLS/입력 SHA·mode·inode와 FD12→12를 보존했다.
새/구형 server root는 비어 있다. 현재 시험의 trusted plugin은 시험 프로세스 내 코드이며 별도 제품 프로세스 배포 증거가 아니다.
조립0.176545초는 내부 객체 구성 관측이며 HTTP 성능이 아니다.

nice19·주 시험 프로세스 표본 최대 RSS130,621,440bytes다. PG 합산 또는 WSL 전체 peak가 아니다.
실제 host 인증4규칙은 SCRAM이며 연결의 `used_password`/`require_auth`를 확인했다.
새 전체 시험과 회귀의 소유 PG는 각각1개/3개 순차 실행했고 schema/role/passfile0·PG PID/data·임시 tree를 정리했다.
계약의 수용 절은 시험 후 추가했으므로 영수증 계약 SHA는 시험 당시 판본이다.

## 다음 단계와 남은 의존성

[인증 route/OpenAPI → runtime/실제 TLS](../contracts/api-crop-cycle-calculation-transport-v1.md)의
두 자식으로 새 API 응답을 연결한다. route5파일·runtime/TLS3파일의 실제 검증 범위를 반영해
남은 작은 API 연결을 **4–6집중시간 잠정**으로 갱신한다. 이전1–2시간은 이 분해로 대체한다.
이후 client/동일 UTC3D와 전체166일 등록 prefix/복원 비용을 확인한다.
생과 수확 → 물/양분/구매 에너지 → Decimal 경제 연결과 독립 자료 확보는 후속이다.

remote `353bffb`는 C0/웹/작성 PG 성공·앱 config 실패이며 Backend는2분할 성공/2진행/2대기 중이었다.
현재 소스 push는 없으며 CI 취소/재시도·설정/한도 변경도 없다.
[기존 앱 설정 생성 호환 수정](application-operator-policy-compatibility-20261007.md)의 hosted 수용도 남아 있다.
로컬 Docker가 없어 실제 Compose는 수행하지 않았다.
실제 품종 입력·국내 독립 자료·작물 Run0건, G0–G4 `not_assessed`를 유지하며 예측·추천과 최종 제품 날짜는 보류다.
