# 현재 환경 입력의 미소비 문턱: 수치 근 정밀화 v1

상태: **합성 수치 근 정밀화 수용 — 2026-10-31 KST.** [103검사/실제 두 계획·보존](../research/supply-forcing-threshold-20261031.md)을 근거로 한다.
[forcing owner](supply-forcing-owner-v1.md)의 실제 확정 상태와 저장된 pending page를 사용한다.
구현은 `backend/app/crop_supply_forcing_threshold.py`의 다음 별도 계산 함수다.

```python
locate_threshold(
    handle, pending_page_sha256, time_tolerance_seconds_exact,
    *, cancelled=None, wall_seconds=60,
) -> dict
```

## 원 자료와 보류 구간

handle은 실제 새 forcing owner가 발급한 객체여야 한다. 변경하지 않은 owner `_session/_restore`에
실제 정의/참조·held stores를 전달하고 handle의 current/basis/cursor bytes를 정확히 대사한다.
이전 Context/CP/owner token을 만들거나 수치 DTO로 source를 대신하지 않는다.
원 source와 새 계획/모든 span의 AND 권리를 보존한다. private:false를 공개 권리로 올리지 않는다.

pending page는 같은 정의·확정 cursor를 가리키는 closed `supply-forcing-pending-page-v1`이어야 한다.
현재 적용된 span의 다음 원 격자/forcing edge/끝으로 정해진 그 **미확정 구간만** 수용된 kernel로
다시 계산하고, 저장 pending 결과 전체·reason을 정확히 비교한다. 현재1/새4=5RHS이며
과거 확정 구간을 다시 적분하지 않는다. source 복구와 무계산 조회 API를 생장 계산으로 바꾸지 않는다.
current=None/awaiting_material·미소비 threshold/원점·sequence·같은 active RHS/flux를 유지해야 한다.

입력 허용 폭은 양의 정확 유리수 초이며 해당 구간보다 크지 않다. 계산과 결과는 처음 접수한
불변 Fraction 값에 묶는다. 호출자의 사전 객체가 나중에 바뀌어도 결과에 다른 허용 폭을 기록하지 않는다.
코드·원 source/profile·정의/선택 current/history·pending blob의 fence를 계산 전후 확인한다.
늦은 변경/손상·권리/재계산 불일치는 root를 제거한 hold와 과거 참조/실패 stage로 남긴다.

## 근의 의미와 순서

기존 [funded-event-time의 수치 방법](crop-funded-event-time-v1.md#method-and-root-certificate)을
변경하지 않고 재사용한다. 네 실제 RK4 단계의 실내 기온과 원 기준온도·누적 시계/문턱에서
동일한 3차 continuous-extension 다항식을 구성한다. 기존 trace의 열적 시계 certificate와
계수/미분 최솟값이 정확히 같아야 한다. 원 실제 경계의 반올림 누적 나이와 이상 다항식의 끝 차이는
보고하되 보정하거나 시계를 문턱에 맞추지 않는다.

닫힌 구간에서 미분 최솟값이 **엄격히 양수**이고 왼쪽 잔차<0≤오른쪽 잔차여야 한다.
정확 유리수 이분법은 최대128회이며 각 반복에서 wall/취소를 검사한다.
반환 lower/upper의 시간 폭은 접수한 허용 폭 이하다. 네 기온이 기준온도보다 높다는 것만으로
다항식의 단조성을 승인하지 않는다. 정밀도 한도를 넘으면 hold다.

이는 **그 수치 다항식 안의 근을 감싼 범위**다. 물리 ODE/실제 출현 시각의 오차 한계,
이전 적분·측정/매개변수 오차, 기관 상태/물질 채택을 보증하지 않는다.
root는 적용된 forcing의 시작 뒤에 있어야 한다. 다음 forcing edge보다 앞인지 구간 포함 또는
해당 끝의 엄격한 잔차로 증명한다. 다항식의 근이 바로 다음 edge와 일치하면 수치 근 증거는 남기되
`ORDER_HOLD`를 유지한다. 실제 동시 관리/물질 사건 순서 정책을 이분법으로 승인하지 않는다.

## 결과와 한도

`root_located`는 원 정의/cursor/pending·numeric/span/interval 입력 hash, 원 schedule/권리,
다항식/미분·반올림 차·원점/정확 root bounds·signed residuals·forcing 순서와 실제 계측을 담는다.
`checkpoint_issued=False`, `history_committed=False`, `material_consumed=False`다.
기관 상태·새 CP/이력·material point를 만들지 않고 locator는 CAS/DB/API/CLI/network에 쓰지 않는다.
별도 관찰자가 private 파일에 결과를 기록하는 것은 제품 게시가 아니다.

wall1–60초의 전체 deadline에서 kernel에 남은 예산만 전달한다. 재계산 실패의 부분 RHS 횟수를
알 수 없으면 unreported로 남긴다. 결과≤2MiB와 기존 source/current/CAS 상한을 유지한다.
같은 고정 owner 계획을 full/split/cold로 실행해 얻은 같은 pending page는 같은 근 결과를 낸다.
이 계산에서 cold는 원 handle 복구를 뜻하며, locator의 미확정 구간5RHS와 구분해 보고한다.

## 수용과 다음 상태

실제 genuine pending/단일 구간5RHS·과거 확정 재적분/쓰기0, 독립 고정밀 root/잔차·반올림 차,
full/split/fresh-process 결과 일치, forcing 앞/뒤/일치 보류·단조성/정밀도/허용 폭·취소,
잘못된 source/page/trace/code와 늦은 변경, 입력 사전 변경·원 자료/기존 화면/WSL 보존을 수용한다.

다음은 이 root bounds에 결속한 **수치 상태/적분량 후보와 국소 간격 축소 진단**이다.
기존 state 계약의 upper-bound 선택·무시계 보정과 실제176상태/185누적/124계정·원 point/기원,
도메인/동일 시각1·2·4 substeps 대사를 먼저 설계/검증한다. 옛 funded 상태의 권한/크기 수용은 이전하지 않는다.
명시 물질 조달/새 기관·layout·원자 채택/원 격자 잔여 재개와 반복·긴 작기/같은 상태3D는 그 뒤다.
실제 품종/독립 자료·G0–G4/R2, 생산·자원 구매/경제·거시/수급·자율 비교/최종 UI는 별도 미완료다.
