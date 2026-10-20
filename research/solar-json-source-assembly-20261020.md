# 페이지→source/times 비노출 조립 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-source-assembly-20261020.json) · [선행 두 commit 읽기](solar-json-load-adapter-20261020.md).

## 구현과 경계

[연구 조립기](solar-json-source-assembly.py)는 실제 native blob reader를 내부에서 호출하고, 원 `_records`의 검증 본문을 같은 storage globals로 실행한다. commit capability와 새 페이지의 strict decode 결과가 검증→source/times 조립→source hash→payload hash까지 내부에 머문다. 외부에서 받은 mutable `_records` 반환값을 소유했다고 선언하지 않는다. helper/codec/builtin/clock 변경과 alias callback은 해당 pair의 소유권을 취소하고 실제 원 해시 경로로 처리한다. callback이 자신을 복원해도 그 pair를 다시 승인하지 않는다.

[기존 소유권 부품](solar-local-json-ownership.py)에 내부 canonical 길이 상한 조회를 추가했다. 기본 raw-backed 동작은 같고, 조립기는 native 입력의 원 길이 합계로 보수적 상한을 계산한다. 추가 재인코딩+decode로 소유권을 만들지 않는다. source를 한 번 인코딩하고 먼저 원 source SHA를 검증한 다음, 닫힌 metadata를 앞/뒤로 인코딩해 payload SHA를 계산한다. source 오류는 payload 계산 전에 거부한다. 해시 pair의 capability는 외부 canonical context 검사 전에 소모한다.

**단일1MiB는 새로 보유하는 metadata/source raw bytes·추가 인코딩 및 최적화된 commit 읽기의 예약 합계다.** 페이지는 원 reader의 동일 호출·2MiB 한도와 기존 임시 원문/canonical 수명을 유지하고 새 raw page buffer를 보관·복제하지 않는다. 원 header/context·fallback의 기존 I/O 한도를 줄이지 않는다. 이 원래의 메모리도 프로세스/5root 전체 RSS 감독에 포함한다. 큰 원 입력이 추가 버퍼 예산에 맞지 않으면 원 해시 경로를 사용하며 입력을 잘라내지 않는다.

[load adapter](solar-json-load-adapter.py)는 내부 AST 변환 hook과 갱신된 부품 핀을 사용한다. backend/app261개·`d477b74b…`는 그대로이고 제품 call site0이다. native CPython/버전 고정 코드의 연구 범위이며 적대적 in-process introspection/임의 Python 코드를 격리하는 장치는 아니다.

## 최종 증거

| 구간 | 확인한 범위 |
| --- | --- |
| WSL Python3.12.3 | 새 조립43 + 이전84 = 고유127검사. pytest15.17초·guard15.745349초. |
| 잠금 Python3.12.13 | 같은127검사. pytest14.20초·guard14.774419초. 기존 잠금 venv 패키지로 실행했으며 hosted 설치/전체 CI 수용은 아니다. |
| 실제46commit | 원 전체267,526bytes/값·UTC·SHA·참조2,314,629bytes·59원 파일이 같다. artifact `_read`104회의 순서/파일명/한도/길이/raw SHA가 같다. decode104→83·metadata 일회 재사용21, source 인코딩46→46·전체 payload 인코딩46→0·native pair46을 실제 관측했다. 추가 원문 예약 최대1,037,131bytes≤1MiB·정리를 확인했다. guard1.889558초. |
| 실제 SCRAM1 | 원 CASE6/input64/chunk1의 기존 첫 checkpoint 확인에서 record·UTC `2026-10-01T00:00:00.123456Z`·current6/SQL4,059·DB digest가 같다. 초기/늦은 권리 철회·일시 HEAD 변조의 원/후보6거부·복원·계산/CLI0·schema/role0. pytest55.60초·guard57.350172초. |

고유127을 두 판본에서254회 실행했다. 초기/늦은 helper·codec/원 error, 정상/물리 hold, source 오류의 선행 거부, 원 결과를 외부에 보관하는 callback, 자신을 복원하는 callback, 두 해시 사이에 source를 변조하는 새 encoder, 작은 추가 버퍼 fallback 등을 포함한다. 과거84/118 및 중간 시행을 새127에 더하지 않는다. 처음 digest 전달 누락과 유효한 원 dict alias를 만들기 위한 검사 보정은 최종 결과에서 제외했다.

네 최종 실행에서 FD4→4·5root·원본2,148·두 frozen source/자산·소유 잔여0을 보존했다. 최대 관측 합 RSS1,064,136,704bytes/1GiB·단일145,444,864bytes/512MiB다. 실제 정상64 actor/input/chunk1/poll/retry360/RSS를 바꾸거나 보호 서비스를 중단하지 않았다. SCRAM의 lease600은 기존 checkpoint 의미 비교 조건이며 원 정상64의 처리량 시험이 아니다.

## 수용과 다음 한 단계

44c의 **연구 조립 의미만 수용**한다. 실제 raw 읽기는 유지했고 metadata 재사용은 이전22에서21로 달라졌다. source/payload 인코딩 변화와 예전 단독1.093551%·구성요소45.306531%를 전체 성능으로 환산·합산하지 않는다.

다음44d는 최종 같은 source/guard를 포함한 원 전체 quantum ABBA다. 평균2% 이상과 양짝 개선을 모두 요구한다. 같은 원 actor/input64/chunk1·현재 권리/HEAD/proof/모든 fresh file·원 값/UTC·종료/정리를 보존한다. 미달이면 연구 결과로 보존하고 제품 적용하지 않는다. 통과 뒤에만 제품 연결/관련 회귀→원 독립 정상64→hold→HTTP취소→계산 중WebGL→WSL 적용으로 진행한다.

전체 비용·backend/browser/새 CI·원 정상64·새 WebGL/사용자 모델 적용은 이번에 실행하지 않았다. 실제 품종/지역·시설/기후 입력 권리와 독립 국내 실측·미래 작기/정산/시장 판본·대응 후보 자료도 남았다. 실제 농장 Run0·G0–G4 보류·미래 생산/마진/최적 추천 미수용·전체 완료일/남은 집중시간 미정·goal active다. 위 실측은 검사 시간이며 전체 날짜의 근거가 아니다. 실제 native CLI gpt-6.1-sol/xhigh 문맥·source/출력 SHA를 기록했고 재귀 CLI/새 agent0이다.

## 사용자 진행 기록 게시

[게시 영수증](artifacts/solar-json-source-assembly-status-publication-20261020.json): 두5173/5174가 같은 최신 JSON·HTTP200/no-store를 제공하며 frozen HTML·환기2,173파일·5root/원본2,148·FD4→4·소유 잔여0을 보존했다. guard0.350953초·최대 합869,883,904bytes다. UI code/DOM/WebGL은 재실행하지 않았다. 기존 환기의 `new_model_deployed:true`는 새 Solar 적용을 뜻하지 않는다.
