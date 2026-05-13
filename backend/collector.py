import logging
from datetime import date, datetime, time, timedelta, timezone

from pykrx import stock

from config import DART_API_KEY, WATCHLIST

_KST = timezone(timedelta(hours=9))
_MARKET_CLOSE = time(16, 0)  # pykrx 데이터 확정 기준 (KST)

logger = logging.getLogger(__name__)


def _market_closed() -> bool:
    return datetime.now(_KST).time() >= _MARKET_CLOSE


def is_business_day(date_str: str) -> bool:
    """pykrx로 해당 날짜가 영업일인지 확인."""
    try:
        df = stock.get_market_ohlcv_by_date(date_str, date_str, "005930")
        return not df.empty
    except Exception:
        return False


def _date_range(days_back: int = 30):
    end = date.today()
    start = end - timedelta(days=days_back)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _fetch_ohlcv(ticker: str, days_back: int = 365):
    s, e = _date_range(days_back)
    return stock.get_market_ohlcv(s, e, ticker)


def _fetch_fundamental(ticker: str):
    try:
        s, e = _date_range()
        df = stock.get_market_fundamental(s, e, ticker)
        # pykrx는 KRX 미업데이트 날짜에 0을 채움 → dropna()가 걸러낼 수 있게 NaN으로 교체
        for col in ("EPS", "BPS", "PER", "PBR"):
            if col in df.columns:
                df[col] = df[col].replace(0, float("nan"))
        return df
    except Exception:
        return None


def _fetch_market_cap(ticker: str):
    try:
        s, e = _date_range()
        return stock.get_market_cap_by_date(s, e, ticker)
    except Exception:
        return None


def _fetch_foreign(ticker: str):
    try:
        s, e = _date_range()
        df = stock.get_exhaustion_rates_of_foreign_investment_by_date(s, e, ticker)
        # pykrx 버전/인코딩에 따라 컬럼명이 달라질 수 있으므로 위치 기반으로 표준화
        df.columns = ["상장주식수", "보유수량", "지분율", "한도수량", "한도소진율"]
        return df
    except Exception as e:
        logger.warning("foreign data fetch failed for %s: %s", ticker, e)
        return None


# pykrx 버전에 따라 투자자 index 이름이 달라지는 경우 표준 이름으로 매핑
_INVESTOR_INDEX_MAP = {
    "외국인":   "외국인합계",   # "외국인합계" 없이 "외국인"으로만 반환되는 케이스
    "연기금 등": "연기금등",    # 공백 포함 "연기금 등" → 표준 "연기금등"
}


def _fetch_investor_trading(ticker: str, date_ymd: str):
    """
    단일 날짜(date_ymd)의 투자자별 순매수 조회.
      Index  : 금융투자, 보험, 투신, 사모, 은행, 기타금융, 연기금등, 기관합계,
               기타법인, 개인, 외국인합계, 기타외국인, 전체
      Columns: 매도, 매수, 순매수  (단위: 주수)
    장중/비영업일에는 KRX에서 빈 응답을 반환하므로 None 처리.
    """
    try:
        df = stock.get_market_trading_volume_by_investor(date_ymd, date_ymd, ticker)
        if df is None or df.empty:
            return None
        df.index = df.index.str.strip().map(lambda x: _INVESTOR_INDEX_MAP.get(x, x))
        logger.info("[investor] %s %s index=%s", ticker, date_ymd, df.index.tolist())
        return df
    except Exception as e:
        logger.warning("investor fetch failed for %s (%s): %s", ticker, date_ymd, e)
        return None


def _fetch_index(index_code: str, start_ymd: str, end_ymd: str):
    """KOSPI("1001") 또는 KOSDAQ("2001") 지수 OHLCV 반환."""
    try:
        return stock.get_index_ohlcv_by_date(start_ymd, end_ymd, index_code)
    except Exception:
        return None


