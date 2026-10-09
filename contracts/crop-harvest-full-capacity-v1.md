# 전체 합성 작기의 수확 수량·용량 대사 v1

선행: [작은 실제 화면 수용](../research/crop-harvest-view-native-implementation-20261009.md),
[전체 생장 결과](../research/crop-cycle-calculation-full166-same-db-completed-20261008.md).
이번 core는 이 계약, `research/crop-harvest-full-capacity.py`,
`backend/tests/test_crop_harvest_full_capacity.py`다.

## 입력과 경계

- 기존 종료0 영수증의 SHA·artifact root·원 47,809 sample/5 event hash를 고정한다.
  보존 archive를 nofollow/bounded reader로 읽고 commit/checkpoint/page 계보·UTC·개수를 검사한다.
  전후 파일 내용·mode/inode와 HEAD를 대사한다. 시간 이동·RHS·새 증명/게시·DB/HTTP 호출은 없다.
- 질량·배정은 기존 `test_crop_harvest.py`의 소유 합성 profile 생성기를 재사용한다.
  원 source, 전체 기간, 마지막 sample/event 선택 범위만 명시적으로 결속한 새 합성 판본이다.
  원 eta/DMC·6규칙·관측 fixture는 유지하고 원 raw UTF-8와 SHA를 기록한다.
  농업 계수 채택이나 관측 자료 수신을 뜻하지 않는다.
- 공개 영수증의 게시 식별자/manifest로 source를 결속한다. 현재 DB 권한·HMAC의 새 검증이나
  `CalculationCurrentCycleQuery`로 가장하지 않는다. archive 구조 검사와 기존 수용을 근거로 하는 오프라인 대사다.

## 수용 기준

1. 원 모든 구간/사건의 과실 제거→질량→배정을 처리한다. 원 위치·hash·UTC 순서,
   leaf/stem 분리, 네 목적과 미배정, 단위·합성/미평가 표시를 보존한다.
2. 독립 Decimal 산술로 원 누적 차이/50구획 합, 질량 환산, 정확 분수 배분과 전체 합계를 대사한다.
   누적 차이의 float64 반올림 잔차는 각 행 half-ULP 합의 명시적 예산과 비교한다.
   생성 함수가 낸 합계만을 정답으로 사용하지 않는다.
3. 실제 canonical 파생 행으로 기존 writer의 64행/2MiB 페이지를 포장한다.
   page hash/최대 bytes·개수, 전체 bytes와 root 최대 2MiB/HEAD/atomic 쓰기 예약을 포함한
   보수적 상한을 기존 512MiB/65,536파일/16,384page에 대조한다. root 실제 크기는 후속 writer에서 확인한다.
4. 순차 nice19·원 1,200초 감독 예산, 단일 RSS 512MiB/소유 합 1GiB·FD/자식 정리를 기록한다.
   전후 원본·소스 hash와 원 도구 종료0, 집중 반례 시험을 확인한 뒤 체크한다.
   수치/저장 한도 초과는 hold이며 계수·원 행·상한을 바꿔 통과시키지 않는다.

## 후속

산출물은 전체 수량/용량 보고서·불변 영수증과 다음 실제 실행 예산이다.
이 대사는 전체 writer/DB 등록·fresh Python 현재 권리 복원·HTTP/대표 WebGL의 수용이 아니다.
그 실행은 `crop-harvest-full-mass-load`에서 측정한다. 그 뒤 기후·물/양분·구매 에너지,
사용자 실행·같은 작기의 Decimal 경제를 연결한다. 생산/미래 마진/추천과 G0–G4는 기존 hold를 유지한다.
