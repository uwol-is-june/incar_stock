import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# backend 디렉터리를 sys.path에 추가해 어디서 실행해도 동작하게 함
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import analyzer
import collector
import reporter
from config import BASE_DIR

logger = logging.getLogger(__name__)

FRONTEND_DIR = BASE_DIR / "frontend"


def _backfill_history(days_to_check: int = 14, max_missing: int = 7):
    """과거 7영업일 리포트가 없으면 자동으로 백필."""
    today = date.today()
    filled = 0
    for offset in range(1, days_to_check + 1):
        if filled >= max_missing:
            break
        d_str = (today - timedelta(days=offset)).isoformat()
        if reporter.exists(d_str):
            continue
        try:
            hist = collector.collect_for_date(d_str)
        except Exception:
            continue
        if not hist:
            continue  # 비영업일
        reporter.save(d_str, hist, "")
        filled += 1


async def _auto_collect_job():
    today = date.today().isoformat()
    if not collector.is_business_day(today):
        logger.info("[scheduler] %s 비영업일, 스킵", today)
        return
    logger.info("[scheduler] %s 자동 수집 시작 (cap_rank 포함 마감 데이터)", today)
    try:
        stocks = collector.collect()
        if stocks:
            reporter.save(today, stocks, "")
            logger.info("[scheduler] %s 자동 수집 완료 (%d종목)", today, len(stocks))
    except Exception as e:
        logger.error("[scheduler] %s 자동 수집 실패: %s", today, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _backfill_history)

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(_auto_collect_job, "cron", hour=16, minute=10)
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(title="InCar Stock Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/generate")
def generate(background_tasks: BackgroundTasks):
    stocks = collector.collect()
    if not stocks:
        raise HTTPException(status_code=503, detail="주가 데이터를 가져올 수 없습니다.")

    enriched, market_summary = analyzer.analyze(stocks)

    # 리포트 기준일: 수집된 데이터 중 가장 최신 data_date 사용
    data_dates = [v["data_date"] for v in enriched.values() if "data_date" in v]
    date_str = max(data_dates) if data_dates else date.today().isoformat()

    reporter.save(date_str, enriched, market_summary)

    # 과거 7영업일 백필 — 응답 반환 후 백그라운드에서 실행
    background_tasks.add_task(_backfill_history)

    return reporter.load(date_str)


@app.post("/api/backfill-investor")
def backfill_investor():
    """
    기존 보고서에 투자자 데이터가 없거나 외국인이 null 이면 재수집해서 패치.
    (collect_for_date() 수정 후 기존 보고서에 일괄 적용할 때 사용)
    """
    _INVESTOR_KEYS = (
        "inst_buy", "inst_sell", "inst_net",
        "indiv_buy", "indiv_sell", "indiv_net",
        "foreign_buy", "foreign_sell", "foreign_net",
        "finv_net", "ins_net", "trust_net", "private_net",
        "bank_net", "etc_fin_net", "pension_net",
    )
    patched, skipped = [], []
    for date_str in reporter.list_dates():
        report = reporter.load(date_str)
        if report is None:
            continue
        stocks = report.get("stocks", {})
        needs_patch = any(
            v.get("foreign_net") is None
            for v in stocks.values()
        )
        if not needs_patch:
            skipped.append(date_str)
            continue
        try:
            fresh = collector.collect_for_date(date_str)
        except Exception as e:
            logger.warning("[backfill-investor] %s collect 실패: %s", date_str, e)
            continue
        if not fresh:
            skipped.append(date_str)
            continue
        for ticker, d in fresh.items():
            if ticker in stocks:
                stocks[ticker].update({k: d[k] for k in _INVESTOR_KEYS if k in d})
        reporter.save(date_str, stocks, report.get("market_summary", ""))
        patched.append(date_str)
        logger.info("[backfill-investor] %s 패치 완료", date_str)
    return {"patched": patched, "skipped": skipped}


@app.get("/api/dates")
def get_dates():
    return reporter.list_dates()


@app.get("/api/report/{date_str}")
def get_report(date_str: str):
    report = reporter.load(date_str)
    if report is None:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return report


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
