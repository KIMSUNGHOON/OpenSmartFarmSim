# 공동 작물·기후 결과의 같은 세션 현재 조회 수용

2026-10-10 06:40 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
core `475eb19f7480a3312660b536ce24b6733596c61b`의 reader87줄·tests223줄·계약29줄을 로컬 수용했다.
[검사 기록](artifacts/crop-climate-joint-current-query-reference-20261010.json)은29,681bytes,
SHA256 `8dde76d089cb46050b59e4c097bb14be05519cee3d80abd661023c7a416802a7`다.
실제 metadata 도구1b0097에서21:20:51.554Z의 모델/강도와 원 LF SHA
`f31e9dbb4b09513aa86bd4fb1b7d08b4e054c2f70e24574d88cd37298e4d8d41`를 확인했다.
새 제품 runtime CLI 실행이나 관문 해제 증거가 아니다.

## 같은 원 결과를 반환하는 경계

[현재 조회 계약](../contracts/crop-climate-joint-current-query-v1.md)은 기존 store `_read`와 원 artifact reader를 재사용한다.
같은 custody 잠금/현재 권리 안에서 원 summary/페이지를 읽고 닫힌 DTO로 투영·직렬화한다.
투영 직전과 직렬화 뒤 DB row·컬럼/HMAC·원 record/packet을 대사하며,
reader의 HEAD/root/header와 custody의 현재 입력/자료 권리·원 progress를 재확인한 뒤 반환한다.
새 authority/key/서비스를 만들지 않고 조회 계산·새 행·자료 채택·관문 승격을 실행하지 않는다.
반환값은 원 typed API의 UTF-8 bytes 또는 현재 계정에 없는 결과의 None이다.

소유 합성32초/16걸음·108상태·3sample/3event의 실제 SCRAM 결과를 사용했다.
정상 summary/sample/event18,904/35,046/73,566bytes가 원 투영 응답과 정확히 같았다.
별도 exec PID2010462도 같은3응답 SHA를 읽고 review 철회를 거부했다. 종료 뒤 PID는 없었다.
작은 사례의 조회는 각각4.799/4.754/4.777초였다. 실제 HTTP·전체 작기 성능으로 외삽하지 않는다.
hold는 원 마지막 확정값·실패 시각·checkpoint 없음·실패 경계 이전 페이지를 유지한다.

## 실제 통과한 검사

같은 core3/source1,763에서 순수4개와 실제 SCRAM6개, 고유10개를7그룹으로 순차 통과했다.

| 그룹 | 고유 검사 | 원 exec → terminal | 실제0 / guard초 |
| --- | ---: | --- | ---: |
| 정확한 초기화 store 타입/조립 | 4 | 13634 → 32aab4 | 1.839 |
| 정상 원 wire·별도 exec SCRAM | 1 | 18165 → 57b1fe | 94.938 |
| 원 hold·마지막 확정·실패 prefix | 1 | 42040 → 67ba66 | 74.539 |
| 투영 중 현재/늦은 철회 | 1 | 40427 → 29a78a | 91.699 |
| 직렬화 뒤 현재/늦은 철회 | 1 | 17507 → 4e16d2 | 91.655 |
| 늦은 DB 기록/서명/컬럼·원 페이지 변조 | 1 | 5615 → b6c09b | 61.009 |
| 한도/농장/tenant/조립·미존재·페이지 cursor/2MiB | 1 | 24651 → 5319e0 | 58.504 |

합474.184초다. 두 철회 그룹은 각각 자료 권리/review/읽기 scope/농장 source4종×3view의
조기12·늦은12회 거부를 확인했다. 같은 조기 조건을 두 번 실행한 것을 별도 고유 검사로 세지 않는다.
늦은 DB 서명/컬럼/recorded_at/미존재는 lookup fault injection이며 불변 SQL 행을 수정한 시험이 아니다.
페이지 변조는 직렬화 뒤 실제 소유 artifact 파일에 공백을 추가해 원 digest 불일치를 만들고 반환 거부/원 bytes 복원을 확인했다.
조회의 Context/start/restore/advance/RHS/step/event/UTC binding8종 호출은0이며 fixture의 최초 계산/검증은 제외한다.
원본2,148항목·기존 UI source/assets/보호3PID·frontend200·controller FD4→4를 보존했다.
실제 PG/schema/role/passfile/임시 경로와 소유 프로세스를 정리했다.
0.25초 관측의 최대 단일PID/소유+명시 보호 트리 RSS 합137,621,504/600,657,920bytes는512MiB/1GiB 안이다.
최종 core/fixture pin·민감 필드 검사·관련 문서의 로컬 링크1,709개와 diff whitespace 검사를 통과했다.

