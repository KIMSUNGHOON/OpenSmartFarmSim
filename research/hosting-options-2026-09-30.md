# 호스팅 후보 조사 — 2026-09-30

조사 시각: **2026-09-30 UTC**. 가격과 서비스 사양은 아래에 연결한 **사업자 공식 문서/가격표를 이날 웹으로 조회한 값**이다. USD와 EUR을 환산하지 않았고, VAT·한국 측 세금·환율·도메인·운영 인건비·외부 자료/지도 비용은 별도다. 표의 월 비용은 서버를 한 달 내내 두는 경우의 표면 가격이며 계약 견적이나 G4 배포 승인이 아니다.

## 이 저장소에 필요한 실행 형태

[아키텍처](../docs/ARCHITECTURE.md#구성과-경계)는 Vite 웹, Python API, 수집·계산·Codex CLI 작업자, PostgreSQL 작업표, 불변 원본/결과 파일을 별도 역할로 둔다. [기술 스택](../docs/TECH_STACK.md#최소-운영-구성-결정표)은 첫 운영을 단일 호스트 Compose와 영속 POSIX 파일로 잡고, DB와 파일을 **같은 복원 시점**으로 백업하도록 요구한다. [작업자 계약](../docs/ARCHITECTURE.md#필수-codex-cli-런타임-작업자)은 작업별 비특권 컨테이너·UID·임시 파일시스템, 제한된 egress, 다른 테넌트/DB 비밀에 대한 접근 차단을 요구한다. 현재 [`compose.yaml`](../compose.yaml)은 의존성 이미지/DB 확인용이며 앱 entrypoint와 실제 작업별 격리 CLI 실행기가 없다. 아래 사양은 **앞으로의 내부 staging 용량 후보**이고, 현재 파일을 배포하면 완성 서비스가 된다는 뜻이 아니다.

8 GiB 메모리는 측정된 최소 요구량이 아니라 API·PostgreSQL·여러 작업자가 같은 호스트에서 뜰 때의 **시험 시작점**이다. 비교한 VM은 2–4 vCPU로 다르므로 CPU 성능을 같은 것으로 취급하지 않는다. 작은 내부 데모는 4 GiB/2 vCPU에서 동시 CLI 작업 1개로 시작해 메모리, CPU, 디스크, 작업 대기 시간을 측정할 수 있다. 아키텍처 초안의 전체 동시 CLI 4개를 이 VM 한 대가 수용한다는 근거는 없다. 한국 사용자 대상이므로 서울 리전의 존재와, 싱가포르/유럽 리전의 실제 지연·자료 위치 허용 여부를 선택 요소로 둔다.

## 실제 Plan 비교

| 사업자·Plan | 상시 VM/DB 시작 가격과 사양 | 지역·추가 비용·판단 |
| --- | --- | --- |
| **AWS Lightsail Linux 공개 IPv4 포함, 서울** | 4 GiB/2 vCPU/80 GB **$24/월**, 8 GiB/2 vCPU/160 GB **$44/월**. 각각 월 전송량 4 TB/5 TB 표기. [공식 가격](https://aws.amazon.com/lightsail/pricing/) | [서울 `ap-northeast-2` 지원](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-regions-and-availability-zones-in-amazon-lightsail.html). 서울 초과 송신은 **$0.13/GB**이고, 송수신 모두 할당량을 소모하되 초과분 중 인터넷 송신만 과금한다. [전송 규칙](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-faq-data-transfer-allowance.html). 8 GiB라도 2 vCPU라 CLI 동시 실행은 실측 필요. |
| **DigitalOcean Basic Droplet Regular, 싱가포르** | 4 GiB/2 vCPU/80 GiB **$24/월**, 8 GiB/4 vCPU/160 GiB **$48/월**. 각각 4,000/5,000 GiB 송신 포함. [공식 가격](https://www.digitalocean.com/pricing/droplets) | [SGP1 지원; 서울은 리전 목록에 없음](https://docs.digitalocean.com/platform/regional-availability/). 초과 송신 **$0.01/GiB**, 수신 무료. [전송 규칙](https://docs.digitalocean.com/platform/billing/bandwidth/). Droplet은 일반 Linux VM이라 Compose와 호스트 Docker를 적용할 후보이나 제품 격리 정책은 별도 시험 필요. |
| **Hetzner Cloud CPX32, 싱가포르** | 4 shared vCPU/8 GiB/160 GB의 **€48.99/월**, 공개 IPv4 별도 **€0.50/월**(부가세 전). [2026-06-15 이후 가격](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [CPX32 사양](https://www.hetzner.com/european-cloud/), [IPv4](https://docs.hetzner.com/cloud/servers/overview/) | [싱가포르 `sin` 제공](https://docs.hetzner.com/cloud/general/locations/). 싱가포르 포함 송신량은 Plan별 **0.5–5 TB**라 정확한 CPX32 할당량을 주문 화면에서 확인해야 한다. 추가 송신 **$8.49/TB**로 안내한다. [싱가포르 설명](https://www.hetzner.com/cloud-singapore/). PostgreSQL은 이 비교에서는 VM에 직접 운영한다. |
| **Hetzner Cloud CPX32, 독일/핀란드** | 같은 사양 **€35.49/월** + IPv4 **€0.50/월**(부가세 전). [가격](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [IPv4](https://docs.hetzner.com/cloud/servers/overview/) | [유럽 클라우드 상품](https://www.hetzner.com/european-cloud/)은 CPX32에 송신 20 TB를 표시한다. 한국과의 실제 지연, 농장 자료의 해외 저장 허용을 확인해야 한다. 싱가포르와 같은 비용으로 취급할 수 없다. |
| **Fly.io Machines + Managed Postgres, 재설계 후보** | 공개 표에 Machines `performance-2x` 4 GiB **$62/월**, `performance-4x` 8 GiB **$124/월** 예시; Managed Postgres Basic 1 GiB **$38/월** + 사용 DB 저장 **$0.28/GB·월**. 표시 VM 가격은 선택 리전에 따라 달라진다. [가격](https://fly.io/pricing/), [DB 사양](https://fly.io/docs/mpg/) | 볼륨 **$0.15/GB·월**, 스냅샷 **$0.08/GB·월**, 아태 인터넷 송신 **$0.04/GB**; 앱별 공유 IPv4 포함, 전용 IPv4 **$2/월**. [가격](https://fly.io/pricing/). [Fly Machines API](https://fly.io/docs/machines/api/working-with-machines-api/)로 작업별 VM을 만들 수 있으나 [지역에 묶인 개별 볼륨](https://fly.io/docs/volumes/overview/)과 현 Compose/POSIX 공유 경계가 달라 저장·작업 실행기를 재설계해야 한다. 초기 선택 우선순위는 낮다. |

Hetzner 표의 CPX32 vCPU/RAM/드라이브는 공식 상품표에 표시되지만 싱가포르 페이지의 동적 가격/세부 할당량이 웹 텍스트에는 완전히 나타나지 않았다. **지역·Plan 조합의 계정 주문 화면 확인**이 남는다. Hetzner의 더 싼 CX 상품은 공식 화면에 생성 불가/제한 재고 표시가 있어 필수 용량의 근거 있는 기본안에서 제외했다. [상품표](https://www.hetzner.com/cloud/cost-optimized/).

## PostgreSQL과 백업

| 구성 | 공식 근거와 비용 | 이 저장소에서 확인할 것 |
| --- | --- | --- |
| Lightsail VM 안의 PostgreSQL | VM 가격에 포함된 디스크 사용. 인스턴스/별도 디스크의 자동 스냅샷은 저장분 **$0.05/GB·월**, 최근 자동 7개다. [스냅샷 설명](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-faq-snapshots.html) | crash-consistent VM 스냅샷만으로 DB와 불변 파일의 동일 시점 복구를 입증할 수 없다. 논리/물리 백업 및 복원 연습 필요. |
| Lightsail 관리형 PostgreSQL | 표면 가격 **$15/월 Standard 1 GiB/40 GB**는 가격표에 *No Data encryption*으로 표시된다. **$30/월 Standard 2 GiB/80 GB**는 *Data encrypted*로 표시된다. 각각 HA는 **$30/$60**. [공식 가격](https://aws.amazon.com/lightsail/pricing/). 관리형 DB는 최근 7일 자동 시점 복원을 제공한다. [DB 백업](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-faq-databases.html) | 서울은 Lightsail 지원 리전이지만 **계정의 서울 DB 생성 가능 목록과 PostgreSQL 18.6 blueprint를 확인하지 못했다**. 현재 Compose DB는 18.6이므로 검증 전에는 호환이라고 주장하지 않는다. 8 GiB VM+$30 DB = **$74/월**은 저장 스냅샷 등 제외 기준. |
| DigitalOcean 관리형 PostgreSQL Standard Basic | **1 GiB/1 vCPU/최소 10 GiB $15.15/월**, **2 GiB/1 vCPU/최소 30 GiB $30.45/월**. [가격](https://www.digitalocean.com/pricing/managed-databases). 공식 문서에 PostgreSQL 18 Standard 지원 목록이 있으나 [정확한 18.6/SGP1 생성 가능성](https://docs.digitalocean.com/products/databases/postgresql/details/supported-extensions/)은 계정에서 확인해야 한다. [7일 PITR·저장/전송 암호화](https://docs.digitalocean.com/products/databases/postgresql/details/features/) 제공; 자동 장애 조치에는 별도 standby node가 필요하다. | 8 GiB Droplet+$15.15 DB = **$63.15/월**부터(추가 저장·백업 제외). DB 백업과 POSIX 파일 백업은 별개이므로 공통 복원시점 절차 필요. |
| Hetzner VM 자동 Backups | 서버 월가의 **20%**, 백업 슬롯 7개. CPX32 싱가포르에서는 약 **€9.80/월**, 서버+IPv4+Backups 약 **€59.29/월**; 유럽은 약 **€43.09/월**(모두 VAT 제외). [백업 요금](https://docs.hetzner.com/cloud/billing/faq/) | [연결 Volume은 서버 백업/스냅샷에 포함되지 않음](https://docs.hetzner.com/cloud/servers/backups-snapshots/overview/). DB+파일을 Volume에 두면 별도 백업 필요. VM 백업만으로 거래 일치성이 보장되지 않는다. |
| DigitalOcean Droplet 자동 Backups | 기본 Weekly는 VM가의 **20%**, Daily는 **30%**. 8 GiB $48 VM이면 $9.60/$14.40/월. [요금](https://docs.digitalocean.com/products/backups/details/pricing/) | [연결 Volumes는 Droplet 자동 백업 범위 밖](https://docs.digitalocean.com/products/backups/details/limits/). 관리형 DB의 7일 PITR도 원본 파일을 백업하지 않는다. |

## Cafe24와 Cloudflare 보완 비교

| 역할·Plan | 공식 요금/제약 | 이 프로젝트에 대한 잠정 판단 |
| --- | --- | --- |
| **Cafe24 클라우드 `m3.xlarge` VM** | 4 vCPU/8 GB/기본 SSD 30 GB **80원/시간**(VAT 별도). 130 GB 블록 스토리지는 10 GB당 3원/시간. **공인 IP는 공식 페이지 사이에 3원/시간과 6원/시간이 충돌한다.** 720시간 가동·총 160 GB 논리 용량 가정 시 VM **57,600원** + 추가 블록 **28,080원** + IP **2,160–4,320원** = **87,840–90,000원/월(VAT 별도, VAT 포함 96,624–99,000원)**. 약 1 TB의 누적 기본 트래픽이 있고 초과 송신은 첫 1,000 GB에 150원/GB(VAT 별도)다. [클라우드 상품·6원 표기](https://serverhosting.cafe24.com/?controller=new_product_page&page=cafe24-cloud), [견적·3원 표기](https://console.cafe24.com/public/estimate). | 현재 Compose/POSIX 구조를 시험할 수 있는 VM 후보. **공인 IP 확정 요금**과 추가 블록의 실제 마운트·성능, Docker 및 작업별 격리 허용, 계정의 서버 위치, DB/파일 복원, 초과 송신비를 확인해야 한다. 스냅샷은 기본 30 GB VM 디스크와 추가 블록이 별도이고 응용 일관성 백업의 대체가 아니다. |
| **Cafe24 개발언어 VPS `DEV C`** | 4 vCPU/8 GB/160 GB NVMe/월 5 TB·공인 IP 1개 **132,000원/월**(설치비 0원). root 권한이 있고 Docker 직접 설치를 안내하지만 기본 구성은 FastAPI와 PostgreSQL **17**의 비컨테이너 설치다. 자동 백업은 없다. **일본 데이터센터** 상품이다. [공식 상품·요금·지역](https://serverhosting.cafe24.com/?controller=new_product_page&page=dev-vps). | 쉬운 개통의 대가로 현재 PostgreSQL **18.6** 잠금·Compose 구성을 직접 교체/재설치하고 운영해야 한다. 일본 자료 위치·지연을 허용하는지 먼저 확인한다. 상품의 “프로덕션” 표기는 이 프로젝트 G4 통과 증거가 아니다. |
| **Cloudflare Pages Free** | 정적 자산 요청은 무료·무제한이다. Free는 월 빌드 500회/동시 빌드 1개, 파일 20,000개·자산당 25 MiB 제한. [정적/Functions 요금](https://developers.cloudflare.com/pages/functions/pricing/), [Pages 한도](https://developers.cloudflare.com/pages/platform/limits/). | React/Three.js의 **정적 3D 웹 화면** 배포 후보. 현재 화면은 동일 출처 `/v1` API를 호출하므로 Pages 단독 업로드로 전체 제품이 동작하지 않는다. 별도 API 호스트·안전한 라우팅/인증·CORS 또는 프록시·캐시 정책이 필요하다. 현재 로컬 전용 합성 데모도 공개 빌드에 포함되지 않는다. |
| **Cloudflare Workers/Containers** | Workers Paid는 최소 **$5/월**, Containers의 메모리·CPU·디스크·송신과 Worker/Durable Object 호출은 사용량 과금. Container `standard-3`은 2 vCPU/8 GiB/16 GB 디스크이고 **로컬 디스크는 재시작 후 지속되지 않는다**. [Workers/Containers 요금](https://developers.cloudflare.com/workers/platform/pricing/), [크기](https://developers.cloudflare.com/containers/platform/limits/), [저장 생명주기](https://developers.cloudflare.com/containers/api/container-class/). | 기술적으로 일부 Python 서비스를 Container로 만들 수 있으나 PostgreSQL과 불변 POSIX 파일·작업별 CLI 격리·일관 복원을 현 구조 그대로 넣을 수 없다. 저장·작업 실행·비용 구조 재설계가 먼저다. 초기 전체 백엔드 호스트 후보로 채택하지 않는다. |

**Cloudflare 프록시 주의:** 기본 원본 읽기 제한은 **125초**이며, 응답 전 이를 넘으면 HTTP 524가 난다. [공식 524 설명](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/). 현 브라우저 작성 검토·계산 접수는 임시로 **180초** 기다린다([코드](../web/src/authored-farm-api.ts)). 이 설정은 실제 접수가 125초를 넘었다는 측정이 아니지만, 125–180초 사이 응답을 허용하는 설계이므로 프록시 경유 전 접수 즉시 202 반환/상태 폴링 및 P95 측정이 필요하다. 검증 전 API는 DNS-only 경로로 분리할 수 있으나 그 경우에도 TLS·인증·CORS를 설계하고 시험해야 한다. Cloudflare Enterprise만 기본 읽기 제한을 상향할 수 있다.

**조합 판단:** 한국 내부 staging에서 Cafe24를 쓰려면 `m3.xlarge`가 현재 구조에 가장 가까운 후보이고 Cloudflare Pages Free를 정적 화면에 붙일 수 있다. 그러나 Cafe24 클라우드 VM의 실제 위치와 복원·격리 성능은 확인하지 못했으므로 **기존 Lightsail 서울 우선순위를 뒤집지 않는다**. Cafe24 DEV C는 일본 데이터센터와 17 기본 DB 때문에 우선순위가 더 낮다. Pages만으로 서버와 CLI 사용료가 없어지는 것은 아니다. 이 판단은 공식 상품 문서에서의 **추론**이며 CLI/G4 승인이나 실제 성능 시험 결과가 아니다.

## 후보 우선순위와 아직 필요한 증거

1. **한국 내부 staging의 첫 후보: AWS Lightsail 서울 Linux 공개 IPv4 8 GiB $44/월**, VM 내 PostgreSQL + 영속 파일로 시작하고 동시 CLI 1개로 부하를 측정한다. 서울 리전·고정 VM 가격·현재 단일 호스트 구조가 일치한다는 **추론**이다. 4 GiB $24는 저동시성 개인 데모의 절약 후보일 뿐 용량 수용 결과가 아니다. DB 운영 부담을 줄이고 싶으면 Lightsail 관리형 PostgreSQL 2 GiB $30을 별도 비교하되 PostgreSQL 18.6 가용성 확인 전 전환하지 않는다. [가격](https://aws.amazon.com/lightsail/pricing/), [리전](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-regions-and-availability-zones-in-amazon-lightsail.html).
2. **관리형 DB 편의를 우선하면 DigitalOcean SGP1 Basic 8 GiB $48 + 관리형 PostgreSQL 1 GiB $15.15부터.** 백업 범위/동일 시점 복구와 서울 대비 지연을 시험한다. 8 GiB/4 vCPU가 계산·CLI 동시 작업에 유리할 가능성은 있으나 성능 실측 전 단정할 수 없다. [VM](https://www.digitalocean.com/pricing/droplets), [DB](https://www.digitalocean.com/pricing/managed-databases), [리전](https://docs.digitalocean.com/platform/regional-availability/).
3. **유럽 저장과 지연이 허용되면 Hetzner CPX32 유럽 €35.49 + IPv4/백업**, 싱가포르가 필요하면 CPX32 싱가포르 €48.99 + IPv4/백업을 비교한다. 셀프 관리형 DB 및 출처 파일의 백업·보안 운영 책임을 감당할 때의 후보이다. [가격](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [위치](https://docs.hetzner.com/cloud/general/locations/).

**결정 전 검증:** (a) 선택 계정의 해당 리전 VM/DB 재고·PostgreSQL 정확한 버전·할당량, (b) 실제 Compose 전체 기동과 작업별 CLI 컨테이너/egress 제한, (c) DB와 불변 POSIX 파일의 일관된 외부 백업/복원, (d) 1/4 동시 작업의 CPU·RAM·디스크·응답 지연, (e) 사용자 위치 지연·농장/제3자 자료의 저장 지역 및 권리, (f) 월간 송신·스토리지·인증서/도메인·로그 비용을 확인한다. 제품은 아직 G4 이전 내부 후보이며 호스팅 결제만으로 공개 운영 관문이 충족되지 않는다.

**AI 사용료는 호스트 비용과 별도다.** Codex 자동화의 `codex exec`는 호출 시 `CODEX_API_KEY` 사용을 공식 안내하며, API 키 인증 CLI는 표준 API 요금으로 청구된다. [`gpt-6-sol` 모델 가격](https://developers.openai.com/api/docs/models/gpt-6-sol)의 표준 짧은 문맥 텍스트 기준 입력 **$2/100만 토큰**, 출력 **$10/100만 토큰**이고 `xhigh`를 지원한다. 캐시·긴 문맥·도구·처리 방식에 따른 실제 청구는 달라진다. [비대화형 인증](https://learn.chatgpt.com/docs/non-interactive-mode), [인증/과금](https://learn.chatgpt.com/docs/auth). 배포 계정의 모델 접근권, 한도, 계약/허용 조건, 요청당 실제 사용량은 **미확인**이다.

## 조사 절차와 한계

공식 가격표·설명서만 웹으로 열어 2026-09-30에 대조했다. 계정에 로그인하거나 VM/DB를 만들지 않았고, 네트워크 지연·실사용 성능·실제 청구액은 측정하지 않았다. 이 조사를 위해 새 Codex CLI 프로세스를 재귀 실행하지 않았다. 이 파일은 웹 조회와 문서 비교 결과이며, [AGENTS.md](../AGENTS.md)의 정확한 CLI 모델/추론 강도 호출을 **별도 증빙한 운영 판단 기록은 아니다**. 최종 사업자 선택과 G4 관문은 지정된 `gpt-6-sol`/`xhigh` CLI 검토·실계정 증거 및 결정적 서버 검증을 거쳐야 한다.
