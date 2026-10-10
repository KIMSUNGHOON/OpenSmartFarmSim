# 공동 작물·기후 작업 발견 — E5a 로컬 수용

2026-10-10 KST. core `4a0774c`의 기존 discovery/test/계약 세 파일을 수용했다.
[실행 증거](artifacts/crop-climate-joint-execution-discovery-reference-20261010.json)는
17,102bytes, SHA-256 `1e92cb3b35e795afde4592c5863f63fc7eefbdf2e6230fa19d6762ac3ba11530`다.

## 변경과 실제 검증

기존 simulation 발견 목록에 `joint-crop-climate-execution-input-v1`을 명시적으로 추가했다.
선택한 판본만 반환하며 전체 입력·현재 농장/자료 권리·임대·checkpoint/result 검증은 E4 worker가 담당한다.
발견은 UUID/판본의 읽기 전용 후보 조회다. 아직 자동 소비나 UI 갱신을 시작하지 않는다.

신규8개·기존 discovery47개·collection2개·loop3개, **고유60개**를 통과했다.
discovery 전체55개는 isolated46/새 실제 SCRAM4/기존 실제 SCRAM5의 세 선택식으로 검증했다.
최종 제품/test SHA가 같은 다섯 묶음이며 단일 명령의 전체 module 실행은 아니다.
기존25개 함수/fixture 정의는 AST 대사로 변경 없음을 확인했다.

| 검사 | 확인한 결과 |
| --- | --- |
| 명시 판본 | joint/기존/둘 모두 선택, 미래 판본 비허용, 결과는 UUID와 판본 두 필드 |
| 실제 E1 요청 | 실제 접수한 두 job ID를 혼합 queue의46페이지에서 정확히 발견 |
| 경계/무변경 | 다른 tenant/stage·미래 재시도·활성 임대·취소 terminal 제외; 다섯 작업 테이블의 전후 SHA 동일 |
| 계산/쓰기0 | 입력 준비·복원·RHS 등10종과 submit/claim/renew/event/publication 등9종 호출0 |
| 거부 | 현재 metadata/실행 scope 상실, 정상 SHA를 가진 비정규 JSON의 페이지 전체 거부·무변경 |
| 기존 회귀 | 경제 작업 경쟁/만료 복구·단일 게시, 기존 권한/손상/페이지, 독립 collection profile, worker별 판본 결속 |

초기 실제 시험 두 번은 취소 fixture 설정으로 실패했다. 첫 실행은 tenant-1의 취소 scope가 없었고,
scope 추가 뒤에도 별도의 tenant-a 관리자 fixture로 취소하여 실패했다. 현재 tenant-1의 감사된
JobStore와 취소 scope를 사용하도록 시험을 수정했다. 제품 취소/권한 검사는 바꾸지 않았다.
원 실패 로그·시험 SHA·종료1과 성공 종료0을 private 증거 및 위 artifact에 보존했다.

기본 명령은 `nice -n 19 backend/.venv/bin/python -m pytest -q -p no:cacheprovider --tb=short`다.
대상·선택식·원 로그 SHA·실제 child/root 종료를 묶음마다 기록했다. DSN/비밀번호·원 argv는 private에만 보존했다.
최종 시험 뒤 계약에 수용 기준4를 추가했으며 실행 코드 bytes는 그대로다.

## 자원·시간·보존

.25초 표본, 최대 단일125,952,000/소유+보호 합317,661,184bytes로512MiB/1GiB 안이었다.
controller FD4→4·소유 PG/process·임시 PG directory/passfile 잔존0을 확인했다.
새 실제 joint 시험 종료의 schema/role은0이었다. 원본2,148항목·제품 source·고정 사용자
source/assets·보호3 identity와5173 HTTP200을 모든 묶음에서 보존했다.
전체 backend/web·빌드·166일 재계산·hosted CI·새 사용자 UI 배포는 실행하지 않았다. push hold를 유지한다.

native Codex CLI `gpt-6.1-sol/xhigh`의03:25:59.979Z 및03:33:41.402Z context를 확인했다.
원 LF 행 SHA는 artifact에 기록했으며 recursive/runtime CLI 실행은0이다.
native→집중 terminal은721.762초(약12분)였고 문서/commit은 별도다.

## 사용자 화면과 다음 단계

현재 `http://localhost:5173/`은 완료된 합성166일 생장/수확을 읽는다.
백엔드 결과 조회는 연결되어 있으나 실행 상태·새 checkpoint의 자동 갱신은 미구현이다.
재생 버튼은 저장된 시점의 이동이다. 새32초 공동 계산 화면도 현재 서버에 배포하지 않았다.

다음 E5b는 같은 worker/outcome의 자동 소비·순차 실행·중지/재시도와 기존 worker 보존이다.
그다음 E6 진행/접수/취소 API → E7 client → E8 자동 갱신/완료 저장3D → E9 실제 사용자 경로를 검증한다.
계산 도중 확정 prefix3D·전체 작기 forcing/자원/경제·최종 통합 UI는 별도 수용이다.
실제 농장 crop Run/국내 독립 자료0건·G0–G4 not_assessed와 생산/미래 마진/추천 hold를 유지한다.
외부 자료 확보는 이 합성 실행 연결의 개발 선행 조건이 아니며 실제 예측/추천 게시에는 필요하다.
