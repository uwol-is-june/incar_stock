# 데이터 출처 및 기준 시간

## 공통 규칙

| 조건 | 동작 |
|------|------|
| 16:00 KST 이전 (장중/장전) | 전일 확정 종가 사용 (`is_fallback = true`) |
| 16:00 KST 이후 (장 마감 후) | 당일 확정 종가 사용 |
| 비영업일 (주말/공휴일) | 직전 영업일 데이터 사용 |

> 데이터 자동 수집 시각: **매 영업일 16:10 KST** (APScheduler)

---

## 상단 고정 영역

### 종가 배너 (종목명 · 기준일 · 현재 종가 · 전일대비 · 등락률)

| 항목 | 출처 | 기준 |
|------|------|------|
| 종가 (close) | pykrx `get_market_ohlcv()` | 영업일 종가 기준 |
| 전일 종가 (prev_close) | pykrx `get_market_ohlcv()` | 직전 영업일 종가 |
| 전일대비 (change) | 직접 계산 `close - prev_close` | — |
| 등락률 (change_pct) | 직접 계산 `change / prev_close × 100` | — |
| 기준일 (data_date) | 수집 시점 기준 최신 영업일 | YYYY-MM-DD |

### KOSPI / KOSDAQ 지수 카드

| 항목 | 출처 | 기준 |
|------|------|------|
| 지수 종가 (close) | pykrx `get_index_ohlcv_by_date()` | 영업일 종가 기준 |
| 전일대비 (change) | pykrx 동일 함수 반환값 | — |
| 등락률 (change_pct) | pykrx 동일 함수 반환값 | — |

> 코드: KOSPI = `0001`, KOSDAQ = `1001` (KRX 지수 코드)

---

## 탭 1 · 시세 현황

### KPI 카드 (시가 · 고가 · 저가 · 거래량 · 거래대금 · 전일 종가)

| 항목 | 출처 | 기준 |
|------|------|------|
| 시가 (open) | pykrx `get_market_ohlcv()` | 당일(또는 전일) 영업일 |
| 고가 (high) | pykrx `get_market_ohlcv()` | 당일(또는 전일) 영업일 |
| 저가 (low) | pykrx `get_market_ohlcv()` | 당일(또는 전일) 영업일 |
| 거래량 (volume) | pykrx `get_market_ohlcv()` | 당일(또는 전일) 영업일 |
| 거래대금 (trading_value) | pykrx `get_market_cap_by_date()` | 당일(또는 전일) 영업일 |
| 전일 종가 (prev_close) | pykrx `get_market_ohlcv()` | 직전 영업일 종가 |

### 최근 7거래일 테이블

| 항목 | 출처 | 기준 |
|------|------|------|
| 기준일 · OHLCV · 등락률 | pykrx `get_market_ohlcv()` | 최근 7영업일 종가 기준 |

---

## 탭 2 · 종목 정보

### 종목 현황 (52주 고저가 · 시가총액 · 시총 순위 · 상장주식수 · 외국인 소진율)

| 항목 | 출처 | 기준 |
|------|------|------|
| 52주 최고가 (week52_high) | pykrx `get_market_ohlcv()` — 최근 365일 고가 최대값 | 직전 365일 영업일 기준 |
| 52주 최저가 (week52_low) | pykrx `get_market_ohlcv()` — 최근 365일 저가 최소값 | 직전 365일 영업일 기준 |
| 시가총액 (market_cap) | pykrx `get_market_cap_by_date()` | 영업일 종가 기준 |
| 시총 순위 (cap_rank) | pykrx `get_market_cap_by_ticker()` | 장 마감 후에만 제공 |
| 상장주식수 (listed_shares) | pykrx `get_market_cap_by_date()` | 해당 영업일 기준 |
| 외국인 소진율 (exhaustion_rate) | pykrx `get_exhaustion_rates_of_foreign_investment_by_date()` | 해당 영업일 기준 |

### 재무 지표 (PER · PBR · EPS · BPS · 당기순이익 TTM · 자본총액)

| 항목 | 출처 | 기준 |
|------|------|------|
| PER | pykrx `get_market_fundamental()` | 최근 30일 내 최신값 |
| PBR | pykrx `get_market_fundamental()` | 최근 30일 내 최신값 |
| EPS | pykrx `get_market_fundamental()` | 최근 30일 내 최신값 |
| BPS | pykrx `get_market_fundamental()` | 최근 30일 내 최신값 |
| 당기순이익 TTM | DART API `dart_fss` `corp.extract_fs()` | 최근 4분기 합산 (Trailing 12 Months) |
| 자본총액 (equity) | DART API `dart_fss` `corp.extract_fs()` | 최신 분기 보고서 기준 |

