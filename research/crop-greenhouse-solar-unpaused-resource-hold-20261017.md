# 일사 독립 작업자·API 동시 실행 자원 보류 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-unpaused-resource-hold-20261017.json) · [미수용 검증 prototype](crop-greenhouse-solar-unpaused-probe.py) · [수용된 설정/API 조립109검사](crop-greenhouse-solar-execution-assembly-implementation-20261017.md).

직접 구성한 실제 API와 별도 자동 worker의 같은64걸음 합성 입력·SCRAM/TLS·전진 prefix/원 값/UTC를 검증하는 실행기를 작성했다. 작업자에는 시험용 중단 장벽을 두지 않았다. 최초 두 실행기 오류는 누락된 bootstrap import와 `http` 이름 충돌이었으며 수정했다. 이 두 실패를 기능 수용으로 계산하지 않는다.

이후 v3–v6은 모두 합 RSS 관문에서 종료돼 **동시 실행 미수용**이다.

| 원 session | 변경/실행 조건 | 관측 합 RSS bytes |
| --- | --- | --- |
| 23328 | 원 malloc·4걸음 청크·즉시 조회 | 1,091,862,528 |
| 79217 | 지원되는 pymalloc 비교 | 1,089,429,504 |
| 86684 | 기존 제품과 같은 응답 후10초 조회·1걸음 청크 | 1,080,832,000 |
| 54708 | 미사용 bootstrap graph 참조 제거·시작 전 GC | 1,079,803,904 |

512MiB/PID·합1GiB를 올리지 않았고, 원5root/동적 자식·원본2,148/두 사용자 서비스·키/역할/현재 권리·모델/매개변수/타입 검사를 유지했다. 각 감독은 소유 scope를 정리했고 FD4→4·소유 process/PG0을 확인했다. v5/v6에서 남은 알려진 시험 passfile 각4개는 PID/start/boot 종료와 파일 소유권·모드·경로를 확인한 뒤 제거했다. controller의 임시 PG 디렉터리 제거 뒤 잔여0도 확인했다. 이 정리는 실패 실행을 통과로 바꾸지 않는다.

allocator import 차이는 약1.6–1.7MB였고 실제 동시 실행을 통과시키지 못했다. controller handoff 축약 진단도327,680bytes만 회수했으므로 감독/worker dispatcher를 재설계하는 근거로 채택하지 않았다. import RSS나 standalone API 수용을 동시 운영 용량으로 외삽하지 않는다. 보존할 서비스의 중지·재시작·교체·누락도 하지 않았다.

미수용 실행기는 기본 pytest 성공 집합에 넣지 않고 재현 가능한 연구 prototype으로 보존한다. assert와 같은 전체 configured API/실제 worker·두 전진 prefix/원 값·UTC·현재 권리·자원 관문은 유지했다. 자동 시험으로 승격하거나 runtime/3D 부모 체크를 완료하려면 실제 통과 증거가 먼저 필요하다.

다음 안전한 작업은 **owned API/worker의 constructor·조회 할당을 각각 분리 계측**하고, 현재5root/동적 자식과 같은 한도에서 회수 가능한 메모리에 근거한 작은 수정 하나를 검증하는 것이다. 추측으로 반복 기동하거나 입력·판본·권리·운영 조립을 채택하지 않는다. 자료·모델·권리·의존성/관문 증거가 부족하거나 충돌하면 hold를 유지한다.

설정·API 조립109검사와 직전 보호 HTTP355검사는 유지하지만 독립 unpaused worker·사용자 Solar3D·전체 CI·실제 농장/G0–G4·생산/경제/추천은 미완료다. 전체 goal은 active이며 완료 날짜는 미정이다.

두 UI의 개발 기록을2026-10-17 10:15:59KST로 게시했다. 원 session70605 종료0에서 HTTP200/no-store·동일 bytes(SHA 7d2a8ead3c83e8f95cec69d2df42d50762abf26900cfc8960b4043ad86e925eb)와 기존 두 HTML/환기 frozen2,173파일 보존을 확인했다. DOM/WebGL은 재실행하지 않았다.
