# OpenSmartFarmSim 설계 백서

현재 자료는 [v0.2 PDF](OpenSmartFarmSim_White_Paper_v0.2.pdf)와 [LaTeX 원고](main.tex)입니다(2026-09-27, 설계 백서·미구현·미검증). 정식·계약 결정 당시의 농업 수급·미래 시장·거시 비용 근거와 조건부 시나리오, 결정 시점별 검증 계획을 포함합니다. 이 백서는 시장 예측 정확도, 미래 이익 또는 작물 순위의 검증 보고서가 아닙니다.

보존된 v0.1 자료: [v0.1 PDF](OpenSmartFarmSim_White_Paper_v0.1.pdf) · [해당 LaTeX 원고](main_v0.1.tex). 아래의 기존 PDF 빌드·글꼴 확인 기록은 이 **v0.1 PDF**에만 해당하며 v0.2의 빌드 결과가 아닙니다.

## PDF 빌드

XeLaTeX와 `kotex`, `fontspec`, `amsmath`, `booktabs`, `tabularx`, `longtable`, `tikz`, `hyperref`, `fancyhdr`, `microtype` 등을 포함한 TeX Live 배포판이 필요합니다. 한국어 본문과 산세리프에는 각각 `Noto Serif CJK KR`, `Noto Sans CJK KR`을 사용합니다. Ubuntu에서는 다음과 같이 TeX Live와 `fonts-noto-cjk`를 설치합니다. 이 패키지의 Noto CJK TTC 네 파일은 JP가 인덱스 0, KR이 인덱스 1 서브폰트이므로 `main.tex`은 일반·굵은 글꼴 모두 `FontIndex=1`을 지정합니다. 다른 배포판에서는 동등한 TeX Live 패키지와 Noto CJK 글꼴을 설치하고, TTC 디렉터리가 Ubuntu 기본값 `/usr/share/fonts/opentype/noto/`와 다르면 `main.tex`을 입력하기 전에 `\NotoCJKFontPath`를 정의하세요. 다음 네 검사 결과에서 모두 `[index 1]`을 확인합니다.

```sh
sudo apt update
sudo apt install texlive-xetex texlive-lang-korean texlive-latex-extra texlive-pictures fonts-noto-cjk fontconfig
fc-match -f '%{family}: %{file} [index %{index}]\n' 'Noto Serif CJK KR:style=Regular'
fc-match -f '%{family}: %{file} [index %{index}]\n' 'Noto Serif CJK KR:style=Bold'
fc-match -f '%{family}: %{file} [index %{index}]\n' 'Noto Sans CJK KR:style=Regular'
fc-match -f '%{family}: %{file} [index %{index}]\n' 'Noto Sans CJK KR:style=Bold'
```

```sh
build_dir="$(mktemp -d)"
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$build_dir" docs/whitepaper/main.tex
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$build_dir" docs/whitepaper/main.tex
```

저장소 루트에서 실행하며 출력은 `$build_dir/main.pdf`입니다. 두 번째 실행은 목차·교차 참조·인용 번호를 확정합니다. 참고문헌은 `main.tex`의 `thebibliography`에 내장되어 있어 BibTeX나 biber가 필요하지 않습니다.

v0.1 원고의 글꼴 수정 후 Tectonic 0.16.9로 실제 빌드했습니다. 추출한 Ubuntu `fonts-noto-cjk` 패키지의 TTC 경로로 `\NotoCJKFontPath`를 재정의한 빌드에서 15쪽 v0.1 PDF가 생성됐고, 한국어 텍스트 추출과 TeX 로그의 일반·굵은 Serif/Sans `:1` 선택을 확인했습니다. 다만 pypdf가 읽은 PDF의 Noto `BaseFont` 이름은 여전히 `NotoSerifCJKjp-*`와 `NotoSansCJKjp-*`입니다. 네 TTC는 서브폰트별 이름·조판 테이블이 다르지만 CFF 글꼴 테이블을 공유하고 그 CFF의 내부 글꼴 이름이 `jp`이므로, 해당 빌드에서는 명시적 KR 서브폰트 선택만으로 PDF의 `BaseFont` 이름을 `kr`로 바꿀 수 없었습니다. 첫 실행에는 Tectonic이 TeX 번들을 가져와야 하므로 네트워크 접근이 필요할 수 있습니다. Noto CJK 글꼴도 위와 같이 설치해야 합니다.

보존된 v0.1 원고를 다시 빌드할 때는 다음 경로를 사용합니다.

```sh
build_dir="$(mktemp -d)"
tectonic -o "$build_dir" --keep-logs docs/whitepaper/main_v0.1.tex
```

v0.2 PDF는 추출한 Ubuntu Noto CJK TTC와 Tectonic 0.16.9로 두 번 빌드한 17쪽입니다. PDF 한국어 텍스트 추출, TeX 로그의 넘친 행·빠진 글자·미해결 참조 없음, 1·5·6·13·14·16·17쪽의 화면 표시를 확인했습니다. 보존된 v0.1 PDF는 15쪽이며 당시 같은 범위의 로그 검사와 1·4·8·13·15쪽 화면 검사를 마쳤습니다. 다른 글꼴이나 LaTeX 배포판으로 다시 빌드하면 줄바꿈과 쪽수가 달라질 수 있습니다.

## 출처와 이용 범위

본문의 번호 인용은 기상청, KREI, KOSIS, KAMIS, 관세청, 한국은행, FAO, WUR, NASA, IFRS Foundation, W3C, OpenAI 등의 직접 확인한 공식/1차 페이지로 연결됩니다. 이 저장소의 `README.md`와 `docs/*.md`는 설계 입력으로 별도 명시했고 독립적인 실험 증거로 취급하지 않았습니다. 외부 페이지는 해당 주장에 필요한 범위로 요약하며 원문·도표·데이터를 이 디렉터리에 복제하지 않습니다. 시장 자료의 과거 최초 공개 판본, 세부 이용·재표시 권리와 농가 정산 연결은 자료별 확인이 남아 있습니다.

저장소가 자체 작성 문서에 적용하는 Apache-2.0은 외부 논문, 기상·가격·농장 원자료, 글꼴, 지도 타일, 3D 자산에 권리를 부여하지 않습니다. 실제 입력 자료의 접근·저장·가공·화면 표시·재배포와 출처표시는 제공자·항목별로 확인해야 합니다. 특히 무료 열람이나 API 접근을 원본 재배포 허가로 해석하지 않습니다.

**PDF 글꼴 권리 상태:** 한국어 글꼴 `Noto Serif CJK KR`과 `Noto Sans CJK KR`의 출처는 [공식 Noto CJK 저장소](https://github.com/notofonts/noto-cjk)이며, 두 글꼴은 [SIL Open Font License 1.1](https://openfontlicense.org/open-font-license-official-text/)로 배포됩니다. 글꼴의 OFL은 이 저장소 자체 작성 문서의 Apache-2.0을 변경하지 않습니다. 원고나 글꼴을 바꾸어 PDF를 다시 만들면 한글 글리프·굵기·줄바꿈·표·그림·인용을 다시 확인해야 합니다.
