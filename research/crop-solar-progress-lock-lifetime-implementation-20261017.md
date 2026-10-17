# 진행 조회의 custody 잠금 수명 — 2026-10-17

[계약](../contracts/crop-solar-progress-lock-lifetime-v1.md) ·
[기계 증거](artifacts/crop-solar-progress-lock-lifetime-implementation-20261017.json) ·
[실제 원인 관측](crop-solar-worker-termination-diagnostics-20261017.md).

## 실제 관측과 수정

[진단 CI39036105645](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39036105645)는221.256초·worker1/API-15로 끝났다.
마지막 확정은4/64·2026-10-01T00:00:08.123456Z, 실제 반환은 **attempt1/queued/solar_execution_busy**다.
confirm→custody open의 Pending과5초 재시도 종료를 원 이벤트/예외 위치로 대사했다.
API는 수집된14응답에서202/200/503과 accepted prefix/page를 반환했다.
이 실행으로 이전 예상 밖 prefix 상태 오류를 해결했다고 주장하지 않는다.

sourcef6b3bde의 변경 제품 파일은 `crop_greenhouse_solar_execution_query.py` 하나다.
기존 `_checkpoint`가 snapshot을 읽은 뒤 후속 `_terminal`·현재 농장/권리·DB/직렬화 검사까지
custody 잠금을 유지했다. 이제 `_capture_checkpoint`의 일관된 snapshot 읽기 뒤 잠금을 닫고,
후속 검증이 끝나면 다시 짧게 열어 원 progress를 대사한다.

잠금을 푼 동안 원 root/intent/proofs/artifact 디렉터리 FD를 복제해 보존한다.
다시 연 디렉터리의 dev/inode를 대사해 같은 내용의 디렉터리 교체도 거부한다.
정상 signed descendant 전진은 원 ancestry를 검증한 뒤 Pending으로 응답을 폐기한다.
종료 대사 잠금 충돌도 Pending이다. 변조·권리 철회·fork/rollback은 원 거부를 유지한다.
조회는 모델/CLI 실행·checkpoint 확정·DB/결과 게시를 하지 않는다.
작업자·수식·입력·64걸음/chunk1·조회 주기·5초 재시도·360/600초·RSS 상한을 바꾸지 않았다.

## 실제 통과 검증

- 7500:1에서 후속 검증 중 별도 open file description의 실제 custody 잠금 획득이 막혀2실패했다.
- 90202:0에서 잠금 해제·최종 재확인의 실제 충돌을 **2검사**로 통과했다.
- 76653:0에서 미리 실제 모델로 만든 signed descendant HEAD 게시의 Pending,
  HEAD 손상과 같은 내용의 디렉터리 교체 거부를 **3검사**로 통과했다.
  이 결정적 경합 시험은 독립 unpaused 실행/처리량의 증거가 아니다.
- 66181:0에서 원 count/UTC/최초 기록·heartbeat/새 attempt·unconfirmed/real lock unavailable,
  읽기 권한/늦은 권리·취소·직렬화 뒤 철회·none/missing의 **6검사**를 통과했다.
- 55637:0에서 정상/수치 hold의 원 값·UTC·결과 연결·성공 게시1/hold 게시0·조회 계산/SQL 변경0의 **2검사**를 통과했다.
  별도 fresh-process 시험을 새로 실행한 것으로 세지 않는다. 따라서 **고유13개**다.
- 12100:0에서 `_checkpoint` 외 기존8개 메서드의 AST, worker/5초 재시도·원 prototype 불변과
  application 변경 파일1개를 대사했다. 모든 통과 배치의 실제 query source SHA도 최종 파일과 일치한다.

최종3배치는151.615/191.832/141.016초·합 RSS1,055,932,416/1,057,746,944/1,068,773,376bytes였다.
새5root·원2,148항목·frozen 소스/자산/두 UI·512MiB/PID·합1GiB,
감독FD4→4·실제 role/schema0·소유 비좀비/PG/임시/passfile0을 유지했다.
이 수치는 개별 소프트웨어 시험이며 독립 API/worker/브라우저의 WSL 동시 용량 수용이 아니다.

## 다음과 남은 의존성

[trace-OFF 원 정상 CI39037993173](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39037993173),
sourcef6b3bde가 진행 중이다. 원64걸음/start1/CLI0·attempt1·두 전진 prefix·원 값/UTC·원 후검사·정리를
모두 통과하기 전 정상 기능으로 수용하지 않는다.
컴포넌트만 로컬 수용이며 full backend·독립 hold/취소·실제 계산 중 WebGL·WSL 용량·S3/S4·새 Solar 적용은 남았다.
실제 품종/독립 농장/자료 권리·G0–G4와 전체 완료일은 미완료/미정이며 전체 goal active다.

최신 진행 기록은91624:0에서 두 주소HTTP200·no-store·원 HTML/source·5root/원본·FD/소유 정리를 확인해 게시했다. 브라우저/디자인 재검사는 하지 않았다.
