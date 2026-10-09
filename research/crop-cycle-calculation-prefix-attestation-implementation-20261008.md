# 현재 bytes와 새 delta 검증 증명의 최종 권한 경계

2026-10-08 KST. [개발 계약](../contracts/crop-cycle-calculation-prefix-attestation-v1.md)의
최종 제품 코드 `9d914d3`을 **고유208개 분할·실제 종료/정리로 로컬 수용**했다.
[최종 불변 영수증](artifacts/crop-cycle-calculation-prefix-attestation-headfence-reference-20261008.json)에 실제 명령·종료/로그 SHA,
실행 당시266 source·원량/권리/복원·32회 곡선과 최종 감사를 보존했다.
판단은 기존 native Codex CLI `gpt-6.1-sol / xhigh`에서 수행했고 재귀 CLI0회다.

## 구현과 검토에서 수정한 두 경계

새 private custody/intent/HEAD proof는 v2다. writer와 독립 publisher가 실제 새 delta를
각각 검증한 뒤 validator source·checkpoint/counts·summary를 서명한다.
재개/진행 조회는 전체 HMAC 체인과 모든 참조 파일의 현재 전체 bytes/SHA·형식·소유/권한·한도를
검사해 증명을 소비한다. 닫힌 불변 prefix 객체와 detached 복사만 writer로 전달한다.
현재 입력·권리를 metadata/mtime cache로 대체하지 않는다.

최초329개 검증 뒤 재개 factory의 진입/종료 입력 검사 누락을 실제 RED로 확인했다
(1실패/22미선택·종료1). 두 `artifact._check`를 복원한 `2fcfa4b`는97개를 통과했다.
[그 판본의 영수증](artifacts/crop-cycle-calculation-prefix-attestation-reference-20261008.json)은 그대로 보존한다.
후속 검토에서 candidate bytes 검사 뒤 권한을 철회하면 오류는 반환하지만 HEAD가 이동하는
반례를 다시 확인했다(1실패/2통과/23미선택·종료1). candidate 검사 뒤 마지막 guard가 오도록 복원했다.
최종 순서는 **현재 권리 확인 → proof fsync → candidate 현재 bytes 검사 → 마지막 현재 입력/권한 검사 → atomic HEAD**다.
root/block 변조와 권한 철회 세 반례 모두 최종 회귀에 포함했다. 검사 횟수와 수식은 그대로다.

원 context/입력 증명/farm/artifact source, 수식·8초 RK4·300초 출력 격자,
최종 결과 증명/DB 게시의 전체 물리 QC는 보존했다. v1 bytes는 당시 고정 코드의 재현 대상이며
새 코드가 자동 복원·변환하지 않는다. 새 서비스/schema/runtime 설정은 없다.

## 최종 수정판 검증

| 검증 | 실제 결과 | 감독자 포함 시간 |
| --- | --- | ---: |
| 집중 회귀: prefix26·서버50·입력11 | 87통과 / 종료0 | 69.805초 |
| 실제 SCRAM 농장 권한·재개·철회 | 12통과 / 종료0 | 233.237초 |
| 결과 게시·실제 DB·원 형식 공존 | 96통과 / 종료0 | 535.480초 |
| 현재 농장/DB 조회 | 12통과 / 종료0 | 466.524초 |
| 같은 전체 입력의 초기32회 | 1통과 / 종료0 | 339.187초 |

합계208개이며 앞선329개·97개를 더하지 않는다. 각 명령의 실제 종료0, 로그 SHA,
원 PID/감독자/queue/PG의 시작 identity와 종료·temp/data/passfile 정리를 별도로 감사했다.
전체 Backend·새 브라우저·전체166일 등록 terminal/DB/API/3D는 실행하지 않았다.

## 같은 전체 입력의 실제32회

| 항목 | 이전 수용 판본 | 최종 수정 판본 |
| --- | ---: | ---: |
| 실제 advance / 누적 걸음 | 32 / 3,990 | 32 / 3,990 |
| 확정 시점 / 관리 사건 | 105 / 2 | 105 / 2 |
| 저장 파일 / bytes | 68 / 1,113,726 | 68 / 1,113,726 |
| 전체 명령 시간 | 358.024초 | 339.187초 |
| advance 시간 합 | 304.344초 | 290.225초 |
| delta 물리 QC | 1,056회 | 64회, 호출마다2회 |
| 과거 `_load_prefix` QC | 63회 | 0회 |
| advance 입력 proof 검사 | 839회 | 839회 |
| 조회 RHS / FD 전후 | 0 / 12→12 | 0 / 12→12 |

고정32회와 checkpoint 전체·단계별 counts/steps/저장량이 같고 원 순수 결과와도
명시한 +273일 이동 및6개 provenance 필드 구분 뒤121상태/seed/clock/cursor·확정 행을 대사했다.
fresh 서비스 복원·현재 권리/계정 거부·미완료 게시 거부와 원 DB 행을 확인했다.
원/새 각750개 입력·원29,141개 artifact 및266 source를 보존했다.
advance 입력 검사839회와 별도 진단 포함 aggregate 869회를 구분한다.
과거 누락 판본의777회는 채택한 최적화 결과가 아니다.

비용 계측 v2는 prefix/new delta/current blob wrapper를 추가했으므로 v1과 exclusive 시간을
같은 지표로 비교하지 않는다. 현재 전체 bytes/HMAC/metadata 순회 비용은 남는다.
proof 33파일/40717bytes,
단일 최대 1244bytes로 기존 한도를 지켰다.
nice19에서 소유 PG/계산을 하나씩 실행했고 pytest primary의 표본 최대 RSS는
253587456bytes다. WSL 전체/PSS 측정이 아니다.
실제 종료·원 파일/source·정리를 감사한 뒤 source freeze를 해제했다.
영수증의 계약 SHA는 실행 당시 판본이며 이후 이 수용 기록 수정과 구분한다.

## 다음 단계와 보류

다음은 현재 전체 bytes/HMAC/metadata 순회의 누적 비용을 줄일 수 있는 계산 묶음 경계의 확인이다.
순수 엔진이 이미 지원하는4,096전이와 기존128전이32호출을 같은 경계에서 대사한다.
그 관측만으로 artifact/서버의128전이 제한을 완화하거나 전체 실행 예산을 확정하지 않는다.
전체 등록 계산 → 저장/복원·같은 UTC3D → 생과 kg → 자원 → Decimal 경제 순서를 유지한다.

원격 `2a3e615`는 다른4workflow 성공, Backend 분할1/4/5 성공·0/2/3 및 집계 실패로 종료했다.
[고정 이미지의 공식 source 조사](ci-host-scram-primary-evidence-20261008.md)는 초기화 규칙의
혼재 가능성을 뒷받침하지만 실패 서버의 실제 HBA rows/platform은 없어 원인 확정은 보류한다.
현재 로컬 코드의 hosted 수용은 없다. CI 설정이나 인증 검사를 변경하지 않았다.

최신 native 화면의 원 종료 기록 누락 hold, 전체166일 등록 terminal/DB/API/3D와
생과/자원/경제 연결은 남아 있다. 실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건,
G0–G4 `not_assessed`, 예측·추천 보류를 유지한다. 최종 제품 완료 날짜는 확정하지 않는다.
