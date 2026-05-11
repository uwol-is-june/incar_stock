import json

import anthropic

from config import ANTHROPIC_API_KEY, WATCHLIST


def analyze(stocks: dict[str, dict]) -> tuple[dict[str, dict], str]:
    enriched = {
        ticker: {"name": WATCHLIST.get(ticker, ticker), **data, "comment": ""}
        for ticker, data in stocks.items()
    }

    if not stocks:
        return enriched, ""

    market_summary = ""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": _build_prompt(stocks)}],
        )
        parsed = json.loads(message.content[0].text)
        market_summary = parsed.get("market_summary", "")
        for ticker in enriched:
            enriched[ticker]["comment"] = parsed.get("stocks", {}).get(ticker, "")
    except Exception:
        pass

    return enriched, market_summary


def _build_prompt(stocks: dict[str, dict]) -> str:
    lines = ["다음 주가 데이터를 분석해 C-level 임원용 한국어 코멘트를 작성해 주세요.\n"]
    for ticker, data in stocks.items():
        name = WATCHLIST.get(ticker, ticker)
        sign = "+" if data["change"] >= 0 else ""
        note = " (전일 데이터 사용)" if data["is_fallback"] else ""
        lines.append(
            f"종목: {name} ({ticker})\n"
            f"종가: {data['close']:,}원\n"
            f"전일대비: {sign}{data['change']:,}원 ({sign}{data['change_pct']}%)\n"
            f"데이터 기준일: {data['data_date']}{note}\n"
        )
    lines.append(
        '\n아래 JSON 형식으로만 응답해 주세요 (마크다운 코드블록 없이):\n'
        '{\n'
        '  "market_summary": "시장 전체 한줄 요약 (1~2문장)",\n'
        '  "stocks": {\n'
        '    "<ticker>": "종목 분석 코멘트 (2~3문장)"\n'
        '  }\n'
        '}'
    )
    return "\n".join(lines)
