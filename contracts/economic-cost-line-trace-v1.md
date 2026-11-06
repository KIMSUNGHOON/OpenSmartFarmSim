# Cost.id별 조건부 비용 기여값 v1

상태: [233집중·독립 산술/별도 프로세스 수용](../research/economic-cost-line-trace-20261031.md). CostLineLedger(repository).calculate(schema4)는 새 CostTraceResult를 반환한다.
기존 ProductionBatchLedger/v10·입력/결과/공식은 보존하고 같은 Decimal _costs를 재사용한다.
이 함수는 명시 계산이며 저장 결과 reader나 HTTP에 금액 재계산을 추가하지 않는다.

새 trace_version/ID·코드/성분 지문·tenant/평가기간과 원 v10 전체 결과를 보존한다.
산출 금액의 통화는 원 원장과 같은 KRW로 명시한다.
각 line은 variable/fixed 구분·원 Cost.id/목적/batch/판매·quantity/단가/지급의 입력 판본/등급,
발생/지급 시각과 incurred·기간 내/후 은행 지급·원 상계·기간 내 상계·기말 미지급을 남긴다.
지급 미정은 null이다. 원 setoff는 현금 지급과 구분하며 비용을 새로 부과하지 않는다.
미선언 group(null)과 명시0 group(빈 배열+원0선언)을 구분한다.

원128자리 Decimal/Inexact 경계를 유지하고 항목 합계는 원 variable/fixed·batch 합계와 일치해야 한다.
새 계산/직렬화 진입점은128자리·ROUND_HALF_UP·표준 유한 지수 문맥을 명시해 호출자의 Decimal 상태를 격리한다.
원 ledger의 지급/미지급이 대사 가능한 경우 같은 범위의 기말 미지급을 대사한다.
미래 지급/상계는 원 future schedule의 해당 Cost.id 항목과 일치해야 한다.
월별 비용 지급분은 원 KST 달력의 양수 outflow component다. 알려진 부분과 미확인 총액을 구분한다.
이는 수금/환불/투자·대출 등을 포함한 원 월별 net과 다른 범위이며 net은 원 값으로 함께 남긴다.
독립 oracle는 혼합 현금흐름의 net과 비용 component를 구분해 대사한다.

입력/결과2MiB·원 현재 source/문맥/권한·최종 code fence와 repository identity를 검사한다.
원 v10 결과/코드를 덮어쓰지 않고 새 trace ID를 전 입력/출력·코드에 결속한다.
사실 값/품목/요금·가격/분배·수확/매출을 생성하거나 모델8counter를 구매량으로 바꾸지 않는다.

수용: 혼합 품목/목적/variable·fixed·batch·부분 선택을 식별할 전체 항목·원 입력의 정확 보존,
부분/미정/기간후 지급·상계·KST 경계·중복/누락·독립 Decimal300 산술과 기존 v10 원 bytes/수치,
현재/늦은 변경·코드/크기·반환 복사와 기존 경제 회귀다.
첫 slice는 계산 커널이며 불변 저장/실행/조회·SDK/창/3D 연결은 후속이다.
자체 합성 조건부 가정/G0–G4 미평가/R2 미승인이며 실제 농장/마진/추천 승인이 아니다.
