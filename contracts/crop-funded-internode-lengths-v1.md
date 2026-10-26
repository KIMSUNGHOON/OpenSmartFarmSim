# 공동 기온 시계에 따른 초기 절간 길이 — 연구 v1

상태: [22검사·독립342길이/114축합 수용](../research/crop-funded-internode-lengths-20261026.md). [수치 줄기 시계](crop-funded-shoot-clock-v1.md)의 초기 절간 나이를
기존 [canonical 길이 point](crop-internode-length-point-v1.md)에 연결한다.

`calculate_funded_initial_internode_lengths(leaf_directory,stem_directory,access,*,leaf_root_sha256,stem_root_sha256)`는
원 두 root와 초기 stem program을 읽고 같은 원 Ta 적분량의 나이를 사용한다.
원 초기 절간의 sequence/ID/출현·곡선/anchor/길이를 검증하고 원문 객체의 사본/지문을 보존한다.
초기 canonical 길이와 anchor는 기존 정규화로 검사하되, 요청 길이 오차를 새 성장 offset으로 만들지 않는다.
모든 후속 길이는 기존 point의 F(age)이며 과거 고정기온 길이/pose를 재사용하거나 비율로 늘리지 않는다.

동적 signed 시계와 기존 길이 상태의 지원 범위를 구별한다.
초기 나이/이전 확정 나이보다 되돌아간 sampled stem age는 길이 궤적으로 게시하지 않는다.
endpoint 검사는 구간 전체의 기온·나이 단조성이나 threshold 시각의 증명이 아니다.
같은 시각의 point 전후 나이/길이는 같고 원 index/step/phase/사건번호·exact 시각/CP/I_Ta를 보존한다.

각 원 절간의 새 나이/길이(m)·curve/초기 source/point 입력 지문과 초기 축 길이의 fsum을 반환한다.
축 합은 **초기 추적 기관의 합**이며 식물 키나 새 마디를 포함한 전체 길이가 아니다.
새 기관/3D 부착·공간 pose·mass/floor·관측 품종/현재 farm 검토·G0–G4/R2는 수용하지 않는다.
원 계산/point·clock·source pins와 원 두 manifest/program은 반환 전 재검사한다.
파일/DB/CLI/network 쓰기·과거 적분/clock advance0, 새 계수/기온 보충0이다.
512frame/512초기기관·2MiB 응답과 기존600초·exact1024자리 상한을 유지한다.

수용: 실제 producer6조건·분수/동시 point, 독립 Decimal 길이/축합과 원 초기 source/anchor 보존,
잘못된 길이/곡선/anchor/나이·되감기/단위/출처/권리·late code/source·응답 용량 거부,
최소/512 경계와 별도 fresh 계산·advance/DB/CLI/network/쓰기0·WSL/원 화면 보존을 확인한다.
