# 잎 목록과 원 저장 줄기의 부착/출현 결속 — 연구 v1

상태: [새13/관련150·실제 원 저장52면적 수용](../research/crop-leaf-stem-binding-20261022.md). [population](crop-leaf-population-v1.md) 뒤의 생산 경계 검증이다.
`bind_leaf_population_to_stored_stem(directory,access,root_sha256,index,population_state)`는
기존 불변 줄기 reader로 실제 원 frame을 읽고 정규 population과 원점/현재 시각을 대사한다.
원 root의 신뢰/권리와 farm 서명은 호출자의 별도 조건이다. 이 함수는 그것을 발급하지 않는다.

각 잎의 attachment_internode_id는 그 frame의 줄기 목록에 존재해야 한다.
원 줄기 출현 정확 초 ≤ 잎 출현 정확 초 ≤ 현재 정확 초여야 한다.
현재 원 UTC의 원점 이후 초는 population의 canonical exact 초와 같아야 한다.
분수 초를 반올림하거나 미래 줄기/잎을 대신 만들지 않는다.
원 잎 ID/부착 ID·면적/나이/출현 초·합계/개수와 원 stem DTO를 새 닫힌 결과에 보관하고
population state SHA/원 stem root/result SHA를 함께 연결한다. output2MiB 상한이다.
버전 `stored-leaf-stem-attachment-binding-research-v1`, 연구/합성/관문 미평가다.

이 검증은 현재 population 정규화(면적 anchor의 식 대조 포함)를 사용하므로 **무계산 GET reader가 아니다**.
구간 성장 advance/새 사건 생성·DB/CLI·파일 쓰기는 하지 않는다. 독립 저장/무계산 조회는 다음 자식이다.
부착 ID의 존재/선후만 확인하며 실제 품종의 마디/잎 관계·부착 위치/각도·유인/내림·관리/자동 출현을 증명하지 않는다.

수용: 부재 RED 뒤 실제 소유 stem14blob/12frame과 명시 초기/새 잎을 대사한다.
같은 UTC/원점·원 ID/분수 출현·면적/합계/개수·원 frame bytes를 확인한다.
부착 없음·줄기보다 이른 잎·미래/현재 시각 혼합·잘못된 root/index/원 blob 변조를 거부한다.
구간 advance/새 생성·DB/CLI/파일쓰기0과 원 blob metadata/bytes·7root/자료·화면/WSL 상한을 지킨다.
실제 Axiany 관측/계수·독립 농장 자료와 G0–G4는 별도다.
