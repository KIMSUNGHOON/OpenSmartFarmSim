# 프로젝트 점검·JSON 소유권 연구 핵심 — 2026-10-20 KST

[기계 증거](artifacts/solar-local-json-ownership-core-20261020.json) · [선행 파일 검증 의무](solar-confirm-load-consumption-review-20261020.md).

## 현재 사용자 기능과 차단점

| 구분 | 확인한 범위 | 남은 수용 |
| --- | --- | --- |
| 기존 사용자 화면 | 5173의 완료 합성 생장·수확 저장 재생, 5174의 기존 공동 계산/환기 경로. 이번에 기존 세 서비스의 인증 조회를 다시 점검했다. | 최종 제품 UI 통합, 새 일사 모델 적용, 계산 중 확정 구간의 새 모델 WebGL/WSL 수용. |
| 작물·기후 계산 | 결정적 계산·불변 저장·API·이전 판본의 저장 3D 연결이 있다. 합성 연구 범위다. | 현재 일사 모델의 원 조건 독립 정상64는 미완료. 최근 CI 3건은 최종 실패다. |
| 실제 지역·농장 판단 | 출처·권리·관문 계약과 보류 경로가 있다. | 실제 농장 Run0. 권리 확인된 품종/시설/기후 입력·독립 국내 실측·미래 작기/경제·대응 후보 비교 자료가 필요하다. 생산량·미래 마진·최적 작물을 검증했다고 게시할 수 없다. |

정상 CI39321398376은 종료 뒤 metadata44/64, 진단CI39328214424는 마지막 confirm27/64였다. 이 수치를 생산량이나 성능 개선율로 사용하지 않는다. 같은 source의 원 정상 CI를 재접수하지 않았다.

## 이번 산출물: 제품과 분리한 연구 후보

[연구 부품](solar-local-json-ownership.py)과 [집중 검사](../backend/tests/test_local_json_ownership.py)를 추가했다. backend/app261개 원 파일과 집계 SHA `d477b74b…`는 같다. 제품 call site는0이다. 성능 수용 전의 부품을 연구 영역에 보관한다. 기존82검사를 이번 후보의 검증 수에 합산하지 않았다.

| 내부 연산 | 이번 확인 |
| --- | --- |
| `decode` → `take_field` | 승인된 native strict decode의 비노출 트리만 분리한다. 외부 mutable 객체를 받아 소유권을 선언하지 않는다. |
| `seal_source` → `bind_payload` | 한 source와 닫힌7개 metadata의 native canonical SHA를 보존한다. Unicode/escaping·signed zero·큰 정수·binary64·bool을 대사했다. |
| `materialise` | 토큰을 소모하며 값을 반환한다. 반환 뒤 같은 토큰으로 hash를 만들거나 값을 다시 전달할 수 없다. |
| `chain` → `commit` | 첫 읽기는 불변 header만 공개한다. 두 번째는 현재 파일의 보안/크기/bytes/SHA를 다시 검사한 뒤 같은 트리를 한 번 전달한다. 세 번째는 다시 decode한다. |
| native 상태 변경 | 고립 참조의 JSON semantic SHA와 승인 함수의 실제 slot/코드를 비교한다. import 전 custom codec을 기본으로 학습하지 않는다. 늦은 codec/helper/limit 변경, 잘못된 자리의 다른 원 함수는 원 경로로 처리한다. |
| 수명·한도 | 한 `with`/PID/thread/task에 한정한다. 보유 원문과 새 인코딩·최적화 중 fresh read의 임시 공간을 단일1MiB 예산으로 예약하고 초과 시 원 경로를 사용한다. 원 경로의 기존 I/O 한도는 바꾸지 않는다. |

CPython3.12의 명시된 native JSON 구성만 최적화 후보가 된다. strict decoder의 명시 hook과 비기본 canonical encoding에서 도달하지 않는 `_default_encoder`/`_default_decoder` 인스턴스는 승인 대상이 아니다. 일반 JSON/임의 Python callback의 동등성이나 적대적 Python 코드에 대한 격리 장치가 아니다. 서버의 버전 고정 코드가 한 load 안에서 수명을 닫아야 한다.

## 최종 집중 검증

최종 같은 source의 **고유56개 검사**를 WSL Python3.12.3과 잠금 Python3.12.13에서 각각 통과했다(112회 실행, 고유112개 아님). pytest0.53/0.49초·guard1.118584/1.131173초다. 최대 합산 RSS977,289,216bytes/1GiB, 단일145,444,864bytes/512MiB, FD4→4, 다섯 서비스 root·원본2,148항목·두 frozen source/자산·소유 잔여0을 확인했다. 기본 파일 변조/삭제/symlink/축소 limit·참조 예산 오류, cache eviction·예외 정리, 초기/늦은 함수와 codec 변경, 미승인 초기 codec, 더 깊은 두 번째 호출의 재decode를 포함한다.

