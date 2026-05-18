# Architecture

## 1. 시스템 개요

cron-job.org가 매 거래일 KST 16:10에 GitHub Actions `workflow_dispatch`를 트리거한다.
`run_collect.py`가 pykrx로 인카금융서비스(211050) 주가·펀더멘털·투자자 동향과 KOSPI/KOSDAQ 지수를 수집하고,
`analyzer.py`가 Gemini AI로 시장 요약과 종목 분석 코멘트를 생성한다.
`reporter.py`가 결과를 `data_date` 기준 날짜별 JSON 파일로 저장한 뒤 `index.json`을 갱신한다.
변경된 `reports/` 파일이 레포에 커밋·푸시되면 Vercel이 자동으로 재배포하고,
`frontend/index.html`이 정적 JSON 파일을 직접 읽어 대시보드를 렌더링한다.

---

## 2. 컴포넌트 구조

```
[cron-job.org - 평일 16:10 KST (Asia/Seoul)]
        │ POST https://api.github.com/.../daily-collect.yml/dispatches
        ▼
[GitHub Actions - workflow_dispatch]
        │
        ▼
[ run_collect.py ]  ← CLI 진입점 (영업일 체크 포함)
        │
        ├─ [ collector.py ] ──pykrx──→ KRX (OHLCV · 펀더멘털 · 투자자 · 지수)
        │                   dart-fss→ DART (분기 재무제표)
        │
        ├─ [ analyzer.py ]  ──Gemini──→ 시장 요약 + 종목 분석 코멘트 (마크다운)
        │
        └─ [ reporter.py ] ──→ reports/YYYY-MM-DD.json
                           ──→ reports/index.json  (save()/prune() 시 자동 갱신)
        │
        ▼ (git commit & push)
[GitHub 레포 reports/]
        │
        ▼ (Vercel 자동 재배포)
[https://incar-stock.vercel.app/]
        │
        ▼
[ frontend/index.html ]
  └─ fetch('./reports/index.json')      → 날짜 목록
  └─ fetch('./reports/${date}.json')    → 리포트 데이터
```

| 컴포넌트 | 역할 | 위치 |
|----------|------|------|
| run_collect.py | CLI 진입점, 영업일 체크, collect→analyze→save→prune 순서 실행 | `backend/run_collect.py` |
| run_backfill_ai.py | AI 분석 강제 재분석 스크립트 (기존 리포트 전체 덮어씀) | `backend/run_backfill_ai.py` |
| collector.py | pykrx 수집 (OHLCV·펀더멘털·투자자·지수·52주), DART 재무, fallback 처리 | `backend/collector.py` |
| analyzer.py | Gemini 2.5 Flash Lite AI 분석 (시장 요약 + 마크다운 5항목 종목 코멘트) | `backend/analyzer.py` |
| reporter.py | JSON 저장/조회/목록/index.json 갱신 | `backend/reporter.py` |
| config.py | WATCHLIST, REPORT_DIR, API 키 설정 | `backend/config.py` |
| main.py | FastAPI 서버 (로컬 개발·관리자 기능용) — 자동 백필, AI 수동 업데이트 엔드포인트 포함 | `backend/main.py` |
| index.html | 인라인 CSS 6탭 대시보드 (시세현황·종목정보·투자자동향·주가차트·AI분석·관리자) | `frontend/index.html` |
| trigger-ai-update.js | 프론트엔드 수동 버튼 → GitHub Actions backfill-ai 트리거 | `api/trigger-ai-update.js` |
| daily-collect.yml | GitHub Actions 워크플로우 — cron-job.org `workflow_dispatch` + 수동 트리거 | `.github/workflows/daily-collect.yml` |
| backfill-ai.yml | GitHub Actions 워크플로우 — AI 재분석 수동 트리거 | `.github/workflows/backfill-ai.yml` |
| vercel.json | Vercel 라우팅 설정 | `vercel.json` |

---

## 3. 데이터 흐름

