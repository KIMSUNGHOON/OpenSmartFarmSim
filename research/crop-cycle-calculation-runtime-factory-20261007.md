# 검증 계산 결과의 명시적 runtime factory — 로컬 수용

2026-10-07 KST. 작은 명시 조립 소프트웨어 자식만 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-runtime-factory-reference-20261007.json)에 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·실제 명령/로그/source SHA와 정리를 기록했다.
새 operator loader·인증 route·새 HTTP 응답·전체166일/3D와 관문은 후속이다.

## 변경과 검토

[runtime](../backend/app/api_runtime.py)에 기본 None/숨긴 repr의 새 store/query factory를 추가했다.
새 flag가 false이면 둘 다 없어야 하고 true이면 둘 다와 기존 cycle 저장 선택이 필요하다.
누락·혼합은 해당 factory 실행과 JobStore 생성 전에 거부하며 비 callable은 dependency 구성에서 거부한다.
동일 jobs/farm authoring service/current principal의 exact 새 store/query만 받고 각각 `_binding()`을 호출한다.
선택 객체는 `calculation_cycle_crop_results`와 `calculation_cycle_crop_query`에 보존한다.
새 도메인 import는 조립 실행 시점에 두고 기존 API 조립을 유지했다.

정확성·가독성·경계·보안·비용을 검토했다. AST상 변경은 `ApiRuntimeDependencies`와 `ApiRuntime`뿐이며
`ApiRuntimeConfig`와 나머지 top-level 선언은 같다. 원 loader·선행 모델/조회/호환 수정을 포함한
**73 source SHA를 전후 보존**했다. 원 signed 이력을 재발행하지 않았다.

## 실제 검증

| 실행 | 실제 결과 |
| --- | --- |
| 새 flag만 켠 연결 전 거부 반례 | 1실패/0.78초·종료1, JobStore 호출 관측 |
| 선택 결속 보완 후 같은 사례 | 1통과/0.72초·종료0 |
| 선택/거부·세 import 순서 | 18통과/3.08초·종료0 |
| 첫 실제 SCRAM 정상 조립 | 1실패/12.60초·종료1 |
| 같은 실패의 위치 추적 | 1실패/12.58초·종료1 |
| 시험 준비 보완 후 새 파일 전체 | **19통과/15.54초·종료0** |
| 기존 API/runtime/loader·호환 회귀 | **136통과/30.53초·종료0** |

초기 SCRAM 거부는 시험에서 사전 준비해야 할 artifact directory가 없어서 발생했다.
실제 `job_store.py:1210`/`api_runtime.py:171`의 `FileNotFoundError`를 기록하고 fixture에서 준비했다.
제품의 누락 디렉터리 거부를 유지했다. 실패 로그·진단 plugin/출력 SHA도 보존했다.
최종 제품/test SHA가 같은 새19개와 선행136개, **고유155개 분할 검증**이며 반복 사례를 더하지 않는다.
전체 backend·단일155개 실행의 수용은 아니다.

실제 SCRAM에서는 정상 조립/새 객체 재구성·동일 jobs/farms/current principal과 네 독립 키를 확인했다.
구형/미타입 store·다른 jobs/농장·store binding 변경·미타입 query·다른 store query·query binding 변경·
중복 evidence key의 **9개 실제 거부 사례**를 같은 소유 DB에서 대사했다. pytest 사례 수와 구분한다.
조회되지 않은 입력/결과 resolver, parser/context·input/result 증명 발행·artifact QC/RHS·advance/게시를 금지했다.
조립 전후 jobs88/job_events88과 구형/새 작물 결과 행0개는 같고 FD12→12, 원 입력 SHA/mode/inode와
빈 server roots를 보존했다. 실제 작물 Run0건이다.

정상 조립0.164778초는 내부 객체 조립 관측이다. 새 HTTP 응답/요청 성능은 미검증이다.
세 시작 순서의 별도 Python에서 새 계산/store/query 모듈이 로드되지 않고 FD4→4였다.
실제 host 인증 네 규칙은 SCRAM이며 연결의 `used_password`/`require_auth`도 확인했다.
새 시험은 nice19·표본 최대 주 프로세스 RSS125,583,360bytes이며 PG 합산 peak가 아니다.
전체 실행의 소유 PG/schema/역할/비밀번호0개·PID/data 부재·임시 tree 정리를 확인했다.
계약은 실제 시험 뒤 수용 기록을 추가했으므로 영수증의 계약 SHA는 시험 당시 판본이다.

## 다음 한 단계와 보류

factory 자식만 체크한다. [별도 operator loader3 core파일](../contracts/crop-cycle-calculation-operator-loader-v1.md)은
새 config 판본/명시 flag·보호 파일·닫힌 형식과 dependency/plugin·실제 SCRAM 조립을 검증한다.
원 loader를 보존하고 기존 `--factory`와 사설 `OSSF_API_CONFIG`로 선택한다.
loader1–2집중시간+route/실제 TLS1–2시간의 **남은 작은 API 연결2–4집중시간 잠정**이다.
기존3–6시간 잠정은 이 분해와 factory 실적으로 갱신한다. CI·전체 등록 작기/3D·외부 자료/최종 날짜는 제외한다.

remote `353bffb`의 Backend에는 실제 진행 중인 분할이 있어 push를 보류했다.
앞선 [기존 설정 생성 호환 수정](application-operator-policy-compatibility-20261007.md)의 hosted Compose도 대기 중이다.
로컬 Docker가 없어 실제 Compose는 수행하지 않았다. 기존 CI 취소/재시도·설정/한도 변경은 없다.
전체 등록166일 prefix/저장 복원·API/같은 UTC3D 뒤 생과/수확 → 자원/구매 에너지 → Decimal 경제를 잇는다.
실제 품종 입력·국내 독립 자료·작물 Run0건, G0–G4 `not_assessed`이며 예측·추천/최종 완료일은 보류다.
