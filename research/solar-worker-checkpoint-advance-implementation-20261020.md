# Worker 계산 전진과 독립 checkpoint 확인 — 2026-10-20 KST

[기계 증거](artifacts/solar-worker-checkpoint-advance-implementation-20261020.json) · [계약](../contracts/solar-worker-checkpoint-advance-v1.md) · [선행 독립 정상 실패](solar-existing-intent-resume-native-normal-20261020.md).

## 변경과 확인 경계

worker는 기존 `advance`의 반환을 버린 뒤 별도 `_confirm`의 결과를 소비했다. 새 서버 내부 `_advance_for_checkpoint`는 같은 guarded write 진입과 계산·저장 본체를 사용하고 `None`을 반환한다. 진행률·권리·checkpoint를 증명하는 응답이 아니다. `_confirm`이 현재 입력/권리, 서명 이력과 lease/cancel을 독립 검사한 결과만 DB 게시와 worker 진행 판단에 사용한다.

`_Session.advance`의 exact-bool 내부 옵션은 기본 `True`다. 공개 `advance`/`inspect`/`page`의 응답과 progress 전후 guard는 그대로다. 내부 옵션이 `False`이면 사용되지 않는 progress 생성만 하지 않는다. 첫 current/선택 HEAD·전체 이력 검증, prepare·start/restore·수치 청크, private page/commit/proof·HEAD 게시 검증과 정리는 유지한다. 종료 이력 재시도도 현재 권리와 authentic 이력을 확인하며 수치 계산을 다시 하지 않는다. 권한·결과 cache나 공개 옵션은 추가하지 않았다.

변경은 backend app261개 중2개이며 나머지259개는 같다. custody의 나머지17 method와 worker의 나머지 본체는 동일하다. worker는 호출 attribute 한 곳만 바뀌었다. 기존 worker 시험의 타이밍/취소/만료 spy는 실제 내부 호출을 관찰하도록 옮겼고 기존103개 assertion AST를 보존했다. 새 `None` assertion1개를 더했다. 원 독립 actor2개의 hash·입력·chunk1/poll/retry360/RSS는 유지한다.

## 최종 같은 source의 로컬 수용

backend app tree는 `d477b74bc0a7ad2258a5bfd7bb522ad559a704ea55fca3849fb2f46e7ce403db`다. **새 기능10 + 기존 회귀71 + 실제 제품 비용1 = 고유82검사**, 독립 controller38개를 대사했다. 이전 source72와 사설 GREEN/비용2개, 예상 RED는82에 더하지 않았다. fault vector 수 역시 pytest 건수에 더하지 않았다.

| 검사 | 건수 | 확인 |
|---|---:|---|
| 새 내부 전진/확인 |10| `None`·progress 생성0·공개 raw 응답/원 값·UTC, strict 옵션/예산, 물리·경제 권리, ack 뒤 권리/HEAD 변경, 늦은 proof 철회, 정상/hold 재시도, 실제 worker·무동작 ack 차단 |
| 기존 재개/잠금 파일 |7 + 1| 비생성 선택·현재 권리/HEAD·strict 모드·잠금 보안 |
| 소유권/읽기 공유 |4 + 7| 현재·prepare 이후 권리/실제 읽기 공존·쓰기 배제 |
| worker |13| 정상·수치 hold 원 값/원자 완료, 취소·임대 만료·재개, 검증 도중 입력 변경과 늦은 취소 |
| query |13| 원 counts/UTC·현재/늦은 권리·snapshot/디렉터리·별도 완료/hold reader·조회 계산/SQL 변경0 |
| HTTP/TLS/fresh |24 + 1 + 1| 고정 실패·실제 SCRAM/TLS503→200·별도 exec 재개/원 값·UTC |
| 실제 제품 ABBA |1| 원 before/advance/confirm 묶음·전체 남은 current/SQL 순서·원 checkpoint bytes 대사 |

새 경계 검사에서는 private ack 직후 아직 DB checkpoint가 없음을 확인했다. 그 뒤 권리 철회/HEAD 변조 시 독립 confirm이 실패하고 DB checkpoint는0이다. 실제 worker의 post-ack 철회와 무동작 ack도 결과 게시 없이 hold였다. 늦은 proof 철회 때는 이전 HEAD를 보존하며, orphan private 파일을 정상 결과로 주장하지 않는다.

## 실제 제품 비용

