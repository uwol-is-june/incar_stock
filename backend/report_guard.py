"""
보고서 멱등성 보호 로직.

`run_collect.py`는 수집 결과의 `data_date`(실제 거래일)를 파일명으로 저장한다.
그래서 GitHub Actions 스케줄이 수 시간 지연 실행되거나(예: 16:10 KST 실행이 다음 날
01:58 KST에 실행) 장중에 중복 실행되면, `data_date`가 **이미 확정된 과거 거래일**로
잡히면서 `reports/{data_date}.json`을 장중/전일 fallback 데이터로 덮어써 버린다.
그 결과 기존 보고서에 있던 지수·투자자 동향·시가총액 같은 확정 데이터가 사라진다.

이 모듈은 "기존 보고서를 덮어써도 되는가"만 판단한다. 파일 I/O와 수집 로직을
포함하지 않아 단위 테스트로 검증할 수 있다.

판단 규칙
- 기존 보고서가 없으면 저장한다.
- `data_date`가 오늘(KST)이면 정상 갱신 대상이므로 저장한다.
  (단, 기존 오늘 보고서가 완전한데 새 데이터가 미완성이면 보호한다.)
- `data_date`가 과거 거래일이면 = 지연/중복/장중 실행이 과거 보고서를 건드리는 경우다.
  기존 보고서가 이미 완전하면 덮어쓰지 않는다.
  기존 보고서가 미완성일 때만, 새 데이터가 더 완전할 경우에 보완 저장한다.
"""

from typing import Any

# 완전성 판단에 쓰는 필수 필드(하나라도 없으면 그 보고서는 미완성)
# - close             : 종가
# - ohlcv_7d          : 최근 7거래일 시세(차트·표)
# - kospi / kosdaq    : 지수 스냅샷(상단 지수 카드)
# - inst/foreign/indiv: 투자자 동향(투자자 탭)
GUARDED_FIELD_COUNT = 5


def _has_index(stock: dict, key: str) -> bool:
    snap = stock.get(key)
    return isinstance(snap, dict) and snap.get("close") is not None


def _has_investor(stock: dict) -> bool:
    return any(
        stock.get(k) is not None
        for k in ("inst_net", "foreign_net", "indiv_net")
    )


def stock_is_complete(stock: dict) -> bool:
    """종목 하나가 '확정 데이터'로 볼 만큼 채워졌는지."""
    if not isinstance(stock, dict):
        return False
    if stock.get("close") is None:
        return False
    if len(stock.get("ohlcv_7d") or []) < 2:
        return False
    if not _has_index(stock, "kospi") or not _has_index(stock, "kosdaq"):
        return False
    if not _has_investor(stock):
        return False
    return True


def is_complete(stocks: dict | None) -> bool:
    """보고서 전체가 완전한지(종목 데이터가 비어 있으면 미완성)."""
    if not stocks:
        return False
    return all(stock_is_complete(s) for s in stocks.values())


def stock_score(stock: dict) -> int:
    """종목 하나의 완전성 점수(0~7). 미완성 보고서끼리 비교할 때 쓴다."""
    if not isinstance(stock, dict):
        return 0
    score = 0
    if stock.get("close") is not None:
        score += 1
    if len(stock.get("ohlcv_7d") or []) >= 2:
        score += 1
    if _has_index(stock, "kospi"):
        score += 1
    if _has_index(stock, "kosdaq"):
        score += 1
    if _has_investor(stock):
        score += 1
    if stock.get("market_cap") is not None:
        score += 1
    if stock.get("per") is not None or stock.get("pbr") is not None:
        score += 1
    return score


def report_score(stocks: dict | None) -> int:
    if not stocks:
        return 0
    return sum(stock_score(s) for s in stocks.values())


def decide(
    existing: dict | None,
    *,
    data_date: str,
    today: str,
    new_stocks: dict | None,
) -> tuple[bool, str]:
    """기존 보고서(existing)를 새 데이터(new_stocks)로 덮어쓸지 판단.

    Returns:
        (덮어쓸지 여부, 사람이 읽을 사유)
    """
    if not new_stocks:
        return False, "새 수집 데이터가 비어 있음"

    if not existing:
        return True, "기존 보고서 없음 → 신규 저장"

    old_stocks: dict[str, Any] = existing.get("stocks") or {}
    if not old_stocks:
        return True, "기존 보고서에 종목 데이터 없음 → 저장"

    if data_date < today:
        # 과거 거래일 보고서를 건드리는 실행 = 지연/중복/장중 실행
        old_complete = is_complete(old_stocks)
        if old_complete:
            return False, f"과거 거래일({data_date}) 확정 보고서 보호 — 덮어쓰지 않음"
        if is_complete(new_stocks):
            return True, f"과거({data_date}) 보고서가 미완성 → 완전한 데이터로 보완"
        if report_score(new_stocks) > report_score(old_stocks):
            return True, f"과거({data_date}) 미완성 보고서를 더 완전한 데이터로 보완"
        return False, (
            f"과거 거래일({data_date}) 보고서 미완성 · "
            "새 데이터도 더 나아지지 않아 덮어쓰지 않음"
        )

    # 오늘(KST) 보고서: 정상 갱신 대상
    if is_complete(old_stocks) and not is_complete(new_stocks):
        return False, "오늘 확정 보고서 보호 — 새 데이터는 미완성"
    return True, "오늘 보고서 갱신"
