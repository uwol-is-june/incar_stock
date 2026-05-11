import json
from datetime import datetime
from pathlib import Path

from config import REPORT_DIR


def save(date_str: str, stocks: dict[str, dict], market_summary: str) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    report = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "market_summary": market_summary,
        "stocks": stocks,
    }
    path = REPORT_DIR / f"{date_str}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load(date_str: str) -> dict | None:
    path = REPORT_DIR / f"{date_str}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def exists(date_str: str) -> bool:
    return (REPORT_DIR / f"{date_str}.json").exists()


def list_dates() -> list[str]:
    if not REPORT_DIR.exists():
        return []
    return sorted(
        [p.stem for p in REPORT_DIR.glob("*.json")],
        reverse=True,
    )
