# 등록 수확의 보호된 reader 설정·별도 Python 복원 수용

2026-10-08 23:26 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 영수증](artifacts/crop-harvest-protected-factory-implementation-reference-20261008.json)에
원 명령/종료·445 source·실제 복원·권한 거부·자원/정리·실패 기록을 결속했다.
선행 [runtime·기본 App 수용](crop-harvest-runtime-assembly-implementation-20261008.md)은 유지한다.

## 구현과 사용자 확인 산출물

[보호된 reader factory](../backend/app/crop_harvest_runtime_factory.py)는 기존 operator의 private 파일 검사를
재사용한다. 명시 config/reader DSN/key/passfile과700 root를 읽고 캡처 bytes·권한·root identity를
생성 전후 검사한다. 설정과 오류에는 계수·자료 승인·관문 결정이 없다.
기존 `ApiRuntimeDependencies.crop_harvest_current_query_factory`에 선택하며 기본None은 유지된다.
[계약](../contracts/crop-harvest-protected-factory-v1.md)의 닫힌 JSON·경로/크기·소유권 조건을 따른다.

[새 시험](../backend/tests/test_crop_harvest_runtime_factory.py)의 소유 private bundle은 시험 전용이다.
기존 `load_calculation_api_runtime`이 실제 dependency module을 import하고 새 ApiRuntime을 구성했다.
같은 프로세스의 재조립이나 import만으로 복원을 대신하지 않았다. 실제 운영 계정/제품 CLI 증거는 아니다.
사용자는 영수증에서 두 정상 자식과 한 거부 자식의 원 종료·FD·원 DB counts·설정/코드 hash를 확인할 수 있다.

## 통과한 검증

| 대상 | 실제 범위 |
| --- | --- |
| 집중 시험 | 새45개(순수44·실제 SCRAM1)+기존 protected loader 순수56개=고유101개/21.43초·원 종료0. 기존 실제 DB1개 명시 제외 |
| 설정 거부 | 닫힌 필드/버전·중복/비정상 JSON·reader/DB·inline password·경로/크기/권한/link·소유 ACL 오류 주입·캡처 bytes/root/code 변경 |
| 실제 복원 | 정상 별도 Python2개·서로 다른 PID·실제 import/ApiRuntime·같은 SCRAM DB/reader/원 query/jobs/farm/principal. 각 FD4→4 |
| 실제 거부 | private key0644 상태의 별도 Python1개·고정 `operator_config_rejected`·종료0. 정상 권한으로 복구 |
| 원본 보존 | 보호 파일16개 hash/mode/inode·원 jobs88/events88·crop/harvest row0 유지·부모 FD12→12·조회/계산/행 생성/증명/등록0 |
| import | 새 Python에서 DB/network0·FD4→4·수확 query lazy loading |
| 정리 | 생성 private 파일14개·실제 passfile·양쪽 schema/role0·임시 PG/자식/경로 종료·445 source 불변 |

최종 실행23:24:31→23:24:53 KST, 준비부터22.071초였다. 정상 복원은 각각1.418/1.429초이며 HTTP 지연은 아니다.
원600초 상한·nice19·0.1초 감시205표본에서 primary RSS129,609,728bytes≤512MiB,
PG/controller/자식 포함 RSS 합321,531,904bytes≤1GiB였다. 공유 page가 중복될 수 있는 합이며 WSL 전체/production 용량은 아니다.
23:26:24 KST 별도 감사가 원 종료·445 source·세 core snapshot·실제 SCRAM/DB/비밀/프로세스 정리를 대사했다.
기존 runtime/route/OpenAPI source는 바꾸지 않았고 표준50 path/201 schema를 유지한다.

첫 실행은45통과 뒤 종료 정리에서 순수 fixture의 소유 sample passfile43개가 남아 원 종료1이었다.
실제 복원 본문과 DB/역할/PG 정리는 통과했으나 그 실행을 수용하지 않았다. 남은 시험 파일을 별도 제거하고,
`private_case`가 자신의 passfile을 `finally`에서 제거하도록 수정했다. 제품 구현은 같으며 원 실패와 제거 기록을 보존한다.

## 다음 한 단계와 남은 의존성

`crop-harvest-protected-factory` 자식과 선행 assembly 증거를 합친 `crop-harvest-runtime-factory` 부모만 체크한다.
API/runtime TLS·SDK·view/replay 부모는 미완료다. 다음은 같은 실제 SCRAM 부모의
HTTPS summary/원6행·분할/현재 권리·계정 거부를30초/2MiB·WSL 자원/정리와 함께 검증한다.
그 뒤 SDK→같은 UTC 표/3D→기후/물·양분/구매 에너지→Decimal 경제 연결로 진행한다.
기존 내부 page약23초는 HTTPS 수용이 아니다. 새 수확 경로의 전체166일 부하는 별도다.

이번 새 HTTP/TLS/SDK/3D·전체 suite/hosted CI/push·제품 CLI는0회다.
실제 품종 입력/환산 계수·국내 독립 농장 자료·실측 작물 Run0건, G0–G4 `not_assessed`이며
생산/미래 마진/추천·원격 Backend·구형 native25시간 원 종료 유실 hold를 유지한다.
현재 완료 시각은 위 작은 복원 작업의 실측이다. 후속 완료일은 실제 분해/검증과 자료 확보에 따라 갱신하며,
독립 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
