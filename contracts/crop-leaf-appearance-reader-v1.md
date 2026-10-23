# 자동 출현 불변 결과의 무계산 조회 — 연구 v1

상태: [신규87/관련349·실제43파일/fresh 수용](../research/crop-leaf-appearance-reader-20261024.md).
[불변 producer](crop-leaf-appearance-artifact-v1.md)의 신뢰 root를 명시해 읽는다.
읽기가 신뢰 root/농장 승인·관문을 새로 발급하지 않는다. 기존33개 계산 소스 지문은 보존하며 소비자 소스는 별도로 기록한다.

`read_leaf_appearance_manifest(directory, access, root_sha256)`는 닫힌 outer manifest와
canonical source/준비/생성 program·내부 population/원 stem의 root/코드/권리/시점·state 연결을 확인한다.
원 초기 영양 위치의 부착/출현과 고유 leaf, 전체 저장 줄기 끝의 원 기관으로부터 파생 사건의 순서/정확 초/나이를 대사한다.
정책의 정수 순번 일치와 ID/원문 hash를 검사하며 생장 모델을 import하거나 새 출현 시각을 계산하지 않는다.
forcing의 UTC→정확 초/단위·정규화는 원 입력 표현의 검사다. 온도 적분/곡선 평가를 하지 않는다.
초기 state hash는 첫 저장 결과의 clock/area anchor 영수증을 원 시점으로 투영해 대사한다.
추측한 초기값이나 면적식으로 초기 상태를 재생성하지 않는다.

`read_leaf_appearance_frame(..., index=...)`는 위 검증 뒤 기존 무계산 population frame의 원 결과/binding·UTC/수치를 그대로 사용한다.
새 `leaf-appearance-replay-frame-v1`의 root는 outer root이고 population_artifact_sha256은 원 내부 root다.
source_program_sha256/preparation_sha256/policy_sha256/leaf_profile_sha256/display_policy를 추가한다.
나머지 원 result/binding/input SHA·index/at/원점/개수/면적/leaves/stem은 기존 frame과 같다. 응답은2MiB 이내다.

반환 전에 예상43개 source/계산/증거 blob의 hash/bytes를 다시 읽어 중간 변경·누락을 거부한다.
root/모든 JSON은 닫힌 형식/2MiB 상한을 따르며 bool을 integer index/시점 수/크기로 허용하지 않는다.
현재 체크아웃의 계산 버전으로 과거 상태를 재계산하거나 옛 지문을 덮어쓰지 않는다.
권리 False/누락·재해시한 원문/정책/프로필/초기/파생/계산 혼합과 원 projection 변조를 거부한다.
redistribute=False는 내부 조회와 구분한다. 제품의 실제 현재 farm 권리/서명 검증은 별도 경계다.

수용은 원43파일 metadata/새 root·12frame/47면적/정확 나이와 기존 frame의 원 수치·UTC 일치,
재해시/후기 변경·범위/권리 거부와 별도 fresh의 생장/출현/기온적분/면적 모듈 import0·DB/CLI/파일쓰기0이다.
WSL/원3root·자료/소유 정리를 확인한다. strict SDK/실제3D·제품 worker 적용은 후속이다.
실제 품종/독립 작기0·G0–G4/예측·생산/경제·자율 선정 보류는 유지한다.
