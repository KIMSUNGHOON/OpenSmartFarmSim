# 조달된 잎·기후의 원 적분량에 따른 줄기 시계 — 연구 v1

상태: [20검사·독립114시점/456산술 수용](../research/crop-funded-shoot-clock-20261026.md). 기존 [줄기 시계](crop-rational-morphology-clock-v1.md)는 구간별 고정 실내 기온이며
[개별 잎·기후 재개](crop-leaf-funded-birth-continuation-v1.md)는 같은 RK4의 동적 Ta 적분량을 보관한다.
두 결과의 시각만 일치시켜 공동 기온 시계로 주장하지 않는다.

`derive_funded_shoot_clock(leaf_directory,stem_directory,access,*,leaf_root_sha256,stem_root_sha256)`는
호출자가 신뢰한 원 두 root의 계산 없는 reader·stem 원 초기 state를 사용한다.
source/코드/권리와 원 stem program SHA·초기 state/age·명시 기준온도/ID를 결속한다.
양쪽 원점과 초기 시각은 같아야 하며, leaf frame0의 경과 초/기온 적분량은0이다.

각 원 frame에서 초기 줄기 나이에 `(I_Ta−I_Ta0−Tbase·elapsed)/86400`을 더한다.
원 cumulative `degC_s` binary64 값을 Fraction으로 정확히 표현해 차이를 계산한다.
이는 **저장된 RK4 수치 적분량으로부터의 나이**이며 연속 기온의 해석적 정확해가 아니다.
원 동적 잎의 signed/no-clip 기온 정의를 사용하고 음의 최종 나이는 보류한다.
순간 기온의 기준 이하 여부나 단조 출현 조건을 endpoint만으로 증명하지 않는다.

분수 초/같은 시각의 point 전후 phase·사건번호·원 CP/상태·I_Ta를 보존한다.
원 초기 절간들의 ID/명시 출현/기준온도·초기 나이도 같은 수치 적분량에 따라 연결한다.
같은 시각 점 전이에서 기온 적분/줄기 나이가 바뀌면 거부한다.
원 root/코드/모든 선택 bytes는 반환 전 재검사한다. 입력 파일/모델·계수는 변경하지 않는다.
512frame/512초기기관·2MiB결과·600초와 정확 유리수1024자리 상한을 유지한다.

새 마디/정확 threshold crossing·출현 시각을 보간하거나 길이/부착 위치·초기 질량을 만들지 않는다.
기존 고정기온 stem 결과는 초기 source 역할이며 이후 pose는 이 시계와 일치한다고 주장하지 않는다.
실제 초기 C/농장·현재 권리 검토/farm 서명·G0–G4/R2 승인은 별도다.
개발은 자체 합성으로 계속하며 이 자식만으로 source-clock-attachment 부모를 완료하지 않는다.

수용: 실제 funded producer의6조건/출현 전후·분수 초/같은 시각, 독립 Fraction 산술·원 초기기관 나이,
원 metadata/bytes·코드/정책/권리·음의 나이/원점·초기 시각 불일치 거부,
별도 cold 조회의 생장 import/DB/CLI/network/쓰기0·WSL/원 GUI 보존을 확인한다.
