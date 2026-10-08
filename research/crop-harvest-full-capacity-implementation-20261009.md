# 전체 합성 작기의 수확 수량·용량 대사

2026-10-09 02:48 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했다.
재귀 CLI0회. [불변 영수증](artifacts/crop-harvest-full-capacity-reference-20261009.json)의 SHA는
`e7759a81ed1e97e75057dc781eb442f276f71baba2c020f119d57960037913f9`다.
원 도구78826 종료0·집중38개·전체 대사 종료0·1,474 source 보존과 소유 정리를 확인했다.

## 산출물과 수용 범위

[3 core 계약](../contracts/crop-harvest-full-capacity-v1.md),
[오프라인 대사기](crop-harvest-full-capacity.py),
[집중 반례 시험](../backend/tests/test_crop_harvest_full_capacity.py)을 추가했다.
기존 종료0의 [전체166일 원 결과](crop-cycle-calculation-full166-same-db-completed-20261008.md)를 읽었다.
원 47,809 sample/5 event·commit/checkpoint 연결·UTC와 모든 행 hash를 대사했고 시간 이동은0회다.
919파일/404,673,556bytes의 내용·mode/inode, HEAD와 FD identity를 전후 비교했다.

기존 소유 fixture의 eta/DMC·6개 배정 규칙·합성 관측을 재사용했다.
`full166-synthetic-v1` revision에서 source와 전체 기간, 마지막 sample/event 선택 범위만 결속했다.
두 raw UTF-8/해시는 영수증에 보존했다. 실제 품종 계수나 농장 관측을 채택한 것이 아니다.
공개 영수증의 기존 게시 ID/payload와 고정된 원 artifact/manifest로 source를 식별했다.
현재 DB/HMAC/농장 권리를 새로 검증한 조회 객체를 만들지는 않았다.

| 대사 대상 | 실제 결과 |
| --- | --- |
| 전체 파생 행 | 47,808 원 인접 구간 + 5 원 사건 = **47,813행**. 원 위치/hash/UTC·순서 전부 검사 |
| 독립 수량 산술 | Decimal 2,200자리로 누적 차이/50과실 구획 합·질량 환산·정확 분수 배분·전체 목적별 합계·합성 관측 비교를 대사 |
| 반올림 수지 | 원 누적 차이/벡터 합과 반올림된 행 합의 잔차를 각 행 half-ULP 합 예산과 비교, 모두 이내 |
| 기관/목적 | leaf/stem 별도 집계·과실 환산 제외. harvest/thinning/disposal/sampling와 미배정·단위·합성/미평가 표시 유지 |
| 페이지 | 원 writer 규칙의64행/2MiB로 **748page/307,675,603bytes(293.42MiB)**. 최대481,468bytes/page·12,034bytes/row |
| root 여유 | 원 query identity를 제외한 알려진 필드와 빈 identity의 최소 크기95,883bytes. 나머지2,001,269bytes. 실제 identity/root는 후속 writer에서 확인 |
| 저장 상한 | 최대 root2MiB 두 번·HEAD8KiB와 페이지 atomic 예약을 포함해 **311,878,099bytes(297.43MiB)≤512MiB**. 파일 예약753≤65,536·page748≤16,384 |
| 실행 | 전체 대사 내부84.298초·실제 명령85.238초/종료0. 집중38개1.02초/종료0. controller 총86.834초/원1,200초 |
| 불변/정리 | RHS·새 증명/게시·DB/HTTP/subprocess 호출을 금지·0회. 원본/1,474 source·FD identity 보존, 두 소유 자식 종료·남은 자식0 |

저장 상한은 **root가 원2MiB 한도에 들어간다는 조건의 보수적 용량**이다.
파생 페이지의 바이트/hash는 실제 행으로 계산했지만 새 전체 artifact를 기록하거나 DB에 등록하지 않았다.
실제 원 query identity와 root 크기·현재 권리·전체 읽기 시간은 다음 단계에서 검증한다.

## 검증과 수정 이력

처음 repository root에서의 pytest 호출은 backend import 경로가 없어 수집 종료2였다.
backend 작업 디렉터리로 수정했다. 다음 시험은26통과/1실패였다.
누락 sample 반례가 제거 후 원 위치를 다시 번호 매겨 누락을 감췄으므로,
원 indexed sample을 보존한 상태에서 하나를 제거하도록 fixture를 수정했다.
집중36개가 통과한 뒤 첫 전체 대사 원79734도 종료0/86.042초였다.

