"""run_collect 멱등성 보호 로직 테스트.

실행:
    python -m unittest discover -s tests -v
"""

import json
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# reporter → config → dotenv 를 테스트 환경에서 import (미설치 대비 스텁)
if "dotenv" not in sys.modules:
    _dotenv = types.ModuleType("dotenv")
    _dotenv.load_dotenv = lambda *a, **k: None
    sys.modules["dotenv"] = _dotenv

import report_guard  # noqa: E402
import reporter  # noqa: E402


def make_stock(*, close=10490, ohlcv=True, index=True, investor=True,
               market_cap=True, per=True, is_fallback=False):
    """테스트용 종목 데이터."""
    return {
        "name": "인카금융서비스",
        "close": close,
        "prev_close": 10070,
        "is_fallback": is_fallback,
        "data_date": "2026-11-16",
        "ohlcv_7d": (
            [{"date": "2026-11-13", "close": 10070}, {"date": "2026-11-16", "close": close}]
            if ohlcv else []
        ),
        "kospi": {"close": 5100.5} if index else {"close": None},
        "kosdaq": {"close": 665.65} if index else {"close": None},
        "inst_net": -22222 if investor else None,
        "foreign_net": 42711 if investor else None,
        "indiv_net": 1000 if investor else None,
        "market_cap": 514312579080 if market_cap else None,
        "per": 7.06 if per else None,
        "pbr": 2.38 if per else None,
    }


def make_report(date_str, *, is_fallback=False, **stock_kwargs):
    return {
        "date": date_str,
        "generated_at": f"{date_str}T16:10:00+09:00",
        "market_summary": "요약",
        "stocks": {"211050": make_stock(is_fallback=is_fallback, **stock_kwargs)},
    }


class GuardDecisionTest(unittest.TestCase):
    """report_guard.decide() 판단 규칙."""

    def test_no_existing_report_saves(self):
        allow, _ = report_guard.decide(
            None, data_date="2026-11-17", today="2026-11-17", new_stocks={"211050": make_stock()}
        )
        self.assertTrue(allow)

    def test_past_date_complete_report_is_protected(self):
        """지연 실행이 이미 확정된 과거 보고서를 fallback 으로 덮어쓰지 못한다."""
        allow, reason = report_guard.decide(
            make_report("2026-11-16"),
            data_date="2026-11-16",
            today="2026-11-17",
            new_stocks={"211050": make_stock(close=10340, investor=False, is_fallback=True)},
        )
        self.assertFalse(allow)
        self.assertIn("보호", reason)

    def test_past_date_incomplete_report_is_repaired(self):
        """기존 과거 보고서가 미완성(지수·투자자 없음)이면 완전한 데이터로 보완한다."""
        allow, _ = report_guard.decide(
            make_report("2026-11-13", index=False, investor=False, market_cap=False, per=False),
            data_date="2026-11-13",
            today="2026-11-17",
            new_stocks={"211050": make_stock()},
        )
        self.assertTrue(allow)

    def test_past_date_incomplete_both_and_not_better_is_skipped(self):
        allow, reason = report_guard.decide(
            make_report("2026-11-13", index=False, investor=False, is_fallback=True),
            data_date="2026-11-13",
            today="2026-11-17",
            new_stocks={"211050": make_stock(index=False, investor=False, is_fallback=True)},
        )
        self.assertFalse(allow)
        self.assertIn("덮어쓰지 않음", reason)

    def test_today_report_updates(self):
        """오늘 16:10 장마감 실행은 정상 동작해야 한다."""
        allow, _ = report_guard.decide(
            make_report("2026-11-17", is_fallback=True),
            data_date="2026-11-17",
            today="2026-11-17",
            new_stocks={"211050": make_stock()},
        )
        self.assertTrue(allow)

    def test_today_first_save(self):
        allow, _ = report_guard.decide(
            None, data_date="2026-11-17", today="2026-11-17", new_stocks={"211050": make_stock()}
        )
        self.assertTrue(allow)

    def test_empty_new_stocks_never_write(self):
        allow, _ = report_guard.decide(
            None, data_date="2026-11-17", today="2026-11-17", new_stocks={}
        )
        self.assertFalse(allow)

    def test_completeness_helpers(self):
        self.assertTrue(report_guard.is_complete({"211050": make_stock()}))
        self.assertFalse(report_guard.is_complete({"211050": make_stock(investor=False)}))
        self.assertFalse(report_guard.is_complete({"211050": make_stock(index=False)}))
        self.assertFalse(report_guard.is_complete({"211050": make_stock(ohlcv=False)}))
        self.assertFalse(report_guard.is_complete({}))
        self.assertFalse(report_guard.is_complete(None))
        self.assertGreater(
            report_guard.report_score({"211050": make_stock()}),
            report_guard.report_score({"211050": make_stock(investor=False)}),
        )


class SaveGuardedTest(unittest.TestCase):
    """reporter.save_guarded() 파일 동작."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self._orig_dir = reporter.REPORT_DIR
        reporter.REPORT_DIR = Path(self._tmp.name)

    def tearDown(self):
        reporter.REPORT_DIR = self._orig_dir
        self._tmp.cleanup()

    def _write_existing(self, date_str, **kwargs):
        path = reporter.REPORT_DIR / f"{date_str}.json"
        path.write_text(
            json.dumps(make_report(date_str, **kwargs), ensure_ascii=False), encoding="utf-8"
        )
        return path

    def test_late_run_does_not_touch_past_report(self):
        """2026-11-17 01:58 지연 실행 시나리오: 11-16 확정 보고서가 보존된다."""
        path = self._write_existing("2026-11-16")
        before = path.read_text(encoding="utf-8")

        saved, reason = reporter.save_guarded(
            "2026-11-16",
            {"211050": make_stock(close=10340, investor=False, is_fallback=True)},
            "장중 fallback 요약",
            today="2026-11-17",
        )

        self.assertIsNone(saved)
        self.assertIn("보호", reason)
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_today_run_writes_and_updates_index(self):
        saved, _ = reporter.save_guarded(
            "2026-11-17", {"211050": make_stock()}, "요약", today="2026-11-17"
        )
        self.assertIsNotNone(saved)
        self.assertTrue((reporter.REPORT_DIR / "2026-11-17.json").exists())
        self.assertEqual(
            json.loads((reporter.REPORT_DIR / "index.json").read_text(encoding="utf-8")),
            ["2026-11-17"],
        )

    def test_intraday_run_fills_missing_today_report(self):
        """장중 수동 실행(전 거래일 데이터)은 오늘 보고서가 없으면 저장한다."""
        saved, _ = reporter.save_guarded(
            "2026-11-17",
            {"211050": make_stock(is_fallback=True)},
            "요약",
            today="2026-11-17",
        )
        self.assertIsNotNone(saved)

    def test_force_overrides_protection(self):
        path = self._write_existing("2026-11-16")
        saved, reason = reporter.save_guarded(
            "2026-11-16",
            {"211050": make_stock(close=10340)},
            "요약",
            today="2026-11-17",
            force=True,
        )
        self.assertIsNotNone(saved)
        self.assertIn("force", reason)
        self.assertEqual(
            json.loads(path.read_text(encoding="utf-8"))["stocks"]["211050"]["close"], 10340
        )


if __name__ == "__main__":
    unittest.main()
