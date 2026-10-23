# 자동 출현 저장 결과의 공개 연구 export — v1

상태: [신규13/관련170·실제20파일/two fresh 수용](../research/crop-leaf-appearance-export-20261024.md).
[무계산 reader](crop-leaf-appearance-reader-v1.md)의 신뢰 root만 내보낸다.
`research/export-leaf-appearance-replay.py`의 `export(directory, root_sha256, output)`은
source program과 원 stem의 명시 redistribute=True를 모두 확인한 뒤 별도 새 output을 만든다.
기존 output을 덮어쓰지 않고 artifact 디렉터리 내부에는 작성하지 않는다. 농장·현재 권리·서명 승인이나 G0를 발급하지 않는다.

원 canonical bytes 그대로 root.json/input.json/preparation.json/generated-input.json/population-root.json/
stem-root.json/stem-input.json의7파일을 보존한다. input.json은 자동 출현 source program이다.
원12개 `leaf-appearance-replay-frame-v1` DTO는 frame-0.json…frame-11.json으로 쓴다.
stem/내부 계산 root·준비/모델/코드·권리와 원 ID/UTC/면적·개수는 변경하지 않는다.

`leaf-appearance-public-fixture-v1` index는 연구/합성/관문 미평가 표식·모델/표시 정책,
outer/source/준비/생성/내부 root/stem root·program SHA, 양쪽 권리와 frame descriptor를 가진다.
descriptor는 index/at/path/sha256/bytes/result_sha256/binding_sha256/stem_result_sha256이다.
각 JSON은2MiB 이내다. 같은 신뢰 root를 다른 새 디렉터리에 내보내면 같은20파일 bytes/index SHA다.

모든19파일의 실제 길이/hash와 원 manifest/양쪽 권리를 마지막에 재확인한다.
index는 별도 임시 파일을 fsync한 뒤 rename으로 마지막에 게시한다.
권리 거부·입력/출력 변조·부분 쓰기/rename 실패에서는 완료 index0이며 부분 출력은 승인 묶음이 아니다.
원43파일/기존17공개파일을 보존한다. 새 생장/출현/기온·면적 계산·DB·외부 명령은0이다.

수용은 부재 RED→집중/관련 검사, 실제43파일의20파일 export/fresh와
원12 DTO/47면적·원 SHA/UTC·권리/후기 변경 거부/같은 bytes·WSL/3root/소유 정리다.
별도 public 디렉터리/fixture digest 기록 뒤 strict SDK·실제3D/사용자 URL은 후속 수용이다.
실제 품종/독립 작기0·생산/자원/경제·자율 선정·G0–G4와 전체 완료일 미정을 유지한다.