검토에서 FD 개수만 비교한 필드명을 발견해 실제 dev/inode/mode/link identity 비교를 추가했다.
root의 알려진 metadata 크기도 별도 검사했다. 같은 FD 개수의 객체 교체와 root 최소 크기 초과
반례2개를 추가해 최종38개를 수용했다. 수정판 전체를 원78826에서 다시 대사했다.
두 전체 대사의 모든 수량/요약·profile·source·원 행 hash·전체 포장 page hash/bytes가 같다.
새 생장 RHS 실행이나 기존166일 계산의 재시작은0회다.

0.1초 표본864개에서 단일 PID 최대111,722,496bytes(106.55MiB)≤512MiB,
controller 포함 소유 RSS 합131,604,480bytes(125.51MiB)≤1GiB다.
nice19·순차 처리를 유지했다. PSS/WSL 전체 부하·표본 사이 최대치·운영 동시 처리 용량 수용은 아니다.

집중 시험은 작은 실제 writer의 페이지 바이트도 비교했으며,
원 UTC/계보/count/hash 변조·누락/순서·leaf-only·단위/목적/분수/수량/합계 오류와
페이지/파일/저장/root 한도 초과를 검사했다. 실제 전체 writer/DB/HTTP/브라우저는0회다.
제품 코드·의존성 잠금 변경0개, 전체 Backend/web/type/build·hosted CI/push는 이번에 수행하지 않았다.

## 다음 실제 실행과 의존성

`crop-harvest-full-capacity`만 체크한다. `crop-harvest-full-mass-load`와
`crop-harvest-replay` 부모는 미완료다. 다음 순서는 다음과 같다.

1. **실제 전체 부모 복원:** 보존된 전체 입력·artifact·농장/게시 metadata와 인증 자료의 재사용 가능성을 확인한다.
   이전 시험은 임시 DB/비밀 파일을 정리했으며 custody key는 원 실행에서 무작위 생성했다
   ([기존 실행 준비](../backend/tests/crop_cycle_registered_full_path_smoke.py)).
   archive가 있다는 사실로 현재 권리나 구형 서명 검증을 대신하지 않는다.
   기존 검증 경로로 새 현재 권한의 같은 전체 부모를 조회하고 원 source/UTC/hash와 대사한다.
   원 인증 자료가 없으면 새 검증 증명의 의미를 구분한 복원 계약/필요 최소 변경을 먼저 고정한다.
   구형 서명/계보 검사 우회·임의 DB 행 삽입으로 통과시키지 않는다.
2. **전체 writer/등록:** 영수증의 같은 raw profile과 source로 모든47,813행을 실제 기록·등록하고,
   전체 원 page hash/수량·실제 root/공간을 대사한다. fresh Python의 현재 권리·철회/계정 거부와 RHS0 읽기를 확인한다.
3. **실제 API/대표3D:** 전체 행 비교와 대표 frame 검사를 구분하고 원 명령 종료·WSL 소유 자원 정리를 확인한다.

첫 부모 복원은 입력/인증 자료와 기존 경로 대조0.5–1시간, 필요한 연결/복원1–2시간,
집중 실제 권리/정리 검증0.5–1시간의 **2–4집중시간/10월9일 KST 잠정**이다.
보호 자료와 호환되는 복원 경로가 남아 있다는 조건이며 누락 시 필요한 변경 근거로 재산정한다.
이번 오프라인85초를 전체 DB writer나748회 현재 조회의 시간으로 외삽하지 않는다.
실제 부모의 읽기/쓰기 비용을 측정한 뒤 원 전체 실행의 wall/disk 예산을 정한다.
그 뒤 기후→물/양분·구매 에너지→사용자 실행→같은 작기/달력의 Decimal 경제다.

이전1.5–3시간은 이번 수용으로 대체한다. 실제 품종 입력·농장 작물 Run·국내 독립 자료0건,
G0–G4 `not_assessed`, 생산/미래 마진/추천 hold와 전체 활성 goal을 유지한다.
자료 접근/이용권·독립 검증 일정이 없어 production 완료일은 확정하지 않는다.
