import json
import logging

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, WATCHLIST

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-lite"


def analyze(stocks: dict[str, dict]) -> tuple[dict[str, dict], str]:
    enriched = {
        ticker: {"name": WATCHLIST.get(ticker, ticker), **data, "comment": ""}
        for ticker, data in stocks.items()
    }

    if not stocks:
        return enriched, ""

    market_summary = ""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_MODEL,
            contents=_build_prompt(stocks),
            config=types.GenerateContentConfig(max_output_tokens=2048),
        )
        text = response.text.strip()
        # 마크다운 코드 펜스 제거
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        parsed = json.loads(text)
        market_summary = parsed.get("market_summary", "")
        for ticker in enriched:
            enriched[ticker]["comment"] = parsed.get("stocks", {}).get(ticker, "")
    except Exception as e:
        logger.warning("[analyzer] Gemini 호출 실패: %s", e)

    return enriched, market_summary


def _fmt_shares(val) -> str:
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:,}주"


def _fmt_vol(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:,}주"


def _fmt_money(val) -> str:
    if val is None:
        return "N/A"
    billions = val / 1_000_000_000
    if abs(billions) >= 1:
        return f"{billions:.1f}억원"
    return f"{val:,}원"


def _fmt_index(snapshot: dict | None) -> str:
    if not snapshot or snapshot.get("close") is None:
        return "N/A"
    c = snapshot["close"]
    pct = snapshot.get("change_pct", 0) or 0
    sign = "+" if pct >= 0 else ""
    return f"{c:,.2f} ({sign}{pct:.2f}%)"


def _build_prompt(stocks: dict[str, dict]) -> str:
    lines = ["다음 주가 데이터를 분석해 C-level 임원용 한국어 코멘트를 작성해 주세요.\n"]
    for ticker, data in stocks.items():
        name = WATCHLIST.get(ticker, ticker)
        sign = "+" if data["change"] >= 0 else ""
        note = " (전일 데이터 사용)" if data["is_fallback"] else ""

        lines.append(
            f"■ 종목: {name} ({ticker})\n"
            f"  종가: {data['close']:,}원  전일대비: {sign}{data['change']:,}원 ({sign}{data['change_pct']}%)\n"
            f"  기준일: {data['data_date']}{note}\n"
            f"  거래량: {_fmt_vol(data.get('volume'))} | 거래대금: {_fmt_money(data.get('trading_value'))}\n"
            f"  [투자자별 순매수]\n"
            f"    개인: {_fmt_shares(data.get('indiv_net'))} | "
            f"외국인: {_fmt_shares(data.get('foreign_net'))} | "
            f"기관합계: {_fmt_shares(data.get('inst_net'))} | "
            f"연기금: {_fmt_shares(data.get('pension_net'))}\n"
            f"  [시장 지수]\n"
            f"    KOSPI: {_fmt_index(data.get('kospi'))} | "
            f"KOSDAQ: {_fmt_index(data.get('kosdaq'))}\n"
        )
    lines.append(
        '\n아래 JSON 형식으로만 응답해 주세요 (마크다운 코드블록 없이):\n'
        '{\n'
        '  "market_summary": "시장 전체 한줄 요약 (1~2문장)",\n'
        '  "stocks": {\n'
        '    "<ticker>": "종목 분석 코멘트 — 아래 5개 항목을 **마크다운** 형식으로 작성:\n'
        '### 가격 / 등락\\n(당일 주가 흐름과 등락 배경 분석)\\n\\n'
        '### 투자자 동향\\n(개인·외국인·기관·연기금 순매수 방향과 의미 분석)\\n\\n'
        '### 거래량 · 거래대금\\n(거래 활성도와 자금 유입/유출 의미 분석)\\n\\n'
        '### 시장 대비 상대 강도\\n(KOSPI·KOSDAQ 흐름 대비 종목 상대 강도 분석)\\n\\n'
        '### 종합 의견\\n(전체를 아우르는 C-level 임원용 한줄 결론)"\n'
        '  }\n'
        '}'
    )
    return "\n".join(lines)
