import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent  # incar_stock/ (프로젝트 루트)

WATCHLIST = {
    "211050": "인카금융서비스",
}

REPORT_DIR = BASE_DIR / "reports"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DART_API_KEY = os.getenv("DART_API_KEY", "")
