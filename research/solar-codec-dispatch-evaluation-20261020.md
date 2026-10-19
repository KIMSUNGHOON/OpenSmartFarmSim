# 기본·교체 codec dispatch 평가: 미채택 — 2026-10-20 KST

[기계 증거](artifacts/solar-codec-dispatch-evaluation-20261020.json) · [선행 비용 적격 후보](solar-default-decoder-canonical-evaluation-20261020.md).

## 원 parser 반례와 수정

원 f._json을 예외를 내는 합성 callback으로 교체하면 원 _blob은 RuntimeError를 내지만 앞선 C decoder 후보는 정상 값을 반환했다. 실제 RED1실패로 재현했다. 제품 실패가 아니며 사설 후보의 알려진 동등성 부족이다.

사설 guarded_v1은 함수 code/default/closure/global 참조, JSON module/class/함수/가변 상수, 실제 recursion/integer 제한을 fast 파싱 전후 대조한다. 기본과 다르거나 지원하지 못하면 원 strict _json과 원 canonical 검사를 실행한다. 원 digest→bounded/no-follow regular file 읽기→실제 SHA 순서는 유지한다. fallback은 **이미 검증한 raw에서 원 파싱 경로를 실행**하며 _blob 전체를 다시 불러 파일/콜백을 중복 읽지 않는다. 코드·global 객체를 교체한 부수 효과를 guard가 실행하지 않도록 알려진 module dict만 읽는다. C parser flag는 모두 False이고 ASCII/no Unicode escape·원 canonical bytes 일치 조건은 같다. 값/권한/원문 cache는0이다.

최종 같은 guard source의 **25 pytest**는 custom parser8·library/정책9·파일6·새 값/읽기1·기본36vector 묶음1이다. 함수/동일함수 code·실제 globals·JSON loads/default/class/encoder/scanner 변경, 실제 sys recursion/integer 제한 변경과 복원, missing/symlink/directory/FIFO/size/hash·새 값 소유권/파일 재읽기·원 오류 cause/context를 대조했다. 초기9/이전 v2의25를 최종25에 더하지 않는다. 모든 외부 권리/제품 callback·보안의 완전한 폐쇄를 증명하지 않았다.

## 최종 guard를 포함한 실제 비용: 실패

원 CASE6/64/output0..64/8/chunk1·41준비 뒤 worker before/private advance/독립 confirm ABBA42..45를 한 번 비교했다. guard snapshot·canonical/fallback 비용을 모두 포함했다. 두 candidate는 fast490/500·fallback각7이었다.

| 순서 | 모드 | quantum | 실제 시간 |
|---|---|---|---|
| 1 | baseline | 42 | 8.162181448초 |
| 2 | candidate | 43 | 8.462705843초 |
| 3 | candidate | 44 | 9.177115342초 |
| 4 | baseline | 45 | 9.205005324초 |

평균 감소율 **−1.569825%**, 짝별−3.681913/+0.302987%다. 사전 평균2%/양짝 감소를 통과하지 못해 **미채택**한다. 원 checkpoint bytes/counts/UTC84/86/88/90.123456Z·current15/순서·SQL9,929/role273/원천2,280·SQL map은 같았다. 한 짝의 작은 이득이나 앞선 무보호7.911314%를 제품 개선으로 쓰지 않는다. 같은 후보를 타이밍 선택용으로 재실행하지 않는다.

최종 경계 guard0.864643초·단일79,118,336/합451,661,824bytes, 비용 guard156.175887초·단일125,038,592/합608,739,328bytes다. 모든 실행은5root/원본2,148/두 frozen source/자산·FD4→4·소유 PG/비좀비/임시/passfile0을 통과했다. 제품 app261/d477b74b…는 그대로이며 기존82/전체 backend/browser/원64는 재실행하지 않았다.

## 초기 상태 학습의 실제 반례

추가 counterexample1검사에서 custom f._json을 **guard 모듈 import 전**에 설치했다. guard는 그 상태를 BASE로 학습해 compatible=True였고 원 경로 RuntimeError/후보 정상 값의 차이가 실제 발생했다. custom 설치와 새 private 모듈·FD는 정리/복원했다. guard1.115267초·합448,307,200bytes·소유 잔여0이다. 최종25 통과만으로 초기 module 상태의 정당성을 수용할 수 없다. 이 반례와 비용 미달 때문에 제품 구현/관련 회귀로 진행하지 않는다. 앞선 비용1은 성능 가능성의 역사적 기록으로만 유지한다.

## 다음 경계와 수용 기준

기존 인코딩 trace의 _blob canonical 경로는517회·328.397455ms였고 fresh-tree 구성요소 약12% 이득은 전체 실행 이득이 아니다. 원 파서를 유지하는 정규화 아이디어도 검토했지만 별도 guard/전체 비용을 통과한 변경은 없다. 그 구성요소 숫자를 근거로 무보호 옵션을 적용하지 않는다.

현재 늦은 quantum profile의 role audit273회·중첩 포함2.917404초와 driver wait/SQL9,929를 근거로 다음은 **인접 table/column 권한 matrix 두 SELECT의 조건부 평가 가능성 검토**다. 새 서비스/DB 함수나 schema를 추가하는 작업이 아니다. [이전4문장 묶음 반례](solar-role-tail-protocol-and-cursor-evaluation-20261020.md)는 유지한다. [공식 CASE](https://www.postgresql.org/docs/16/functions-conditional.html#FUNCTIONS-CASE)는 필요한 분기만 평가하는 설명과 planning-time 예외를 함께 명시하며, [CTE materialization](https://www.postgresql.org/docs/16/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION) 문서만으로 원 두 statement의 현재 snapshot/오류 순서를 증명할 수 없다. 공식 자료는 아래 실험의 출발점이며 최적화 승인이 아니다.

먼저 현재 두 원 SQL/인자·table-first RolePolicyHold·뒤 column SQL 오류의 실행 여부/transaction 상태·READ COMMITTED와 동시 grant/함수 변경 경계를 대조한다. 정확한 기존 반례를 같은 소유 SCRAM에서 재현하고, 조건부 SQL 후보가 같은 첫 오류와 현재 검증을 보존할 때만 사설 실제 비용 비교를 고려한다. planner의 선평가나 statement snapshot 차이를 해결하지 못하면 후보를 제외한다. 제품 수용에는 최종 source의 현재 권리/철회·오류·정리와 실제 전체 quantum 평균2%/양짝 감소·관련 회귀가 여전히 필요하다. 원 권리/감사 결과 cache·새 DDL/기반 서비스·일괄 후속 SQL 실행·원 actor/input/chunk/poll/retry360/RSS 변경은 없다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 사용자 적용, 실제 농장 자료/독립 작기·G0–G4는 남는다. 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh의 실제 문맥·사전/소스/종료 해시를 결속했고 재귀 CLI/하위 에이전트는0이다.

## 사용자 상태 게시와 검증 범위

[상태 게시 증거](artifacts/solar-codec-dispatch-status-publication-20261020.json): 두5173/5174 HTTP200·동일 최신 상태/no-store, frozen HTML/환기2,173/5root/원본2,148·FD4→4·소유 PG/비좀비/임시0을 확인했다. guard2.391801초·합494,309,376bytes다. UI code·browser DOM/WebGL·전체 backend·원 정상64는 재실행하지 않았다.