def _index_snapshot(df, use_prev_row: bool = False) -> dict:
    """지수 DataFrame → {close, prev_close, change, change_pct}. 실패 시 전부 None."""
    try:
        if df is None or len(df) < 2:
            return {"close": None, "prev_close": None, "change": None, "change_pct": None}
        row = -2 if use_prev_row else -1
        close = round(float(df["종가"].iloc[row]), 2)
        prev_c = round(float(df["종가"].iloc[row - 1]), 2)
        chg = round(close - prev_c, 2)
        chg_pct = round(chg / prev_c * 100, 2) if prev_c else 0.0
        return {"close": close, "prev_close": prev_c, "change": chg, "change_pct": chg_pct}
    except Exception:
        return {"close": None, "prev_close": None, "change": None, "change_pct": None}


def _fetch_market_cap_ranking(ticker: str, date_ymd: str) -> "int | None":
    """KOSDAQ 시총 순위 (1-based). 실패 시 None."""
    try:
        df = stock.get_market_cap_by_ticker(date_ymd, market="KOSDAQ")
        if df is None or ticker not in df.index:
            return None
        sorted_idx = list(df["시가총액"].sort_values(ascending=False).index)
        return sorted_idx.index(ticker) + 1
    except Exception as e:
        logger.warning("cap_rank fetch failed for %s (%s): %s", ticker, date_ymd, e)
        return None


def _fetch_company_info(ticker: str) -> dict:
    """pyKRX get_stock_major_changes로 기업 주요변경 이력 및 현재 상태 조회."""
    try:
        df = stock.get_stock_major_changes(ticker)
        if df is None or df.empty:
            return {}

        def latest_str(col):
            vals = [str(v) for v in df[col] if str(v).strip() != "-"]
            return vals[-1] if vals else None

        def latest_int(col):
            vals = [int(v) for v in df[col] if v != 0]
            return vals[-1] if vals else None

        history = []
        for date_idx, row in df.iterrows():
            changes = []
            for before_col, after_col, label in [
                ("상호변경전", "상호변경후", "상호"),
                ("업종변경전", "업종변경후", "업종"),
                ("대표이사변경전", "대표이사변경후", "대표이사"),
            ]:
                b = str(row[before_col]).strip()
                a = str(row[after_col]).strip()
                if b != "-" or a != "-":
                    changes.append({
                        "구분": label,
                        "변경전": b if b != "-" else None,
                        "변경후": a if a != "-" else None,
                    })
            bv, av = int(row["액면변경전"]), int(row["액면변경후"])
            if bv != 0 or av != 0:
                changes.append({
                    "구분": "액면가",
                    "변경전": bv if bv != 0 else None,
                    "변경후": av if av != 0 else None,
                })
            if changes:
                history.append({"date": str(date_idx.date()), "changes": changes})

        return {
            "상호":    latest_str("상호변경후"),
            "업종":    latest_str("업종변경후"),
            "액면가":  latest_int("액면변경후"),
            "대표이사": latest_str("대표이사변경후"),
            "변경이력": history,
        }
    except Exception as e:
        logger.warning("company_info fetch failed for %s: %s", ticker, e)
        return {}


def _investor_val(df, row_key: str, col_key: str):
    """df.loc[row_key, col_key] 안전 추출."""
    try:
        if df is None or row_key not in df.index or col_key not in df.columns:
            return None
        val = df.loc[row_key, col_key]
        return int(val) if val == val else None  # NaN 제외
    except Exception:
        return None


def _latest(df, col):
    """df에서 col의 가장 최근 non-null 값 반환, 실패 시 None"""
    try:
        if df is None:
            return None
        s = df[col].dropna()
        return float(s.iloc[-1]) if not s.empty else None
    except Exception:
        return None