```
[cron-job.org - 평일 16:10 KST]
  └─ POST GitHub API workflow_dispatch → daily-collect.yml
       └─ run_collect.py
                 ├─ is_business_day() 체크 → 비영업일이면 종료
                 ├─ collector.collect()
                 │    ├─ pykrx 365일치 OHLCV → 52주 고저 계산
                 │    ├─ 장중(16:00 전)이면 전 거래일 종가 사용 (is_fallback=True)
                 │    └─ 보조 API (best-effort):
                 │         ├─ get_market_fundamental      → PER, PBR, EPS, BPS
                 │         ├─ get_market_cap_by_date      → 시가총액, 상장주식수, 거래대금
                 │         ├─ get_exhaustion_rates_*      → 외국인 보유비율, 한도소진율
                 │         ├─ get_market_cap_by_ticker    → KOSDAQ 시총 순위
                 │         ├─ get_market_trading_volume_* → 투자자별 매수·매도·순매수
                 │         ├─ get_index_ohlcv_by_date     → KOSPI/KOSDAQ 지수 + 15일 히스토리
                 │         └─ dart-fss                   → 분기 당기순이익 TTM + 자본총액
                 ├─ analyzer.analyze(stocks)
                 │    └─ Gemini 2.5 Flash Lite API 호출
                 │         ├─ market_summary: 시장 전체 한줄 요약
                 │         └─ stocks[ticker].comment: 마크다운 5항목 종목 분석
                 ├─ reporter.save(date, enriched, market_summary) → YYYY-MM-DD.json + index.json
                 └─ reporter.prune(5)                             → 최신 5개만 보관

[Vercel]
  └─ GitHub push 감지 → 자동 재배포

[브라우저]
  └─ index.html
       ├─ ./reports/index.json     → 날짜 목록 로드
       └─ ./reports/${date}.json   → 리포트 데이터 로드
            └─ 상단 Hero 카드: 인카 종가 + AI 한 줄 요약 (2rem 강조)
            └─ 상단 보조 행: KOSPI/KOSDAQ 지수 카드 (미니 스파크라인 + 글로우 닷)
            └─ 탭1 시세현황: KPI 카드 + 7일 OHLCV 테이블
            └─ 탭2 종목정보: 52주고저·시가총액·PER·PBR·EPS·BPS·TTM·외국인소진율·시총순위
            └─ 탭3 투자자동향: 5거래일 순매수 트렌드 + 기관세부 + 매수매도 상세
            └─ 탭4 주가차트: Chart.js 라인 차트 + 네이버 10년 차트
            └─ 탭5 AI 분석: Gemini AI 시장 요약 + 마크다운 5항목 종목 분석 (marked.js 렌더링)
            └─ 탭6 관리자: 로컬 서버 전용 — AI 분석 수동 업데이트 버튼
```

---

## 4. JSON 보고서 스키마

```json
{
  "date": "2026-05-12",
  "generated_at": "2026-05-12T16:15:00",
  "market_summary": "시장 전체 한줄 요약 (1~2문장)",
  "stocks": {
    "211050": {
      "name": "인카금융서비스",
      "comment": "### 가격 / 등락\n...\n### 투자자 동향\n...\n### 거래량 · 거래대금\n...\n### 시장 대비 상대 강도\n...\n### 종합 의견\n...",
      "close": 7030,
      "prev_close": 6980,
      "change": 50,
      "change_pct": 0.72,
      "is_fallback": false,
      "data_date": "2026-05-12",
      "prev_date": "2026-05-11",
      "open": 7000, "high": 7050, "low": 6950,
      "volume": 123456,
      "trading_value": 867654320,
      "week52_high": 7500, "week52_low": 5200,
      "market_cap": 514312579080,
      "listed_shares": 49263657,
      "per": 7.05, "pbr": 2.38, "eps": 1480, "bps": 4387,
      "equity": 216239746159,
      "foreign_pct": 12.5,
      "exhaustion_rate": 25.3,
      "cap_rank": 42,
      "kospi": {
        "close": 2680.12, "prev_close": 2650.33, "change": 29.79, "change_pct": 1.12,
        "history": [{ "date": "2026-05-12", "close": 2680.12 }]
      },
      "kosdaq": {
        "close": 850.45, "prev_close": 843.20, "change": 7.25, "change_pct": 0.86,
        "history": [{ "date": "2026-05-12", "close": 850.45 }]
      },
      "inst_buy": 12000, "inst_sell": 9000, "inst_net": 3000,
      "indiv_buy": 50000, "indiv_sell": 55000, "indiv_net": -5000,
      "foreign_buy": 8000, "foreign_sell": 6000, "foreign_net": 2000,
      "finv_net": 1000, "ins_net": 500, "trust_net": 800,
      "private_net": 200, "bank_net": 100, "etc_fin_net": 50, "pension_net": 350,
      "dart_financials": [
        { "period": "2026/Q1", "net_income": 18000000000 }
      ],
      "net_income_ttm": 74000000000,
      "ohlcv_7d": [
        { "date": "2026-05-12", "open": 7000, "high": 7050, "low": 6950,
          "close": 7030, "volume": 123456, "change": 50, "change_pct": 0.72 }
      ]
    }
  }
}
```

