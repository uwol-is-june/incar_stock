import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import analyzer
import reporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    dates = reporter.list_dates()
    if not dates:
        logger.info("[backfill_ai] 리포트 없음")
        return

    for date_str in dates:
        report = reporter.load(date_str)
        if not report:
            continue
        logger.info("[backfill_ai] %s AI 재분석 시작", date_str)
        enriched, market_summary = analyzer.analyze(report["stocks"])
        reporter.save(date_str, enriched, market_summary)
        logger.info("[backfill_ai] %s 완료", date_str)

    logger.info("[backfill_ai] 전체 완료")


if __name__ == "__main__":
    main()
