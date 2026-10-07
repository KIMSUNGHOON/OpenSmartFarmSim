# 새 계산 결과의 검증 증명 — 로컬 수용

2026-10-07 KST. `crop-cycle-calculation-result-evidence`를 자체 소유 합성 자료의 작은 소프트웨어 범위에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-result-evidence-reference-20261007.json)에 실제 시험·참조 호출/출력의 SHA,
실행 당시 source·native CLI `gpt-6.1-sol / xhigh` turn context를 기록했다. 재귀 CLI 실행은0회다.
이 증명은 농장 권리나 G0–G4 승인, 실제 농작물 정확도의 증거가 아니다.

## 변경과 검토

[새 module](../backend/app/crop_cycle_calculation_result_evidence.py)은337줄이다.
원18함수 중11함수의 AST는 같고7함수는 새 판본·문맥/provenance·현재 snapshot 결속을 검토했다.
추가3함수는 공식 계산 manifest 변환과 저장 metadata의 SHA 대사다.
원 evidence/artifact/계산 소스와 기존55 source SHA는 그대로다. 새 서비스·queue·framework는 없다.

- 새 authority/type·판본 `crop-cycle-verified-result-evidence-v1`·별도 HMAC domain과 입력 key와 다른 결과 key를 사용한다.
- 발행은 공식 계산 context와 새 artifact의 원 전체 QC를 실제 실행한다. 전후 입력/결과 bytes·inode/HEAD/source를 대사한다.
- 검증은 원 입력 authority가 확인한 context에서 공식 manifest 변환만 적용한다.
  원 validated context SHA·새 calculation context SHA·input evidence SHA를 구분하며 token을 주입하지 않는다.
- 별도 Python의 검증에서 parser·context factory·전체 prefix/delta QC·advance/RHS는 실행하지 않는다.
- 실제 header/commit에서 원 summary/index의 SHA를 구성해 snapshot에 결속한다. 유효 HMAC여도 저장된
  121상태·clock·확인 과거·페이지/manifest와 다른 요약을 반환하지 않는다. 이 metadata 읽기는 원 수지 QC가 아니다.
- bounded0400 파일·현재 hash/canonical JSON·닫힌 형식,8MiB 증명과 원 파일/commit/저장 한도를 유지한다.
  summary/index/context/identity는 사본이며 `rights_or_gate_approval=False`다.

## 실제 시험

| 실행 | 결과 |
| --- | --- |
| 단순 판본 이식 뒤 실제 정상 경로 | 3실패/4.49초·종료1: 구형 context를 새 artifact에 전달 |
| 공식 context/provenance 연결 뒤 첫 실행 | 새41통과/64.11초·종료0; 아래 실행과 중복 |
| 새77개 + 원 결과41개 + 입력33개 | 151통과/166.56초·종료0 |
| 추가한 유효 hash 고아 파일의 발행/조회 거부 | 2통과/4.00초·종료0 |

**새79개·선행74개, 고유153개를 분할 검증했다.** 단일 전체153개나 전체 backend 실행으로 표시하지 않는다.
추가 시험 전151개 test source가 현재 파일의 정확한 prefix인 SHA를 확인했고 제품 module은 동일하다.
초기 잘못된 작업 경로·module 부재 수집 오류·system Python의 pytest 부재는 환경/수집 오류이며 행동 RED로 세지 않는다.

정상/수치 hold·사본/단위/UTC/provenance, 유효 HMAC의 잘못된 validation/code/clock/state/확인 과거/index/inventory,
다른 key/ID/version·구형 증명 혼합, 크기/중복 key/비정규 JSON, 현재 파일·권한/링크/inode/source,
발행 중 입력/HEAD 변경과 검사 중 교체, 실제 QC 실패·미완료·고아 파일 거부 및 FD 정리를 확인했다.
유효 HMAC를 시험에서 다시 만드는 key는 자체 작성 시험용이며 외부 자료/운영 자격증명이 아니다.

## 새 자체 합성 참조와 별도 Python

[참조 실행기](crop-cycle-calculation-result-evidence-reference.py)는 자체5시간/60구간·10초 RK4 입력을 새로 쓴다.
과거166일 artifact나 등록 농장 이력을 새 판본으로 재표시하지 않는다. 정상/마지막 관리의 수치 hold 두 사례다.
각각 원 artifact reader의 전체 행/요약과 **새 Python exec child**의 증명·모든 행/UTC SHA를 대사했다.
child는 원 parser/context/QC/advance/RHS8곳을 금지했고 모두0회다. 이는 새 typed page reader 수용이 아니다.

| 항목 | 정상 | 확인 과거 hold |
| --- | ---: | ---: |
| 실제 걸음 / 계획 | 1,800 / 1,800 | 1,800 / 1,800 |
| 원 시점 / 사건 | 61 / 3 | 60 / 2 |
| 증명 bytes | 19,412 | 24,102 |
| 발행 시 원 전체 QC | 1회 | 1회 |
| 증명 발행 | 0.200342초 | 0.196131초 |
| 별도 Python 검증 | 0.016934초 | 0.018343초 |
| 별도 Python 전체 원 행 대사 | 0.037860초 | 0.036502초 |

정상의 전체121개 checkpoint state/clock/cursor·원 summary/index와 hold의 이유/확인 과거를 그대로 보존했다.
참조 호출은 종료0/40.281057초, 주 실행의 관측 peak RSS87,302,144bytes다.
FD는 주 실행과 두 child 각각4→4, context/input/page cache는 닫히고 비었으며 child PID 두 개가 모두 없다.
키·증명·원 자체 파일/명령/출력은0700 사설 경로/0400 기록으로 보존했다.
실행 당시 계약 SHA를 영수증에 보존했으며, 수용 상태/다음 계약의 문서는 실행 후 갱신했다. 제품3 source SHA는 동일하다.

## 다음 수용과 남은 의존성

이 증명 자식만 체크한다. 다음은 [새 조회 전용 타입의4 core파일 계약](../contracts/crop-cycle-calculation-result-read-context-v1.md)이다.
원값/UTC·sample64/event8·응답2MiB·byte-short/관리 전후·현재 bytes·사본/변조·별도 Python·FD/cache를 검증한다.
이식/대사1시간과 실제 시험/참조/기록1–2시간의2–3집중시간 잠정이며 전체 제품 완료일이 아니다.
앞 증명의2–4집중시간 잠정은 이번 실제 수용으로 대체한다.

새 증명의 전체166일 크기/추가 metadata 대사 비용, 등록 계산 누적 prefix 비용, farm/DB 현재 query,
공개 판본/operator-config/API runtime·HTTPS30초와 같은 UTC3D는 아직 검증하지 않았다.
이후 수확/생과 → 물/양분·구매 에너지 → Decimal 경제 연결이 남는다.
전체 backend/browser·hosted CI·농장 현장/미래 검증도 이번 수용에 없다.
승인 실제 품종 입력·국내 독립 검증 자료·실제 작물 Run은0건, G0–G4는 `not_assessed`다.
전체 등록 경로와 외부 자료 실측 전에는 최종 완료 날짜를 확정하지 않는다.