> 투자자 동향 필드(`inst_*`, `indiv_*`, `foreign_*`)는 장 마감 후에만 제공된다.
> `comment` 필드는 Gemini AI가 생성하는 마크다운 텍스트 (5개 ### 헤더 구조).
> `kospi.history` / `kosdaq.history`는 최근 15일 종가 배열 (스파크라인용).

---

## 5. 주요 설계 결정 (ADR)

### ADR-001: 저장소 — JSON 파일 채택 (SQLite 대신)
- **결정**: `reports/YYYY-MM-DD.json` 날짜별 파일 저장
- **이유**: 별도 DB 설정 불필요, 정적 호스팅과 호환, reporter.py 교체로 Supabase 전환 용이

### ADR-002: 배포 — Vercel 정적 호스팅 채택 (FastAPI 서버 대신)
- **결정**: GitHub Actions로 JSON 생성 후 레포 커밋 → Vercel 자동 재배포
- **이유**: 서버 운영 비용 없음, 항상 최신 데이터 보장, 별도 서버 프로세스 불필요
- **트레이드오프**: 관리자 기능(AI 수동 업데이트 등)은 로컬 서버(`main.py`) 실행 또는 GitHub Actions workflow_dispatch로만 실행 가능

### ADR-003: 자동화 — cron-job.org + GitHub Actions workflow_dispatch 채택
- **결정**: cron-job.org (Asia/Seoul 16:10) → GitHub API `workflow_dispatch` 직접 호출 → `daily-collect.yml` 실행
- **이유**: GitHub Actions `schedule:` 피크 시간대 2~3시간 지연, Vercel Hobby Cron 미작동 문제. cron-job.org는 ±1분 이내 정시 HTTP 요청 보장
- **인증**: cron-job.org 요청 헤더에 GitHub Fine-grained PAT (`actions=write` 권한) 설정
- **주말 처리**: cron-job.org는 매일 실행하되 `run_collect.py`의 `is_business_day()` 가 비영업일 자동 스킵

### ADR-004: 전일대비 계산 — 직접 계산 방식
- **결정**: pykrx 365일치 조회 후 `curr_close - prev_close` 직접 계산
- **이유**: pykrx에 전일대비(원) 전용 컬럼 없음, 장중 fallback과 일관된 방식

### ADR-005: AI 분석 — Gemini 2.5 Flash Lite 채택 (Claude 유료 API 대신)
- **결정**: `gemini-2.5-flash-lite` 모델로 시장 요약 + 마크다운 5항목 종목 분석 생성
- **이유**: 무료 티어로 일 1회 수집 비용 없음, JSON 응답 품질 안정적
- **출력 형식**: JSON `{ market_summary, stocks: { ticker: "마크다운" } }` — 줄바꿈 `\n` 이스케이프 필수

---

## 6. 외부 연동

| 서비스 | 용도 | 인증 방식 |
|--------|------|-----------|
| KRX (한국거래소) | OHLCV·펀더멘털·투자자·지수 수집 | KRX_ID/PW 환경변수 (pykrx 자동 사용) |
| DART (금융감독원) | 분기 재무제표 수집 (TTM, 자본총액) | DART_API_KEY 환경변수 |
| Gemini AI (Google) | 시장 요약 + 종목 분석 코멘트 생성 | GEMINI_API_KEY 환경변수 |
| Naver Finance | 10년 주가 차트 이미지 | 없음 (img src 직접 참조) |
| Vercel | 정적 파일 호스팅 | GitHub 레포 연동 |
| cron-job.org | 매 거래일 KST 16:10 workflow_dispatch 트리거 | GitHub Fine-grained PAT (cron-job.org 헤더 설정) |
| GitHub Actions | 수집 워크플로우 실행 | 레포 내장 GITHUB_TOKEN |
