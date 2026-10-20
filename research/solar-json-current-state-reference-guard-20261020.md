# JSON 현재 참조 비교 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-current-state-reference-guard-20261020.json) · [선행 비용 평가](solar-json-combined-guarded-cost-20261020.md).

## 현재 판정

**의미 검증은 통과했지만 전체 비용 기준은 미달하여 제품에 적용하지 않았다.** 변경된 최종 코드의 실제 ABBA에서 후보가 평균 **2.252640% 느렸다**. 기존 후보의 유효한 시험을 반복하지 않았으며, 이 변경 후보의 유효한 전체 비용 비교도 한 번만 수행했다. backend/app261개와 제품 호출0을 유지했다.

## 변경과 검증

처음 승인한 객체·code·기본값·클로저·가변 컨테이너·builtin 참조와 현재 상태를 직접 비교한다. 재귀 code-name 집합과 정렬된 ID tuple을 검사할 때마다 다시 만들던 비용을 줄였다. 최초 JSON 고립 참조 두 SHA와 pristine 함수 승인은 유지한다. 캡처한 참조의 최초 ID 표현을 원 baseline과 대사해 승인 도중의 변경을 새 기본값으로 채택하지 않는다.

원 `_live_stamp`, `LegacyPolicy.stamp`, `_attested`, `OwnedJSONScope` 전체 AST와 source assembly 원 bytes가 같다. `_ready`와 조립의 관측 위치·감시 항목을 줄이지 않았다. 승인한 참조와 immutable code-name 구조만 보관하며 입력·권리·현재·HEAD·proof를 캐시하지 않는다. JSON 자료는 기존 일회 소유·수명·예산·정리 계약을 따른다.

- 새46 + 기존127 = 고유173검사. CPython3.12.3과 잠금 판본3.12.13에서 각각173개 통과했다. 후자는 현재 설치된 잠금 패키지를 사용한 검사이며 clean hosted 설치나 전체 CI가 아니다.
- 원 oracle와 module/class 추가·삭제·동수 교체, 함수 code/default/kwdefault, nested dict/list·closure/빈 cell, builtin·실행 한도, alias·초기/늦은 변경·오류·수명을 대조했다. sentinel 값을 가진 새 이름으로 동수 교체하는 반례를 RED로 확인해 수정했고, 승인 중 변경도 거부한다. 미승인 preimport codec은 복원 뒤에도 승인되지 않는다.
- 원46commit/59파일·전체267,526bytes·SHA `3136aa2840c1f2515925b8b335cc52e0d49cd8c771170d72d7f34d868c652249`가 같다. IO104개의 순서·이름·상한·길이·SHA, seen/참조2,314,629bytes가 같다. decode104→83·source pair46·payload canonical46→0·합산1MiB/정리를 확인했다.
- 실제 DB 검사1에서 원 CASE6/input64/chunk1의 confirm 전체 record·UTC·current6/SQL4,059가 같다. 최초/늦은 권리·일시 HEAD 변경의6개 보류도 같다. 조회 중 수치 계산/CLI0·DB 불변·역할/schema0·정리를 확인했다. 원 독립64 완주 검사가 아니다.

## 원 전체 비용

원64 입력/output0..64/8·chunk1에서41단계 이력을 준비하고42–45의 `before → advance → confirm` 전체를 ABBA로 측정했다. 후보에서는 소유 시험 안의 storage loader만 교체했다. SQL/current 함수는 유지하고 PEP669로 호출을 관측했다. 원 actor·입력·poll/retry360·RSS 상한은 바꾸지 않았다.

| 순서 | 원 단계 | 전체 초 |
| --- | ---: | ---: |
| 기존 A | 42 | 9.550943558 |
| 후보 B | 43 | 9.734650311 |
| 후보 B | 44 | 10.022255041 |
| 기존 A | 45 | 9.770714335 |

