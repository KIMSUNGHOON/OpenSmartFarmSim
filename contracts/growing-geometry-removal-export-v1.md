# 제거 구간의 원 파일 내보내기 — 연구 v1

상태: [25신규/18관련·fresh12결과 수용](../research/growing-geometry-removal-export-20261024.md).
[불변 저장/reader](growing-geometry-removal-artifact-v1.md)의 후속이다.
strict SDK·3D 적용과 farm/서명 custody·과학 관문은 후속이다.

`research/export-growing-geometry-removal-replay.py`의
`export(directory, root_sha256, output)`은 신뢰한 자체 합성 root를 읽는다.
입력의 use/display/redistribute가 모두 true여야 하며 기존 private false를 바꾸지 않는다.
출력은 소유한 새 절대 디렉터리이며 source 내부·상위·동일 경로/심볼릭 링크를 거부한다.
root·원16source/notice·각 원 CP bytes와 reader가 반환한 DTO를 복사한다.
원 reference profile은 참고 자료의 metadata/notice 범위를 보존하며 논문/PDF 전문을 내보내지 않는다.

index schema는 `growing-geometry-removal-public-fixture-v1`이다.
root scope/claim·권리와 exporter SHA, 원 source/CP/DTO의 path/bytes/SHA를 가진다.
CP descriptor는 root sample의 모든 필드에 path/SHA/bytes를 더한다.
DTO descriptor는 index/global_step_index/phase/at·양쪽 context/point·CP/sample/state 지문을 포함한다.
같은 정확 시각의 제거 전후는 서로 다른 flat index/phase·CP/DTO로 남는다.
총 count+2 frame이며 count16은 root/16source·18CP·18DTO·index의54파일이다.

출력 파일은 EXCL/NOFOLLOW로 쓰고 flush/fsync한다.
원 source/코드·권리와 출력 파일의 소유/권한·목록·bytes/hash를 다시 검사한 뒤
마지막에 임시 index를 index.json으로 원자 변경한다.
부분 쓰기/hold/late 권리·코드/파일 변경은 완료 index를 게시하지 않는다.
reader의2MiB/CP256KiB/전체 격자 한도는 그대로다.

exporter는 계산/point/context 준비/continuation/producer를 import/호출하지 않는다.
DB 접속/CLI/network·source 쓰기0이며 새 소유 출력에 필요한 쓰기만 수행한다.
동일 입력의 다른 새 출력은 모든 파일 bytes가 같아야 한다.
임의의 전체 graph 재작성이나 실제 farm 권리/배포 승인을 입증하는 API가 아니다.

수용은12결과의 원16source/notice·모든 CP/DTO·정확 phase/시각/권리,
False 거부/초기·늦은 철회·source/code/output 변조·부분 쓰기/완료 실패,
경로/소유권 정책·무계산 조회·동일 재출력이다.
별도 프로세스의 계산 import 금지/실제 DB·CLI/network/외부 쓰기0과
원 private false/소스·4서비스·WSL/FD/소유 잔류 보존을 확인한다.