## 후속으로 확인한 시험의 실행 환경 차이

CI 선언은 Python3.12.13, 현재 WSL interpreter는3.12.3이다.
앞선 순수 projection fixture는 현재 환경에서 계산한 root를 과거3.12.3 packet의 고정 root와 비교했다.
`platform.python_version`만3.12.13으로 fault injection한 원70221→2ed98b는 fixture root 불일치로 실제1을 반환했다.
이는 실제 Python3.12.13 실행이나 hosted 실패를 관측한 검사가 아니다.
첫 private 재현82096→b24042의 argv slicing 오류는40개 모두 deselected/실제5였고 재현 근거로 사용하지 않았다.
원 로그/종료/정리와 스크립트 판본을 보존한 뒤 올바른 인자로 재현했다.

core `3829a5842d4de17bb199f334a315f829c3307dee`는 시험 파일만 수정했다.
현재 native context/UTC/root·소유 입력 evidence로 순수 type fixture를 만들며 과거 packet은 농장 참조의 형식 template로만 쓴다.
farm/custody는 **미등록 type fixture**이며 해당 응답이 현재 HMAC/권리 인증을 통과했다고 주장하지 않는다.
과거 원본 packet/artifact와 계산·projection·실제 store 코드, 운영의 runtime identity 관문은 바꾸지 않았다.
실행 환경이 다른 실제 서명 결과의 운영 조회를 승인하는 호환성 변경이 아니다.

원78491→55b0c4 실제0/4.401초에서 순수39개를 통과했고 같은 재현96233→0b6f05도 실제0/2.101초·1통과였다.
재현1개는39개와 겹치므로 더하지 않는다. 새 identity 검사도 fault injection 범위임을 기록한다.
실제 DB2개와 cleanup의 AST는 원 코드와 같았으며 재실행하지 않았다.
current query10개 검사는 이 fixture 변경 전에 실행했다. 그 core3는 동일하고 바뀐 helper는 해당 검사에서 호출하지 않는다.
순수 projection 최종 두 그룹의 source는 같고 앞선 source와의 차이는 그 시험 파일1개뿐이었다.

## 다음 단계·사용자 화면·남은 의존성

다음은 `crop-climate-joint-http-route`의 core4: 새 route·기존 api·해당 tests·HTTP 계약이다.
같은 jobs/farm/principal 조립의 인증 GET, 엄격 query/본문·조기 연결 종료,
summary/samples/events·no-store/2MiB·반환 전 계정 재검사와 실제 SCRAM/HTTPS·늦은 철회/원량/정리를 수용한다.
기존 route95줄과 이번 작은 current read4.8초를 근거로2–3집중시간 잠정이며 연속 작업/새 계약 오류 없음 조건이다.
HTTP 비용·실제 runtime/3D 수용 뒤 후속 일정을 갱신한다. CI 대기·전체 작기/자료 확보·최종 UI/U3 날짜는 포함하지 않는다.

**http://localhost:5173/** 은 계속 완료 합성166일 생장·수확의 저장 재생이며 새 joint/실시간 U3는 미연결이다.
새 HTTP/runtime/브라우저/WebGL, 기존233/82/993 전체 회귀·전체166일 계산/writer는 실행하지 않았다.
실제 품종 입력/농장 crop Run/국내 독립 자료0건·G0–G4/생산/미래 마진/추천 hold를 유지한다.
온실 경계·forcing·물/양분·구매 에너지·사용자 실행/Decimal 경제와 독립 자료 확보는 남아 있다.
운영 기반 d19f7c0 고정과 전체 goal을 유지한다.
마지막 실제 조회에서 원900288b의 CI5종은 모두 success로 종료했고 Backend37981057415의0–5/집계도 success였다.
이번 local core/fixture 변경의 hosted 수용은 해당 커밋의 새 실행으로 따로 확인한다.
