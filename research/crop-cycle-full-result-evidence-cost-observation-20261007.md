# 완료된 166일 원 결과의 증명·별도 Python 조회 비용

2026-10-07 KST. [전체 RHS 완료](crop-cycle-full-rhs-durable-completed-20261007.md)의 **소유 합성 원 artifact**에서
기존 result evidence/typed reader의 실제 크기·비용을 측정했다.
[불변 관측 영수증](artifacts/crop-cycle-full-result-evidence-cost-reference-20261007.json)에
실제 argv/종료·source/로그·원 증명 SHA와 자원/정리를 보존했다.
native Codex CLI `gpt-6.1-sol / xhigh`이며 재귀 CLI0회다.

## 실제 관측

원 입력/결과의 regular file·0400·현재 bytes/inode/HEAD와 원 전체 수지 검사를 유지했다.
결과 증명은 원47,809시점/5사건·14,567commit의 terminal/121상태와 전체 index/inventory를 서명했다.
원 `ResultEvidenceAuthority`와 `ResultReadContext`를 그대로 사용했으며 새 계산 판본으로 재표시하지 않았다.

| 범위 | 관측 |
| --- | ---: |
| 원 입력 증명 발행 | 33.332299초 / 148,989bytes |
| 원 결과 증명 발행(전체 QC 포함) | 175.675297초 |
| 전체 결과 증명 | 6,111,094bytes / 기존 한도8,388,608 |
| index / inventory | 2,458,956 / 2,666,222bytes |
| 같은 Python 결과 증명 검증 | 1.533085초 |
| **새 별도 Python** 결과 증명 검증 | **1.589495초** |
| 별도 Python typed reader 열기 | 3.558657초 |
| 첫64시점 page | 2.033227초 / 561,506bytes |
| 중간64시점 page | 2.035086초 / 536,874bytes |
| 마지막1시점 page | 1.661881초 / 8,445bytes |
| 전체5사건 page | 1.659134초 / 83,592bytes |

발행 뒤 검증·page에서는 원 input parser/context 준비·terminal QC를 실제로 금지했다.
RHS는 두 프로세스의 모든 단계에서 금지했으며0회다. 별도 Python의 원 terminal summary는
기존 결과 전체와 같고 선택 page의 원 UTC·개수·bytes/행 SHA를 기록했다.
입력·결과 증명은 사설0400 파일로 보존하며 repository/API에 raw proof나 key를 보내지 않는다.
사설8MiB와 공개 page2MiB는 서로 다른 한도다.

## 자원과 보존

관측은 원6시간 수치 실험의 예산 재설정이 아니다. 별도 read-only 관측 예산420초,
주 프로세스 RSS256MiB·nice19로 제한했다. 전체 controller wall225.950937초,
두 worker는 실제 종료0·FD4→4·PID 부재다.
200ms 표본 최대 VmRSS는 발행139,628,544bytes·새 조회182,333,440bytes였다.
확정 peak나 WSL/전체 자식 메모리 합계로 해석하지 않는다.
원 HEAD bytes·고정55 source와 추가4개를 포함한59 source 전후 SHA를 보존했다.
DB·서버·브라우저는 기동하지 않았다.

## 판단과 다음 구현

실제 전체 결과 증명이 기존8MiB 안에 들어왔으므로 출력/index를 자르거나 한도를 높일 근거가 없다.
175.68초의 전체 QC 발행은 HTTP 밖에서 수행하고, 현재 bytes와 저장 검증 증명을 사용하는 조회를 유지한다.
별도 검증/선택 page의 실측은 작지만 farm/DB/원 server trace와 응답 투영·전송 비용은 포함하지 않았다.
이 관측을30초 HTTPS/3D 수용으로 표시하지 않는다.

[새 조회 계약](../contracts/crop-cycle-calculation-query-v1.md)의 다음 evidence → reader → current query →
명시 API/runtime → client/같은 UTC3D로 연결한다. 새 공식 calculation context/manifest와 artifact 판본은
이 구형 proof가 받는 대상과 달라 별도 판본·원 provenance 대사가 필요하다.
등록 계산의 누적 prefix/서명·저장 비용은 읽기 개선과 독립적으로 실제 측정한다.

typed reader로 모든47,809행을 다시 조회하거나 byte-short/관리 전후·실제 farm/DB/HTTPS/WebGL,
새 calculation evidence·cache-cold/반복/저사양 기기 검증은 이번 관측에서 수행하지 않았다.
원 전체 QC/행 hash 수용과 이번 시작/중간/끝의129시점·5사건 선택 조회를 구분한다.
전체 replay-restore/부하 부모·G0–G4는 미수용이다. 실제 품종/국내 독립 자료·실제 작물 Run0,
생산 예측·미래 마진·추천 게시 보류와 수확/자원/경제의 남은 순서를 유지한다.
