# 명시 새 잎 population의 불변 계산 결과 — 연구 v1

상태: [producer14검사/실제40blob 수용](../research/crop-leaf-population-artifact-20261022.md). 무계산 reader/export/3D는 별도 자식이다.
기존 leaf v1/40blob과 사용자 저장3잎 화면을 유지하며 원 stem14blob을 새 디렉터리에 복사한다.

입력 `leaf-population-software-program-v1`은 schema_version/origin/program_id/rights/stem/initialization/births/display_policy다.
origin=synthetic, 명시 자체 권리와 원 stem root/program SHA, 기존 population initialization과 명시 사건 목록을 요구한다.
전체1–512잎·오름차순/고유 ID·현재 초기 이후/원 forcing 끝 이내의 출현과 원 UTC를 검사한다.
초기 면적/곡선은 각 입력에 명시하고 자동 출현/품종 수치를 만들지 않는다.
표시 정책은 기존 단면 삼각형 면적 대응과 같되 leaf_count=`declared_initial_and_births_only`다.

producer는 초기 계산 전·각 저장 시점 전·완료 전의 source SHA를 고정/재검사한다.
원 stem forcing/output UTC에 따라 기존/새 잎을 전진하고 원 저장 stem과 부착/시각을 대사한다.
원 program/초기 state SHA·모델/코드·각 원 population result/binding bytes와 그 SHA/크기·입력/현재 state chain·
원 stem result SHA·terminal state를 별도 root `leaf-population-research-artifact-v1`에 보관한다.
root/각 raw는2MiB 이내, 운송은 기존64MiB/4096files 상한과 소유 POSIX writer를 재사용한다.
마지막 검증 전에는 completed root를 게시하지 않는다. 실패한 별도 소유 디렉터리에 부분 blob이 남을 수 있다.
같은 source/입력 재실행은 같은 root이며 기존 파일 metadata/bytes를 보존해야 한다.

producer-only 수용: 부재 RED→원12시점/52면적·원 stem14blob과 원 raw/binding/개수·분수 출현/chain/권리/코드 지문,
재실행 같은 root·원/새 metadata 보존, 부적합 입력/출현·부착/권리/원 stem 및 늦은 code drift의 완료 root0,
원7root·자료/화면과 지정 WSL 상한을 확인한다. CLI/DB/새 Run은 만들지 않는다.

후속 reader는 생장 import/식 평가·DB/CLI/쓰기 없이 원 raw/population/선언·binding 투영을 검증해야 한다.
신뢰 root는 계산/권리/관문 증명이 아니며 farm/current rights·서명/worker 통합은 별도다.
export는 stem과 population 양쪽 재배포 권리를 확인하고 strict SDK→실제 WebGL/표/그래프·새 잎 수/면적을 대사한다.
실제 Axiany 계수/관측·독립 농장 검증0과 자동 출현/관리·생산/경제·G0–G4는 후속이다.

## 작은 조회 자식: manifest만

`read_leaf_population_manifest`는 완료 root·명시 입력/권리·기존 stem manifest·28개 계산 source 지문 형태와
완전한 같은 UTC descriptor chain만 검증한다. 생장 모듈을 import하거나 식을 평가하지 않는다.
단일 root는 신뢰된 호출자 입력이며 실제 현장 증명/서명 권한은 별도다.
manifest12검사와 실제40blob 별도 fresh의 import/DB/CLI/쓰기0·원 metadata/bytes가 수용 기준이다.
이 단계는 각 population raw/binding의 원 수치 투영을 검증했다고 주장하지 않는다. frame reader/export는 다음이다.

## 시점별 원 수치 조회

`read_leaf_population_frame(..., index=정수)`는 같은 신뢰 root의 manifest/원 program·숫자 result/state 지문,
원 stem DTO와 binding의 원 bytes를 대사한다. 초기 목록과 그 시점까지의 명시 출현 목록을 원 program에 결속하고
같은 ID/원점/출현·현재 정확 초/나이/curve hash·초기 면적 영수증·면적 단위/범위/개수와 이번 사건 수를 검사한다.
원 binding은 저장 result에서 계산 없는 투영으로 만든 기대 bytes와 같아야 한다. 재해시한 투영 변조도 거부한다.
반환 `leaf-population-replay-frame-v1`은 원 artifact/result/binding/input SHA·index/UTC·잎 개수/면적·원 stem/각 leaf를 담는다.
면적/나이를 새 식으로 계산하거나 중간 시점·곡선 값을 만들지 않는다. 신뢰 root가 계산 증명이라는 뜻은 아니다.
별도 fresh의 생장/producer import·식 평가·SQL/CLI/파일쓰기0, 원40blob metadata/bytes 및 원12시점/52면적 대사가 수용 조건이다.
현재2026-10-23에는 과거6서비스가 종료됐고5175만 생존했다. 이 집중 조회 검증은 실제 생존 root와 원 저장물/WSL 상한을 보호한다.
과거7root 생존을 현재 검증의 전제로 표시하지 않는다. export/SDK/새 잎3D 및 필요한 runtime 복구는 후속이다.
