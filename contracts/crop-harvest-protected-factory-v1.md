# 등록 수확의 보호된 reader factory — v1

2026-10-08. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [runtime 조립](crop-harvest-runtime-assembly-v1.md) 뒤3 core파일은 이 계약·
`backend/app/crop_harvest_runtime_factory.py`·`backend/tests/test_crop_harvest_runtime_factory.py`다.

`load_harvest_current_query_factory(config_path)`는 기존 operator의 private 파일 검사를 재사용한다.
설정은 닫힌 `config_version,policy,directory,reader_dsn_file,integrity_key_file`이며
config_version은 `crop-harvest-reader-config-v1`, policy는 기존 `HarvestRegistryPolicy`의5 필드다.
설정≤64KiB·DSN/passfile≤8KiB·key32..4096bytes, absolute/no traversal·소유700 parent·소유600 regular/nlink1/no ACL 파일이다.
설정/DSN/key/passfile 경로는 다르며 DSN은 명시 TCP host·해당 DB/reader·private passfile을 사용하고 inline password를 받지 않는다.
reader root는 기존700/no ACL/no symlink 검사와 dev/inode identity를 따른다.

반환 callable은 기존 `ApiRuntimeDependencies.crop_harvest_current_query_factory`에 명시 선택한다.
호출은 `factory(calculation_current_query=...)`이고 정확한 원 query로 reader registry/current query를 구성한다.
생성 전후에 config/DSN/key/passfile의 캡처 bytes·소유/모드와 root identity·code pins를 재검사한다.
별도 DB/정확 ACL·부모/farm/principal 검사는 기존 ApiRuntime이 실제 SCRAM 연결로 확인한다.
설정/구성 실패는 고정 `harvest_reader_config_rejected`이며 private 값은 repr/로그/공개 응답에 넣지 않는다.
설정은 계수·원천·관문 승인을 포함하지 않고 조립은 입력 해석·RHS·행 생성·증명/등록을 실행하지 않는다.

수용: 닫힌 JSON·중복/누락/unknown·권한/경로/link/ACL·잘못된 reader·변경된 캡처/코드/root 거부,
FD/import 연결 부작용0·기존 runtime/route 회귀·실제 같은 DB/reader/부모/jobs/farm/principal의 별도 Python 복원과 정리를 확인한다.
실제 복원은 기존 `load_calculation_api_runtime`이 진짜 dependencies module을 import하고 새 ApiRuntime을 구성한다.
native 시험은 소유 private bundle/keys/market context와 미사용 resolver를 사용한 row0 조립이다.
소유 bundle은 운영 인증/제품 CLI/작물 정확도 증거가 아니며 공개 영수증에는 hash/정리 결과만 기록한다.

`crop-harvest-protected-factory`와 선행 assembly가 통과하면 runtime/factory 부모를 평가할 수 있다.
실제 HTTPS summary/원6행·split/현재 권리·30초/2MiB/자원 정리는 다음 단계이며,
그 뒤 SDK→같은 UTC 표/3D→자원/Decimal 경제를 연결한다. 실제 품종/독립 자료·G0–G4·생산/미래 마진/추천은 별도다.


## 개발 수용

2026-10-08 23:26 KST [개발 수용](../research/crop-harvest-protected-factory-implementation-20261008.md):
새45개(실제 SCRAM1)/기존 loader 순수56개·고유101개·원 종료0·445 source/정리.
실제 module import/새 ApiRuntime의 정상 별도 Python2개·키 권한 거부1개·같은 DB/reader/부모/farm과
원 bytes/counts/FD를 확인했다. 선행 assembly와 합쳐 runtime/factory 부모만 수용한다.
HTTP/TLS/SDK/3D·전체166일 질량 조회·실제 품종/독립 농장 자료/관문은 별도다.
