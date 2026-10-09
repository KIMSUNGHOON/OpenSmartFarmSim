# 공동 작물·기후 결과 등록과 현재 조회의 로컬 수용

2026-10-10 05:44 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
core `2c0f30519342cf9c49a705594b1493f42af408f6`의 새 store310줄·tests326줄·계약51줄을 구현했다.
[불변 검사 기록](artifacts/crop-climate-joint-result-store-reference-20261010.json)은551,161bytes,
SHA256 `ba17b03fca1e7f1a7291fb8e282a0c7ca0194a086b5909452c9f0e1e4a6d4344`다.
native turn_context20:19:46.896Z의 원 LF 포함 SHA는
`a6fa2bce775c180beef6cd5642cfd682ddb949afcdb9fc1a8adae58de9869392`이며 실제 metadata 도구5635b3에서 확인했다.
개발 CLI 증거이며 새 제품 runtime CLI 실행/관문 승인 증거가 아니다.

## 구현과 수용 범위

[계약](../contracts/crop-climate-joint-result-store-v1.md)에 따라 같은 tenant/farm/crop/batch/zone,
원 등록 job·source/context/마이크로초 UTC/evidence·intent/HEAD/proof/root를 별도 ID/domain/HMAC으로 결속한다.
명시 새 flag=True·authority·전체 grant 감사가 필요하다. 이미 종료된 completed/hold만 원자 등록한다.
같은 bytes의 재시도는 최초 recorded_at을 유지하고, 다른 결과의 같은 판본은 Conflict다.
현재 권리와 원 서명 이력/페이지를 조회 전후 확인한다. 계산 함수는 조회 경로에서 실행하지 않는다.

실제 FarmAuthoringService와 소유 합성32초의16걸음·3sample/3event를 사용했다.
원 metadata32,175bytes·모든 SQL 참조 컬럼·원 root251,743bytes와 UTC를 대사했다.
별도 exec PID1973421은 실제 SCRAM DB에서 원 bytes/최초 시각·두 페이지·summary를 재조회했고 review 철회를 거부했다.
parent G0–G4를 승인하거나 실제 품종/작기·생산/구매 자원/미래 마진/추천을 수용한 검사가 아니다.

## 실제 실행과 실패 경계

7그룹을 순차 실행한 고유9개 검사다. 그룹마다 소유 PG/schema/role/passfile/임시 경로·프로세스 정리,
controller FD4→4, 원본2,148항목/source1,753·기존 UI source/assets/3개 보호 PID·frontend200을 확인했다.
모든 제품 store/contract bytes는 같다. normal 뒤 **아홉 번째 검사만 test 파일 끝에 추가**했다.
원8개 검사 파일의 byte prefix SHA가 원 guard pin과 일치함을 확인했으며 첫 그룹의 최종 test 파일 SHA까지 같다고 주장하지 않는다.

| 그룹 | 고유 검사 | 원 exec → 실제 terminal | 실제0 / guard초 |
| --- | ---: | --- | ---: |
| 정상 등록/재시도/원 페이지/summary/fresh SCRAM | 1 | 64000 → e8e9c4 | 116.346 |
| 기본 False·미생성/미완료·key/tenant·DB 잠금 | 2 | 57435 → 70cc22 | 68.174 |
| commit 전/후 쓰기 권리 철회 | 2 | 48880 → c3175a | 84.994 |
| 현재 input/review/read/farm-source 철회·잘못된 페이지 | 1 | 24586 → 6273c8 | 71.036 |
| 유효 HMAC을 다시 만들어도 혼합/변조 거부 | 1 | 94592 → 63509f | 54.922 |
| 원 hold/checkpoint/last_confirmed/UTC 보존 | 1 | 12534 → a76766 | 55.772 |
| 다른 결과의 같은 판본·강제 오류 rollback·기존 행·늦은 철회 | 1 | 44137 → 069421 | 97.234 |