def _at_date(df, date_iso: str, col: str):
    """df에서 date_iso(YYYY-MM-DD) 날짜 행의 col 반환. 없으면 _latest fallback."""
    try:
        if df is None:
            return None
        mask = df.index.date == date.fromisoformat(date_iso)
        row = df.loc[mask, col]
        if not row.empty:
            val = row.iloc[0]
            return None if val != val else float(val)  # NaN guard
        return _latest(df, col)
    except Exception:
        return _latest(df, col)


def _safe_int(val):
    try:
        return int(val) if val is not None else None
    except Exception:
        return None


def _safe_float(val, decimals: int = 2):
    try:
        return round(float(val), decimals) if val is not None else None
    except Exception:
        return None


def _fetch_dart_fs(ticker: str) -> dict:
    """DART API로 최근 4분기 당기순이익 + 최신 자본총계 수집. 실패 시 기본값 반환."""
    _default = {"financials": [], "equity": None}
    if not DART_API_KEY:
        return _default
    try:
        import dart_fss as dart
        from datetime import datetime as _dt
        dart.set_api_key(api_key=DART_API_KEY)
        corp_list = dart.get_corp_list()
        corp = corp_list.find_by_stock_code(ticker)
        if corp is None:
            return _default
        bgn_de = (date.today() - timedelta(days=730)).strftime("%Y%m%d")
        fs = corp.extract_fs(bgn_de=bgn_de, report_tp='quarter')

        # --- IS: 당기순이익 ---
        is_df = fs['is'] if fs['is'] is not None else fs['cis']
        financials = []
        if is_df is not None:
            label_ko_col = next(
                (c for c in is_df.columns if isinstance(c, tuple) and c[-1] == 'label_ko'), None
            )
            if label_ko_col is not None:
                mask = is_df[label_ko_col].astype(str).str.contains("당기순이익", na=False)
                if mask.any():
                    row = is_df[mask].iloc[0]

                    def _parse_period(col):
                        if not (isinstance(col, tuple) and isinstance(col[0], str)
                                and len(col[0]) == 17 and col[0][8] == '-'):
                            return None
                        try:
                            s = _dt.strptime(col[0][:8], "%Y%m%d")
                            e = _dt.strptime(col[0][9:], "%Y%m%d")
                            return s, e, (e - s).days
                        except Exception:
                            return None

                    def _val(col):
                        v = row[col]
                        try:
                            return int(float(v)) if v is not None and str(v) not in ("nan", "None") else None
                        except Exception:
                            return None

                    quarters: dict[str, tuple] = {}
                    annual: dict[int, int] = {}
                    nine_month: dict[int, int] = {}

                    for col in is_df.columns:
                        parsed = _parse_period(col)
                        if parsed is None:
                            continue
                        s, e, days = parsed
                        v = _val(col)
                        if 85 <= days <= 95:
                            quarters[col[0]] = (e, v)
                        elif 355 <= days <= 375 and v is not None:
                            annual[e.year] = v
                        elif 260 <= days <= 280 and v is not None:
                            nine_month[e.year] = v

                    for year in set(annual) & set(nine_month):
                        q4_key = f"{year}1001-{year}1231"
                        if q4_key not in quarters:
                            quarters[q4_key] = (_dt(year, 12, 31), annual[year] - nine_month[year])

                    sorted_q = sorted(quarters.items(), key=lambda x: x[1][0], reverse=True)[:4]
                    for _, (end_dt, v) in sorted_q:
                        qn = (end_dt.month - 1) // 3 + 1
                        financials.append({"period": f"{end_dt.year}/Q{qn}", "net_income": v})

        # --- BS: 자본총계 ---
        equity = None
        bs_df = fs['bs']
        if bs_df is not None:
            from datetime import datetime as _dt
            label_ko_col = next(
                (c for c in bs_df.columns if isinstance(c, tuple) and c[-1] == 'label_ko'), None
            )
            if label_ko_col is not None:
                mask = bs_df[label_ko_col].astype(str).str.contains("자본총계|자본합계|자본총액", na=False)
                if mask.any():
                    bs_row = bs_df[mask].iloc[0]
                    best_val, best_date = None, None
                    for col in bs_df.columns:
                        if not (isinstance(col, tuple) and isinstance(col[0], str)):
                            continue
                        try:
                            col_date = _dt.strptime(col[0][:8], "%Y%m%d")
                        except Exception:
                            continue
                        v = bs_row[col]
                        try:
                            v_int = int(float(v)) if v is not None and str(v) not in ("nan", "None") else None
                        except Exception:
                            v_int = None
                        if v_int and (best_date is None or col_date > best_date):
                            best_val, best_date = v_int, col_date
                    equity = best_val

        return {"financials": financials, "equity": equity}
    except Exception as e:
        logger.warning("[_fetch_dart_fs] %s: %s", ticker, e)
        return _default


