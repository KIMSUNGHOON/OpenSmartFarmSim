# 명시 잎 면적·원 줄기의 불변 연구 결과 — v1

상태: [18pytest·실제 생산/별도 fresh/export 수용](../research/crop-leaf-area-artifact-20261022.md). [초기 잎 목록](crop-declared-leaf-inventory-v1.md) 뒤의 저장 자식이다.
현재 farm/job/현재 권리 API의 새 판본이나 실제 농장 Run을 게시하지 않는다.

## 입력·생산

명시 자체 합성 leaf-software-program-v1은 program_id/rights, 원 v2 stem artifact/program SHA,
명시 잎 inventory initialization과 display policy를 가진다. 사용/변환/표시/보관을 소유한다고 선언한 자료만 계산한다.
재배포는 leaf/stem 양쪽의 명시 권리가 있을 때만 별도 export한다.
기존 줄기 프로그램의 기온/출력 UTC를 사용하고 매 시점의 실제 줄기 ID와 잎 attachment를 대사한다.
잎의 초기 시계·곡선/면적은 별도로 명시한다. 줄기 나이/계수로 잎 상태를 만들지 않는다.

기존 MorphologyBlobStore에 새 디렉터리로 원 stem14개 blob과 leaf 입력·실제 계산 결과/투영·root를 보관한다.
원 stem 저장소를 쓰거나 교체하지 않는다. 새 root는 입력·모델/source SHA, 선언 기관과 각 원 UTC의
수치 result/state chain·public payload hash/bytes를 결속한다. 계산 전후/각 시점의 source 지문을 대조한다.
최종 root 전 실패는 부분 blob만 남길 수 있으며 완료 artifact로 게시하지 않는다.

## 계산 없는 조회

`crop_leaf_artifact_reader.py`는 숫자 모델을 import하지 않는다.
명시 신뢰 root·원 입력/권리·현재 선택 원 blob/상태 지문·원 줄기 read와 원 시각/ID·단위/선언 목록을 검증한다.
DTO는 저장 결과의 투영이며 면적/생장·합계를 다시 계산하지 않는다.
fresh 프로세스에서 모델 import/생장 호출·SQL/CLI0과 원 결과 bytes를 확인한다.
이는 hash로 신뢰한 연구 artifact의 형식/무결성 검사이며 서명 farm custody/관측 정확도의 승인과 다르다.

public frame-v1은 root/result/input SHA·index/UTC/원점, 선언 잎 수/면적 합계·잎별 ID/attachment/정확 출현 초/나이/면적,
원 morphology-replay-frame-v2를 포함한다. 이전 v2/원 public15파일은 보존한다.
source/input/root/payload/result는2MiB 이하, 원 stem의 최대64시점을 따른다.

## 표시 정책

면적은 제작한 단면 leaflet 삼각형 면적에 대응한다. petiole/rachis·길이/폭/각도·소엽 수/표면은 제작 가정이다.
원 측정 면적의 정의/품종 형태와 이 표시 정책이 같다는 검증은 없다.
부착은 명시 줄기 위 끝과 제작 각도를 사용한다. 잎 개수는 초기 선언이며 새로운 잎 수/길이를 예측하지 않는다.
이 정책을 입력/manifest에 기록하고 실제3D 적용은 저장 수용 뒤 별도 검증한다.

## 수용

실제 producer의 원12시점/36잎·독립 면적 대사, 원 줄기 DTO/UTC/ID·체인·fresh 원 조회,
단위/권리/잘못된 부착·변조/상한/중도 source 변경 거부와 원 source/7root/WSL 상한을 확인한다.
이후 public export→typed frontend/원 면적·실제 mesh→실제 브라우저/현재 화면 보존을 각각 수용한다.
실제 품종·독립 농장자료·생산/자원/경제·G0–G4와 새 잎/관리는 후속이다.