7그룹 합548.478초다. 등록/조회 구간과 fresh의 Context/start/restore/advance/RHS/step/event/UTC binding8종 호출은0이다.
fixture의 원 계산/입력 evidence 발행까지 계산0이라고 주장하지 않는다.
commit 전 철회/강제 오류는 행0, commit 뒤 철회는 private 감사 행1을 남기고 응답을 거부했다.
현재 철회4종의12조회와 잘못된 페이지6개, 변조10종·다른 농장 참조/서명 key·비canonical JSON을 거부했다.
늦은 page 권리 철회도 반환 전에 거부했다. custody callback의 DB 잠금 Pending을 별도로 전달한다.
기존2테이블의 합성 schema-only 행 각1개/권한은 유지했다. 과거 signed packet의 새 판본 이관 시험이 아니다.

0.25초 관측의7그룹 최대 단일PID/소유+명시 보호 트리 RSS 합은126,730,240/590,618,624bytes로
512MiB/1GiB 안이다. WSL 전체 메모리나 PSS를 측정한 값이 아니다.
이전233/82/993 전체 회귀·전체166일 재계산/writer·새 joint HTTP/UI/브라우저·PG17+ hosted는 재실행하지 않았다.

## 기존 사용자 UI의 실제 종료 확인과 복구

첫 guard4c0e62는 **검사 자식 시작 전** 기존 보호3PID 부재로 거부됐다.
기존 run-v1의 controller/service terminal에는 requested_stop/서비스 종료0·정리/원본 보존이 기록됐다.
원24180 도구 핸들도 없었다. 원 도구 종료 코드를 직접 재관측한 것은 아니다.
소유 종료 기록과 실제 부재를 확인한 뒤 보존된 원 backup을 새 run-v3로 복원했다. 전체 계산을 재실행하지 않았다.
첫 private 재기동839406도 이전 helper의 live 보호 PID 요구로 자식 시작 전 거부됐고,
현재 pidfd helper와 확인한 종료 상태를 사용한 원98883/469187은 의도적으로 계속 실행 중이다.

**http://localhost:5173/**, 기존 제품 App·HTTPS8445·별도 복원한 실제 SCRAM DB를 제공한다.
새 자격증명 안내는 [web README](../web/README.md#기존-제품-앱의-로컬-동시-기동--2026-10-09)의 run-v3 경로다.
원72182→555595 실제0/15.424초에서 인증된 생장 summary6.006초/9,628bytes와
수확 summary8.884초/16,519bytes가 이전 수용 wire SHA와 각각 일치했다. 계산/게시 guard0·FD8→8이다.
첫 관측18602→6aabbb 실제1은 응답 직후 .25초 live FD snapshot을 idle로 잘못 가정한 관측 오류다.
제품 변경 없이 실제 idle8을 확인한 뒤10초 이내의 정착 검사를 사용했다. 최종 snapshot16→8/0.251초였다.
최종 API guard의 단일/합 RSS137,621,504/336,797,696bytes·원본/source/UI/FD/소유 정리를 통과했다.
새 브라우저/WebGL을 실행한 검사가 아니며, **화면은 완료 저장 결과의 재생이고 실시간 U3는 미완료**다.

## 다음 단계와 현재 보류

schema/roles/store3자식 근거로 `crop-climate-joint-result-registry`의 작은 합성 저장 부모를 수용한다.
다음은 원108상태·장부/UTC의 닫힌 API 투영→같은 현재 권리의 HTTP/runtime→수치3D다.
새 projection core3는 새 replay module/tests/계약이며 기존220줄 projection과 이번 저장 경계에 근거해2–4집중시간을 잠정 잡는다.
10/10 연속 작업·새 계약 오류 없음 조건이며 HTTP/최종 UI/U3·제품 완료 날짜의 추정은 아니다.
이번 native 조사/설계부터 기록 생성까지 약24분이며 UI 복구와 실제 집중 검사를 포함한다.

원900288b CI는 Web/AuthoredPG/Compose/runtime4개 성공, Backend37981057415는0/1/2/3 성공·4/5 진행 중이다.
draft PR1과 main42ddb8e를 유지하고 push/merge·CI 취소/재시작은 하지 않았다. 새 core의 hosted 수용과 다르다.
운영 기반 d19f7c0 고정, 기존 G0–G4 정의·독립 검토/해제 조건을 유지한다.
실제 품종 입력/농장 crop Run/국내 독립 자료0건, 전체 공동 작기/forcing·물/양분·구매 에너지·Decimal 경제·사용자 실행/U3는 미완료다.
독립 현장 자료 확보는 모델 개발과 병행하며 실제 생산·미래 마진/추천은 hold다.