def collect() -> dict[str, dict]:
    today_str = date.today().isoformat()
    closed = _market_closed()
    now_kst = datetime.now(_KST).strftime("%H:%M:%S")
    logger.info("[collect] KST %s | 장마감=%s", now_kst, closed)
    result = {}

    for ticker in WATCHLIST:
        # 365일치 OHLCV → 52주 계산에도 사용
        df = _fetch_ohlcv(ticker, days_back=365)

        if df is None or len(df) < 2:
            continue

        last_date = df.index[-1].date().isoformat()
        today_not_closed = last_date == today_str and not closed

        # 장중이면 오늘 미확정 데이터를 버리고 전 거래일 확정 종가를 사용
        if today_not_closed:
            if len(df) < 3:
                continue
            curr_row, prev_row = -2, -3
            is_fallback = True
            history_df = df.iloc[:-1]  # 52주 계산용 (오늘 제외)
        else:
            curr_row, prev_row = -1, -2
            is_fallback = last_date != today_str
            history_df = df

        curr_close = int(df["종가"].iloc[curr_row])
        prev_close = int(df["종가"].iloc[prev_row])
        data_date  = df.index[curr_row].date().isoformat()
        prev_date  = df.index[prev_row].date().isoformat()
        logger.info("[collect] %s | is_fallback=%s | data_date=%s", ticker, is_fallback, data_date)
        change = curr_close - prev_close
        change_pct = round(change / prev_close * 100, 2) if prev_close else 0.0

        # 최근 7거래일 OHLCV 내장 (curr_row 기준)
        _n = len(df)
        _abs_end = _n + curr_row + 1
        _abs_start = max(0, _abs_end - 7)
        _slice = df.iloc[_abs_start:_abs_end]
        _prev_c = None
        ohlcv_7d = []
        for _idx, _row in _slice.iterrows():
            _c = int(_row["종가"])
            _ch = (_c - _prev_c) if _prev_c is not None else None
            _ch_pct = round(_ch / _prev_c * 100, 2) if _prev_c else None
            ohlcv_7d.append({
                "date":       _idx.date().isoformat(),
                "open":       int(_row["시가"]),
                "high":       int(_row["고가"]),
                "low":        int(_row["저가"]),
                "close":      _c,
                "volume":     int(_row["거래량"]),
                "change":     _ch,
                "change_pct": _ch_pct,
            })
            _prev_c = _c
        ohlcv_7d.reverse()

        # OHLCV에서 curr_row 기준 필드
        def _row_int(col):
            try:
                return int(df[col].iloc[curr_row])
            except Exception:
                return None

        open_price    = _row_int("시가")
        high_price    = _row_int("고가")
        low_price     = _row_int("저가")
        volume        = _row_int("거래량")

        # 52주 최고가·최저가 (history_df 전체 구간)
        try:
            week52_high = int(history_df["고가"].max())
        except Exception:
            week52_high = None
        try:
            week52_low = int(history_df["저가"].min())
        except Exception:
            week52_low = None

        # 수집 기준일 (YYYYMMDD)
        data_date_ymd = df.index[curr_row].date().strftime("%Y%m%d")

        # 보조 API (best-effort — 장 마감 후 또는 API 제공 시 자동 채워짐)
        dart_result     = _fetch_dart_fs(ticker)
        dart_financials = dart_result["financials"]
        dart_equity     = dart_result["equity"]
        _ttm_vals = [q["net_income"] for q in dart_financials if q.get("net_income") is not None]
        net_income_ttm = sum(_ttm_vals) if len(_ttm_vals) == 4 else None
        df_fund      = _fetch_fundamental(ticker)
        df_cap       = _fetch_market_cap(ticker)
        df_foreign   = _fetch_foreign(ticker)
        df_inv       = _fetch_investor_trading(ticker, data_date_ymd)
        company_info = _fetch_company_info(ticker)

        # KOSPI/KOSDAQ 지수 (5일치 — 전일 대비 변동 계산용)
        s5, e5 = _date_range(5)
        df_kospi  = _fetch_index("1001", s5, e5)
        df_kosdaq = _fetch_index("2001", s5, e5)

        # 시총 순위: 장 마감 후 확정 데이터만 유효 — 장중엔 KRX가 당일 데이터 미완성
        cap_rank = _fetch_market_cap_ranking(ticker, data_date_ymd) if closed else None

        _pbr    = _safe_float(_latest(df_fund, "PBR"))
        _bps    = _safe_int(_latest(df_fund, "BPS"))
        _listed = _safe_int(_at_date(df_cap, data_date, "상장주식수"))
        _equity = _bps * _listed if _bps and _listed else None

        result[ticker] = {
            "close":       curr_close,
            "prev_close":  prev_close,
            "change":      change,
            "change_pct":  change_pct,
            "is_fallback": is_fallback,
            "data_date":   data_date,
            "prev_date":   prev_date,
            "ohlcv_7d":    ohlcv_7d,
            # OHLCV 추가 필드 (항상 사용 가능)
            "open":        open_price,
            "high":        high_price,
            "low":         low_price,
            "volume":         volume,
            "trading_value":  _safe_int(_at_date(df_cap, data_date, "거래대금")),
            "week52_high": week52_high,
            "week52_low":  week52_low,
            # 보조 API — 펀더멘털 (None 허용)
            "market_cap":      _safe_int(_at_date(df_cap, data_date, "시가총액")),
            "listed_shares":   _listed,
            "per":             _safe_float(_latest(df_fund, "PER")),
            "pbr":             _pbr,
            "eps":             _safe_int(_latest(df_fund, "EPS")),
            "bps":             _bps,
            "equity":          dart_equity or _equity,
            "foreign_pct":     _safe_float(_latest(df_foreign, "지분율")),
            "exhaustion_rate": _safe_float(_latest(df_foreign, "한도소진율")),
            "cap_rank":        cap_rank,
            # 지수 (None 허용)
            "kospi":  _index_snapshot(df_kospi,  use_prev_row=is_fallback),
            "kosdaq": _index_snapshot(df_kosdaq, use_prev_row=is_fallback),
            # 투자자별 동향 (None 허용 — 장 마감 후 제공)
            "inst_buy":     _investor_val(df_inv, "기관합계",  "매수"),
            "inst_sell":    _investor_val(df_inv, "기관합계",  "매도"),
            "inst_net":     _investor_val(df_inv, "기관합계",  "순매수"),
            "indiv_buy":    _investor_val(df_inv, "개인",      "매수"),
            "indiv_sell":   _investor_val(df_inv, "개인",      "매도"),
            "indiv_net":    _investor_val(df_inv, "개인",      "순매수"),
            "foreign_buy":  _investor_val(df_inv, "외국인합계", "매수"),
            "foreign_sell": _investor_val(df_inv, "외국인합계", "매도"),
            "foreign_net":  _investor_val(df_inv, "외국인합계", "순매수"),
            # 기관 세부 순매수 (None 허용)
            "finv_net":    _investor_val(df_inv, "금융투자", "순매수"),
            "ins_net":     _investor_val(df_inv, "보험",     "순매수"),
            "trust_net":   _investor_val(df_inv, "투신",     "순매수"),
            "private_net": _investor_val(df_inv, "사모",     "순매수"),
            "bank_net":    _investor_val(df_inv, "은행",     "순매수"),
            "etc_fin_net": _investor_val(df_inv, "기타금융", "순매수"),
            "pension_net": _investor_val(df_inv, "연기금등", "순매수"),
            # DART 분기 재무 (TASK-022 TTM)
            "dart_financials": dart_financials,
            "net_income_ttm":  net_income_ttm,
            # 기업 주요변경이력 (TASK-002)
            "company_info": company_info,
        }

    return result


