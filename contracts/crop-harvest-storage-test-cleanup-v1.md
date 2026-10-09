# 수확 보존 자격증명 시험의 정리 v1

선행: [실제 CI 종료](../research/crop-result-ci-terminal-20261009.md)의 분할1 로그는
`test_registry_credentials_are_private_and_cannot_overwrite_existing_file`이 만든
`reader.pgpass` 하나를 뒤의 로그인 자원 감사가 검출했음을 보여준다.
제품 자격증명 저장 동작과 합성 파일의0600·기존 파일 덮어쓰기 거부·원 bytes 단언은 유지한다.

해당 시험이 만든 파일은 성공/단언 실패 모두 `finally`에서 제거한다.
다른 시험의 파일·계정·schema를 정리하거나 전역 감사의 검색 범위를 줄이지 않는다.
과거 영수증과 frozen producer·진행 중 계산/미리보기는 변경하지 않는다.

수용: 같은 pytest 실행/공유 basetemp에서 기존 자격증명 시험 다음 실제 SCRAM/HBA·세 정리 감사를
실행해 원 잔여1 실패를 재현한다. 수정 후 같은 순서의 종료0과 schema/role/passfile0,
0600·덮어쓰기/원량 단언 보존을 확인한다. 별도 실패 대조로 생성 후 단언이 실패해도
소유 파일이 제거되는지 확인한다. 실제 원 종료·source/보호 identity/dist·시험 PG 정리를 기록한다.

이 수정은 분할1의 해당 파일 누수만 다룬다. 분할5 교착/잔여 감사와 수정 후 hosted18·전체 Backend/UID,
UI 실시간 연동과 실제 품종/농장 관문은 별도 미완료다.
