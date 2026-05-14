# incar_stock

인카금융서비스(211050) 주가 수집 · AI 분석 · 대시보드

**배포 URL**: https://incar-stock.vercel.app/

## 기술 스택

| 구분 | 기술 | 비고 |
|------|------|------|
| 언어 | Python 3.10+ | |
| 주가 데이터 | pykrx | KRX 공식 데이터 |
| 재무 데이터 | dart-fss | DART 분기 재무제표 (TTM 당기순이익, 자본총액) |
| AI 분석 | Gemini 2.5 Flash Lite | 시장 요약 + 마크다운 5항목 종목 분석 |
| 자동화 | GitHub Actions | cron: 평일 16:10 KST |
| 배포 | Vercel | 정적 파일 호스팅 |
| 환경 변수 | python-dotenv | .env 파일 로드 |
| 저장소 | JSON 파일 | reports/YYYY-MM-DD.json |
| 프론트엔드 | Vanilla JS + Chart.js + marked.js | 인라인 CSS, 마크다운 렌더링 |

## 프로젝트 구조

```
incar_stock/
├── .github/
│   └── workflows/
│       └── daily-collect.yml  # GitHub Actions 자동 수집 + AI 분석
├── backend/
│   ├── run_collect.py         # CLI 진입점 (Actions에서 실행)
│   ├── collector.py           # pykrx 수집 (OHLCV·펀더멘털·투자자·지수·DART)
│   ├── analyzer.py            # Gemini AI 분석 (시장 요약 + 종목 코멘트)
│   ├── reporter.py            # JSON 저장/조회/index.json 갱신
│   ├── main.py                # FastAPI 서버 (로컬 개발·관리자 기능용)
│   └── config.py              # WATCHLIST, REPORT_DIR, API 키
├── frontend/
│   └── index.html             # 6탭 대시보드 (정적 JSON 읽기)
├── reports/                   # YYYY-MM-DD.json + index.json
├── docs/                      # 내부 문서
├── vercel.json                # Vercel 라우팅 설정
├── .env                       # 환경 변수 (gitignore)
└── requirements.txt
```

## 로컬 환경 세팅

```bash
# 1. 저장소 클론
git clone https://github.com/uwol-is-june/incar_stock.git
cd incar_stock

# 2. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
# .env 파일 생성 후 아래 변수 입력
```

## 환경 변수

| 변수명 | 설명 | 필수 여부 |
|--------|------|-----------|
| `GEMINI_API_KEY` | Google Gemini API 키 | 선택 (AI 분석 활성화) |
| `DART_API_KEY` | DART OpenAPI 인증 키 | 선택 (TTM 당기순이익·자본총액 활성화) |
| `KRX_ID` | KRX 데이터마켓 계정 ID | 선택 (투자자·외국인 데이터 수집) |
| `KRX_PW` | KRX 데이터마켓 계정 PW | 선택 (투자자·외국인 데이터 수집) |

GitHub Actions 실행 시 동일한 변수를 **GitHub Secrets**에 등록해야 한다.
(레포 → Settings → Secrets and variables → Actions)

## 데이터 수집 실행

### 로컬 수동 실행

```bash
python backend/run_collect.py
# reports/YYYY-MM-DD.json, reports/index.json 생성
```

### 로컬 서버 실행 (관리자 기능)

```bash
python backend/main.py
# http://localhost:8000 접속 → 관리자 탭에서 AI 분석 업데이트 등 가능
```

### GitHub Actions 수동 실행

GitHub 레포 → Actions → Daily Stock Collect → **Run workflow**

### 자동 실행 스케줄

평일(월~금) **KST 16:10** 자동 실행 (`cron: '10 7 * * 1-5'`)

## 대시보드 탭

| 탭 | 내용 |
|----|------|
| 시세현황 | KPI 카드 (시가·고가·저가·거래량·거래대금) + 7일 OHLCV 테이블 |
| 종목정보 | 52주고저·시가총액·PER·PBR·EPS·BPS·TTM·자본총액·외국인소진율·시총순위 |
| 투자자동향 | 5거래일 순매수 트렌드 + 기관세부 7개 + 매수매도 상세 |
| 주가차트 | Chart.js 라인 차트 + 네이버 10년 차트 |
| AI 분석 | Gemini AI 시장 요약 + 마크다운 5항목 종목 분석 (가격/투자자/거래량/시장비교/종합) |
| 관리자 | AI 분석 수동 업데이트 (로컬 서버 실행 시에만 동작) |

## Vercel 배포

- GitHub 레포 연결 후 자동 배포
- Framework Preset: **Other**
- Build Command / Output Directory: 비워두기
- `reports/` 파일이 커밋되면 Vercel이 자동 재배포
