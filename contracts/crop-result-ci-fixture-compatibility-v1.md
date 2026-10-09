# 작물 저장·조회 CI fixture 호환 v1

선행: [8dd386d hosted 실패](../research/crop-result-ci-terminal-20261009.md)의 실제 로그와
`PYTHONPATH` 없는 현재 checkout의 선언8오류/TLS import1실패 재현.
핵심5파일은 이 계약과 다음 네 시험 파일이다.

- `backend/tests/test_crop_cycle_registered_terminal_publication.py`
- `backend/tests/test_crop_harvest_current_query.py`
- `backend/tests/test_crop_harvest_runtime_factory.py`
- `backend/tests/test_crop_harvest_runtime_tls.py`

## 변경과 수용

게시 선언의 합성 단위 fixture는 역사적 수용 source 목록 대신 명시한 소유 fixture source map을 쓴다.
SHA/판본/닫힌 필드/권한 mode/source/key 분리/원 마감 거부와 runtime assembly 전 차단을 유지한다.
실제 `sources()`는 별도 소유 파일/참조에서 유효 원 hash를 읽고 파일 bytes 또는 참조 hash 변경을
거부하는지 확인한다. 과거 참조·실제 publisher/supervisor·진행 중 frozen producer는 변경하지 않는다.

수확의 별도 Python 세 경로에는 backend와 tests의 절대 import 경로를 명시하고 상속 환경을 유지한다.
시험 프로세스가 가진 `sys.path`나 실행자의 우연한 `PYTHONPATH`를 자식 복원의 근거로 삼지 않는다.
같은 DB의 원 서명/결과/수량/UTC와 현재 권리·부족한 계정·fresh PID·FD·조회 계산0 단언을 유지한다.

원 실패를 기록한 뒤 `PYTHONPATH`가 없는 별도 실행에서 선언/실제 source guard/TLS 무연결 import를 검증한다.
current query와 runtime factory는 별도 소유 SCRAM DB의 fresh Python 정상/거부와 원 수량/현재 권리·정리로
검증한다. 실제 자식 종료·로그/hash·현재 source·보호된 전체 계산/미리보기 identity·WSL 자원을 기록한다.
집중 검사와 실제 두 DB 경로가 통과한 작업만 체크한다. 합성 시험을 실제 품종/농장 검증으로 표시하지 않는다.

DB 정리 교착/잔여 감사, 전체 hosted Backend/UID, UI 브라우저와 실시간 연결은 별도 미완료 작업이다.
진행 중 계산 또는 미리보기의 DB를 시험용으로 사용하지 않는다.