사전 기준은 두 짝 모두 wall 감소, 평균2% 이상이다. baseline은 최종 소프트웨어/입력 pin 아래 **원 `_Session.advance` 본체**를 복원한 비교다. private prototype의 평균10.03998%와 최종 제품 비교를 구분한다.

| ABBA 짝 | 기존 초 | 제품 초 | 감소율 |
|---|---:|---:|---:|
| 첫 짝 |8.141987289|7.033147605|13.618784%|
| 둘째 짝 |8.043026087|6.930643310|13.830401%|

평균 **13.723946% 감소**로 기준을 통과했다. 원 checkpoint bytes/counts와 UTC04/06/08/10.123456Z를 유지했다. full current17→15·SQL11,125→9,929·role 감사301→273·원천 읽기2,584→2,280은 오직 버려지는 advance progress의 전후2검사에 해당한다. 모든 남은 current 검사의 순서/SQL이 baseline과 정확히 같음을 대사했다. 공개 기본 경로에는 원 progress2검사가 유지된다. 이전 개선율과 합산하거나 원64 전체 처리량으로 환산하지 않는다.

## 실행·보존·한계

RED는 새 내부 호출이 없는 원 코드의 `AttributeError`였다. 사설 prototype GREEN/비용은 제품82에서 제외했다. 마지막 정상/hold 묶음은 합 RSS1,076,531,200bytes로 중단돼 수용에서 제외했다. 상한과 기존 서비스를 유지하고 동일 두 사례를 별도 프로세스로 분리했다. 종료 뒤 native identity로 소유 PG/감독 잔여0·임시 DB0을 재확인하고 인증 파일4개를 내용을 읽지 않고 삭제했다. 최초 분리 선택자는 fixture ID가 빠져 계산 전에 종료됐다. 실제 collect2개로 정확한 ID를 확인했으며 선택 오류/수집 실행도82에서 제외했다. 원 실패 기록은 변경하지 않았다.

현재82는 최종 같은 app source, FD4→4·원5root/2,148항목·두 frozen UI/source·자산 보존과 소유 PG/비좀비/임시/passfile0을 확인했다. 단일/합산 RSS 최대는 **170,602,496 / 1,070,297,088bytes**, controller wall 합은 **1,739.668162초**다. 이는 시험 소요이며 제품 완료 일정이 아니다.

실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥과 원행 SHA·사전 기준·최종 source/로그/종료 SHA를 기계 증거에 결속했다. 재귀 CLI/하위 에이전트·새 라이브러리/수치 프로필·자료 채택은0이다. 전체 backend/browser CI·새 DOM/WebGL을 이번 집중검사로 수용하지 않았다.

## 다음 관문과 사용자 상태

다음은 이 source의 **원 계측 OFF 독립 정상64**다. 원 actor/input64·chunk1·poll/retry360·RSS, 두 전진 prefix/원 값·UTC·start1/CLI0/attempt1/success1·actor0/0·DB/소유 정리를 별도로 통과해야 한다. sourceaeb7a90의 CI39303668519는 원360초 미완료·종료 뒤 저장 metadata41/64이며 정상/현재 권리 proof가 아니다. 이전 실패는 그대로 보존한다.

독립 정상→독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용으로 진행한다. localhost5173은 기존 합성166일 저장 재생,5174는 기존 환기 실행 UI다. 이번 변경은 새 Solar의 사용자 배포나 계산 중3D 활성화가 아니다. 실제 농장 Run0·국내 원 실측/독립 작기·G0–G4는 보류다. 독립 정상과 외부 자료가 확보되기 전 전체 완료 날짜는 산정하지 않는다. goal은 active다.

최종 진행 게시 `focused-solar-worker-ack-final82-status-v3`는 자식0·guard1.620722초였다. 같은 app82·원 actor 두 hash·관련 로컬 링크2,761개·두 HTTP200/동일bytes/no-store·두 frozen HTML/환기2,173파일·5root/원본2,148/FD4→4/소유 정리를 확인했다. 게시 시각은2026-10-19T20:39:52.989961Z다. 초기 게시 helper의 묶음 수37→38 보정과 상태 설명256→205자 축약은 게시 전에 차단됐던 검증 오류의 수정이며, 공개 제한/제품 소스/82검사 수를 바꾸지 않았다. 새 DOM/WebGL 수용은 아니다.

수용 제품 구현 commit은 `a6bd34dfdca0af05c694c4a93899eaa3ef07bdd1`다. 이 뒤의 문서/진행 기록 commit은 같은 app tree를 유지한다. 원 독립 정상은 다음 CI 전용 head에서 한 번 접수한다.
