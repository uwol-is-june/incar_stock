import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
from pathlib import Path

import report_guard
from config import REPORT_DIR


def save(date_str: str, stocks: dict[str, dict], market_summary: str) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    report = {
        "date": date_str,
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "market_summary": market_summary,
        "stocks": stocks,
    }
    path = REPORT_DIR / f"{date_str}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    update_index()
    return path


def save_guarded(
    date_str: str,
    stocks: dict[str, dict],
    market_summary: str,
    *,
    today: str | None = None,
    force: bool = False,
) -> tuple[Path | None, str]:
    """멱등성 보호를 거쳐 저장한다 (run_collect.py 전용).

    이미 확정된 과거 거래일 보고서를 지연·중복 실행이 덮어쓰지 않도록
    report_guard.decide()로 판단한 뒤, 허용될 때만 실제로 쓴다.
    (백필·AI 재분석처럼 기존 보고서를 의도적으로 고치는 경로는 save()를 그대로 쓴다.)

    Returns:
        (저장된 경로 또는 None, 사유)
    """
    today = today or datetime.now(KST).date().isoformat()
    if force:
        return save(date_str, stocks, market_summary), "--force: 보호 로직 무시하고 저장"

    allowed, reason = report_guard.decide(
        load(date_str),
        data_date=date_str,
        today=today,
        new_stocks=stocks,
    )
    if not allowed:
        return None, reason
    return save(date_str, stocks, market_summary), reason


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
        [p.stem for p in REPORT_DIR.glob("*.json") if p.stem != "index"],
        reverse=True,
    )


def update_index() -> None:
    dates = list_dates()
    index_path = REPORT_DIR / "index.json"
    index_path.write_text(json.dumps(dates, ensure_ascii=False, indent=2), encoding="utf-8")


def prune(keep_n: int = 5) -> list[str]:
    """최신 keep_n개만 남기고 나머지 JSON 파일 삭제."""
    deleted = []
    for d in list_dates()[keep_n:]:
        p = REPORT_DIR / f"{d}.json"
        if p.exists():
            p.unlink()
            deleted.append(d)
    update_index()
    return deleted
