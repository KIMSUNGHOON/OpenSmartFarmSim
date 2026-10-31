# 새 기관 전후 저장 창의 strict HTTP SDK v1

상태: [84신규·9회귀/전체 타입·실제 HTTP](../research/supply-material-http-sdk-20261031.md)의 증거가 수용된 범위다.
[공개 저장/export 계약](supply-material-public-replay-v1.md)의 고정 자체 합성106파일만 읽는다.
임의 외부 root의 농장 권한·현재 외부 권리나 실제 품종을 승인하는 인터페이스가 아니다.

`loadSupplyMaterialReplay(signal)`은 고정 namespace/root/index·115개 source code pin,
exporter/writer/NOTICE와 모든 파일의 원 hash/bytes를 검사한다. canonical wire tokenizer가
중복 키·깊이 초과·비유한 수를 거부하며 원 Python float token과 정확 분수를 유지한다.
파일당2MiB·전체64MiB·최대512frame/32768좌표·group1024descriptor/256cursor 제한을 적용한다.
경로는 평면의 허용 파일명만 받으며 credentials omit·no-store·redirect error로 순차 GET한다.

원본은 원본의 binding/context/checkpoint/material 계약으로 검증한다. 새 base/forcing/material은
자기 definition/basis/cursor/current/page/pending/point/origin schema와 참조로 검증하며,
536초의 새 numeric을 기존512초 Context/CP로 취급하지 않는다. 선택되지 않은 추가 blob도 거부한다.
use/display/redistribute가 모두 true인 입력과 source·plan·point/current 권리를 요구한다.

저장된 RK4 네 단계의 상태·시각·끝 상태/누산기는 정확 Fraction 산술과
binary64 인접값의 중간 경계/짝수 반올림으로 대조한다. 새 RHS/곡선/생장 전진은 실행하지 않는다.
저장 trace와 derived는 local producer witness이며 독립 현장 검증을 대신하지 않는다.
기관 목록·ID/부착·면적/길이/탄수화물·시계/기원·단위·lifetime/point/global 수지와 예산을 대사한다.
원 `material_before`는 dense-before이고 checkpoint가 아니다. 같은 정확 시각의
`material_after`와 이후 확정 current를 별개 frame으로 유지한다. 선언 종료가 격자와 일치하면
outer phase는 `declared_end`, 내부 수치 phase는 `original_grid_endpoint`일 수 있다.

`summary()`와 `frame(index)`는 매번 방어 복사한다. boolean/분수/범위 밖 선택은 다른 frame으로
바꾸지 않는다. `SupplyMaterialRequest.cancel()`과 새 `load()`는 이전 세대의 반환을 거부한다.
각 awaited read 전후에 abort를 검사하며 네트워크가 abort를 무시해도 늦은 결과를 게시하지 않는다.
HTTP 실패의 자동 재시도·캐시·자료 수정/생성·DB/worker/CLI는 추가하지 않는다.

이번 고정 창은4시점/722좌표·11→12잎이며 `covers_whole_season:false`다.
원 시각은 합성 모델 시계이고 실제 출현 시각 측정이 아니다. `G0_G4:not_assessed`,
`R2:not_approved`를 유지한다. 사용자3D/제품 API·실제 품종/생산·자원/경제/추천은 별도 수용이다.
