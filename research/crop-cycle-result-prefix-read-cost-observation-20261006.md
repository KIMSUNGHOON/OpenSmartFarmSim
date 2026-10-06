# 확정 과거 결과의 전체 검증 비용 — 부분 관측

2026-10-06 KST. **실제 소유 합성 결과 prefix의 조회 비용만 관측했다.**
전체166일 완료·현재 농장 권리/서버 custody·HTTP·3D 수용은 아니다.
[원 입력 조회](crop-cycle-input-read-context-implementation-20261006.md)의 개선 후에도
결과의 전체 검증이 공개 응답30초에 들어갈 수 있는지 확인하는 측정이다.

진행 중인 원166일(session81574)의 `HEAD`를 `2026-10-06T09:41:13.717394+00:00`에
한 번 캡처했다. 원 `_Files._load_prefix`로 그 HEAD의 불변 참조만 검증했다.
writer·lock을 열거나 원 파일/계산을 변경하지 않았다. 이후 추가된 commit은 관측에 포함하지 않는다.
원 terminal root는 아직 없었다. `yielded`를 완료로 바꾸지 않았다.

## 실제 범위와 비용

| 범위 | 실제 관측 |
| --- | ---: |
| 확정 prefix | 8,175commit·1,019,567걸음·26,831출력·5사건 |
| 원 input packet 열기/전체 preflight | 20.855223초 |
| 원 계산 문맥/격자 준비 | 9.100745초 |
| 원 모든 prefix checkpoint·출력/사건·수지 검증 | 73.707263초 |
| 같은 참조16,354 blob/262,417,701bytes의 byte/hash 재대사 | 1.033711초 |
| 원 index canonical 크기 | 1,378,708bytes |
| 참조 inventory canonical 크기 | 1,496,393bytes |
| 두 구조 크기의 합 | 2,875,101bytes |

바이트 측정은 SHA와 크기만 다시 대사했다. 원 수학 검증·서명 증명·현재 농장 권리·
전체 HTTP 지연을 측정한 값으로 확대하지 않는다. 순수 참조 artifact는 농장에 등록해
서버가 계산한 custody trace도 아니다.

프로세스는 nice15·RHS0·FD4→4·peak RSS64,843,776bytes였다.
import/준비/두 관측부터 receipt 저장 직전까지104.930602초이며 종료/저장 시간은 제외했다.
기존 nice10 계산과 동시였고 OS cache는 통제하지 않았다.
원53 source hash를 관측 전후 대사했다. 별도 서버·DB·browser나 의존성을 추가하지 않았다.
이 관측을 저사양 기기/전체 작기의 성능 또는 독립 농장 정확도로 표시하지 않는다.

## 판단과 다음 작은 단계

입력 비용을 제외한 결과 검증만 이미73.71초여서 전체 결과를 매번 같은 방식으로
검증하는 경로는30초 수용 전에 개선해야 한다. [결과 검증 영수증 계약](../contracts/crop-cycle-result-evidence-v1.md)은
원 terminal artifact의 전체 검증과 현재 byte 대사/요청 page 읽기를 분리한다.
새 키 서비스/DB 표/stack 없이 서버 제공 키의 별도 증명부터3 core파일로 검증한다.

개발 착수는 기존 terminal artifact/입력 조회 수용과 이 비용 근거에 의존한다.
자작 작은 정상/hold terminal 사례로 primitive를 개발하는 동안 원 전체166일 계산은 계속한다.
실제 전체 결과 발행/크기·typed result reader·현재 farm/Scope/등록/권리·원 server trace·
30초/2MiB/API/같은 UTC3D는 별도 후속 수용이며 전체166일 실제 종료 증거가 필요하다.
참조 영수증으로 농장 계산 이력을 만들어 내거나 v1 private type을 위조하지 않는다.

실제 native CLI `gpt-6.1-sol / xhigh` 문맥과 invocation·source/raw/log hash·종료0은
[불변 receipt](artifacts/crop-cycle-result-prefix-read-cost-reference-20261006.json)에 기록했다.
전체 작기/복원 부모와 G0–G4는 미수용이며 생과·자원·경제의 구현 순서는 유지한다.
