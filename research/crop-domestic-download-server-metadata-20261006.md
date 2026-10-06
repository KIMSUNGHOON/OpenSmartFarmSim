# 국내 방울토마토 후보 B 서버 다운로드 응답 메타데이터 — 2026-10-06

상태: **지역 ZIP 한 개의 익명 요청 응답 헤더만 확인. 본문/원자료 수신·권리 승인·관문 판정 전**.
[앞선 다운로드 조건 조사](crop-domestic-download-conditions-20261006.md)의
‘서버 POST 미시험’ 사항 하나를 보완한다. 국내 수신 자료·독립 작기 수는 0건이며,
[확보 상태](crop-independent-data-status.json)와 코드·시험·프로필·todo는 변경하지 않았다.

## 실제 CLI 문맥과 명령

현재 위임 연구자의 `CODEX_THREAD_ID`에 대응하는 실제 native CLI 로그
`/home/sunghoonk/.codex/sessions/2026/10/06/rollout-2026-10-06T16-00-07-01a11003-32db-7b23-ad6e-538344f1984b.jsonl`에서
자신의 마지막 `turn_context`만 출력 필드를 제한하여 확인했다.
실제 시각은 `2026-10-06T07:37:16.298Z`, 모델은 정확히 `gpt-6.1-sol`, effort는 `xhigh`다.
원 JSONL 줄의 SHA-256은 마지막 LF 포함
`50a17134a56a6f5bafaa9114e6d79f6dce0a8875f1972fdb1aa30feb945e6a10`,
LF 제외 `6152016f57dc7e97db6ed23c149b82370bc897ecf23ec0e4f2dcd586643a1706`이다.
이는 **연구자 독립 관찰**이다. 원 로그 본문·인증 정보는 메모나 receipt에 복제하지 않았다.

별도로 부모가 제공한 native 문맥은 `2026-10-06T07:28:43.236Z`, 원 줄 SHA-256
`cd1ad45f69e3cee70c9728e1f0d1c8099e5b9a7705aa8466ae6dfb80feb0dfed`다.
부모의 원 줄은 이 후속 조사에서 재확인하지 않았다. 기존 native CLI 턴에서 수행했고
`codex`/`codex exec` 재귀 호출은 0회다. 실제 연구 출력은 이 메모와 아래 사설 메타데이터 receipt다.

공개 제품 HTML은 `python3 - <<'PY'`로 실행한 bounded `urllib.request.urlopen()` GET에서
읽었고, 파일 다운로드의 **실제 단일 명령**은 다음과 같다.

```bash
python3 /tmp/ossf-B-server-metadata-20261006-uzrdfy2z/post_headers_once.py
```

해당 스크립트는 Python 표준 `http.client.HTTPSConnection`으로 TLS 요청을 보내고
`getresponse()`로 상태/헤더를 확인한 뒤 즉시 `response.close()`와 `connection.close()`를
호출한다. 응답 본문의 `read()` 호출·보관·해싱·압축 검사·출력은 없다.
HTTP redirect를 따라가는 기능은 사용하지 않았다. 안전한 헤더만 receipt에 기록했고,
`Location`이 있을 경우 query/fragment·userinfo 및 허용하지 않은 path를 제거하도록 했다.

## 공개 페이지로 확인한 요청과 실제 결과

