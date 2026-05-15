"""기존 reports/*.json에 kospi_history / kosdaq_history 필드를 소급 추가한다.

AI 코멘트 등 기존 데이터는 그대로 보존하고 히스토리 필드만 삽입한다.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collector import _fetch_index, _index_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
TICKER = "211050"


def patch_file(json_path: Path) -> bool:
    date_str = json_path.stem  # e.g. "2026-05-14"
    try:
        target_dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.warning("날짜 파싱 실패, 스킵: %s", json_path.name)
        return False

    data = json.loads(json_path.read_text(encoding="utf-8"))
    stock = data.get("stocks", {}).get(TICKER)
    if stock is None:
        logger.warning("%s: 종목 데이터 없음, 스킵", json_path.name)
        return False

    if "kospi_history" in stock and "kosdaq_history" in stock:
        if stock["kospi_history"] and stock["kosdaq_history"]:
            logger.info("%s: 이미 히스토리 존재, 스킵", json_path.name)
            return False

    idx_start = (target_dt - timedelta(days=44)).strftime("%Y%m%d")
    end_ymd = target_dt.strftime("%Y%m%d")

    logger.info("%s: 지수 데이터 fetch (%s ~ %s)", json_path.name, idx_start, end_ymd)
    df_kospi = _fetch_index("1001", idx_start, end_ymd)
    df_kosdaq = _fetch_index("2001", idx_start, end_ymd)

    kospi_hist = _index_history(df_kospi)
    kosdaq_hist = _index_history(df_kosdaq)

    if not kospi_hist:
        logger.warning("%s: kospi 히스토리 비어 있음 (비영업일?)", json_path.name)

    stock["kospi_history"] = kospi_hist
    stock["kosdaq_history"] = kosdaq_hist

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("%s: 패치 완료 (kospi %d개, kosdaq %d개)", json_path.name, len(kospi_hist), len(kosdaq_hist))
    return True


def main() -> None:
    files = sorted(REPORTS_DIR.glob("*.json"))
    if not files:
        logger.error("reports/ 에 JSON 파일이 없습니다.")
        return

    patched = 0
    for f in files:
        if patch_file(f):
            patched += 1

    logger.info("완료: %d/%d 파일 패치됨", patched, len(files))


if __name__ == "__main__":
    main()
