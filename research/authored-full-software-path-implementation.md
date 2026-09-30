# 작성 농장 입력 → 저장 Run 합성 연결 시험

2026-09-30. [시험](../backend/tests/test_authored_full_software_path.py)은 실제
PostgreSQL 16.15의 별도 SCRAM 로그인과 작성 농장 등록 서비스를 사용한다. 사용자
소유로 선언한 합성 입력을 등록하고, 검토 작업을 임대한 가짜 CLI가 완료한 뒤
저장된 CLI 캡처와 합성 관찰자 서명을 실제 완료 검증기로 검사했다. 완성된 증명에
대응하는 120시점 계산 후보도 실제 작성 입력에서 한 번 도출해 해시를 대사했다.

그 뒤 별도의 **합성** 검토자 키로 보고서 세 개를 서명하고 실제 해제 검증기와
불변 저장소에 넣었다. 실제 `AuthoredRunPreparer`, `AuthoredSimulationService`,
`AuthoredSimulationWorker`, `AuthoredRunStore`를 연결해 한 작업에서 원자적으로
Run을 게시했다. 재조회에서 검토 작업·해제 해시, 두 개의 연속된 60시점 궤적,
완료 상태, 다른 테넌트의 읽기 거부를 확인했다.

시험 시간의 중복 재계산을 제한하려고, 처음 실제 검증을 통과한 완료 증명과
계산 후보는 후속 서비스 조립 동안 같은 불변 객체로 고정했다. 따라서 이 시험은
후속 호출마다 권리·자료를 재검사하는 동작의 단독 증거가 아니다. 각 서비스의
별도 시험이 변경/철회와 원자 롤백을 다룬다.

격리된 로컬 PostgreSQL 16.15를 `OSSF_TEST_PG_DSN`으로 지정하고 `backend/`에서
다음 명령을 실행했다.

```bash
uv run --locked --group dev pytest -q --tb=short tests/test_authored_full_software_path.py
```

결과: **1 passed in 230.07s**. 변경된 합성 서명 도우미의 순수 시험은
`uv run --locked --group dev pytest -q tests/test_farm_authored_release.py`로
**1 passed in 0.44s**. 이 실행의 임시 소켓 경로는 재현용 고정 설정이 아니며,
다른 환경은 자체 `OSSF_TEST_PG_DSN`을 지정해야 한다.

이 시험은 실제 Codex CLI 실행, 독립 검토자, 농업 자료 G0, 제품 G1,
현장 G2, 작물·경제 전망 G3, 운영 G4의 증거가 아니다. 작성 폼에서 API를 거쳐
해당 Run을 3D 화면까지 여는 하나의 브라우저 시험도 아직 별도 단계다. 반복
권리/역할 감사가 길어지는 비용은 운영 성능 평가 대상으로 남긴다.
