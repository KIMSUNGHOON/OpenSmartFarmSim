# 한 load의 두 commit 읽기 연결 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-load-adapter-20261020.json) · [선행 연구 핵심](solar-local-json-ownership-core-20261020.md).

## 연결과 수용 범위

[연구 adapter](solar-json-load-adapter.py)는 원 저장 `_load`의 두 commit 읽기에 [기존 소유권 부품](solar-local-json-ownership.py)을 연결한다. 원 source SHA와 함수의 module/slot/code를 확인하고, 첫 루프의 type/key/version/header/sequence/parent 검사를 불변 header로 수행한다. 두 번째는 현재 파일 보안/크기/bytes/SHA를 다시 확인한 뒤 private 트리를 한 번 전달한다. 그 밖의 원 함수 본문은 source에서 유도하며 **실제 storage module의 globals**로 실행해 늦은 helper 변경을 관측한다. source/payload hash는 원 구현이다.

초기 변경된 loader/header/records·함수 body·다른 원 함수를 잘못 연결한 slot은 실제 기존 경로로 처리한다. 실행 중 loader 자체의 body를 바꿔도 이미 실행 중인 원 frame이 이전 본문을 계속 수행하는 동작과 비교했다. parser/blob/records/hash/canonical 및 파일 변경의 원 오류도 대사했다. 임의 Python introspection/적대적 in-process 코드를 격리하는 장치는 아니다.

backend/app261개와 SHA `d477b74b…`는 그대로이고 제품 call site0이다. 기존 두 UI·새 일사 배포 상태도 같다. **44b의 연구 연결 의미만 수용**하며 전체 load/pair 소유권·성능·원64/제품 수용은 아니다.

## 최종 검증

| 구간 | 실제 확인 |
| --- | --- |
| WSL Python3.12.3 | 새 adapter28 + 기존 핵심56 = 고유84검사. pytest6.83초·guard7.305936초. |
| 잠금 Python3.12.13 | 같은84검사. pytest5.90초·guard6.533893초. 기존 잠금 venv 패키지를 썼으며 hosted 설치/전체 CI 수용은 아니다. |
| 실제 저장46commit | 전체 반환267,526bytes/SHA·원 시점/단위·참조 집합/2,314,629bytes가 같다. artifact `_read`104회의 파일명/순서/한도/길이/raw SHA가 같다. JSON decode104→82·일회 재사용22이며 보유/임시 원문 상한1,034,884bytes≤1MiB. 원59파일 불변·scope 정리를 확인했다. guard1.380433초. |
| 실제 SCRAM·기존 확정 확인 | 원 CASE6/input64/chunk1의 첫 checkpoint에서 원/후보 전체 record와 UTC `2026-10-01T00:00:00.123456Z`·DB digest가 같다. 각 current6/SQL4,059를 보존했다. 초기·늦은 권리 철회/일시 HEAD 변경의 원/후보6거부와 복원·계산/CLI0·schema/role0을 확인했다. 최종1검사·pytest54.61초·guard56.627514초. |

84개는 두 판본에서168회 실행한 같은 고유84개다. 이전56/23 및 중간 시행을 새84에 더하지 않는다. 물리 first/last event·interval hold의 전체 확정 값/실패 UTC, rooted chain 오류8개, 초기 helper6개, 늦은 변경8개와 방법 연결/원 참조 집계 등을 포함한다. native 확정은 이미 생성된 한 checkpoint의 idempotent 확인이다. fixture lease600초는 이 의미 비교 범위이며 원 actor/360초 normal64 처리량 시험이 아니다.

최종 네 실행은 FD4→4·5root·원본2,148/두 frozen source·자산·소유 잔여0을 확인했다. 최대 합 RSS1,058,791,424bytes/1GiB·단일145,444,864bytes/512MiB다. 보호 서비스를 중단하지 않았고 원 정상 actor/input/chunk1/poll/retry360/RSS를 변경하지 않았다.

초기 pin의65자리 오기로 기본 경로로 돌아간 두 시도, 첫 불변 header의 parent 접근 오류, native 기록기의 datetime/존재하지 않는 raw value key 가정은 수정 후 최종 증거에서 제외했다. 제품 app은 어느 시도에서도 바꾸지 않았다. PEP669 관측은 코드 대체 없이 수행했고 해제했다.

## 다음 한 단계와 수용 기준

다음은44c **페이지→source/times의 실제 비노출 조립**이다. 원 `_records`가 검증한 페이지의 native decode provenance를 끊지 않고 값/시간을 분리·조립해야 한다. 외부 mutable 반환을 승인된 토큰으로 취급하거나 재인코딩+decode 비용을 숨기지 않는다. 원 페이지 값/시각·descriptor/cursor/prefix·source/payload SHA와 helper/codec/alias/오류·공유1MiB·일회 전달/정리를 실제 원 저장 및 current/HEAD/proof 경로에서 대조한다.

그 의미 수용 뒤에만44d 최종 결합 guard의 원 전체 quantum ABBA 평균2% 이상/양짝 개선을 측정한다. 이번 decode 감소, 이전 단독1.093551% 및 구성요소45.306531%를 전체 성능으로 환산·합산하지 않는다. 통과하면 제품 연결/관련 회귀→원 독립 정상64→hold→HTTP취소→계산 중WebGL→WSL 적용 순서다. full backend/browser/새 CI/원 정상64와 WebGL은 이번에 재실행하지 않았다.

실제 품종·지역/시설 입력과 이용권, 독립 국내 실측 및 미래 작기/정산/시장 판본·대응 후보 자료는 외부 의존성이다. 실제 농장 Run0·G0–G4 보류·미래 생산/마진/최적 추천 미수용·전체 완료일/남은 집중시간 미정·goal active를 유지한다. 위 실측은 검사 시간이며 후속 개발/자료 확보의 날짜 추정으로 확대하지 않는다. 실제 native CLI gpt-6.1-sol/xhigh 문맥·source/출력 SHA를 기록했고 재귀 CLI/새 하위 agent0이다.

## 사용자 진행 기록 게시

[게시 영수증](artifacts/solar-json-load-adapter-status-publication-20261020.json): 두5173/5174가 같은 최신 JSON·HTTP200/no-store를 제공한다. frozen HTML·환기2,173파일·5root/원본2,148·FD4→4·소유 잔여0을 보존했다. guard0.341778초·최대 합870,440,960bytes다. UI code/DOM/WebGL은 재실행하지 않았다. 기존 환기의 `new_model_deployed:true`를 유지하며 새 Solar 적용은 아니다.
