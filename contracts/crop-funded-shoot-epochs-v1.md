# 저장된 줄기 이력의 두 원점과 동적 기온 투영 — 연구 v1

상태: [25검사·독립163시점/659나이·496길이·163축합 수용](../research/crop-funded-shoot-epochs-20261026.md). 기존 원점 시작용 시계/길이 v1과 원 자료는 바꾸지 않는다.
`project_funded_shoot_from_stored_state(leaf_directory,stem_directory,access,*,leaf_root_sha256,stem_root_sha256,stem_start_index)`는
신뢰한 원 stem program 초기 상태(-1) 또는 실제 저장 frame(0 이상)을 선택한다.
원 root/program/선택 result/state SHA·index·시각과 전체 초기 state/curve/anchor/ID를 결속한다.
이력이 있는 상태를 나이0으로 초기화하거나 이전 기온 적분을 새 구간에 두 번 더하지 않는다.

선택 stem의 현재 UTC와 leaf의 시뮬레이션 원점이 같아야 한다.
stem 발달 원점은 별도 UTC로 보존한다. 원점 차이는 UTC 정수 초를 정확 유리수로 옮긴다.
각 frame의 원 at는 시뮬레이션 기준이며, development_elapsed는 원점 차이+원 exact elapsed다.
기존 절간의 출현 오프셋은 **발달 원점 기준**으로 남긴다. 음의 시뮬레이션 상대 출현을 새로 만들지 않는다.

새 줄기/절간 나이는 선택 상태의 원 나이+(새 I_Ta−Tbase×새 elapsed)/86400이다.
source 초기 prefix는0, 같은 시각의 조달점에서 I_Ta/나이는 불변이며 원 code/profile/phase/CP를 보존한다.
기존 canonical 길이 point·초기 정규화로 선택 시점 길이/curve/anchor를 보존한다.
축 합은 선택한 기존 기관들의 합이고 식물 키나 새 전체 축이 아니다.
음의/되돌아간 sampled 나이는 보류하며 구간 전체 단조성이나 해석적 정확해를 주장하지 않는다.

원 next threshold/phyllochron/순번과 기존 exact 열적 사건 커널로 endpoint 사이의 기준 통과를 열거한다.
각 candidate는 양쪽 원 frame/CP·정확 시간 구간과 thermal threshold를 보관한다.
이 bracket은 **정확 사건 시각이 아니며 새 기관/잎/조달점을 만들지 않는다**.
정확 within-step 시각/공동 ODE 사건 전이는 다음 수치 단계다. 원 고정기온의 이후 사건/pose를 가져오지 않는다.

원 source/권리·코드와 선택 raw result/program은 반환 전 재검사한다. 원 root 신뢰/farm 현재 검토·G0–G4/R2는 별도다.
계산 중 원 forcing/과거 ODE/시계 advance·DB/CLI/network/파일쓰기0, 새 농업 계수0이다.
기존512frame/512기관/512후보·2MiB 응답/600초·exact1024자리 상한을 유지한다.
수용은 실제 초기/7시간·8시간 저장 상태, 분수 출현/경과·같은 시각·원 나이/길이/anchor,
독립 Fraction/Decimal·threshold bracket과 index/시각/코드/권리/late source/용량·WSL/원 자료 보존이다.
