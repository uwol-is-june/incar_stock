import sys
import logging
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import analyzer
import collector
import reporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    today = date.today().isoformat()

    if not collector.is_business_day(today):
        logger.info("[run_collect] %s 비영업일, 스킵", today)
        return

    logger.info("[run_collect] %s 수집 시작", today)
    stocks = collector.collect()
    if not stocks:
        logger.error("[run_collect] 데이터 수집 실패")
        sys.exit(1)

    data_date = stocks[0]["data_date"]
    enriched, market_summary = analyzer.analyze(stocks)
    reporter.save(data_date, enriched, market_summary)  # save() → update_index() 자동 호출
    reporter.prune(5)                 # prune() → update_index() 자동 호출
    logger.info("[run_collect] %s 완료 (data_date=%s)", today, data_date)


if __name__ == "__main__":
    main()
