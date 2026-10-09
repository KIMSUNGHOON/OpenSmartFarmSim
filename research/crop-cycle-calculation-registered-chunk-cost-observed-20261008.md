# 등록 농장의 큰 계산 묶음·별도 프로세스 비용 관측

2026-10-08 KST. [관측 계약](../contracts/crop-cycle-calculation-registered-chunk-cost-v1.md)을
**실제 SCRAM1통과·원 명령 종료0·정리로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-registered-chunk-cost-reference-20261008.json)의 SHA는
`77b474287db375d56b2189c9ac6da05e522189af260a16ef7f08c1ba76dcc5b4`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는0회다.

## 실제 계산과 원 결과 대사

전체166일의 고정된 소유 합성 입력을 PostgreSQL16.15의 등록 농장/경제 달력에 연결했다.
두 실제 advance에 `max_steps=10000, max_transitions=4096`을 사용했다.
첫 묶음은 부모, 둘째 묶음은 별도 fork 자식에서 새 서버·입력 문맥·DB 연결로 계산했다.

| 항목 | 첫 묶음 뒤 | 두 번째 묶음 뒤 |
| --- | ---: | ---: |
| 누적 전이 / 적분 걸음 | 4,096 / 3,990 | 8,192 / 7,980 |
| 누적 출력 / 관리 사건 | 105 / 2 | 210 / 4 |
| 누적 commit / 상태 | 1 / yielded | 2 / yielded |
| 해당 advance wall | 50.212초 | 47.349초 |
| 해당 advance 실제 RHS 호출 | 20,056 | 20,056 |
| 해당 advance delta 물리 QC | 2 | 2 |
| 이어서 수행한 read-only checkpoint 조회 | 4.462초 | 4.512초 |

첫 checkpoint 전체는 선행 실제4,096 저장 증거와 계보 필드까지 정확히 같다.
두 번째 checkpoint는 원128전이64commit의6 provenance 필드를 구분해 대사했고
121상태·seed·clock/cursor·누적과 원210행/4사건은 명시한 +273일 달력 이동 뒤 같다.
원 수식·8초RK4·300초 출력·전체 입력·예산/행/bytes 한도는 바뀌지 않았다.

자식은 첫 checkpoint 전체를 현재 bytes/HMAC·농장 권리를 다시 확인하며 RHS0으로 복원했다.
둘째 묶음을 실제 계산해 종료0이었고 부모 재조회도 같은 확정 상태를 읽었다.
측정한 두 조회와 자식 복원에서 과거 delta QC/원 prefix 재검증은0회다.
현재 전체 bytes/HMAC 검사는 계속 실행했다. 원량 대사를 위해 관측 밖에서 수행한
독립 artifact 전체 QC는 이 조회 비용과 구분한다.

이 재개는 **fork**다. 새 Python 실행 환경·제품 CLI worker/설정 loader·독립 G1 해제를 입증하지 않는다.
앞선 별도 Python 파일 복원 증거를 대체하지 않으며, 등록 런타임 fresh exec 수용도 후속이다.

## 남는 비용

기존 비용 계측기의v2 wrapper/코드를 보존했다. 농장/시장/Decimal 참조 검증은 실제 수행했지만
이는 기존 농장 경제 입력의 현재 유효성 확인이며 작물 수확량과 손익의 신규 연결이 아니다.

| 측정 | 첫 advance | 둘째 advance |
| --- | ---: | ---: |
| RHS wall | 36.386초 | 36.474초 |
| 현재 input proof 검사 | 33회 | 26회 |
| 현재 artifact blob 검사 | 18회 / 2,946,538bytes | 37회 / 7,757,794bytes |
| 현재 농장 권리 검사 | 7회 | 5회 |

blob bytes는 반복을 포함한 실제 해시 읽기의 합이며 저장 용량이 아니다.
wrapper 시간은 중첩되므로 항목을 더해서 advance wall을 만들지 않는다.
전체 이력의 현재 bytes/HMAC 순회는 여전히 늘어난다. 두 초기 구간을 전체 완료 시간으로 외삽하지 않는다.

## 거부·보존과 정리

현재 입력 권리 철회, 계정 read scope 철회와 복사 packet의 같은 길이/mtime root·block 변조를 거부했다.
복사본의 정상 조회를 먼저 확인한 뒤 변조했으며 거부/조회 중 RHS를 금지했다.
선택한 HEAD/서명 이력은 그대로이고 yielded prefix의 DB 완료 게시도 거부했다.
준비 후 DB 행 수는 `[89,89,0,0,0]`으로 같아 새 작물 결과/Run/계산 게시 행은0이다.

원/새 각750입력·원29,141 artifact의 bytes/hash/mode/identity와 선행 증거를 보존했다.
276 source 중 선행274개는 모두 그대로이며 신규 core는 관측 계약/수동 시험뿐이다.
FD12→12·부모/자식 context/cache·schema/role/passfile0과 PG 한 cluster의 종료/경로 제거를 확인했다.
모든 host rule4개가 `scram-sha-256`이었고 실제 역할 연결의 SCRAM/used_password를 확인했다.
별도 최종 감사는 원 명령·로그 SHA·부모/자식/감독자/PG 시작 identity와 정리를 대사해 종료0이었다.
이 감사 뒤 source freeze를 해제했다.

pytest1통과173.26초, 원 명령/정리174.001초다.
시험 본문 관측157.584초는 전체 명령 시간과 범위가 다르다.
primary 표본 최대 RSS219,074,560bytes·당시 descendant RSS 합 최대299,700,224bytes는 process 표본이다.
WSL 전체 메모리/PSS나 production 성능 수용으로 표시하지 않는다. nice19·소유 계산 하나씩 실행했다.
최초 launcher 경로 오타는 script를 열기 전 종료2였고 그 기록을 보존했다.
시험은 정상 경로에서 한 번 실행했으며 관측 만료로 재시작하지 않았다.

## 다음 단계와 hold

다음은 RHS0으로 전체 원 격자의 묶음 수/행 경계와 참조 저장 용량·최대 예약 공간을 대조하는 단계다.
현재 bytes/HMAC 증가 비용을 함께 검토해 전체 등록 실행의 예산/감독·재개/정리 계약을 고정한다.
그 뒤 전체166일 terminal·DB 저장·현재 조회/API·같은 UTC3D로 진행한다.
이 관측으로 전체 실행 예산이나 최종 완료 날짜를 고정하지 않는다.

전체 Backend·전체166일 terminal·새 게시/API/TLS/WebGL·등록 런타임 fresh exec·실제 제품 CLI는 실행하지 않았다.
최신 native 화면의 원 명령 종료 기록 누락 hold와 원격 Backend HBA 실패도 별도다.
생과/물·양분/구매 에너지·작물 결과와 Decimal 손익, 실제 품종·국내 독립 자료·측정 농장 작물 Run0건,
G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
