# 전체 원 격자와 참조 저장 용량 수용

2026-10-08 KST. [관측 계약](../contracts/crop-cycle-calculation-full-capacity-v1.md)의 RHS0 용량 자식을
**고유10개·원 명령 종료0·최종 source/PID 감사로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-full-capacity-reference-20261008.json)의 SHA는
`4b04c305c3c8b7b3c8e1d95195acef6bf7aaf90daa537b0afde212bbcce35f84`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했으며 재귀 CLI는0회다.

## 전체 격자·원량

고정된 전체166일 소유 합성 달력의47,811경계를 읽고 요청4,096전이/10,000걸음·실효128경계로 나눴다.
결과는 **456묶음**, 최종 정수 위치는1,864,515전이/1,816,704걸음·47,809출력/5사건이다.
처음 두 정수 위치·cursor/count는 실제 등록4,096/8,192 checkpoint와 같다.
이 정수 계획은 상태 벡터가 없으며 crop checkpoint나 새 계산 결과가 아니다.

원 불변 artifact의14,567commit·모든 참조 page를 bounded canonical/SHA reader로 읽고
부모/순서·전체47,809행/5사건 hash를 선행 전체 수용과 정확히 대사했다.
명시 +273일 달력 이동 뒤 행 크기는 모두 같으며 이동 후 전체 행 hash도 사설/공개 영수증에 남겼다.
새 생장 계산·RHS·advance는 실제로 금지했고0회다. 모든 원/새 입력과 원 artifact를 보존했다.

## 참조 용량과 예약

| 항목 | 실제 원 행을 사용한 조건부 용량 |
| --- | ---: |
| 새 묶음별 참조 page 수 | 459 |
| 참조 page bytes 합 | 402,648,021 |
| 최대 한 묶음의 page bytes / page 수 | 954,453 / 2 |
| metadata/header/root/HEAD 상계 포함 artifact | 464,653,269 bytes |
| 최대 advance 예약 | 17,334,272 bytes / 40 files |
| 예약 포함 artifact / 기존 한도 | **481,987,541 / 536,870,912 bytes** |
| 예약 포함 artifact 파일 / 기존 한도 | 959 / 65,536 |
| 예약 포함 proof / 기존 한도 | 3,768,320 / 134,217,728 bytes |
| 예약 포함 intent / 기존 한도 | 485,952,469 / 671,088,640 bytes |
| 예약 포함 server root / 기존 한도 | 485,968,853 / 1,073,741,824 bytes |

commit별 metadata128KiB·header128KiB·root2MiB·HEAD8KiB와 proof별8KiB의 형식 상계를 적용했다.
각 page2MiB/128행·delta8MiB/16page·commit/file/proof/intent 개수 및 finalize/publish 예약도 통과했다.
artifact byte 여유는54,883,371bytes다. 한도를 높이거나 출력/사건을 줄이지 않았다.
이는 **같은 참조 행·깨끗한 단일 intent**의 조건부 용량이다.
신규 전체 실행의 실제 결과 크기·중단 후 orphan 공간·throughput/WSL 전체 메모리 수용은 아니다.
실제 writer/server의 현재 크기·예약·hold 검사는 그대로 필요하다.

## 검증과 자원

새 정수 planner 모듈 부재를 실제 RED exit2로 확인한 뒤 구현했다.
조밀한 경계·긴 간격·경계 대기·출력 없는 forcing·잘못된 grid9개가 통과했다.
최종 source 고정 실행은 이9개와 실제 전체 참조 감사1개를 합한 **10개/45.40초**다.
별도 초기9개 GREEN은 최종10개와 중복이며 더해서 고유19개로 세지 않는다.

원 명령/감독자 wall45.811초, 본문43.331초, grid 읽기11.162초다.
nice19·primary 표본 RSS140,320,768bytes/384MiB·FD12→12·context/cache 정리를 확인했다.
DB·브라우저·컨테이너·새 생장 계산을 시작하지 않았다.
원/새 각750입력과 원29,141 artifact의 hash/mode/identity, 선행276개를 포함한279 source를 보존했다.
실제 primary/controller 종료·원 로그 SHA·불변 사설 receipt를 대사한 최종 감사 뒤 source freeze를 해제했다.

## 다음 실행과 hold

관측 시점의 영수증은 `full_registered_execution_budget_fixed=false`다.
그 뒤 이 전체 용량·기존 전체 실제20,518.836초·남는 bytes/HMAC 이력 순회 구조를 검토해
[후속 지속 실행 계약](../contracts/crop-cycle-calculation-full-registered-run-v1.md)에9시간의 **실험 상한**과
RSS/중단/원 종료·fresh Python 복원·DB/권리/정리 수용 기준을 고정했다. 완료 시간 추정은 아니다.
다음은 작은 등록 감독자/런타임 검증이며 해당 증거 전 장시간166일을 시작하지 않는다.

전체 Backend·새 등록 전체166일 계산/DB/API/TLS/WebGL·fresh exec 등록 런타임·실제 제품 CLI는 실행하지 않았다.
최신 native 화면 원 명령 종료 기록 누락과 hosted Backend HBA 실패도 별도 hold다.
생과/물·양분/구매 에너지·작물 Decimal 손익, 실제 품종/국내 독립 자료/측정 농장 작물 Run0건,
G0–G4 `not_assessed`, 생산 예측·미래 마진·추천 hold를 유지한다.