초기 미구현 RED, 이전1/41/50/53 및 시험 기대 오류가 있던35통과+1실패는 최종56에 더하지 않는다. 해당 실패는 잘못 연결한 canonical 함수가 원 경로에서 TypeError를 내는 상황을 시험이 성공 값으로 기대한 오류였다. 원 오류와 비교하도록 고쳤다.

기존 환기 서비스는 이번에 실제 UI proxy/검증된 HTTPS의 정상·보류8응답이 원 저장 wire와 일치했고, 조회 계산/제품 쓰기 hook0·FD8→8·환기 frozen2,173파일을 보존했다. 기존 생장/수확과 joint도 별도 소유 감독 아래 인증 조회를 확인했다. 이 조회는 새로운 WebGL 검증이나 새 일사 배포가 아니다.

## Python 참조와 코드 검토

실제 WSL은 Python3.12.3, CI 잠금은3.12.13이다. 두 고립 `-I -S -B --reference`의 SHA가 다름을 확인했고, 처음의 “두 판본이 같아야 한다”는 probe 기대를 폐기했다. 설치된 원 JSON 파일을 대조해 decoder의 ASCII hex4 정규식·scanner의 ASCII 숫자 정규식·encoder 문서 차이를 확인했다. 검토한 두 native 참조만 명시적으로 등록하고, 잘못된 Unicode escape/비ASCII 정수·소수 입력의 원 거부 대조3개를 추가했다. 두 참조의 최종 source SHA·원 JSON4파일 SHA를 기계 증거에 기록했다. 알 수 없는 참조를 import 시 학습하는 동작은 없다.

3.12.13 검사는 해당 인터프리터와 기존 잠금 venv 패키지로 실행했다. 새 hosted 설치/전체 backend CI 수용이 아니다. 초기 참조 probe1의 실패와 후속 실제 차이 관측은 최종56검사의 실패로 합산하지 않는다.

`code-review-and-quality` 검토에서는 정확성의 범위를 위56개와 닫힌 API로 한정했다. native 상태 지문의 복잡도/비용과 실제 source 조립은 미수용이다. 일반 프레임워크·의존성을 추가하지 않았고 연구 후보를 제품 경로와 분리했다. 원 현재 권리/HEAD/proof 검증을 생략하는 연결은0이다. 성능은 최종 전체 비용을 확인한 뒤 판단한다.

## 남은 작업과 다음 한 단계

부품56은 전체 load/pair 소유권이나 성능 수용이 아니다. **다음은 한 load의 두 commit 읽기 adapter**다. 기존 첫 루프의 전체 key/version/header/sequence/parent 검사를 불변 header로 그대로 수행하고, 두 번째 루프의 mutable commit은 fresh read 후 한 번만 전달한다. 실제 같은 HEAD에서 원 전체 반환 bytes/UTC·오류/계정/권리·HEAD/proof·모든 fresh page 검사를 대조하고, 초기/늦은 method 변경과 정리·상한을 확인해야 한다. 이 단계는 hash 최적화를 도입하지 않는다.

그 뒤 저장 페이지→source/times 조립까지 소유권을 이어 준다. `_records`의 기존 mutable 반환을 승인된 토큰으로 간주하거나 재인코딩 후 decode해 추가 비용을 숨기지 않는다. 이 실제 조립 경계·custom helper fallback/오류·alias/메모리 수용을 마친 뒤 최종 결합 guard의 원 quantum ABBA 평균2% 이상/양짝 개선을 측정한다. 이전 단독1.093551%와 인코딩 구성요소45.306531%를 합산하지 않는다.

성능 수용 후에만 제품 연결/관련 회귀→원 독립 정상64→hold→HTTP취소→계산 중WebGL→WSL 적용으로 진행한다. 실제 자료 확보·검증은 병행 의존성이다. 기존 G0–G4를 유지한다.

이번56검사의 판본별 약1.1초와 기존 전체 ABBA guard146.97초는 관측된 검사 시간이다. adapter 개발·원64 통과·외부 자료 확보의 완료일을 추정할 근거로 확대하지 않는다. 전체 완료일/남은 집중시간은 미정이며 goal active다. 실제 native CLI gpt-6.1-sol/xhigh 문맥 SHA를 기록했고 재귀 CLI/새 agent0이다.

## 사용자 진행 기록 게시

[게시 영수증](artifacts/solar-local-json-core-status-publication-20261020.json): 두5173/5174의 같은 최신 JSON·HTTP200/no-store와 frozen HTML, 환기2,173파일·5root/원본2,148·FD4→4·소유 잔여0을 확인했다. guard0.342539초·최대 합873,984,000bytes다. UI code/DOM/WebGL은 재실행하지 않았다. `new_model_deployed:true`는 기존 환기 모델이며 새 Solar 적용을 뜻하지 않는다.
