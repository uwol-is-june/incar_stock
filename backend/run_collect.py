import sys
import logging
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import analyzer
import collector
import reporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="인카금융서비스 일일 시세 수집")
    parser.add_argument(
        "--force",
        action="store_true",
        help="이미 확정된 과거 보고서도 덮어쓴다 (기본은 보호).",
    )
    args = parser.parse_args()

    today = date.today().isoformat()

    if not collector.is_business_day(today):
        logger.info("[run_collect] %s 비영업일, 스킵", today)
        return

    logger.info("[run_collect] %s 수집 시작", today)
    stocks = collector.collect()
    if not stocks:
        logger.error("[run_collect] 데이터 수집 실패")
        sys.exit(1)

    data_date = next(iter(stocks.values()))["data_date"]
    enriched, market_summary = analyzer.analyze(stocks)

    # 이미 확정된 과거 거래일 보고서는 지연·중복 실행이 덮어쓰지 않는다.
    # (reporter.save() → update_index() 자동 호출)
    path, reason = reporter.save_guarded(
        data_date,
        enriched,
        market_summary,
        today=today,
        force=args.force,
    )

    if path is None:
        logger.warning(
            "[run_collect] %s 저장 생략 (data_date=%s, 실행일=%s): %s",
            data_date, data_date, today, reason,
        )
        return

    reporter.prune(10)  # prune() → update_index() 자동 호출
    logger.info(
        "[run_collect] %s 완료 (data_date=%s, 실행일=%s): %s",
        today, data_date, today, reason,
    )


if __name__ == "__main__":
    main()
