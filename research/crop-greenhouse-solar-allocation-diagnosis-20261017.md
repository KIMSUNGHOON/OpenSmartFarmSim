# 일사 API·작업자 할당 분리 진단 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-allocation-diagnosis-20261017.json) · [앞선 동시 실행 hold](crop-greenhouse-solar-unpaused-resource-hold-20261017.md) · [연구 실행기](crop-greenhouse-solar-unpaused-probe.py).

**분리 진단3개를 완료했다. 독립 API/worker 동시 실행과 새 Solar3D는 미수용이다.** 기존 조립109검사/보호 HTTP355검사는 유지하며 이번 진단을 새 기능 검사 수에 더하지 않는다. 실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의 문맥·출력·실행/종료 증거를 기록했고 재귀 CLI는 실행하지 않았다. 제품 코드는 변경하지 않았다.

## 관측과 검증

| 구분 | 실제 실행 | 관측 및 통과 범위 | 전체 보호 scope 최대 RSS bytes |
| --- | --- | --- | ---: |
| 워커 단독 | 27943:0 | 같은64걸음 합성 입력에서 초기 경계 포함 예산9→8걸음/확정 checkpoint. 실제 SCRAM·생성자 retained Python 할당1,832bytes·최대 DB 연결4개 | 1,013,616,640 |
| API 단독 | 24478:0 | 앞선 별도 워커가 종료된 뒤 같은 checkpoint를 실제 설정 API/SCRAM/TLS로 조회. 진행/요약/sample3건200/no-store·sample2개. 조회 계산/CLI/SQL 변경0 | 1,068,240,896 |
| 클라이언트 import 분리 | 55261:0 | 두 fresh 프로세스의 driver import RSS21,209,088→16,146,432bytes. 기능/동시 실행 수용이 아닌 진단 | 815,325,184 |

API 조립 직후 retained Python 할당은15,629,925bytes였다. 상위 할당 위치는 import·Pydantic field/schema 생성이었다. GET 뒤 retained 할당과 import도 관측했다. 이 값은 메모리 누수나 제거 가능한 중복을 증명하지 않는다. 양쪽에서 관측된 최대 열린 DB 연결은 각각4개이며, 연결별 RSS 상위값을 서로 다른 시점끼리 더해 동시 최대치로 쓰지 않는다.

깊이1 `tracemalloc`은 CPU와 메모리를 추가로 사용한다. 위 API/워커 RSS를 일반 배포 용량이나 무계측 동시 실행 성공으로 외삽하지 않는다. 워커 계측의 잘못된 경계 예산 기대값과 첫 API 계측의 `running` 기대값은 각각 초기 경계0 포함과 공개 상태 `simulating`에 맞춰 수정했다. 실패 두 건은 보존하고 진단 수용에서 제외했다.

## 작은 수정과 실제 재검증

별도 시험 driver의 HTTP/TLS import 비용을 분리 관측한 뒤, HTTPS 조회 클라이언트를 이미 해당 모듈을 사용하는 API actor로 옮겼다. 부모는 프로세스 소유/정리를 담당하고 실제 POST 접수 뒤 별도 자동 워커를 기동한다. 원 입력64걸음·정확한 configured API·검증된 TLS·10초 조회·두 전진 prefix/원 UTC·최종 원 수치 대사 단언을 유지했다. worker 장벽/수식/권리/역할 감사/한도는 바꾸지 않았다. 이 배치는 독립 브라우저/client 프로세스 수용을 대신하지 않는다.

최초 실행31789:1은 이동한 함수 이름 `http`가 모듈과 충돌해 실패했다. `request_http`로 수정했다. 후속2179:1은 **합 RSS1,082,724,352bytes**에서 종료됐다. import 절감은 실제 동시 최대치 절감이나 성공을 보장하지 않았다. 연구 실행기는 계속 미수용이며 기본 pytest 성공 집합에 넣지 않았다.

## 실패 위치 추가 관측과 다음 한 단계

별도95939:1에서 추적 도구의 큰 heap 비용 없이 소유 `/proc` identity/RSS·연결 열기/닫기·기존 작업자 호출 시각을 기록했다. SQL/DSN/매개변수/입력 원문은 기록하지 않았다. 합 RSS1,082,331,136bytes에서 종료됐다.

이 실행의 마지막 API 요청은 접수 POST였고 GET 시작은0개였다. 워커의 첫 `advance` 시작도 관측되지 않았다. 따라서 이 실패를 API GET과 수치 계산의 중첩 탓으로 단정하지 않는다. `_before` 종료 뒤에도 단계명은 다음 계측 호출까지 유지된다. `_adopt`는 별도 계측하지 않았으므로 그 이름만으로 `_before` 안의 실패라고 좁히지 않는다.

다음 작은 작업은 **API가 idle인 상태의 첫 custody 채택/current 검사에서 실제 연결 중첩 호출 위치를 분리**하는 것이다. 저비용 관측으로 `_adopt`와 연결 생성 call site를 확인한 뒤 회수 수정의 근거를 정한다. 수용하려면 같은 전체 설정·독립 unpaused 워커의 정상/hold/취소·현재 권리·전진 prefix/원 UTC/수치·자원/원본 보존을 통과해야 한다. 그 뒤 typed 웹/같은 UTC3D→사용자 적용 순서다. 기존 역할·현재 권리 검사를 생략하는 수정은 채택하지 않는다.

## 보존·사용자 산출물·남은 의존성

8개 실행 모두 보호5root/동적 자식·원본2,148항목·기존 두 서비스/source/assets를 보존했다. FD4→4·소유 process/PG/passfile/임시 PG 잔여0을 확인했다. 512MiB/PID·합1GiB는 유지했다. 실제 실행기/로그/terminal/추적 해시는 기계 증거와 사설 상태에 보존한다.

두 사용자 화면의 개발 진행 feed에 이 진단과 동시 실행 hold를2026-10-17 10:43:09KST로 게시했다. 실제91040:0에서 양쪽 HTTP200/no-store·원 feed bytes, 기존 HTML과 환기 frozen2,173파일 보존을 확인했다. 이번 DOM/WebGL·전체 CI·새 Solar3D 사용자 배포는 실행하지 않았다. 실제 지역/품종/시설 입력과 독립 농장·시장 검증 자료는 계속 외부 의존성이다. 실제 농장 Run0·G0–G4 `not_assessed`·`rights_or_gate_approval=False`, 생산/경제 예측·추천 보류와 goal active를 유지한다. 전체 완료일/남은 집중 시간은 자료와 후속 실행 수용이 없어 미정이다.