> DART 데이터는 공시 시점에 따라 최신 분기 반영까지 수주 지연될 수 있음.
> DART 연동 실패 시 자본총액은 `BPS × 상장주식수`로 대체 계산.

---

## 탭 3 · 투자자 동향

> 투자자별 순매수 데이터는 **KRX가 영업일 장 마감 후에만 확정 제공**.
> 장중 수집 시 해당 날짜 데이터는 없으며, 전일 데이터가 최신값으로 표시됨.

### 최근 5거래일 순매수 동향 (기관 · 개인 · 외국인)

| 항목 | 출처 | 기준 |
|------|------|------|
| 기관 순매수 (inst_net) | pykrx `get_market_trading_volume_by_investor()` | 각 영업일 마감 후 확정값 |
| 개인 순매수 (indiv_net) | pykrx `get_market_trading_volume_by_investor()` | 각 영업일 마감 후 확정값 |
| 외국인 순매수 (foreign_net) | pykrx `get_market_trading_volume_by_investor()` | 각 영업일 마감 후 확정값 |

### 기관 세부 순매수 (당일 기준)

| 항목 | 출처 | 기준 |
|------|------|------|
| 금융투자 (finv_net) | pykrx `get_market_trading_volume_by_investor()` | 최신 영업일 마감 후 |
| 보험 (ins_net) | pykrx 동일 | 최신 영업일 마감 후 |
| 투신 (trust_net) | pykrx 동일 | 최신 영업일 마감 후 |
| 사모 (private_net) | pykrx 동일 | 최신 영업일 마감 후 |
| 은행 (bank_net) | pykrx 동일 | 최신 영업일 마감 후 |
| 기타금융 (etc_fin_net) | pykrx 동일 | 최신 영업일 마감 후 |
| 연기금 (pension_net) | pykrx 동일 | 최신 영업일 마감 후 |

### 매수·매도 상세 (기관합계 · 개인 · 외국인합계)

| 항목 | 출처 | 기준 |
|------|------|------|
| 매수/매도/순매수 (각 주체별) | pykrx `get_market_trading_volume_by_investor()` | 최신 영업일 마감 후 |

---

## 탭 4 · 주가 차트

| 항목 | 출처 | 기준 |
|------|------|------|
| 종가 추이 라인 차트 | pykrx `get_market_ohlcv()` — 최근 7거래일 close | 영업일 종가 기준 |
| 전체 주가 추이 이미지 | Naver 금융 차트 이미지 URL | Naver 제공 기준 (실시간 아님) |

---

## 탭 5 · AI 분석

> Gemini 2.5 Flash Lite 모델이 수집된 주가·투자자·지수 데이터를 기반으로 생성.
> 수집 시(GitHub Actions) 자동 생성. 관리자 탭에서 수동 재분석 가능 (로컬 서버 전용).

### 시장 요약

| 항목 | 출처 | 기준 |
|------|------|------|
| market_summary | Gemini AI 생성 | 당일 KOSPI·KOSDAQ 흐름 + 종목 동향 1~2문장 |

### 종목 분석 코멘트

| 항목 | 출처 | 기준 |
|------|------|------|
| comment (가격/등락) | Gemini AI 생성 | 당일 주가 흐름 및 등락 배경 |
| comment (투자자 동향) | Gemini AI 생성 | 개인·외국인·기관·연기금 순매수 방향 및 의미 |
| comment (거래량·거래대금) | Gemini AI 생성 | 거래 활성도 및 자금 유입/유출 해석 |
| comment (시장 대비 상대 강도) | Gemini AI 생성 | KOSPI·KOSDAQ 대비 종목 상대 강도 |
| comment (종합 의견) | Gemini AI 생성 | C-level 임원용 한줄 결론 |

> `comment` 필드는 마크다운 형식 문자열. 프론트엔드에서 marked.js로 렌더링.
> Gemini API 호출 실패 시 빈 문자열 저장, 분석 없음 메시지 표시.

---

## 수집 주기 요약

| 구분 | 수집 시각 | 비고 |
|------|-----------|------|
| 정기 자동 수집 | 매 영업일 16:10 KST | GitHub Actions cron |
| 수동 수집 | GitHub Actions workflow_dispatch | Actions 탭에서 Run workflow |
| 과거 데이터 백필 | 로컬 서버 시작 시 | 최근 10영업일 내 누락 날짜 자동 보완 |
| AI 분석 재실행 | 관리자 탭 버튼 (로컬 서버 전용) | 기존 리포트 AI 분석 덮어씀 |
| 리포트 보관 기간 | 최신 5개 파일 유지 | 오래된 파일 자동 삭제 |
