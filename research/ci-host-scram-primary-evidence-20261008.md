# Backend CI 전체 host SCRAM 검사의 1차 출처 조사

2026-10-08 KST. 대상은 origin `2a3e61571d0574a063577ec1edcfb75aa5f2d565`의
[종료된 Backend CI 37669114958](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958)다.
**전체 host 감사 실패는 확인했으며, initdb 기본 trust와 entrypoint의 SCRAM 추가가 함께 남는 원인 설명은 아직 추론이다.**
이번에는 고정 이미지의 `linux/amd64` entrypoint 바이트까지 공식 registry에서 확인했다.
실패한 hosted 서버의 실제 HBA 행·로드 상태·선택 platform은 확보하지 않았다.

## 실제 실행과 조사 범위

상위 native CLI 실행 영수증 `native-cli-proof-primary-ci-research.json`을 읽었다.
모델은 `gpt-6.1-sol`, 강도는 `xhigh`, thread는 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`,
`turn_context` 시각은 `2026-10-07T21:46:10.153Z`다.
해당 context 행 SHA-256은 `9edfd215a108a54d029010d15a1ac31e1633cb0ba13e52ddaa5fc63be0fa12fa`,
읽은 영수증 SHA-256은 `968a459560d0e9d0c9a73b4b7a8ee1689f160983cfc29b1ce625785f483ffebe`다.
이 영수증은 상위 실제 native 판단 경로의 증거다. 조사 자식의 spawn 요청도 같은 모델/강도였지만,
자식 자체의 실제 native rollout metadata는 별도 확보하지 않았으므로 동일한 실행 증거로 세지 않는다.
결과물은 이 문서이며 최종 채택은 상위의 같은 native CLI 검토를 기다린다. 재귀 CLI 호출은 0회다.

읽기 전용 Git/source·기존 분류 영수증·공식 문서·공식 registry만 조사했다.
ALL266 고정 파일, runtime·계약·workflow·설정·제한은 수정하지 않았다.
DB/Docker/test 실행, 이미지 pull, 큰 layer 수신, 파일시스템 이미지 추출, CI 재실행/취소/push는 0회다.
기존 [호환 수정 기록](calculation-ci-fixture-compatibility-20261008.md)에 이어지는 원인 조사이며 새 수용 결과가 아니다.

## 확인된 프로젝트 증거

[고정 helper](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/blob/2a3e61571d0574a063577ec1edcfb75aa5f2d565/backend/tests/login_database.py#L23-L28)는
`pg_hba_file_rules`의 모든 오류를 거부한 뒤 `host`로 시작하는 모든 종류의 인증 방식이 SCRAM인지 확인한다.
Unix socket의 `local` trust는 대상이 아니다. 일반/복제·IPv4/IPv6·실제 접속에 선택되지 않은 host 규칙도 제외하지 않는다.
host 규칙이 비었거나 하나라도 다른 인증 방식이면 마지막 assertion이 실패한다.
따라서 마지막 assertion의 실패만으로 실제 값이 trust였다고 확정할 수 없다.

[같은 SHA의 workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/blob/2a3e61571d0574a063577ec1edcfb75aa5f2d565/.github/workflows/backend-tests.yml#L80-L105)는
`postgres:18.6-bookworm@sha256:3725f4e2499eef5134592b3b4ab79a543ed7f8e533b05b5b637af926630f6650`을 시작한다.
password file·user·database를 전달하지만 `POSTGRES_INITDB_ARGS`와 `POSTGRES_HOST_AUTH_METHOD`는 전달하지 않는다.
호스트의 loopback에 publish하는 설정은 있지만 서버가 관측한 client 주소는 기록되지 않았다.
helper와 workflow를 `git show`로 읽어 현재 파일과 바이트가 같음을 확인했다.

읽은 기존 영수증의 분류 결과는 아래와 같다. 이번 조사에서 원 job 로그 전체를 다시 감사한 것은 아니다.

| 분할 | 보존된 관측 | 원 로그 SHA-256 |
| --- | --- | --- |
| [0](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958/job/112955941155) | 실제 SCRAM/`used_password` 로그인 통과 뒤 전체 host assertion 실패 | `d97afa0695d0457ecc05af78a8cf73b9f2888c4bbdaa1ff6ce05151ae866671a` |
| [2](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958/job/112955940876) | 918 passed, teardown 오류 2개; operator config:242와 calculation runtime:91 → helper:28 | `ce37a40be7d0523a65fdb6c3f9862446980ac70b3f7f2d08d381ee59e100b975` |
| [3](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958/job/112955941129) | 1007 passed, teardown 오류 1개; calculation TLS:72 → helper:28 | `bacef93e03cb9ab0cbda6ebaebdd37843a2e86ba87787556fc02de8387625792` |

분할1/4/5는 성공, 0/2/3과 집계는 실패로 종료했다. 실제 hosted HBA 행은 세 영수증 모두에 없다.
세 teardown 호출 위치도 해당 Git SHA에서 직접 확인했으며 현재 바이트와 일치했다.
이 오류 위치는 HBA 감사 실패를 가리킨다. 뒤에 있는 schema/role/passfile 정리 assertion까지 통과했다는 뜻은 아니다.

## 공식 initdb·entrypoint의 동작

PostgreSQL 18 문서는 인증 방법을 지정하지 않은 initdb의 기본값을 trust로 설명한다.
`--auth-host`는 TCP host 행, `--auth-local`은 Unix socket 행을 설정하며 일반 연결과 복제 연결을 초기화한다.
password file은 bootstrap 사용자 비밀번호를 설정하는 별도 옵션이다.
[공식 initdb 문서](https://www.postgresql.org/docs/18/app-initdb.html)

`REL_18_6`을 commit `724edf9bde9d356724ad384a2e196edc3c9f80f7`로 고정해 읽었다.
인증 인수가 없으면 host/local 각각 trust를 선택하고, HBA 템플릿의 인증 치환자에 적용한다.
템플릿에는 일반/복제용 IPv4 loopback과 IPv6 loopback host 항목이 있다. 실제 생성 행의 개수·IPv6 포함 여부는 미관측이다.
[기본값 선택](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/bin/initdb/initdb.c#L2571-L2579),
[host/local 적용](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/bin/initdb/initdb.c#L3457-L3463),
[HBA 템플릿](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/libpq/pg_hba.conf.sample#L110-L122)

고정 Docker entrypoint는 initdb에 사용자·password file·`POSTGRES_INITDB_ARGS`를 전달한다.
host 인증 인수를 자체 추가하지 않는다. 이후 서버의 `password_encryption` 값이나 명시한 host auth 값을 사용해
포괄적인 host 규칙을 기존 HBA 파일 끝에 추가한다. 앞의 initdb host 행을 모두 바꾸는 동작은 아니다.
초기화는 기존 DB가 없는 경우에 수행한다.
[initdb 호출](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/docker-entrypoint.sh#L87-L92),
[HBA 추가](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/docker-entrypoint.sh#L266-L285),
[초기화 순서](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/docker-entrypoint.sh#L346-L355)

Docker 공식 image 문서도 PostgreSQL 14 이상에서 기본으로 추가하는 host 인증이 SCRAM임을 설명하고,
필요하면 initdb host 인증 인수를 별도로 지정하도록 안내한다. 비밀번호 지정만으로 모든 host 행을 SCRAM으로 바꾼다는 설명은 아니다.
[공식 image 환경변수 문서](https://github.com/docker-library/docs/blob/96d19e6068e598698511eb4149bd29b925174e60/postgres/README.md#L192-L216)

## 고정 digest와 source의 직접 연결

공식 registry에 익명 읽기 요청을 보내 workflow의 index digest 자체를 SHA-256으로 대사했다.
선택해 조사한 variant는 `linux/amd64`다. 아래 manifest/config/COPY layer도 응답 원본 바이트의 digest를 모두 대사했다.
원 hosted runner가 실제로 고른 variant를 확인한 것은 아니다.

| 항목 | 실제 값과 직접 원천 |
| --- | --- |
| OCI index | [3725f4e2…](https://registry-1.docker.io/v2/library/postgres/manifests/sha256:3725f4e2499eef5134592b3b4ab79a543ed7f8e533b05b5b637af926630f6650), 6,491 bytes |
| linux/amd64 manifest | [9e73daeb…](https://registry-1.docker.io/v2/library/postgres/manifests/sha256:9e73daeb439141c2b11eea2463f5f1a3b269fd90d897b41cddb7cb440f21aa5d), 3,452 bytes |
| config | [8d76d8de…](https://registry-1.docker.io/v2/library/postgres/blobs/sha256:8d76d8de17e883d3995f76252e260bc6b7761e9c23edbf3356b0676d37c49ddb), 10,040 bytes; `PG_VERSION=18.6-1.pgdg12+2`; entrypoint `docker-entrypoint.sh`; command `postgres`; initdb/auth override 환경변수 없음 |
| entrypoint COPY layer | [9dd6e879…](https://registry-1.docker.io/v2/library/postgres/blobs/sha256:9dd6e87956748671b979456490c76456014e9e7ab10493e568f3aae2f07b3835), 압축 6,109 bytes; entrypoint 14,577 bytes, SHA-256 `9c440299ae04a0a79d55b8bf03307036d890a40979d2fb698073c9050d4b20a5` |
| 그 뒤 마지막 layer | [ddda533f…](https://registry-1.docker.io/v2/library/postgres/blobs/sha256:ddda533f81f87f9f1355a87999bb4139cc7f6d295dbf57152c00e35472a9fca4), 184 bytes; 다른 initdb helper symlink와 부모 directory만 있으며 entrypoint 삭제/덮어쓰기 없음 |

COPY layer의 entrypoint hash는 위에서 읽은 고정 upstream 파일 hash와 완전히 같다.
해당 upstream의 [18/bookworm Dockerfile](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/18/bookworm/Dockerfile#L89-L92)도 같은 PostgreSQL package 버전을 명시한다.
이는 현재 master의 이름만 보고 해당 이미지에 같은 코드가 있다고 가정한 결과보다 좁고 직접적인 증거다.
큰 PostgreSQL package layer의 binary·템플릿은 받지 않았으므로 그 바이트까지 upstream release와 대사한 것은 아니다.

수신은 metadata 각 256 KiB 이하, layer 각 128 KiB 이하로 제한했다.
작은 layer만 메모리에서 살폈고 재조회까지 image metadata/layer 총 56,440 bytes였다.
registry의 익명 인증 token은 메모리에서만 사용했으며 문서·로그·파일에 복사하지 않았다.
registry 응답 URL은 인증 없이 브라우저로 열면 인증 요청을 반환할 수 있다. 문서의 digest와 수신 크기는 실제 조사 결과다.

## 원인 설명의 범위와 남은 보류

**추론:** 기본 initdb의 loopback host trust가 남고 뒤에 넓은 SCRAM host 행이 추가됐다면,
그 넓은 행에 해당하는 실제 연결은 SCRAM을 사용할 수 있으면서 전체 host 감사는 실패할 수 있다.
PostgreSQL은 주소·DB·사용자·종류가 맞는 첫 규칙을 사용하므로 실제 한 연결의 인증 성공으로 다른 host 규칙을 증명할 수 없다.
[공식 HBA 매칭 규칙](https://www.postgresql.org/docs/18/auth-pg-hba-conf.html)
이미지의 동작과 실패 증거에 들어맞는 설명이지만, 실제 실패 서버에 그 행들이 있었는지는 아직 확인하지 못했다.

`pg_hba_file_rules`는 현재 파일 내용을 보여주며 마지막 로드된 HBA 설정을 증명하지 않는다.
따라서 다음 증거에서는 순서·주소가 포함된 view와 별도 새 연결의 실제 인증을 함께 기록해야 한다.
운영 역할에 이 superuser view 권한을 새로 주지 않는다.
[공식 view 문서](https://www.postgresql.org/docs/18/view-pg-hba-file-rules.html)

보류는 실패 hosted HBA 행 부재, 실제 선택 platform 부재, 당시 파일과 로드 상태 부재다.
정확한 이미지를 실행한 현지 재현도 없다. 이 자료만으로 원인 확정·workflow 수정 수용·전체 Backend 성공을 선언하지 않는다.
전체 host SCRAM assertion은 그대로 유지한다.

## 주 수용 queue 정리 뒤의 가장 작은 소유 실험

기존 소유 PostgreSQL binary와 private scratch만 사용해 두 fresh cluster를 직렬로 비교한다.
먼저 고정 entrypoint의 initdb/규칙 추가 두 단계만 재현한다. 두 번째는 같은 초기화에
`--auth-host=scram-sha-256`을 명시한다. socket admin 경로와 loopback listen을 사용하고
새로운 workflow·Docker Engine·proxy·외부 network 구성을 만들지 않는다. 이번 조사에서는 실행하지 않았다.

| 단계 | 확인할 증거와 예상 대조 |
| --- | --- |
| A: initdb host 인수 없음 + 같은 포괄 SCRAM 행 추가 | 생성 파일 hash, 정렬한 HBA view, 기존 helper의 실패. native loopback 접속은 앞의 trust에 걸릴 수 있으므로 이 단계의 실제 SCRAM 로그인 성공을 기대하지 않는다. |
| A의 선택적 controlled probe | loopback SCRAM 행 하나를 앞에 넣고 reload하되 다른 initdb trust host 행은 남긴다. 새 SCRAM/`used_password` 연결 성공과 기존 helper 실패가 함께 가능한지 확인한다. 이 앞 삽입은 증상 분리용 대조이며 image와 같은 초기화라고 주장하지 않는다. |
| B: fresh initdb에 명시 host SCRAM + 같은 포괄 행 추가 | 모든 오류가 없고 모든 host 행이 SCRAM인지 기존 helper로 검사한다. 별도 새 `require_auth=scram-sha-256` 연결과 `used_password`도 확인한다. |

각 단계는 `rule_number`, `line_number`, `type`, `database`, `user_name`, `address`, `netmask`,
`auth_method`, `error`와 `inet_client_addr()`·server version·binary version을 비밀 없이 기록한다.
helper/source hash를 전후 대사하고 cluster·role·password file·process 정리를 확인한다.
로컬 PG16으로 수행한다면 메커니즘 대조의 증거에 한정하며 pinned PG18.6 hosted 재현으로 세지 않는다.
기본 두 cluster 대조로 충분하면 추가 probe나 전체 suite를 먼저 늘리지 않는다.

## 원천 판본·조회·권리 기록

외부 농업/경제 자료를 채택한 조사가 아니다. 단위는 text/bytes, 관측은 아래 조회 시각,
`available_at`은 이번 조사자가 실제 확인한 조회 시각으로만 기록한다. 원 문서의 최초 공표일을 대신하지 않는다.
HTML 문서의 공표/개정 시각은 미제공이며 major 18 URL은 가변이다.
source commit 시각은 Git revision metadata이고 해당 파일 최초 발표 시각으로 해석하지 않는다.
QC는 공식 소유자 확인·commit 고정·raw SHA-256·실제 registry content digest 대사다.
검토자는 위 위임 조사 자식이며 상위 native 최종 검토는 별도다.

| 원천 | 판본/시각 UTC | 실제 조회 UTC | raw SHA-256 |
| --- | --- | --- | --- |
| [initdb 문서](https://www.postgresql.org/docs/18/app-initdb.html) | major 18; 공표/개정 미제공 | 2026-10-07T21:49:22.023472Z | `1b354fc8f4a2a4be70d8895e9018177da93105bf1b0985d2a85c514bae38002c` |
| [initdb source](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/bin/initdb/initdb.c) | REL_18_6 → `724edf9b…`; commit 2026-08-11T18:38:31Z | 2026-10-07T21:50:52.726850Z | `92d56b22abad61337b4badc4c8b94a50763b858f979b2e018fa730442776d5d2` |
| [HBA template](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/libpq/pg_hba.conf.sample) | 同 release commit | 2026-10-07T21:50:53.087822Z | `e3abfe29646ac6ece67e92d0b5255eb3b35d2878d23c7ea6bbd94f100054c168` |
| [Docker entrypoint](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/docker-entrypoint.sh) | `d588a446…`; commit 2026-09-24T17:02:45Z | 2026-10-07T21:48:49.385398Z | `9c440299ae04a0a79d55b8bf03307036d890a40979d2fb698073c9050d4b20a5` |
| [Docker image docs](https://github.com/docker-library/docs/blob/96d19e6068e598698511eb4149bd29b925174e60/postgres/README.md) | `96d19e60…`; commit 2026-10-07T19:12:45Z | 2026-10-07T21:48:49.878121Z | `b25dfc8fe2ae18ac47ad98341e3ca8708c282655ce41809b3cd9848005ebe159` |
| [HBA matching docs](https://www.postgresql.org/docs/18/auth-pg-hba-conf.html) | major 18; 공표/개정 미제공 | 2026-10-07T21:49:24.089555Z | `b00dac28df0e962879b092380772a64a72fa13bf94c1e1940e3ec70273021056` |
| [HBA view docs](https://www.postgresql.org/docs/18/view-pg-hba-file-rules.html) | major 18; 공표/개정 미제공 | 2026-10-07T21:49:25.949782Z | `d73f34a0f03d126a69328677c253425f7d342c4ac01c6cc582d1dcc7f10b97d7` |
| [Dockerfile](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/18/bookworm/Dockerfile) | 위 Docker source commit | 2026-10-07T21:50:53.722676Z | `ea58330e69627cb7b626043c7da44bc227ccd935126c239ceb33c8b4ddf745c2` |
| 위 OCI index/config/layers | config 생성 2026-09-19T00:36:23.342656378Z; tag 공표/availability 미확정 | 2026-10-07T21:51:41Z–21:52:18Z | 위 직접 URL의 content digest; entrypoint 별도 raw hash도 위에 기록 |

공개 원천을 읽고 링크·요약·hash만 이 문서에 남겼다.
PostgreSQL source/docs는 [고정 COPYRIGHT](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/COPYRIGHT),
Docker source/docs는 각 [고정 source LICENSE](https://github.com/docker-library/postgres/blob/d588a44673ea9d123c1acb1a6924de10a27fc315/LICENSE)와
[고정 docs LICENSE](https://github.com/docker-library/docs/blob/96d19e6068e598698511eb4149bd29b925174e60/LICENSE)의 이용/표시/배포 조건에 따른다.
raw 문서·코드·image layer를 저장소에 재배포하지 않았다. 원천별 직접 인용은 25단어 이하로 제한했다.

읽은 private 분류 영수증은 위치를 공개하지 않고 이름/hash만 기록한다.

| 영수증 | SHA-256 |
| --- | --- |
| `ci-2a3e615-terminal.json` | `b757112bb17793d6b81e6bb4cb3a0a60971e8a9d51b806373f83daacd3d74128` |
| `ci-partition2-source-confirmed.json` | `3493bf0770a5f0ddddd18ca53929f735d594e972a87fdbcc06e6eb255b6e1127` |
| `ci-partition3-readonly-classification.json` | `a0e5c3713f68c7e654712f87dd6f0bcbb51d3511a5937fa75dc312aa8f8be638` |

## 이번 검증

Git 고정 helper/workflow·세 teardown 호출 위치 대사와 공식 source/registry digest 대사는 통과했다.
이 문서의 상대 링크 대상과 신규 파일 범위를 확인했다.
DB/Docker/pytest와 후속 소유 실험은 실행하지 않았다.
실패 당시 hosted HBA 원 행·로드 상태·platform 및 최종 native 검토는 보류다.