감소율은 평균 **−2.252640%**, 짝별 **−1.923441% / −2.574435%**다. 사전 평균2% 이상·양짝 양수 기준을 통과하지 못했다. 단일 로컬 비교이며 전체64 처리량이나 일반적인 성능으로 확장하지 않는다. 원 checkpoint bytes/counts/UTC·current15/SQL9,929·role273/원천2,280을 보존했다. 후보의 각5 scope에서 pair218/223·원 파일 재읽기·일회 소유 폐기·1MiB 한도를 확인했다.

별도 cProfile의 원46 load는0.726623612초다. `_ready`1,899회·조립1,442회·native JSON1,900회로 이전과 같다. `_ready` cumulative0.368254초·JSON current0.269716초를 관측했다. 중첩 cumulative 시간을 합산하지 않고, 이 관측을 전체 비용 개선율로 환산하지 않는다. 앞선 후보보다 profile의 상태 비교 비용이 작아져도 제품 비용 기준을 대신하지 않는다.

## 자원·실패 기록

최종 같은 source의 수용한6실행에서 최대 합 RSS1,063,518,208bytes/1GiB·단일145,444,864bytes/512MiB다. 각 FD4→4·5root·원본2,148·두 frozen UI source/자산·소유 잔여0을 확인했다. 최종 native guard62.720006초·전체 비용 guard173.255586초다.

초기 native 시험은 합 RSS1,076,109,312bytes로 상한 중단됐다. 별도 설정 오류로 시작한 시험도 중단했다. 둘 다 성공 집계에서 제외했고 소유 DB·임시 인증 파일 정리와 원 실패 증거를 보존했다. 기존 controller의 미사용 handoff 이력 해제를 pytest/restore_probe에도 적용했다. 한도·보호 판정·원본 pin은 유지했고 보호 서비스를 중단하지 않았다. 이후 최종 source의 native/비용 시험은 원 상한 안에서 종료했다.

## 다음 단계와 외부 의존성

다음 작은 작업은 `crop-solar-json-reference-guard-remaining-cost`다. 현재 전체 구간에서 남은 상태 비교·canonical/검증 비용을 호출 위치와 함께 대조해 원 비용 실패의 최소 후속 경계를 정한다. 성능 개선이 입증되기 전까지 제품 경로는 유지한다. 같은 유효한 timing 시험이나 변경 없는 CI를 반복하지 않는다. 현재/권리/입력/HEAD/proof/fresh IO와 원 actor·64/chunk1/poll/retry360/RSS는 유지한다.

비용 수용 뒤 제품 연결/관련 회귀 → 변경 source의 원 독립 정상64 → hold → HTTP 취소 → 계산 중 WebGL → WSL 사용자 적용 순서다. 마지막 정상 CI39321398376은 저장44/64, 후속 진단39328214424는 마지막 확인27/64로 미완료이며, 현재 API에서도 모두 종료·실패 상태를 확인했다. 새 CI는 접수하지 않았다.

실제 국내 한 품종/한 작기의 권리 있는 농장·기후·시설·재배·수확/자원 자료와 독립 검증, 경제/시장 시점 판본·미래 작기·대응 후보 검증은 외부 의존성이다. 실제 농장 Run0·G0–G4/미래 생산·마진·최적 추천은 보류다. 전체 완료일/남은 집중시간은 자료 확보와 원64 검증이 없어 미정이다. 실제 native Codex CLI gpt-6.1-sol/xhigh 문맥·입출력 SHA를 기록했고 재귀 CLI/새 agent0·goal active다.

## 사용자 진행 정보 게시

[게시 영수증](artifacts/solar-json-reference-guard-status-publication-20261020.json)에서 두5173/5174의 같은 최신 JSON·HTTP200/no-store·원 HTML과 환기2,173파일을 확인했다. 새173/원 비용 미채택과 미완료64/새 일사 배포를 표시한다. UI 코드·DOM/WebGL은 다시 실행하지 않았다. 기존 환기의 `new_model_deployed:true`는 유지하며 새 Solar 적용이 아니다.
