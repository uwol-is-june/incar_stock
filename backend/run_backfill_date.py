import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import analyzer
import collector
import reporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(target_date: str) -> None:
    if reporter.exists(target_date):
        logger.info("[backfill_date] %s 이미 존재, 스킵", target_date)
        return

    logger.info("[backfill_date] %s 수집 시작", target_date)
    stocks = collector.collect_for_date(target_date)
    if not stocks:
        logger.error("[backfill_date] %s 비영업일 또는 데이터 없음", target_date)
        return

    enriched, market_summary = analyzer.analyze(stocks)
    reporter.save(target_date, enriched, market_summary)
    reporter.prune(5)
    logger.info("[backfill_date] 완료 — 보고서 %d개: %s",
                len(reporter.list_dates()), reporter.list_dates())


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else "2026-05-08"
    main(date_arg)
