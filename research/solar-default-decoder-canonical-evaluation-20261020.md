# 기본 decoder·원 canonical 대사 — 2026-10-20 KST

[기계 증거](artifacts/solar-default-decoder-canonical-evaluation-20261020.json) · [선행 진단](solar-current-worker-api-diagnostic-20261020.md).

## 검토한 경계

현재 잠금은 Pydantic2.13.5/core2.46.5다. 설치된 함수 signature·pyi/바이너리 SHA와 [공식 API](https://pydantic.dev/docs/validation/latest/api/pydantic-core/pydantic_core/#pydantic_core.from_json)·[공식 JSON 설명](https://pydantic.dev/docs/validation/latest/concepts/json/)을 확인했다. 공식 문서는 partial parsing과 string cache를 지원하므로 후보는 allow_inf_nan/allow_partial/cache_strings를 모두 False로 명시했다. 실시간 공식 문서를 설치 판본 source 증명으로 쓰지 않았다. 직접 문서 요청403 두 건·설치 판본 GitHub tag 요청404를 보존했다. 웹 도구로 읽은 공식 API 출력과 로컬 설치물을 별도로 해시했다. 자료 승인/작물 데이터 도입은0이다.

사설 후보는 기존 _blob의 digest 형식→원 bounded/no-follow regular file 읽기→실제 SHA 검사를 그대로 실행한다. ASCII이며 Unicode escape가 없는 raw만 C parser로 읽고 **원 _canonical(value)==raw**일 때만 값을 사용한다. 다른 경우는 원 strict _json과 원 canonical 검사를 실행한다. 실패한 C parser의 except 구간 밖에서 원 parser를 호출하여 그 오류 cause/context를 덧씌우지 않았다. 매번 새 값이며 load/호출 사이 cache나 입력 재사용은0이다. 일반 JSON parser 전체를 교체하지 않았다.

기본 codec 경계1 pytest에서 정상/중복 key·중첩 중복/정렬·공백·nonfinite/overflow·float최소/최대/음의0·Unicode/잘못된UTF8/escape·깊은 중첩·큰 정수36 vector와 크기/SHA3경계를 원 값·원 오류 type/message/cause/context로 대조했다. 이36/3을39독립 test나 완전한 보안 검증으로 세지 않는다.

## 실제 비용1 pytest

원 CASE6/64/output0..64/8/chunk1·41준비 뒤 worker before/private advance/독립 confirm ABBA42..45다. 두 candidate에서 fast490/500·fallback각7을 실제 관측했다. 원 checkpoint bytes/counts/UTC84/86/88/90.123456Z·current15/순서·SQL9,929/role273/원천2,280·SQL map은 같다.

| 순서 | 모드 | quantum | 실제 시간 |
|---|---|---|---|
| 1 | baseline | 42 | 9.690677504초 |
| 2 | candidate | 43 | 8.390109690초 |
| 3 | candidate | 44 | 8.412564791초 |
| 4 | baseline | 45 | 8.555510113초 |

평균 **7.911314%**, 짝별13.420814/1.670798%로 사전 평균2%·양짝 감소 기준은 통과했다. baseline 차이와 짝별 차이가 크므로 일반 개선율·독립64 처리량으로 확대하지 않는다. guard159.172296초·단일126,124,032/합684,032,000bytes·사유null·FD4→4·5root/원본2,148/두 frozen UI·소유 PG/비좀비/임시/passfile0을 확인했다. 기본 경계 guard0.853195초·합545,890,304bytes도 통과했다.

## 제품 적용 보류·다음 수용 기준

현재 후보는 custom f._json이나 inputs._json·그 함수 globals/JSON module이 교체된 경우의 원 동작을 보존하지 않는다. 원 parser가 예외를 내도록 교체되더라도 fast 성공은 이를 건너뛸 수 있다. **이는 알려진 사설 후보 제한이며 제품 적용을 금지한다.** 모든 decoder/encoder alias·code/default·parser flags·Unicode/numeric·오류·자원 경계의 동등성을 수용하지 않았다. 원 app261파일/d477b74b…는 그대로이고, 기존82를 재실행하거나 새2검사를 제품 수용 수에 더하지 않는다.

다음 작은 구현은 기본 codec 경로와 교체된 codec 경로의 dispatch다. 원 callback/오류가 보존되지 않는 RED를 먼저 남긴다. 기본 함수·code/globals/JSON 내부/recursion·integer 정책을 식별하지 못하거나 바뀌면 원 _blob을 실행한다. 최종 후보는 canonical 원 bytes·파일/한도·원 오류 순서와 변경/보안/수명 검증, 그 최종 source의 실제 비용 기준과 관련 회귀를 통과한 뒤에만 제품 적용을 판단한다. 이때 guard의 실제 비용도 포함한다. 새 의존성/교차 load cache·원 input/actor/chunk/poll/retry360/RSS 변경은 없다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 사용자 적용과 실제 농장 자료/독립 검증은 남는다. 새 Solar 미배포·실제 농장 Run0·G0–G4 보류·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh의 실제 문맥/해시를 기록했고 재귀 CLI·하위 에이전트는0이다.

## 사용자 상태·검증 범위

[상태 게시 증거](artifacts/solar-default-decoder-status-publication-20261020.json): 두5173/5174 HTTP200·동일 최신 상태/no-store, frozen HTML/환기2,173/원본2,148/5root·FD4→4·소유 잔여0을 확인했다. guard1.884949초·합559,472,640bytes다. 상태 데이터만 갱신했고 browser DOM/WebGL·전체 회귀·정상64는 재실행하지 않았다.