[공식 제공자 제품 B](https://data.mafra.go.kr/opendata/data/indexOpenDataDetail.do?data_id=20210928000000001574&service_ty=&filter_ty=F)를
`2026-10-06T07:38:19.605622Z`~`07:38:19.748520Z`에 직접 GET하여 HTTP 200을 확인했다.
현재 HTML의 `filedownload()`와 파일 목록은 `경기도.zip`을
`data_id=20210928000000001574`, `file_ty_code=file`, `file_sn=4`에 연결한다.
`fileForm`에는 이 세 필드 외에 `preview_ty_code=prew`도 있으나, 이번 명시된 범위에 따라
**다운로드 식별자 세 개만** 보냈다. 쿠키·인증·로그인·신청·이용목적·계정 변경·외부 연락은 없었다.

[공식 다운로드 action](https://data.mafra.go.kr/opendata/data/downloadOpenDataWebFile.do)에
`POST`, `Content-Type: application/x-www-form-urlencoded`로 보낸 정확한 body는 다음과 같다.

```text
data_id=20210928000000001574&file_ty_code=file&file_sn=4
```

| 이번 단일 요청의 관찰 | 값 |
| --- | --- |
| 요청 시작 UTC | `2026-10-06T07:38:55.776025Z` |
| 헤더 수신 UTC | `2026-10-06T07:38:55.953700Z` |
| 응답/연결 닫힘 UTC | `2026-10-06T07:38:55.953819Z` |
| HTTP 상태 | `200` |
| `Content-Type` | `application/download; charset=utf-8` |
| `Content-Length` | `28409` — 서버가 주장한 byte 수, 본문 크기 실측 아님 |
| `Content-Disposition` | `attachment; filename="%EA%B2%BD%EA%B8%B0%EB%8F%84.zip";` — URL 디코딩 파일명 `경기도.zip` |
| `Location` | 없음 |
| 응답 본문을 읽은 호출 / 원자료 보관 | `0` / 없음 |
| 재시도 / 다른 지역 요청 / redirect 추적 | `0` / `0` / `0` |

**확정한 사실:** 이 시각의 익명 POST에 서버가 200과 위 첨부 헤더를 반환했다.
**한계:** `application/download`는 일반 다운로드 media 표기이므로 헤더만으로 실제
ZIP 본문인지 판정할 수 없다. ZIP 무결성·압축 내부 파일/농장/기간·실제 레코드 제공은
미확인이다. 이 결과를 데이터 수신이나 실제 ZIP 다운로드 성공으로 계산하지 않는다.
본문 읽기 0회는 애플리케이션 호출 관찰이며, 전송 계층의 수신/버퍼링 byte 수는 측정하지 않았다.
접근 응답은 [앞선 제품 허락/회원 약관 적용 문제](crop-domestic-download-conditions-20261006.md)를
해결하지 않으며, 권리·독립성·QC·`available_at`/vintage와 G0~G4는 이 조사에서 평가하지 않았다.

## 사설 메타데이터 증거와 검증 범위

사설 디렉터리 `/tmp/ossf-B-server-metadata-20261006-uzrdfy2z/`는 임시 조회 근거다.
헤더 receipt의 해시는 농장/ZIP 본문의 raw hash가 아니다.

| 사설 파일 | SHA-256 |
| --- | --- |
| `product-B.html` — 공개 GET HTML | `1f00cb8bd63de9c59cb869bf55b57e6405bc7c740136fee12d59b4a2d57c5a92` |
| `server-response-metadata.json` — whitelist 헤더/요청 시각·조건 | `f7c9be950887ea20ed0834ddbd59241c54d66705cbaff99cdb76d8c55d969137` |
| `post_headers_once.py` — 실제 단일 요청 명령의 코드 | `4be04c8af69a0ec1a2ae6b02ecdd27187af9eca65a1d9d7a76b6307b4e91253a` |
| `native-context-verification.json` — 연구자 자신의 whitelist 문맥 관찰 | `eb5d294d6522516eb869ac2a2d4ae98b36f9a98f93481c3d18cb2d3099b663dc` |

실제 헤더 관찰을 위 요청/본문 읽기 금지 구현과 대사했다. 농장 원자료·PDF/ZIP 본문,
로그인·신청·목적 제출, PG·브라우저·빌드·시험 과정은 실행하지 않았다.
연구 제안의 deterministic 검토자와 자료/권리 승인자는 미지정이다.

### 부모의 별도 증거 대사

부모는 위 사설 파일4개의 실제 SHA와 연구자의 원 native `turn_context` 줄을 직접 대사했다.
모델·effort·시각과 LF 포함 해시가 일치했다. 요청 코드의 AST와 본문을 읽어 애플리케이션
응답 body 읽기 호출이 없는 범위를 확인했고, 같은 POST를 재실행하지 않았다.
기존53개 계산 소스와 확보 상태 파일은 그대로이며, 확보 상태 SHA256은
`a5c5400257e408a034137ff79e2a0f99ed3db293ef34b430389230352b0c5778`다.
이 대사는 연구 실행/메타데이터의 확인이며 원 ZIP·권리·QC·독립성 또는 관문 승인이 아니다.