def collect_for_date(target_date: str) -> dict[str, dict]:
    """
    특정 과거 날짜의 OHLCV + 지수 수집. 백필 전용.
    - cap_rank는 수집 안 함 (전체 시장 조회라 느림)
    - 비영업일이면 빈 dict 반환
    """
    target_dt = date.fromisoformat(target_date)
    start_ymd = (target_dt - timedelta(days=14)).strftime("%Y%m%d")
    end_ymd   = target_dt.strftime("%Y%m%d")
    result = {}

    for ticker in WATCHLIST:
        try:
            df = stock.get_market_ohlcv(start_ymd, end_ymd, ticker)
        except Exception:
            continue

        if df is None or len(df) < 2:
            continue

        last_date = df.index[-1].date().isoformat()
        if last_date != target_date:
            continue  # 비영업일 — target_date 데이터 없음

        curr_row, prev_row = -1, -2
        curr_close = int(df["종가"].iloc[curr_row])
        prev_close = int(df["종가"].iloc[prev_row])
        change = curr_close - prev_close
        change_pct = round(change / prev_close * 100, 2) if prev_close else 0.0

        def _row_int(col):
            try:
                return int(df[col].iloc[curr_row])
            except Exception:
                return None

        try:
            week52_high = int(df["고가"].max())
        except Exception:
            week52_high = None
        try:
            week52_low = int(df["저가"].min())
        except Exception:
            week52_low = None

        # 시가총액·거래대금 (target_date 기준)
        try:
            df_cap = stock.get_market_cap_by_date(start_ymd, end_ymd, ticker)
        except Exception:
            df_cap = None

        # 지수 데이터 (target_date 전후 10일)
        idx_start = (target_dt - timedelta(days=10)).strftime("%Y%m%d")
        df_kospi  = _fetch_index("1001", idx_start, end_ymd)
        df_kosdaq = _fetch_index("2001", idx_start, end_ymd)

        # 투자자별 일별 순매수 (단일일 조회)
        df_inv = _fetch_investor_trading(ticker, end_ymd)

        # 펀더멘털 (per, pbr, eps, bps)
        try:
            df_fund = stock.get_market_fundamental(start_ymd, end_ymd, ticker)
            for col in ("EPS", "BPS", "PER", "PBR"):
                if col in df_fund.columns:
                    df_fund[col] = df_fund[col].replace(0, float("nan"))
        except Exception:
            df_fund = None

        # 외국인 소진율
        try:
            df_foreign_raw = stock.get_exhaustion_rates_of_foreign_investment_by_date(start_ymd, end_ymd, ticker)
            df_foreign_raw.columns = ["상장주식수", "보유수량", "지분율", "한도수량", "한도소진율"]
            df_foreign = df_foreign_raw
        except Exception:
            df_foreign = None

        # DART (net_income_ttm, equity)
        dart_result_fd   = _fetch_dart_fs(ticker)
        dart_fins_fd     = dart_result_fd["financials"]
        dart_equity_fd   = dart_result_fd["equity"]
        _ttm_fd = [q["net_income"] for q in dart_fins_fd if q.get("net_income") is not None]
        net_income_ttm_fd = sum(_ttm_fd) if len(_ttm_fd) == 4 else None

        _bps_fd    = _safe_int(_latest(df_fund, "BPS"))
        _listed_fd = _safe_int(_at_date(df_cap, target_date, "상장주식수"))
        _equity_fd = dart_equity_fd or (_bps_fd * _listed_fd if _bps_fd and _listed_fd else None)

        # 최근 7거래일 OHLCV 내장
        _n = len(df)
        _slice = df.iloc[max(0, _n - 7):_n]
        _prev_c = None
        ohlcv_7d = []
        for _idx, _row in _slice.iterrows():
            _c = int(_row["종가"])
            _ch = (_c - _prev_c) if _prev_c is not None else None
            _ch_pct = round(_ch / _prev_c * 100, 2) if _prev_c else None
            ohlcv_7d.append({
                "date":       _idx.date().isoformat(),
                "open":       int(_row["시가"]),
                "high":       int(_row["고가"]),
                "low":        int(_row["저가"]),
                "close":      _c,
                "volume":     int(_row["거래량"]),
                "change":     _ch,
                "change_pct": _ch_pct,
            })
            _prev_c = _c
        ohlcv_7d.reverse()

        result[ticker] = {
            "close":           curr_close,
            "prev_close":      prev_close,
            "change":          change,
            "change_pct":      change_pct,
            "is_fallback":     False,
            "data_date":       target_date,
            "ohlcv_7d":        ohlcv_7d,
            "open":            _row_int("시가"),
            "high":            _row_int("고가"),
            "low":             _row_int("저가"),
            "volume":          _row_int("거래량"),
            "trading_value":   _safe_int(_at_date(df_cap, target_date, "거래대금")),
            "week52_high":     week52_high,
            "week52_low":      week52_low,
            "market_cap":      _safe_int(_at_date(df_cap, target_date, "시가총액")),
            "listed_shares":   _listed_fd,
            "per":             _safe_float(_latest(df_fund, "PER")),
            "pbr":             _safe_float(_latest(df_fund, "PBR")),
            "eps":             _safe_int(_latest(df_fund, "EPS")),
            "bps":             _bps_fd,
            "equity":          _equity_fd,
            "foreign_pct":     _safe_float(_latest(df_foreign, "지분율")),
            "exhaustion_rate": _safe_float(_latest(df_foreign, "한도소진율")),
            "cap_rank":        _fetch_market_cap_ranking(ticker, end_ymd),
            "dart_financials": dart_fins_fd,
            "net_income_ttm":  net_income_ttm_fd,
            "kospi":           _index_snapshot(df_kospi),
            "kosdaq":          _index_snapshot(df_kosdaq),
            "inst_buy":     _investor_val(df_inv, "기관합계",  "매수"),
            "inst_sell":    _investor_val(df_inv, "기관합계",  "매도"),
            "inst_net":     _investor_val(df_inv, "기관합계",  "순매수"),
            "indiv_buy":    _investor_val(df_inv, "개인",      "매수"),
            "indiv_sell":   _investor_val(df_inv, "개인",      "매도"),
            "indiv_net":    _investor_val(df_inv, "개인",      "순매수"),
            "foreign_buy":  _investor_val(df_inv, "외국인합계", "매수"),
            "foreign_sell": _investor_val(df_inv, "외국인합계", "매도"),
            "foreign_net":  _investor_val(df_inv, "외국인합계", "순매수"),
            "finv_net":    _investor_val(df_inv, "금융투자", "순매수"),
            "ins_net":     _investor_val(df_inv, "보험",     "순매수"),
            "trust_net":   _investor_val(df_inv, "투신",     "순매수"),
            "private_net": _investor_val(df_inv, "사모",     "순매수"),
            "bank_net":    _investor_val(df_inv, "은행",     "순매수"),
            "etc_fin_net": _investor_val(df_inv, "기타금융", "순매수"),
            "pension_net": _investor_val(df_inv, "연기금등", "순매수"),
        }

    return result
